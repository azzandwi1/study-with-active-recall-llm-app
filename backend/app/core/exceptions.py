"""
Custom exceptions for the Active Recall Backend
"""


class ActiveRecallException(Exception):
    """Base exception for Active Recall application"""
    pass


class APIKeyError(ActiveRecallException):
    """Exception raised for API key related errors"""
    pass


class ContentProcessingError(ActiveRecallException):
    """Exception raised during content processing"""
    pass


class PDFProcessingError(ContentProcessingError):
    """Exception raised during PDF processing"""
    pass


class OCRProcessingError(ContentProcessingError):
    """Exception raised during OCR processing"""
    pass


class WebScrapingError(ContentProcessingError):
    """Exception raised during web scraping"""
    pass


class EmbeddingError(ActiveRecallException):
    """Exception raised during embedding generation"""
    pass


class FAISSError(ActiveRecallException):
    """Exception raised during FAISS operations"""
    pass


class LLMError(ActiveRecallException):
    """Exception raised during LLM operations"""
    pass


class GradingError(ActiveRecallException):
    """Exception raised during answer grading"""
    pass


class DatabaseError(ActiveRecallException):
    """Exception raised during database operations"""
    pass


class ValidationError(ActiveRecallException):
    """Exception raised during data validation"""
    pass


class FileUploadError(ActiveRecallException):
    """Exception raised during file upload operations"""
    pass


class CollectionNotFoundError(ActiveRecallException):
    """Exception raised when collection is not found"""
    pass


class FlashcardNotFoundError(ActiveRecallException):
    """Exception raised when flashcard is not found"""
    pass


class QuizSessionNotFoundError(ActiveRecallException):
    """Exception raised when quiz session is not found"""
    pass
