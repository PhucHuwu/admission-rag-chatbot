#!/usr/bin/env python3
"""
evaluate.py — Chấm điểm RAGAS và domain-specific metrics từ raw_results.json.
Không gọi API backend. Output: per_query_metrics.csv + summary_metrics.csv.
"""

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from datasets import Dataset
from langchain_openai import ChatOpenAI
from ragas import evaluate as ragas_evaluate
from ragas.metrics import (
    _AnswerRelevancy as AnswerRelevancy,
    _Faithfulness as Faithfulness,
    _LLMContextPrecisionWithoutReference as ContextPrecision,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate collected RAG results")
    parser.add_argument("--run-dir", required=True, help="Output directory from collect.py")
    parser.add_argument("--judge-model", default="gpt-4o-mini", help="OpenAI judge model")
    parser.add_argument("--judge-base-url", default="https://api.openai.com/v1", help="OpenAI base URL")
    return parser.parse_args()


def load_raw(run_dir: str) -> list[dict[str, Any]]:
    path = Path(run_dir) / "raw_results.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_numbers(text: str) -> list[str]:
    return re.findall(r"\b\d{1,2}(?:\.\d{1,2})?\b", text)


def numerical_faithfulness(answer: str, contexts: list[str]) -> float:
    nums = extract_numbers(answer)
    if not nums:
        return 1.0
    context_text = " ".join(contexts)
    matched = sum(1 for n in nums if n in context_text)
    return matched / len(nums)


def compute_data_sufficiency_accuracy(raw: list[dict[str, Any]]) -> float:
    has_answer_items = [r for r in raw if r.get("expected_has_answer") is True and r["status"] == "ok"]
    no_answer_items = [r for r in raw if r.get("expected_has_answer") is False and r["status"] == "ok"]

    has_answer_acc = (
        sum(1 for r in has_answer_items if r.get("data_sufficient") is True) / max(len(has_answer_items), 1)
    )
    no_answer_acc = (
        sum(1 for r in no_answer_items if r.get("data_sufficient") is False) / max(len(no_answer_items), 1)
    )
    return (has_answer_acc + no_answer_acc) / 2


def main() -> int:
    args = parse_args()
    run_dir = Path(args.run_dir)
    raw = load_raw(str(run_dir))

    ok_items = [r for r in raw if r["status"] == "ok" and r.get("retrieved_contexts")]

    if not ok_items:
        print("No successful results with contexts to evaluate.", file=sys.stderr)
        return 1

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY not set.", file=sys.stderr)
        return 1

    llm = ChatOpenAI(
        model=args.judge_model,
        api_key=api_key,
        base_url=args.judge_base_url,
        temperature=0.0,
    )

    ragas_rows = [
        {
            "user_input": item["query"],
            "retrieved_contexts": item["retrieved_contexts"],
            "response": item["answer"],
        }
        for item in ok_items
    ]

    dataset = Dataset.from_list(ragas_rows)
    metrics = [Faithfulness(), AnswerRelevancy(), ContextPrecision()]

    print("Running RAGAS evaluation...")
    result = ragas_evaluate(dataset=dataset, metrics=metrics, llm=llm)
    scores_df = result.to_pandas()

    id_to_ragas: dict[str, dict[str, float]] = {}
    for idx, row in scores_df.iterrows():
        qid = ok_items[idx]["id"]
        id_to_ragas[qid] = {
            "faithfulness": float(row.get("faithfulness", np.nan)),
            "answer_relevancy": float(row.get("answer_relevancy", np.nan)),
            "context_precision": float(
                row.get("llm_context_precision_without_reference", row.get("context_precision", np.nan))
            ),
        }

    per_query_rows = []
    for item in raw:
        qid = item["id"]
        ragas_scores = id_to_ragas.get(qid, {})
        nf = (
            numerical_faithfulness(item.get("answer", ""), item.get("retrieved_contexts", []))
            if item["status"] == "ok"
            else np.nan
        )
        row = {
            "id": qid,
            "query": item["query"],
            "category": item.get("category", ""),
            "expected_has_answer": item.get("expected_has_answer", True),
            "status": item["status"],
            "faithfulness": ragas_scores.get("faithfulness", np.nan),
            "answer_relevancy": ragas_scores.get("answer_relevancy", np.nan),
            "context_precision": ragas_scores.get("context_precision", np.nan),
            "numerical_faithfulness": nf,
            "data_sufficient": item.get("data_sufficient", False),
            "total_latency_ms": item.get("total_latency_ms", np.nan),
        }
        per_query_rows.append(row)

    per_query_path = run_dir / "per_query_metrics.csv"
    with open(per_query_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "query",
                "category",
                "expected_has_answer",
                "status",
                "faithfulness",
                "answer_relevancy",
                "context_precision",
                "numerical_faithfulness",
                "data_sufficient",
                "total_latency_ms",
            ],
        )
        writer.writeheader()
        writer.writerows(per_query_rows)

    ok_df = pd.DataFrame([r for r in per_query_rows if r["status"] == "ok"])

    faithfulness_mean = ok_df["faithfulness"].mean() if not ok_df.empty else 0.0
    answer_relevancy_mean = ok_df["answer_relevancy"].mean() if not ok_df.empty else 0.0
    context_precision_mean = ok_df["context_precision"].mean() if not ok_df.empty else 0.0
    rag_score = faithfulness_mean * 0.4 + answer_relevancy_mean * 0.35 + context_precision_mean * 0.25

    nf_mean = ok_df["numerical_faithfulness"].mean() if not ok_df.empty else 0.0
    data_sufficiency_accuracy = compute_data_sufficiency_accuracy(raw)

    latencies = ok_df["total_latency_ms"].dropna().values if not ok_df.empty else np.array([])
    latency_mean = float(np.mean(latencies)) if len(latencies) else 0.0
    latency_p50 = float(np.percentile(latencies, 50)) if len(latencies) else 0.0
    latency_p95 = float(np.percentile(latencies, 95)) if len(latencies) else 0.0
    latency_p99 = float(np.percentile(latencies, 99)) if len(latencies) else 0.0

    total = len(raw)
    ok_count = sum(1 for r in raw if r["status"] == "ok")
    error_rate = (total - ok_count) / total if total else 0.0

    summary = {
        "faithfulness": round(faithfulness_mean, 4),
        "answer_relevancy": round(answer_relevancy_mean, 4),
        "context_precision": round(context_precision_mean, 4),
        "rag_score": round(rag_score, 4),
        "numerical_faithfulness": round(nf_mean, 4),
        "data_sufficiency_accuracy": round(data_sufficiency_accuracy, 4),
        "latency_mean_ms": round(latency_mean, 2),
        "latency_p50_ms": round(latency_p50, 2),
        "latency_p95_ms": round(latency_p95, 2),
        "latency_p99_ms": round(latency_p99, 2),
        "error_rate": round(error_rate, 4),
        "query_count_total": total,
        "query_count_ok": ok_count,
        "query_count_error": total - ok_count,
    }

    summary_path = run_dir / "summary_metrics.csv"
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary.keys()))
        writer.writeheader()
        writer.writerow(summary)

    print(f"Per-query metrics: {per_query_path}")
    print(f"Summary metrics  : {summary_path}")
    print(f"RAG Score        : {rag_score:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
