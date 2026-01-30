import json
import csv
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

ROOT = "node_churn_results"
OUTPUT = "final_analysis"
ALGORITHMS = ["AASC", "PoS", "PoCH", "PoEM"]

BASE_CHURN = 0.0
COMPARE_CHURN = 0.10

Path(OUTPUT).mkdir(exist_ok=True)


def compute_relative_drop(base, current):
    if base == 0:
        return 0
    drop = ((base - current) / base) * 100
    return round(max(drop, 0), 2)

def load_all():
    data = {}

    for config_dir in Path(ROOT).iterdir():
        if not config_dir.is_dir():
            continue

        config_name = config_dir.name
        data[config_name] = {}

        for f in config_dir.glob("churn_*.json"):
            churn_percent = int(f.stem.split("_")[1])
            churn = churn_percent / 100.0

            with open(f) as jf:
                content = json.load(jf)

            data[config_name][churn] = content["results"]

    return data

def extract_metric(data, config, metric):
    """
    metric: 'throughput' or 'avg_tx_submission_time'
    """
    churns = sorted(data[config].keys())
    values = {algo: [] for algo in ALGORITHMS}

    for churn in churns:
        for algo in ALGORITHMS:
            # Handle missing data gracefully
            val = data[config][churn].get(algo, {}).get(metric, 0)
            values[algo].append(val)

    return churns, values

def plot_throughput_vs_churn(data):
    for config in data:
        churns, values = extract_metric(data, config, "throughput")

        plt.figure(figsize=(7, 4))

        for algo in ALGORITHMS:
            plt.plot(
                [c * 100 for c in churns],
                values[algo],
                marker="o",
                label=algo
            )

        plt.xlabel("Churn Rate (%)")
        plt.ylabel("Throughput (TPS)")
        plt.title(f"Throughput vs Node Churn ({config})")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()

        plt.tight_layout()
        plt.savefig(f"{OUTPUT}/throughput_vs_churn_{config}.png", dpi=300)
        print(f"✓ Saved throughput_vs_churn_{config}.png")
        # plt.show() # Commented out to avoid blocking execution if run interactively without display

def plot_latency_vs_churn(data):
    for config in data:
        churns, values = extract_metric(
            data, config, "avg_tx_submission_time"
        )

        plt.figure(figsize=(7, 4))

        for algo in ALGORITHMS:
            plt.plot(
                [c * 100 for c in churns],
                values[algo],
                marker="o",
                label=algo
            )

        plt.xlabel("Churn Rate (%)")
        plt.ylabel("Avg Transaction Submission Time (s)")
        plt.title(f"Avg TX Submission Time vs Node Churn ({config})")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend()

        plt.tight_layout()
        plt.savefig(f"{OUTPUT}/tx_time_vs_churn_{config}.png", dpi=300)
        print(f"✓ Saved tx_time_vs_churn_{config}.png")
        # plt.show()

if __name__ == "__main__":
    data = load_all()
    plot_throughput_vs_churn(data)
    plot_latency_vs_churn(data)
