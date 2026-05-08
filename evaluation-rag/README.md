# RAG Evaluation Suite

Bộ công cụ đánh giá hệ thống RAG theo hướng nghiên cứu khoa học, tập trung vào độ chính xác truy vấn vector retrieval.

## Mục tiêu

- Đo lường chất lượng retrieval bằng các chỉ số: `Recall@K`, `Precision@K`, `HitRate@K`, `MRR@K`, `nDCG@K`.
- Đo lường hiệu năng: latency `mean/p50/p95/p99`.
- Xuất báo cáo có cấu trúc để dùng cho luận văn/báo cáo kỹ thuật: bảng, CSV, JSON, biểu đồ.

## Cấu trúc thư mục

```text
evaluation-rag/
├── dataset/
│   ├── ground_truth.example.json
│   └── ground_truth.v1.json
├── notebooks/
│   └── rag_evaluation.ipynb
└── output/                 # kết quả sinh ra sau mỗi lần chạy notebook
```

## Dataset ground-truth

Mỗi phần tử trong file JSON có dạng:

```json
{
  "id": "IUH_001",
  "query": "điểm chuẩn ngành công nghệ thông tin IUH năm 2025",
  "university_code": "IUH",
  "relevant_chunk_ids": ["chunk_123", "chunk_456"],
  "notes": "ghi chú nếu cần"
}
```

- `id`: mã query để đối chiếu.
- `query`: câu hỏi đầu vào.
- `university_code`: tùy chọn, truyền vào API `/api/v1/search`.
- `relevant_chunk_ids`: danh sách chunk đúng (ground-truth).
- `notes`: ghi chú nghiên cứu.

## Cách chạy bằng Notebook

1. Mở `evaluation-rag/notebooks/rag_evaluation.ipynb`.
2. Kiểm tra biến cấu hình (`BASE_URL`, `ENDPOINT`, `DATASET_PATH`, `KS`).
3. Chạy tuần tự các cell.

## Đầu ra

Sau mỗi lần chạy, notebook tạo một thư mục timestamp trong `evaluation-rag/output` gồm:

- `config.json`
- `raw_results.json`
- `per_query_metrics.csv`
- `summary_metrics.csv`
- `report.md`
- `charts/aggregate_metrics.png`
- `charts/latency_percentiles.png`

## Quy trình nghiên cứu đề xuất

1. Chuẩn hóa bộ câu hỏi benchmark (nên từ 50+ query).
2. Gán nhãn `relevant_chunk_ids` cho từng query.
3. Chạy baseline với cấu hình hiện tại.
4. Thay đổi từng thành phần retrieval/rerank và chạy lại.
5. So sánh các lần chạy bằng `summary_metrics.csv` và biểu đồ.
