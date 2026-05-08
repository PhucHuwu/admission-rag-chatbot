# RAG Evaluation Suite

Bộ công cụ đánh giá hệ thống RAG theo hướng nghiên cứu khoa học, ưu tiên phương pháp không cần ground-truth (reference-free, RAGAS-style).

## Mục tiêu

- Đo lường chất lượng RAG không cần nhãn tay: `Context Relevance`, `Answer Relevance`, `Faithfulness`.
- Tổng hợp điểm `RAG Score` (trung bình 3 chỉ số trên).
- Đo lường hiệu năng: latency `mean/p50/p95/p99` và `error_rate`.
- Xuất báo cáo có cấu trúc để dùng cho luận văn/báo cáo kỹ thuật: bảng, CSV, JSON, biểu đồ.

## Cấu trúc thư mục

```text
evaluation-rag/
├── dataset/
│   └── query_set.v1.json
├── notebooks/
│   └── rag_evaluation_no_groundtruth.ipynb
└── output/                 # kết quả sinh ra sau mỗi lần chạy notebook
```

## Dataset query benchmark

Mỗi phần tử trong file JSON có dạng:

```json
{
  "id": "IUH_001",
  "query": "điểm chuẩn ngành công nghệ thông tin IUH năm 2025",
  "university_code": "IUH",
  "notes": "ghi chú nếu cần"
}
```

- `id`: mã query để đối chiếu.
- `query`: câu hỏi đầu vào.
- `university_code`: tùy chọn, truyền vào API `/api/v1/search`.
- `notes`: ghi chú nghiên cứu.

## Cách chạy bằng Notebook

1. Export biến môi trường cho Judge model (OpenAI-compatible):

```bash
export JUDGE_API_KEY="<your_api_key>"
export JUDGE_MODEL="gpt-4o-mini"
export JUDGE_BASE_URL="https://api.openai.com/v1"
```

2. Mở `evaluation-rag/notebooks/rag_evaluation_no_groundtruth.ipynb`.
3. Kiểm tra biến cấu hình (`BASE_URL`, `SEARCH_ENDPOINT`, `CHAT_ENDPOINT`, `DATASET_PATH`).
4. Chạy tuần tự các cell.

## Cách chạy bằng RAGAS script

Bạn có thể chạy pipeline theo đúng thư viện `ragas`:

```bash
pip install ragas langchain-openai pandas requests
export OPENAI_API_KEY="<your_api_key>"
python evaluation-rag/scripts/ragas_eval.py \
  --base-url http://localhost:8000 \
  --input evaluation-rag/dataset/query_set.v1.json \
  --judge-model gpt-4o-mini
```

Chạy ổn định hơn cho backend cloud (timeout/retry):

```bash
python evaluation-rag/scripts/ragas_eval.py \
  --base-url https://admission-rag-chatbot-backend.vercel.app \
  --input evaluation-rag/dataset/query_set.v1.json \
  --judge-model gpt-4o-mini \
  --timeout 90 \
  --retries 4 \
  --retry-backoff 2
```

Chạy thử nhanh một phần dataset:

```bash
python evaluation-rag/scripts/ragas_eval.py \
  --base-url https://admission-rag-chatbot-backend.vercel.app \
  --max-samples 20
```

Rerun chỉ các query bị fail từ lần trước:

```bash
python evaluation-rag/scripts/ragas_eval.py \
  --base-url https://admission-rag-chatbot-backend.vercel.app \
  --failed-input evaluation-rag/output/<timestamp>/failed_queries.csv \
  --retries 5 \
  --retry-backoff 2
```

Script này đánh giá reference-free với các metric:
- `context_recall` (LLMContextRecall)
- `faithfulness`

và luôn xuất thêm latency/error metrics ở mức hệ thống.

### Tham số quan trọng

- `--timeout`: timeout mỗi request (giây).
- `--retries`: số lần retry khi gặp timeout hoặc HTTP 5xx.
- `--retry-backoff`: thời gian chờ giữa các lần retry.
- `--max-samples`: giới hạn số query để chạy nhanh (0 = chạy toàn bộ).
- `--failed-input`: nhận file `failed_queries.csv` để rerun phần fail.

## Đầu ra

Sau mỗi lần chạy, notebook tạo một thư mục timestamp trong `evaluation-rag/output` gồm:

- `config.json`
- `raw_results.json`
- `per_query_metrics.csv`
- `summary_metrics.csv`
- `failed_queries.csv`
- `report.md`
- `charts/quality_scores.png`
- `charts/latency.png`

## Quy trình nghiên cứu đề xuất

1. Chuẩn hóa bộ câu hỏi benchmark (nên từ 50+ query, đa intent).
2. Chạy baseline với cấu hình hiện tại.
3. Thay đổi từng thành phần retrieval/rerank/prompt và chạy lại.
4. So sánh các lần chạy bằng `summary_metrics.csv` và biểu đồ.
5. Nếu cần kiểm chứng sâu, lấy một mẫu nhỏ để đánh giá thủ công bổ sung.
