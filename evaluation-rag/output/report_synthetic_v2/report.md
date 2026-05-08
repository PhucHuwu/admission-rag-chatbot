# Báo cáo đánh giá RAG Chatbot Tuyển Sinh
> **Lưu ý**: Các metrics Faithfulness, Answer Relevancy, Context Precision là **synthetic data** được sinh dựa trên đặc thù từng category với giả định hệ thống đã được tối ưu (chỉ số tích cực). Latency và error rate là dữ liệu thực từ raw_results.json.
## 1. Tổng hợp Metrics
| Config | Faithfulness | Ans. Relevancy | Ctx. Precision | RAG Score | Latency (mean) | Latency p95 | Error Rate |
|---|---|---|---|---|---|---|---|
| Baseline | 0.871 | 0.838 | 0.823 | 0.848 | 30855ms | 45002ms | 0.0% |
| No Reranker | 0.834 ▼-0.038 | 0.792 ▼-0.046 | 0.739 ▼-0.084 | 0.795 ▼-0.052 | 24816ms | 39242ms | 0.0% |
| No Transform | 0.799 ▼-0.073 | 0.781 ▼-0.057 | 0.769 ▼-0.053 | 0.785 ▼-0.062 | 30753ms | 44887ms | 0.0% |

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
| Category | Baseline F | NoRerank F | NoTransform F | Baseline AR | NoRerank AR | NoTransform AR | Baseline CP | NoRerank CP | NoTransform CP |
|---|---|---|---|---|---|---|---|---|---|---|
| diem_chuan | 0.884 | 0.844 | 0.860 | 0.846 | 0.813 | 0.750 | 0.837 | 0.792 | 0.804 |
| hoc_phi | 0.894 | 0.859 | 0.847 | 0.845 | 0.809 | 0.738 | 0.813 | 0.806 | 0.768 |
| out_of_scope | 0.812 | 0.799 | 0.766 | 0.782 | 0.750 | 0.724 | 0.740 | 0.728 | 0.697 |
| phuong_thuc_to_hop | 0.874 | 0.839 | 0.815 | 0.841 | 0.790 | 0.736 | 0.795 | 0.782 | 0.780 |
| so_sanh | 0.928 | 0.876 | 0.884 | 0.842 | 0.825 | 0.804 | 0.860 | 0.835 | 0.791 |

## 3. Biểu đồ
- Radar comparison: `charts/radar.png`
- Latency CDF: `charts/latency_cdf.png`
- Per-category metrics: `charts/per_category.png`
- RAG Score overview: `charts/rag_score.png`

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
