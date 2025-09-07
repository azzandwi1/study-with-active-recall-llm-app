import pytest
import tempfile
import os
from pathlib import Path
from app.core.settings import settings
from app.core.chunk import TextChunker
from app.core.embed import EmbeddingService
from app.core.sm2 import SM2Algorithm, SM2Parameters
from datetime import datetime, timedelta


class TestTextChunker:
    """Test text chunking functionality"""
    
    def test_basic_chunking(self):
        """Test basic text chunking"""
        chunker = TextChunker()
        text = "This is a test document. " * 100  # Create long text
        
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) > 0
        assert all('content' in chunk for chunk in chunks)
        assert all('token_count' in chunk for chunk in chunks)
    
    def test_heading_detection(self):
        """Test heading detection in text"""
        chunker = TextChunker()
        text = """
        # Main Title
        This is the main content.
        
        ## Subtitle
        This is subtitle content.
        
        ### Another Level
        More content here.
        """
        
        chunks = chunker.chunk_text(text)
        
        # Should detect headings
        assert any('heading' in chunk for chunk in chunks)
    
    def test_token_counting(self):
        """Test token counting"""
        chunker = TextChunker()
        text = "Hello world, this is a test."
        
        token_count = chunker.count_tokens(text)
        assert token_count > 0
        assert isinstance(token_count, int)


class TestSM2Algorithm:
    """Test SM-2 spaced repetition algorithm"""
    
    def test_initial_parameters(self):
        """Test initial SM-2 parameters"""
        sm2 = SM2Algorithm()
        params = SM2Parameters()
        
        assert params.repetitions == 0
        assert params.interval_days == 1
        assert params.easiness_factor == 2.5
    
    def test_quality_conversion(self):
        """Test score to quality conversion"""
        sm2 = SM2Algorithm()
        
        assert sm2.quality_from_score(0.95) == 5  # Perfect
        assert sm2.quality_from_score(0.85) == 4  # Good
        assert sm2.quality_from_score(0.65) == 3  # OK
        assert sm2.quality_from_score(0.35) == 2  # Poor
        assert sm2.quality_from_score(0.15) == 1  # Very poor
        assert sm2.quality_from_score(0.05) == 0  # Blackout
    
    def test_review_calculation(self):
        """Test review parameter calculation"""
        sm2 = SM2Algorithm()
        params = SM2Parameters()
        
        # Test correct answer (quality 5)
        new_params = sm2.calculate_next_review(5, params)
        
        assert new_params.repetitions == 1
        assert new_params.interval_days == 1
        assert new_params.easiness_factor > params.easiness_factor
    
    def test_reset_on_poor_performance(self):
        """Test reset when quality < 3"""
        sm2 = SM2Algorithm()
        params = SM2Parameters(repetitions=5, interval_days=30, easiness_factor=2.8)
        
        # Test poor answer (quality 2)
        new_params = sm2.calculate_next_review(2, params)
        
        assert new_params.repetitions == 0
        assert new_params.interval_days == 1
        assert new_params.easiness_factor == params.easiness_factor  # Should not change


class TestEmbeddingService:
    """Test embedding service functionality"""
    
    def test_embedding_validation(self):
        """Test embedding validation"""
        service = EmbeddingService()
        
        # Valid embedding
        valid_embedding = [0.1] * 768
        assert service.validate_embedding(valid_embedding) == True
        
        # Invalid embedding (wrong dimension)
        invalid_embedding = [0.1] * 100
        assert service.validate_embedding(invalid_embedding) == False
        
        # Invalid embedding (empty)
        assert service.validate_embedding([]) == False
    
    def test_cosine_similarity(self):
        """Test cosine similarity calculation"""
        service = EmbeddingService()
        
        # Identical vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = service.cosine_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 0.001
        
        # Orthogonal vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]
        similarity = service.cosine_similarity(vec1, vec2)
        assert abs(similarity - 0.0) < 0.001


class TestSettings:
    """Test settings configuration"""
    
    def test_settings_initialization(self):
        """Test that settings are properly initialized"""
        assert settings.data_dir is not None
        assert settings.uploads_dir is not None
        assert settings.faiss_dir is not None
        assert settings.max_upload_mb > 0
        assert settings.chunk_size > 0
        assert settings.chunk_overlap >= 0
    
    def test_directory_creation(self):
        """Test that directories are created"""
        assert settings.data_dir.exists()
        assert settings.uploads_dir.exists()
        assert settings.faiss_dir.exists()


if __name__ == "__main__":
    pytest.main([__file__])
