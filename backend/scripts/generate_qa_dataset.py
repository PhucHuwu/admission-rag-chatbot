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


def compact_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def variants(*qs: str) -> list[str]:
    return [q.strip() for q in qs if q and q.strip()]


def unique_qa(items: list[QAItem]) -> list[QAItem]:
    seen: set[tuple[str, str, str]] = set()
    out: list[QAItem] = []
    for item in items:
        key = (item.university_code, item.intent, item.question.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def fallback_missing_message(topic: str, school: str, year: int | None) -> str:
    year_text = str(year) if year else "năm hiện tại"
    return f"Xin lỗi, hiện tại {topic} của {school} cho {year_text} chưa được cung cấp."


def qa_item(
    question: str,
    answer: str,
    intent: str,
    code: str,
    name: str,
    year: int | None,
    data_status: str,
    confidence: float,
    tags: list[str],
) -> QAItem:
    return QAItem(
        question=question,
        answer=answer,
        intent=intent,
        university_code=code,
        university_name=name,
        admission_year=year,
        data_status=data_status,
        confidence=confidence,
        tags=tags,
    )


def school_aliases(name: str, short_name: str | None, code: str) -> list[str]:
    aliases = {name, code}
    if short_name:
        aliases.add(short_name)
    aliases.add(name.replace("Đại Học", "ĐH"))
    aliases.add(name.replace("Đại học", "ĐH"))
    aliases.add(name.replace("Học viện", "HV"))
    return [a for a in aliases if compact_text(a)]


def build_method_summary(methods: list[dict[str, Any]]) -> str:
    lines = []
    for m in methods:
        method_name = compact_text(m.get("method_name"))
        desc = compact_text(m.get("description"))
        if method_name:
            lines.append(f"- {method_name}: {desc}" if desc else f"- {method_name}")
    return "\n".join(lines)


def build_program_list(methods: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    all_programs: list[dict[str, Any]] = []
    program_to_methods: dict[str, list[str]] = {}
    for method in methods:
        m_name = compact_text(method.get("method_name"))
        for p in method.get("programs") or []:
            p_name = compact_text(p.get("program_name"))
            p_code = compact_text(p.get("program_code"))
            p_type = compact_text(p.get("program_type"))
            groups = p.get("subject_groups") or []
            all_programs.append(
                {
                    "program_name": p_name,
                    "program_code": p_code,
                    "program_type": p_type,
                    "subject_groups": groups,
                    "method_name": m_name,
                }
            )
            if p_name:
                program_to_methods.setdefault(p_name, [])
                if m_name and m_name not in program_to_methods[p_name]:
                    program_to_methods[p_name].append(m_name)
    return all_programs, program_to_methods


def qa_overview(data: dict[str, Any], code: str, name: str, aliases: list[str]) -> list[QAItem]:
    year = data.get("admission_year")
    overview = compact_text(data.get("admission_overview"))
    quota = data.get("total_quota")
    quota_text = f"Tổng chỉ tiêu: {quota}." if quota is not None else "Chưa có số liệu tổng chỉ tiêu rõ ràng."
    ans = f"Tổng quan tuyển sinh của {name} năm {year if year else 'hiện tại'}: {overview} {quota_text}".strip()

    items: list[QAItem] = []
    for alias in aliases:
        for q in variants(
            f"{alias} năm nay tuyển sinh như thế nào?",
            f"Cho mình thông tin tuyển sinh của {alias}.",
            f"Tổng quan đề án tuyển sinh của {alias} là gì?",
            f"{alias} có gì đáng chú ý trong tuyển sinh năm {year if year else 'nay'}?",
        ):
            items.append(qa_item(q, ans, "admission_overview", code, name, year, "complete" if overview else "partial", 0.9, ["overview", "quota"]))
    return items


def qa_methods(data: dict[str, Any], code: str, name: str, aliases: list[str]) -> list[QAItem]:
    year = data.get("admission_year")
    methods = data.get("admission_methods") or []
    items: list[QAItem] = []

    if not methods:
        for alias in aliases:
            items.append(
                qa_item(
                    f"{alias} có những phương thức xét tuyển nào?",
                    fallback_missing_message("phương thức xét tuyển", name, year),
                    "admission_methods",
                    code,
                    name,
                    year,
                    "missing",
                    0.2,
                    ["methods", "missing"],
                )
            )
        return items

    method_names = [compact_text(m.get("method_name")) for m in methods if compact_text(m.get("method_name"))]
    method_summary = build_method_summary(methods)
    method_answer = "Các phương thức xét tuyển gồm:\n" + "\n".join(f"- {m}" for m in method_names)

    for alias in aliases:
        for q in variants(
            f"{alias} có những phương thức xét tuyển nào?",
            f"Các diện xét tuyển vào {alias} là gì?",
            f"Năm {year if year else 'nay'}, {alias} tuyển theo phương thức nào?",
        ):
            items.append(qa_item(q, method_answer, "admission_methods", code, name, year, "complete", 0.95, ["methods"]))

    for m in methods:
        m_name = compact_text(m.get("method_name"))
        if not m_name:
            continue
        m_desc = compact_text(m.get("description"))
        m_eligibility = compact_text(m.get("eligibility"))
        m_rules = compact_text(m.get("rules"))
        answer = " ".join(
            p
            for p in [
                f"Phương thức {m_name}.",
                f"Mô tả: {m_desc}" if m_desc else "",
                f"Đối tượng: {m_eligibility}" if m_eligibility else "",
                f"Quy chế: {m_rules}" if m_rules else "",
            ]
            if p
        )
        for alias in aliases:
            for q in variants(
                f"Điều kiện của phương thức {m_name} tại {alias} là gì?",
                f"Quy chế xét tuyển theo {m_name} của {alias} ra sao?",
                f"{alias} yêu cầu gì ở phương thức {m_name}?",
            ):
                items.append(qa_item(q, answer, "method_detail", code, name, year, "complete" if answer else "partial", 0.88, ["methods", "rules", "eligibility"]))

    # Global summary for method descriptions
    if method_summary:
        for alias in aliases:
            items.append(
                qa_item(
                    f"Mô tả ngắn gọn các phương thức xét tuyển của {alias}.",
                    "Tóm tắt các phương thức:\n" + method_summary,
                    "methods_summary",
                    code,
                    name,
                    year,
                    "complete",
                    0.9,
                    ["methods", "summary"],
                )
            )
    return items


def qa_programs(data: dict[str, Any], code: str, name: str, aliases: list[str], max_programs_per_school: int) -> list[QAItem]:
    year = data.get("admission_year")
    methods = data.get("admission_methods") or []
    items: list[QAItem] = []
    programs, program_to_methods = build_program_list(methods)

    unique_program_names: list[str] = []
    seen_names: set[str] = set()
    for p in programs:
        p_name = p["program_name"]
        if p_name and p_name not in seen_names:
            seen_names.add(p_name)
            unique_program_names.append(p_name)

    # Full list intent
    if unique_program_names:
        full_list = "; ".join(unique_program_names)
        ans = f"{name} hiện có các ngành trong dữ liệu: {full_list}."
        for alias in aliases:
            for q in variants(
                f"{alias} có những ngành nào?",
                f"Danh sách ngành của {alias} là gì?",
                f"{alias} đang tuyển các ngành nào?",
                f"Cho mình xem toàn bộ ngành của {alias}.",
            ):
                items.append(qa_item(q, ans, "program_list", code, name, year, "complete", 0.95, ["program", "list"]))
    else:
        for alias in aliases:
            items.append(
                qa_item(
                    f"{alias} có những ngành nào?",
                    fallback_missing_message("ngành đào tạo", name, year),
                    "program_list",
                    code,
                    name,
                    year,
                    "missing",
                    0.2,
                    ["program", "missing"],
                )
            )

    # Per program exhaustive QA
    seen_program_keys: set[tuple[str, str]] = set()
    count = 0
    for p in programs:
        p_name = p["program_name"]
        p_code = p["program_code"]
        key = (p_name, p_code)
        if not p_name or key in seen_program_keys:
            continue
        seen_program_keys.add(key)

        groups = p["subject_groups"] or []
        groups_text = ", ".join(groups) if groups else "chưa có dữ liệu tổ hợp môn"
        p_type = p["program_type"] or "chưa rõ"
        m_list = ", ".join(program_to_methods.get(p_name, [])) or "chưa rõ"
        base_answer = (
            f"Ngành {p_name} (mã {p_code if p_code else 'chưa rõ'}) tại {name}. "
            f"Loại chương trình: {p_type}. Tổ hợp môn: {groups_text}. "
            f"Phương thức liên quan: {m_list}."
        )
        status = "complete" if groups else "partial"
        conf = 0.9 if groups else 0.65

        for alias in aliases:
            for q in variants(
                f"Ngành {p_name} của {alias} xét tuyển như thế nào?",
                f"{alias} tuyển ngành {p_name} theo phương thức nào?",
                f"Thông tin xét tuyển ngành {p_name} tại {alias}.",
                f"Ngành {p_name} ở {alias} có tổ hợp gì?",
            ):
                items.append(qa_item(q, base_answer, "program_detail", code, name, year, status, conf, ["program", "subject_groups", "program_type"]))

        if not groups:
            for alias in aliases:
                items.append(
                    qa_item(
                        f"Tổ hợp môn ngành {p_name} của {alias} là gì?",
                        f"Xin lỗi, hiện tại tổ hợp môn cho ngành {p_name} của {name} chưa được cung cấp.",
                        "subject_group_missing",
                        code,
                        name,
                        year,
                        "missing",
                        0.3,
                        ["program", "missing", "subject_groups"],
                    )
                )

        count += 1
        if count >= max_programs_per_school:
            break
    return items


def qa_cutoff(data: dict[str, Any], code: str, name: str, aliases: list[str]) -> list[QAItem]:
    year = data.get("admission_year")
    items: list[QAItem] = []

    if code in CUTOFF_MISSING_CODES:
        for alias in aliases:
            for q in variants(
                f"Điểm chuẩn của {alias} năm {year if year else 'hiện tại'} là bao nhiêu?",
                f"{alias} năm nay lấy bao nhiêu điểm?",
                f"Điểm trúng tuyển của {alias} đã có chưa?",
            ):
                items.append(qa_item(q, fallback_missing_message("điểm chuẩn", name, year), "cutoff_missing_known", code, name, year, "missing", 0.2, ["cutoff", "missing"]))
        return items

    cutoff = data.get("cutoff_scores") or {}
    methods = cutoff.get("methods") or []
    found = False
    for method in methods:
        m_name = compact_text(method.get("method_name"))
        cutoff_year = method.get("year") or cutoff.get("year") or year
        for entry in method.get("entries") or []:
            p_name = compact_text(entry.get("program_name"))
            score = entry.get("score")
            if not p_name or score in (None, ""):
                continue
            found = True
            ans = (
                f"Theo dữ liệu hiện có, điểm chuẩn ngành {p_name} của {name} "
                f"({m_name if m_name else 'phương thức hiện có'}) là {score} cho năm {cutoff_year}."
            )
            for alias in aliases:
                for q in variants(
                    f"Điểm chuẩn ngành {p_name} của {alias} là bao nhiêu?",
                    f"Ngành {p_name} ở {alias} lấy bao nhiêu điểm?",
                    f"Điểm vào ngành {p_name} của {alias} năm {cutoff_year} là bao nhiêu?",
                ):
                    items.append(qa_item(q, ans, "cutoff_score", code, name, year, "complete", 0.95, ["cutoff", "structured"]))

    if found:
        return items

    cutoff_text = compact_text(data.get("cutoff_scores_text"))
    if cutoff_text:
        for alias in aliases:
            for q in variants(
                f"Điểm chuẩn của {alias} có thông tin gì?",
                f"{alias} đã có công bố điểm chuẩn chi tiết chưa?",
            ):
                items.append(qa_item(q, f"Thông tin điểm chuẩn hiện có ở dạng mô tả: {cutoff_text}", "cutoff_text_only", code, name, year, "partial", 0.6, ["cutoff", "raw_text"]))
    else:
        for alias in aliases:
            items.append(
                qa_item(
                    f"Điểm chuẩn của {alias} năm {year if year else 'hiện tại'} là bao nhiêu?",
                    fallback_missing_message("điểm chuẩn", name, year),
                    "cutoff_missing",
                    code,
                    name,
                    year,
                    "missing",
                    0.2,
                    ["cutoff", "missing"],
                )
            )
    return items


def qa_tuition_timeline(data: dict[str, Any], code: str, name: str, aliases: list[str]) -> list[QAItem]:
    year = data.get("admission_year")
    tuition = compact_text(data.get("tuition_text"))
    timeline = compact_text(data.get("timeline_text"))
    items: list[QAItem] = []

    for alias in aliases:
        for q in variants(
            f"Học phí của {alias} năm {year if year else 'hiện tại'} như thế nào?",
            f"Mức học phí ở {alias} là bao nhiêu?",
            f"Học ở {alias} tốn khoảng bao nhiêu tiền?",
        ):
            ans = f"Thông tin học phí: {tuition}" if tuition else fallback_missing_message("học phí", name, year)
            items.append(qa_item(q, ans, "tuition", code, name, year, "complete" if tuition else "missing", 0.85 if tuition else 0.2, ["tuition"]))

    for alias in aliases:
        for q in variants(
            f"Lịch tuyển sinh của {alias} năm nay như thế nào?",
            f"Mốc thời gian và hồ sơ xét tuyển của {alias} là gì?",
            f"Khi nào nộp hồ sơ vào {alias}?",
        ):
            ans = f"Thông tin thời gian và hồ sơ: {timeline}" if timeline else fallback_missing_message("thời gian và hồ sơ", name, year)
            items.append(qa_item(q, ans, "timeline", code, name, year, "complete" if timeline else "missing", 0.85 if timeline else 0.2, ["timeline"]))

    return items


def qa_university_profile(data: dict[str, Any], code: str, name: str, aliases: list[str]) -> list[QAItem]:
    year = data.get("admission_year")
    uni = data.get("university") or {}
    short_name = compact_text(uni.get("short_name"))
    location = ", ".join(uni.get("location") or [])
    address = compact_text(uni.get("address"))
    website = compact_text(uni.get("website"))
    utype = compact_text(uni.get("type"))
    answer = (
        f"Thông tin trường {name}: mã trường {code}; viết tắt {short_name if short_name else 'chưa rõ'}; "
        f"khu vực {location if location else 'chưa rõ'}; địa chỉ {address if address else 'chưa rõ'}; "
        f"website {website if website else 'chưa rõ'}; loại trường {utype if utype else 'chưa rõ'}."
    )
    items: list[QAItem] = []
    for alias in aliases:
        for q in variants(
            f"Thông tin cơ bản của {alias} là gì?",
            f"{alias} ở đâu, mã trường là gì?",
            f"Cho mình thông tin profile của {alias}.",
        ):
            items.append(qa_item(q, answer, "university_profile", code, name, year, "complete", 0.9, ["university", "profile"]))
    return items


def qa_cross_coverage(data: dict[str, Any], code: str, name: str, aliases: list[str]) -> list[QAItem]:
    year = data.get("admission_year")
    methods = data.get("admission_methods") or []
    programs, program_to_methods = build_program_list(methods)
    items: list[QAItem] = []

    # Program x method relation coverage
    for p_name, m_names in list(program_to_methods.items())[:2000]:
        methods_text = ", ".join(m_names) if m_names else "chưa rõ"
        for alias in aliases[:2]:
            items.append(
                qa_item(
                    f"Ngành {p_name} của {alias} có trong những phương thức nào?",
                    f"Ngành {p_name} của {name} hiện xuất hiện trong các phương thức: {methods_text}.",
                    "program_method_mapping",
                    code,
                    name,
                    year,
                    "complete" if m_names else "partial",
                    0.82,
                    ["program", "method", "mapping"],
                )
            )

    # Method x program count
    for m in methods:
        m_name = compact_text(m.get("method_name"))
        count = len(m.get("programs") or [])
        if not m_name:
            continue
        for alias in aliases[:2]:
            items.append(
                qa_item(
                    f"Phương thức {m_name} của {alias} có bao nhiêu ngành?",
                    f"Theo dữ liệu hiện có, phương thức {m_name} của {name} có {count} ngành/chương trình.",
                    "method_program_count",
                    code,
                    name,
                    year,
                    "complete",
                    0.86,
                    ["method", "program", "count"],
                )
            )
    return items


def generate_for_school(data: dict[str, Any], max_programs_per_school: int) -> list[QAItem]:
    uni = data.get("university") or {}
    code = compact_text(uni.get("code")).upper() or "UNK"
    name = compact_text(uni.get("name")) or "Trường chưa rõ tên"
    short_name = compact_text(uni.get("short_name"))
    aliases = school_aliases(name, short_name, code)

    items: list[QAItem] = []
    items.extend(qa_university_profile(data, code, name, aliases))
    items.extend(qa_overview(data, code, name, aliases))
    items.extend(qa_methods(data, code, name, aliases))
    items.extend(qa_programs(data, code, name, aliases, max_programs_per_school=max_programs_per_school))
    items.extend(qa_cutoff(data, code, name, aliases))
    items.extend(qa_tuition_timeline(data, code, name, aliases))
    items.extend(qa_cross_coverage(data, code, name, aliases))
    return unique_qa(items)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, items: list[QAItem]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate exhaustive Q&A dataset from crawled admission JSON files")
    parser.add_argument("--data-dir", default="../data", help="Path to source JSON directory")
    parser.add_argument("--output", default="./storage/qa_dataset.jsonl", help="Output JSONL path")
    parser.add_argument(
        "--max-programs-per-school",
        type=int,
        default=100000,
        help="Max number of unique program-level QA per school",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    files = sorted(data_dir.glob("*.json")) if data_dir.exists() else []
    if not files:
        raise SystemExit(f"No JSON files found in {data_dir}")

    all_items: list[QAItem] = []
    for i, file_path in enumerate(files, start=1):
        data = load_json(file_path)
        school_items = generate_for_school(data, max_programs_per_school=args.max_programs_per_school)
        all_items.extend(school_items)
        if i % 20 == 0:
            print(f"[gen-qa] processed {i}/{len(files)} schools, total QA={len(all_items)}")

    all_items = unique_qa(all_items)
    output = Path(args.output)
    write_jsonl(output, all_items)

    print(f"Generated {len(all_items)} QA pairs from {len(files)} schools")
    print(f"Output: {output.resolve()}")


if __name__ == "__main__":
    main()
