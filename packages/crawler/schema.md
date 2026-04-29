# University Admission Data Schema (RAG-Optimized)

## Overview

Each university admission page from `tuyensinh247.com` is parsed into a single JSON file.
Data is structured for **Retrieval-Augmented Generation (RAG)** chatbot use-case:
- Flat top-level metadata for fast filtering
- Text-heavy sections preserved as raw strings for semantic search
- Structured program lists for precise retrieval

---

## File Structure

One JSON file per university, named `{university_code}.json`.

Example: `KHA.json`, `BKA.json`, `FPT.json`

---

## Top-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `university` | `UniversityInfo` | School identity and contact info |
| `admission_year` | `number \| null` | Academic year of admission (e.g. 2026) |
| `total_quota` | `number \| null` | Total enrollment quota |
| `source_url` | `string` | Original crawled URL |
| `pdf_url` | `string \| null` | Link to official PDF admission plan |
| `admission_overview` | `string \| null` | Executive summary text from top of page |
| `admission_methods` | `AdmissionMethod[]` | List of admission methods with programs |
| `cutoff_scores_text` | `string \| null` | Raw text from "Điểm chuẩn" section |
| `tuition_text` | `string \| null` | Raw text from "Học phí" section |
| `timeline_text` | `string \| null` | Raw text from "Thờigian và hồ sơ" section |

---

## `UniversityInfo`

```typescript
interface UniversityInfo {
  code: string;           // e.g. "KHA", "BKA", "FPT"
  name: string;           // Full Vietnamese name
  short_name: string | null;  // Abbreviation, e.g. "NEU", "HUST"
  location: string[];     // City list, e.g. ["Hà Nội"]
  address: string | null;
  website: string | null;
  type: string | null;    // "công lập" | "tư thục" | "quốc tế" | null
  description: string | null;
}
```

---

## `AdmissionMethod`

Each method represents one admission pathway (e.g. Điểm thi THPT, Xét tuyển thẳng, Chứng chỉ quốc tế...).

```typescript
interface AdmissionMethod {
  method_id: string;      // slugified name, e.g. "diem-thi-thpt"
  method_name: string;    // Human-readable name
  description: string | null;   // General rules / summary text
  eligibility: string | null;   // Đối tượng xét tuyển
  rules: string | null;         // Quy chế / conditions
  programs: ProgramInfo[];      // Programs available under this method
}
```

**Method ID naming convention:**
- Slugified Vietnamese, lowercase, hyphen-separated
- Examples: `diem-thi-thpt`, `uutien-xet-tuyen-thang`, `chung-chi-quoc-te`

---

## `ProgramInfo`

Each program (major) under a specific admission method.

```typescript
interface ProgramInfo {
  program_code: string;       // e.g. "7220201", "CLC1", "BF1"
  program_name: string;       // e.g. "Ngôn ngữ Anh"
  subject_groups: string[];   // e.g. ["A00", "A01", "D01", "D07"]
  program_type: string;       // See enum below
  note: string | null;        // Additional note / remark
}
```

### `program_type` enum values

| Value | Meaning |
|-------|---------|
| `chuẩn` | Standard program |
| `tiên_tiến` | Advanced / Elitech program |
| `chất_lượng_cao` | High-quality (CLC) program |
| `liên_kết_quốc_tế` | International joint program |
| `việt_pháp` | PFIEV Vietnam-France program |
| `liên_kết_troy` | Troy University joint program |

---

## Data Coverage per Page Section

| DOM Section | Extracted To | Coverage |
|-------------|--------------|----------|
| Overview text (before first section) | `admission_overview` | Full text |
| Phương thức xét tuyển | `admission_methods[]` | Each method split individually |
| Danh sách ngành đào tạo | `admission_methods[].programs` | All programs per method |
| Điểm chuẩn | `cutoff_scores_text` | Raw text (links to historical data) |
| Học phí | `tuition_text` | Raw text with fee ranges |
| Thờigian và hồ sơ | `timeline_text` | Raw text with schedule & requirements |
| File PDF | `pdf_url` | First PDF link found |
| Giới thiệu trường | `university` object | Name, address, website, code |

---

## Sample JSON (Condensed)

```json
{
  "university": {
    "code": "KHA",
    "name": "Đại Học Kinh Tế Quốc Dân",
    "short_name": "NEU",
    "location": ["Hà Nội"],
    "address": "207 đường Giải Phóng, Q. Hai Bà Trưng, Hà Nội",
    "website": "http://www.neu.edu.vn",
    "type": null,
    "description": null
  },
  "admission_year": 2026,
  "total_quota": 8780,
  "source_url": "https://diemthi.tuyensinh247.com/de-an-tuyen-sinh/dai-hoc-kinh-te-quoc-dan-KHA.html",
  "pdf_url": "https://images.tuyensinh247.com/picture/2026/0306/thong-tin-tuyen-sinh-dai-hoc-kinh-te-quoc-dan-2026.pdf",
  "admission_overview": "Thông tin tuyển sinh Đại Học Kinh Tế Quốc Dân (NEU) năm 2026...",
  "admission_methods": [
    {
      "method_id": "diem-thi-thpt",
      "method_name": "1 ĐIỂM THI THPT",
      "description": "Xét theo kết quả điểm thi TN THPT năm 2026...",
      "eligibility": "Đối tượng dự tuyển...",
      "rules": "Tổ hợp xét tuyển: A00, A01, D01, D07...",
      "programs": [
        {
          "program_code": "7220201",
          "program_name": "Ngôn ngữ Anh",
          "subject_groups": ["A00", "A01", "D01", "D07"],
          "program_type": "chuẩn",
          "note": null
        }
      ]
    }
  ],
  "cutoff_scores_text": "Xem điểm chuẩn Đại học Kinh tế quốc dân các năm Tại đây",
  "tuition_text": "Học phí đại học chính quy chương trình chuẩn...",
  "timeline_text": "Tổ chức tuyển sinh ĐHKTQD xét tuyển theo kế hoạch..."
}
```

---

## Known Limitations

1. **Cutoff scores** are stored as raw text (not structured tables) because tuyensinh247 links to external historical pages rather than embedding tabular data.
2. **Tuition** is stored as raw text because fee structures vary by program type and are described in paragraphs.
3. **Program type detection** is heuristic-based on program name keywords (e.g. "tiên tiến", "CLC", "liên kết"). Edge cases may be misclassified.
4. **Rowspan/colspan tables** are normalized into a flat grid; merged cells are duplicated across affected rows/columns.
5. **Note field** may occasionally capture STT (row number) when the table lacks a true "Ghi chú" column.

---

## RAG Chunking Recommendation

For optimal RAG retrieval, chunk each JSON into the following document units:

1. **University metadata chunk** — `university` object + `admission_overview` + `admission_year` + `total_quota`
2. **Per-method chunk** — Each `AdmissionMethod` as a standalone document, including its `programs[]`
3. **Raw-text chunks** — `cutoff_scores_text`, `tuition_text`, `timeline_text` each as separate documents

This allows the retriever to:
- Filter by university code / location first
- Retrieve specific admission methods by query intent
- Answer fee/timeline questions from raw text
