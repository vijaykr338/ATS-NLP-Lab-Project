# Installation Instructions

This project can be run either locally with Python or through Docker.

## Prerequisites

- Python 3.10 or newer
- `pip`
- Git
- Optional: Docker

## Local Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd ats-resume-analyzer-main
```

### 2. Create and activate a virtual environment

#### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Install the spaCy language model

The app requires the English spaCy model used by `src/text_cleaner.py`.

```bash
python -m spacy download en_core_web_sm
```

### 5. Run the application

From the project root:

```bash
python src/app.py
```

Open the app in your browser:

```text
http://localhost:5000
```

## Docker Installation

### 1. Build the image

```bash
docker build -t ats-system .
```

### 2. Run the container

```bash
docker run -p 5000:5000 ats-system
```

Open the app in your browser:

```text
http://localhost:5000
```

## System Overview

This project is a hybrid ATS-style ranking engine for one job description and multiple resume PDFs.

It combines four major ideas:

1. Semantic similarity using sentence embeddings
2. Lexical similarity using TF-IDF
3. Rule-based skill overlap matching
4. Deterministic hard-constraint gating (`g_hard`) using must-have skills, minimum relevant years, and minimum CGPA

The browser UI uploads data to `POST /analyze`, and the backend returns ranked JSON results.

## End-to-End Request Flow

1. User enters job description and uploads multiple resume PDFs.
2. Frontend sends multipart form data to Flask (`/analyze`).
3. Backend processes JD once:
	- cleans text
	- extracts JD skills
	- extracts hard constraints (must-have skills + minimum years)
4. Backend processes each resume:
	- extracts PDF text
	- splits sections (`skills`, `experience`, `education`, `other`)
	- cleans section/full text
	- extracts resume skills
	- computes structured signals (relevant years, total years, education levels)
	- evaluates hard constraints (`g_hard`)
5. Based on `constraint_mode`:
	- `exclude`: remove failed candidates before expensive embedding scoring
	- `penalize`: keep failed candidates, then force score to `0.0`
6. For candidates in scoring stage, backend computes:
	- embedding similarity
	- TF-IDF similarity
	- skill overlap score
7. Combines feature scores, sorts descending, assigns rank, optionally applies top-N cutoff.
8. Returns JSON payload consumed by the frontend.

## Detailed Parsing Approach

### 1) PDF Text Extraction

- Uses `pdfplumber` page-by-page extraction.
- Non-empty page text is concatenated with newlines.
- This works best on text-based PDFs; scanned image PDFs are a known limitation.

### 2) Resume Section Detection

- The parser normalizes each candidate heading line (lowercase + remove non-letter characters).
- It detects section transitions via regex patterns for headings like:
  - `skills`, `technical skills`, `core skills`
  - `experience`, `work experience`, `professional experience`
  - `education`, `academic background`, `qualifications`
- Lines are bucketed under the currently active section.
- Any unmatched content is stored under `other`.

### 3) Text Cleaning

- Uses spaCy (`en_core_web_sm`) to normalize text:
  - lowercase
  - stopword removal
  - punctuation removal
  - lemmatization
- Cleaned text is produced for both full document and section-level text.

### 4) Relevant Experience Computation (Important)

Relevant years are not the same as total years.

The algorithm:

1. Parse date intervals from the `experience` section using patterns such as:
	- `Jan 2020 - Mar 2023`
	- `2020 - 2023`
	- `2019 - Present`
2. Normalize each boundary token to concrete dates.
3. For each interval, capture a local context window around the date range.
4. Build relevant-term set:
	- use JD must-have skills when available
	- otherwise fallback to JD skill set
5. Mark intervals as relevant only when local context contains relevant terms.
6. Merge overlapping relevant intervals and sum duration in days.
7. Convert days to years (`days / 365.25`) and round.

Outputs:

- `relevant_years_experience`
- `total_years_experience`
- warnings when date extraction is weak/ambiguous

### 5) Education Normalization

Education section text is normalized into levels using pattern dictionaries:

- `PhD`
- `Masters`
- `Bachelors`
- `Diploma`
- fallback `Unknown`

The parser returns detected levels and `highest_education`.

## Hard Constraints (Rules-First Layer)

Hard constraints are deterministic and applied before final ranking logic.

### Constraint Extraction from JD

1. Requirement cue segmentation:
	- looks for requirement phrases like `must`, `required`, `mandatory`, `minimum`, `at least`
2. Must-have skill extraction:
	- extracts skills only from requirement segments
3. Minimum years extraction:
	- regex patterns for `3+ years`, `minimum 3 years`, `at least 3 years`, etc.
4. Minimum CGPA extraction:
	- regex patterns for `minimum cgpa 8.0`, `gpa 3.2/4`, `cgpa 7.5/10`, etc.

### Gate Evaluation

Each resume gets a binary gate variable:

```text
g_hard ∈ {0, 1}
```

`g_hard = 0` when any hard constraint fails:

- missing must-have skills
- relevant years below required threshold
- CGPA below required threshold or missing CGPA evidence when CGPA is required

### Constraint Modes

- `exclude`: remove candidates with `g_hard = 0` before ranking
- `penalize`: keep candidates but set final score to `0.0` and include failure reasons

Set mode through form/API field `constraint_mode`.

## Scoring Features and Formula

For each scored resume, the backend computes:

1. `embedding_similarity`
	- cosine similarity between resume and JD embeddings
2. `tfidf_similarity`
	- cosine similarity between resume and JD TF-IDF vectors
3. `skill_overlap_score`
	- `|matched_skills| / |required_skills|`

Final score:

```text
final_score = 0.5 * embedding_similarity + 0.3 * tfidf_similarity + 0.2 * skill_overlap_score
```

Candidates are sorted by `score` descending and assigned `rank` starting at 1.

## Ranking Output Semantics

Each candidate result contains:

- Identity: `resume_id`, `rank`
- Scores: `score`, `embedding_similarity`, `tfidf_similarity`, `skill_overlap_score`
- Constraints: `g_hard`, `failed_constraints`, `hard_constraint_reason_codes`
- Structured signals: `relevant_years_experience`, `total_years_experience`, `education_levels`, `highest_education`
- Explainability: `matched_skills`, `missing_skills`, `explanation`

## API Response Shape (`POST /analyze`)

```json
[
	{
		"rank": 1,
		"resume_id": "candidate_a.pdf",
		"score": 0.87,
		"embedding_similarity": 0.91,
		"tfidf_similarity": 0.82,
		"skill_overlap_score": 0.75,
		"g_hard": 1,
		"failed_constraints": [],
		"hard_constraint_reason_codes": [],
		"relevant_years_experience": 4.2,
		"total_years_experience": 5.4,
		"cgpa_value": 8.7,
		"education_levels": ["Masters", "Bachelors"],
		"highest_education": "Masters",
		"matched_skills": ["python", "sql"],
		"missing_skills": ["docker"],
		"explanation": "High semantic alignment with the job description, strong keyword similarity (0.82), and skill coverage (0.75)."
	}
]
```

## Frontend Behavior Summary

- Form fields include:
	- `job_description`
	- `resumes` (multi-file)
	- `top_n` (optional)
	- `constraint_mode` (`exclude` or `penalize`)
- On submit:
	- show loading state
	- call `/analyze`
	- render ranked cards with metrics, eligibility status, and skill evidence

## Design Rationale

This architecture intentionally mixes deterministic logic and statistical similarity:

1. Deterministic rules (`g_hard`) enforce non-negotiable requirements.
2. Statistical ranking (embedding + TF-IDF + skill overlap) differentiates candidates who passed (or are retained in penalize mode).
3. Structured signals improve interpretability and recruiter trust.

## Notes

- The app works best with text-based PDF resumes. Scanned PDFs may not extract correctly.
- The embedding model is `all-MiniLM-L6-v2` from `sentence-transformers`.
- You can optionally send `top_n` to return only the highest-ranked resumes.
- The app saves uploaded resumes temporarily in `Data/Resumes/` when running locally.
- Docker is optional, but it provides the most consistent environment.
