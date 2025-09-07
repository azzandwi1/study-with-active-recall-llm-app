from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


class Collection(Base):
    __tablename__ = "collections"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    documents = relationship("Document", back_populates="collection", cascade="all, delete-orphan")
    flashcards = relationship("Flashcard", back_populates="collection", cascade="all, delete-orphan")
    quiz_sessions = relationship("QuizSession", back_populates="collection", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    collection_id = Column(String, ForeignKey("collections.id"), nullable=False)
    source_type = Column(String(20), nullable=False)  # 'pdf', 'url', 'text'
    source_url = Column(String(1000))  # For URL sources
    filename = Column(String(255))  # For file uploads
    title = Column(String(500))
    content = Column(Text)
    metadata = Column(JSON)  # Store additional metadata
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    collection = relationship("Collection", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    embedding_vector = Column(JSON)  # Store embedding as JSON array
    metadata = Column(JSON)  # Store chunk-specific metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    flashcards = relationship("Flashcard", back_populates="source_chunks")
    
    # Indexes
    __table_args__ = (
        Index('idx_chunk_document', 'document_id'),
        Index('idx_chunk_index', 'document_id', 'chunk_index'),
    )


class Flashcard(Base):
    __tablename__ = "flashcards"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    collection_id = Column(String, ForeignKey("collections.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    difficulty = Column(String(20), default="medium")  # 'easy', 'medium', 'hard'
    tags = Column(JSON)  # Store tags as JSON array
    style = Column(String(20), default="basic")  # 'basic', 'cloze', 'concept'
    source_chunk_ids = Column(JSON)  # Array of chunk IDs used to generate this card
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    collection = relationship("Collection", back_populates="flashcards")
    source_chunks = relationship("Chunk", back_populates="flashcards")
    reviews = relationship("Review", back_populates="flashcard", cascade="all, delete-orphan")
    quiz_questions = relationship("QuizQuestion", back_populates="flashcard", cascade="all, delete-orphan")


class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    flashcard_id = Column(String, ForeignKey("flashcards.id"), nullable=False)
    user_id = Column(String(100), nullable=False)  # Simple user identifier
    
    # SM-2 Algorithm fields
    repetitions = Column(Integer, default=0)
    interval_days = Column(Integer, default=1)
    easiness_factor = Column(Float, default=2.5)
    due_at = Column(DateTime(timezone=True), nullable=False)
    
    # Review tracking
    last_reviewed_at = Column(DateTime(timezone=True))
    review_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    flashcard = relationship("Flashcard", back_populates="reviews")
    
    # Indexes
    __table_args__ = (
        Index('idx_review_user_due', 'user_id', 'due_at'),
        Index('idx_review_flashcard', 'flashcard_id'),
    )


class QuizSession(Base):
    __tablename__ = "quiz_sessions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    collection_id = Column(String, ForeignKey("collections.id"), nullable=False)
    user_id = Column(String(100), nullable=False)
    strategy = Column(String(20), default="mixed")  # 'mixed', 'weakest', 'new'
    total_questions = Column(Integer, nullable=False)
    completed_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    collection = relationship("Collection", back_populates="quiz_sessions")
    questions = relationship("QuizQuestion", back_populates="session", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index('idx_quiz_user', 'user_id'),
        Index('idx_quiz_collection', 'collection_id'),
    )


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("quiz_sessions.id"), nullable=False)
    flashcard_id = Column(String, ForeignKey("flashcards.id"), nullable=False)
    question_index = Column(Integer, nullable=False)
    user_answer = Column(Text)
    is_correct = Column(Boolean)
    score = Column(Float)  # 0.0 to 1.0
    feedback = Column(Text)
    answered_at = Column(DateTime(timezone=True))
    
    # Relationships
    session = relationship("QuizSession", back_populates="questions")
    flashcard = relationship("Flashcard", back_populates="quiz_questions")
    
    # Indexes
    __table_args__ = (
        Index('idx_quiz_question_session', 'session_id', 'question_index'),
    )
