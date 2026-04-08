from flask import Flask, request, jsonify, send_from_directory
import os

from pdf_parser import extract_text_from_pdf
from text_cleaner import clean_text
from skill_extractor import extract_skills, extract_skills_regex
from matcher import compute_match_score
from classifier import ResumeClassifier

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))

classifier = ResumeClassifier()

UPLOAD_FOLDER = "Data/Resumes"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/analyze", methods=["POST"])
def analyze_resume():
    resume_file = request.files.get("resume")
    jd_text = request.form.get("job_description")

    if not resume_file or not jd_text:
        return jsonify({"error": "Resume file and job description are required"}), 400

    resume_path = os.path.join(UPLOAD_FOLDER, resume_file.filename)
    resume_file.save(resume_path)

    # --- Pipeline ---
    resume_text = extract_text_from_pdf(resume_path)
    clean_resume = clean_text(resume_text)
    clean_jd = clean_text(jd_text)

    resume_skills = extract_skills(clean_resume) | extract_skills_regex(clean_resume)
    jd_skills = extract_skills(clean_jd) | extract_skills_regex(clean_jd)

    missing_skills = list(jd_skills - resume_skills)
    matched_skills = list(resume_skills & jd_skills)

    match_score = compute_match_score(
        clean_resume, clean_jd, resume_skills, jd_skills
    )

    category = classifier.predict(clean_resume)

    return jsonify({
        "match_score": match_score,
        "resume_category": category,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills
    })

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)