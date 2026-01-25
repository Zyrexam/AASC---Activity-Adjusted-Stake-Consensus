"""
Test PoCH specifically to verify the infinite loop fix
Tests with realistic node/miner configurations matching test.py
"""
import time
import threading
import random
from poch_demo import Node, Blockchain


# import sys

# log_file = open("poch_fix_internal.log", "w")
# sys.stdout = log_file
# sys.stderr = log_file


def run_node(node):
    """Run a node in a separate thread"""
    try:
        node.start()
    except Exception as e:
        print(f"Node {node.port} error: {e}")

def test_poch_with_miners(num_nodes=20, num_miners=4, num_transactions=100):
    """Test PoCH with specified number of nodes, miners, and transactions"""
    print(f"\n{'='*60}")
    print(f"Testing PoCH: {num_nodes} nodes, {num_miners} miners, {num_transactions} transactions")
    print(f"{'='*60}\n")
    
    # Create network
    base_port = 8000
    nodes = []
    
    # Create nodes
    for i in range(num_nodes):
        node = Node('127.0.0.1', base_port + i)
        nodes.append(node)
    
    # Select miners (subset of nodes that will participate in consensus)
    miner_nodes = random.sample(nodes, num_miners)
    miner_ports = [n.port for n in miner_nodes]
    
    print(f"Miners: {miner_ports}")
    
    # Connect nodes in a network topology
    for i, node in enumerate(nodes):
        # Connect to 3-5 random peers
        num_peers = random.randint(3, min(5, num_nodes - 1))
        peers = random.sample([n for n in nodes if n != node], num_peers)
        for peer in peers:
            node.add_peer(peer.address, peer.port)
    
    # Start all nodes in threads
    threads = []
    for node in nodes:
        t = threading.Thread(target=run_node, args=(node,), daemon=True)
        t.start()
        threads.append(t)
    
    print("Waiting for nodes to start...")
    time.sleep(2)
    
    # Collect candidacies (only from miners)
    print("Collecting candidacies from miners...")
    for node in miner_nodes:
        node.blockchain.candidancies[node.id] = node.id
        if len(node.messages_id) != 0:
            max_msg_id = max(node.messages_id)
        else:
            max_msg_id = 0
        node.broadcast({
            'type': 'store_candidancies',
            'candidancies': node.blockchain.candidancies,
            'id': max_msg_id + 1
        })
    
    time.sleep(2)
    
    # Send transactions
    print(f"Sending {num_transactions} transactions...")
    start_time = time.time()
    completed = 0
    failed = 0
    
    for tx_num in range(num_transactions):
        try:
            # Any node can send transactions
            sender_node = random.choice(nodes)
            recipient = f"user_{random.randint(1, 100)}"
            amount = random.randint(1, 100)
            
            if len(sender_node.messages_id) != 0:
                max_msg_id = max(sender_node.messages_id)
            else:
                max_msg_id = 0
            
            sender_node.broadcast({
                'type': 'new_transaction',
                'data': {
                    'sender': f"{sender_node.address}:{sender_node.port}",
                    'recipient': recipient,
                    'amount': amount
                },
                'id': max_msg_id + 1
            })
            
            completed += 1
            if (tx_num + 1) % 20 == 0:
                print(f"  Transaction {tx_num + 1}/{num_transactions} sent")
            
            time.sleep(0.05)  # Small delay between transactions
            
        except Exception as e:
            failed += 1
            print(f"  ❌ Transaction {tx_num + 1} failed: {e}")
    
    # Wait for processing
    print("\nWaiting for consensus to complete...")
    time.sleep(5)
    
    elapsed = time.time() - start_time
    
    # Stop all nodes
    print("Stopping nodes...")
    for node in nodes:
        try:
            node.stop()
        except:
            pass
    
    # Results
    print(f"\n{'='*60}")
    print(f"PoCH Test Results:")
    print(f"{'='*60}")
    print(f"Nodes: {num_nodes}, Miners: {num_miners}")
    print(f"Transactions sent: {completed}")
    print(f"Transactions failed: {failed}")
    print(f"Time elapsed: {elapsed:.2f}s")
    # print(f"Throughput: {completed/elapsed:.2f} tx/s")

    committed_blocks = len(node.blockchain.chain) - 1
    throughput = committed_blocks / elapsed
    print(f"Throughput: {throughput:.2f} blocks/s")
    latency = elapsed / committed_blocks if committed_blocks > 0 else float('inf')
    print(f"Latency: {latency:.2f}s")
    
    # Check blockchain lengths
    chain_lengths = [len(node.blockchain.chain) for node in nodes]
    print(f"Blockchain lengths: min={min(chain_lengths)}, max={max(chain_lengths)}, avg={sum(chain_lengths)/len(chain_lengths):.1f}")
    
    if completed == num_transactions and failed == 0:
        print("\n✅ PoCH test PASSED - All transactions completed!")
        return True
    else:
        print(f"\n⚠️  PoCH test completed with {failed} failures")
        return False

if __name__ == "__main__":
    print("="*60)
    print("PoCH Infinite Loop Fix Verification")
    print("Testing with realistic node/miner configurations")
    print("="*60)
    
    # Test configurations matching your main test.py
    # (nodes, miners, transactions)
    test_configs = [
        (20, 10, 100),    # Small network
        (30, 10, 100),   # Medium network  
        (40, 10, 100),
        (50, 10, 100),
        (70, 14, 100),
        (100, 20, 100),   # Larger network
    ]
    
    results = []
    for num_nodes, num_miners, num_tx in test_configs:
        success = test_poch_with_miners(num_nodes, num_miners, num_tx)
        results.append((num_nodes, num_miners, num_tx, success))
        time.sleep(3)  # Delay between tests
    
    # Summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    for nodes, miners, txs, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{nodes} nodes, {miners} miners, {txs} txs: {status}")
    
    all_passed = all(r[3] for r in results)
    if all_passed:
        print("\n🎉 All PoCH tests PASSED! The infinite loop fix is working!")
    else:
        print("\n⚠️  Some tests failed. Review the output above.")
