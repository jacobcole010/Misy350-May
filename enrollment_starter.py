"""
Module 8 Student Enrollment backend starter with Streamlit UI.

This file contains both the backend service layer and the Streamlit UI layer.
The UI provides a two-page dashboard for students to view enrollments and
manage enrollment keys.

Run with:
    streamlit run enrollment_starter.py
"""

from __future__ import annotations

import json
import sqlite3
import streamlit as st
from pathlib import Path
from typing import Any, Optional


DB_PATH = Path(__file__).with_name("student_enrollment_practice.db")
SNAPSHOT_PATH = Path(__file__).with_name("student_enrollment_snapshot.json")

CURRENT_STUDENT = {
    "user_id": "u100",
    "name": "Jacob Cole",
    "email": "jacob.cole@example.edu",
}

STATUS_ENROLLED = "enrolled"
STATUS_UNENROLLED = "unenrolled"

AVAILABLE_COURSE_KEYS = [
    {
        "course_id": "MISY350",
        "course_name": "Python for Business Analytics",
        "instructor": "Dr. Rivera",
        "enrollment_key": "MISY350-SPRING",
    },
    {
        "course_id": "DATA210",
        "course_name": "Data Storytelling",
        "instructor": "Prof. Morgan",
        "enrollment_key": "DATA210-SPRING",
    },
    {
        "course_id": "WEB220",
        "course_name": "Web Apps With Streamlit",
        "instructor": "Dr. Chen",
        "enrollment_key": "WEB220-SPRING",
    },
]

SAMPLE_ENROLLMENTS = [
    ("u100", "jacob.cole@example.edu", "MISY350", STATUS_ENROLLED),
    ("u100", "jacob.cole@example.edu", "DATA210", STATUS_UNENROLLED),
    ("u101", "alex@example.edu", "MISY350", STATUS_ENROLLED),
    ("u102", "blair@example.edu", "WEB220", STATUS_ENROLLED),
]


def connect() -> sqlite3.Connection:
    """Open a database connection."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_tables() -> None:
    """Create the courses and enrollments tables."""
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS courses (
                course_id TEXT PRIMARY KEY,
                course_name TEXT NOT NULL,
                instructor TEXT NOT NULL,
                enrollment_key TEXT NOT NULL UNIQUE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS enrollments (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                email TEXT NOT NULL,
                course_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'enrolled',
                enrolled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, course_id),
                FOREIGN KEY(course_id) REFERENCES courses(course_id)
            )
            """
        )


def seed_sample_data() -> None:
    """Seed courses, enrollment keys, and a few practice enrollment records."""
    with connect() as connection:
        connection.executemany(
            """
            INSERT OR IGNORE INTO courses (
                course_id, course_name, instructor, enrollment_key
            )
            VALUES (?, ?, ?, ?)
            """,
            [
                (
                    course["course_id"],
                    course["course_name"],
                    course["instructor"],
                    course["enrollment_key"],
                )
                for course in AVAILABLE_COURSE_KEYS
            ],
        )
        connection.executemany(
            """
            INSERT OR IGNORE INTO enrollments (user_id, email, course_id, status)
            VALUES (?, ?, ?, ?)
            """,
            SAMPLE_ENROLLMENTS,
        )


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    """Convert SQLite rows into dictionaries."""
    return [dict(row) for row in rows]


def get_available_course_keys() -> list[dict[str, Any]]:
    """Return the course keys that a UI could show for practice."""
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT course_id, course_name, instructor, enrollment_key
            FROM courses
            ORDER BY course_id
            """
        ).fetchall()

    return rows_to_dicts(rows)


def get_course_by_key(enrollment_key: str) -> Optional[dict[str, Any]]:
    """Find a course by its enrollment key."""
    if not enrollment_key:
        return None

    with connect() as connection:
        row = connection.execute(
            """
            SELECT course_id, course_name, instructor, enrollment_key
            FROM courses
            WHERE enrollment_key = ?
            """,
            (enrollment_key.strip().upper(),),
        ).fetchone()

    return dict(row) if row else None


def get_student_enrollments(user_id: str) -> list[dict[str, Any]]:
    """Return the classes where the student is currently enrolled."""
    if not user_id:
        return []

    with connect() as connection:
        rows = connection.execute(
            """
            SELECT
                e.enrollment_id,
                e.user_id,
                e.email,
                e.course_id,
                c.course_name,
                c.instructor,
                e.status,
                e.enrolled_at
            FROM enrollments e
            JOIN courses c ON c.course_id = e.course_id
            WHERE e.user_id = ? AND e.status = ?
            ORDER BY c.course_id
            """,
            (user_id, STATUS_ENROLLED),
        ).fetchall()

    return rows_to_dicts(rows)


def get_student_enrollment_history(user_id: str) -> list[dict[str, Any]]:
    """Return all enrollment records for one student, including unenrolled."""
    if not user_id:
        return []

    with connect() as connection:
        rows = connection.execute(
            """
            SELECT
                e.enrollment_id,
                e.user_id,
                e.email,
                e.course_id,
                c.course_name,
                c.instructor,
                e.status,
                e.enrolled_at
            FROM enrollments e
            JOIN courses c ON c.course_id = e.course_id
            WHERE e.user_id = ?
            ORDER BY c.course_id
            """,
            (user_id,),
        ).fetchall()

    return rows_to_dicts(rows)


def get_student_course_record(
    user_id: str,
    course_id: str,
) -> Optional[dict[str, Any]]:
    """Return one student's enrollment record for one course."""
    if not user_id or not course_id:
        return None

    with connect() as connection:
        row = connection.execute(
            """
            SELECT enrollment_id, user_id, email, course_id, status, enrolled_at
            FROM enrollments
            WHERE user_id = ? AND course_id = ?
            """,
            (user_id, course_id),
        ).fetchone()

    return dict(row) if row else None


def enroll_with_key(
    user_id: str,
    email: str,
    enrollment_key: str,
) -> Optional[dict[str, Any]]:
    """Enroll or reactivate a student using a course enrollment key."""
    if not user_id or not email or "@" not in email or not enrollment_key:
        return None

    course = get_course_by_key(enrollment_key)
    if not course:
        return None

    with connect() as connection:
        connection.execute(
            """
            INSERT INTO enrollments (user_id, email, course_id, status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, course_id)
            DO UPDATE SET
                email = excluded.email,
                status = excluded.status,
                enrolled_at = CURRENT_TIMESTAMP
            """,
            (user_id, email, course["course_id"], STATUS_ENROLLED),
        )

    return get_student_course_record(user_id, course["course_id"])


def soft_unenroll_student(user_id: str, course_id: str) -> bool:
    """Soft-unenroll one student by changing status instead of deleting."""
    if not user_id or not course_id:
        return False

    with connect() as connection:
        cursor = connection.execute(
            """
            UPDATE enrollments
            SET status = ?
            WHERE user_id = ? AND course_id = ?
            """,
            (STATUS_UNENROLLED, user_id, course_id),
        )

    return cursor.rowcount > 0


def get_student_summary(user_id: str) -> dict[str, int]:
    """Return summary counts for one student."""
    summary = {
        "total_records": 0,
        STATUS_ENROLLED: 0,
        STATUS_UNENROLLED: 0,
    }

    for record in get_student_enrollment_history(user_id):
        summary["total_records"] += 1
        status = record["status"]
        if status in summary:
            summary[status] += 1

    return summary


def get_all_enrollment_records() -> list[dict[str, Any]]:
    """Return every enrollment record for the database snapshot."""
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT
                e.enrollment_id,
                e.user_id,
                e.email,
                e.course_id,
                c.course_name,
                c.instructor,
                e.status,
                e.enrolled_at
            FROM enrollments e
            JOIN courses c ON c.course_id = e.course_id
            ORDER BY e.user_id, e.course_id
            """
        ).fetchall()

    return rows_to_dicts(rows)


def export_database_snapshot(path: Path = SNAPSHOT_PATH) -> None:
    """Write seeded database content to JSON so students can inspect it."""
    snapshot = {
        "current_student": CURRENT_STUDENT,
        "available_course_keys": get_available_course_keys(),
        "enrollment_table": get_all_enrollment_records(),
    }
    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")


def init_session_state() -> None:
    """Initialize session state keys for the Streamlit UI."""
    if "page" not in st.session_state:
        st.session_state.page = "dashboard"
    if "selected_course_id" not in st.session_state:
        st.session_state.selected_course_id = None
    if "feedback_message" not in st.session_state:
        st.session_state.feedback_message = ""
    if "feedback_type" not in st.session_state:
        st.session_state.feedback_type = ""


def render_dashboard() -> None:
    """Render the student dashboard page."""
    st.title("Student Dashboard")
    st.write(f"Welcome, {CURRENT_STUDENT['name']}")

    st.subheader("Your Enrolled Classes")
    enrolled_courses = get_student_enrollments(CURRENT_STUDENT["user_id"])

    if not enrolled_courses:
        st.info("You're not enrolled in any classes yet. Enter an enrollment key to enroll.")
    else:
        for course in enrolled_courses:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**{course['course_name']}**")
                    st.write(f"Instructor: {course['instructor']}")
                    st.write(f"Enrolled: {course['enrolled_at']}")
                with col2:
                    if st.button("Go to Class", key=f"go_{course['course_id']}"):
                        st.session_state.selected_course_id = course["course_id"]
                        st.session_state.page = "class_detail"
                        st.rerun()
                    if st.button("Unenroll", key=f"unenroll_{course['course_id']}"):
                        soft_unenroll_student(CURRENT_STUDENT["user_id"], course["course_id"])
                        st.session_state.feedback_message = f"You have unenrolled from {course['course_name']}. You can re-enroll anytime."
                        st.session_state.feedback_type = "success"
                        st.rerun()

    st.subheader("Enroll in a New Class")
    enrollment_key = st.text_input("Enter enrollment key:")
    if st.button("Enroll"):
        if enrollment_key:
            course = get_course_by_key(enrollment_key)
            if course:
                result = enroll_with_key(CURRENT_STUDENT["user_id"], CURRENT_STUDENT["email"], enrollment_key)
                if result:
                    st.session_state.feedback_message = f"Successfully enrolled in {course['course_name']}!"
                    st.session_state.feedback_type = "success"
                    st.rerun()
            else:
                st.session_state.feedback_message = "Enrollment key not found. Please check and try again."
                st.session_state.feedback_type = "error"
        else:
            st.session_state.feedback_message = "Please enter an enrollment key."
            st.session_state.feedback_type = "error"

    if st.session_state.feedback_message:
        if st.session_state.feedback_type == "success":
            st.success(st.session_state.feedback_message)
        elif st.session_state.feedback_type == "error":
            st.error(st.session_state.feedback_message)
        elif st.session_state.feedback_type == "warning":
            st.warning(st.session_state.feedback_message)
        st.session_state.feedback_message = ""
        st.session_state.feedback_type = ""


def render_class_detail() -> None:
    """Render the class detail page."""
    course_id = st.session_state.selected_course_id
    enrollment_record = get_student_course_record(CURRENT_STUDENT["user_id"], course_id)

    if not enrollment_record:
        st.error("Course not found.")
        if st.button("Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.session_state.selected_course_id = None
            st.rerun()
        return

    # Get course details
    course = get_course_by_key("")  # This won't work; need to fetch course by ID
    courses = get_available_course_keys()
    course = next((c for c in courses if c["course_id"] == course_id), None)

    if not course:
        st.error("Course details not found.")
        if st.button("Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.session_state.selected_course_id = None
            st.rerun()
        return

    st.title(course["course_name"])
    st.write(f"Instructor: {course['instructor']}")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("Course ID", course_id)
    with col2:
        st.metric("Enrolled Since", enrollment_record["enrolled_at"])

    if st.button("Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.session_state.selected_course_id = None
        st.rerun()


def main() -> None:
    """Main Streamlit app entry point."""
    create_tables()
    seed_sample_data()
    init_session_state()

    if st.session_state.page == "dashboard":
        render_dashboard()
    elif st.session_state.page == "class_detail":
        render_class_detail()


if __name__ == "__main__":
    main()