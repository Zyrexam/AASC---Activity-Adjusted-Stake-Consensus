import threading
import time
import random
import json
from datetime import datetime
from tabulate import tabulate


class ChurnTest:
    def __init__(self, number_of_transactions=100):
        self.number_of_transactions = number_of_transactions

    # --------------------------------------------------
    # Network setup
    # --------------------------------------------------
    def create_network(self, num_nodes, num_miners):
        nodes = [7000 + i for i in range(num_nodes)]
        validators = random.sample(nodes, num_miners)

        edges = []
        shuffled = nodes[:]
        random.shuffle(shuffled)
        for i in range(1, len(shuffled)):
            edges.append((shuffled[i], shuffled[random.randint(0, i - 1)]))

        return nodes, validators, edges

    # --------------------------------------------------
    # Node launcher (algorithm-aware)
    # --------------------------------------------------
    def run_node(self, port, is_validator, algo):
        try:
            # PoCH nodes do NOT take validator flag
            if algo.__name__.lower() == "poch":
                node = algo.Node("127.0.0.1", port)
            else:
                node = algo.Node("127.0.0.1", port, is_validator)

            cli = algo.NodeCLI(node)
            t = threading.Thread(target=node.start, daemon=True)
            t.start()
            return node, cli

        except Exception as e:
            print(f"Failed to start node {port}: {e}")
            return None, None

    # --------------------------------------------------
    # REAL churn: nodes are removed from active set
    # --------------------------------------------------
    def simulate_churn(self, active_nodes, validators,
                       churn_rate, duration, lock, algo):
        """
        churn_rate = probability per second that ONE node fails
        """
        start = time.time()
        churn_events = 0

        while time.time() - start < duration:
            time.sleep(1)

            if random.random() < churn_rate:
                with lock:
                    online = list(active_nodes.keys())

                if len(online) <= 1:
                    continue

                victim = random.choice(online)

                with lock:
                    try:
                        active_nodes[victim][1].do_exit("")
                    except:
                        pass
                    del active_nodes[victim]

                churn_events += 1
                print(f"[CHURN] Node {victim} removed")

        return churn_events

    # --------------------------------------------------
    # Run one algorithm
    # --------------------------------------------------
    def run_algorithm(self, algo_name, nodes, validators, edges,
                      churn_rate, tx_count, churn_duration):

        print(f"\n[TEST] {algo_name}")

        if algo_name == "AASC":
            import aasc as algo
        elif algo_name == "PoS":
            import pos as algo
        elif algo_name == "PoCH":
            import poch as algo
        elif algo_name == "PoEM":
            import poem_global as algo
        else:
            raise ValueError("Unknown algorithm")

        active_nodes = {}
        lock = threading.Lock()

        # Start nodes
        for p in nodes:
            is_val = p in validators
            node, cli = self.run_node(p, is_val, algo)
            if cli:
                active_nodes[p] = (node, cli)

        if len(active_nodes) == 0:
            raise RuntimeError("No nodes started")

        # Connect peers
        for u, v in edges:
            if u in active_nodes and v in active_nodes:
                try:
                    active_nodes[u][1].do_addpeer(f"127.0.0.1 {v}")
                except:
                    pass

        time.sleep(2)

        # Trigger validation
        first = list(active_nodes.keys())[0]
        cli = active_nodes[first][1]
        if hasattr(cli, "do_sval"):
            cli.do_sval("")
        elif hasattr(cli, "do_cval"):
            cli.do_cval("")

        # Start churn thread
        churn_thread = threading.Thread(
            target=self.simulate_churn,
            args=(active_nodes, validators, churn_rate,
                  churn_duration, lock, algo),
            daemon=True
        )
        churn_thread.start()

        # Transaction sending
        start_time = time.time()
        sent = 0
        failed = 0

        for _ in range(tx_count):
            with lock:
                online = list(active_nodes.keys())
            if not online:
                failed += 1
                continue

            sender = random.choice(online)
            try:
                active_nodes[sender][1].do_addtx(
                    f"user{random.randint(1,100)} {random.randint(1,10)}"
                )
                sent += 1
            except:
                failed += 1

            time.sleep(0.05)

        time.sleep(2)
        elapsed = time.time() - start_time

        # Cleanup
        with lock:
            for p in list(active_nodes.keys()):
                try:
                    active_nodes[p][1].do_exit("")
                except:
                    pass

        success_rate = ((sent - failed) / sent * 100) if sent else 0

        return {
            "throughput": round(sent / elapsed, 4),
            "avg_tx_submission_time": round(elapsed / sent, 4) if sent else 0,
            "total_transactions": sent,
            "failed_transactions": failed,
            "success_rate": round(success_rate, 2),
        }

    # --------------------------------------------------
    # Run full experiment
    # --------------------------------------------------
    def run_test(self, num_nodes, num_miners, churn_rate, tx_count, duration):
        nodes, validators, edges = self.create_network(num_nodes, num_miners)

        print("\n" + "=" * 80)
        print(f"CHURN TEST | Nodes={num_nodes} | Miners={num_miners} | Churn={churn_rate}")
        print("=" * 80)

        results = {}
        for algo in ["AASC", "PoS", "PoCH", "PoEM"]:
            try:
                results[algo] = self.run_algorithm(
                    algo, nodes, validators, edges,
                    churn_rate, tx_count, duration
                )
            except Exception as e:
                results[algo] = {"error": str(e)}

            time.sleep(5)

        self.save_results(num_nodes, num_miners, churn_rate, results)
        return results

    # --------------------------------------------------
    # Save
    # --------------------------------------------------     
        
    def save_results(self, nodes, miners, churn_rate, results):
        """
        Save results in structured folder:
        node_churn_results/<nodes>nodes_<miners>miners/churn_<rate>.json
        """

        import os

        base_dir = "node_churn_results"
        config_dir = os.path.join(base_dir, f"{nodes}nodes_{miners}miners")
        os.makedirs(config_dir, exist_ok=True)

        filename = os.path.join(
            config_dir,
            f"churn_{int(churn_rate * 100)}.json"
        )

        output = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "nodes": nodes,
                "miners": miners,
                "churn_rate": churn_rate
            },
            "results": results
        }

        with open(filename, "w") as f:
            json.dump(output, f, indent=2)

        print(f"\n✓ Results saved to {filename}")

        # Console summary (unchanged)
        table = []
        for algo, r in results.items():
            if "error" not in r:
                table.append([
                    algo,
                    r["success_rate"],
                    r["throughput"],
                    r["avg_tx_submission_time"],
                    r["total_transactions"]
                ])

        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        print(tabulate(
            table,
            headers=["Algorithm", "Success %", "TPS", "Avg TX Time", "TX Sent"],
            tablefmt="grid"
        ))



# --------------------------------------------------
# Main
# --------------------------------------------------
if __name__ == "__main__":
    test = ChurnTest()

    for churn in [0.0, 0.05, 0.10, 0.15, 0.20, 0.25]:
        test.run_test(
            num_nodes=20,
            num_miners=4,
            churn_rate=churn,
            tx_count=100,
            duration=20
        )
        time.sleep(10)
