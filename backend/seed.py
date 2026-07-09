import sys
import os
from typing import List, Dict, Any
from sqlalchemy.orm import Session

# Ensure we can import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
import models

EMBEDDING_DIM = 384


SEED_DATA: List[Dict[str, Any]] = [
    {
        "title": "Big O Notation",
        "description": "Comprehensive overview of algorithmic time and space complexity.",
        "lessons": [
            {
                "title": "Big O Notation",
                "video_url": "https://www.youtube.com/embed/sample_big_o_video",
                "content": """# Big O Notation

## Introduction

Big O Notation is a way of describing the performance or efficiency of an algorithm as the size of the input grows.

This lesson provides common examples and practical guidance for algorithmic analysis.
""",
            }
        ],
    }
]


def seed_database():
    db: Session = SessionLocal()
    try:
        print("Seeding database with core Computer Science content...")

        # If models.Lesson defines a content_embedding column, prepare a mock vector
        has_embedding = hasattr(models.Lesson, "content_embedding")
        mock_vector = [0.0] * EMBEDDING_DIM if has_embedding else None

        for course_data in SEED_DATA:
            title = course_data.get("title")
            if not title:
                print("Skipping a course with no title")
                continue

            description = course_data.get("description", "")

            course = db.query(models.Course).filter(models.Course.title == title).first()
            if course:
                course.description = description
            else:
                course = models.Course(title=title, description=description)
                db.add(course)
                db.flush()

            lessons = course_data.get("lessons", [])
            for lesson_data in lessons:
                ltitle = lesson_data.get("title")
                if not ltitle:
                    print(f"Skipping a lesson with no title for course {title}")
                    continue

                content = lesson_data.get("content", "")
                video_url = lesson_data.get("video_url")

                lesson = db.query(models.Lesson).filter(
                    models.Lesson.course_id == course.id,
                    models.Lesson.title == ltitle,
                ).first()

                if lesson:
                    lesson.content = content
                    lesson.video_url = video_url
                else:
                    lesson = models.Lesson(
                        course_id=course.id,
                        title=ltitle,
                        content=content,
                        video_url=video_url,
                    )
                if mock_vector is not None:
                    try:
                        lesson.content_embedding = mock_vector
                    except Exception:
                        # If assignment fails (e.g. pgvector not configured), ignore
                        pass

                db.add(lesson)

        db.commit()
        print("Successfully seeded courses and lessons into the database.")

    except Exception as e:
        db.rollback()
        print(f"An error occurred during seeding: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
