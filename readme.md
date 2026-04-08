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

- The frontend in `static/` collects a PDF resume and a job description.
- The browser sends both to the Flask backend at `POST /analyze`.
- The backend extracts text from the PDF, cleans the text with spaCy, extracts skills, calculates a match score, and predicts a resume category.
- Results are returned as JSON and displayed in the UI.

## Notes

- The app works best with text-based PDF resumes. Scanned PDFs may not extract correctly.
- The classifier uses pre-trained model files stored in `models/`.
- The app saves uploaded resumes temporarily in `Data/Resumes/` when running locally.
- Docker is optional, but it provides the most consistent environment.
