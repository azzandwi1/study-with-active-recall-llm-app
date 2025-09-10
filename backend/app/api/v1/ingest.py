from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import logging
from pathlib import Path
from app.core.database import get_db
from app.core.models import Collection, Document, Chunk
from app.core.settings import settings
from app.core.pdf import PDFProcessor
from app.core.web import WebScraper
from app.core.chunk import TextChunker
from app.core.embed import EmbeddingService
from app.core.rag import FAISSIndex
from app.core.deps import get_api_key

logger = logging.getLogger(__name__)
router = APIRouter()


class IngestRequest:
    """Request model for content ingestion"""
    def __init__(self, source_type: str, collection_id: Optional[str] = None, 
                 collection_name: Optional[str] = None, url: Optional[str] = None, 
                 text: Optional[str] = None):
        self.source_type = source_type
        self.collection_id = collection_id
        self.collection_name = collection_name
        self.url = url
        self.text = text


@router.post("/ingest")
async def ingest_content(
    type: str = Form(...),  # Frontend sends 'type'
    collection_id: Optional[str] = Form(None),
    collection_name: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    content: Optional[str] = Form(None),  # Frontend sends 'content' for text/url
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Ingest content from various sources (PDF, URL, text)
    
    Args:
        type: Type of source ('pdf', 'url', 'text')
        collection_id: Existing collection ID (optional)
        collection_name: Name for new collection (optional)
        url: URL to scrape (for 'url' type)
        text: Text content (for 'text' type)
        content: Content from frontend (for 'url' or 'text' type)
        file: Uploaded file (for 'pdf' type)
        db: Database session
        api_key: User's Gemini API key
        
    Returns:
        Ingest result with collection info and processing details
    """
    try:
        # Validate source type
        if type not in ['pdf', 'url', 'text']:
            raise HTTPException(status_code=400, detail="Invalid type. Must be 'pdf', 'url', or 'text'")
        
        # Get or create collection
        collection = await _get_or_create_collection(db, collection_id, collection_name)
        
        # Process content based on source type
        if type == 'pdf':
            if not file:
                raise HTTPException(status_code=400, detail="File is required for PDF ingestion")
            content, metadata = await _process_pdf(file)
        elif type == 'url':
            # Use 'content' field from frontend for URL
            url_to_process = content or url
            if not url_to_process:
                raise HTTPException(status_code=400, detail="URL is required for URL ingestion")
            content, metadata = await _process_url(url_to_process)
        elif type == 'text':
            # Use 'content' field from frontend for text
            text_to_process = content or text
            if not text_to_process:
                raise HTTPException(status_code=400, detail="Text content is required for text ingestion")
            content, metadata = await _process_text(text_to_process)
        
        # Create document record
        document = Document(
            collection_id=collection.id,
            source_type=type,
            source_url=url_to_process if type == 'url' else None,
            filename=file.filename if file else None,
            title=metadata.get('title', 'Untitled'),
            content=content,
            meta=metadata,
            word_count=metadata.get('word_count', 0)
        )
        db.add(document)
        db.flush()  # Get document ID
        
        # Chunk the content
        chunker = TextChunker()
        chunks_data = chunker.chunk_text(content, metadata)
        
        # Generate embeddings
        embedding_service = EmbeddingService()
        chunk_texts = [chunk['content'] for chunk in chunks_data]
        embeddings = embedding_service.get_embeddings(chunk_texts, api_key)
        
        # Create chunk records
        chunks = []
        for i, (chunk_data, embedding) in enumerate(zip(chunks_data, embeddings)):
            chunk = Chunk(
                document_id=document.id,
                chunk_index=i,
                content=chunk_data['content'],
                token_count=chunk_data['token_count'],
                embedding_vector=embedding,
                meta={
                    'heading': chunk_data.get('heading', ''),
                    'level': chunk_data.get('level', 0),
                    **chunk_data.get('metadata', {})
                }
            )
            chunks.append(chunk)
            db.add(chunk)
        
        # Create FAISS index
        faiss_index = FAISSIndex(collection.id)
        chunk_metadata = [
            {
                'chunk_id': chunk.id,
                'content': chunk.content,
                'heading': (chunk.meta or {}).get('heading', ''),
                'document_id': document.id
            }
            for chunk in chunks
        ]
        
        success = faiss_index.create_index(embeddings, chunk_metadata)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create vector index")
        
        # Commit all changes
        db.commit()
        
        logger.info(f"Successfully ingested {type} content into collection {collection.id}")
        
        return {
            "success": True,
            "collection_id": collection.id,
            "document_id": document.id,
            "n_chunks": len(chunks),
            "word_count": document.word_count,
            "processing_time": metadata.get('processing_time', 0),
            "extraction_method": metadata.get('extraction_method', 'unknown')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ingest failed: {str(e)}")


async def _get_or_create_collection(db: Session, collection_id: Optional[str], 
                                  collection_name: Optional[str]) -> Collection:
    """Get existing collection or create new one"""
    if collection_id:
        collection = db.query(Collection).filter(Collection.id == collection_id).first()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        return collection
    else:
        # Create new collection
        collection = Collection(
            name=collection_name or f"Collection {uuid.uuid4().hex[:8]}",
            description="Auto-generated collection"
        )
        db.add(collection)
        db.flush()
        return collection


async def _process_pdf(file: UploadFile) -> tuple[str, dict]:
    """Process uploaded PDF file"""
    try:
        # Validate file
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        # Check file size
        content = await file.read()
        if len(content) > settings.max_upload_bytes:
            raise HTTPException(status_code=400, detail=f"File too large. Max size: {settings.max_upload_mb}MB")
        
        # Save file temporarily
        temp_path = settings.uploads_dir / f"temp_{uuid.uuid4().hex}.pdf"
        temp_path.write_bytes(content)
        
        try:
            # Process PDF
            pdf_processor = PDFProcessor()
            if not pdf_processor.validate_pdf(temp_path):
                raise HTTPException(status_code=400, detail="Invalid or corrupted PDF file")
            
            text, metadata = pdf_processor.extract_text(temp_path)
            
            if not text.strip():
                raise HTTPException(status_code=400, detail="No text could be extracted from PDF")
            
            metadata['filename'] = file.filename
            metadata['file_size'] = len(content)
            
            return text, metadata
            
        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {str(e)}")


async def _process_url(url: str) -> tuple[str, dict]:
    """Process URL content"""
    try:
        web_scraper = WebScraper()
        text, metadata = web_scraper.extract_content(url)
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No content could be extracted from URL")
        
        return text, metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"URL processing failed: {str(e)}")


async def _process_text(text: str) -> tuple[str, dict]:
    """Process direct text input"""
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="Text content cannot be empty")
        
        metadata = {
            'source_type': 'text',
            'title': 'Direct Text Input',
            'word_count': len(text.split()),
            'extraction_method': 'direct'
        }
        
        return text, metadata
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Text processing failed: {str(e)}")


@router.get("/ingest/collections")
async def list_collections(db: Session = Depends(get_db)):
    """List all collections"""
    try:
        collections = db.query(Collection).all()
        return {
            "collections": [
                {
                    "id": col.id,
                    "name": col.name,
                    "description": col.description,
                    "created_at": col.created_at.isoformat(),
                    "document_count": len(col.documents)
                }
                for col in collections
            ]
        }
    except Exception as e:
        logger.error(f"Failed to list collections: {e}")
        raise HTTPException(status_code=500, detail="Failed to list collections")


@router.get("/ingest/collections/{collection_id}")
async def get_collection(collection_id: str, db: Session = Depends(get_db)):
    """Get collection details"""
    try:
        collection = db.query(Collection).filter(Collection.id == collection_id).first()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        return {
            "id": collection.id,
            "name": collection.name,
            "description": collection.description,
            "created_at": collection.created_at.isoformat(),
            "documents": [
                {
                    "id": doc.id,
                    "source_type": doc.source_type,
                    "title": doc.title,
                    "word_count": doc.word_count,
                    "created_at": doc.created_at.isoformat()
                }
                for doc in collection.documents
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collection: {e}")
        raise HTTPException(status_code=500, detail="Failed to get collection")
