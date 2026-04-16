from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


EMBEDDING_WEIGHT = 0.5
TFIDF_WEIGHT = 0.3
SKILL_WEIGHT = 0.2


def compute_embedding_similarity(resume_embedding, jd_embedding):
    return float(cosine_similarity([resume_embedding], [jd_embedding])[0][0])


def compute_tfidf_similarities(clean_jd_text, clean_resume_texts):
    vectorizer = TfidfVectorizer(max_features=3000, ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform([clean_jd_text] + clean_resume_texts)

    jd_vector = tfidf_matrix[0]
    resume_vectors = tfidf_matrix[1:]

    return cosine_similarity(resume_vectors, jd_vector).flatten().tolist()


def compute_skill_overlap(resume_skills, required_skills):
    if not required_skills:
        return 0.0, [], []

    matched = sorted(resume_skills & required_skills)
    missing = sorted(required_skills - resume_skills)
    score = len(matched) / len(required_skills)

    return score, matched, missing


def compute_final_score(embedding_similarity, tfidf_similarity, skill_overlap_score):
    return (
        EMBEDDING_WEIGHT * embedding_similarity
        + TFIDF_WEIGHT * tfidf_similarity
        + SKILL_WEIGHT * skill_overlap_score
    )


def build_rank_reason(embedding_similarity, tfidf_similarity, skill_overlap_score):
    return (
        "High semantic alignment with the job description, "
        f"strong keyword similarity ({tfidf_similarity:.2f}), "
        f"and skill coverage ({skill_overlap_score:.2f})."
    )