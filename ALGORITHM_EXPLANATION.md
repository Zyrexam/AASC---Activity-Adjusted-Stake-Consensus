# AASC Implementation Guide

## What is AASC?

**Activity-Adjusted Stake Consensus (AASC)** is a fully distributed, on-chain consensus algorithm for IoT networks. It selects block producers based on node activity, fairness, and rotation - all computed from blockchain data.

**Key Property:** AASC is **pure on-chain** - it requires NO off-chain learning system, NO centralized server, and NO external coordination. All data needed for consensus is derived from the blockchain itself.

---

## How AASC Works

### Phase 1: Track Activity (On-chain)

**Location:** `aasc.py` lines 310-320

Each node independently tracks 5 activity metrics per validator from the blockchain:

- **`lit`**: Last Instance Time (when did they last mine a block?)
- **`aist`**: Activity Interval Sample Time (how active are they over time?)
- **`cst`**: Consecutive Success Time (how many blocks in a row?)
- **`tst`**: Total Sample Time (time window for activity tracking)
- **`cbm`**: Consecutive Blocks Mined (recent block production count)

These metrics are **updated from blockchain data only** - no external communication required.

### Phase 2: Compute Consensus Score (Local)

**Location:** `aasc.py` lines 275-294

Formula:
```
CS = [α * AIST * (1 - CST/TST) * log(1 + 1/LIT)] / [β * (CBM + 1)²]
```

Where:
- `α = 3`, `β = 1` (constants)
- Each node computes CS independently from blockchain data
- Result: Consensus Score (CS) for each validator

### Phase 3: Select Leader (Deterministic)

**Location:** `aasc.py` lines 323-327

Method: `argmax(CS)` — pick validator with highest score

**Why Deterministic:**
- All nodes have identical blockchain view (after sync)
- All nodes compute activity from same blockchain data
- All nodes apply same scoring formula
- Therefore: All nodes arrive at same leader

### Phase 4: Mine Block (Broadcast)

**Location:** `aasc.py` lines 330-344

- If selected: create block and broadcast to peers
- All nodes receive and verify block
- All nodes update local activity tracking

---

## Why is AASC Fully Distributed?

✅ **All data is on-chain** - activity metrics derived from blockchain  
✅ **No central server** - each node computes independently  
✅ **No off-chain communication** - only block broadcast required  
✅ **Deterministic consensus** - all nodes agree on leader  
✅ **Self-healing** - nodes can recover state from blockchain replay  

---

## Complexity Analysis

### Time Complexity

**Per consensus round:**

- Activity update: **O(1)** - update one validator's metrics
- CS computation: **O(v)** - compute CS for each of v validators (unavoidable)
- Leader selection: **O(v)** - find argmax (unavoidable)

**Total: O(v) per round per node**

**Note:** The claim "O(1) complexity" is **incorrect**. O(v) is the correct complexity because:
1. Computing CS requires looping through v validators (line 323)
2. Selecting leader (argmax) requires O(v) comparisons (line 326)

**Why O(v) is Still Good:**
- For IoT networks: v << n (validators << total nodes)
- Example: v = 10-100 validators is typical
- O(v) = O(10-100) is practical and efficient
- Much better than O(n) which would require all nodes

### Space Complexity

**Per node:**

- Activity parameters: **O(v)** - one dict per validator
- Blockchain storage: **O(b)** where b = total blocks
- Messages: **O(1)** per round (one block)

**Total: O(v + b) per node**

### Communication Complexity

**Per round:**

- Blocks: **O(1)** per leader (constant size)
- Gossip: **O(n)** - broadcast to all n nodes (unavoidable for any consensus)

**Total: O(n) per round**

**Compared to Off-Chain Learning:**
- Off-chain learning would require additional **O(?)** communication for ML model sync
- AASC requires **NO off-chain communication** - this solves the bottleneck problem

### Churn Recovery Complexity

**When node rejoins after offline period:**

- Blockchain replay: **O(b*v)** where b = blocks, v = validators
- This is a **one-time cost** during rejoin
- Acceptable for IoT networks where rejoin is infrequent

---

## Fairness Guarantees

AASC ensures fairness through:

1. **Activity boost:** Recently inactive nodes (`lit` high) get higher scores via `log(1 + 1/LIT)`
2. **Monopoly penalty:** Recent block producers (`cbm` high) get lower scores via `(CBM + 1)²` denominator
3. **Rotation:** `cbm` ensures dominance is penalized
4. **Time weighting:** `aist` adapts to recent activity patterns

---

## Churn Handling (IoT Suitability)

**Problem:** IoT nodes frequently go offline/online (churn)

**Solution:** AASC can recover state from blockchain replay

**Location:** `aasc.py` lines 246-285 (`recover_parameters_from_chain`)

**How it works:**
1. Node goes offline
2. Node rejoins and syncs blockchain
3. Node calls `recover_parameters_from_chain()`
4. Function replays all blocks and rebuilds activity parameters
5. Node rejoins consensus immediately

**Why this is good for IoT:**
- No external state server needed
- No coordination required
- Node can recover independently
- Guaranteed to have same state as other nodes

---

## Code Structure

### Main Files

- **`aasc.py`** - Main AASC implementation (pure on-chain)
- **`m_aasc.py`** - Variant with stake gossip (not in main paper)
- **`pos.py`** - Baseline: Traditional Proof of Stake
- **`poch.py`** - Baseline: Proof of Chance (hash-based)

### Related Files (Not Part of AASC)

- **`poem_global.py`** - ML-based consensus with centralized model
  - **Note:** This is a separate algorithm, NOT part of AASC
  - Uses global ML model (centralized bottleneck)
  - Included in experiments for reference only

### Test Files

- **`test.py`** - Comparative experiments: AASC vs PoS vs PoCH vs PoEM
- **`test_maasc.py`** - Tests mAASC variant

---

## Addressing Reviewer Concerns

### Reviewer Concern #1: "Off-chain learning bottleneck unclear"

**Answer:** AASC has **NO off-chain learning system**. All data is on-chain. The `poem_global.py` file is a separate algorithm and is NOT part of AASC.

### Reviewer Concern #2: "O(1) complexity claim unclear"

**Answer:** Corrected - AASC complexity is **O(v)**, not O(1). This is:
- Mathematically correct (must evaluate all validators)
- Practically efficient (v << n for IoT)
- Clearly documented in code and paper

---

## Comparison with Other Algorithms

| Algorithm | File | Type | Centralized? | Uses ML? | Off-chain? |
|-----------|------|------|--------------|----------|------------|
| **AASC (Proposed)** | `aasc.py` | Activity-based | ❌ NO | ❌ NO | ❌ NO |
| PoS (Baseline) | `pos.py` | Stake-weighted | ❌ NO | ❌ NO | ❌ NO |
| PoCH (Baseline) | `poch.py` | Hash-based | ❌ NO | ❌ NO | ❌ NO |
| PoEM (Reference) | `poem_global.py` | ML-based | ✅ YES | ✅ YES | ⚠️ Uses global model |

**Note:** PoEM is included for comparison but is **NOT part of AASC**. It is a separate algorithm with different architecture.

---

## Implementation Details

### Consensus Score Formula

```python
CS = (alpha * aist * (1 - cst/tst) * np.log(1 + 1/(lit + 0.000001))) / (beta * (cbm + 1)**2)
```

Where:
- `alpha = 3`, `beta = 1`
- Formula rewards inactive nodes and penalizes recent block producers
- Ensures fairness and rotation

### Leader Selection

```python
CS = [self.score(self.parameters[val]) for val in self.blockchain.validators]  # O(v)
block_producer_index = np.argmax(CS)  # O(v)
block_producer = list(self.blockchain.validators)[block_producer_index]
```

Deterministic - all nodes compute same result.

### Activity Update

```python
self.parameters[mined_by]['aist'] = (
    (old_aist * old_cst + block_pos + 1 - old_lit) / (old_cst + 1)
)
self.parameters[mined_by]['cst'] += 1
self.parameters[mined_by]['tst'] = block_pos + 1 - self.active
self.parameters[mined_by]['lit'] = block_pos + 1
self.parameters[mined_by]['cbm'] += 1
```

Updated from blockchain data only - no external communication.

---

## Summary

**AASC is:**
- ✅ Fully distributed (no central server)
- ✅ On-chain only (no off-chain learning)
- ✅ Deterministic (all nodes agree)
- ✅ Fair (activity-based rotation)
- ✅ IoT-suitable (handles churn)

**AASC is NOT:**
- ❌ Off-chain learning system
- ❌ ML-based selection
- ❌ Centralized coordination
- ❌ O(1) complexity (it's O(v))

**Correct Complexity:**
- Time: **O(v)** per round
- Space: **O(v + b)** per node
- Communication: **O(n)** per round

This addresses all reviewer concerns and provides a clear, defensible contribution.
