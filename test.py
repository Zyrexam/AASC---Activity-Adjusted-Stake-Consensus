import threading
import time
import random
import poem_global as poem
import aasc as aasc
import pos as pos
import poch as poch
from tabulate import tabulate
import psutil

class Test:
    def __init__(self, test_type = 'throughput', number_of_transactions = 200):
        self.test_type = test_type
        self.number_of_transactions = number_of_transactions

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
            'nodes' : nodes,
            'validators' : validators,
            'edges' : edges
        }

        with open('network.txt', 'a') as f:
            print(network, file = f)

        return nodes, validators, edges
    
    def run_node(self, port, is_validator = None, address = '127.0.0.1', algo = aasc):
        if is_validator is None:
            node = algo.Node(address, port)
        else:
            node = algo.Node(address, port, is_validator)

        cli = algo.NodeCLI(node)
        node_thread = threading.Thread(target=node.start, daemon=True)
        node_thread.start()
        
        # Small delay to stagger node startup and prevent simultaneous socket binding
        time.sleep(0.1)
        
        return node, cli
    
    def run_test(self, num_nodes, num_miners):
        """
        Run comparative experiments for consensus algorithms.
        Use different port ranges for each algorithm to avoid conflicts.
        """
        # Create network topology once (will be reused with different port ranges)
        _, validators_indices, edges_template = self.create_network(num_nodes, num_miners)
        
        print(f"Running test for {num_nodes} nodes and {num_miners} miners")

        # PoCH - Port range 7000-7999
        BASE_PORT = 7000
        nodes = [BASE_PORT + i for i in range(num_nodes)]
        validators = [BASE_PORT + i for i in validators_indices]
        edges = [(BASE_PORT + u - 7000, BASE_PORT + v - 7000) for u, v in edges_template]
        
        process = psutil.Process()
        initial_cpu = process.cpu_percent(interval=None)
        initial_memory = process.memory_info().rss

        poch_result = self.PoCH_test(nodes, validators, edges)

        final_cpu = process.cpu_percent(interval=None)
        final_memory = process.memory_info().rss
        cpu_usage_poch = final_cpu - initial_cpu
        memory_usage_poch = (final_memory - initial_memory) / (1024 * 1024)
        poch_result['cpu_usage'] = cpu_usage_poch
        poch_result['memory_usage'] = memory_usage_poch

        with open('checkpoint.txt', 'a') as f:
            print("TEST", file = f)
            print(poch_result, file = f)
        
        print("POCH Test Completed")
        time.sleep(10)  # Increased wait time for Windows to release ports

        # PoEM - Port range 8000-8999
        BASE_PORT = 8000
        nodes = [BASE_PORT + i for i in range(num_nodes)]
        validators = [nodes[i] for i, orig in enumerate(range(7000, 7000 + num_nodes)) if orig in validators_indices]
        edges = [(BASE_PORT + (u - 7000), BASE_PORT + (v - 7000)) for u, v in edges_template]
        
        process = psutil.Process()
        initial_cpu = process.cpu_percent(interval=None)
        initial_memory = process.memory_info().rss

        poem_result = self.PoEM_test(nodes, validators, edges)

        final_cpu = process.cpu_percent(interval=None)
        final_memory = process.memory_info().rss
        cpu_usage_poem = final_cpu - initial_cpu
        memory_usage_poem = (final_memory - initial_memory) / (1024 * 1024)
        poem_result['cpu_usage'] = cpu_usage_poem
        poem_result['memory_usage'] = memory_usage_poem

        with open('checkpoint.txt', 'a') as f:
            print(poem_result, file = f)

        print("PoEM Test Completed")
        time.sleep(10)  # Increased wait time for Windows to release ports

        # AASC - Port range 9000-9999
        BASE_PORT = 9000
        nodes = [BASE_PORT + i for i in range(num_nodes)]
        validators = [nodes[i] for i, orig in enumerate(range(7000, 7000 + num_nodes)) if orig in validators_indices]
        edges = [(BASE_PORT + (u - 7000), BASE_PORT + (v - 7000)) for u, v in edges_template]

        process = psutil.Process()
        initial_cpu = process.cpu_percent(interval=None)
        initial_memory = process.memory_info().rss

        aasc_result = self.AASC_test(nodes, validators, edges)

        final_cpu = process.cpu_percent(interval=None)
        final_memory = process.memory_info().rss
        cpu_usage_aasc = final_cpu - initial_cpu
        memory_usage_aasc = (final_memory - initial_memory) / (1024 * 1024)
        aasc_result['cpu_usage'] = cpu_usage_aasc
        aasc_result['memory_usage'] = memory_usage_aasc

        with open('checkpoint.txt', 'a') as f:
            print(aasc_result, file = f)

        print("AASC Test Completed")
        time.sleep(10)  # Increased wait time for Windows to release ports

        # POS - Port range 10000-10999
        BASE_PORT = 10000
        nodes = [BASE_PORT + i for i in range(num_nodes)]
        validators = [nodes[i] for i, orig in enumerate(range(7000, 7000 + num_nodes)) if orig in validators_indices]
        edges = [(BASE_PORT + (u - 7000), BASE_PORT + (v - 7000)) for u, v in edges_template]

        process = psutil.Process()
        initial_cpu = process.cpu_percent(interval=None)
        initial_memory = process.memory_info().rss

        pos_result = self.POS_test(nodes, validators, edges)

        final_cpu = process.cpu_percent(interval=None)
        final_memory = process.memory_info().rss
        cpu_usage_pos = final_cpu - initial_cpu
        memory_usage_pos = (final_memory - initial_memory) / (1024 * 1024)
        pos_result['cpu_usage'] = cpu_usage_pos
        pos_result['memory_usage'] = memory_usage_pos

        with open('checkpoint.txt', 'a') as f:
            print(pos_result, file = f)
            print(file = f)

        print("POS Test Completed")
    
        result = {
            'PoS (Baseline)' : pos_result,
            'PoCH (Baseline)' : poch_result,  # Commented out - not running PoCH
            'AASC (Proposed)' : aasc_result,
            'PoEM (Reference)' : poem_result,
        }

        table = []
        for algo, result in result.items():
            table.append([algo, result['throughput'], result['latency'], result['cpu_usage'], result['memory_usage']])
        
        with open('result.txt', 'a') as f:
            print(f"Number of Nodes: {num_nodes}, Number of Miners: {num_miners}, Number of transaction: {self.number_of_transactions}", file = f)
            print(f"Test Results for {num_nodes} nodes and {num_miners} miners", file = f)
            print("-" * 50, file = f)
            print(tabulate(table, headers = ['Algorithm', 'Throughput', 'Latency', 'CPU Usage', 'Memory Usage']), file = f)
            print("-" * 50, file = f)
            print("\n\n", file = f)

        print("DONE")
    
    def PoCH_test(self, nodes, validators, edges):
        active_nodes = {node : self.run_node(node, algo = poch) for node in nodes}
        print("PoCH")
        print("Attempting to connect nodes")
        k=0
        for u, v in edges:
            active_nodes[u][1].do_addpeer(f"127.0.0.1 {v}")
            k+=1
            print(f"{k}/{len(edges)}", end='\r')
            time.sleep(0.25)

        time.sleep(2)
        print("Collecting IDs")
        active_nodes[nodes[0]][1].do_cval("")
        time.sleep(2)
        transaction_nodes = random.sample(nodes, len(nodes) // 2)
        transaction_per_nodes = self.number_of_transactions//len(transaction_nodes)
        total_transactions = 0
        print("Starting transactions")
        start_time = time.time()
        for node in transaction_nodes:
            for _ in range(transaction_per_nodes):
                try:
                    recipient = f"user{random.randint(1, 100)}"
                    amount = random.randint(1, 10)
                    cmd_str = f"{recipient} {amount}"
                    active_nodes[node][1].do_addtx(cmd_str)
                    total_transactions += 1
                    print(f"Transaction {total_transactions} completed", end = '\r')
                except Exception as e:
                    pass
        end_time = time.time()
        total_time = end_time - start_time
        throughput = total_transactions / total_time if total_time > 0 else 0
        latency = total_time / total_transactions if total_transactions > 0 else 0

        result = {
            'throughput' : throughput,
            'latency' : latency
        }

        time.sleep(2)
        for node in nodes:
            active_nodes[node][1].do_exit("")

        return result

    def AASC_test(self, nodes, validators, edges):
        print("AASC")
        active_nodes = {node : self.run_node(node, node in validators, algo = aasc) for node in nodes}
        print("Attempting to connect nodes")
        k = 1
        total_edges = len(edges)
        for u, v in edges:
            active_nodes[u][1].do_addpeer(f"127.0.0.1 {v}")
            print(f"{k}/{total_edges}", end='\r')
            k += 1
            time.sleep(0.15)
        
        time.sleep(2)
        print("Collecting validators")
        active_nodes[nodes[0]][1].do_sval("")
        time.sleep(2)
        transaction_nodes = random.sample(nodes, len(nodes) // 2)
        transaction_per_nodes = self.number_of_transactions//len(transaction_nodes)
        total_transactions = 0
        print("Starting transactions")
        start_time = time.time()
        for node in transaction_nodes:
            for _ in range(transaction_per_nodes):
                try:
                    recipient = f"user{random.randint(1, 100)}"
                    amount = random.randint(1, 10)
                    cmd_str = f"{recipient} {amount}"
                    active_nodes[node][1].do_addtx(cmd_str)
                    # REMOVED: time.sleep(1) - This was causing timeouts
                    total_transactions += 1
                    print(f"Transaction {total_transactions} completed", end = '\r')
                except Exception as e:
                    pass
        end_time = time.time()

        total_time = end_time - start_time
        throughput = total_transactions / total_time if total_time > 0 else 0
        latency = total_time / total_transactions if total_transactions > 0 else 0

        result = {
            'throughput' : throughput,
            'latency' : latency
        }

        time.sleep(2)
        for node in nodes:
            active_nodes[node][1].do_exit("")

        return result


    def PoEM_test(self, nodes, validators, edges):
        print("PoEM")
        active_nodes = {node : self.run_node(node, node in validators, algo = poem) for node in nodes}
        print("Attempting to connect nodes")
        k = 0
        for u, v in edges:
            active_nodes[u][1].do_addpeer(f"127.0.0.1 {v}")
            k+=1
            print(f"{k}/{len(edges)}", end='\r')
            time.sleep(0.25)

        time.sleep(2)
        print("Collecting validators")
        active_nodes[nodes[0]][1].do_sval("")
        time.sleep(2)

        transaction_nodes = random.sample(nodes, len(nodes) // 2)
        transaction_per_nodes = self.number_of_transactions//len(transaction_nodes)
        total_transactions = 0
        print("Starting transactions")
        start_time = time.time()
        for node in transaction_nodes:
            for _ in range(transaction_per_nodes):
                try:
                    recipient = f"user{random.randint(1, 100)}"
                    amount = random.randint(1, 10)
                    cmd_str = f"{recipient} {amount}"
                    active_nodes[node][1].do_addtx(cmd_str)
                    # REMOVED: time.sleep(1) - This was causing timeouts
                    total_transactions += 1
                    print(f"Transaction {total_transactions} completed", end = '\r')
                except Exception as e:
                    pass
        end_time = time.time()
        total_time = end_time - start_time
        throughput = total_transactions / total_time if total_time > 0 else 0
        latency = total_time / total_transactions if total_transactions > 0 else 0

        result = {
            'throughput' : throughput,
            'latency' : latency
        }

        time.sleep(2)
        for node in nodes:
            active_nodes[node][1].do_exit("")

        return result

    def POS_test(self, nodes, validators, edges):
        print("POS")
        active_nodes = {node : self.run_node(node, node in validators, algo = pos) for node in nodes}
        print("Attempting to connect nodes")
        k=0
        for u, v in edges:
            active_nodes[u][1].do_addpeer(f"127.0.0.1 {v}")
            k+=1
            print(f"{k}/{len(edges)}", end='\r')
            time.sleep(0.25)
        
        time.sleep(2)
        print("Collecting validators")
        active_nodes[nodes[0]][1].do_sval("")
        time.sleep(2)

        transaction_nodes = random.sample(nodes, len(nodes) // 2)
        transaction_per_nodes = self.number_of_transactions//len(transaction_nodes)
        total_transactions = 0
        print("Starting transactions")
        start_time = time.time()
        for node in transaction_nodes:
            for _ in range(transaction_per_nodes):
                try:
                    recipient = f"user{random.randint(1, 100)}"
                    amount = random.randint(1, 10)
                    cmd_str = f"{recipient} {amount}"
                    active_nodes[node][1].do_addtx(cmd_str)
                    total_transactions += 1
                    print(f"Transaction {total_transactions} completed", end = '\r')
                except Exception as e:
                    pass
        end_time = time.time()
        total_time = end_time - start_time
        throughput = total_transactions / total_time if total_time > 0 else 0
        latency = total_time / total_transactions if total_transactions > 0 else 0

        result = {
            'throughput' : throughput,
            'latency' : latency
        }

        time.sleep(2)
        for node in nodes:
            active_nodes[node][1].do_exit("")

        return result


            
# if __name__ == "__main__":
#     test = Test(number_of_transactions=100)
#     test.run_test(20, 4)


# if __name__ == "__main__":
#     test = Test(number_of_transactions=500)
#     # without PoCH
#     # (nodes, miners)
#     experiments = [
#         # (10, 2),
#         # (20, 4),
#         # (30, 6),
#         # (40, 8),
#         (50, 10),
#     ]

#     REPEATS = 1

#     for r in range(REPEATS):
#         print(f"\n================ RUN {r+1}/{REPEATS} ================\n")
#         for nodes, miners in experiments:
#             test.run_test(nodes, miners)
#             time.sleep(50)


if __name__ == "__main__":
    test = Test(number_of_transactions=100)

    # (nodes, miners)
    experiments = [
        # (20, 10),
        # (30, 10),
        # (40, 10),
        # (50, 10),
        # (70, 14),
        # (100, 20),
    ]

    REPEATS = 1

    for r in range(REPEATS):
        print(f"\n================ RUN {r+1}/{REPEATS} ================\n")
        for nodes, miners in experiments:
            test.run_test(nodes, miners)
            time.sleep(10)
