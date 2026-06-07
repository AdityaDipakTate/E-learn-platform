import sys
import os
from sqlalchemy.orm import Session

# Ensure the script can locate your database and models modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
import models

# 1. Define High-Quality Computer Science Content (Clean Data Separation)
SEED_DATA = [
    {
        "title": "Introduction to Programming",
        "description": "Learn foundational programming concepts using Python.",
        "lessons": [
            {
                "title": "Introduction to Python Arrays",
                "video_url": "https://www.youtube.com/embed/sample_array_video",
                "content": """### Understanding Arrays in Python

In Python, native lists typically serve the purpose of arrays. An **array** is a linear collection of elements stored at contiguous memory locations.

#### Key Characteristics
* **Fixed Size:** In low-level languages, arrays have a static size (Python lists bypass this by dynamically resizing).
* **Indexing:** Elements are accessed using a zero-based index system.

```python
# Creating a simple array-like list in Python
numbers = [10, 20, 30, 40, 50]

# Accessing elements via index - O(1) complexity
print(numbers[0]) # Output: 10
print(numbers[3]) # Output: 40
```"""
            }
        ]
    },
    {
        "title": "Data Structures & Algorithms",
        "description": "Master algorithmic complexity and foundational data structures.",
        "lessons": [
            {
                "title": "Understanding Binary Search Trees",
                "video_url": "https://www.youtube.com/embed/sample_bst_video",
                "content": """### Introduction to Binary Search Trees (BST)

A **Binary Search Tree** is a node-based binary tree data structure which has the following properties:
1. The left subtree of a node contains only nodes with keys **less than** the node's key.
2. The right subtree of a node contains only nodes with keys **greater than** the node's key.

#### Why use a BST?
Instead of searching an array linearly ($O(n)$), a balanced BST allows you to skip half the remaining elements at each step!

Using a BST allows for $O(\\log n)$ time complexity for search operations!"""
            }
        ]
    }
]

# 2. Seeding Logic Function
def seed_database():
    db: Session = SessionLocal()
    try:
        print("Checking existing database contents...")
        existing_courses = db.query(models.Course).first()
        
        if existing_courses:
            print("Database already contains data! Skipping seeding to prevent duplication.")
            return

        print("Seeding database with core Computer Science content...")
        
        # Check if the embedding column is currently active in models.py
        has_embedding = hasattr(models.Lesson, 'content_embedding')
        mock_vector = [0.1] * 1536 if has_embedding else None

        for course_data in SEED_DATA:
            # Create the Course entry
            new_course = models.Course(
                title=course_data["title"],
                description=course_data["description"]
            )
            db.add(new_course)
            db.flush()  # Flushes to generate the course ID for foreign key relational binding

            # Create the Lesson entries linked to this course
            for lesson_data in course_data["lessons"]:
                new_lesson = models.Lesson(
                    course_id=new_course.id,
                    title=lesson_data["title"],
                    content=lesson_data["content"],
                    video_url=lesson_data["video_url"]
                )
                
                # Dynamically inject the vector only if you've uncommented it in models.py
                if has_embedding:
                    new_lesson.content_embedding = mock_vector
                    
                db.add(new_lesson)
        
        db.commit()
        print("🎉 Successfully seeded courses and lessons into PostgreSQL!")

    except Exception as e:
        db.rollback()
        print(f"An error occurred during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()