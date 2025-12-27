"""
Database module for the SOLO Quiz Generator
Handles all database operations using SQLite with SQLAlchemy ORM
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import enum

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), 'quiz_database.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine and base
engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)


class SoloLevel(enum.Enum):
    """SOLO Taxonomy levels for questions"""
    UNISTRUCTURAL = "unistructural"
    MULTISTRUCTURAL = "multistructural"
    RELATIONAL = "relational"
    EXTENDED_ABSTRACT = "extended_abstract"


class Course(Base):
    """
    Course model - top level container (e.g., "Operating Systems")
    """
    __tablename__ = 'courses'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), nullable=True)  # e.g., "OS", "CS101"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    lessons = relationship("Lesson", back_populates="course", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="course", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'lesson_count': len(self.lessons) if self.lessons else 0
        }


class Lesson(Base):
    """
    Lesson model - represents a PDF file/lesson (e.g., "Virtual Memory")
    """
    __tablename__ = 'lessons'
    
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=True)  # Original PDF filename
    file_path = Column(String(512), nullable=True)  # Path to stored PDF
    raw_content = Column(Text, nullable=True)  # Extracted text from PDF
    summary = Column(Text, nullable=True)  # AI-generated summary
    order_index = Column(Integer, default=0)  # Order within course
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = relationship("Course", back_populates="lessons")
    sections = relationship("Section", back_populates="lesson", cascade="all, delete-orphan")
    
    def to_dict(self, include_content=False):
        result = {
            'id': self.id,
            'course_id': self.course_id,
            'title': self.title,
            'filename': self.filename,
            'summary': self.summary,
            'order_index': self.order_index,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'section_count': len(self.sections) if self.sections else 0
        }
        if include_content:
            result['raw_content'] = self.raw_content
        return result


class Section(Base):
    """
    Section model - major divisions within a lesson (e.g., "Page Replacement Algorithms")
    """
    __tablename__ = 'sections'
    
    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey('lessons.id'), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)  # Text content of this section
    summary = Column(Text, nullable=True)  # AI-generated summary
    order_index = Column(Integer, default=0)  # Order within lesson
    start_page = Column(Integer, nullable=True)  # PDF page where section starts
    end_page = Column(Integer, nullable=True)  # PDF page where section ends
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    lesson = relationship("Lesson", back_populates="sections")
    learning_objects = relationship("LearningObject", back_populates="section", cascade="all, delete-orphan")
    
    def to_dict(self, include_content=False):
        result = {
            'id': self.id,
            'lesson_id': self.lesson_id,
            'title': self.title,
            'summary': self.summary,
            'order_index': self.order_index,
            'start_page': self.start_page,
            'end_page': self.end_page,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'learning_object_count': 0
        }
        # Try to get learning object count, fallback to 0 if columns don't exist
        try:
            result['learning_object_count'] = len(self.learning_objects) if self.learning_objects else 0
        except Exception:
            result['learning_object_count'] = 0
        if include_content:
            result['content'] = self.content
        return result


class LearningObject(Base):
    """
    Learning Object model - smallest unit of knowledge (concepts, definitions, procedures)
    """
    __tablename__ = 'learning_objects'
    
    id = Column(Integer, primary_key=True)
    section_id = Column(Integer, ForeignKey('sections.id'), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)  # The actual learning content (legacy, can be used for detailed description)
    description = Column(Text, nullable=True)  # Rich 4-6 sentence comprehensive description
    key_points = Column(JSON, nullable=True)  # List of detailed key points
    object_type = Column(String(50), nullable=True)  # concept, definition, procedure, example, etc.
    keywords = Column(JSON, nullable=True)  # List of keywords for this learning object
    order_index = Column(Integer, default=0)
    is_ai_generated = Column(Integer, default=1)  # Boolean as int: 1 = AI generated, 0 = human created
    human_modified = Column(Integer, default=0)  # Boolean as int: 1 = human edited, 0 = never edited
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    section = relationship("Section", back_populates="learning_objects")
    
    def to_dict(self):
        return {
            'id': self.id,
            'section_id': self.section_id,
            'title': self.title,
            'content': self.content,
            'description': self.description,
            'key_points': self.key_points,
            'object_type': self.object_type,
            'keywords': self.keywords,
            'order_index': self.order_index,
            'is_ai_generated': bool(getattr(self, 'is_ai_generated', 1)),
            'human_modified': bool(getattr(self, 'human_modified', 0)),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ConceptRelationship(Base):
    """
    Ontology relationship between learning objects (concepts)
    """
    __tablename__ = 'concept_relationships'
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('learning_objects.id'), nullable=False)
    target_id = Column(Integer, ForeignKey('learning_objects.id'), nullable=False)
    relationship_type = Column(String(50), nullable=False)  # prerequisite, part_of, related_to, etc.
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    source = relationship("LearningObject", foreign_keys=[source_id])
    target = relationship("LearningObject", foreign_keys=[target_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relationship_type': self.relationship_type,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'source_title': self.source.title if self.source else None,
            'target_title': self.target.title if self.target else None
        }


class Question(Base):
    """
    Question model - stores generated questions
    """
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True)
    # Source tracking - which lesson(s) was this generated from
    primary_lesson_id = Column(Integer, ForeignKey('lessons.id'), nullable=True)
    secondary_lesson_id = Column(Integer, ForeignKey('lessons.id'), nullable=True)  # For extended abstract
    section_id = Column(Integer, ForeignKey('sections.id'), nullable=True)
    learning_object_id = Column(Integer, ForeignKey('learning_objects.id'), nullable=True)
    
    # Question content
    solo_level = Column(String(50), nullable=False)  # unistructural, multistructural, relational, extended_abstract
    question_text = Column(Text, nullable=False)
    question_type = Column(String(50), default='multiple_choice')  # multiple_choice, true_false, short_answer
    
    # For multiple choice
    options = Column(JSON, nullable=True)  # List of options
    correct_answer = Column(Text, nullable=True)
    correct_option_index = Column(Integer, nullable=True)
    
    # Metadata
    explanation = Column(Text, nullable=True)
    difficulty = Column(Float, nullable=True)  # 0-1 scale
    bloom_level = Column(String(50), nullable=True)  # Bloom's taxonomy equivalent
    tags = Column(JSON, nullable=True)  # List of tags
    
    # AI Generation tracking
    is_ai_generated = Column(Integer, default=1)  # Boolean as int: 1 = AI generated, 0 = human created
    human_modified = Column(Integer, default=0)  # Boolean as int: 1 = human edited, 0 = never edited
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    used_count = Column(Integer, default=0)  # How many times used in quizzes
    
    # Relationships
    primary_lesson = relationship("Lesson", foreign_keys=[primary_lesson_id])
    secondary_lesson = relationship("Lesson", foreign_keys=[secondary_lesson_id])
    quiz_questions = relationship("QuizQuestion", back_populates="question", cascade="all, delete-orphan")
    
    def to_dict(self):
        result = {
            'id': self.id,
            'primary_lesson_id': self.primary_lesson_id,
            'secondary_lesson_id': self.secondary_lesson_id,
            'section_id': self.section_id,
            'learning_object_id': self.learning_object_id,
            'solo_level': self.solo_level,
            'question_text': self.question_text,
            'question_type': self.question_type,
            'options': self.options,
            'correct_answer': self.correct_answer,
            'correct_option_index': self.correct_option_index,
            'explanation': self.explanation,
            'difficulty': self.difficulty,
            'bloom_level': self.bloom_level,
            'tags': self.tags,
            'is_ai_generated': bool(getattr(self, 'is_ai_generated', 1)),
            'human_modified': bool(getattr(self, 'human_modified', 0)),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'used_count': self.used_count
        }
        # Add lesson titles
        if self.primary_lesson:
            result['primary_lesson_title'] = self.primary_lesson.title
        if self.secondary_lesson:
            result['secondary_lesson_title'] = self.secondary_lesson.title
        return result


class Quiz(Base):
    """
    Quiz model - a collection of questions
    """
    __tablename__ = 'quizzes'
    
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Configuration
    time_limit_minutes = Column(Integer, nullable=True)
    passing_score = Column(Float, nullable=True)  # Percentage
    shuffle_questions = Column(Integer, default=0)  # Boolean as int
    shuffle_options = Column(Integer, default=0)  # Boolean as int
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    course = relationship("Course", back_populates="quizzes")
    quiz_questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")
    
    def to_dict(self, include_questions=False):
        result = {
            'id': self.id,
            'course_id': self.course_id,
            'title': self.title,
            'description': self.description,
            'time_limit_minutes': self.time_limit_minutes,
            'passing_score': self.passing_score,
            'shuffle_questions': bool(self.shuffle_questions),
            'shuffle_options': bool(self.shuffle_options),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'question_count': len(self.quiz_questions) if self.quiz_questions else 0
        }
        if include_questions:
            result['questions'] = [qq.question.to_dict() for qq in self.quiz_questions]
        return result


class QuizQuestion(Base):
    """
    Association table between Quiz and Question with ordering
    """
    __tablename__ = 'quiz_questions'
    
    id = Column(Integer, primary_key=True)
    quiz_id = Column(Integer, ForeignKey('quizzes.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    order_index = Column(Integer, default=0)
    points = Column(Float, default=1.0)
    
    # Relationships
    quiz = relationship("Quiz", back_populates="quiz_questions")
    question = relationship("Question", back_populates="quiz_questions")


# Database operations class
class DatabaseManager:
    """Manager class for database operations"""
    
    def __init__(self):
        self.Session = Session
    
    def get_session(self):
        return self.Session()
    
    # Course operations
    def create_course(self, name, code=None, description=None):
        session = self.get_session()
        try:
            course = Course(name=name, code=code, description=description)
            session.add(course)
            session.commit()
            result = course.to_dict()
            return result
        finally:
            session.close()
    
    def get_all_courses(self):
        session = self.get_session()
        try:
            courses = session.query(Course).all()
            return [c.to_dict() for c in courses]
        finally:
            session.close()
    
    def get_course(self, course_id):
        session = self.get_session()
        try:
            course = session.query(Course).filter(Course.id == course_id).first()
            return course.to_dict() if course else None
        finally:
            session.close()
    
    def delete_course(self, course_id):
        session = self.get_session()
        try:
            course = session.query(Course).filter(Course.id == course_id).first()
            if course:
                session.delete(course)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    # Lesson operations
    def create_lesson(self, course_id, title, filename=None, file_path=None, raw_content=None):
        session = self.get_session()
        try:
            # Get max order_index for this course
            max_order = session.query(Lesson).filter(Lesson.course_id == course_id).count()
            lesson = Lesson(
                course_id=course_id,
                title=title,
                filename=filename,
                file_path=file_path,
                raw_content=raw_content,
                order_index=max_order
            )
            session.add(lesson)
            session.commit()
            result = lesson.to_dict()
            return result
        finally:
            session.close()
    
    def get_lessons_for_course(self, course_id):
        session = self.get_session()
        try:
            lessons = session.query(Lesson).filter(Lesson.course_id == course_id).order_by(Lesson.order_index).all()
            return [l.to_dict() for l in lessons]
        finally:
            session.close()
    
    def get_lesson(self, lesson_id, include_content=False):
        session = self.get_session()
        try:
            lesson = session.query(Lesson).filter(Lesson.id == lesson_id).first()
            return lesson.to_dict(include_content=include_content) if lesson else None
        finally:
            session.close()
    
    def get_lesson_with_sections(self, lesson_id):
        session = self.get_session()
        try:
            # Query lesson without trying to load learning_objects columns that may not exist
            lesson = session.query(Lesson).filter(Lesson.id == lesson_id).first()
            if not lesson:
                return None
            
            result = lesson.to_dict(include_content=True)
            sections_list = []
            
            # Manually load sections and learning_objects to avoid column errors
            for s in lesson.sections:
                section_dict = s.to_dict(include_content=True)
                # Load learning objects for this section with SQL that doesn't require new columns
                try:
                    learning_objects = session.query(LearningObject).filter(
                        LearningObject.section_id == s.id
                    ).all()
                    section_dict['learning_objects'] = [lo.to_dict() for lo in learning_objects]
                except Exception as e:
                    print(f"[WARNING] Could not load learning objects for section {s.id}: {str(e)}")
                    section_dict['learning_objects'] = []
                
                sections_list.append(section_dict)
            
            result['sections'] = sections_list
            return result
        finally:
            session.close()
    
    def delete_lesson(self, lesson_id):
        session = self.get_session()
        try:
            lesson = session.query(Lesson).filter(Lesson.id == lesson_id).first()
            if lesson:
                session.delete(lesson)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    # Section operations
    def create_section(self, lesson_id, title, content=None, start_page=None, end_page=None):
        session = self.get_session()
        try:
            max_order = session.query(Section).filter(Section.lesson_id == lesson_id).count()
            section = Section(
                lesson_id=lesson_id,
                title=title,
                content=content,
                start_page=start_page,
                end_page=end_page,
                order_index=max_order
            )
            session.add(section)
            session.commit()
            result = section.to_dict()
            return result
        finally:
            session.close()
    
    def get_sections_for_lesson(self, lesson_id):
        session = self.get_session()
        try:
            sections = session.query(Section).filter(Section.lesson_id == lesson_id).order_by(Section.order_index).all()
            return [s.to_dict() for s in sections]
        finally:
            session.close()
    
    def get_section_with_learning_objects(self, section_id):
        session = self.get_session()
        try:
            section = session.query(Section).filter(Section.id == section_id).first()
            if not section:
                return None
            result = section.to_dict(include_content=True)
            result['learning_objects'] = [lo.to_dict() for lo in section.learning_objects]
            return result
        finally:
            session.close()
    
    # Learning object operations
    def create_learning_object(self, section_id, title, content=None, object_type=None, keywords=None, is_ai_generated=True):
        session = self.get_session()
        try:
            max_order = session.query(LearningObject).filter(LearningObject.section_id == section_id).count()
            lo = LearningObject(
                section_id=section_id,
                title=title,
                content=content,
                object_type=object_type,
                keywords=keywords,
                order_index=max_order,
                is_ai_generated=int(is_ai_generated)
            )
            session.add(lo)
            session.commit()
            result = lo.to_dict()
            return result
        finally:
            session.close()
    
    def update_learning_object(self, lo_id, title=None, content=None, object_type=None, keywords=None, mark_as_human_modified=False):
        session = self.get_session()
        try:
            lo = session.query(LearningObject).filter(LearningObject.id == lo_id).first()
            if not lo:
                return None
            
            if title is not None:
                lo.title = title
            if content is not None:
                lo.content = content
            if object_type is not None:
                lo.object_type = object_type
            if keywords is not None:
                lo.keywords = keywords
            if mark_as_human_modified:
                lo.human_modified = 1
            lo.updated_at = datetime.utcnow()
            
            session.commit()
            return lo.to_dict()
        finally:
            session.close()
    
    def delete_learning_object(self, lo_id):
        session = self.get_session()
        try:
            lo = session.query(LearningObject).filter(LearningObject.id == lo_id).first()
            if lo:
                session.delete(lo)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    def get_learning_objects_for_section(self, section_id):
        session = self.get_session()
        try:
            los = session.query(LearningObject).filter(LearningObject.section_id == section_id).order_by(LearningObject.order_index).all()
            return [lo.to_dict() for lo in los]
        finally:
            session.close()
    
    # Ontology/Relationship operations
    def create_relationship(self, source_id, target_id, relationship_type, description=None):
        session = self.get_session()
        try:
            rel = ConceptRelationship(
                source_id=source_id,
                target_id=target_id,
                relationship_type=relationship_type,
                description=description
            )
            session.add(rel)
            session.commit()
            return rel.to_dict()
        finally:
            session.close()

    def get_relationships_for_lesson(self, lesson_id):
        session = self.get_session()
        try:
            # Get all learning objects for this lesson
            sections = session.query(Section).filter(Section.lesson_id == lesson_id).all()
            section_ids = [s.id for s in sections]
            los = session.query(LearningObject).filter(LearningObject.section_id.in_(section_ids)).all()
            lo_ids = [lo.id for lo in los]
            
            # Get relationships where both source and target are in this lesson
            rels = session.query(ConceptRelationship).filter(
                ConceptRelationship.source_id.in_(lo_ids) | 
                ConceptRelationship.target_id.in_(lo_ids)
            ).all()
            return [r.to_dict() for r in rels]
        finally:
            session.close()

    def delete_relationship(self, rel_id):
        """Delete a relationship by ID"""
        session = self.get_session()
        try:
            rel = session.query(ConceptRelationship).filter(ConceptRelationship.id == rel_id).first()
            if not rel:
                raise ValueError(f"Relationship with ID {rel_id} not found")
            session.delete(rel)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def bulk_create_relationships(self, relationships_data):
        session = self.get_session()
        try:
            for r_data in relationships_data:
                rel = ConceptRelationship(
                    source_id=r_data['source_id'],
                    target_id=r_data['target_id'],
                    relationship_type=r_data['relationship_type'],
                    description=r_data.get('description')
                )
                session.add(rel)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # Question operations
    def create_question(self, solo_level, question_text, question_type='multiple_choice',
                       primary_lesson_id=None, secondary_lesson_id=None, section_id=None,
                       learning_object_id=None, options=None, correct_answer=None,
                       correct_option_index=None, explanation=None, difficulty=None,
                       bloom_level=None, tags=None, is_ai_generated=True):
        session = self.get_session()
        try:
            question = Question(
                solo_level=solo_level,
                question_text=question_text,
                question_type=question_type,
                primary_lesson_id=primary_lesson_id,
                secondary_lesson_id=secondary_lesson_id,
                section_id=section_id,
                learning_object_id=learning_object_id,
                options=options,
                correct_answer=correct_answer,
                correct_option_index=correct_option_index,
                explanation=explanation,
                difficulty=difficulty,
                bloom_level=bloom_level,
                tags=tags,
                is_ai_generated=int(is_ai_generated)
            )
            session.add(question)
            session.commit()
            result = question.to_dict()
            return result
        finally:
            session.close()
    
    def update_question(self, question_id, **kwargs):
        session = self.get_session()
        try:
            question = session.query(Question).filter(Question.id == question_id).first()
            if not question:
                return None
            
            # Mark as human modified if updating
            mark_human_modified = kwargs.pop('mark_human_modified', False)
            
            for key, value in kwargs.items():
                if hasattr(question, key) and value is not None:
                    setattr(question, key, value)
            
            if mark_human_modified:
                question.human_modified = 1
            question.updated_at = datetime.utcnow()
            
            session.commit()
            return question.to_dict()
        finally:
            session.close()
    
    def get_questions_by_lesson(self, lesson_id):
        session = self.get_session()
        try:
            questions = session.query(Question).filter(
                (Question.primary_lesson_id == lesson_id) | 
                (Question.secondary_lesson_id == lesson_id)
            ).all()
            return [q.to_dict() for q in questions]
        finally:
            session.close()
    
    def get_questions_by_solo_level(self, solo_level, lesson_id=None):
        session = self.get_session()
        try:
            query = session.query(Question).filter(Question.solo_level == solo_level)
            if lesson_id:
                query = query.filter(
                    (Question.primary_lesson_id == lesson_id) | 
                    (Question.secondary_lesson_id == lesson_id)
                )
            questions = query.all()
            return [q.to_dict() for q in questions]
        finally:
            session.close()
    
    def get_all_questions(self, course_id=None):
        session = self.get_session()
        try:
            if course_id:
                # Get all lessons for this course
                lessons = session.query(Lesson).filter(Lesson.course_id == course_id).all()
                lesson_ids = [l.id for l in lessons]
                questions = session.query(Question).filter(
                    (Question.primary_lesson_id.in_(lesson_ids)) | 
                    (Question.secondary_lesson_id.in_(lesson_ids))
                ).all()
            else:
                questions = session.query(Question).all()
            return [q.to_dict() for q in questions]
        finally:
            session.close()
    
    def delete_question(self, question_id):
        session = self.get_session()
        try:
            question = session.query(Question).filter(Question.id == question_id).first()
            if question:
                session.delete(question)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    # Quiz operations
    def create_quiz(self, title, course_id=None, description=None, time_limit_minutes=None,
                   passing_score=None, shuffle_questions=False, shuffle_options=False):
        session = self.get_session()
        try:
            quiz = Quiz(
                title=title,
                course_id=course_id,
                description=description,
                time_limit_minutes=time_limit_minutes,
                passing_score=passing_score,
                shuffle_questions=int(shuffle_questions),
                shuffle_options=int(shuffle_options)
            )
            session.add(quiz)
            session.commit()
            result = quiz.to_dict()
            return result
        finally:
            session.close()
    
    def add_question_to_quiz(self, quiz_id, question_id, points=1.0):
        session = self.get_session()
        try:
            max_order = session.query(QuizQuestion).filter(QuizQuestion.quiz_id == quiz_id).count()
            qq = QuizQuestion(
                quiz_id=quiz_id,
                question_id=question_id,
                order_index=max_order,
                points=points
            )
            session.add(qq)
            session.commit()
            return True
        finally:
            session.close()
    
    def get_quiz(self, quiz_id, include_questions=False):
        session = self.get_session()
        try:
            quiz = session.query(Quiz).filter(Quiz.id == quiz_id).first()
            return quiz.to_dict(include_questions=include_questions) if quiz else None
        finally:
            session.close()
    
    def get_quizzes_for_course(self, course_id):
        session = self.get_session()
        try:
            quizzes = session.query(Quiz).filter(Quiz.course_id == course_id).all()
            return [q.to_dict() for q in quizzes]
        finally:
            session.close()
    
    def delete_quiz(self, quiz_id):
        session = self.get_session()
        try:
            quiz = session.query(Quiz).filter(Quiz.id == quiz_id).first()
            if quiz:
                session.delete(quiz)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    # Bulk operations for importing parsed content
    def bulk_create_sections_and_learning_objects(self, lesson_id, parsed_data):
        """
        Create multiple sections and learning objects from parsed PDF data
        parsed_data format:
        [
            {
                'title': 'Section Title',
                'content': 'Section content...',
                'start_page': 1,
                'end_page': 5,
                'learning_objects': [
                    {
                        'title': 'LO Title',
                        'content': 'LO content...',
                        'object_type': 'concept',
                        'keywords': ['keyword1', 'keyword2']
                    },
                    ...
                ]
            },
            ...
        ]
        """
        session = self.get_session()
        try:
            for idx, section_data in enumerate(parsed_data):
                section = Section(
                    lesson_id=lesson_id,
                    title=section_data['title'],
                    content=section_data.get('content'),
                    start_page=section_data.get('start_page'),
                    end_page=section_data.get('end_page'),
                    order_index=idx
                )
                session.add(section)
                session.flush()  # Get section.id
                
                for lo_idx, lo_data in enumerate(section_data.get('learning_objects', [])):
                    lo = LearningObject(
                        section_id=section.id,
                        title=lo_data['title'],
                        content=lo_data.get('content'),
                        description=lo_data.get('description'),  # Rich description
                        key_points=lo_data.get('key_points'),  # Detailed key points
                        object_type=lo_data.get('object_type'),
                        keywords=lo_data.get('keywords'),
                        order_index=lo_idx
                    )
                    session.add(lo)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def bulk_create_questions(self, questions_data):
        """Create multiple questions at once"""
        session = self.get_session()
        try:
            created_ids = []
            for q_data in questions_data:
                question = Question(
                    solo_level=q_data['solo_level'],
                    question_text=q_data['question_text'],
                    question_type=q_data.get('question_type', 'multiple_choice'),
                    primary_lesson_id=q_data.get('primary_lesson_id'),
                    secondary_lesson_id=q_data.get('secondary_lesson_id'),
                    section_id=q_data.get('section_id'),
                    learning_object_id=q_data.get('learning_object_id'),
                    options=q_data.get('options'),
                    correct_answer=q_data.get('correct_answer'),
                    correct_option_index=q_data.get('correct_option_index'),
                    explanation=q_data.get('explanation'),
                    difficulty=q_data.get('difficulty'),
                    bloom_level=q_data.get('bloom_level'),
                    tags=q_data.get('tags')
                )
                session.add(question)
                session.flush()
                created_ids.append(question.id)
            
            session.commit()
            return created_ids
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


def init_database():
    """Initialize the database, creating all tables"""
    Base.metadata.create_all(engine)
    print(f"[DATABASE] Initialized at {DB_PATH}")


# Initialize database on module import
init_database()

# Create a global database manager instance
db = DatabaseManager()
