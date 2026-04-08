import pickle
import os

class ResumeClassifier:
    def __init__(self, model_dir="models"):
        with open(os.path.join(model_dir, "vectorizer.pkl"), "rb") as f:
            self.vectorizer = pickle.load(f)

        with open(os.path.join(model_dir, "classifier.pkl"), "rb") as f:
            self.model = pickle.load(f)

    def predict(self, text):
        X = self.vectorizer.transform([text])
        return self.model.predict(X)[0]