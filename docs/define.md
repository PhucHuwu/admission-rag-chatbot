# TỪ ĐIỂN KHÁI NIỆM HÀN LÂM (BẢN DIỄN GIẢI CHI TIẾT VỪA ĐỦ)

Tài liệu này diễn giải các thực thể kiến thức hàn lâm xuất hiện trong báo cáo RAG tư vấn tuyển sinh. Mỗi khái niệm được viết ngắn gọn nhưng có thêm ngữ cảnh ứng dụng để dễ dùng khi thuyết trình và vấn đáp.

## Nhóm nền tảng mô hình

- **LLM (Large Language Model)**: Mô hình ngôn ngữ lớn sinh văn bản dựa trên xác suất token kế tiếp theo ngữ cảnh đầu vào. Trong bài toán tuyển sinh, LLM mạnh ở diễn đạt tự nhiên nhưng cần ràng buộc dữ liệu để tránh suy diễn.
- **Tự hồi quy (Autoregressive Generation)**: Cơ chế sinh tuần tự từng token, trong đó token mới phụ thuộc chuỗi token trước đó. Vì sinh theo chuỗi, sai lệch ngữ cảnh ở đầu có thể lan truyền sang toàn bộ câu trả lời.
- **Giải mã (Decoding)**: Quy tắc chọn token tại mỗi bước sinh (ví dụ greedy, sampling). Quy tắc này ảnh hưởng trực tiếp tính ổn định, độ đa dạng và mức nhất quán của phản hồi.
- **Temperature**: Siêu tham số điều chỉnh độ ngẫu nhiên của phân phối sinh. Temperature thấp cho đầu ra chắc tay hơn; temperature cao tăng đa dạng nhưng dễ dao động dữ kiện.

## Nhóm biểu diễn và truy xuất

- **Embedding**: Biểu diễn văn bản thành vector số trong không gian ngữ nghĩa nhiều chiều. Nhờ embedding, hệ thống có thể tìm đoạn “cùng ngữ nghĩa” dù khác từ bề mặt.
- **Semantic Similarity**: Mức gần nghĩa giữa hai văn bản, thường tính từ khoảng cách/góc giữa hai vector embedding. Đây là lõi của semantic retrieval.
- **Cosine Similarity**: Độ tương đồng theo góc giữa hai vector; giá trị càng gần 1 thì càng gần nghĩa. Chỉ số này giảm tác động của độ dài văn bản so với so khớp từ khóa thuần.
- **Vector Database**: Hệ lưu trữ và truy vấn tối ưu cho dữ liệu vector, thường hỗ trợ top-k nearest neighbors và filter metadata. Đây là hạ tầng truy xuất trung tâm của RAG.
- **Top-k Retrieval**: Bước lấy ra k ứng viên có điểm liên quan cao nhất từ kho tri thức. K quá nhỏ dễ thiếu thông tin, K quá lớn dễ tăng nhiễu.
- **ANN (Approximate Nearest Neighbor)**: Kỹ thuật tìm lân cận gần đúng để giảm độ trễ truy xuất ở quy mô lớn. Đánh đổi là có thể bỏ sót một phần nhỏ ứng viên tốt nhất tuyệt đối.
- **Metadata Filter**: Điều kiện lọc theo thuộc tính miền như mã trường, năm tuyển sinh, loại nội dung. Filter giúp tăng precision vì loại bỏ tài liệu không thuộc phạm vi câu hỏi.

## Nhóm truy xuất lexical và hybrid

- **Lexical Retrieval**: Truy xuất dựa trên khớp từ khóa bề mặt, phù hợp khi truy vấn chứa thực thể cụ thể như mã ngành/tổ hợp. Điểm mạnh là chính xác thực thể, điểm yếu là kém linh hoạt diễn đạt.
- **BM25**: Hàm xếp hạng lexical kinh điển, cân bằng tần suất từ khóa, độ dài tài liệu và độ hiếm của từ. BM25 đặc biệt hữu ích trong truy vấn chứa cụm thuật ngữ cố định.
- **IDF (Inverse Document Frequency)**: Thành phần tăng trọng số cho từ hiếm và giảm trọng số cho từ quá phổ biến trong tập tài liệu. Mục tiêu là làm nổi bật tín hiệu phân biệt.
- **Hybrid Search**: Cơ chế kết hợp semantic score và lexical score để vừa hiểu ý tự nhiên vừa bám thực thể cứng. Đây là hướng thực dụng để tăng độ bền retrieval trong dữ liệu thật.

## Nhóm kiến trúc RAG

- **RAG (Retrieval-Augmented Generation)**: Kiến trúc kết hợp truy xuất tri thức ngoài với khả năng sinh ngôn ngữ của LLM. Mục tiêu là giảm hallucination và tăng khả năng kiểm chứng phản hồi.
- **Naive RAG**: Biến thể đơn giản: truy xuất một lần, sinh một lần. Dễ triển khai nhưng nhạy với nhiễu retrieval.
- **Multi-query RAG**: Tạo nhiều biến thể truy vấn để tăng khả năng bao phủ tài liệu liên quan (recall). Thường cho chất lượng tốt hơn với truy vấn ngắn/viết tắt.
- **Iterative RAG**: Truy xuất và sinh theo nhiều vòng, dùng kết quả trung gian để truy xuất bổ sung. Phù hợp câu hỏi phức tạp nhưng chi phí thời gian cao hơn.
- **Preprocess Query**: Chuẩn hóa truy vấn đầu vào (khoảng trắng, ký tự, viết tắt) để giảm sai khác bề mặt. Đây là lớp chống nhiễu sớm trong pipeline.
- **Query Transformation**: Biến đổi một truy vấn thành nhiều cách diễn đạt tương đương về ý nghĩa. Mục tiêu là tăng xác suất chạm đúng cụm tri thức trong kho.
- **Reranking**: Tái chấm điểm và sắp hạng lại ứng viên sau retrieval ban đầu. Vai trò chính là tăng Context Precision trước khi chuyển sang generation.
- **Context Window (ngữ cảnh đưa vào sinh)**: Tập đoạn văn bản được chọn làm bằng chứng cho LLM. Chất lượng context window quyết định trực tiếp trần chất lượng phản hồi.
- **Decision Gate / data_sufficient**: Cổng ra quyết định dữ liệu đủ hay thiếu trước khi trả lời. Cơ chế này giúp hệ thống trả lời có trách nhiệm thay vì khẳng định khi thiếu bằng chứng.

## Nhóm dữ liệu và tiền xử lý

- **Schema**: Cấu trúc chuẩn của dữ liệu gồm trường, kiểu dữ liệu, và quy ước liên kết. Schema tốt giúp truy xuất nhất quán và giảm lỗi tích hợp nguồn.
- **Chunking**: Chia tài liệu dài thành đoạn nhỏ để embedding và retrieval hoạt động hiệu quả. Thiết kế chunk cần cân bằng giữa đủ ngữ cảnh và đủ tập trung chủ đề.
- **Chunk Overlap**: Phần chồng lấp giữa hai chunk liên tiếp để giảm mất mạch thông tin ở ranh giới đoạn. Overlap cao tăng recall nhưng tăng chi phí chỉ mục.
- **Knowledge Base**: Kho tri thức đã được chuẩn hóa, phân đoạn, gắn metadata và sẵn sàng truy xuất. Đây là lớp “sự thật dữ liệu” của hệ thống.
- **Ingestion / Indexing**: Quy trình nạp dữ liệu vào kho và tạo chỉ mục truy xuất vector/metadata. Chất lượng ingestion ảnh hưởng trực tiếp chất lượng retrieval sau này.

## Nhóm hội thoại và tương tác

- **Multi-turn Conversation**: Hội thoại nhiều lượt, trong đó mỗi lượt mới có thể phụ thuộc ngữ cảnh các lượt trước. Bài toán cốt lõi là giữ mạch ngữ nghĩa liên tục mà không kéo nhiễu lịch sử quá xa.
- **Query Rewrite (theo lịch sử)**: Viết lại câu hỏi rút gọn thành câu đầy đủ dựa trên lịch sử gần. Rewrite đúng giúp retrieval hiểu đúng chủ thể đang được nhắc đến.
- **Streaming Response**: Trả lời dần theo dòng token thay vì đợi hoàn tất toàn bộ. Cách này không luôn giảm độ trễ tuyệt đối nhưng cải thiện rõ độ trễ cảm nhận.

## Nhóm đánh giá học thuật

- **Evaluation (định lượng)**: Đo chất lượng bằng bộ chỉ số rõ ràng thay vì nhận xét cảm tính. Đây là điều kiện để so sánh cấu hình một cách khoa học.
- **Reference-free Metrics**: Chỉ số đánh giá không phụ thuộc hoàn toàn vào một đáp án vàng duy nhất. Phù hợp với bài toán hội thoại mở có nhiều cách diễn đạt đúng.
- **Faithfulness**: Mức độ phát biểu trong câu trả lời được hỗ trợ bởi ngữ cảnh truy xuất. Faithfulness cao đồng nghĩa rủi ro bịa đặt thấp.
- **Answer Relevancy**: Mức độ câu trả lời đi đúng trọng tâm câu hỏi. Chỉ số này tách biệt vấn đề “đúng dữ kiện” với “đúng ý hỏi”.
- **Context Precision**: Tỷ lệ phần ngữ cảnh truy xuất thực sự hữu ích cho đáp án. Chỉ số cao cho thấy retrieval/reranking ít kéo nhiễu.
- **RAG Score**: Điểm tổng hợp trung bình của Faithfulness, Answer Relevancy và Context Precision. Dùng để nhìn nhanh chất lượng đầu-cuối toàn hệ thống.
- **Latency (mean/p50/p95/p99)**: Nhóm chỉ số thời gian phản hồi; mean thể hiện trung bình, p50 là trung vị, p95/p99 phản ánh vùng đuôi truy vấn chậm. Đây là chỉ báo quan trọng của trải nghiệm thực tế.
- **Error Rate**: Tỷ lệ truy vấn không trả về kết quả hợp lệ trên tổng truy vấn. Chỉ số này phản ánh độ ổn định vận hành, không chỉ chất lượng nội dung.
- **Benchmark**: Bộ truy vấn chuẩn hóa, có phân nhóm chủ đề và độ khó, dùng để so sánh công bằng giữa các cấu hình.
- **Ablation Study**: Phương pháp tắt từng thành phần trong khi giữ nguyên phần còn lại để đo đóng góp riêng. Đây là cách kết luận nhân quả kỹ thuật rõ hơn so với so sánh cảm tính.

## Nhóm phương pháp luận hệ thống

- **Modular Pipeline**: Thiết kế theo các mô-đun độc lập (preprocess, retrieval, rerank, generation) để dễ thay thế và kiểm thử từng tầng.
- **End-to-end Quality**: Chất lượng đầu-cuối phản ánh kết quả của toàn chuỗi xử lý, không chỉ năng lực một thành phần riêng lẻ.
- **Precision-Recall Trade-off**: Đánh đổi giữa trả về ít nhưng rất đúng (precision cao) và trả về rộng để ít bỏ sót (recall cao).
- **Quality-Latency Trade-off**: Đánh đổi giữa tăng chất lượng và tăng thời gian phản hồi; thường gặp khi thêm query transform hoặc reranking sâu.
- **Data Lifecycle**: Vòng đời dữ liệu liên tục từ thu thập đến cập nhật lại chỉ mục. Tư duy vòng đời giúp hệ thống duy trì chất lượng theo thời gian, đặc biệt khi dữ liệu tuyển sinh thay đổi theo niên khóa.

## Ghi nhớ nhanh

- **RAG mạnh** khi retrieval đúng, context sạch, và generation bị ràng buộc bởi bằng chứng.
- **Sai số phổ biến** thường nằm ở truy xuất ngữ cảnh (thiếu hoặc nhiễu), không chỉ nằm ở mô hình sinh.
- **Đánh giá chuẩn** cần nhìn đồng thời chất lượng nội dung (F/AR/CP) và hiệu năng vận hành (latency/error rate).
