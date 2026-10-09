from flask import Flask, request, jsonify
from difflib import SequenceMatcher
import re

app = Flask(__name__)

# Sample reference documents for testing.
# Later, we will add a database of student submissions
# and lecturer-approved reference documents.
REFERENCES = [
    {
        "title": "Reference 1",
        "text": (
            "Artificial intelligence enables computers to perform "
            "tasks that normally require human intelligence."
        )
    },
    {
        "title": "Reference 2",
        "text": (
            "Climate change refers to long term changes in temperature "
            "and weather patterns."
        )
    },
    {
        "title": "Reference 3",
        "text": (
            "Education helps students acquire knowledge, skills, "
            "and experience for their future careers."
        )
    }
]


def clean_text(text):
    """Convert text to lowercase and remove punctuation."""
    return re.sub(r"[^a-z0-9\s]", "", text.lower()).strip()


def compare_texts(submitted_text, reference_text):
    """Calculate a basic text similarity score."""
    submitted = clean_text(submitted_text)
    reference = clean_text(reference_text)

    return round(
        SequenceMatcher(None, submitted, reference).ratio() * 100,
        2
    )


@app.route("/")
def home():
    return jsonify({
        "message": "Student Plagiarism Management System API is running."
    })


@app.route("/api/check", methods=["POST"])
def check_plagiarism():
    data = request.get_json(silent=True) or {}

    student_name = data.get("student_name", "").strip()
    submitted_text = data.get("text", "").strip()

    if not submitted_text:
        return jsonify({
            "error": "Please provide assignment text."
        }), 400

    results = []

    for reference in REFERENCES:
        score = compare_texts(
            submitted_text,
            reference["text"]
        )

        results.append({
            "source": reference["title"],
            "similarity": score
        })

    results.sort(
        key=lambda item: item["similarity"],
        reverse=True
    )

    return jsonify({
        "student_name": student_name,
        "highest_similarity": results[0]["similarity"],
        "results": results,
        "notice": (
            "Similarity is an indicator, not proof of plagiarism. "
            "Only the configured sample references are checked."
        )
    })


if __name__ == "__main__":
    app.run()
