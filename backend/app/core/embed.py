import logging
from typing import List, Dict, Optional
import google.generativeai as genai
import numpy as np
from app.core.settings import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Handle text embeddings using Gemini text-embedding-004"""
    
    def __init__(self):
        self.model_name = settings.embed_model
        self.dimension = settings.faiss_dimension
    
    def get_embeddings(self, texts: List[str], api_key: str) -> List[List[float]]:
        """
        Get embeddings for a list of texts using Gemini API
        
        Args:
            texts: List of texts to embed
            api_key: User's Gemini API key
            
        Returns:
            List of embedding vectors
        """
        try:
            # Configure Gemini with user's API key
            genai.configure(api_key=api_key)
            
            # Process texts in batches to avoid rate limits
            batch_size = 10  # Adjust based on API limits
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = self._get_batch_embeddings(batch)
                all_embeddings.extend(batch_embeddings)
                
                # Small delay between batches
                if i + batch_size < len(texts):
                    import time
                    time.sleep(0.1)
            
            logger.info(f"Generated {len(all_embeddings)} embeddings")
            return all_embeddings
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    def _get_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a batch of texts"""
        try:
            # Use Gemini's embedding model
            model = genai.GenerativeModel(self.model_name)
            
            embeddings = []
            for text in texts:
                # Clean and prepare text
                clean_text = self._prepare_text_for_embedding(text)
                
                # Get embedding
                result = model.embed_content(clean_text)
                embedding = result['embedding']
                
                # Validate embedding
                if len(embedding) != self.dimension:
                    logger.warning(f"Unexpected embedding dimension: {len(embedding)}")
                
                embeddings.append(embedding)
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            raise
    
    def _prepare_text_for_embedding(self, text: str) -> str:
        """Prepare text for embedding by cleaning and truncating"""
        # Remove excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Truncate if too long (Gemini has token limits)
        max_tokens = 8000  # Conservative limit
        if len(text) > max_tokens * 4:  # Rough estimate: 4 chars per token
            text = text[:max_tokens * 4]
            logger.warning("Text truncated for embedding")
        
        return text
    
    def get_single_embedding(self, text: str, api_key: str) -> List[float]:
        """
        Get embedding for a single text
        
        Args:
            text: Text to embed
            api_key: User's Gemini API key
            
        Returns:
            Embedding vector
        """
        embeddings = self.get_embeddings([text], api_key)
        return embeddings[0] if embeddings else []
    
    def validate_embedding(self, embedding: List[float]) -> bool:
        """Validate that an embedding has the expected properties"""
        if not embedding:
            return False
        
        if len(embedding) != self.dimension:
            logger.warning(f"Embedding dimension mismatch: expected {self.dimension}, got {len(embedding)}")
            return False
        
        # Check for NaN or infinite values
        if any(not np.isfinite(val) for val in embedding):
            logger.warning("Embedding contains NaN or infinite values")
            return False
        
        return True
    
    def cosine_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Cosine similarity calculation failed: {e}")
            return 0.0
    
    def get_embedding_stats(self, embeddings: List[List[float]]) -> Dict:
        """Get statistics about a set of embeddings"""
        if not embeddings:
            return {}
        
        try:
            embeddings_array = np.array(embeddings)
            
            stats = {
                'count': len(embeddings),
                'dimension': len(embeddings[0]) if embeddings else 0,
                'mean_magnitude': float(np.mean([np.linalg.norm(emb) for emb in embeddings])),
                'std_magnitude': float(np.std([np.linalg.norm(emb) for emb in embeddings])),
                'min_magnitude': float(np.min([np.linalg.norm(emb) for emb in embeddings])),
                'max_magnitude': float(np.max([np.linalg.norm(emb) for emb in embeddings]))
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Embedding stats calculation failed: {e}")
            return {'count': len(embeddings), 'error': str(e)}
