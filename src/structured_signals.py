import calendar
import re
from datetime import date, timedelta


MONTH_LOOKUP = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}

MONTH_TOKEN = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
    r"jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|"
    r"nov(?:ember)?|dec(?:ember)?)"
)

MONTH_YEAR_RANGE_PATTERN = re.compile(
    rf"({MONTH_TOKEN}\s+\d{{4}})\s*(?:-|–|to)\s*"
    rf"({MONTH_TOKEN}\s+\d{{4}}|present|current|ongoing|today)",
    re.IGNORECASE,
)

YEAR_RANGE_PATTERN = re.compile(
    r"((?:19|20)\d{2})\s*(?:-|–|to)\s*((?:19|20)\d{2}|present|current|ongoing|today)",
    re.IGNORECASE,
)

EDUCATION_PATTERNS = {
    "PhD": [
        r"\bph\.?d\b",
        r"\bdoctorate\b",
        r"\bdoctoral\b",
    ],
    "Masters": [
        r"\bmaster(?:'s)?\b",
        r"\bm\.?s\b",
        r"\bm\.tech\b",
        r"\bmtech\b",
        r"\bmba\b",
        r"\bmca\b",
    ],
    "Bachelors": [
        r"\bbachelor(?:'s)?\b",
        r"\bb\.?s\b",
        r"\bb\.tech\b",
        r"\bbtech\b",
        r"\bb\.?e\b",
        r"\bbe\b",
        r"\bbca\b",
    ],
    "Diploma": [
        r"\bdiploma\b",
        r"\bassociate\b",
    ],
}

EDUCATION_ORDER = ["PhD", "Masters", "Bachelors", "Diploma"]

CGPA_WITH_SCALE_PATTERN = re.compile(
    r"(?:cgpa|gpa)\s*[:=]?\s*(\d{1,2}(?:\.\d+)?)\s*(?:/|out\s+of)\s*(\d{1,2}(?:\.\d+)?)",
    re.IGNORECASE,
)

CGPA_PLAIN_PATTERN = re.compile(
    r"(?:cgpa|gpa)\s*[:=]?\s*(\d(?:\.\d+)?)",
    re.IGNORECASE,
)


def _parse_date_token(token, is_end=False):
    normalized = token.strip().lower().replace(".", "")
    if normalized in {"present", "current", "ongoing", "today"}:
        return date.today()

    month_year_match = re.fullmatch(rf"({MONTH_TOKEN})\s+(\d{{4}})", normalized)
    if month_year_match:
        month_label = month_year_match.group(1)[:3]
        month = MONTH_LOOKUP[month_label]
        year = int(month_year_match.group(2))
        if is_end:
            last_day = calendar.monthrange(year, month)[1]
            return date(year, month, last_day)
        return date(year, month, 1)

    year_match = re.fullmatch(r"((?:19|20)\d{2})", normalized)
    if year_match:
        year = int(year_match.group(1))
        if is_end:
            return date(year, 12, 31)
        return date(year, 1, 1)

    return None


def _merge_intervals(intervals):
    if not intervals:
        return []

    sorted_intervals = sorted(intervals, key=lambda interval: interval[0])
    merged = [sorted_intervals[0]]

    for start, end in sorted_intervals[1:]:
        current_start, current_end = merged[-1]
        if start <= current_end + timedelta(days=1):
            merged[-1] = (current_start, max(current_end, end))
        else:
            merged.append((start, end))

    return merged


def _intervals_to_years(intervals):
    merged_intervals = _merge_intervals(intervals)

    total_days = 0
    for start_date, end_date in merged_intervals:
        total_days += (end_date - start_date).days + 1

    total_years = round(total_days / 365.25, 2) if total_days > 0 else 0.0
    return total_years, merged_intervals


def _collect_experience_intervals(experience_text):
    intervals_with_context = []
    warnings = []

    for pattern in [MONTH_YEAR_RANGE_PATTERN, YEAR_RANGE_PATTERN]:
        for match in pattern.finditer(experience_text):
            start_token = match.group(1)
            end_token = match.group(2)

            start_date = _parse_date_token(start_token, is_end=False)
            end_date = _parse_date_token(end_token, is_end=True)

            if not start_date or not end_date:
                warnings.append(f"Unparsed date range: {start_token} - {end_token}")
                continue

            if end_date < start_date:
                warnings.append(f"Invalid date range: {start_token} - {end_token}")
                continue

            context_start = max(0, match.start() - 180)
            context_end = min(len(experience_text), match.end() + 180)
            context = experience_text[context_start:context_end].lower()

            intervals_with_context.append(
                {
                    "start": start_date,
                    "end": end_date,
                    "context": context,
                }
            )

    # Deduplicate exact interval duplicates gathered from overlapping regex patterns.
    deduped = {}
    for entry in intervals_with_context:
        key = (entry["start"], entry["end"])
        if key not in deduped:
            deduped[key] = entry

    return list(deduped.values()), warnings


def _context_matches_relevant_terms(context, relevant_terms):
    for term in relevant_terms:
        normalized_term = str(term).strip().lower()
        if not normalized_term:
            continue

        if re.search(r"\b" + re.escape(normalized_term) + r"\b", context):
            return True

    return False


def extract_total_years_experience(experience_text):
    intervals_with_context, warnings = _collect_experience_intervals(experience_text)
    intervals = [(entry["start"], entry["end"]) for entry in intervals_with_context]
    total_years, merged_intervals = _intervals_to_years(intervals)

    if not merged_intervals:
        warnings.append("No valid experience date ranges were detected")

    return {
        "total_years_experience": total_years,
        "interval_count": len(merged_intervals),
        "extraction_warnings": warnings,
    }


def extract_relevant_years_experience(experience_text, relevant_terms):
    intervals_with_context, warnings = _collect_experience_intervals(experience_text)

    total_intervals = [(entry["start"], entry["end"]) for entry in intervals_with_context]
    total_years, _ = _intervals_to_years(total_intervals)

    active_terms = [term for term in (relevant_terms or []) if str(term).strip()]
    if not active_terms:
        warnings.append("No relevant terms provided; falling back to total experience")
        relevant_intervals = total_intervals
    else:
        relevant_intervals = []
        for entry in intervals_with_context:
            if _context_matches_relevant_terms(entry["context"], active_terms):
                relevant_intervals.append((entry["start"], entry["end"]))

    relevant_years, merged_relevant = _intervals_to_years(relevant_intervals)

    if total_intervals and not merged_relevant:
        warnings.append(
            "No experience intervals matched the relevant-term context; relevant years set to 0"
        )

    if not total_intervals:
        warnings.append("No valid experience date ranges were detected")

    return {
        "relevant_years_experience": relevant_years,
        "total_years_experience": total_years,
        "relevant_interval_count": len(merged_relevant),
        "interval_count": len(total_intervals),
        "extraction_warnings": warnings,
    }


def normalize_education_levels(education_text):
    normalized = education_text.lower()
    education_levels = []

    for level in EDUCATION_ORDER:
        patterns = EDUCATION_PATTERNS[level]
        if any(re.search(pattern, normalized) for pattern in patterns):
            education_levels.append(level)

    highest_education = education_levels[0] if education_levels else "Unknown"
    if not education_levels:
        education_levels = ["Unknown"]

    return {
        "education_levels": education_levels,
        "highest_education": highest_education,
    }


def _normalize_to_ten_scale(value, scale):
    if scale is None:
        # Most resumes use CGPA on either 10 or 4. For unlabeled values <= 4, assume /4.
        detected_scale = 4.0 if value <= 4.0 else 10.0
    else:
        detected_scale = float(scale)

    if detected_scale <= 0:
        return None

    normalized = (float(value) / detected_scale) * 10.0
    if normalized < 0:
        return None

    return round(normalized, 2)


def extract_cgpa(education_text):
    candidates = []
    warnings = []

    for match in CGPA_WITH_SCALE_PATTERN.finditer(education_text):
        value = float(match.group(1))
        scale = float(match.group(2))
        normalized = _normalize_to_ten_scale(value, scale)
        if normalized is None:
            continue
        candidates.append(
            {
                "normalized": normalized,
                "raw_value": value,
                "scale": scale,
            }
        )

    # If explicit scale is missing, still capture labeled GPA/CGPA values.
    for match in CGPA_PLAIN_PATTERN.finditer(education_text):
        value = float(match.group(1))
        normalized = _normalize_to_ten_scale(value, None)
        if normalized is None:
            continue
        candidates.append(
            {
                "normalized": normalized,
                "raw_value": value,
                "scale": None,
            }
        )

    if not candidates:
        warnings.append("No CGPA/GPA value detected in education section")
        return {
            "cgpa_value": None,
            "cgpa_raw": None,
            "cgpa_scale": None,
            "extraction_warnings": warnings,
        }

    # Pick best academic performance if multiple degree-level values are present.
    best = max(candidates, key=lambda item: item["normalized"])
    return {
        "cgpa_value": best["normalized"],
        "cgpa_raw": best["raw_value"],
        "cgpa_scale": best["scale"],
        "extraction_warnings": warnings,
    }