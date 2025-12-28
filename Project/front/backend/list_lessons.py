from database import DatabaseManager, Lesson
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

db_manager = DatabaseManager()
session = db_manager.Session()
lessons = session.query(Lesson).limit(15).all()

print("Available lessons:")
for i, lesson in enumerate(lessons[:15], 1):
    lesson_id = lesson.id
    title = lesson.title
    print(f"{i}. ID={lesson_id} | {title}")
