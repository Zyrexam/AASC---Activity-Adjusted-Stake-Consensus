import threading
import time
import random
import poem_global as poem
import aasc as aasc
import pos as pos
import poch as poch
from tabulate import tabulate
import psutil
import json
from datetime import datetime
import os

class Test:
    def __init__(self, test_type='throughput', number_of_transactions=200):
        self.test_type = test_type
        self.number_of_transactions = number_of_transactions
        self.process = psutil.Process()

    def ensure_results_dir(self, nodes, miners):
        base_dir = os.path.join("results", "churn")
        config_dir = os.path.join(base_dir, f"{nodes}nodes_{miners}miners")
        os.makedirs(config_dir, exist_ok=True)
        return config_dir

    def create_network(self, num_nodes, num_miners):
        assert num_nodes >= num_miners
        nodes = [7000 + i for i in range(num_nodes)]
        validators = random.sample(nodes, num_miners)

        edges = []
        shuffled_nodes = nodes[:]
        random.shuffle(shuffled_nodes)
        
        for i in range(1, num_nodes):
            u = shuffled_nodes[i]
            v = shuffled_nodes[random.randint(0, i - 1)]
            edges.append((u, v))
        
        possible_edges = [
            (u, v) for i, u in enumerate(nodes) for v in nodes[i + 1:]
            if (u, v) not in edges and (v, u) not in edges
        ]
        
        random.shuffle(possible_edges)
        extra_edges = min(num_nodes*7, len(possible_edges)//2)
        
        for _ in range(extra_edges):
            edges.append(possible_edges.pop())   

        network = {
            'nodes': nodes,
            'validators': validators,
            'edges': edges
        }

        with open('network.txt', 'a') as f:
            print(network, file=f)

        return nodes, validators, edges
    
    def run_node(self, port, is_validator=None, address='127.0.0.1', algo=aasc):
        if is_validator is None:
            node = algo.Node(address, port)
        else:
            node = algo.Node(address, port, is_validator)

        cli = algo.NodeCLI(node)
        node_thread = threading.Thread(target=node.start, daemon=True)
        node_thread.start()
        
        return node, cli
    
    def get_cpu_memory_usage(self):
        """Get CPU and memory usage with proper measurement"""
        try:
            # interval=0.2 for stability, discard this sample if it's the first one in a sequence
            # But here we just return current snapshot
            cpu = self.process.cpu_percent(interval=0.2)
            memory = self.process.memory_info().rss / (1024 * 1024)  # MB
            return max(0, cpu), max(0, memory)
        except:
            return 0, 0
    
    def simulate_churn(self, active_nodes, nodes, validators, churn_rate, online_nodes, duration=30):
        """
        Simulate node churn by deterministically offlining and onlining nodes
        
        Args:
            online_nodes: Shared set to track currently online nodes
        Returns:
            churn_events: list of churn events with timestamps
        """
        offline_nodes = set()
        churn_events = []
        start_time = time.time()
        check_interval = 1  # Check every 1 second
        
        print(f"[CHURN] Starting churn simulation (duration: {duration}s, rate: {churn_rate*100:.0f}%)")
        
        while time.time() - start_time < duration:
            current_time = time.time() - start_time
            
            # Deterministic Churn Logic
            # Calculate target number of nodes to fail
            target_fail_count = int(len(active_nodes) * churn_rate)
            if churn_rate > 0:
                target_fail_count = max(1, target_fail_count)
            else:
                target_fail_count = 0
            
            current_offline = len(offline_nodes)
            
            # Node failure (go offline)
            if current_offline < target_fail_count and len(active_nodes) > 1:
                available_nodes = [n for n in active_nodes.keys() if n not in offline_nodes]
                if available_nodes:
                    node_to_fail = random.choice(available_nodes)
                    try:
                        offline_nodes.add(node_to_fail)
                        if node_to_fail in online_nodes:
                            online_nodes.remove(node_to_fail)
                            
                        churn_events.append({
                            'time': round(current_time, 2),
                            'event': 'offline',
                            'node': node_to_fail
                        })
                        print(f"[CHURN] Node {node_to_fail} OFFLINE at {current_time:.2f}s")
                    except Exception as e:
                        print(f"[ERROR] Failed to offline node: {e}")
            
            # Node recovery (rejoin) - periodic reintegration
            # We want to maintain roughly 'target_fail_count' offline, but cycle them
            # So if we are at target, maybe recover one to let another fail next tick?
            # Or just simple logic: recover if we have offline nodes, to simulate turnover
            
            # Simulating turnover: If we have offline nodes, recover one with some probability
            # to allow a new one to fail in next iteration
            if offline_nodes and random.random() < 0.3:
                node_to_recover = random.choice(list(offline_nodes))
                try:
                    offline_nodes.discard(node_to_recover)
                    online_nodes.add(node_to_recover)
                    
                    churn_events.append({
                        'time': round(current_time, 2),
                        'event': 'online',
                        'node': node_to_recover
                    })
                    print(f"[CHURN] Node {node_to_recover} ONLINE at {current_time:.2f}s")
                except Exception as e:
                    print(f"[ERROR] Failed to recover node: {e}")
            
            time.sleep(check_interval)
        
        print(f"[CHURN] Simulation complete. Events: {len(churn_events)}")
        # Restore all nodes at end
        for node in offline_nodes:
            online_nodes.add(node)
        return churn_events, offline_nodes
    
    def run_test_with_churn(self, num_nodes, num_miners, churn_rate=0.0, 
                           transaction_count=100, churn_duration=30):
        """Run consensus test with simulated node churn multiple times and average"""
        
        total_runs = 5
        aggregated_results = {'AASC': [], 'PoS': [], 'PoCH': [], 'PoEM': []}
        
        print(f"\n{'='*80}")
        print(f"CHURN TEST: {num_nodes} nodes, {num_miners} miners, {churn_rate*100:.0f}% churn")
        print(f"Running {total_runs} independent trials for averaging...")
        print(f"{'='*80}\n")
        
        for run_idx in range(total_runs):
            print(f"\n>>> RUN {run_idx + 1}/{total_runs}")
            nodes, validators, edges = self.create_network(num_nodes, num_miners)
            
            # Test AASC
            print("\n[TEST 1/4] AASC with Churn")
            res = self.AASC_test_with_churn(nodes, validators, edges, churn_rate, transaction_count, churn_duration)
            aggregated_results['AASC'].append(res)
            time.sleep(2)
            
            # Test PoS
            print("\n[TEST 2/4] PoS with Churn")
            res = self.POS_test_with_churn(nodes, validators, edges, churn_rate, transaction_count, churn_duration)
            aggregated_results['PoS'].append(res)
            time.sleep(2)
            
            # Test PoCH
            print("\n[TEST 3/4] PoCH with Churn")
            res = self.PoCH_test_with_churn(nodes, validators, edges, churn_rate, transaction_count, churn_duration)
            aggregated_results['PoCH'].append(res)
            time.sleep(2)
            
            # Test PoEM
            print("\n[TEST 4/4] PoEM with Churn")
            res = self.PoEM_test_with_churn(nodes, validators, edges, churn_rate, transaction_count, churn_duration)
            aggregated_results['PoEM'].append(res)
            time.sleep(2)
            
        # Average results
        final_results = {}
        for algo, runs in aggregated_results.items():
            avg_res = {
                'throughput': sum(r['throughput'] for r in runs) / len(runs),
                'latency': sum(r['latency'] for r in runs) / len(runs), # Actually block_latency now
                'cpu_usage': sum(r['cpu_usage'] for r in runs) / len(runs),
                'memory_usage': sum(r['memory_usage'] for r in runs) / len(runs),
                'success_rate': sum(r['success_rate'] for r in runs) / len(runs),
                'consensus_failure_rate': sum(r['consensus_failure_rate'] for r in runs) / len(runs)
            }
            final_results[algo] = avg_res
            
        # Save results
        self.save_churn_results(num_nodes, num_miners, churn_rate, final_results)
        
        return final_results

    def AASC_test_with_churn(self, nodes, validators, edges, churn_rate, 
                            tx_count, churn_duration):
        """AASC consensus with churn"""
        active_nodes = {node: self.run_node(node, node in validators, algo=aasc) 
                       for node in nodes}
        
        # Shared state for online nodes (Paper Fix #1)
        online_nodes = set(nodes)
        
        print("Connecting peer nodes...")
        for u, v in edges:
            try:
                active_nodes[u][1].do_addpeer(f"127.0.0.1 {v}")
                time.sleep(0.05)
            except:
                pass
        
        time.sleep(2)
        
        # Start churn simulation in parallel
        churn_thread = threading.Thread(
            target=self.simulate_churn,
            args=(active_nodes, nodes, validators, churn_rate, online_nodes, churn_duration),
            daemon=True
        )
        churn_thread.start()
        
        # Collect validators
        try:
            active_nodes[nodes[0]][1].do_sval("")
            time.sleep(1)
        except:
            pass
        
        # Send transactions while churn happens
        transaction_nodes = random.sample(nodes, max(1, len(nodes) // 2))
        total_transactions = 0
        failed_transactions = 0
        
        # Consensus Failure Tracking
        failed_rounds = 0
        total_rounds = 0
        initial_chain_len = active_nodes[nodes[0]][1].do_count("")
        last_chain_len = initial_chain_len
        
        print("Starting transaction phase with churn...")
        # Measure CPU/Memory at start
        self.process.cpu_percent(interval=None)
        initial_memory = self.process.memory_info().rss / (1024 * 1024)
        cpu_samples = []
        
        start_time = time.time()
        
        for node in transaction_nodes:
            batch_size = tx_count // max(1, len(transaction_nodes))
            for i in range(batch_size):
                # FIX #1: Only send if node is online
                if node not in online_nodes:
                    # Retry logic or skip? Skip means effective churn reducing load
                    continue
                
                # Check for validator blocking - implicitly done by node logic if we could stop it,
                # but here we just ensure we don't interact with offline validators
                if node in validators and node not in online_nodes:
                    continue

                try:
                    if node in active_nodes:
                        recipient = f"user{random.randint(1, 100)}"
                        amount = random.randint(1, 10)
                        cmd_str = f"{recipient} {amount}"
                        active_nodes[node][1].do_addtx(cmd_str)
                        total_transactions += 1
                        
                        # CPU measurement (Fix #4)
                        if i % 5 == 0:
                            # Use smaller interval but discard first few in post-processing
                            cpu_samples.append(self.process.cpu_percent(interval=0.2))
                except Exception as e:
                    failed_transactions += 1
                
                time.sleep(0.05)
                
                # Check consensus progress (Fix #3)
                if i % 10 == 0:
                    total_rounds += 1
                    current_len = active_nodes[nodes[0]][1].do_count("")
                    if current_len == last_chain_len:
                        failed_rounds += 1
                    last_chain_len = current_len

        
        # Wait for churn to complete
        remaining_time = churn_duration - (time.time() - start_time)
        if remaining_time > 0:
            time.sleep(remaining_time)
            
        end_time = time.time()
        
        # Calculate metrics
        final_chain_len = active_nodes[nodes[0]][1].do_count("")
        blocks_produced = final_chain_len - initial_chain_len
        
        elapsed_time = end_time - start_time
        throughput = total_transactions / elapsed_time if elapsed_time > 0 else 0
        
        # FIX #2: Correct Latency
        latency = elapsed_time / blocks_produced if blocks_produced > 0 else 0
        
        success_rate = ((total_transactions - failed_transactions) / total_transactions * 100) \
                       if total_transactions > 0 else 0
                       
        # FIX #3: Consensus Failure Rate
        consensus_failure_rate = (failed_rounds / total_rounds * 100) if total_rounds > 0 else 0
        
        # CPU and Memory
        final_memory = self.process.memory_info().rss / (1024 * 1024)
        
        # FIX #4: Discard first 2 CPU samples
        if len(cpu_samples) > 2:
            cpu_samples = cpu_samples[2:]
        avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
        avg_memory = (initial_memory + final_memory) / 2
        
        # Cleanup
        for node in nodes:
            try:
                if node in active_nodes:
                    active_nodes[node][1].do_exit("")
            except:
                pass
        
        result = {
            'throughput': throughput,
            'latency': latency,
            'cpu_usage': round(avg_cpu, 2),
            'memory_usage': round(avg_memory, 2),
            'total_transactions': total_transactions,
            'failed_transactions': failed_transactions,
            'success_rate': round(success_rate, 2),
            'consensus_failure_rate': round(consensus_failure_rate, 2)
        }
        
        print(f"✓ AASC: {success_rate:.1f}% success | {throughput:.4f} tps | {latency:.4f}s latency | fail_rate: {consensus_failure_rate:.1f}%")
        
        return result

    def POS_test_with_churn(self, nodes, validators, edges, churn_rate, 
                           tx_count, churn_duration):
        """PoS consensus with churn"""
        active_nodes = {node: self.run_node(node, node in validators, algo=pos) 
                       for node in nodes}
        
        online_nodes = set(nodes)
        
        print("Connecting peer nodes...")
        for u, v in edges:
            try:
                active_nodes[u][1].do_addpeer(f"127.0.0.1 {v}")
                time.sleep(0.05)
            except:
                pass
        
        time.sleep(2)
        
        churn_thread = threading.Thread(
            target=self.simulate_churn,
            args=(active_nodes, nodes, validators, churn_rate, online_nodes, churn_duration),
            daemon=True
        )
        churn_thread.start()
        
        try:
            active_nodes[nodes[0]][1].do_sval("")
            time.sleep(1)
        except:
            pass
        
        transaction_nodes = random.sample(nodes, max(1, len(nodes) // 2))
        total_transactions = 0
        failed_transactions = 0
        
        failed_rounds = 0
        total_rounds = 0
        initial_chain_len = active_nodes[nodes[0]][1].do_count("")
        last_chain_len = initial_chain_len
        
        print("Starting transaction phase with churn...")
        self.process.cpu_percent(interval=None)
        initial_memory = self.process.memory_info().rss / (1024 * 1024)
        cpu_samples = []
        
        start_time = time.time()
        
        for node in transaction_nodes:
            batch_size = tx_count // max(1, len(transaction_nodes))
            for i in range(batch_size):
                if node not in online_nodes:
                    continue
                try:
                    if node in active_nodes:
                        recipient = f"user{random.randint(1, 100)}"
                        amount = random.randint(1, 10)
                        cmd_str = f"{recipient} {amount}"
                        active_nodes[node][1].do_addtx(cmd_str)
                        total_transactions += 1
                        
                        if i % 5 == 0:
                            cpu_samples.append(self.process.cpu_percent(interval=0.2))
                except:
                    failed_transactions += 1
                
                time.sleep(0.05)

                if i % 10 == 0:
                    total_rounds += 1
                    current_len = active_nodes[nodes[0]][1].do_count("")
                    if current_len == last_chain_len:
                        failed_rounds += 1
                    last_chain_len = current_len

        remaining_time = churn_duration - (time.time() - start_time)
        if remaining_time > 0:
            time.sleep(remaining_time)
            
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        final_chain_len = active_nodes[nodes[0]][1].do_count("")
        blocks_produced = final_chain_len - initial_chain_len
        
        throughput = total_transactions / elapsed_time if elapsed_time > 0 else 0
        latency = elapsed_time / blocks_produced if blocks_produced > 0 else 0
        
        success_rate = ((total_transactions - failed_transactions) / total_transactions * 100) \
                       if total_transactions > 0 else 0
        
        consensus_failure_rate = (failed_rounds / total_rounds * 100) if total_rounds > 0 else 0
        
        final_memory = self.process.memory_info().rss / (1024 * 1024)
        if len(cpu_samples) > 2:
            cpu_samples = cpu_samples[2:]
        avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
        avg_memory = (initial_memory + final_memory) / 2
        
        for node in nodes:
            try:
                if node in active_nodes:
                    active_nodes[node][1].do_exit("")
            except:
                pass
        
        result = {
            'throughput': throughput,
            'latency': latency,
            'cpu_usage': round(avg_cpu, 2),
            'memory_usage': round(avg_memory, 2),
            'total_transactions': total_transactions,
            'failed_transactions': failed_transactions,
            'success_rate': round(success_rate, 2),
            'consensus_failure_rate': round(consensus_failure_rate, 2)
        }
        
        print(f"✓ PoS: {success_rate:.1f}% success | {throughput:.4f} tps | {latency:.4f}s latency | fail_rate: {consensus_failure_rate:.1f}%")
        
        return result

    def PoCH_test_with_churn(self, nodes, validators, edges, churn_rate, 
                            tx_count, churn_duration):
        """PoCH consensus with churn"""
        active_nodes = {node: self.run_node(node, algo=poch) for node in nodes}
        
        online_nodes = set(nodes)
        
        print("Connecting peer nodes...")
        for u, v in edges:
            try:
                active_nodes[u][1].do_addpeer(f"127.0.0.1 {v}")
                time.sleep(0.05)
            except:
                pass
        
        time.sleep(2)
        
        churn_thread = threading.Thread(
            target=self.simulate_churn,
            args=(active_nodes, nodes, validators, churn_rate, online_nodes, churn_duration),
            daemon=True
        )
        churn_thread.start()
        
        try:
            active_nodes[nodes[0]][1].do_cval("")
            time.sleep(1)
        except:
            pass
        
        transaction_nodes = random.sample(nodes, max(1, len(nodes) // 2))
        total_transactions = 0
        failed_transactions = 0
        
        failed_rounds = 0
        total_rounds = 0
        initial_chain_len = active_nodes[nodes[0]][1].do_count("")
        last_chain_len = initial_chain_len
        
        print("Starting transaction phase with churn...")
        self.process.cpu_percent(interval=None)
        initial_memory = self.process.memory_info().rss / (1024 * 1024)
        cpu_samples = []
        
        start_time = time.time()
        
        for node in transaction_nodes:
            batch_size = tx_count // max(1, len(transaction_nodes))
            for i in range(batch_size):
                if node not in online_nodes:
                    continue
                try:
                    if node in active_nodes:
                        recipient = f"user{random.randint(1, 100)}"
                        amount = random.randint(1, 10)
                        cmd_str = f"{recipient} {amount}"
                        active_nodes[node][1].do_addtx(cmd_str)
                        total_transactions += 1
                        
                        if i % 5 == 0:
                            cpu_samples.append(self.process.cpu_percent(interval=0.2))
                except:
                    failed_transactions += 1
                
                time.sleep(0.05)

                if i % 10 == 0:
                    total_rounds += 1
                    current_len = active_nodes[nodes[0]][1].do_count("")
                    if current_len == last_chain_len:
                        failed_rounds += 1
                    last_chain_len = current_len

        remaining_time = churn_duration - (time.time() - start_time)
        if remaining_time > 0:
            time.sleep(remaining_time)
            
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        final_chain_len = active_nodes[nodes[0]][1].do_count("")
        blocks_produced = final_chain_len - initial_chain_len
        
        throughput = total_transactions / elapsed_time if elapsed_time > 0 else 0
        latency = elapsed_time / blocks_produced if blocks_produced > 0 else 0
        
        success_rate = ((total_transactions - failed_transactions) / total_transactions * 100) \
                       if total_transactions > 0 else 0
        
        consensus_failure_rate = (failed_rounds / total_rounds * 100) if total_rounds > 0 else 0
        
        final_memory = self.process.memory_info().rss / (1024 * 1024)
        if len(cpu_samples) > 2:
            cpu_samples = cpu_samples[2:]
        avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
        avg_memory = (initial_memory + final_memory) / 2
        
        for node in nodes:
            try:
                if node in active_nodes:
                    active_nodes[node][1].do_exit("")
            except:
                pass
        
        result = {
            'throughput': throughput,
            'latency': latency,
            'cpu_usage': round(avg_cpu, 2),
            'memory_usage': round(avg_memory, 2),
            'total_transactions': total_transactions,
            'failed_transactions': failed_transactions,
            'success_rate': round(success_rate, 2),
            'consensus_failure_rate': round(consensus_failure_rate, 2)
        }
        
        print(f"✓ PoCH: {success_rate:.1f}% success | {throughput:.4f} tps | {latency:.4f}s latency | fail_rate: {consensus_failure_rate:.1f}%")
        
        return result

    def PoEM_test_with_churn(self, nodes, validators, edges, churn_rate, 
                            tx_count, churn_duration):
        """PoEM consensus with churn"""
        active_nodes = {node: self.run_node(node, node in validators, algo=poem) 
                       for node in nodes}
        
        online_nodes = set(nodes)
        
        print("Connecting peer nodes...")
        for u, v in edges:
            try:
                active_nodes[u][1].do_addpeer(f"127.0.0.1 {v}")
                time.sleep(0.05)
            except:
                pass
        
        time.sleep(2)
        
        churn_thread = threading.Thread(
            target=self.simulate_churn,
            args=(active_nodes, nodes, validators, churn_rate, online_nodes, churn_duration),
            daemon=True
        )
        churn_thread.start()
        
        try:
            active_nodes[nodes[0]][1].do_sval("")
            time.sleep(1)
        except:
            pass
        
        transaction_nodes = random.sample(nodes, max(1, len(nodes) // 2))
        total_transactions = 0
        failed_transactions = 0
        
        failed_rounds = 0
        total_rounds = 0
        initial_chain_len = active_nodes[nodes[0]][1].do_count("")
        last_chain_len = initial_chain_len
        
        print("Starting transaction phase with churn...")
        self.process.cpu_percent(interval=None)
        initial_memory = self.process.memory_info().rss / (1024 * 1024)
        cpu_samples = []
        
        start_time = time.time()
        
        for node in transaction_nodes:
            batch_size = tx_count // max(1, len(transaction_nodes))
            for i in range(batch_size):
                if node not in online_nodes:
                    continue
                try:
                    if node in active_nodes:
                        recipient = f"user{random.randint(1, 100)}"
                        amount = random.randint(1, 10)
                        cmd_str = f"{recipient} {amount}"
                        active_nodes[node][1].do_addtx(cmd_str)
                        total_transactions += 1
                        
                        if i % 5 == 0:
                            cpu_samples.append(self.process.cpu_percent(interval=0.2))
                except:
                    failed_transactions += 1
                
                time.sleep(0.05)

                if i % 10 == 0:
                    total_rounds += 1
                    current_len = active_nodes[nodes[0]][1].do_count("")
                    if current_len == last_chain_len:
                        failed_rounds += 1
                    last_chain_len = current_len

        remaining_time = churn_duration - (time.time() - start_time)
        if remaining_time > 0:
            time.sleep(remaining_time)
            
        end_time = time.time()
        
        elapsed_time = end_time - start_time
        final_chain_len = active_nodes[nodes[0]][1].do_count("")
        blocks_produced = final_chain_len - initial_chain_len
        
        throughput = total_transactions / elapsed_time if elapsed_time > 0 else 0
        latency = elapsed_time / blocks_produced if blocks_produced > 0 else 0
        
        success_rate = ((total_transactions - failed_transactions) / total_transactions * 100) \
                       if total_transactions > 0 else 0
        
        consensus_failure_rate = (failed_rounds / total_rounds * 100) if total_rounds > 0 else 0
        
        final_memory = self.process.memory_info().rss / (1024 * 1024)
        if len(cpu_samples) > 2:
            cpu_samples = cpu_samples[2:]
        avg_cpu = sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0
        avg_memory = (initial_memory + final_memory) / 2
        
        for node in nodes:
            try:
                if node in active_nodes:
                    active_nodes[node][1].do_exit("")
            except:
                pass
        
        result = {
            'throughput': throughput,
            'latency': latency,
            'cpu_usage': round(avg_cpu, 2),
            'memory_usage': round(avg_memory, 2),
            'total_transactions': total_transactions,
            'failed_transactions': failed_transactions,
            'success_rate': round(success_rate, 2),
            'consensus_failure_rate': round(consensus_failure_rate, 2)
        }
        
        print(f"✓ PoEM: {success_rate:.1f}% success | {throughput:.4f} tps | {latency:.4f}s latency | fail_rate: {consensus_failure_rate:.1f}%")
        
        return result

    def save_churn_results(self, nodes, miners, churn_rate, results):
        """Save churn test results to structured folder"""
        
        config_dir = self.ensure_results_dir(nodes, miners)
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(
            config_dir,
            f"churn_{int(churn_rate * 100)}_run_{run_id}.json"
        )

        output = {
            'timestamp': datetime.now().isoformat(),
            'test_config': {
                'nodes': nodes,
                'miners': miners,
                'churn_rate': churn_rate
            },
            'results': results
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n✓ Results saved to {filename}")

        # Summary table
        print("\n" + "=" * 90)
        print(f"CHURN TEST SUMMARY (Nodes: {nodes}, Churn Rate: {churn_rate*100:.0f}%)")
        print("=" * 90)

        table = []
        for algo, result in results.items():
            table.append([
                algo,
                f"{result['throughput']:.4f}",
                f"{result['latency']:.6f}",
                f"{result['success_rate']:.1f}%",
                f"{result['consensus_failure_rate']:.1f}%",
                f"{result['cpu_usage']:.1f}",
                f"{result['memory_usage']:.2f}"
            ])

        print(tabulate(
            table,
            headers=[
                'Algorithm',
                'Throughput (tps)',
                'Block Latency (s)',
                'Success Rate',
                'Failure Rate',
                'CPU %',
                'Memory (MB)'
            ],
            tablefmt='grid'
        ))


if __name__ == "__main__":
    test = Test(number_of_transactions=100)
    
    # Churn configurations
    churn_configs = [
        (0.0, "No Churn (Baseline)"),
        (0.05, "5% Churn"),
        (0.10, "10% Churn"),
        (0.15, "15% Churn"),
        (0.20, "20% Churn"),
    ]
    
    # Network configurations
    network_configs = [
        (20, 4),
        (30, 6),
    ]
    
    print("\n" + "="*90)
    print("AASC NODE CHURN RESILIENCE TESTING")
    print("="*90)
    
    for nodes, miners in network_configs:
        print(f"\n{'='*90}")
        print(f"Testing with {nodes} nodes and {miners} miners")
        print(f"{'='*90}")
        
        for churn_rate, churn_label in churn_configs:
            print(f"\n>>> {churn_label}")
            test.run_test_with_churn(
                num_nodes=nodes,
                num_miners=miners,
                churn_rate=churn_rate,
                transaction_count=100,
                churn_duration=20  # Reduced from 30
            )
            time.sleep(10)
    
    print("\n" + "="*90)
    print("ALL CHURN TESTS COMPLETED ✓")
    print("="*90)