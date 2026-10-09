from flask import Flask, request, jsonify
from difflib import SequenceMatcher
import sqlite3
import re
import os

app = Flask(__name__)

DATABASE = "submissions.db"


def clean_text(text):
    return re.sub(r"[^a-z0-9\s]", " ", text.lower()).strip()


def similarity(text1, text2):
    text1 = clean_text(text1)
    text2 = clean_text(text2)

    if not text1 or not text2:
        return 0.0

    return round(
        SequenceMatcher(None, text1, text2).ratio() * 100,
        2
    )


def get_connection():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT NOT NULL,
                assignment_title TEXT NOT NULL,
                assignment_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


initialize_database()


@app.route("/")
def home():
    return jsonify({
        "message": "Student Plagiarism Management System API is running."
    })


@app.route("/api/submit", methods=["POST"])
def submit_assignment():
    data = request.get_json(silent=True) or {}

    student_name = data.get("student_name", "").strip()
    title = data.get("title", "").strip()
    text = data.get("text", "").strip()

    if not student_name or not title or not text:
        return jsonify({
            "error": "Student name, assignment title, and text are required."
        }), 400

    if len(text) > 200000:
        return jsonify({
            "error": "Assignment text is too long."
        }), 400

    connection = get_connection()

    try:
        previous = connection.execute(
            "SELECT id, student_name, assignment_title, assignment_text "
            "FROM submissions"
        ).fetchall()

        matches = []

        for submission in previous:
            # Do not compare a student's submission against itself.
            if submission["student_name"].casefold() == student_name.casefold():
                continue

            score = similarity(text, submission["assignment_text"])

            matches.append({
                "submission_id": submission["id"],
                "student_name": submission["student_name"],
                "assignment_title": submission["assignment_title"],
                "similarity": score
            })

        matches.sort(
            key=lambda item: item["similarity"],
            reverse=True
        )

        cursor = connection.execute(
            "INSERT INTO submissions "
            "(student_name, assignment_title, assignment_text) "
            "VALUES (?, ?, ?)",
            (student_name, title, text)
        )

        connection.commit()

        return jsonify({
            "message": "Assignment saved successfully.",
            "submission_id": cursor.lastrowid,
            "student_name": student_name,
            "assignment_title": title,
            "comparisons": matches,
            "notice": (
                "Similarity is a screening aid, not proof of plagiarism. "
                "Review matching text and context before making a decision."
            )
        }), 201

    finally:
        connection.close()


@app.route("/api/submissions", methods=["GET"])
def list_submissions():
    connection = get_connection()

    try:
        rows = connection.execute(
            "SELECT id, student_name, assignment_title, created_at "
            "FROM submissions ORDER BY id DESC"
        ).fetchall()

        return jsonify({
            "submissions": [dict(row) for row in rows]
        })

    finally:
        connection.close()


if __name__ == "__main__":
    app.run()
