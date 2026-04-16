import re

import pdfplumber

from text_cleaner import clean_text


SECTION_PATTERNS = {
    "skills": [
        r"^skills?$",
        r"^technical skills?$",
        r"^core skills?$",
        r"^competencies$",
    ],
    "experience": [
        r"^experience$",
        r"^work experience$",
        r"^professional experience$",
        r"^employment history$",
    ],
    "education": [
        r"^education$",
        r"^academic background$",
        r"^qualifications?$",
    ],
}


def extract_text_from_pdf(pdf_path):
    full_text = []

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                full_text.append(text)

    return "\n".join(full_text)


def _normalize_heading(line):
    return re.sub(r"[^a-z\s]", "", line.lower()).strip()


def _match_section_heading(line):
    normalized = _normalize_heading(line)
    for section_name, patterns in SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.match(pattern, normalized):
                return section_name
    return None


def split_resume_sections(text):
    section_buckets = {
        "skills": [],
        "experience": [],
        "education": [],
        "other": [],
    }

    current_section = "other"
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        matched_section = _match_section_heading(line)
        if matched_section:
            current_section = matched_section
            continue

        section_buckets[current_section].append(line)

    return {key: "\n".join(value).strip() for key, value in section_buckets.items()}


def process_job_description(jd_text):
    return {
        "raw_text": jd_text,
        "clean_text": clean_text(jd_text),
    }


def process_resume_pdf(pdf_path):
    raw_text = extract_text_from_pdf(pdf_path)
    sections = split_resume_sections(raw_text)

    clean_sections = {
        section_name: clean_text(section_text) if section_text else ""
        for section_name, section_text in sections.items()
    }

    return {
        "raw_text": raw_text,
        "clean_text": clean_text(raw_text),
        "sections": sections,
        "clean_sections": clean_sections,
    }