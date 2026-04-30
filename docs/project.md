# admission-rag-chatbot

Một trang web tích hợp chatbot sử dụng RAG để tư vấn tuyển sinh cho các học sinh và phụ huynh.

## Mục tiêu
- Xây dựng một hệ thống chatbot RAG chạy localhost để hỗ trợ hỏi đáp tuyển sinh đại học.
- Hệ thống có 3 trang chính:
  - Trang chủ: Landing page giới thiệu dự án và hướng dẫn sử dụng.
  - Trang chatbot: Người dùng trò chuyện với chatbot để nhận tư vấn tuyển sinh.
  - Trang truy vấn: Người dùng tự tra cứu thông tin trường, ngành, phương thức xét tuyển.
- Ưu tiên tính đúng đắn theo dữ liệu đã crawl hơn là trả lời "hay".

## Phạm vi
- Đây là dự án bài tập lớn, triển khai và chạy trên localhost.
- Không nhắm tới production: không có yêu cầu HA, autoscaling, hoặc bảo mật doanh nghiệp.
- Dữ liệu tập trung vào các trường đã crawl được từ `tuyensinh247.com`.
- Không thay thế tư vấn tuyển sinh chính thức từ trường hoặc Bộ GD-DT.

## Tech stack
- Frontend: Next.js + Tailwind CSS
- Backend: python (3.11) + FastAPI
- Database: PostgreSQL
- Vector database: Chroma (persist xuống disk, không lưu vào RAM)
- AI: openrouter (openai/gpt-oss-120b:free)

## RAG pipeline
- Nguồn dữ liệu: mỗi trường đại học là một file JSON theo schema trong `packages/crawler/schema.md`.
- Quy trình tổng quát:
  1. Crawl/parse dữ liệu tuyển sinh -> JSON.
  2. Chuẩn hóa và tách chunk.
  3. Tạo embedding và lưu vào Chroma.
  4. Khi user hỏi: retrieve top-k chunk liên quan + tạo câu trả lời bằng LLM.
  5. Trả lời dựa trên ngữ cảnh đã truy xuất từ kho dữ liệu nội bộ.

### Chiến lược chunking (theo schema)
- University metadata chunk:
  - `university` + `admission_overview` + `admission_year` + `total_quota`
- Per-method chunk:
  - Mỗi `AdmissionMethod` là một chunk độc lập, gồm cả `programs[]`
- Raw-text chunks:
  - `cutoff_scores_text`
  - `tuition_text`
  - `timeline_text`

### Metadata filter đề xuất
- `university.code`
- `university.name`
- `university.location`
- `admission_year`
- `method_id`
- `program_code`
- `program_type`

## Mô hình dữ liệu đang có
- Mỗi file dữ liệu đại diện cho 1 trường: `{university_code}.json` (ví dụ: `KHA.json`, `BKA.json`, `FPT.json`).
- Trường dữ liệu quan trọng:
  - `university`: thông tin nhận diện trường (mã, tên, địa điểm, website, ...)
  - `admission_year`: năm tuyển sinh
  - `total_quota`: tổng chỉ tiêu
  - `admission_methods[]`: danh sách phương thức xét tuyển
  - `admission_methods[].programs[]`: danh sách ngành theo từng phương thức
  - `cutoff_scores_text`, `tuition_text`, `timeline_text`: text thô cho điểm chuẩn, học phí, mốc thời gian/hồ sơ
  - `source_url`, `pdf_url`: nguồn

## Yêu cầu chức năng (Functional Requirements)
- FR-01: Người dùng có thể chat nhiều lượt với chatbot trên trang chatbot.
- FR-02: Chatbot trả lời dựa trên dữ liệu đã index từ bộ JSON crawler.
- FR-03: Câu trả lời phải ưu tiên thông tin theo đúng trường/ngành/phương thức được hỏi.
- FR-04: Khi không đủ dữ liệu, chatbot phải nêu rõ "không đủ thông tin" thay vì suy đoán.
- FR-05: Trang truy vấn hỗ trợ tra cứu theo mã trường, tên trường, năm, phương thức, mã ngành, tổ hợp môn.
- FR-06: Có cơ chế ingest/re-index thủ công dữ liệu để phục vụ demo.

## Yêu cầu phi chức năng (Non-Functional Requirements)
- NFR-01: Hệ thống chạy ổn định trên localhost trong buổi demo.
- NFR-02: Thời gian phản hồi mục tiêu: trung bình 5-10 giây/câu hỏi (dataset nhỏ).
- NFR-03: Dữ liệu vector phải được persist trên disk để không mất sau khi restart.
- NFR-04: Cấu hình chạy bằng `.env`, không hard-code secret trong source code.
- NFR-05: Log lỗi cơ bản ở backend để dễ debug khi demo.

## Đánh giá chất lượng (Evaluation)
- Chuẩn bị bộ test tối thiểu 30 câu hỏi, chia theo nhóm:
  - Chỉ tiêu tuyển sinh
  - Phương thức xét tuyển
  - Ngành và tổ hợp môn
  - Học phí
  - Mốc thời gian và hồ sơ
- Báo cáo tối thiểu các chỉ số:
  - Tỉ lệ câu trả lời đúng theo dữ liệu
  - Tỉ lệ câu trả lời "không đủ thông tin" khi dữ liệu thiếu
  - Thời gian phản hồi trung bình

## Hạn chế dữ liệu đã biết
- Điểm chuẩn đang lưu dạng text thô, chưa có bảng cấu trúc chuẩn.
- Học phí lưu dạng text thô vì mỗi trường mô tả khác nhau.
- `program_type` được phân loại theo heuristic từ tên ngành/chương trình, có thể sai ở edge cases.
- Bảng HTML có rowspan/colspan được làm phẳng, có thể lặp giá trị ở một số ô.
- `note` trong một số dòng có thể chứa STT nếu bảng gốc không có cột ghi chú chuẩn.

## Giới hạn dự án
- Đây là sản phẩm phục vụ học thuật, không phải hệ thống tư vấn tuyển sinh chính thức.
- Kết quả trả lời phụ thuộc vào phạm vi và độ mới của dữ liệu crawl.
- Không cam kết tính đầy đủ tuyệt đối cho mọi trường/ngành tại mọi thời điểm.

## Hướng dẫn vận hành tối thiểu
- Chuẩn bị biến môi trường theo `.env.example`.
- Chạy backend FastAPI, frontend Next.js, PostgreSQL và Chroma local.
- Thực hiện ingest dữ liệu JSON trước khi demo chatbot.
- Kiểm tra nhanh bằng một bộ câu hỏi mẫu trước khi trình bày.
