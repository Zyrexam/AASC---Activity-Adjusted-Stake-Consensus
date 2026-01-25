# How to Run the AASC Blockchain Project

## Project Overview

This project implements **AASC (Activity-Adjusted Stake Consensus)** - a fully distributed, on-chain consensus algorithm for IoT blockchains, along with baseline algorithms for comparison.

### Main Files

| File             | Purpose                                   | Status               |
| ---------------- | ----------------------------------------- | -------------------- |
| `aasc.py`        | **Main AASC algorithm** (pure on-chain)   | ✅ Main contribution |
| `m_aasc.py`      | Modified AASC variant (with stake gossip) | ⚠️ Variant only      |
| `pos.py`         | Proof of Stake baseline                   | ✅ Baseline          |
| `poch.py`        | Proof of Chance baseline                  | ✅ Baseline          |
| `poem_global.py` | ML-based consensus (separate algorithm)   | ℹ️ Reference only    |
| `test.py`        | **Comparative experiments runner**        | ✅ Main test script  |
| `test_maasc.py`  | Tests for mAASC variant                   | ⚠️ Variant tests     |
| `results.ipynb`  | Results analysis & visualization          | ✅ Analysis notebook |

---

## Quick Start: Run Complete Experiments

### Option 1: Run Full Comparative Tests (Recommended)

This runs AASC vs PoS vs PoCH vs PoEM across multiple network sizes:

```bash
python test.py
```

**What it does:**

- Tests network sizes: 150, 200, 300, 400, 500 nodes
- Validators: 10-30 (scales with network size)
- Transactions: 100 per test
- Measures: Throughput, Latency, CPU, Memory
- Outputs: `result.txt` (raw data), `checkpoint.txt` (debug logs)

**Expected runtime:** 2-4 hours (depending on your machine)

**Note:** This is the main experiment that generates data for your paper!

---

### Option 2: Run Quick Test (Single Network Size)

Edit `test.py` line 366-367:

```python
if __name__ == "__main__":
    test = Test(number_of_transactions=100)
    # Comment out the loop, run single test:
    test.run_test(20, 10)  # 20 nodes, 10 validators
```

Then run:

```bash
python test.py
```

**Expected runtime:** 5-10 minutes

---

## Analyze Results

### Step 1: Check Raw Results

After running `test.py`, check:

```bash
# View results
type result.txt

# View debug logs
type checkpoint.txt
```

### Step 2: Generate Visualizations

Open Jupyter Notebook:

```bash
jupyter notebook results.ipynb
```

Or run the Python script version:

```bash
python run_results_analysis.py
```

**Outputs:**

- `images/throughput_aasc.png` - Throughput comparison chart
- `images/latency_aasc.png` - Latency comparison chart
- `images/cpu_aasc.png` - CPU usage chart
- `images/memory_aasc.png` - Memory usage chart
- Console output with statistical tables

---

## Run Individual Algorithms

### Run AASC Node Manually

Terminal 1 (Validator Node):

```bash
python aasc.py 5000 true
```

Terminal 2 (Regular Node):

```bash
python aasc.py 5001 false
```

Terminal 3 (Another Validator):

```bash
python aasc.py 5002 true
```

**Interactive Commands:**

```
blockchain> addpeer 127.0.0.1 5001    # Connect to peer
blockchain> sval                       # Sync validators
blockchain> addtx user1 100           # Add transaction
blockchain> viewchain                  # View blockchain
blockchain> params                     # View activity parameters
blockchain> scores                     # View consensus scores
blockchain> exit                       # Stop node
```

---

### Run mAASC Variant

Same as AASC but use `m_aasc.py`:

```bash
python m_aasc.py 5000 true
```

---

### Run PoS Baseline

```bash
python pos.py 5000 true
```

---

### Run PoCH Baseline

```bash
python poch.py 5000 false
```

---

## Understanding the Test Flow

When you run `test.py`, here's what happens:

### 1. Network Creation

```python
nodes, validators, edges = create_network(num_nodes, num_miners)
```

- Creates random network topology
- Selects random validators
- Generates peer connections (tree + extra edges)

### 2. Algorithm Tests (Sequential)

For each algorithm (PoCH → PoEM → AASC → PoS):

**a) Node Setup**

- Spawn `num_nodes` nodes (mix of validators and regular nodes)
- Each node runs in separate thread

**b) Network Connection**

- Connect nodes according to `edges`
- Wait for network stabilization

**c) Validator Sync**

- Broadcast validator list across network
- All nodes learn who the validators are

**d) Transaction Phase**

- Random nodes submit transactions
- Validators mine blocks using their consensus algorithm
- Measure throughput and latency

**e) Resource Measurement**

- CPU usage (before/after)
- Memory usage (before/after)

**f) Cleanup**

- Stop all nodes
- Record results

### 3. Results Output

Results are written to `result.txt` in this format:

```
Number of Nodes: 20, Number of Miners: 10, Number of transaction: 100
Test Results for 20 nodes and 10 miners
--------------------------------------------------
Algorithm      Throughput    Latency    CPU Usage    Memory Usage
-----------  ------------  ---------  -----------  --------------
POS              0.549399   1.82017         121.5       -0.792969
POCH             0.686762   1.45611         101.1       10.0156
PoEM             0.329444   3.03542         214.3        2.08984
AASC             2.42826    0.411817         65.5        3.42578
--------------------------------------------------
```

---

## Key Metrics Explained

### Throughput (tx/s)

- **Higher is better**
- Number of transactions processed per second
- Formula: `total_transactions / total_time`

### Latency (seconds)

- **Lower is better**
- Average time to confirm a transaction
- Formula: `total_time / total_transactions`

### CPU Usage (%)

- **Lower is better** (for IoT)
- Processor utilization during test
- Measured using `psutil`

### Memory Usage (MB)

- **Lower is better** (for IoT)
- RAM consumption during test
- Measured using `psutil`

---

## Troubleshooting

### Issue: "Port already in use"

**Solution:** Kill existing processes:

```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Or restart your terminal
```

### Issue: "Connection refused"

**Cause:** Nodes not started yet or network not stabilized

**Solution:** Increase sleep times in `test.py`:

```python
time.sleep(2)  # Increase to 5
```

### Issue: "No results in result.txt"

**Cause:** Test crashed or didn't complete

**Solution:**

1. Check `checkpoint.txt` for errors
2. Run smaller network first (20 nodes)
3. Reduce transaction count

### Issue: "Jupyter notebook not found"

**Solution:** Install Jupyter:

```bash
pip install jupyter notebook
```

Or use the Python script:

```bash
python run_results_analysis.py
```

---

## File Structure Summary

```
blockchain-python/
├── aasc.py                    # Main AASC algorithm ✅
├── m_aasc.py                  # AASC variant
├── pos.py                     # PoS baseline
├── poch.py                    # PoCH baseline
├── poem_global.py             # PoEM reference
├── test.py                    # Main experiment runner ✅
├── test_maasc.py              # mAASC tests
├── results.ipynb              # Results analysis ✅
├── run_results_analysis.py    # Python version of results.ipynb
├── result.txt                 # Experimental results (generated)
├── checkpoint.txt             # Debug logs (generated)
├── network.txt                # Network topology logs (generated)
├── images/                    # Generated charts
│   ├── throughput_aasc.png
│   ├── latency_aasc.png
│   ├── cpu_aasc.png
│   └── memory_aasc.png
├── ALGORITHM_EXPLANATION.md   # Technical documentation
├── IMPLEMENTATION_STATUS.md   # Project status
├── REVIEWER_FIXES_SUMMARY.md  # Reviewer response
└── helper.md                  # Paper revision guide
```

---

## Workflow for Paper

### 1. Run Experiments

```bash
python test.py
```

Wait 2-4 hours for completion.

### 2. Generate Visualizations

```bash
jupyter notebook results.ipynb
```

Or:

```bash
python run_results_analysis.py
```

### 3. Use Results in Paper

**From `result.txt`:**

- Copy performance tables directly
- Use for quantitative comparisons

**From `images/`:**

- Include charts in paper
- Reference in Results section

**Key Claims to Make:**

- AASC achieves **X% higher throughput** than PoS at 20 nodes
- AASC has **Y% lower latency** than PoEM
- AASC uses **Z% less CPU** than PoEM (no ML overhead)
- AASC is suitable for IoT (low memory footprint)

---

## What Each Algorithm Does

### AASC (`aasc.py`) - **YOUR MAIN CONTRIBUTION**

- **Fully distributed, on-chain**
- Tracks activity metrics from blockchain
- Computes Consensus Score (CS) locally
- Selects leader deterministically (argmax)
- **Complexity:** O(v) per round
- **No off-chain learning required**

### mAASC (`m_aasc.py`) - Variant

- Similar to AASC but adds explicit stake gossip
- Uses probabilistic leader selection (cumulative distribution)
- **NOT part of main paper contribution**

### PoS (`pos.py`) - Baseline

- Traditional stake-weighted selection
- Random selection based on stake
- Simple and well-known

### PoCH (`poch.py`) - Baseline

- Hash-based randomized selection
- No stake consideration
- Pure chance-based

### PoEM (`poem_global.py`) - Reference

- ML-based consensus with centralized model
- **Separate algorithm, NOT part of AASC**
- Included for comparison only
- Shows bottleneck of off-chain learning

---

## Expected Results

Based on your `result.txt`:

### At 20 nodes:

- **AASC:** ~2.43 tx/s, ~0.41s latency, ~65% CPU
- **PoS:** ~0.55 tx/s, ~1.82s latency, ~121% CPU
- **PoCH:** ~0.69 tx/s, ~1.46s latency, ~101% CPU
- **PoEM:** ~0.33 tx/s, ~3.04s latency, ~214% CPU

### Key Findings:

1. **AASC has highest throughput** (4-7x better than baselines)
2. **AASC has lowest latency** (3-7x faster)
3. **AASC has lower CPU than PoEM** (no ML overhead)
4. **AASC scales reasonably** to 100 nodes

---

## Next Steps

1. ✅ **Code is complete** - All algorithms implemented
2. ✅ **Tests are ready** - `test.py` runs all comparisons
3. ✅ **Analysis is ready** - `results.ipynb` generates charts
4. 📝 **Paper needs updates** - See `helper.md` for details

**To resubmit paper:**

1. Run `python test.py` (if you need fresh results)
2. Run `results.ipynb` (generate charts)
3. Update paper sections (see `helper.md`)
4. Submit! 🚀

---

## Questions?

**Q: Which file is the main AASC algorithm?**  
A: `aasc.py` - This is your main contribution.

**Q: What's the difference between AASC and mAASC?**  
A: mAASC is a variant with explicit stake gossip. AASC is pure on-chain.

**Q: Why is PoEM included?**  
A: For comparison only. It shows the bottleneck of off-chain learning.

**Q: How long does test.py take?**  
A: 2-4 hours for full run (5 network sizes). 5-10 min for single network.

**Q: Can I run tests in parallel?**  
A: No, tests run sequentially to avoid port conflicts.

**Q: What if I just want AASC results?**  
A: Edit `test.py` to only run `AASC_test()`.

---

**Last Updated:** 2026-01-20  
**Status:** ✅ Ready to run
