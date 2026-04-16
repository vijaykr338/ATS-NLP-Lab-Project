import os
from uuid import uuid4

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from embedding_model import get_embedding_model
from matcher import (
    build_rank_reason,
    compute_embedding_similarity,
    compute_final_score,
    compute_skill_overlap,
    compute_tfidf_similarities,
)
from parser import process_job_description, process_resume_pdf
from skill_extractor import extract_skills, extract_skills_regex

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))

UPLOAD_FOLDER = "Data/Resumes"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def _extract_skill_set(clean_text_value):
    return extract_skills(clean_text_value) | extract_skills_regex(clean_text_value)


def analyze_multiple_resumes(jd_text, resume_files, top_n=None):
    jd_processed = process_job_description(jd_text)
    jd_clean_text = jd_processed["clean_text"]
    jd_skills = _extract_skill_set(jd_clean_text)

    resume_records = []
    for resume_file in resume_files:
        if not resume_file or not resume_file.filename:
            continue

        safe_name = secure_filename(resume_file.filename)
        if not safe_name.lower().endswith(".pdf"):
            continue

        resume_id = f"{uuid4().hex}_{safe_name}"
        resume_path = os.path.join(UPLOAD_FOLDER, resume_id)
        resume_file.save(resume_path)

        parsed_resume = process_resume_pdf(resume_path)

        # Skill-heavy section is prioritized, then fallback to whole cleaned resume.
        skill_context = " ".join(
            [
                parsed_resume["clean_sections"].get("skills", ""),
                parsed_resume["clean_sections"].get("experience", ""),
                parsed_resume["clean_text"],
            ]
        )

        resume_records.append(
            {
                "resume_id": safe_name,
                "clean_text": parsed_resume["clean_text"],
                "resume_skills": _extract_skill_set(skill_context),
            }
        )

    if not resume_records:
        return []

    embedding_model = get_embedding_model()

    jd_embedding = embedding_model.encode([jd_clean_text])[0]
    resume_clean_texts = [record["clean_text"] for record in resume_records]
    resume_embeddings = embedding_model.encode(resume_clean_texts)
    tfidf_scores = compute_tfidf_similarities(jd_clean_text, resume_clean_texts)

    ranked_results = []
    for index, record in enumerate(resume_records):
        embedding_similarity = compute_embedding_similarity(
            resume_embeddings[index], jd_embedding
        )
        tfidf_similarity = float(tfidf_scores[index])
        skill_overlap_score, matched_skills, missing_skills = compute_skill_overlap(
            record["resume_skills"], jd_skills
        )

        final_score = compute_final_score(
            embedding_similarity,
            tfidf_similarity,
            skill_overlap_score,
        )

        ranked_results.append(
            {
                "resume_id": record["resume_id"],
                "score": round(final_score, 4),
                "embedding_similarity": round(embedding_similarity, 4),
                "tfidf_similarity": round(tfidf_similarity, 4),
                "skill_overlap_score": round(skill_overlap_score, 4),
                "matched_skills": matched_skills,
                "missing_skills": missing_skills,
                "explanation": build_rank_reason(
                    embedding_similarity,
                    tfidf_similarity,
                    skill_overlap_score,
                ),
            }
        )

    ranked_results.sort(key=lambda item: item["score"], reverse=True)

    for rank, item in enumerate(ranked_results, start=1):
        item["rank"] = rank

    if top_n and top_n > 0:
        return ranked_results[:top_n]

    return ranked_results

@app.route("/analyze", methods=["POST"])
def analyze_resume():
    jd_text = request.form.get("job_description")
    resume_files = request.files.getlist("resumes")

    # Backward-compatible fallback for old single-file clients.
    if not resume_files:
        single_resume = request.files.get("resume")
        if single_resume:
            resume_files = [single_resume]

    top_n = request.form.get("top_n", type=int)

    if not jd_text or not resume_files:
        return jsonify({"error": "Job description and at least one resume are required"}), 400

    try:
        ranked_results = analyze_multiple_resumes(jd_text, resume_files, top_n=top_n)
    except Exception as exc:
        return jsonify({"error": f"Failed to analyze resumes: {exc}"}), 500

    return jsonify(ranked_results)

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)