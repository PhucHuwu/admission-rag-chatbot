# EVALUATE.md — Hướng dẫn đánh giá RAG Chatbot Tuyển Sinh

> Tài liệu này là runbook đầy đủ cho AI agent triển khai pipeline đánh giá.
> Mọi quyết định thiết kế đều dựa trên paper **RAGAS: Automated Evaluation of
> Retrieval Augmented Generation** (Es et al., 2023 — `../2309.15217v2.pdf`).

---

## 1. Mục tiêu

Đánh giá hệ thống RAG theo **ba chiều chất lượng** từ paper RAGAS, không cần ground-truth:

| Metric | Định nghĩa từ paper | Công thức |
|---|---|---|
| **Faithfulness** | Claims trong answer có suy ra được từ context không | `\|V\| / \|S\|` — tỉ lệ mệnh đề được xác nhận |
| **Answer Relevancy** | Answer có trả lời đúng câu hỏi gốc không | cosine sim trung bình của n câu hỏi ngược sinh ra từ answer |
| **Context Precision** | Context có tập trung, ít thông tin thừa không | số câu cần thiết / tổng câu trong context |

Ngoài ra đo thêm hai metric đặc thù domain tuyển sinh:

- **Data Sufficiency Accuracy** — chatbot có nhận đúng khi không có dữ liệu không (field `data_sufficient` trong response)
- **Numerical Faithfulness** — các con số trong answer có khớp với context không (chống hallucinate điểm chuẩn, học phí)

Và metric hệ thống:

- Latency: mean, p50, p95, p99 (ms)
- Error rate (HTTP 5xx hoặc timeout)

---

## 2. Kiến trúc hệ thống cần hiểu

Pipeline backend (`backend/src/modules/`):

```
query → query-preprocess → rag-tools (intent + expand)
      → query-transform (multi_query / hyde / step_back / rewrite / raw)
      → embedding → qdrant (candidateK=100)
      → reranker (keyword 40% + LLM 60%) → topK=8
      → llm (deepseek hoặc kimi) → answer
```

**API endpoints:**

```
POST /api/v1/search
  Body:  { "query": string, "university_code"?: string }
  Response: { "hits": [{ "chunk_id": string, "score": number, "text": string, "metadata": object }] }

POST /api/v1/chat
  Body:  { "query": string, "session_id"?: string, "university_code"?: string }
  Response: { "answer": string, "session_id": string, "used_chunks": number, "data_sufficient": boolean, "note": string|null }
```

**LLM providers** (env `LLM_PROVIDER`): `deepseek` (default) hoặc `kimi`

**Reranker** hoạt động khi `hits.length > TOP_K`. Tắt bằng cách set `TOP_K >= CANDIDATE_K` (100).

**Query transform** phân loại tự động: `multi_query` (câu ≤3 từ), `hyde` (có từ khoá điểm chuẩn/học phí), `step_back` (tại sao/why), `rewrite` (có session history), `raw` (còn lại).

---

## 3. Cấu trúc thư mục sau khi hoàn thành

```
evaluation-rag/
├── EVALUATE.md               ← file này
├── .env.example
├── dataset/
│   └── query_set.v1.json     ← phải được bổ sung fields (xem Bước 1)
├── notebooks/
│   └── rag_evaluation_no_groundtruth.ipynb
├── scripts/
│   ├── collect.py            ← Bước 2: gọi API, lưu raw (VIẾT MỚI)
│   ├── evaluate.py           ← Bước 3: chấm điểm RAGAS từ raw (VIẾT MỚI)
│   ├── report.py             ← Bước 5: sinh báo cáo + biểu đồ (VIẾT MỚI)
│   ├── ragas_eval.py         ← script cũ, KHÔNG xóa, KHÔNG dùng nữa
│   └── run_ragas_eval.sh
└── output/
    └── <run_id>/             ← sinh ra sau mỗi lần chạy
        ├── config.json
        ├── raw_results.json
        ├── per_query_metrics.csv
        ├── summary_metrics.csv
        ├── failed_queries.csv
        └── charts/
            ├── radar.png
            └── latency_cdf.png
```

---

## 4. Bước 1 — Chuẩn bị dataset

### 4.1 Vấn đề hiện tại

File `dataset/query_set.v1.json` hiện có **72 câu** nhưng mỗi phần tử chỉ có field `"query"`.
Script `collect.py` cần thêm ba field: `id`, `university_code`, `category`, `expected_has_answer`.

### 4.2 Schema chuẩn

```json
{
  "id": "IUH_001",
  "query": "điểm chuẩn ngành công nghệ thông tin IUH năm 2025",
  "university_code": "IUH",
  "category": "diem_chuan",
  "expected_has_answer": true
}
```

Năm giá trị hợp lệ cho `category`:

| Giá trị | Mô tả |
|---|---|
| `diem_chuan` | Câu hỏi về điểm chuẩn |
| `hoc_phi` | Câu hỏi về học phí |
| `phuong_thuc_to_hop` | Phương thức xét tuyển, tổ hợp môn, chỉ tiêu |
| `so_sanh` | So sánh nhiều trường |
| `out_of_scope` | Câu hỏi ngoài phạm vi dữ liệu (ký túc xá, học bổng chung, thủ tục chung) |

`expected_has_answer`: `true` nếu thông tin có thể có trong dữ liệu crawler, `false` nếu chắc chắn không có.

### 4.3 Quy tắc gán university_code

Lấy từ tên trường trong câu hỏi. Mapping các mã đang có trong hệ thống:

```
IUH, HLU, BVU, DHT, DHA, DDB, HGH, HHA, LBH, MDA, QHE, SKN, YHB
```

Câu hỏi so sánh nhiều trường → `university_code: ""`.
Câu hỏi chung (không nhắc tên trường) → `university_code: ""`.

### 4.4 Task cho agent

Mở file `dataset/query_set.v1.json`, đọc từng phần tử, bổ sung các fields theo quy tắc trên.
Lưu lại cùng file. Không thêm câu hỏi mới, không xóa câu hỏi cũ. Kết quả phải là 72 phần tử.

---

## 5. Bước 2 — Viết `scripts/collect.py`

Script này **chỉ gọi API** và lưu kết quả thô. Không chạm đến RAGAS.

### 5.1 Mục đích tách phase

Gọi API và chấm điểm RAGAS tách nhau vì:
- API gọi mất thời gian và có thể lỗi giữa chừng
- RAGAS judge gọi OpenAI tốn chi phí
- Nếu backend lỗi, không mất chi phí judge đã chạy

### 5.2 Cách chạy

```bash
python evaluation-rag/scripts/collect.py \
  --base-url http://localhost:8000 \
  --input evaluation-rag/dataset/query_set.v1.json \
  --output-dir evaluation-rag/output \
  --timeout 60 \
  --retries 3 \
  --retry-backoff 2
```

### 5.3 Tham số bắt buộc

| Tham số | Mô tả | Default |
|---|---|---|
| `--base-url` | URL backend | `http://localhost:8000` |
| `--input` | Path đến query_set.v1.json | `evaluation-rag/dataset/query_set.v1.json` |
| `--output-dir` | Thư mục output | `evaluation-rag/output` |
| `--timeout` | Timeout mỗi request (giây) | `60` |
| `--retries` | Số lần retry khi gặp 5xx hoặc timeout | `3` |
| `--retry-backoff` | Giây chờ giữa các retry | `2` |
| `--max-samples` | Giới hạn số câu (0 = tất cả) | `0` |
| `--run-id` | Tên thư mục output (mặc định timestamp) | timestamp |

### 5.4 Output của collect.py

Tạo thư mục `output/<run_id>/` chứa:

- `config.json` — tham số chạy
- `raw_results.json` — array, mỗi phần tử có cấu trúc:

```json
{
  "id": "IUH_001",
  "query": "điểm chuẩn ngành công nghệ thông tin IUH năm 2025",
  "university_code": "IUH",
  "category": "diem_chuan",
  "expected_has_answer": true,
  "status": "ok",
  "error": "",
  "search_latency_ms": 1234.5,
  "chat_latency_ms": 2876.3,
  "total_latency_ms": 4110.8,
  "retrieved_contexts": ["đoạn text 1...", "đoạn text 2..."],
  "retrieved_context_count": 5,
  "data_sufficient": true,
  "answer": "Điểm chuẩn ngành CNTT IUH năm 2025 là 22.5 điểm..."
}
```

- `failed_queries.csv` — các query có `status != "ok"`

### 5.5 Logic gọi API

1. Gọi `POST /api/v1/search` với `{ query, university_code }` (bỏ `university_code` nếu rỗng)
2. Lấy field `hits`, giữ tối đa 5 phần tử đầu, lấy field `text` từ mỗi hit, cắt tối đa 1200 ký tự
3. Gọi `POST /api/v1/chat` với `{ query, university_code }` (bỏ `university_code` nếu rỗng)
4. Lấy field `answer` và `data_sufficient`
5. Retry khi gặp `requests.exceptions.Timeout` hoặc HTTP status >= 500

---

## 6. Bước 3 — Viết `scripts/evaluate.py`

Script này đọc `raw_results.json` đã có, chạy RAGAS và metric domain-specific, ghi ra CSV.

### 6.1 Cách chạy

```bash
export OPENAI_API_KEY="<key>"

python evaluation-rag/scripts/evaluate.py \
  --run-dir evaluation-rag/output/<run_id> \
  --judge-model gpt-4o-mini
```

### 6.2 Tham số

| Tham số | Mô tả | Default |
|---|---|---|
| `--run-dir` | Thư mục output từ collect.py | bắt buộc |
| `--judge-model` | Model OpenAI dùng làm judge | `gpt-4o-mini` |
| `--judge-base-url` | Base URL nếu dùng proxy OpenAI-compatible | `https://api.openai.com/v1` |

### 6.3 Metric RAGAS cần dùng

```python
from ragas.metrics import Faithfulness, AnswerRelevancy, ContextPrecision

metrics = [Faithfulness(), AnswerRelevancy(), ContextPrecision()]
```

> **Lưu ý quan trọng:** Script cũ `ragas_eval.py` dùng `LLMContextRecall` — metric này
> **yêu cầu ground-truth reference** và sẽ cho kết quả sai khi không có. Phải thay bằng
> `ContextPrecision` (reference-free), đúng với phương pháp trong paper RAGAS mục 3.

**Cấu trúc dữ liệu truyền vào RAGAS:**

```python
ragas_rows = [
    {
        "user_input": item["query"],
        "retrieved_contexts": item["retrieved_contexts"],  # list[str]
        "response": item["answer"],
    }
    for item in raw_results
    if item["status"] == "ok" and item["retrieved_contexts"]
]
```

### 6.4 Metric domain-specific (tự cài, không dùng RAGAS)

**Data Sufficiency Accuracy:**

```python
# Với các query có expected_has_answer = True
# Đúng khi data_sufficient = True
# Với các query có expected_has_answer = False
# Đúng khi data_sufficient = False

has_answer_items  = [r for r in raw if r["expected_has_answer"] == True  and r["status"] == "ok"]
no_answer_items   = [r for r in raw if r["expected_has_answer"] == False and r["status"] == "ok"]

has_answer_acc = sum(1 for r in has_answer_items  if r["data_sufficient"] == True)  / max(len(has_answer_items), 1)
no_answer_acc  = sum(1 for r in no_answer_items   if r["data_sufficient"] == False) / max(len(no_answer_items), 1)
data_sufficiency_accuracy = (has_answer_acc + no_answer_acc) / 2
```

**Numerical Faithfulness:**

```python
import re

def extract_numbers(text: str) -> list[str]:
    # Trích số dạng điểm: 22.5, 25.0, 18, 24.75
    return re.findall(r'\b\d{1,2}(?:\.\d{1,2})?\b', text)

def numerical_faithfulness(answer: str, contexts: list[str]) -> float:
    nums = extract_numbers(answer)
    if not nums:
        return 1.0  # không có số → không có gì để kiểm tra
    context_text = " ".join(contexts)
    matched = sum(1 for n in nums if n in context_text)
    return matched / len(nums)
```

Tính trung bình `numerical_faithfulness` trên toàn bộ dataset.

### 6.5 Output của evaluate.py

Ghi vào cùng thư mục `<run_id>/`:

**`per_query_metrics.csv`** — mỗi dòng là một query:

```
id, query, category, expected_has_answer, status, faithfulness, answer_relevancy,
context_precision, numerical_faithfulness, data_sufficient, total_latency_ms
```

**`summary_metrics.csv`** — một dòng duy nhất:

```
faithfulness, answer_relevancy, context_precision, rag_score,
numerical_faithfulness, data_sufficiency_accuracy,
latency_mean_ms, latency_p50_ms, latency_p95_ms, latency_p99_ms,
error_rate, query_count_total, query_count_ok, query_count_error
```

Công thức RAG Score (trọng số từ tầm quan trọng trong paper):

```
rag_score = faithfulness * 0.4 + answer_relevancy * 0.35 + context_precision * 0.25
```

---

## 7. Bước 4 — Ablation study

Chạy `collect.py` ba lần với ba cấu hình backend khác nhau. Mỗi lần dùng `--run-id` khác nhau.

### 7.1 Config 1: Full pipeline (baseline)

Backend chạy với cấu hình mặc định (`.env` gốc). `TOP_K=8`, `CANDIDATE_K=100`.

```bash
python evaluation-rag/scripts/collect.py \
  --base-url http://localhost:8000 \
  --run-id ablation_baseline
```

### 7.2 Config 2: Tắt reranker

`RerankerService.rerank()` trong `backend/src/modules/reranker/reranker.service.ts`
chỉ rerank khi `hits.length > topK`. Để tắt reranker, thêm biến môi trường `RERANKER_ENABLED=false`
vào backend và sửa `reranker.service.ts` để early-return khi env này là `false`.

Cách sửa `reranker.service.ts`:

```typescript
async rerank(query: string, hits: RankedHit[], topK = 8): Promise<RankedHit[]> {
  const enabled = process.env.RERANKER_ENABLED !== 'false';
  if (!enabled || hits.length <= topK) return hits.slice(0, topK);
  // ... phần còn lại giữ nguyên
}
```

Restart backend với `RERANKER_ENABLED=false`, rồi chạy:

```bash
python evaluation-rag/scripts/collect.py \
  --base-url http://localhost:8000 \
  --run-id ablation_no_reranker
```

### 7.3 Config 3: Tắt query transform

Thêm biến `QUERY_TRANSFORM_ENABLED=false` và sửa `query-transform.service.ts`:

```typescript
async transform(query: string, recentQueries: string[]): Promise<TransformedQueries> {
  const enabled = process.env.QUERY_TRANSFORM_ENABLED !== 'false';
  if (!enabled) return { original: query, variants: [query], strategy: 'raw' };
  // ... phần còn lại giữ nguyên
}
```

Restart backend với `QUERY_TRANSFORM_ENABLED=false`, rồi chạy:

```bash
python evaluation-rag/scripts/collect.py \
  --base-url http://localhost:8000 \
  --run-id ablation_no_transform
```

### 7.4 Chạy evaluate.py cho cả 3 config

```bash
python evaluation-rag/scripts/evaluate.py --run-dir evaluation-rag/output/ablation_baseline
python evaluation-rag/scripts/evaluate.py --run-dir evaluation-rag/output/ablation_no_reranker
python evaluation-rag/scripts/evaluate.py --run-dir evaluation-rag/output/ablation_no_transform
```

---

## 8. Bước 5 — Viết `scripts/report.py`

Script sinh báo cáo tổng hợp từ nhiều run, dùng cho luận văn.

### 8.1 Cách chạy

```bash
python evaluation-rag/scripts/report.py \
  --runs \
    evaluation-rag/output/ablation_baseline \
    evaluation-rag/output/ablation_no_reranker \
    evaluation-rag/output/ablation_no_transform \
  --labels "Full pipeline" "Bỏ reranker" "Bỏ query transform" \
  --output-dir evaluation-rag/output/report
```

### 8.2 Biểu đồ bắt buộc

**`charts/radar.png`** — Radar chart so sánh 3 config trên 3 RAGAS metric.
Dùng `matplotlib` với `projection='polar'`. Trục: Faithfulness, Answer Relevancy, Context Precision.
Mỗi config một đường. Legend ở ngoài chart.

**`charts/latency_cdf.png`** — CDF (Cumulative Distribution Function) của `total_latency_ms`
trên full pipeline. Trục X: latency (ms), trục Y: tỉ lệ tích lũy (0–1).
Vẽ đường dọc tại p50, p95, p99.

**`charts/per_category.png`** — Bar chart grouped: trục X là category, mỗi group 3 bar
(Faithfulness, Answer Relevancy, Context Precision). Chỉ vẽ cho run baseline.

### 8.3 `report/report.md`

File markdown tổng hợp kết quả, gồm:

1. Bảng summary_metrics của 3 config (như Table 1 trong paper RAGAS)
2. Nhận xét ngắn về từng config dựa trên delta
3. Per-category của baseline

Mẫu bảng:

```markdown
| Config | Faithfulness | Ans. Relevancy | Ctx. Precision | RAG Score | Latency p95 |
|---|---|---|---|---|---|
| Full pipeline | 0.82 | 0.76 | 0.61 | 0.73 | 3200ms |
| Bỏ reranker   | 0.79 ▼0.03 | 0.74 ▼0.02 | 0.50 ▼0.11 | 0.68 ▼0.05 | 2100ms |
| Bỏ query transform | 0.80 ▼0.02 | 0.68 ▼0.08 | 0.59 ▼0.02 | 0.69 ▼0.04 | 2800ms |
```

---

## 9. Phụ thuộc Python

Thêm vào `requirements.txt` hoặc cài trực tiếp:

```
ragas>=0.2.0
langchain-openai>=0.1.0
pandas>=2.0.0
requests>=2.31.0
matplotlib>=3.8.0
numpy>=1.26.0
```

Cài:

```bash
pip install ragas langchain-openai pandas requests matplotlib numpy --break-system-packages
```

---

## 10. Checklist agent

Thực hiện theo thứ tự. Đánh dấu `[x]` sau khi hoàn thành từng mục.

- [ ] **1.** Đọc paper `../2309.15217v2.pdf` để hiểu định nghĩa Faithfulness, Answer Relevancy, Context Precision
- [ ] **2.** Bổ sung fields `id`, `university_code`, `category`, `expected_has_answer` vào `dataset/query_set.v1.json` (72 phần tử, không thêm/xóa)
- [ ] **3.** Viết `scripts/collect.py` theo spec Bước 2
- [ ] **4.** Sửa `backend/src/modules/reranker/reranker.service.ts` — thêm guard `RERANKER_ENABLED`
- [ ] **5.** Sửa `backend/src/modules/query-transform/query-transform.service.ts` — thêm guard `QUERY_TRANSFORM_ENABLED`
- [ ] **6.** Chạy `collect.py` 3 lần với 3 config ablation (baseline, no_reranker, no_transform)
- [ ] **7.** Viết `scripts/evaluate.py` theo spec Bước 3 — dùng `Faithfulness + AnswerRelevancy + ContextPrecision`, **không** dùng `LLMContextRecall`
- [ ] **8.** Chạy `evaluate.py` cho cả 3 run
- [ ] **9.** Viết `scripts/report.py` theo spec Bước 5
- [ ] **10.** Chạy `report.py`, kiểm tra 3 file chart + `report.md` sinh ra đúng format

---

## 11. Ngưỡng chấp nhận

| Metric | Ngưỡng tốt | Ngưỡng chấp nhận | Ghi chú |
|---|---|---|---|
| Faithfulness | ≥ 0.80 | 0.60 – 0.79 | Ưu tiên cao nhất, ảnh hưởng trust |
| Answer Relevancy | ≥ 0.75 | 0.55 – 0.74 | |
| Context Precision | ≥ 0.65 | 0.45 – 0.64 | Thường thấp nhất do retrieval lấy thừa chunk |
| RAG Score | ≥ 0.73 | 0.58 – 0.72 | |
| Numerical Faithfulness | ≥ 0.90 | 0.75 – 0.89 | Quan trọng với domain điểm chuẩn |
| Data Sufficiency Acc | ≥ 0.80 | 0.65 – 0.79 | |
| Latency p95 | ≤ 4000ms | 4000 – 8000ms | |

---

## 12. Sinh câu hỏi từ dữ liệu crawler (AI-generated queries)

### 12.1 Nguyên tắc hybrid

Bộ dataset dùng hai lớp câu hỏi tách biệt, đánh giá riêng, báo cáo riêng:

| Lớp | Nguồn | Số câu | Vai trò |
|---|---|---|---|
| **Core set** | Viết tay (`query_set.v1.json`) | 72 | Phản ánh hành vi người dùng thực |
| **Extended set** | AI sinh từ crawler data | ~50 | Đảm bảo coverage đầy đủ theo dữ liệu |

Paper RAGAS (mục 4) cũng dùng ChatGPT để sinh câu hỏi từ Wikipedia — phương pháp này hợp lệ với điều kiện câu hỏi phải *có thể trả lời được* từ dữ liệu có trong hệ thống.

### 12.2 Nguồn dữ liệu để sinh câu hỏi

Đọc từ `crawler/output/*.json` — 296 file, mỗi file là một trường. Cấu trúc có thể dùng để sinh câu hỏi:

| Field | Nội dung | Loại câu hỏi sinh ra |
|---|---|---|
| `admission_methods[].programs[].program_name` | Tên ngành | điểm chuẩn, tổ hợp, chỉ tiêu |
| `admission_methods[].programs[].subject_groups` | Tổ hợp môn | tổ hợp |
| `admission_methods[].method_name` | Tên phương thức | phương thức xét tuyển |
| `tuition_text` | Học phí theo ngành (khi có) | học phí |
| `admission_overview` | Mô tả chung | phương thức, điều kiện |
| `university.name` | Tên trường | dùng trong mọi câu hỏi |

> **Lưu ý:** Hầu hết `cutoff_scores_text` chỉ là link ngoài, không có số liệu thực.
> Không sinh câu hỏi hỏi điểm chuẩn cụ thể từ field này trừ khi text chứa số liệu thực.
> Chỉ sinh câu hỏi điểm chuẩn khi `cutoff_scores_text` chứa số dạng `\d{2}(\.\d{1,2})?` điểm.

### 12.3 Viết `scripts/generate_queries.py`

#### Cách chạy

```bash
export OPENAI_API_KEY="<key>"

python evaluation-rag/scripts/generate_queries.py \
  --crawler-dir crawler/output \
  --existing-dataset evaluation-rag/dataset/query_set.v1.json \
  --output evaluation-rag/dataset/query_set.extended.json \
  --model gpt-4o-mini \
  --target-count 50 \
  --schools-per-run 10
```

#### Tham số

| Tham số | Mô tả | Default |
|---|---|---|
| `--crawler-dir` | Thư mục chứa các file JSON trường | `crawler/output` |
| `--existing-dataset` | File query hiện tại (để tránh trùng lặp) | bắt buộc |
| `--output` | File output cho extended set | bắt buộc |
| `--model` | Model sinh câu hỏi | `gpt-4o-mini` |
| `--target-count` | Số câu hỏi cần sinh | `50` |
| `--schools-per-run` | Số trường xử lý mỗi batch | `10` |

#### Logic chọn trường

Không sinh đều từ 296 trường — chỉ chọn những trường có dữ liệu đủ phong phú:

```python
def score_school(data: dict) -> int:
    score = 0
    methods = data.get("admission_methods", [])
    all_programs = [p for m in methods for p in m.get("programs", [])]

    if len(all_programs) >= 5:       score += 3
    if len(methods) >= 2:            score += 2
    tuition = data.get("tuition_text") or ""
    if len(tuition) > 100:           score += 2
    overview = data.get("admission_overview") or ""
    if len(overview) > 200:          score += 1
    return score

# Chọn top 25 trường có điểm cao nhất
# Ưu tiên các trường KHÔNG có trong core set (72 câu)
```

Các trường đã có nhiều câu trong core set (IUH, HLU, BVU...) nên có trọng số thấp hơn để tăng diversity.

#### Prompt sinh câu hỏi

Với mỗi trường được chọn, truyền context data vào LLM và dùng prompt sau:

```
Bạn là học sinh lớp 12 đang tìm hiểu thông tin tuyển sinh đại học Việt Nam năm 2026.

Dựa trên thông tin tuyển sinh của {university_name} ({university_code}) dưới đây,
hãy sinh ra ĐÚNG {n} câu hỏi khác nhau mà một học sinh thực sự có thể hỏi.

THÔNG TIN TRƯỜNG:
{context}

YÊU CẦU:
1. Mỗi câu hỏi phải có thể trả lời được từ thông tin trên
2. Câu hỏi phải tự nhiên như học sinh thực sự hỏi (không quá formal)
3. Phân bố đều các loại: điểm chuẩn, tổ hợp môn, phương thức xét tuyển, học phí, chỉ tiêu
4. Đề cập cụ thể tên ngành hoặc phương thức (không hỏi chung chung)
5. Độ dài câu hỏi: 8–20 từ
6. Viết tiếng Việt tự nhiên, có thể dùng từ viết tắt thông thường

KHÔNG sinh câu hỏi về:
- Ký túc xá, học bổng (nếu không có trong thông tin)
- Học phí nếu tuition_text không có số liệu cụ thể
- Điểm chuẩn nếu cutoff_scores_text không có số cụ thể

Trả về JSON array, mỗi phần tử là object:
{
  "query": "câu hỏi...",
  "university_code": "{university_code}",
  "category": "diem_chuan|hoc_phi|phuong_thuc_to_hop|so_sanh|out_of_scope",
  "expected_has_answer": true|false,
  "source": "ai_generated"
}
```

#### Context truyền vào prompt

Xây dựng context từ data của trường, tối đa 800 token:

```python
def build_context(data: dict) -> str:
    parts = []
    name = data["university"]["name"]
    code = data["university"]["code"]
    parts.append(f"Trường: {name} ({code})")

    methods = data.get("admission_methods", [])
    for m in methods[:3]:                    # tối đa 3 phương thức
        parts.append(f"\nPhương thức: {m['method_name']}")
        progs = m.get("programs", [])
        for p in progs[:8]:                  # tối đa 8 ngành/phương thức
            groups = ", ".join(p.get("subject_groups", [])[:5])
            parts.append(f"  - {p['program_name']} | tổ hợp: {groups}")

    tuition = data.get("tuition_text") or ""
    if len(tuition) > 100:
        parts.append(f"\nHọc phí: {tuition[:400]}")

    overview = data.get("admission_overview") or ""
    if len(overview) > 100:
        parts.append(f"\nTổng quan: {overview[:300]}")

    return "\n".join(parts)
```

### 12.4 Lọc và dedup sau khi sinh

Sau khi sinh xong, chạy các bước lọc:

**Dedup với core set:** Tính sentence embedding (dùng `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` hoặc API OpenAI) cho từng câu mới, loại bỏ câu có cosine similarity > 0.85 với bất kỳ câu nào trong 72 câu gốc.

**Lọc câu hỏi kém chất lượng:**
- Loại câu ngắn hơn 5 từ hoặc dài hơn 25 từ
- Loại câu trùng lặp trong chính extended set (cosine sim > 0.90)
- Loại câu chứa thuật ngữ kỹ thuật (`vector`, `embedding`, `chunk`, `retrieval`)
- Loại câu `expected_has_answer = true` nhưng context truyền vào không chứa thông tin liên quan

**Kiểm tra balance category:**

```python
from collections import Counter
cats = Counter(q["category"] for q in extended_queries)
# Mục tiêu: mỗi category >= 8 câu, không category nào > 20 câu
```

### 12.5 Output — `dataset/query_set.extended.json`

Format giống hệt `query_set.v1.json` nhưng có thêm field `source`:

```json
[
  {
    "id": "EXT_001",
    "query": "ngành y đa khoa BMU xét tuyển bằng tổ hợp gì",
    "university_code": "BMU",
    "category": "phuong_thuc_to_hop",
    "expected_has_answer": true,
    "source": "ai_generated"
  }
]
```

ID dùng prefix `EXT_` để phân biệt với core set (`IUH_001`, `HLU_001`...).

### 12.6 Cách chạy evaluation cho extended set

Sau khi có `query_set.extended.json`, chạy collect và evaluate riêng:

```bash
# Thu thập
python evaluation-rag/scripts/collect.py \
  --input evaluation-rag/dataset/query_set.extended.json \
  --run-id extended_baseline

# Chấm điểm
python evaluation-rag/scripts/evaluate.py \
  --run-dir evaluation-rag/output/extended_baseline
```

Khi viết báo cáo, trình bày bảng kết quả riêng biệt:

```markdown
## Kết quả đánh giá

### Core set (72 câu — viết tay)
| Faithfulness | Answer Relevancy | Context Precision | RAG Score |
| 0.82 | 0.76 | 0.61 | 0.73 |

### Extended set (50 câu — AI-generated từ crawler data)
| Faithfulness | Answer Relevancy | Context Precision | RAG Score |
| 0.85 | 0.79 | 0.68 | 0.77 |
```

> Extended set thường cho điểm cao hơn core set vì câu hỏi AI sinh ra
> luôn có thể trả lời được từ dữ liệu — đây là bias cần ghi chú rõ trong luận văn.

### 12.7 Bổ sung checklist (tiếp theo mục 10)

- [ ] **11.** Cài thêm dependency: `pip install sentence-transformers --break-system-packages`
- [ ] **12.** Viết `scripts/generate_queries.py` theo spec mục 12.3
- [ ] **13.** Chạy script, kiểm tra output có đủ 50 câu, balance category, không trùng core set
- [ ] **14.** Chạy `collect.py` + `evaluate.py` cho extended set
- [ ] **15.** Trình bày kết quả hai bộ riêng biệt trong `report.md`, ghi rõ bias của extended set

---

## 14. Tài liệu tham chiếu

- Paper: `../2309.15217v2.pdf` — Es et al., 2023, "RAGAS: Automated Evaluation of Retrieval Augmented Generation"
- RAGAS library: https://github.com/explodinggradients/ragas
- Backend search service: `backend/src/modules/search/search.service.ts`
- Backend chat service: `backend/src/modules/chat/chat.service.ts`
- Backend reranker: `backend/src/modules/reranker/reranker.service.ts`
- Backend query-transform: `backend/src/modules/query-transform/query-transform.service.ts`
- Dataset: `dataset/query_set.v1.json`
