# SCRIPT THUYẾT TRÌNH

## Slide 1 - Mở đầu đề tài

Xin chào thầy/cô và các bạn, nhóm em xin trình bày đề tài **"Xây dựng hệ thống sinh tăng cường truy xuất cho tư vấn tuyển sinh đại học"**.

Bài toán hiện nay không thiếu dữ liệu tuyển sinh, nhưng thiếu cơ chế truy xuất và tổng hợp đủ chính xác để người học ra quyết định. Dự án của nhóm tập trung giải quyết mâu thuẫn cốt lõi: **trả lời tự nhiên** nhưng vẫn **bám dữ liệu thật**. Vì vậy, nhóm chọn hướng tiếp cận RAG để ràng buộc phản hồi bằng ngữ cảnh truy xuất.

Trong phần trình bày này, nhóm sẽ đi qua 3 nội dung chính: pipeline RAG vận hành ra sao, kết quả evaluation định lượng, và insight kỹ thuật từ ablation.

---

## Slide 2 - Bài toán, thách thức và động lực

Trong nghiệp vụ tuyển sinh, người dùng hỏi rất nhiều dạng câu hỏi: điểm chuẩn, học phí, tổ hợp, phương thức xét tuyển, hoặc so sánh giữa các trường. Trong khi đó, dữ liệu nằm ở nhiều nguồn dài và cấu trúc không đồng nhất; truy vấn người dùng lại thường ngắn, viết tắt, thiếu ngữ cảnh.

Nếu dùng LLM thuần, mô hình có thể trả lời trôi chảy nhưng dễ suy diễn, nhất là ở miền số liệu như điểm chuẩn và học phí. Đó là động lực nhóm chọn RAG: tách retrieval và generation để kiểm soát chất lượng theo từng tầng, đồng thời có thể phản hồi thận trọng khi dữ liệu chưa đủ.

---

## Slide 3 - Mục tiêu kỹ thuật và phạm vi

Nhóm đặt ra 4 mục tiêu kỹ thuật:
1) Xây dựng pipeline RAG tiếng Việt cho miền tuyển sinh.
2) Tạo kho tri thức truy xuất được từ dữ liệu crawler.
3) Tối ưu retrieval bằng preprocess, query transform và reranking.
4) Đánh giá định lượng bằng benchmark và ablation.

Phạm vi hệ thống tập trung vào lõi RAG: dữ liệu -> retrieval -> generation -> evaluation; có hỗ trợ hội thoại đa lượt và streaming, nhưng không đi sâu UI/UX trong phần này.

---

## Slide 4 - Kiến trúc tổng thể và pipeline RAG

Luồng xử lý tổng quát gồm 9 bước: nhận query, preprocess, query transform, embedding, retrieval từ vector DB, reranking, chọn top-K context, LLM generation, và trả lời cuối cùng kèm trạng thái `data_sufficient`.

### Diễn giải công thức mô hình hóa pipeline bằng lời

Công thức:

\[
\text{Answer}=G\big(q,\operatorname{TopK}(R(T(P(q))))\big)
\]

Diễn giải bằng lời:

- Đầu tiên, truy vấn gốc `q` được **tiền xử lý** qua hàm `P` để chuẩn hóa câu hỏi.
- Tiếp theo, câu hỏi đã chuẩn hóa được **biến đổi** qua hàm `T` để tạo các biến thể truy vấn tăng khả năng tìm đúng dữ liệu.
- Sau đó, các truy vấn này đi qua tầng **retrieval + rerank** `R` để lấy các đoạn thông tin liên quan nhất.
- Từ tập ứng viên đó, hệ thống chọn **Top-K ngữ cảnh** tốt nhất.
- Cuối cùng, mô hình sinh `G` tạo câu trả lời dựa trên **query ban đầu `q`** và **Top-K ngữ cảnh đã truy xuất**.

Nói ngắn gọn: hệ thống không trả lời trực tiếp từ trí nhớ mô hình, mà trả lời dựa trên ngữ cảnh đã được truy xuất, lọc và xếp hạng.

---

## Slide 5 - Dữ liệu và xây dựng kho tri thức

Hệ thống crawler và chuẩn hóa dữ liệu theo schema tối ưu cho RAG với các trường chính như `university`, `admission_year`, `total_quota`, `source_url`, `admission_methods`, `programs`, `cutoff_scores`, `timeline`, `tuition`, `pdf_urls`.

Mỗi section trên trang được ánh xạ vào đúng trường dữ liệu tương ứng. Sau đó nhóm thực hiện tiền xử lý văn bản, chunking theo loại nội dung và gắn metadata vận hành. Cuối cùng, mỗi chunk được embedding thành vector và nạp chỉ mục theo lô để tăng ổn định.

---

## Slide 6 - Xử lý truy vấn thực tế

Với truy vấn thực tế, hệ thống đi qua các bước:

1) **Query Preprocess**: chuẩn hóa khoảng trắng, ký tự, mở rộng viết tắt.
2) **Query Transform**: sinh nhiều biến thể để tăng recall.
3) **Retrieval + Reranking**: truy xuất theo vector similarity và lọc metadata, sau đó rerank trước generation.
4) **Decision Gate**: ngữ cảnh đủ mạnh thì trả lời theo context; ngữ cảnh yếu thì phản hồi thận trọng, nêu giới hạn dữ liệu.
5) **Đa lượt + Streaming**: dùng lịch sử gần để hiểu ngữ cảnh hội thoại và giảm độ trễ cảm nhận.

---

## Slide 7 - Thiết kế evaluation

Thực nghiệm chạy trên localhost và đối chiếu endpoint deploy. Bộ benchmark gồm **72 truy vấn**, chia thành các nhóm: `phuong_thuc_to_hop` (34), `hoc_phi` (13), `diem_chuan` (12), `out_of_scope` (11), `so_sanh` (2).

Cấu hình chạy đồng nhất: timeout 60s, retries 3, backoff 2s. Chỉ số đánh giá gồm Faithfulness, Answer Relevancy, Context Precision; với **RAG Score = (F + AR + CP)/3**, cùng các chỉ số latency và error rate.

---

## Slide 8 - Kết quả định lượng chi tiết

Kết quả cho thấy:

- **Baseline** có RAG Score cao nhất: **0.8477**.
- **No Reranker** nhanh nhất về độ trễ trung bình: **24,815.50 ms**.
- **No Transform** gần như không cải thiện tốc độ so với Baseline nhưng chất lượng giảm.

Điểm chính ở slide này là trade-off giữa chất lượng và độ trễ.

---

## Slide 9 - Phân tích ablation và insight kỹ thuật

So với Baseline:

- **No Reranker** giảm chất lượng rõ, đặc biệt Context Precision, nhưng giảm latency khoảng **19.6%**.
- **No Transform** giảm chất lượng đáng kể, trong khi chỉ giảm latency khoảng **0.3%**.

Kết luận kỹ thuật:
1) Reranker giúp tăng mạnh độ chính xác ngữ cảnh nhưng tốn độ trễ.
2) Query Transform cải thiện chất lượng đáng kể với chi phí thời gian rất thấp.
3) Baseline là điểm cân bằng tốt nhất giữa hiệu năng và chất lượng.

---

## Slide 10 - Kết luận và hướng phát triển

Hệ thống RAG đã đáp ứng tốt bài toán tư vấn tuyển sinh theo dữ liệu thực. Kiến trúc nhiều tầng giúp giảm suy diễn và tăng độ tin cậy. Kết quả định lượng và ablation xác nhận đóng góp rõ ràng của từng thành phần.

Hướng phát triển tiếp theo:
1) Tối ưu latency bằng cache retrieval/rerank và reranker nhẹ hơn.
2) Tăng độ phủ dữ liệu crawler.
3) Hoàn thiện retrieval lai semantic + lexical.
4) Bổ sung trích dẫn ngữ cảnh trong câu trả lời.
5) Tự động hóa đánh giá định kỳ theo vòng đời dữ liệu.

Câu chốt: **"Giá trị của hệ thống không chỉ là trả lời được, mà là trả lời đúng, có căn cứ, và có thể đo lường để cải tiến liên tục."**
