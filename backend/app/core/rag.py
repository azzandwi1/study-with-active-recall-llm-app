import logging
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import faiss
from app.core.settings import settings
from app.core.embed import EmbeddingService

logger = logging.getLogger(__name__)


class FAISSIndex:
    """Handle FAISS vector index creation, storage, and retrieval"""
    
    def __init__(self, collection_id: str):
        self.collection_id = collection_id
        self.dimension = settings.faiss_dimension
        self.index_path = settings.faiss_dir / f"{collection_id}.index"
        self.metadata_path = settings.faiss_dir / f"{collection_id}.metadata"
        self.index = None
        self.metadata = []
        self.embedding_service = EmbeddingService()
    
    def create_index(self, embeddings: List[List[float]], chunk_metadata: List[Dict]) -> bool:
        """
        Create a new FAISS index with embeddings and metadata
        
        Args:
            embeddings: List of embedding vectors
            chunk_metadata: List of metadata for each chunk
            
        Returns:
            True if successful
        """
        try:
            if not embeddings:
                logger.warning("No embeddings provided for index creation")
                return False
            
            # Validate embeddings
            valid_embeddings = []
            valid_metadata = []
            
            for i, (embedding, metadata) in enumerate(zip(embeddings, chunk_metadata)):
                if self.embedding_service.validate_embedding(embedding):
                    valid_embeddings.append(embedding)
                    valid_metadata.append(metadata)
                else:
                    logger.warning(f"Skipping invalid embedding at index {i}")
            
            if not valid_embeddings:
                logger.error("No valid embeddings found")
                return False
            
            # Create FAISS index
            embeddings_array = np.array(valid_embeddings).astype('float32')
            
            # Use IndexFlatIP for cosine similarity (after normalization)
            self.index = faiss.IndexFlatIP(self.dimension)
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings_array)
            
            # Add embeddings to index
            self.index.add(embeddings_array)
            
            # Store metadata
            self.metadata = valid_metadata
            
            # Save to disk
            self._save_index()
            
            logger.info(f"Created FAISS index with {len(valid_embeddings)} vectors for collection {self.collection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create FAISS index: {e}")
            return False
    
    def load_index(self) -> bool:
        """Load existing FAISS index from disk"""
        try:
            if not self.index_path.exists() or not self.metadata_path.exists():
                logger.warning(f"Index files not found for collection {self.collection_id}")
                return False
            
            # Load FAISS index
            self.index = faiss.read_index(str(self.index_path))
            
            # Load metadata
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            
            logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors for collection {self.collection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            return False
    
    def add_embeddings(self, embeddings: List[List[float]], chunk_metadata: List[Dict]) -> bool:
        """
        Add new embeddings to existing index
        
        Args:
            embeddings: List of new embedding vectors
            chunk_metadata: List of metadata for new chunks
            
        Returns:
            True if successful
        """
        try:
            if self.index is None:
                logger.error("No index loaded. Call load_index() first.")
                return False
            
            # Validate and filter embeddings
            valid_embeddings = []
            valid_metadata = []
            
            for embedding, metadata in zip(embeddings, chunk_metadata):
                if self.embedding_service.validate_embedding(embedding):
                    valid_embeddings.append(embedding)
                    valid_metadata.append(metadata)
            
            if not valid_embeddings:
                logger.warning("No valid embeddings to add")
                return False
            
            # Prepare embeddings
            embeddings_array = np.array(valid_embeddings).astype('float32')
            faiss.normalize_L2(embeddings_array)
            
            # Add to index
            self.index.add(embeddings_array)
            
            # Update metadata
            self.metadata.extend(valid_metadata)
            
            # Save updated index
            self._save_index()
            
            logger.info(f"Added {len(valid_embeddings)} vectors to index for collection {self.collection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add embeddings to index: {e}")
            return False
    
    def search(self, query_embedding: List[float], k: int = 5) -> List[Dict]:
        """
        Search for similar vectors in the index
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of search results with metadata and scores
        """
        try:
            if self.index is None:
                logger.error("No index loaded. Call load_index() first.")
                return []
            
            if not self.embedding_service.validate_embedding(query_embedding):
                logger.error("Invalid query embedding")
                return []
            
            # Prepare query
            query_array = np.array([query_embedding]).astype('float32')
            faiss.normalize_L2(query_array)
            
            # Search
            scores, indices = self.index.search(query_array, min(k, self.index.ntotal))
            
            # Format results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.metadata):  # Valid index
                    result = {
                        'chunk_id': self.metadata[idx].get('chunk_id'),
                        'content': self.metadata[idx].get('content', ''),
                        'heading': self.metadata[idx].get('heading', ''),
                        'score': float(score),
                        'metadata': self.metadata[idx]
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """Get statistics about the index"""
        if self.index is None:
            return {'status': 'not_loaded'}
        
        return {
            'status': 'loaded',
            'collection_id': self.collection_id,
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'index_type': 'IndexFlatIP',
            'metadata_count': len(self.metadata)
        }
    
    def _save_index(self) -> bool:
        """Save index and metadata to disk"""
        try:
            # Ensure directory exists
            settings.faiss_dir.mkdir(parents=True, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            logger.info(f"Saved FAISS index for collection {self.collection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
            return False
    
    def delete_index(self) -> bool:
        """Delete index files from disk"""
        try:
            if self.index_path.exists():
                self.index_path.unlink()
            
            if self.metadata_path.exists():
                self.metadata_path.unlink()
            
            logger.info(f"Deleted FAISS index for collection {self.collection_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete FAISS index: {e}")
            return False


class RAGService:
    """Retrieval-Augmented Generation service using FAISS"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    def retrieve_relevant_chunks(self, query: str, collection_id: str, api_key: str, k: int = 5) -> List[Dict]:
        """
        Retrieve relevant chunks for a query using RAG
        
        Args:
            query: Search query
            collection_id: Collection to search in
            api_key: User's Gemini API key
            k: Number of chunks to retrieve
            
        Returns:
            List of relevant chunks with scores
        """
        try:
            # Get query embedding
            query_embedding = self.embedding_service.get_single_embedding(query, api_key)
            
            if not query_embedding:
                logger.error("Failed to generate query embedding")
                return []
            
            # Load index and search
            index = FAISSIndex(collection_id)
            if not index.load_index():
                logger.error(f"Failed to load index for collection {collection_id}")
                return []
            
            # Search for relevant chunks
            results = index.search(query_embedding, k)
            
            logger.info(f"Retrieved {len(results)} relevant chunks for query")
            return results
            
        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return []
    
    def create_context_from_chunks(self, chunks: List[Dict], max_tokens: int = 2000, per_chunk_max_chars: int = 2000) -> str:
        """
        Create context string from retrieved chunks
        
        Args:
            chunks: List of chunk results from search
            max_tokens: Maximum tokens for context
            
        Returns:
            Formatted context string
        """
        try:
            context_parts = []
            current_tokens = 0
            
            for chunk in chunks:
                # Format chunk content
                heading = chunk.get('heading', '')
                content = chunk.get('content', '')
                # Trim per-chunk length to avoid massive prompts
                if len(content) > per_chunk_max_chars:
                    content = content[:per_chunk_max_chars].rsplit(' ', 1)[0] + '...'
                score = chunk.get('score', 0.0)
                
                if heading:
                    chunk_text = f"## {heading}\n{content}\n"
                else:
                    chunk_text = f"{content}\n"
                
                # Estimate tokens (rough approximation)
                chunk_tokens = len(chunk_text.split()) * 1.3
                
                if current_tokens + chunk_tokens > max_tokens:
                    break
                
                context_parts.append(chunk_text)
                current_tokens += chunk_tokens
            
            context = "\n---\n".join(context_parts)
            return context
            
        except Exception as e:
            logger.error(f"Context creation failed: {e}")
            return ""
    
    def get_collection_stats(self, collection_id: str) -> Dict:
        """Get statistics for a collection's FAISS index"""
        try:
            index = FAISSIndex(collection_id)
            if index.load_index():
                return index.get_stats()
            else:
                return {'status': 'not_found'}
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {'status': 'error', 'error': str(e)}
