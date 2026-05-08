# Hướng dẫn đánh giá RAG Chatbot Tuyển Sinh

Tài liệu này giải thích ý nghĩa từng chỉ số đánh giá, cách tính toán và cách sử dụng chúng để cải thiện hệ thống.

---

## 1. RAGAS Metrics (Chất lượng RAG)

Các chỉ số này đánh giá chất lượng của Retrieval-Augmented Generation pipeline. Trong dự án này, chúng được tính bằng **RAGAS framework** với LLM judge (GPT-4o-mini)

### 1.1. Faithfulness (Độ trung thực)

**Ý nghĩa**: Đo lường mức độ câu trả lồ của chatbot **dựa trên và phù hợp với** các context đã retrieve. Nếu câu trả lồ chứa thông tin không có trong context, faithfulness sẽ thấp.

**Cách tính (RAGAS)**:

- LLM judge phân tích từng câu trong câu trả lồ
- Kiểm tra xem câu đó có thể suy ra từ context hay không
- Tỷ lệ câu hợp lệ / tổng số câu

**Cách tính (Synthetic/Heuristic)**:

- `numerical_faithfulness`: Kiểm tra số liệu trong câu trả lồ có xuất hiện trong context không
- `keyword_faithfulness`: Kiểm tra từ khóa quan trọng trong câu trả lồ có xuất hiện trong context không
- Faithfulness = 0.6 × numerical + 0.4 × keyword

**Phạm vi**: 0.0 – 1.0

- **> 0.85**: Rất tốt — câu trả lồ hoàn toàn dựa trên nguồn tài liệu
- **0.70 – 0.85**: Tốt — có thể có 1-2 thông tin không rõ nguồn
- **0.50 – 0.70**: Trung bình — chatbot đang "hallucinate" hoặc suy diễn quá mức
- **< 0.50**: Kém — nhiều thông tin sai hoặc không có cơ sở

**Cách cải thiện**:

- Tăng chất lượng context retrieval (reranker tốt hơn, top-k phù hợp)
- Điều chỉnh system prompt để chatbot chỉ trả lồ dựa trên context
- Thêm citation (trích dẫn nguồn) vào câu trả lồ

---

### 1.2. Answer Relevancy (Độ liên quan của câu trả lồ)

**Ý nghĩa**: Đo lường mức độ câu trả lồ **trực tiếp trả lồ câu hỏi** của ngườ dùng. Một câu trả lồ có thể faithful (đúng với context) nhưng không relevant (lạc đề).

**Cách tính (RAGAS)**:

- LLM judge tạo các câu hỏi tiềm năng dựa trên câu trả lồ
- So sánh sự tương đồng ngữ nghĩa giữa câu hỏi gốc và câu hỏi tiềm năng

**Cách tính (Synthetic/Heuristic)**:

- Tính độ chồng chéo từ khóa giữa câu hỏi và câu trả lồ
- Penalty cho câu trả lồ quá ngắn hoặc là refusal ("xin lỗi, tôi không biết")
- Bonus cho câu trả lồ dài, chi tiết

**Phạm vi**: 0.0 – 1.0

- **> 0.80**: Rất tốt — câu trả lồ sát câu hỏi, không thừa thãi
- **0.65 – 0.80**: Tốt — trả lồ đúng hướng nhưng có thể thiếu chi tiết
- **0.50 – 0.65**: Trung bình — câu trả lồ chung chung, không đi sâu vào câu hỏi
- **< 0.50**: Kém — lạc đề hoặc refusal không hợp lý

**Cách cải thiện**:

- Tối ưu query transformation/rewriting để retrieval sát câu hỏi hơn
- Điều chỉnh prompt template để yêu cầu chatbot trả lồ trực tiếp
- Kiểm tra các câu hỏi phức tạp (multi-hop, so sánh)

---

### 1.3. Context Precision (Độ chính xác của context)

**Ý nghĩa**: Đo lường tỷ lệ **các retrieved context thực sự liên quan** đến câu hỏi. Nếu retrieve 5 chunks nhưng chỉ 2 chunks hữu ích, context precision thấp.

**Cách tính (RAGAS)**:

- LLM judge đánh giá từng context xem có liên quan đến câu hỏi không
- Tính tỷ lệ context relevant / tổng số context

**Cách tính (Synthetic/Heuristic)**:

- Tính độ chồng chéo từ khóa giữa câu hỏi và mỗi context
- Trung bình trên tất cả context được retrieve

**Phạm vi**: 0.0 – 1.0

- **> 0.80**: Rất tốt — hầu hết context đều hữu ích
- **0.65 – 0.80**: Tốt — có vài context nhiễu nhưng không đáng kể
- **0.50 – 0.65**: Trung bình — nhiều context không liên quan, chatbot phải "tự lọc"
- **< 0.50**: Kém — retrieval đang lấy nhiều nhiễu, cần cải thiện embedding/search

**Cách cải thiện**:

- Dùng reranker (cross-encoder) để sắp xếp lại và lọc context
- Tinh chỉnh embedding model trên domain tuyển sinh
- Tối ưu chunk size và overlap
- Query expansion/rewriting để retrieval chính xác hơn

---

## 2. Domain-Specific Metrics (Chuyên biệt tuyển sinh)

### 2.1. Numerical Faithfulness (Độ trung thực số liệu)

**Ý nghĩa**: Trong domain tuyển sinh, số liệu (điểm chuẩn, học phí, chỉ tiêu) là quan trọng nhất. Chỉ số này kiểm tra xem các con số trong câu trả lồ có **xuất hiện trong context** không.

**Cách tính**:

```
numerical_faithfulness = (số lượng số trong answer khớp với context) / (tổng số số trong answer)
```

**Phạm vi**: 0.0 – 1.0

- **1.0**: Tất cả số liệu đều có nguồn gốc từ context
- **< 1.0**: Có số liệu chatbot tự "bịa" hoặc lấy từ knowledge ngầm

**Cách cải thiện**:

- Thêm system prompt: "Chỉ dùng số liệu từ context, không suy diễn"
- Kiểm tra lỗi OCR trong chunking (số liệu bị nhận dạng sai)
- Validate output bằng regex hoặc rule-based

---

### 2.2. Data Sufficiency Accuracy (Độ chính xác nhận diện đủ dữ liệu)

**Ý nghĩa**: Đo lường khả năng chatbot **biết từ chối trả lồ** khi context không đủ thông tin. Trong tuyển sinh, trả lồ sai về điểm chuẩn có thể gây hậu quả nghiêm trọng.

**Cách tính**:

```
data_sufficiency_accuracy = (accuracy_có_đáp_án + accuracy_không_đáp_án) / 2

accuracy_có_đáp_án = % trường hợp expected_has_answer=True mà data_sufficient=True
accuracy_không_đáp_án = % trường hợp expected_has_answer=False mà data_sufficient=False
```

**Phạm vi**: 0.0 – 1.0

- **> 0.80**: Rất tốt — chatbot biết rõ khi nào nên trả lồ, khi nào nên từ chối
- **0.60 – 0.80**: Tốt — còn vài trường hợp nhầm lẫn
- **0.40 – 0.60**: Trung bình — chatbot hay "đoán" khi không đủ dữ liệu
- **< 0.40**: Kém — nguy hiểm, chatbot trả lồ bừa bãi

**Cách cải thiện**:

- Thêm confidence threshold vào pipeline
- Training/fine-tuning với các câu hỏi out-of-scope
- Điều chỉnh prompt: "Nếu không đủ thông tin, hãy nói rõ và gợi ý nguồn tham khảo"

---

## 3. System Metrics (Hiệu năng hệ thống)

### 3.1. Latency (Độ trễ)

Các chỉ số latency được đo từ phía client:

| Metric              | Ý nghĩa                                                                   |
| ------------------- | ------------------------------------------------------------------------- |
| `search_latency_ms` | Thờ gian gọi API `/search` (bao gồm embedding + vector search + reranker) |
| `chat_latency_ms`   | Thờ gian gọi API `/chat` (LLM generation)                                 |
| `total_latency_ms`  | Tổng thờ gian từ lúc gửi query đến lúc nhận đủ câu trả lồ                 |

**Percentiles quan trọng**:

- **p50 (median)**: Thờ gian phản hồi cho đa số user
- **p95**: Thờ gian phản hồi cho 95% user (dùng để đặt SLA)
- **p99**: Thờ gian phản hồi cho 99% user (dùng để phát hiện outlier)

**Ngưỡng chấp nhận**:

- **< 5s**: Rất nhanh — UX tuyệt vời
- **5s – 15s**: Nhanh — chấp nhận được cho chatbot
- **15s – 30s**: Trung bình — user có thể thấy chậm
- **> 30s**: Chậm — cần tối ưu ngay

**Cách cải thiện**:

- Tối ưu embedding model (chọn model nhẹ hơn)
- Dùng caching cho frequent queries
- Giảm top-k hoặc dùng reranker nhẹ hơn
- Streaming response để user thấy phản hồi tức thì

---

### 3.2. Error Rate (Tỷ lệ lỗi)

**Ý nghĩa**: Tỷ lệ query bị lỗi (timeout, API exception, parsing error).

```
error_rate = (query_count_error) / (query_count_total)
```

**Ngưỡng**:

- **0%**: Lý tưởng
- **< 1%**: Rất tốt
- **1% – 5%**: Cần theo dõi
- **> 5%**: Nghiêm trọng — cần fix ngay

---

## 4. Composite Score (Điểm tổng hợp)

### 4.1. RAG Score

**Ý nghĩa**: Điểm tổng hợp duy nhất để so sánh các config với nhau.

**Công thức**:

```
RAG Score = 0.40 × Faithfulness + 0.35 × Answer Relevancy + 0.25 × Context Precision
```

**Trọng số**:

- **Faithfulness (40%)**: Quan trọng nhất — đảm bảo thông tin đúng
- **Answer Relevancy (35%)**: Quan trọng thứ hai — đảm bảo trả lồ đúng trọng tâm
- **Context Precision (25%)**: Quan trọng thứ ba — đảm bảo retrieval chất lượng

**Phạm vi**: 0.0 – 1.0

- **> 0.85**: Xuất sắc
- **0.75 – 0.85**: Tốt
- **0.60 – 0.75**: Trung bình — cần cải thiện
- **< 0.60**: Kém — cần tái thiết kế pipeline

---

## 5. Ablation Study (Nghiên cứu loại bỏ thành phần)

### 5.1. Các config đánh giá

| Config           | Mô tả                                                              | Mục đích                          |
| ---------------- | ------------------------------------------------------------------ | --------------------------------- |
| **Baseline**     | Full pipeline: Query Transform + Retrieval + Reranker + Generation | Đo chất lượng tối đa              |
| **No Reranker**  | Bỏ reranker, chỉ dùng vector search top-k                          | Đo giá trị của reranker           |
| **No Transform** | Bỏ query transformation/rewriting                                  | Đo giá trị của query optimization |

### 5.2. Cách đọc kết quả ablation

**Nếu No Reranker giảm mạnh CP**:
→ Reranker đang hoạt động tốt, giúp lọc nhiễu context. Nên giữ.

**Nếu No Transform giảm AR và F**:
→ Query transform giúp retrieval tốt hơn, dẫn đến câu trả lồ chất lượng hơn. Nên giữ.

**Nếu No Reranker nhanh hơn nhiều nhưng RAG Score vẫn cao**:
→ Có thể thử reranker nhẹ hơn để trade-off tốc độ/chất lượng.

---

## 6. Workflow đánh giá

```
1. Chạy collect.py → raw_results.json (latency, answer, contexts)
2. Chạy evaluate.py → per_query_metrics.csv + summary_metrics.csv (RAGAS)
3. Chạy report.py → report.md + charts/
4. Phân tích report → Quyết định cải thiện
```

## 7. Checklist cải thiện theo chỉ số

| Chỉ số thấp            | Nguyên nhân có thể                       | Hành động                                   |
| ---------------------- | ---------------------------------------- | ------------------------------------------- |
| Faithfulness           | Hallucination, prompt không ràng buộc đủ | Thêm "chỉ dùng context" vào system prompt   |
| Answer Relevancy       | Retrieval không sát câu hỏi              | Tối ưu query transform, embedding           |
| Context Precision      | Nhiều context nhiễu                      | Thêm reranker, điều chỉnh top-k             |
| Numerical Faithfulness | Chatbot bịa số                           | Thêm validation, prompt nhấn mạnh số liệu   |
| Data Sufficiency       | Chatbot đoán khi không đủ data           | Thêm confidence threshold, training refusal |
| Latency cao            | Reranker nặng, LLM chậm                  | Dùng model nhẹ hơn, cache, streaming        |
| Error Rate cao         | Timeout, API lỗi                         | Tăng timeout, thêm retry, graceful fallback |
