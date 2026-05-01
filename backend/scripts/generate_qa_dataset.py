from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


CUTOFF_MISSING_CODES = {"DNH", "DQH", "DYH", "TCU", "CIV", "LCDF", "RHM", "RMU"}


@dataclass
class QAItem:
    question: str
    answer: str
    intent: str
    university_code: str
    university_name: str
    admission_year: int | None
    data_status: str
    confidence: float
    tags: list[str]


def variants(*qs: str) -> list[str]:
    return [q.strip() for q in qs if q and q.strip()]


def compact_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def get_uni_name(data: dict[str, Any]) -> str:
    return compact_text(data.get("university", {}).get("name")) or "Trường chưa rõ tên"


def get_uni_code(data: dict[str, Any], fallback: str) -> str:
    return (compact_text(data.get("university", {}).get("code")) or fallback).upper()


def fallback_missing_message(topic: str, school: str, year: int | None) -> str:
    year_text = str(year) if year else "năm hiện tại"
    return (
        f"Xin lỗi, hiện chưa có dữ liệu {topic} của {school} cho {year_text} "
        "trong bộ crawl hiện tại."
    )


def qa_overview(data: dict[str, Any], code: str, name: str) -> list[QAItem]:
    year = data.get("admission_year")
    overview = compact_text(data.get("admission_overview"))
    quota = data.get("total_quota")
    quota_text = f"Tổng chỉ tiêu hiện có là {quota}." if quota is not None else "Hiện chưa có số liệu tổng chỉ tiêu rõ ràng."
    answer = f"Thông tin tuyển sinh của {name} cho năm {year if year else 'hiện tại'}: {overview} {quota_text}".strip()
    items: list[QAItem] = []
    for q in variants(
        f"Thông tin tuyển sinh tổng quan của {name} năm {year if year else 'hiện tại'} là gì?",
        f"Cho mình xin thông tin tuyển sinh của {name}.",
        f"{name} năm nay tuyển sinh ra sao?",
        f"Tổng quan đề án tuyển sinh của {name} thế nào?",
        f"Năm {year if year else 'nay'}, {name} có gì đáng chú ý trong tuyển sinh?",
        f"{name} tuyển sinh những gì trong năm {year if year else 'hiện tại'}?",
    ):
        items.append(
            QAItem(
                question=q,
                answer=answer,
                intent="admission_overview",
                university_code=code,
                university_name=name,
                admission_year=year,
                data_status="complete" if overview else "partial",
                confidence=0.9 if overview else 0.4,
                tags=["overview", "quota"],
            )
        )
    return items


def qa_methods(data: dict[str, Any], code: str, name: str) -> list[QAItem]:
    year = data.get("admission_year")
    methods = data.get("admission_methods") or []
    items: list[QAItem] = []
    if not methods:
        for q in variants(
            f"{name} có những phương thức xét tuyển nào?",
            f"Các cách xét tuyển vào {name} là gì?",
            f"Năm nay {name} xét tuyển theo những phương thức nào?",
            f"Mình có thể vào {name} bằng các diện nào?",
            f"{name} nhận hồ sơ theo các phương thức nào?",
        ):
            items.append(
                QAItem(
                    question=q,
                    answer=fallback_missing_message("phương thức xét tuyển", name, year),
                    intent="admission_methods",
                    university_code=code,
                    university_name=name,
                    admission_year=year,
                    data_status="missing",
                    confidence=0.2,
                    tags=["methods", "missing"],
                )
            )
        return items

    method_names = [compact_text(m.get("method_name")) for m in methods if compact_text(m.get("method_name"))]
    if method_names:
        answer_methods = "Các phương thức xét tuyển gồm: " + "; ".join(method_names) + "."
        for q in variants(
            f"{name} có những phương thức xét tuyển nào trong năm {year if year else 'hiện tại'}?",
            f"Các phương thức xét tuyển của {name} là gì?",
            f"{name} tuyển sinh theo những diện nào?",
            f"Mình muốn vào {name} thì có các cách xét tuyển nào?",
            f"Năm {year if year else 'nay'}, {name} dùng các phương thức nào để tuyển sinh?",
        ):
            items.append(
                QAItem(
                    question=q,
                    answer=answer_methods,
                    intent="admission_methods",
                    university_code=code,
                    university_name=name,
                    admission_year=year,
                    data_status="complete",
                    confidence=0.95,
                    tags=["methods"],
                )
            )

    for method in methods:
        method_name = compact_text(method.get("method_name"))
        if not method_name:
            continue
        desc = compact_text(method.get("description"))
        eligibility = compact_text(method.get("eligibility"))
        rules = compact_text(method.get("rules"))
        answer_parts = [f"Phương thức {method_name}."]
        if desc:
            answer_parts.append(f"Mô tả: {desc}")
        if eligibility:
            answer_parts.append(f"Đối tượng: {eligibility}")
        if rules:
            answer_parts.append(f"Quy chế: {rules}")
        for q in variants(
            f"Điều kiện và quy chế của phương thức {method_name} tại {name} là gì?",
            f"Phương thức {method_name} của {name} yêu cầu những gì?",
            f"Mình cần đáp ứng điều kiện nào để xét theo {method_name} ở {name}?",
            f"Quy định xét tuyển theo {method_name} của {name} ra sao?",
            f"Cho mình biết đối tượng áp dụng của {method_name} tại {name}.",
        ):
            items.append(
                QAItem(
                    question=q,
                    answer=" ".join(answer_parts),
                    intent="method_detail",
                    university_code=code,
                    university_name=name,
                    admission_year=year,
                    data_status="complete" if (desc or eligibility or rules) else "partial",
                    confidence=0.88 if (desc or eligibility or rules) else 0.45,
                    tags=["methods", "eligibility", "rules"],
                )
            )
    return items


def qa_programs(data: dict[str, Any], code: str, name: str, max_programs_per_school: int) -> list[QAItem]:
    year = data.get("admission_year")
    methods = data.get("admission_methods") or []
    items: list[QAItem] = []

    seen_programs: set[tuple[str, str]] = set()
    count = 0

    for method in methods:
        method_name = compact_text(method.get("method_name"))
        for p in method.get("programs") or []:
            program_name = compact_text(p.get("program_name"))
            program_code = compact_text(p.get("program_code"))
            if not program_name:
                continue
            key = (program_name, program_code)
            if key in seen_programs:
                continue
            seen_programs.add(key)

            subject_groups = p.get("subject_groups") or []
            groups_text = ", ".join(subject_groups) if subject_groups else "chưa có dữ liệu tổ hợp môn"
            ptype = compact_text(p.get("program_type")) or "chưa rõ"
            answer = (
                f"Ngành {program_name} (mã {program_code if program_code else 'chưa rõ'}) tại {name} "
                f"thuộc loại chương trình {ptype}. "
                f"Tổ hợp môn: {groups_text}. "
                f"Phương thức liên quan: {method_name if method_name else 'chưa rõ'}"
            )
            status = "complete" if subject_groups else "partial"
            confidence = 0.9 if subject_groups else 0.65
            for q in variants(
                f"Ngành {program_name} của {name} xét tuyển như thế nào?",
                f"Muốn học ngành {program_name} ở {name} thì xét tuyển ra sao?",
                f"{name} tuyển ngành {program_name} theo phương thức nào?",
                f"Ngành {program_name} tại {name} có tổ hợp gì và điều kiện gì?",
                f"Cho mình thông tin xét tuyển ngành {program_name} của {name}.",
            ):
                items.append(
                    QAItem(
                        question=q,
                        answer=answer,
                        intent="program_detail",
                        university_code=code,
                        university_name=name,
                        admission_year=year,
                        data_status=status,
                        confidence=confidence,
                        tags=["program", "subject_groups", "program_type"],
                    )
                )

            if not subject_groups:
                for q in variants(
                    f"{name} xét tổ hợp nào cho ngành {program_name}?",
                    f"Tổ hợp môn ngành {program_name} của {name} là gì?",
                    f"Ngành {program_name} ở {name} cần những môn nào để xét tuyển?",
                    f"Cho mình tổ hợp xét tuyển ngành {program_name} tại {name}.",
                ):
                    items.append(
                        QAItem(
                            question=q,
                            answer=(
                                f"Xin lỗi, hiện chưa có dữ liệu tổ hợp môn cho ngành {program_name} của {name} "
                                "trong bộ crawl hiện tại."
                            ),
                            intent="subject_group_missing",
                            university_code=code,
                            university_name=name,
                            admission_year=year,
                            data_status="missing",
                            confidence=0.3,
                            tags=["program", "missing", "subject_groups"],
                        )
                    )

            count += 1
            if count >= max_programs_per_school:
                return items

    if not items:
        for q in variants(
            f"{name} có những ngành đào tạo nào?",
            f"Danh sách ngành của {name} gồm những gì?",
            f"Trường {name} đang tuyển các ngành nào?",
            f"Mình muốn xem các ngành của {name}.",
        ):
            items.append(
                QAItem(
                    question=q,
                    answer=fallback_missing_message("ngành đào tạo", name, year),
                    intent="programs_missing",
                    university_code=code,
                    university_name=name,
                    admission_year=year,
                    data_status="missing",
                    confidence=0.2,
                    tags=["program", "missing"],
                )
            )
    return items


def qa_cutoff(data: dict[str, Any], code: str, name: str) -> list[QAItem]:
    year = data.get("admission_year")
    items: list[QAItem] = []

    if code in CUTOFF_MISSING_CODES:
        for q in variants(
            f"Điểm chuẩn của {name} năm {year if year else 'hiện tại'} là bao nhiêu?",
            f"Năm nay {name} lấy bao nhiêu điểm chuẩn?",
            f"Cho mình điểm chuẩn mới nhất của {name}.",
            f"Mức điểm trúng tuyển của {name} hiện có chưa?",
            f"Điểm vào {name} năm {year if year else 'nay'} là bao nhiêu?",
        ):
            items.append(
                QAItem(
                    question=q,
                    answer=fallback_missing_message("điểm chuẩn", name, year),
                    intent="cutoff_missing_known",
                    university_code=code,
                    university_name=name,
                    admission_year=year,
                    data_status="missing",
                    confidence=0.2,
                    tags=["cutoff", "missing", "known_exception"],
                )
            )
        return items

    cutoff = data.get("cutoff_scores") or {}
    methods = cutoff.get("methods") or []
    found_structured = False
    for method in methods:
        method_name = compact_text(method.get("method_name"))
        cutoff_year = method.get("year") or cutoff.get("year") or year
        entries = method.get("entries") or []
        for e in entries:
            program_name = compact_text(e.get("program_name"))
            score = e.get("score")
            if not program_name or score in (None, ""):
                continue
            found_structured = True
            answer = (
                f"Theo dữ liệu hiện có, điểm chuẩn ngành {program_name} của {name} "
                f"({method_name if method_name else 'phương thức hiện có'}) là {score} "
                f"cho năm {cutoff_year}."
            )
            for q in variants(
                f"Điểm chuẩn ngành {program_name} của {name} là bao nhiêu?",
                f"Ngành {program_name} ở {name} lấy bao nhiêu điểm?",
                f"Mức điểm trúng tuyển ngành {program_name} của {name} là bao nhiêu?",
                f"Cho mình điểm chuẩn {program_name} tại {name}.",
                f"Điểm vào ngành {program_name} của {name} năm {cutoff_year} là bao nhiêu?",
            ):
                items.append(
                    QAItem(
                        question=q,
                        answer=answer,
                        intent="cutoff_score",
                        university_code=code,
                        university_name=name,
                        admission_year=year,
                        data_status="complete",
                        confidence=0.95,
                        tags=["cutoff", "structured"],
                    )
                )

    if found_structured:
        return items

    cutoff_text = compact_text(data.get("cutoff_scores_text"))
    if cutoff_text:
        for q in variants(
            f"Điểm chuẩn của {name} có thông tin gì?",
            f"Hiện có dữ liệu điểm chuẩn nào của {name}?",
            f"Mình xem thông tin điểm chuẩn {name} ở đâu trong dữ liệu hiện có?",
            f"{name} đã có công bố điểm chuẩn chi tiết chưa?",
        ):
            items.append(
                QAItem(
                    question=q,
                    answer=f"Thông tin điểm chuẩn hiện có ở dạng mô tả: {cutoff_text}",
                    intent="cutoff_text_only",
                    university_code=code,
                    university_name=name,
                    admission_year=year,
                    data_status="partial",
                    confidence=0.6,
                    tags=["cutoff", "raw_text"],
                )
            )
    else:
        for q in variants(
            f"Điểm chuẩn của {name} năm {year if year else 'hiện tại'} là bao nhiêu?",
            f"Năm nay {name} lấy bao nhiêu điểm?",
            f"Cho mình điểm chuẩn mới nhất của {name}.",
            f"{name} đã có điểm trúng tuyển chưa?",
        ):
            items.append(
                QAItem(
                    question=q,
                    answer=fallback_missing_message("điểm chuẩn", name, year),
                    intent="cutoff_missing",
                    university_code=code,
                    university_name=name,
                    admission_year=year,
                    data_status="missing",
                    confidence=0.2,
                    tags=["cutoff", "missing"],
                )
            )
    return items


def qa_tuition_timeline(data: dict[str, Any], code: str, name: str) -> list[QAItem]:
    year = data.get("admission_year")
    tuition = compact_text(data.get("tuition_text"))
    timeline = compact_text(data.get("timeline_text"))
    items: list[QAItem] = []

    for q in variants(
        f"Học phí của {name} năm {year if year else 'hiện tại'} như thế nào?",
        f"Cho mình thông tin học phí của {name}.",
        f"Mức học phí tại {name} hiện nay ra sao?",
        f"{name} có học phí dự kiến bao nhiêu?",
        f"Học ở {name} tốn khoảng bao nhiêu tiền?",
    ):
        items.append(
            QAItem(
                question=q,
                answer=(f"Thông tin học phí: {tuition}" if tuition else fallback_missing_message("học phí", name, year)),
                intent="tuition",
                university_code=code,
                university_name=name,
                admission_year=year,
                data_status="complete" if tuition else "missing",
                confidence=0.85 if tuition else 0.2,
                tags=["tuition"],
            )
        )
    for q in variants(
        f"Mốc thời gian và hồ sơ xét tuyển của {name} là gì?",
        f"Khi nào nộp hồ sơ vào {name}?",
        f"Lịch tuyển sinh của {name} năm nay như thế nào?",
        f"Cho mình timeline xét tuyển của {name}.",
        f"{name} yêu cầu hồ sơ và thời gian đăng ký ra sao?",
    ):
        items.append(
            QAItem(
                question=q,
                answer=(
                    f"Thông tin thời gian và hồ sơ: {timeline}"
                    if timeline
                    else fallback_missing_message("thời gian và hồ sơ", name, year)
                ),
                intent="timeline",
                university_code=code,
                university_name=name,
                admission_year=year,
                data_status="complete" if timeline else "missing",
                confidence=0.85 if timeline else 0.2,
                tags=["timeline"],
            )
        )
    return items


def generate_for_school(data: dict[str, Any], code: str, max_programs_per_school: int) -> list[QAItem]:
    name = get_uni_name(data)
    items: list[QAItem] = []
    items.extend(qa_overview(data, code, name))
    items.extend(qa_methods(data, code, name))
    items.extend(qa_programs(data, code, name, max_programs_per_school=max_programs_per_school))
    items.extend(qa_cutoff(data, code, name))
    items.extend(qa_tuition_timeline(data, code, name))
    return items


def write_jsonl(path: Path, items: list[QAItem]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate full-case Q&A dataset from crawled admission JSON files")
    parser.add_argument("--data-dir", default="../data", help="Path to source JSON directory")
    parser.add_argument("--output", default="./storage/qa_dataset.jsonl", help="Output JSONL path")
    parser.add_argument(
        "--max-programs-per-school",
        type=int,
        default=50,
        help="Max number of unique program Q&A generated per school",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    files = sorted(data_dir.glob("*.json")) if data_dir.exists() else []
    if not files:
        raise SystemExit(f"No JSON files found in {data_dir}")

    all_items: list[QAItem] = []
    for file_path in files:
        data = load_json(file_path)
        code = get_uni_code(data, fallback=file_path.stem)
        all_items.extend(generate_for_school(data, code=code, max_programs_per_school=args.max_programs_per_school))

    output = Path(args.output)
    write_jsonl(output, all_items)

    print(f"Generated {len(all_items)} QA pairs from {len(files)} schools")
    print(f"Output: {output.resolve()}")


if __name__ == "__main__":
    main()
