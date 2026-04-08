import spacy

nlp = spacy.load("en_core_web_sm")

def clean_text(text):
    doc = nlp(text.lower())
    tokens = []

    for token in doc:
        if token.is_stop or token.is_punct:
            continue
        tokens.append(token.lemma_)

    return " ".join(tokens)