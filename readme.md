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

## How the App Works

- The frontend in `static/` collects one job description and multiple resume PDFs.
- The browser sends data to the Flask backend at `POST /analyze`.
- The backend processes the job description once (cleaning + embedding + TF-IDF setup).
- Each resume is parsed, cleaned, sectioned (skills/experience/education), embedded, and compared with the job description.
- The final score per resume uses:

```text
final_score = 0.5 * embedding_similarity + 0.3 * tfidf_similarity + 0.2 * skill_overlap_score
```

- The backend returns ranked candidates (highest score first), with matched and missing skills and an explanation string.

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
		"matched_skills": ["python", "sql"],
		"missing_skills": ["docker"],
		"explanation": "High semantic alignment with the job description, strong keyword similarity (0.82), and skill coverage (0.75)."
	}
]
```

## Notes

- The app works best with text-based PDF resumes. Scanned PDFs may not extract correctly.
- The embedding model is `all-MiniLM-L6-v2` from `sentence-transformers`.
- You can optionally send `top_n` to return only the highest-ranked resumes.
- The app saves uploaded resumes temporarily in `Data/Resumes/` when running locally.
- Docker is optional, but it provides the most consistent environment.
