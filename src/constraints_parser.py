import re

from skill_extractor import extract_skills, extract_skills_regex
from text_cleaner import clean_text


REQUIREMENT_CUE_PATTERN = re.compile(
    r"\b(must|required|mandatory|minimum|min\.?|at least|should have|need to have)\b",
    re.IGNORECASE,
)

MIN_YEARS_PATTERNS = [
    re.compile(
        r"(?:at\s+least|minimum|min\.?)\s*(\d{1,2})\s*\+?\s*(?:years?|yrs?)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience\s+)?(?:required|must|mandatory)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:required|must\s+have|needs?)\s+(?:\w+\s+){0,5}?(\d{1,2})\s*\+?\s*(?:years?|yrs?)",
        re.IGNORECASE,
    ),
]

MIN_CGPA_PATTERNS = [
    re.compile(
        r"(?:minimum|min\.?|at\s+least|required)\s*(?:cgpa|gpa)\s*(?:of\s*)?(\d{1,2}(?:\.\d+)?)\s*(?:/|out\s+of)?\s*(\d{1,2}(?:\.\d+)?)?",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:cgpa|gpa)\s*(?:>=|>|at\s+least|min\.?|minimum|required)?\s*(\d{1,2}(?:\.\d+)?)\s*(?:/|out\s+of)?\s*(\d{1,2}(?:\.\d+)?)?",
        re.IGNORECASE,
    ),
]


def _normalize_to_ten_scale(value, scale):
    if scale is None:
        detected_scale = 4.0 if value <= 4.0 else 10.0
    else:
        detected_scale = float(scale)

    if detected_scale <= 0:
        return None

    return round((float(value) / detected_scale) * 10.0, 2)


def _extract_requirement_segments(jd_text):
    segments = []
    for chunk in re.split(r"[\n.;]", jd_text):
        candidate = chunk.strip()
        if not candidate:
            continue

        if REQUIREMENT_CUE_PATTERN.search(candidate):
            segments.append(candidate)

    return segments


def extract_min_years_required(jd_text):
    matches = []
    for pattern in MIN_YEARS_PATTERNS:
        for result in pattern.findall(jd_text):
            try:
                matches.append(int(result))
            except ValueError:
                continue

    if not matches:
        return None

    # Use the strictest explicitly-stated requirement when multiple values appear.
    return max(matches)


def extract_must_have_skills(jd_text, jd_skills):
    requirement_segments = _extract_requirement_segments(jd_text)
    extracted = set()

    for segment in requirement_segments:
        clean_segment = clean_text(segment)
        extracted |= extract_skills(clean_segment)
        extracted |= extract_skills_regex(clean_segment)

        raw_segment = segment.lower()
        extracted |= extract_skills(raw_segment)
        extracted |= extract_skills_regex(raw_segment)

    # Keep must-have skills bounded to the JD skill universe for consistency.
    return extracted & set(jd_skills)


def extract_min_cgpa_required(jd_text):
    values = []
    for pattern in MIN_CGPA_PATTERNS:
        for match in pattern.findall(jd_text):
            try:
                raw_value = float(match[0])
                raw_scale = float(match[1]) if match[1] else None
            except ValueError:
                continue

            normalized = _normalize_to_ten_scale(raw_value, raw_scale)
            if normalized is not None:
                values.append(normalized)

    if not values:
        return None

    return max(values)


def parse_hard_constraints_from_jd(jd_text, jd_skills):
    must_have_skills = extract_must_have_skills(jd_text, jd_skills)
    min_years_required = extract_min_years_required(jd_text)
    min_cgpa_required = extract_min_cgpa_required(jd_text)

    warnings = []
    if not must_have_skills:
        warnings.append("No explicit must-have skill cues were detected in job description")
    if min_years_required is None:
        warnings.append("No explicit minimum years requirement detected in job description")
    if min_cgpa_required is None:
        warnings.append("No explicit minimum CGPA/GPA requirement detected in job description")

    return {
        "must_have_skills": must_have_skills,
        "min_years_required": min_years_required,
        "min_cgpa_required": min_cgpa_required,
        "parse_warnings": warnings,
    }


def evaluate_hard_constraints(
    resume_skills,
    must_have_skills,
    years_experience,
    min_years_required,
    cgpa_value,
    min_cgpa_required,
):
    failed_constraints = []
    reason_codes = []

    if must_have_skills:
        missing_must_have = sorted(set(must_have_skills) - set(resume_skills))
        if missing_must_have:
            reason_codes.append("missing_must_have_skills")
            failed_constraints.append(
                "Missing must-have skills: " + ", ".join(missing_must_have)
            )

    if min_years_required is not None and years_experience < min_years_required:
        reason_codes.append("below_minimum_years")
        failed_constraints.append(
            f"Requires at least {min_years_required} relevant years; detected {years_experience:.2f}"
        )

    if min_cgpa_required is not None:
        if cgpa_value is None:
            reason_codes.append("missing_cgpa_evidence")
            failed_constraints.append(
                f"Requires minimum CGPA {min_cgpa_required:.2f}/10; no CGPA evidence detected"
            )
        elif cgpa_value < min_cgpa_required:
            reason_codes.append("below_minimum_cgpa")
            failed_constraints.append(
                f"Requires minimum CGPA {min_cgpa_required:.2f}/10; detected {cgpa_value:.2f}/10"
            )

    g_hard = 0 if failed_constraints else 1

    return {
        "g_hard": g_hard,
        "failed_constraints": failed_constraints,
        "reason_codes": reason_codes,
    }