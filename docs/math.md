# GIẢI THÍCH CHUYÊN SÂU CÁC CÔNG THỨC TRONG `docs/report.md`

Tài liệu này diễn giải các công thức theo 3 lớp:

1. **Công thức (preview được trên Markdown)**
2. **Ý tưởng cốt lõi của công thức**
3. **Diễn giải bằng lời trong ngữ cảnh hệ RAG tư vấn tuyển sinh**

---

## 1) Xác suất sinh của LLM (tự hồi quy)

$$
P(y\mid x)=\prod_{t=1}^{T} P\left(y_t\mid y_{<t},x\right)
$$

### Ý tưởng

- Xác suất tạo **toàn bộ câu trả lời** bằng tích xác suất tạo **từng token** theo thứ tự thời gian.
- Ở bước $t$, mô hình dùng mọi token đã sinh trước đó $y_{<t}$ và ngữ cảnh đầu vào $x$ để dự đoán token kế tiếp $y_t$.

### Diễn giải bằng lời

LLM không “nghĩ ra cả câu một lần”, mà sinh từng mảnh liên tiếp. Vì là tích của nhiều xác suất điều kiện, chỉ cần vài bước có lựa chọn lệch thì toàn bộ câu trả lời có thể trôi xa dữ kiện. Do đó, trong bài toán tuyển sinh, nếu ngữ cảnh đầu vào $x$ không đáng tin, mô hình vẫn có thể sinh câu trôi chảy nhưng sai số liệu.

---

## 2) Bài toán giải mã tối ưu theo ngữ cảnh truy xuất

$$
\hat{y}=\arg\max_y P(y\mid q,\mathcal{C})
$$

### Ý tưởng

- Tìm câu trả lời $\hat{y}$ có xác suất cao nhất khi biết truy vấn $q$ và tập ngữ cảnh $\mathcal{C}$.
- Đây là phát biểu toán học của việc “trả lời dựa trên context”, không trả lời thuần từ trí nhớ tham số.

### Diễn giải bằng lời

Trong RAG, chất lượng không chỉ nằm ở LLM mà nằm ở việc cung cấp đúng $\mathcal{C}$. Cùng một câu hỏi $q$, nếu thay ngữ cảnh, nghiệm tối ưu $\hat{y}$ đổi theo. Vì vậy retrieval quyết định trần chất lượng của generation.

---

## 3) Độ tương đồng cosine giữa truy vấn và tài liệu

$$
\operatorname{sim}(\mathbf{q},\mathbf{d})=
\frac{\mathbf{q}\cdot\mathbf{d}}{\lVert\mathbf{q}\rVert\,\lVert\mathbf{d}\rVert}
$$

### Ý tưởng

- Đo “độ cùng hướng” giữa hai vector embedding, gần như độc lập với độ lớn vector.
- Giá trị gần 1: rất gần nghĩa; gần 0: ít liên quan; âm: xu hướng đối nghịch.

### Diễn giải bằng lời

Cosine similarity cho phép bắt được trường hợp “khác chữ nhưng cùng ý”. Đây là lý do semantic retrieval hiệu quả với truy vấn người dùng viết tắt/diễn đạt tự do. Tuy nhiên, với thực thể cứng (mã ngành, số liệu hiếm), cosine đơn thuần có thể chưa đủ, nên cần thêm lexical hoặc rerank.

---

## 4) Tập tài liệu sau khi lọc metadata

$$
\mathcal{D}'=\{d\in\mathcal{D}\mid \phi(d)=1\}
$$

### Ý tưởng

- Không truy xuất trên toàn kho, mà truy xuất trên tập con thỏa điều kiện lọc $\phi$.
- $\phi(d)=1$ nghĩa là tài liệu $d$ hợp lệ theo ràng buộc miền (ví dụ đúng trường, đúng năm).

### Diễn giải bằng lời

Đây là cơ chế giảm nhiễu “đúng chủ đề nhưng sai đối tượng”. Trong tuyển sinh, lọc metadata giúp tránh việc kéo ngữ cảnh của trường khác hoặc niên khóa khác vào câu trả lời.

---

## 5) Công thức BM25 (lexical retrieval)

$$
\operatorname{BM25}(D,Q)=\sum_{t\in Q}
\operatorname{IDF}(t)
\cdot
\frac{f(t,D)(k_1+1)}{f(t,D)+k_1\left(1-b+b\frac{|D|}{\operatorname{avgdl}}\right)}
$$

### Ý tưởng

- Tính điểm tài liệu $D$ theo từng từ truy vấn $t$.
- Điểm tăng khi từ khóa xuất hiện nhiều trong tài liệu (qua $f(t,D)$), nhưng tăng **bão hòa** (không tăng mãi tuyến tính).
- Có chuẩn hóa độ dài tài liệu qua thành phần $|D|/\operatorname{avgdl}$ để không thiên vị tài liệu quá dài.
- IDF phạt từ quá phổ biến, thưởng từ đặc trưng.

### Diễn giải bằng lời

BM25 mạnh khi câu hỏi chứa thực thể rõ ràng: mã ngành, tổ hợp, cụm thuật ngữ cố định. Nó giúp “neo” retrieval vào từ khóa thật, bù cho semantic search ở các trường hợp embedding dễ làm mờ tín hiệu ký hiệu/số.

---

## 6) Hợp nhất điểm semantic và BM25

$$
S(d)=\lambda\,\tilde{S}_{sem}(d)+(1-\lambda)\,\tilde{S}_{bm25}(d),\quad \lambda\in[0,1]
$$

### Ý tưởng

- Trộn tuyến tính hai nguồn điểm đã chuẩn hóa: ngữ nghĩa và từ khóa.
- $\lambda$ là “núm chỉnh” trade-off:
  - $\lambda$ cao: ưu tiên hiểu ý.
  - $\lambda$ thấp: ưu tiên khớp thực thể.

### Diễn giải bằng lời

Hybrid score là cách thực dụng để tăng độ bền retrieval trước truy vấn thực tế vốn trộn cả ngôn ngữ tự nhiên và thực thể cứng. Đây là công thức quan trọng khi hệ thống phục vụ người dùng đại trà, nơi cách hỏi rất đa dạng.

---

## 7) Hợp ứng viên từ đa biến thể truy vấn

$$
\mathcal{D}_{union}=\bigcup_{i=1}^{m} \operatorname{TopK}(q_i)
$$

### Ý tưởng

- Sinh $m$ biến thể truy vấn $q_i$ để tăng recall.
- Mỗi biến thể lấy Top-K, sau đó hợp nhất thành một tập ứng viên lớn hơn.

### Diễn giải bằng lời

Một truy vấn ngắn có thể bỏ sót ý. Multi-query tạo nhiều “góc chiếu” vào kho tri thức để giảm bỏ sót. Đổi lại, tập hợp ứng viên sẽ nhiễu hơn, nên cần reranking mạnh ở bước sau.

---

## 8) Điểm tổng hợp RAG Score

$$
\operatorname{RAG\ Score}=
\frac{\operatorname{Faithfulness}+\operatorname{Answer\ Relevancy}+\operatorname{Context\ Precision}}{3}
$$

Hoặc dạng ký hiệu ngắn:

$$
\operatorname{RAG\ Score}=\frac{F+AR+CP}{3}
$$

### Ý tưởng

- Lấy trung bình cộng 3 chiều chất lượng:
  - $F$: bám chứng cứ (không bịa),
  - $AR$: trả lời đúng trọng tâm,
  - $CP$: ngữ cảnh truy xuất tinh gọn, đúng phần cần thiết.

### Diễn giải bằng lời

Đây là chỉ số “đầu-cuối” đơn giản nhưng cân bằng: một hệ không thể đạt điểm cao nếu chỉ giỏi một mặt. Ví dụ trả lời đúng ý nhưng context nhiễu hoặc thiếu căn cứ vẫn bị kéo điểm xuống.

---

## 9) Tỷ lệ lỗi hệ thống

$$
\operatorname{Error\ Rate}=\frac{N_{error}}{N_{total}}
$$

### Ý tưởng

- Đo độ ổn định vận hành: bao nhiêu truy vấn thất bại trên tổng truy vấn.

### Diễn giải bằng lời

Chỉ số chất lượng nội dung cao nhưng Error Rate cao thì hệ thống vẫn khó dùng trong thực tế. Vì vậy báo cáo cần theo dõi song song “đúng bao nhiêu” và “sống ổn định đến mức nào”.

---

## 10) Hybrid score trong thiết kế hệ thống (ký hiệu alpha)

$$
S_{hybrid}(d)=\alpha\,S_{semantic}(d)+(1-\alpha)\,S_{lexical}(d),\quad 0\le\alpha\le1
$$

### Ý tưởng

- Tương đương công thức trộn ở trên nhưng dùng ký hiệu triển khai ở Chương 3.
- $\alpha$ điều khiển cân bằng giữa hiểu nghĩa và khớp từ khóa.

### Diễn giải bằng lời

Hai công thức (dùng $\lambda$ hay $\alpha$) cùng bản chất. Khi triển khai, cần chuẩn hóa thang điểm trước khi cộng, nếu không nhánh có biên độ điểm lớn hơn sẽ lấn át nhánh còn lại.

---

## 11) Điểm rerank kết hợp keyword và mô hình đánh giá cặp query-document

$$
S_{rerank}(d)=w_k\,S_{keyword}(d)+w_l\,S_{llm}(d),\quad w_k+w_l=1
$$

### Ý tưởng

- Reranker tái chấm điểm ứng viên bằng hai tín hiệu:
  - tín hiệu keyword (neo thực thể),
  - tín hiệu ngữ nghĩa sâu từ mô hình (độ phù hợp thật theo ngữ cảnh câu hỏi).
- Điều kiện $w_k+w_l=1$ giữ tổng trọng số ổn định, dễ diễn giải.

### Diễn giải bằng lời

Đây là lớp “lọc tinh” sau retrieval thô. Nó thường cải thiện Context Precision rõ rệt, nhưng trả giá bằng latency. Vì vậy ablation thường cho thấy bỏ rerank thì nhanh hơn nhưng kém chính xác hơn.

---

## 12) Số chunk xấp xỉ khi dùng overlap

$$
N_{chunk}\approx\left\lceil\frac{L-o}{s-o}\right\rceil
$$

Trong đó:

- $L$: độ dài tài liệu,
- $s$: kích thước chunk,
- $o$: độ chồng lấp (overlap),
- $\lceil\cdot\rceil$: làm tròn lên.

### Ý tưởng

- Mỗi chunk mới “tiến” thêm một bước $s-o$ (vì có phần chồng lấp).
- Overlap lớn giảm đứt mạch ngữ cảnh nhưng làm tăng số chunk và chi phí indexing/retrieval.

### Diễn giải bằng lời

Đây là công thức vận hành rất thực tế: nó giúp ước lượng trước chi phí dữ liệu và độ trễ khi đổi tham số chunking. Nói cách khác, đây là điểm nối trực tiếp giữa quyết định tiền xử lý và chi phí hệ thống.

---

## 13) Ánh xạ từ chunk sang vector embedding

$$
\mathcal{V}=\{\mathbf{v}_1,\dots,\mathbf{v}_n\},\quad \mathbf{v}_i=E(c_i)
$$

### Ý tưởng

- Mỗi chunk $c_i$ được ánh xạ qua hàm embedding $E$ để thành vector $\mathbf{v}_i$.
- Tập vector $\mathcal{V}$ là nền chỉ mục cho semantic retrieval.

### Diễn giải bằng lời

Chất lượng của bước này quyết định “hình học tri thức” trong kho vector. Nếu chunking hoặc chuẩn hóa không tốt, vector không phản ánh đúng ý nghĩa, kéo theo retrieval sai ngay từ gốc.

---

## 14) Top-K có lọc metadata

$$
\operatorname{TopK}_{filtered}(q)=\operatorname{TopK}\left(\{d\mid \phi(d)=1\}\right)
$$

### Ý tưởng

- Thực hiện Top-K trên tập đã lọc thay vì trên toàn kho.

### Diễn giải bằng lời

Trong miền tuyển sinh, đây là cơ chế “đúng người đúng việc”: chỉ cho phép retrieval cạnh tranh trong tập tài liệu phù hợp ngữ cảnh nghiệp vụ. Nó tăng precision và giảm nguy cơ trả lời nhầm trường/nhầm năm.

---

## 15) Hàm hợp thành pipeline RAG

$$
\text{Answer}=G\big(q,\operatorname{TopK}(R(T(P(q))))\big)
$$

### Ý tưởng

- Đây là hàm hợp thành nhiều tầng:
  1. $P(q)$: tiền xử lý truy vấn,
  2. $T(\cdot)$: biến đổi truy vấn,
  3. $R(\cdot)$: retrieval + rerank,
  4. $\operatorname{TopK}(\cdot)$: chọn ngữ cảnh cuối,
  5. $G(\cdot)$: sinh câu trả lời.

### Diễn giải bằng lời

Công thức nói rằng chất lượng đầu ra không phải do riêng LLM, mà là kết quả dây chuyền. Một tầng yếu có thể kéo sập toàn bộ pipeline. Vì thế tối ưu RAG phải theo tư duy hệ thống: đo, chẩn đoán, và cải tiến từng tầng.

---

## 16) Chu trình vận hành vòng đời dữ liệu

$$
\text{Thu thập} \rightarrow \text{Chuẩn hóa} \rightarrow \text{Chỉ mục hóa} \rightarrow \text{Phục vụ truy vấn} \rightarrow \text{Đánh giá} \rightarrow \text{Cập nhật}
$$

### Ý tưởng

- Đây là “công thức quy trình”, không phải phương trình số học.
- Mô tả vòng lặp cải tiến liên tục của hệ thống RAG trong thực tế.

### Diễn giải bằng lời

RAG không phải mô hình train xong là kết thúc. Dữ liệu tuyển sinh đổi theo năm nên hệ thống phải có vòng đời dữ liệu khép kín để duy trì chất lượng lâu dài.

---

## Gợi ý đọc nhanh theo logic nhân-quả

Nếu cần nhớ nhanh toàn bộ phần toán trong báo cáo, có thể đi theo chuỗi sau:

1. **LLM objective**: $P(y\mid x)$ và $\arg\max$ (mục tiêu sinh có điều kiện).
2. **Retrieval geometry**: cosine similarity + metadata filter (tìm đúng tài liệu).
3. **Lexical grounding**: BM25 và hybrid score (neo vào thực thể cứng).
4. **Pipeline composition**: công thức hợp thành RAG (liên kết các tầng).
5. **Evaluation objective**: RAG Score + Error Rate (đo chất lượng và ổn định).

Chuỗi này thể hiện đúng tinh thần của báo cáo: **tăng độ đúng bằng ràng buộc dữ liệu, rồi đo lường để tối ưu liên tục**.
