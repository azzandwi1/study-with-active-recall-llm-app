from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import logging
from app.core.database import get_db
from app.core.models import Collection, Flashcard, Chunk
from app.core.rag import RAGService
from app.core.llm import LLMService
from app.core.prompts import PromptBuilder, FlashcardStyle
from app.core.deps import get_api_key

logger = logging.getLogger(__name__)
router = APIRouter()


class FlashcardGenerationRequest(BaseModel):
    collection_id: str
    n_cards: Optional[int] = 5
    style: Optional[str] = "basic"  # basic, cloze, concept


class FlashcardResponse(BaseModel):
    id: str
    question: str
    answer: str
    difficulty: str
    tags: List[str]
    style: str


@router.post("/generate/flashcards")
async def generate_flashcards(
    request: FlashcardGenerationRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Generate flashcards from collection content using RAG
    
    Args:
        request: Flashcard generation request
        db: Database session
        api_key: User's Gemini API key
        
    Returns:
        List of generated flashcards
    """
    try:
        # Validate collection exists
        collection = db.query(Collection).filter(Collection.id == request.collection_id).first()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Validate style
        try:
            style = FlashcardStyle(request.style)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid style. Must be 'basic', 'cloze', or 'concept'")
        
        # Validate number of cards
        if not 1 <= request.n_cards <= 20:
            raise HTTPException(status_code=400, detail="Number of cards must be between 1 and 20")
        
        # Get relevant chunks using RAG
        rag_service = RAGService()
        
        # Use collection name and description as query for RAG
        query = f"{collection.name} {collection.description or ''}"
        relevant_chunks = rag_service.retrieve_relevant_chunks(
            query=query,
            collection_id=request.collection_id,
            api_key=api_key,
            k=min(request.n_cards * 2, 10)  # Get more chunks than needed
        )
        
        if not relevant_chunks:
            raise HTTPException(status_code=400, detail="No relevant content found in collection")
        
        # Create context from chunks
        context = rag_service.create_context_from_chunks(relevant_chunks, max_tokens=3000)
        
        # Generate flashcards using LLM
        llm_service = LLMService()
        prompt = PromptBuilder.build_flashcard_prompt(
            context=context,
            n_cards=request.n_cards,
            style=style
        )
        
        # Get structured response
        flashcard_data = llm_service.generate_structured_content(prompt, api_key, "JSON")
        
        if not isinstance(flashcard_data, list):
            raise HTTPException(status_code=500, detail="Invalid flashcard generation response")
        
        # Create flashcard records
        created_flashcards = []
        source_chunk_ids = [chunk['chunk_id'] for chunk in relevant_chunks]
        
        for i, card_data in enumerate(flashcard_data[:request.n_cards]):
            try:
                # Validate required fields
                if not all(key in card_data for key in ['question', 'answer', 'difficulty']):
                    logger.warning(f"Skipping invalid flashcard data: {card_data}")
                    continue
                
                # Create flashcard
                flashcard = Flashcard(
                    collection_id=request.collection_id,
                    question=card_data['question'],
                    answer=card_data['answer'],
                    difficulty=card_data['difficulty'],
                    tags=card_data.get('tags', []),
                    style=request.style,
                    source_chunk_ids=source_chunk_ids
                )
                
                db.add(flashcard)
                db.flush()  # Get ID
                
                created_flashcards.append({
                    "id": flashcard.id,
                    "question": flashcard.question,
                    "answer": flashcard.answer,
                    "difficulty": flashcard.difficulty,
                    "tags": flashcard.tags,
                    "style": flashcard.style
                })
                
            except Exception as e:
                logger.warning(f"Failed to create flashcard {i}: {e}")
                continue
        
        if not created_flashcards:
            raise HTTPException(status_code=500, detail="Failed to generate any valid flashcards")
        
        db.commit()
        
        logger.info(f"Generated {len(created_flashcards)} flashcards for collection {request.collection_id}")
        
        return {
            "success": True,
            "flashcards": created_flashcards,
            "collection_id": request.collection_id,
            "generated_count": len(created_flashcards)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Flashcard generation failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Flashcard generation failed: {str(e)}")


@router.get("/generate/flashcards/{collection_id}")
async def get_flashcards(
    collection_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all flashcards for a collection
    
    Args:
        collection_id: Collection ID
        db: Database session
        
    Returns:
        List of flashcards in the collection
    """
    try:
        # Validate collection exists
        collection = db.query(Collection).filter(Collection.id == collection_id).first()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Get flashcards
        flashcards = db.query(Flashcard).filter(Flashcard.collection_id == collection_id).all()
        
        return {
            "collection_id": collection_id,
            "flashcards": [
                {
                    "id": card.id,
                    "question": card.question,
                    "answer": card.answer,
                    "difficulty": card.difficulty,
                    "tags": card.tags,
                    "style": card.style,
                    "created_at": card.created_at.isoformat()
                }
                for card in flashcards
            ],
            "total_count": len(flashcards)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get flashcards: {e}")
        raise HTTPException(status_code=500, detail="Failed to get flashcards")


@router.delete("/generate/flashcards/{flashcard_id}")
async def delete_flashcard(
    flashcard_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a specific flashcard
    
    Args:
        flashcard_id: Flashcard ID to delete
        db: Database session
        
    Returns:
        Success confirmation
    """
    try:
        flashcard = db.query(Flashcard).filter(Flashcard.id == flashcard_id).first()
        if not flashcard:
            raise HTTPException(status_code=404, detail="Flashcard not found")
        
        db.delete(flashcard)
        db.commit()
        
        logger.info(f"Deleted flashcard {flashcard_id}")
        
        return {
            "success": True,
            "message": "Flashcard deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete flashcard: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete flashcard")


@router.get("/generate/collections/{collection_id}/stats")
async def get_collection_stats(
    collection_id: str,
    db: Session = Depends(get_db)
):
    """
    Get statistics for a collection
    
    Args:
        collection_id: Collection ID
        db: Database session
        
    Returns:
        Collection statistics
    """
    try:
        # Validate collection exists
        collection = db.query(Collection).filter(Collection.id == collection_id).first()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Get statistics
        total_documents = len(collection.documents)
        total_flashcards = len(collection.flashcards)
        total_chunks = sum(len(doc.chunks) for doc in collection.documents)
        
        # Difficulty distribution
        difficulty_counts = {}
        for card in collection.flashcards:
            difficulty_counts[card.difficulty] = difficulty_counts.get(card.difficulty, 0) + 1
        
        return {
            "collection_id": collection_id,
            "collection_name": collection.name,
            "total_documents": total_documents,
            "total_flashcards": total_flashcards,
            "total_chunks": total_chunks,
            "difficulty_distribution": difficulty_counts,
            "created_at": collection.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get collection stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get collection stats")
