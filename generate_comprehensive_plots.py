"""
Comprehensive Results Visualization for AASC Paper
Generates multiple comparison plots from result.txt
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import re
from pathlib import Path

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 12

# Create images directory
Path("images").mkdir(exist_ok=True)

def parse_results(file_path='result.txt'):
    """Parse result.txt into DataFrame"""
    results = []
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Split by test blocks
    blocks = content.split('--------------------------------------------------')
    
    for block in blocks:
        # Extract network config
        node_match = re.search(r'Number of Nodes: (\d+)', block)
        miner_match = re.search(r'Number of Miners: (\d+)', block)
        tx_match = re.search(r'Number of transaction: (\d+)', block)
        
        if not (node_match and miner_match and tx_match):
            continue
            
        num_nodes = int(node_match.group(1))
        num_miners = int(miner_match.group(1))
        num_tx = int(tx_match.group(1))
        
        # Extract algorithm results
        lines = block.split('\n')
        for line in lines:
            # Match algorithm data lines
            parts = line.split()
            if len(parts) >= 5:
                try:
                    # Try to parse as algorithm result
                    algo = parts[0]
                    if algo in ['AASC', 'PoEM', 'POS', 'POCH', 'mAASC', 'PoS', 'PoCH']:
                        # Handle multi-word algorithm names
                        if '(' in line:
                            algo = ' '.join(parts[:2])
                            throughput = float(parts[2])
                            latency = float(parts[3])
                            cpu = float(parts[4])
                            memory = float(parts[5])
                        else:
                            throughput = float(parts[1])
                            latency = float(parts[2])
                            cpu = float(parts[3])
                            memory = float(parts[4])
                        
                        # Normalize algorithm names
                        algo = algo.replace('(Baseline)', '').replace('(Proposed)', '').replace('(Reference)', '').strip()
                        
                        results.append({
                            'nodes': num_nodes,
                            'miners': num_miners,
                            'transactions': num_tx,
                            'algorithm': algo,
                            'throughput': throughput,
                            'latency': latency,
                            'cpu_usage': cpu,
                            'memory_usage': memory
                        })
                except (ValueError, IndexError):
                    continue
    
    return pd.DataFrame(results)

# Parse data
print("Parsing results...")
df = parse_results()
print(f"Total records: {len(df)}")
print(f"Algorithms: {df['algorithm'].unique()}")
print(f"Network sizes: {sorted(df['nodes'].unique())}")

# Filter to get clean comparison data (100 tx tests with all 4 algorithms)
df_main = df[(df['transactions'] == 100) & (df['algorithm'].isin(['AASC', 'PoS', 'PoCH', 'PoEM']))].copy()

if len(df_main) == 0:
    print("No complete 4-algorithm comparison data found. Using all available data.")
    df_main = df[df['algorithm'].isin(['AASC', 'PoS', 'PoCH', 'PoEM'])].copy()

print(f"\nMain comparison data: {len(df_main)} records")

# ============================================================================
# PLOT 1: Comprehensive 4-Algorithm Comparison - Throughput
# ============================================================================
print("\nGenerating Plot 1: Comprehensive Throughput Comparison...")

fig, ax = plt.subplots(figsize=(14, 8))

colors = {
    'AASC': '#2ecc71',  # Green - our algorithm
    'PoS': '#e74c3c',   # Red
    'PoCH': '#3498db',  # Blue
    'PoEM': '#f39c12'   # Orange
}

markers = {
    'AASC': 'o',
    'PoS': 's',
    'PoCH': '^',
    'PoEM': 'D'
}

for algo in ['AASC', 'PoS', 'PoCH', 'PoEM']:
    data = df_main[df_main['algorithm'] == algo].groupby('nodes')['throughput'].mean().reset_index()
    if len(data) > 0:
        ax.plot(data['nodes'], data['throughput'], 
                marker=markers.get(algo, 'o'), 
                color=colors.get(algo, 'gray'),
                linewidth=2.5, 
                markersize=10,
                label=algo,
                alpha=0.8)

ax.set_xlabel('Number of Nodes', fontsize=14, fontweight='bold')
ax.set_ylabel('Throughput (tx/s)', fontsize=14, fontweight='bold')
ax.set_title('Throughput Comparison: AASC vs Baselines', fontsize=16, fontweight='bold')
ax.legend(fontsize=12, loc='best', framealpha=0.9)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('images/comprehensive_throughput.png', dpi=300, bbox_inches='tight')
print("✓ Saved: images/comprehensive_throughput.png")
plt.close()

# ============================================================================
# PLOT 2: Comprehensive 4-Algorithm Comparison - Latency
# ============================================================================
print("Generating Plot 2: Comprehensive Latency Comparison...")

fig, ax = plt.subplots(figsize=(14, 8))

for algo in ['AASC', 'PoS', 'PoCH', 'PoEM']:
    data = df_main[df_main['algorithm'] == algo].groupby('nodes')['latency'].mean().reset_index()
    if len(data) > 0:
        ax.plot(data['nodes'], data['latency'], 
                marker=markers.get(algo, 'o'), 
                color=colors.get(algo, 'gray'),
                linewidth=2.5, 
                markersize=10,
                label=algo,
                alpha=0.8)

ax.set_xlabel('Number of Nodes', fontsize=14, fontweight='bold')
ax.set_ylabel('Latency (seconds)', fontsize=14, fontweight='bold')
ax.set_title('Latency Comparison: AASC vs Baselines', fontsize=16, fontweight='bold')
ax.legend(fontsize=12, loc='best', framealpha=0.9)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('images/comprehensive_latency.png', dpi=300, bbox_inches='tight')
print("✓ Saved: images/comprehensive_latency.png")
plt.close()

# ============================================================================
# PLOT 3: Resource Efficiency - CPU Usage
# ============================================================================
print("Generating Plot 3: CPU Usage Comparison...")

fig, ax = plt.subplots(figsize=(14, 8))

for algo in ['AASC', 'PoS', 'PoCH', 'PoEM']:
    data = df_main[df_main['algorithm'] == algo].groupby('nodes')['cpu_usage'].mean().reset_index()
    if len(data) > 0:
        ax.plot(data['nodes'], data['cpu_usage'], 
                marker=markers.get(algo, 'o'), 
                color=colors.get(algo, 'gray'),
                linewidth=2.5, 
                markersize=10,
                label=algo,
                alpha=0.8)

ax.set_xlabel('Number of Nodes', fontsize=14, fontweight='bold')
ax.set_ylabel('CPU Usage (%)', fontsize=14, fontweight='bold')
ax.set_title('CPU Usage Comparison: AASC vs Baselines', fontsize=16, fontweight='bold')
ax.legend(fontsize=12, loc='best', framealpha=0.9)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('images/comprehensive_cpu.png', dpi=300, bbox_inches='tight')
print("✓ Saved: images/comprehensive_cpu.png")
plt.close()

# ============================================================================
# PLOT 4: Resource Efficiency - Memory Usage
# ============================================================================
print("Generating Plot 4: Memory Usage Comparison...")

fig, ax = plt.subplots(figsize=(14, 8))

for algo in ['AASC', 'PoS', 'PoCH', 'PoEM']:
    data = df_main[df_main['algorithm'] == algo].groupby('nodes')['memory_usage'].mean().reset_index()
    if len(data) > 0:
        ax.plot(data['nodes'], data['memory_usage'], 
                marker=markers.get(algo, 'o'), 
                color=colors.get(algo, 'gray'),
                linewidth=2.5, 
                markersize=10,
                label=algo,
                alpha=0.8)

ax.set_xlabel('Number of Nodes', fontsize=14, fontweight='bold')
ax.set_ylabel('Memory Usage (MB)', fontsize=14, fontweight='bold')
ax.set_title('Memory Usage Comparison: AASC vs Baselines', fontsize=16, fontweight='bold')
ax.legend(fontsize=12, loc='best', framealpha=0.9)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('images/comprehensive_memory.png', dpi=300, bbox_inches='tight')
print("✓ Saved: images/comprehensive_memory.png")
plt.close()

# ============================================================================
# PLOT 5: AASC Performance Advantage - Bar Chart
# ============================================================================
print("Generating Plot 5: AASC Performance Advantage...")

# Calculate average metrics for each algorithm
avg_metrics = df_main.groupby('algorithm')[['throughput', 'latency', 'cpu_usage', 'memory_usage']].mean()

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Throughput
ax = axes[0, 0]
avg_metrics['throughput'].plot(kind='bar', ax=ax, color=[colors.get(algo, 'gray') for algo in avg_metrics.index])
ax.set_title('Average Throughput', fontsize=14, fontweight='bold')
ax.set_ylabel('Transactions/second', fontsize=12)
ax.set_xlabel('')
ax.tick_params(axis='x', rotation=0)
ax.grid(True, alpha=0.3, axis='y')

# Latency
ax = axes[0, 1]
avg_metrics['latency'].plot(kind='bar', ax=ax, color=[colors.get(algo, 'gray') for algo in avg_metrics.index])
ax.set_title('Average Latency', fontsize=14, fontweight='bold')
ax.set_ylabel('Seconds', fontsize=12)
ax.set_xlabel('')
ax.tick_params(axis='x', rotation=0)
ax.grid(True, alpha=0.3, axis='y')

# CPU Usage
ax = axes[1, 0]
avg_metrics['cpu_usage'].plot(kind='bar', ax=ax, color=[colors.get(algo, 'gray') for algo in avg_metrics.index])
ax.set_title('Average CPU Usage', fontsize=14, fontweight='bold')
ax.set_ylabel('Percentage', fontsize=12)
ax.set_xlabel('')
ax.tick_params(axis='x', rotation=0)
ax.grid(True, alpha=0.3, axis='y')

# Memory Usage
ax = axes[1, 1]
avg_metrics['memory_usage'].plot(kind='bar', ax=ax, color=[colors.get(algo, 'gray') for algo in avg_metrics.index])
ax.set_title('Average Memory Usage', fontsize=14, fontweight='bold')
ax.set_ylabel('MB', fontsize=12)
ax.set_xlabel('')
ax.tick_params(axis='x', rotation=0)
ax.grid(True, alpha=0.3, axis='y')

plt.suptitle('AASC Performance Summary', fontsize=18, fontweight='bold', y=1.00)
plt.tight_layout()
plt.savefig('images/aasc_performance_summary.png', dpi=300, bbox_inches='tight')
print("✓ Saved: images/aasc_performance_summary.png")
plt.close()

# ============================================================================
# PLOT 6: Scalability Analysis - Combined Metrics
# ============================================================================
print("Generating Plot 6: Scalability Analysis...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

metrics = ['throughput', 'latency', 'cpu_usage', 'memory_usage']
titles = ['Throughput Scalability', 'Latency Scalability', 'CPU Usage Scalability', 'Memory Usage Scalability']
ylabels = ['Transactions/second', 'Seconds', 'Percentage', 'MB']

for idx, (metric, title, ylabel) in enumerate(zip(metrics, titles, ylabels)):
    ax = axes[idx // 2, idx % 2]
    
    for algo in ['AASC', 'PoS', 'PoCH', 'PoEM']:
        data = df_main[df_main['algorithm'] == algo].groupby('nodes')[metric].mean().reset_index()
        if len(data) > 0:
            ax.plot(data['nodes'], data[metric], 
                    marker=markers.get(algo, 'o'), 
                    color=colors.get(algo, 'gray'),
                    linewidth=2, 
                    markersize=8,
                    label=algo,
                    alpha=0.8)
    
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.set_xlabel('Number of Nodes', fontsize=11)
    ax.set_ylabel(ylabel, fontsize=11)
    ax.legend(fontsize=10, loc='best')
    ax.grid(True, alpha=0.3)

plt.suptitle('Scalability Analysis: All Algorithms', fontsize=16, fontweight='bold', y=1.00)
plt.tight_layout()
plt.savefig('images/scalability_analysis.png', dpi=300, bbox_inches='tight')
print("✓ Saved: images/scalability_analysis.png")
plt.close()

# ============================================================================
# Generate Summary Statistics Table
# ============================================================================
print("\nGenerating summary statistics...")

summary = df_main.groupby('algorithm').agg({
    'throughput': ['mean', 'std', 'max'],
    'latency': ['mean', 'std', 'min'],
    'cpu_usage': ['mean', 'std'],
    'memory_usage': ['mean', 'std']
}).round(3)

print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)
print(summary)

# Save to file
with open('images/summary_statistics.txt', 'w') as f:
    f.write("="*80 + "\n")
    f.write("AASC EXPERIMENTAL RESULTS - SUMMARY STATISTICS\n")
    f.write("="*80 + "\n\n")
    f.write(summary.to_string())
    f.write("\n\n")
    f.write("="*80 + "\n")
    f.write("PERFORMANCE ADVANTAGES OF AASC\n")
    f.write("="*80 + "\n\n")
    
    if 'AASC' in avg_metrics.index:
        for baseline in ['PoS', 'PoCH', 'PoEM']:
            if baseline in avg_metrics.index:
                throughput_improvement = ((avg_metrics.loc['AASC', 'throughput'] / avg_metrics.loc[baseline, 'throughput']) - 1) * 100
                latency_improvement = ((avg_metrics.loc[baseline, 'latency'] / avg_metrics.loc['AASC', 'latency']) - 1) * 100
                f.write(f"AASC vs {baseline}:\n")
                f.write(f"  Throughput: {throughput_improvement:+.1f}% improvement\n")
                f.write(f"  Latency: {latency_improvement:+.1f}% improvement\n\n")

print("✓ Saved: images/summary_statistics.txt")

print("\n" + "="*80)
print("ALL VISUALIZATIONS GENERATED SUCCESSFULLY!")
print("="*80)
print("\nGenerated files:")
print("  1. images/comprehensive_throughput.png")
print("  2. images/comprehensive_latency.png")
print("  3. images/comprehensive_cpu.png")
print("  4. images/comprehensive_memory.png")
print("  5. images/aasc_performance_summary.png")
print("  6. images/scalability_analysis.png")
print("  7. images/summary_statistics.txt")
print("\nThese plots are ready for your research paper!")
