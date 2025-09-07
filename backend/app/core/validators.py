"""
Data validation utilities for the Active Recall Backend
"""

import re
from typing import Optional, List
from urllib.parse import urlparse
from app.core.exceptions import ValidationError, FileUploadError


class ContentValidator:
    """Validator for content-related operations"""
    
    @staticmethod
    def validate_text_content(text: str, min_length: int = 10, max_length: int = 1000000) -> str:
        """Validate text content"""
        if not text or not isinstance(text, str):
            raise ValidationError("Text content is required")
        
        text = text.strip()
        if len(text) < min_length:
            raise ValidationError(f"Text content must be at least {min_length} characters long")
        
        if len(text) > max_length:
            raise ValidationError(f"Text content must be no more than {max_length} characters long")
        
        return text
    
    @staticmethod
    def validate_url(url: str) -> str:
        """Validate URL format and security"""
        if not url or not isinstance(url, str):
            raise ValidationError("URL is required")
        
        url = url.strip()
        
        # Basic URL format validation
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValidationError("Invalid URL format")
            
            if parsed.scheme not in ['http', 'https']:
                raise ValidationError("URL must use HTTP or HTTPS protocol")
            
        except Exception:
            raise ValidationError("Invalid URL format")
        
        # Security checks
        blocked_patterns = [
            'file://',
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            '::1'
        ]
        
        url_lower = url.lower()
        for pattern in blocked_patterns:
            if pattern in url_lower:
                raise ValidationError(f"URL contains blocked pattern: {pattern}")
        
        return url
    
    @staticmethod
    def validate_collection_name(name: str) -> str:
        """Validate collection name"""
        if not name or not isinstance(name, str):
            raise ValidationError("Collection name is required")
        
        name = name.strip()
        if len(name) < 1:
            raise ValidationError("Collection name cannot be empty")
        
        if len(name) > 255:
            raise ValidationError("Collection name must be no more than 255 characters")
        
        # Check for invalid characters
        if re.search(r'[<>:"/\\|?*]', name):
            raise ValidationError("Collection name contains invalid characters")
        
        return name


class FileValidator:
    """Validator for file uploads"""
    
    ALLOWED_EXTENSIONS = {'.pdf'}
    ALLOWED_MIME_TYPES = {'application/pdf'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def validate_file_upload(filename: str, content_type: str, file_size: int) -> None:
        """Validate file upload"""
        if not filename:
            raise FileUploadError("Filename is required")
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in FileValidator.ALLOWED_EXTENSIONS:
            raise FileUploadError(f"File type {file_ext} is not allowed. Allowed types: {', '.join(FileValidator.ALLOWED_EXTENSIONS)}")
        
        # Check MIME type
        if content_type not in FileValidator.ALLOWED_MIME_TYPES:
            raise FileUploadError(f"MIME type {content_type} is not allowed. Allowed types: {', '.join(FileValidator.ALLOWED_MIME_TYPES)}")
        
        # Check file size
        if file_size > FileValidator.MAX_FILE_SIZE:
            raise FileUploadError(f"File size {file_size} bytes exceeds maximum allowed size of {FileValidator.MAX_FILE_SIZE} bytes")
        
        if file_size == 0:
            raise FileUploadError("File is empty")


class APIValidator:
    """Validator for API requests"""
    
    @staticmethod
    def validate_api_key(api_key: str) -> str:
        """Validate API key format"""
        if not api_key or not isinstance(api_key, str):
            raise ValidationError("API key is required")
        
        api_key = api_key.strip()
        if len(api_key) < 10:
            raise ValidationError("API key appears to be too short")
        
        if len(api_key) > 200:
            raise ValidationError("API key appears to be too long")
        
        return api_key
    
    @staticmethod
    def validate_user_id(user_id: str) -> str:
        """Validate user ID format"""
        if not user_id or not isinstance(user_id, str):
            raise ValidationError("User ID is required")
        
        user_id = user_id.strip()
        if len(user_id) < 1:
            raise ValidationError("User ID cannot be empty")
        
        if len(user_id) > 100:
            raise ValidationError("User ID must be no more than 100 characters")
        
        # Check for invalid characters
        if re.search(r'[<>:"/\\|?*]', user_id):
            raise ValidationError("User ID contains invalid characters")
        
        return user_id
    
    @staticmethod
    def validate_collection_id(collection_id: str) -> str:
        """Validate collection ID format"""
        if not collection_id or not isinstance(collection_id, str):
            raise ValidationError("Collection ID is required")
        
        collection_id = collection_id.strip()
        if len(collection_id) < 1:
            raise ValidationError("Collection ID cannot be empty")
        
        # UUID format validation (basic)
        if not re.match(r'^[a-f0-9-]{36}$', collection_id):
            raise ValidationError("Invalid collection ID format")
        
        return collection_id


class QuizValidator:
    """Validator for quiz-related operations"""
    
    @staticmethod
    def validate_quiz_count(count: int) -> int:
        """Validate quiz question count"""
        if not isinstance(count, int):
            raise ValidationError("Quiz count must be an integer")
        
        if count < 1:
            raise ValidationError("Quiz count must be at least 1")
        
        if count > 50:
            raise ValidationError("Quiz count must be no more than 50")
        
        return count
    
    @staticmethod
    def validate_quiz_strategy(strategy: str) -> str:
        """Validate quiz strategy"""
        if not strategy or not isinstance(strategy, str):
            raise ValidationError("Quiz strategy is required")
        
        strategy = strategy.strip().lower()
        valid_strategies = ['mixed', 'weakest', 'new']
        
        if strategy not in valid_strategies:
            raise ValidationError(f"Invalid quiz strategy. Valid strategies: {', '.join(valid_strategies)}")
        
        return strategy
    
    @staticmethod
    def validate_flashcard_style(style: str) -> str:
        """Validate flashcard style"""
        if not style or not isinstance(style, str):
            raise ValidationError("Flashcard style is required")
        
        style = style.strip().lower()
        valid_styles = ['basic', 'cloze', 'concept']
        
        if style not in valid_styles:
            raise ValidationError(f"Invalid flashcard style. Valid styles: {', '.join(valid_styles)}")
        
        return style
    
    @staticmethod
    def validate_difficulty(difficulty: str) -> str:
        """Validate difficulty level"""
        if not difficulty or not isinstance(difficulty, str):
            raise ValidationError("Difficulty is required")
        
        difficulty = difficulty.strip().lower()
        valid_difficulties = ['easy', 'medium', 'hard']
        
        if difficulty not in valid_difficulties:
            raise ValidationError(f"Invalid difficulty. Valid difficulties: {', '.join(valid_difficulties)}")
        
        return difficulty


class SM2Validator:
    """Validator for SM-2 algorithm parameters"""
    
    @staticmethod
    def validate_quality(quality: int) -> int:
        """Validate SM-2 quality score"""
        if not isinstance(quality, int):
            raise ValidationError("Quality must be an integer")
        
        if not 0 <= quality <= 5:
            raise ValidationError("Quality must be between 0 and 5")
        
        return quality
    
    @staticmethod
    def validate_score(score: float) -> float:
        """Validate numerical score"""
        if not isinstance(score, (int, float)):
            raise ValidationError("Score must be a number")
        
        if not 0.0 <= score <= 1.0:
            raise ValidationError("Score must be between 0.0 and 1.0")
        
        return float(score)
    
    @staticmethod
    def validate_easiness_factor(easiness: float) -> float:
        """Validate easiness factor"""
        if not isinstance(easiness, (int, float)):
            raise ValidationError("Easiness factor must be a number")
        
        if not 1.3 <= easiness <= 3.0:
            raise ValidationError("Easiness factor must be between 1.3 and 3.0")
        
        return float(easiness)
