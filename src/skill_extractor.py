SKILLS = [
    "python", "sql", "machine learning", "data analysis",
    "docker", "flask", "tensorflow", "pandas",
    "numpy", "javascript", "react", "html", "css",

    # Data Science & ML
    "scikit-learn", "matplotlib", "seaborn", "statistics",
    "data visualization", "feature engineering",
    "model evaluation", "hyperparameter tuning",

    # Deep Learning & AI
    "keras", "pytorch", "computer vision",
    "natural language processing", "time series analysis",

    # Backend & APIs
    "fastapi", "rest apis", "graphql",
    "authentication", "authorization",

    # Databases & Big Data
    "postgresql", "mysql", "mongodb",
    "data warehousing", "etl pipelines",

    # DevOps & Deployment
    "linux", "git", "github actions",
    "ci/cd", "cloud computing",
    "aws", "model deployment",

    # Web & General CS
    "node.js", "express.js",
    "responsive design", "software engineering",
    "data structures", "algorithms"
]

import re

REGEX_SKILLS = {
    "machine learning": r"(machine[-\s]?learning|\bml\b)",
    "deep learning": r"(deep[-\s]?learning|\bdl\b)",
    "data science": r"(data[-\s]?science)",
    
    "c++": r"(c\+\+)",
    "python": r"\bpython\b",
    "sql": r"\bsql\b",

    "node.js": r"(node\.?js|nodejs|\bnode\b)",
    "express.js": r"(express\.?js|expressjs|\bexpress\b)",
    "react": r"\breact(\.js)?\b",

    "tensorflow": r"\btensorflow\b",
    "pytorch": r"\bpytorch\b",
    "scikit-learn": r"(scikit[-\s]?learn|sklearn)",

    "postgresql": r"(postgresql|postgres)",
    "mongodb": r"\bmongo(db)?\b",

    "aws": r"\baws\b|amazon web services",
    "docker": r"\bdocker\b",
    "git": r"\bgit\b",
}

def extract_skills(text, skill_list=SKILLS):
    extracted_skills = set()
    for skill in skill_list:
        if skill in text:
            extracted_skills.add(skill)
    return extracted_skills

def extract_skills_regex(text, regex_dict=REGEX_SKILLS):
    extracted = set()
    for skill, pattern in regex_dict.items():
        if re.search(pattern, text):
            extracted.add(skill)
    return extracted