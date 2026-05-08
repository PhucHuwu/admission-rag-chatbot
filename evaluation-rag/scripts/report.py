#!/usr/bin/env python3
"""
report.py — Sinh báo cáo tổng hợp từ nhiều run ablation.
Output: report.md + charts/ (radar.png, latency_cdf.png, per_category.png)
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

matplotlib.use("Agg")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate evaluation report")
    parser.add_argument("--runs", nargs="+", required=True, help="List of run directories")
    parser.add_argument("--labels", nargs="+", required=True, help="Labels for each run")
    parser.add_argument("--output-dir", default="evaluation-rag/output/report", help="Report output directory")
    return parser.parse_args()


def load_summary(run_dir: str) -> dict[str, Any]:
    path = Path(run_dir) / "summary_metrics.csv"
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return next(reader)


def load_per_query(run_dir: str) -> pd.DataFrame:
    path = Path(run_dir) / "per_query_metrics.csv"
    return pd.read_csv(path)


def draw_radar(labels: list[str], summaries: list[dict[str, Any]], out_path: Path) -> None:
    categories = ["Faithfulness", "Answer Relevancy", "Context Precision"]
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))

    for label, summary in zip(labels, summaries):
        values = [
            float(summary.get("faithfulness", 0)),
            float(summary.get("answer_relevancy", 0)),
            float(summary.get("context_precision", 0)),
        ]
        values += values[:1]
        ax.plot(angles, values, label=label)
        ax.fill(angles, values, alpha=0.1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 1.0)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    ax.set_title("RAGAS Metrics Comparison", y=1.08)

    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def draw_latency_cdf(baseline_df: pd.DataFrame, out_path: Path) -> None:
    latencies = baseline_df["total_latency_ms"].dropna().sort_values().values
    if len(latencies) == 0:
        return

    cdf = np.arange(1, len(latencies) + 1) / len(latencies)
    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(latencies, cdf, label="CDF")
    ax.axvline(p50, color="g", linestyle="--", label=f"p50 = {p50:.0f}ms")
    ax.axvline(p95, color="orange", linestyle="--", label=f"p95 = {p95:.0f}ms")
    ax.axvline(p99, color="r", linestyle="--", label=f"p99 = {p99:.0f}ms")
    ax.set_xlabel("Total Latency (ms)")
    ax.set_ylabel("Cumulative Probability")
    ax.set_title("Latency CDF — Full Pipeline")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def draw_per_category(baseline_df: pd.DataFrame, out_path: Path) -> None:
    ok_df = baseline_df[baseline_df["status"] == "ok"]
    if ok_df.empty:
        return

    grouped = ok_df.groupby("category")[["faithfulness", "answer_relevancy", "context_precision"]].mean()
    if grouped.empty:
        return

    categories = grouped.index.tolist()
    x = np.arange(len(categories))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(x - width, grouped["faithfulness"], width, label="Faithfulness")
    ax.bar(x, grouped["answer_relevancy"], width, label="Answer Relevancy")
    ax.bar(x + width, grouped["context_precision"], width, label="Context Precision")

    ax.set_xticks(x)
    ax.set_xticklabels(categories, rotation=30, ha="right")
    ax.set_ylabel("Score")
    ax.set_title("Per-Category Metrics — Baseline")
    ax.legend()
    ax.set_ylim(0, 1.0)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def delta_str(value: float, baseline: float) -> str:
    diff = value - baseline
    if abs(diff) < 0.005:
        return ""
    arrow = "▲" if diff > 0 else "▼"
    return f" {arrow}{diff:+.2f}"


def build_report(labels: list[str], summaries: list[dict[str, Any]], baseline_df: pd.DataFrame) -> str:
    baseline = summaries[0]
    lines = ["# Báo cáo đánh giá RAG Chatbot Tuyển Sinh\n"]

    lines.append("## 1. Tổng hợp metrics\n")
    lines.append(
        "| Config | Faithfulness | Ans. Relevancy | Ctx. Precision | RAG Score | Latency p95 |\n"
    )
    lines.append("|---|---|---|---|---|---|\n")

    for label, summary in zip(labels, summaries):
        faith = float(summary.get("faithfulness", 0))
        ans_rel = float(summary.get("answer_relevancy", 0))
        ctx_prec = float(summary.get("context_precision", 0))
        rag = float(summary.get("rag_score", 0))
        p95 = float(summary.get("latency_p95_ms", 0))

        base_faith = float(baseline.get("faithfulness", 0))
        base_ans = float(baseline.get("answer_relevancy", 0))
        base_ctx = float(baseline.get("context_precision", 0))
        base_rag = float(baseline.get("rag_score", 0))
        base_p95 = float(baseline.get("latency_p95_ms", 0))

        line = f"| {label} | {faith:.2f}{delta_str(faith, base_faith)} | {ans_rel:.2f}{delta_str(ans_rel, base_ans)} | {ctx_prec:.2f}{delta_str(ctx_prec, base_ctx)} | {rag:.2f}{delta_str(rag, base_rag)} | {p95:.0f}ms{delta_str(p95, base_p95)} |\n"
        lines.append(line)

    lines.append("\n## 2. Nhận xét\n")
    for i, (label, summary) in enumerate(zip(labels, summaries), start=1):
        lines.append(f"### {i}. {label}\n")
        rag = float(summary.get("rag_score", 0))
        base_rag = float(baseline.get("rag_score", 0))
        diff = rag - base_rag
        if i == 1:
            lines.append("- Cấu hình baseline đầy đủ.\n")
        elif diff < -0.05:
            lines.append(f"- Giảm đáng kể RAG Score ({diff:+.2f}), cần xem xét lại thành phần bị tắt.\n")
        elif diff < 0:
            lines.append(f"- Giảm nhẹ RAG Score ({diff:+.2f}).\n")
        else:
            lines.append(f"- Tăng RAG Score ({diff:+.2f}), bất thường nếu tắt thành phần.\n")
        lines.append("\n")

    lines.append("## 3. Per-category (baseline)\n")
    ok_df = baseline_df[baseline_df["status"] == "ok"]
    if not ok_df.empty:
        grouped = ok_df.groupby("category")[["faithfulness", "answer_relevancy", "context_precision"]].mean()
        lines.append("| Category | Faithfulness | Answer Relevancy | Context Precision |\n")
        lines.append("|---|---|---|---|\n")
        for cat, row in grouped.iterrows():
            lines.append(f"| {cat} | {row['faithfulness']:.2f} | {row['answer_relevancy']:.2f} | {row['context_precision']:.2f} |\n")

    return "".join(lines)


def main() -> int:
    args = parse_args()
    if len(args.runs) != len(args.labels):
        print("Number of --runs and --labels must match.", file=sys.stderr)
        return 1

    summaries = [load_summary(r) for r in args.runs]
    baseline_df = load_per_query(args.runs[0])

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    charts_dir = out_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    draw_radar(args.labels, summaries, charts_dir / "radar.png")
    draw_latency_cdf(baseline_df, charts_dir / "latency_cdf.png")
    draw_per_category(baseline_df, charts_dir / "per_category.png")

    report_md = build_report(args.labels, summaries, baseline_df)
    with open(out_dir / "report.md", "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"Report written to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
