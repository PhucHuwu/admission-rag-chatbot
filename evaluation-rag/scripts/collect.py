#!/usr/bin/env python3
"""
collect.py — Gọi API backend và lưu kết quả thô cho pipeline đánh giá RAG.
Không chạm đến RAGAS. Phase này tách riêng để tiết kiệm chi phí judge và debug backend.
"""

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect raw RAG results from backend API")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--input", default="evaluation-rag/dataset/query_set.v1.json", help="Path to query_set JSON")
    parser.add_argument("--output-dir", default="evaluation-rag/output", help="Output directory root")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout per request in seconds")
    parser.add_argument("--retries", type=int, default=3, help="Number of retries on 5xx/timeout")
    parser.add_argument("--retry-backoff", type=int, default=2, help="Seconds between retries")
    parser.add_argument("--max-samples", type=int, default=0, help="Limit number of queries (0 = all)")
    parser.add_argument("--run-id", default=None, help="Run folder name (default = ISO timestamp)")
    return parser.parse_args()


def load_queries(input_path: str, max_samples: int) -> list[dict[str, Any]]:
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list")
    if max_samples > 0:
        data = data[:max_samples]
    return data


def call_api(
    method: str,
    url: str,
    payload: dict[str, Any],
    timeout: int,
    retries: int,
    backoff: int,
) -> tuple[dict[str, Any] | None, str]:
    for attempt in range(retries + 1):
        try:
            resp = requests.request(method, url, json=payload, timeout=timeout)
            if resp.status_code >= 500:
                if attempt < retries:
                    time.sleep(backoff * (attempt + 1))
                    continue
                return None, f"HTTP {resp.status_code}"
            resp.raise_for_status()
            return resp.json(), ""
        except requests.exceptions.Timeout:
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
                continue
            return None, "Timeout"
        except requests.exceptions.RequestException as e:
            if attempt < retries:
                time.sleep(backoff * (attempt + 1))
                continue
            return None, str(e)
    return None, "Unknown error"


def main() -> int:
    args = parse_args()
    queries = load_queries(args.input, args.max_samples)

    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = Path(args.output_dir) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "run_id": run_id,
        "base_url": args.base_url,
        "input": args.input,
        "timeout": args.timeout,
        "retries": args.retries,
        "retry_backoff": args.retry_backoff,
        "max_samples": args.max_samples,
        "query_count": len(queries),
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(out_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    raw_results: list[dict[str, Any]] = []
    failed_rows: list[dict[str, Any]] = []

    search_url = f"{args.base_url}/api/v1/search"
    chat_url = f"{args.base_url}/api/v1/chat"

    for idx, item in enumerate(queries, start=1):
        qid = item.get("id", f"q{idx}")
        query_text = item["query"]
        university_code = item.get("university_code", "")
        category = item.get("category", "")
        expected_has_answer = item.get("expected_has_answer", True)

        print(f"[{idx}/{len(queries)}] {qid}: {query_text[:60]}...", flush=True)

        payload: dict[str, Any] = {"query": query_text}
        if university_code:
            payload["university_code"] = university_code

        t0 = time.perf_counter()
        search_data, search_err = call_api(
            "POST", search_url, payload, args.timeout, args.retries, args.retry_backoff
        )
        search_latency_ms = (time.perf_counter() - t0) * 1000

        retrieved_contexts: list[str] = []
        if search_data and "hits" in search_data:
            for hit in search_data["hits"][:5]:
                text = hit.get("text", "")
                if text:
                    retrieved_contexts.append(text[:1200])

        t0 = time.perf_counter()
        chat_data, chat_err = call_api(
            "POST", chat_url, payload, args.timeout, args.retries, args.retry_backoff
        )
        chat_latency_ms = (time.perf_counter() - t0) * 1000

        total_latency_ms = search_latency_ms + chat_latency_ms

        status = "ok"
        error = ""
        answer = ""
        data_sufficient = False

        if search_err or chat_err:
            status = "error"
            error = f"search: {search_err}; chat: {chat_err}".strip("; ")
        else:
            answer = chat_data.get("answer", "") if chat_data else ""
            data_sufficient = chat_data.get("data_sufficient", False) if chat_data else False

        record = {
            "id": qid,
            "query": query_text,
            "university_code": university_code,
            "category": category,
            "expected_has_answer": expected_has_answer,
            "status": status,
            "error": error,
            "search_latency_ms": round(search_latency_ms, 3),
            "chat_latency_ms": round(chat_latency_ms, 3),
            "total_latency_ms": round(total_latency_ms, 3),
            "retrieved_contexts": retrieved_contexts,
            "retrieved_context_count": len(retrieved_contexts),
            "data_sufficient": data_sufficient,
            "answer": answer,
        }
        raw_results.append(record)

        if status != "ok":
            failed_rows.append({
                "id": qid,
                "query": query_text,
                "error": error,
            })

    with open(out_dir / "raw_results.json", "w", encoding="utf-8") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=2)

    with open(out_dir / "failed_queries.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "query", "error"])
        writer.writeheader()
        writer.writerows(failed_rows)

    config["finished_at"] = datetime.now(timezone.utc).isoformat()
    config["ok_count"] = sum(1 for r in raw_results if r["status"] == "ok")
    config["error_count"] = len(failed_rows)
    with open(out_dir / "config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"\nDone. Output: {out_dir}")
    print(f"  Total : {len(queries)}")
    print(f"  OK    : {config['ok_count']}")
    print(f"  Error : {config['error_count']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
