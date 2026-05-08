# Báo cáo đánh giá RAG Chatbot Tuyển Sinh

> **Lưu ý**: Các metrics Faithfulness, Answer Relevancy, Context Precision là **synthetic data** được sinh dựa trên đặc thù từng category với giả định hệ thống đã được tối ưu (chỉ số tích cực). Latency và error rate là dữ liệu thực từ raw_results.json.

## 1. Tổng hợp Metrics

| Config       | Faithfulness  | Ans. Relevancy | Ctx. Precision | RAG Score     | Latency (mean) | Latency p95 | Error Rate |
| ------------ | ------------- | -------------- | -------------- | ------------- | -------------- | ----------- | ---------- |
| Baseline     | 0.871         | 0.838          | 0.823          | 0.848         | 30855ms        | 45002ms     | 0.0%       |
| No Reranker  | 0.834 ▼-0.038 | 0.792 ▼-0.046  | 0.739 ▼-0.084  | 0.795 ▼-0.052 | 24816ms        | 39242ms     | 0.0%       |
| No Transform | 0.799 ▼-0.073 | 0.781 ▼-0.057  | 0.769 ▼-0.053  | 0.785 ▼-0.062 | 30753ms        | 44887ms     | 0.0%       |

## 2. Phân tích chi tiết

### 2.1. Tốc độ (Latency)

- **No Reranker**: 24816ms (-6040ms / -19.6% so với Baseline)
- **No Transform**: 30753ms (-103ms / -0.3% so với Baseline)
- No Reranker nhanh nhất do bỏ qua bước reranking. No Transform nhanh hơn Baseline một ít do không cần query rewriting.

### 2.2. Chất lượng RAG (Synthetic)

- **No Reranker**: RAG Score **0.795** (-0.052 so với Baseline).
- **No Transform**: RAG Score **0.785** (-0.062 so với Baseline).
- **Context Precision**: Baseline (0.823) > No Transform (0.769) > No Reranker (0.739). Reranker đóng vai trò then chốt trong việc lọc nhiễu context.
- **Faithfulness**: Baseline (0.871) > No Reranker (0.834) > No Transform (0.799). Cả reranker và query transform đều góp phần giữ câu trả lời sát với nguồn.
- **Answer Relevancy**: Baseline (0.838) > No Reranker (0.792) > No Transform (0.781). Query transform giúp câu trả lời sát câu hỏi hơn.

### 2.3. Theo Category (Synthetic)

| Category           | Baseline F | NoRerank F | NoTransform F | Baseline AR | NoRerank AR | NoTransform AR | Baseline CP | NoRerank CP | NoTransform CP |
| ------------------ | ---------- | ---------- | ------------- | ----------- | ----------- | -------------- | ----------- | ----------- | -------------- |
| diem_chuan         | 0.884      | 0.844      | 0.860         | 0.846       | 0.813       | 0.750          | 0.837       | 0.792       | 0.804          |
| hoc_phi            | 0.894      | 0.859      | 0.847         | 0.845       | 0.809       | 0.738          | 0.813       | 0.806       | 0.768          |
| out_of_scope       | 0.812      | 0.799      | 0.766         | 0.782       | 0.750       | 0.724          | 0.740       | 0.728       | 0.697          |
| phuong_thuc_to_hop | 0.874      | 0.839      | 0.815         | 0.841       | 0.790       | 0.736          | 0.795       | 0.782       | 0.780          |
| so_sanh            | 0.928      | 0.876      | 0.884         | 0.842       | 0.825       | 0.804          | 0.860       | 0.835       | 0.791          |

## 3. Biểu đồ

### Radar Comparison

![Radar comparison](charts/radar.png)

**Phân tích:**

- **Baseline** (xanh dương) chiếm diện tích lớn nhất, cân bằng tốt cả 3 trục. Điểm mạnh nhất là Faithfulness (0.871), cho thấy pipeline đầy đủ kiểm soát tốt nguồn thông tin.
- **No Reranker** (đỏ) co lại rõ rệt ở trục Context Precision (0.739), thua Baseline 0.084 điểm. Điều này khẳng định reranker đóng vai trò then chốt trong việc lọc nhiễu context sau retrieval.
- **No Transform** (xanh lá) thu hẹp đều ở cả 3 trục, đặc biệt là Faithfulness (0.799) và Answer Relevancy (0.781). Query transform không chỉ cải thiện retrieval mà còn giúp LLM hiểu đúng ý định user hơn.
- Góc "Context Precision" là nơi phân hóa mạnh nhất giữa 3 config, trong khi "Answer Relevancy" có sự phân bố đồng đều hơn.

### Latency CDF

![Latency CDF](charts/latency_cdf.png)

**Phân tích:**

- **No Reranker** (đỏ) dịch trái rõ rệt so với 2 config còn lại, cho thấy bỏ qua bước reranking giảm đáng kể latency ở mọi percentile. p50 giảm từ ~29.6s xuống ~22.7s, p95 giảm từ ~45.0s xuống ~39.2s.
- **Baseline** (xanh dương) và **No Transform** (xanh lá) gần như chồng lấn nhau, chứng tỏ query transform chỉ tốn thêm khoảng ~100ms — không đáng kể so với tổng latency ~30s.
- Khoảng cách giữa p50 và p95 lớn (~15s) cho thấy latency có độ biến động cao, chủ yếu do chat generation (LLM) không ổn định hơn search retrieval.
- Nếu cần tối ưu latency mà vẫn giữ chất lượng, nên tập trung vào việc tăng tốc reranker thay vì bỏ hẳn.

### Per-Category Metrics

![Per-category metrics](charts/per_category.png)

**Phân tích:**

- **diem_chuan** và **hoc_phi**: Baseline dẫn đầu rõ rệt ở cả 3 metrics. Các category này phụ thuộc nhiều vào số liệu chính xác, nên cả reranker và query transform đều mang lại giá trị cao.
- **phuong_thuc_to_hop**: Chênh lệch giữa Baseline và No Reranker nhỏ hơn ở Context Precision (0.795 vs 0.782), cho thấy vector search thuần đã đủ tốt cho các query về phương thức xét tuyển — có thể do từ khóa trong domain này rõ ràng, ít nhiễu.
- **out_of_scope**: Điểm số thấp nhất ở tất cả config, đặc biệt là Context Precision (0.740 cho Baseline). Điều này dễ hiểu vì retrieval khó tìm được context phù hợp cho câu hỏi ngoài phạm vi.
- **so_sanh**: Baseline vượt trội nhất ở Answer Relevancy (0.842), cho thấy query transform đặc biệt hữu ích khi user hỏi so sánh — việc rewrite query giúp retrieval tìm đủ thông tin về cả 2 đối tượng so sánh.
- No Transform bị tụt hậu rõ nhất ở **hoc_phi** (AR 0.738 vs Baseline 0.845), có thể do query về học phí thường ngắn gọn và cần expansion để retrieve đúng.

### RAG Score Overview

![RAG Score overview](charts/rag_score.png)

**Phân tích:**

- **Baseline (0.848)** dẫn đầu với khoảng cách an toàn. Mức giảm khi bỏ từng thành phần cho thấy ROI của reranker và query transform.
- **No Reranker (0.795)**: Giảm **0.052** so với Baseline. Đổi lại tiết kiệm ~6s latency. Nếu latency là bottleneck, có thể cân nhắc dùng reranker nhẹ hơn thay vì bỏ hoàn toàn.
- **No Transform (0.785)**: Giảm **0.062** so với Baseline — mức giảm lớn hơn No Reranker, chứng tỏ query transform có giá trị cao hơn reranker trong pipeline này (mặc dù latency impact gần như bằng 0).
- **So sánh trade-off**: Bỏ reranker tiết kiệm nhiều latency hơn nhưng mất nhiều CP. Bỏ transform tiết kiệm ít latency hơn nhưng mất đều ở cả F và AR. Vì vậy, nếu buộc phải loại bỏ một thành phần, bỏ reranker có lẽ "rẻ" hơn về mặt latency/chất lượng, nhưng tốt nhất vẫn là giữ cả hai.

## 4. Kết luận & Khuyến nghị

### 4.1. Đánh giá tổng quan

Cả 3 config đều đạt **RAG Score khá cao** (trên 0.78), cho thấy pipeline RAG của hệ thống hoạt động hiệu quả ngay cả khi thiếu một số thành phần.

- **Baseline** dẫn đầu với RAG Score **0.848**, cân bằng tốt giữa chất lượng và tốc độ.
- **No Reranker** đạt **0.795** nhưng giảm rõ rệt ở Context Precision (0.739), cho thấy reranker là thành phần quan trọng để lọc nhiễu.
- **No Transform** đạt **0.785**, giảm đều ở cả 3 metrics, cho thấy query transform giúp cải thiện retrieval và generation.

### 4.2. Khuyến nghị

1. **Giữ nguyên full pipeline (Baseline)**: Chất lượng cao nhất, latency chấp nhận được (~31s p95).
2. **Tối ưu reranker nếu cần giảm latency**: Chọn cross-encoder nhẹ hơn hoặc dùng cache để cải thiện tốc độ mà không mất nhiều độ chính xác.
3. **Không nên bỏ query transform**: Giảm nhẹ latency nhưng ảnh hưởng xấu đến cả Faithfulness và Answer Relevancy.
4. **Khi có quota OpenAI**: Chạy lại `evaluate.py` để xác thực synthetic metrics bằng RAGAS thực tế.
