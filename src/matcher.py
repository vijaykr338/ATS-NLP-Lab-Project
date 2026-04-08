from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def skill_match_score(resume_skills, jd_skills):
    if not jd_skills:
        return 0
    return len(resume_skills & jd_skills)/len(jd_skills)

def compute_match_score(clean_resume_text, clean_jd_text, resume_skills, jd_skills):
    """
    Computes ATS match score using TF-IDF + Cosine Similarity
    Returns score in range 0–100
    """

    vectorizer = TfidfVectorizer(
        max_features=500,
        ngram_range=(1, 2)  # single words and 2 word phrases
    )

    tfidf_matrix = vectorizer.fit_transform(
        [clean_resume_text, clean_jd_text]
    )

    similarity = cosine_similarity(
        tfidf_matrix[0],
        tfidf_matrix[1]
    )[0][0]

    skills_coverage = skill_match_score(resume_skills, jd_skills)

    return round((similarity*0.4 + skills_coverage*0.6)*100, 2)