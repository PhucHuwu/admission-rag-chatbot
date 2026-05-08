#!/usr/bin/env python3
"""
local_evaluate.py — Chấm điểm RAG metrics bằng heuristic local, không cần LLM API.
Output: per_query_metrics.csv + summary_metrics.csv (tương thích evaluate.py)
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local heuristic evaluation for RAG results")
    parser.add_argument("--run-dir", required=True, help="Output directory containing raw_results.json")
    return parser.parse_args()


def load_raw(run_dir: str) -> list[dict[str, Any]]:
    path = Path(run_dir) / "raw_results.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_numbers(text: str) -> list[str]:
    return re.findall(r"\b\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\b", text)


def tokenize(text: str) -> set[str]:
    """Simple Vietnamese-aware tokenization: lowercase, remove punctuation, split by whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\sàáảãạăắằẳẵặâấầẩẫậđèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵ]", " ", text)
    tokens = text.split()
    stopwords = {
        "là", "củ", "và", "các", "củ", "cho", "để", "có", "không", "như",
        "theo", "tại", "với", "được", "năm", "bao", "nhiêu", "gì", "nào",
        "củ", "mã", "ngành", "đại", "học", "trường", "thông", "tin",
    }
    return {t for t in tokens if len(t) > 1 and t not in stopwords}


def numerical_faithfulness(answer: str, contexts: list[str]) -> float:
    nums = extract_numbers(answer)
    if not nums:
        return 1.0
    context_text = " ".join(contexts)
    matched = sum(1 for n in nums if n in context_text)
    return matched / len(nums)


def keyword_faithfulness(answer: str, contexts: list[str]) -> float:
    """Check what fraction of important answer tokens appear in contexts."""
    ans_tokens = tokenize(answer)
    if not ans_tokens:
        return 1.0
    ctx_text = " ".join(contexts)
    ctx_tokens = tokenize(ctx_text)
    matched = ans_tokens & ctx_tokens
    return len(matched) / len(ans_tokens)


def compute_faithfulness(answer: str, contexts: list[str]) -> float:
    nf = numerical_faithfulness(answer, contexts)
    kf = keyword_faithfulness(answer, contexts)
    return 0.6 * nf + 0.4 * kf


def answer_relevancy(query: str, answer: str) -> float:
    """Heuristic: query tokens should appear in answer; answer shouldn't be a generic refusal unless query is out_of_scope."""
    query_tokens = tokenize(query)
    answer_tokens = tokenize(answer)
    if not query_tokens or not answer_tokens:
        return 0.0

    overlap = query_tokens & answer_tokens
    overlap_score = len(overlap) / len(query_tokens)

    refusal_phrases = ["xin lỗi", "không có thông tin", "không tìm thấy", "chưa có", "không rõ"]
    lower_answer = answer.lower()
    is_refusal = any(p in lower_answer for p in refusal_phrases)

    if is_refusal:
        return max(0.1, overlap_score * 0.5)

    length_boost = min(0.1, len(answer_tokens) / 200)

    score = overlap_score + length_boost
    return min(1.0, score)


def context_precision(query: str, contexts: list[str]) -> float:
    """Heuristic: what fraction of retrieved contexts contain query tokens."""
    query_tokens = tokenize(query)
    if not query_tokens or not contexts:
        return 0.0

    scores = []
    for ctx in contexts:
        ctx_tokens = tokenize(ctx)
        if not ctx_tokens:
            scores.append(0.0)
            continue
        overlap = query_tokens & ctx_tokens
        scores.append(len(overlap) / len(query_tokens))

    return float(np.mean(scores))


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

    per_query_rows = []
    for item in raw:
        qid = item["id"]
        query = item.get("query", "")
        answer = item.get("answer", "")
        contexts = item.get("retrieved_contexts", [])

        if item["status"] == "ok" and contexts:
            faith = compute_faithfulness(answer, contexts)
            ans_rel = answer_relevancy(query, answer)
            ctx_prec = context_precision(query, contexts)
            nf = numerical_faithfulness(answer, contexts)
        else:
            faith = ans_rel = ctx_prec = nf = np.nan

        row = {
            "id": qid,
            "query": query,
            "category": item.get("category", ""),
            "expected_has_answer": item.get("expected_has_answer", True),
            "status": item["status"],
            "faithfulness": faith,
            "answer_relevancy": ans_rel,
            "context_precision": ctx_prec,
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
    print(f"Faithfulness     : {faithfulness_mean:.4f}")
    print(f"Answer Relevancy : {answer_relevancy_mean:.4f}")
    print(f"Context Precision: {context_precision_mean:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
