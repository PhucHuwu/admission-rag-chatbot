from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from langchain_openai import ChatOpenAI
from ragas import EvaluationDataset, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness, LLMContextRecall


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate RAG without ground-truth labels using RAGAS")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Backend base URL")
    parser.add_argument("--search-endpoint", default="/api/v1/search", help="Search endpoint")
    parser.add_argument("--chat-endpoint", default="/api/v1/chat", help="Chat endpoint")
    parser.add_argument(
        "--input",
        default="evaluation-rag/dataset/query_set.v1.json",
        help="Query dataset path (only id/query/university_code are required)",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Top contexts to keep")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout (seconds)")
    parser.add_argument("--judge-model", default="gpt-4o-mini", help="Evaluator model name")
    parser.add_argument(
        "--output-dir",
        default="evaluation-rag/output",
        help="Output directory",
    )
    return parser.parse_args()


def request_json(url: str, payload: dict[str, Any], timeout: int) -> tuple[dict[str, Any], float]:
    started = time.perf_counter()
    res = requests.post(url, json=payload, timeout=timeout)
    latency_ms = (time.perf_counter() - started) * 1000
    res.raise_for_status()
    return res.json(), latency_ms


def main() -> None:
    args = parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("Missing OPENAI_API_KEY for RAGAS evaluator LLM")

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Dataset not found: {input_path}")

    run_id = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    out_dir = Path(args.output_dir) / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    dataset = json.loads(input_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    ragas_rows: list[dict[str, Any]] = []

    search_url = args.base_url.rstrip("/") + args.search_endpoint
    chat_url = args.base_url.rstrip("/") + args.chat_endpoint

    for idx, item in enumerate(dataset, start=1):
        query_id = str(item.get("id", idx))
        query = str(item.get("query", "")).strip()
        university_code = str(item.get("university_code", "") or "")

        payload = {"query": query}
        if university_code:
            payload["university_code"] = university_code

        status = "ok"
        error = ""
        search_latency_ms = 0.0
        chat_latency_ms = 0.0
        retrieved_contexts: list[str] = []
        response_text = ""

        try:
            search_body, search_latency_ms = request_json(search_url, payload, args.timeout)
            hits = search_body.get("hits", []) if isinstance(search_body, dict) else []
            retrieved_contexts = [str(h.get("text", ""))[:1200] for h in hits[: args.top_k]]

            chat_body, chat_latency_ms = request_json(chat_url, payload, args.timeout)
            response_text = str(chat_body.get("answer", "")) if isinstance(chat_body, dict) else ""

            ragas_rows.append(
                {
                    "user_input": query,
                    "retrieved_contexts": retrieved_contexts,
                    "response": response_text,
                }
            )
        except Exception as exc:
            status = "error"
            error = str(exc)

        rows.append(
            {
                "id": query_id,
                "query": query,
                "university_code": university_code,
                "status": status,
                "error": error,
                "search_latency_ms": search_latency_ms,
                "chat_latency_ms": chat_latency_ms,
                "total_latency_ms": search_latency_ms + chat_latency_ms,
                "retrieved_context_count": len(retrieved_contexts),
                "response": response_text,
                "retrieved_contexts": retrieved_contexts,
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(out_dir / "per_query_metrics.csv", index=False)

    summary: dict[str, Any] = {
        "query_count_total": int(len(df)),
        "query_count_ok": int((df["status"] == "ok").sum()),
        "query_count_error": int((df["status"] == "error").sum()),
        "error_rate": float((df["status"] == "error").mean()) if len(df) else 0.0,
        "total_latency_mean_ms": float(df["total_latency_ms"].mean()) if len(df) else 0.0,
        "total_latency_p50_ms": float(df["total_latency_ms"].quantile(0.50)) if len(df) else 0.0,
        "total_latency_p95_ms": float(df["total_latency_ms"].quantile(0.95)) if len(df) else 0.0,
        "total_latency_p99_ms": float(df["total_latency_ms"].quantile(0.99)) if len(df) else 0.0,
    }

    if ragas_rows:
        evaluator = LangchainLLMWrapper(ChatOpenAI(model=args.judge_model, temperature=0))
        eval_dataset = EvaluationDataset.from_list(ragas_rows)
        result = evaluate(
            dataset=eval_dataset,
            metrics=[LLMContextRecall(), Faithfulness()],
            llm=evaluator,
        )
        result_dict = result.to_pandas().mean(numeric_only=True).to_dict()
        summary.update(
            {
                "context_recall": float(result_dict.get("context_recall", 0.0)),
                "faithfulness": float(result_dict.get("faithfulness", 0.0)),
            }
        )

    pd.DataFrame([{"metric": k, "value": v} for k, v in summary.items()]).to_csv(
        out_dir / "summary_metrics.csv",
        index=False,
    )
    (out_dir / "config.json").write_text(
        json.dumps(
            {
                "base_url": args.base_url,
                "search_endpoint": args.search_endpoint,
                "chat_endpoint": args.chat_endpoint,
                "input": str(input_path),
                "top_k": args.top_k,
                "timeout": args.timeout,
                "judge_model": args.judge_model,
                "executed_at": datetime.now().isoformat(),
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    (out_dir / "raw_results.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Done. Output: {out_dir}")


if __name__ == "__main__":
    main()
