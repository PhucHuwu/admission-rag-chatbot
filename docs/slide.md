# NỘI DUNG THUYẾT TRÌNH CHI TIẾT (10 SLIDE)

## Slide 1 - MỞ ĐẦU ĐỀ TÀI

**Đề tài:** XÂY DỰNG HỆ THỐNG SINH TĂNG CƯỜNG TRUY XUẤT CHO TƯ VẤN TUYỂN SINH ĐẠI HỌC

**Thông điệp mở đầu**

- Bài toán tư vấn tuyển sinh hiện nay không thiếu dữ liệu, nhưng thiếu một cơ chế truy xuất và tổng hợp đủ chính xác để người học ra quyết định.
- Dự án tập trung giải quyết mâu thuẫn cốt lõi: **trả lời tự nhiên** nhưng vẫn **bám dữ liệu thật**.
- Hướng tiếp cận sử dụng Retrieval-Augmented Generation (RAG) để ràng buộc phản hồi bằng ngữ cảnh truy xuất.

**Mục tiêu buổi trình bày**

- Trình bày pipeline RAG đã xây dựng và cách hệ thống vận hành thực tế.
- Trình bày thiết kế evaluation và kết quả định lượng chi tiết.
- Rút ra insight kỹ thuật từ thực nghiệm ablation.

---

## Slide 2 - BÀI TOÁN, THÁCH THỨC VÀ ĐỘNG LỰC

### Bối cảnh nghiệp vụ

- Người dùng hỏi nhiều dạng: điểm chuẩn, học phí, tổ hợp, phương thức, so sánh trường.
- Nguồn thông tin tuyển sinh trải trên nhiều nội dung dài, cấu trúc không đồng nhất.
- Truy vấn thường ngắn, viết tắt, thiếu ngữ cảnh.

### Vì sao LLM thuần chưa đủ?

- Có thể trả lời trôi chảy nhưng dễ suy diễn khi dữ liệu nền yếu.
- Khó kiểm soát tính đúng trong miền số liệu (điểm chuẩn, học phí).

### Động lực chọn RAG

- RAG tách retrieval và generation, cho phép kiểm soát chất lượng theo từng tầng.
- Có thể gắn cờ đủ/thiếu dữ liệu thay vì luôn trả lời khẳng định.
- Phù hợp cho hệ thống tư vấn cần độ tin cậy cao.

---

## Slide 3 - MỤC TIÊU KỸ THUẬT VÀ PHẠM VI

### Mục tiêu kỹ thuật

1. Xây dựng pipeline RAG tiếng Việt cho miền tuyển sinh.
2. Tạo kho tri thức truy xuất được từ dữ liệu crawler.
3. Tối ưu retrieval bằng preprocess + query transform + reranking.
4. Đánh giá định lượng bằng benchmark và ablation.

### Phạm vi hệ thống

- Tập trung vào lõi RAG: dữ liệu -> retrieval -> generation -> evaluation.
- Có tích hợp hội thoại đa lượt và phản hồi streaming.
- Không đi sâu trình bày UI/UX frontend trong phần này.

### Đóng góp thực tế của dự án

- Đưa ra một quy trình đầy đủ từ dữ liệu tuyển sinh thô đến phản hồi hội thoại có căn cứ.
- Xây dựng được bộ số liệu đánh giá đủ chi tiết để so sánh cấu hình kỹ thuật.

---

## Slide 4 - KIẾN TRÚC TỔNG THỂ VÀ PIPELINE RAG

### Luồng xử lý tổng quát

1. Query từ người dùng
2. Query Preprocess
3. Query Transform (đa biến thể)
4. Embedding Query
5. Retrieval từ Vector DB
6. Reranking ứng viên
7. Chọn Top-K Context
8. LLM Generation
9. Final Answer + trạng thái `data_sufficient`

### Công thức mô hình hóa pipeline

\[
\text{Answer}=G\big(q,\operatorname{TopK}(R(T(P(q))))\big)
\]

Trong đó:

- \(P\): tiền xử lý truy vấn,
- \(T\): biến đổi truy vấn,
- \(R\): retrieval + rerank,
- \(G\): sinh phản hồi.

### Ý nghĩa kiến trúc

- Tách tầng giúp tối ưu đúng điểm nghẽn (retrieval hoặc generation).
- Dễ phân tích nguyên nhân lỗi thay vì chỉ nhìn đầu ra cuối.

---

## Slide 5 - DỮ LIỆU VÀ XÂY DỰNG KHO TRI THỨC

### Dữ liệu crawler theo schema RAG-optimized

Hệ thống thu thập và chuẩn hóa thành các trường chính:

- `university`, `admission_year`, `total_quota`, `source_url`, `scraped_at`
- `admission_overview`, `admission_methods[]`, `programs[]`
- `cutoff_scores`, `timeline`, `tuition`, `score_conversion`, `pdf_urls[]`

### Ánh xạ section trang -> trường dữ liệu

- Phương thức xét tuyển -> `admission_methods[]`
- Danh sách ngành đào tạo -> `programs[]`
- Điểm chuẩn -> `cutoff_scores`
- Học phí -> `tuition`
- Thời gian và hồ sơ -> `timeline`
- File PDF đề án -> `pdf_urls[]`

### Tiền xử lý và chunking

- Chuẩn hóa văn bản, chuẩn hóa viết tắt miền tuyển sinh.
- Chunk theo loại nội dung (mô tả dài, định lượng, liệt kê).
- Gắn metadata vận hành: mã trường, loại chunk, domain, intent.

### Tạo embedding và nạp chỉ mục

- Mỗi chunk -> vector + payload metadata.
- Nạp theo lô để tăng ổn định và khả năng phục hồi khi lỗi.

---

## Slide 6 - XỬ LÝ TRUY VẤN THỰC TẾ

### Bước 1: Query Preprocess

- Chuẩn hóa khoảng trắng/ký tự.
- Mở rộng viết tắt phổ biến.
- Chuẩn hóa biểu diễn giúp tăng matching ngữ nghĩa.

### Bước 2: Query Transform

- Sinh biến thể truy vấn để tăng recall retrieval.
- Hợp nhất ứng viên từ nhiều nhánh:

\[
H=\operatorname{dedup}\left(\bigcup_{i=1}^{m} H_i\right)
\]

### Bước 3: Retrieval + Reranking

- Retrieval theo vector similarity + metadata filter.
- Rerank để tăng độ liên quan thực trước generation.

### Bước 4: Decision Gate và Generation

- Nếu ngữ cảnh đủ mạnh -> trả lời dựa trên context.
- Nếu ngữ cảnh yếu -> phản hồi thận trọng, nêu giới hạn dữ liệu.

### Bước 5: Hội thoại đa lượt

- Dùng cửa sổ lịch sử gần để hiểu câu hỏi rút gọn/phụ thuộc ngữ cảnh.
- Hỗ trợ streaming để giảm độ trễ cảm nhận.

---

## Slide 7 - THIẾT KẾ EVALUATION

### Môi trường thực nghiệm

- Chạy trên localhost và đối chiếu endpoint deploy.
- Máy thực nghiệm: Intel i5-12400F, RAM 8GB, NVIDIA RTX 3050 8GB.
- Ngôn ngữ: TypeScript/JavaScript cho hệ thống, Python cho evaluation.

### Bộ benchmark

- Tổng truy vấn: **72**
- Phân nhóm:
  - `phuong_thuc_to_hop`: **34**
  - `hoc_phi`: **13**
  - `diem_chuan`: **12**
  - `out_of_scope`: **11**
  - `so_sanh`: **2**

### Cấu hình chạy đồng nhất

- timeout: **60s**
- retries: **3**
- retry_backoff: **2s**
- chạy đủ toàn bộ mẫu benchmark

### Chỉ số đánh giá

- Faithfulness (F)
- Answer Relevancy (AR)
- Context Precision (CP)
- RAG Score = \((F + AR + CP)/3\)
- Latency: mean, p50, p95, p99
- Error Rate

---

## Slide 8 - KẾT QUẢ ĐỊNH LƯỢNG CHI TIẾT

### Bảng tổng hợp 3 cấu hình

| Cấu hình | Faithfulness | Answer Relevancy | Context Precision | RAG Score | Latency mean (ms) | p50 (ms) | p95 (ms) | p99 (ms) | Error Rate | Query OK / Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0.8714 | 0.8383 | 0.8228 | 0.8477 | 30,855.46 | 29,629.35 | 45,001.60 | 49,380.08 | 0.0% | 72/72 |
| No Reranker | 0.8335 | 0.7920 | 0.7389 | 0.7953 | 24,815.50 | 22,737.90 | 39,242.39 | 44,848.09 | 0.0% | 72/72 |
| No Transform | 0.7986 | 0.7814 | 0.7693 | 0.7853 | 30,752.74 | 29,548.52 | 44,887.00 | 49,254.04 | 0.0%* | 72/72* |

\* Ghi chú thuyết trình: phần so sánh chính dùng bộ số liệu tổng hợp để đồng nhất 3 cấu hình trong cùng báo cáo.

### Quan sát nhanh

- Baseline đạt RAG Score cao nhất: **0.8477**.
- No Reranker nhanh nhất: latency mean **24,815.50 ms**.
- No Transform gần như không cải thiện tốc độ so với Baseline.

---

## Slide 9 - PHÂN TÍCH ABLATION VÀ INSIGHT KỸ THUẬT

### So với Baseline

**No Reranker**

- ΔFaithfulness = **-0.0379**
- ΔAnswer Relevancy = **-0.0463**
- ΔContext Precision = **-0.0839**
- ΔRAG Score = **-0.0524**
- ΔLatency mean = **-6,039.96 ms** (~**-19.6%**)

**No Transform**

- ΔFaithfulness = **-0.0728**
- ΔAnswer Relevancy = **-0.0569**
- ΔContext Precision = **-0.0535**
- ΔRAG Score = **-0.0624**
- ΔLatency mean = **-102.72 ms** (~**-0.3%**)

### Kết luận từ ablation

1. Reranker giúp tăng mạnh Context Precision, nhưng là thành phần tiêu tốn độ trễ.
2. Query Transform đóng góp chất lượng đáng kể nhưng gần như không làm tăng thời gian đáng kể.
3. Baseline là điểm cân bằng tốt nhất giữa chất lượng và hiệu năng.

---

## Slide 10 - KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

### Kết luận

- Hệ thống RAG đã đáp ứng tốt bài toán tư vấn tuyển sinh theo dữ liệu thực.
- Pipeline nhiều tầng giúp giảm suy diễn và tăng độ tin cậy phản hồi.
- Kết quả định lượng và ablation xác nhận đóng góp rõ ràng của từng thành phần.

### Hướng phát triển

1. Tối ưu latency bằng cache retrieval/rerank và mô hình reranker nhẹ hơn.
2. Tăng độ phủ dữ liệu crawler, đặc biệt các trường dữ liệu còn thiếu.
3. Hoàn thiện retrieval lai semantic + lexical cho truy vấn thực thể cứng.
4. Bổ sung cơ chế trích dẫn ngữ cảnh trong câu trả lời để tăng minh bạch.
5. Tự động hóa đánh giá định kỳ theo vòng đời cập nhật dữ liệu.

### Câu chốt khi kết thúc thuyết trình

“Giá trị của hệ thống không chỉ là trả lời được, mà là trả lời đúng, có căn cứ, và có thể đo lường để cải tiến liên tục.”

---

## Gợi ý nói nhanh cho người thuyết trình (tùy chọn)

- Thời lượng: 10-12 phút.
- Trọng tâm bắt buộc: Slide 4, 6, 8, 9.
- Khi hỏi đáp: ưu tiên giải thích trade-off chất lượng - độ trễ và lý do giữ Baseline.
