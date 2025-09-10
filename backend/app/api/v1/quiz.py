from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import uuid
import logging
from datetime import datetime
from app.core.database import get_db
from app.core.models import Collection, Flashcard, QuizSession, QuizQuestion, Review, Chunk
from app.core.sm2 import SpacedRepetitionService, SM2Parameters
from app.core.deps import get_api_key

logger = logging.getLogger(__name__)
router = APIRouter()


class QuizStartRequest(BaseModel):
    collection_id: str
    count: Optional[int] = 10
    strategy: Optional[str] = "mixed"  # mixed, weakest, new
    user_id: Optional[str] = "default_user"


class QuizCheckRequest(BaseModel):
    card_id: str
    user_answer: str
    context: Optional[str] = "strict"  # strict, lenient
    user_id: Optional[str] = "default_user"


class QuizQuestionResponse(BaseModel):
    card_id: str
    question: str
    difficulty: str
    tags: List[str]


@router.post("/quiz/start")
async def start_quiz(
    request: QuizStartRequest,
    db: Session = Depends(get_db)
):
    """
    Start a new quiz session
    
    Args:
        request: Quiz start request
        db: Database session
        
    Returns:
        Quiz session with questions
    """
    try:
        # Validate collection exists
        collection = db.query(Collection).filter(Collection.id == request.collection_id).first()
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        # Validate count
        if not 1 <= request.count <= 50:
            raise HTTPException(status_code=400, detail="Count must be between 1 and 50")
        
        # Get flashcards based on strategy
        flashcards = await _select_flashcards_for_quiz(
            db, request.collection_id, request.count, request.strategy, request.user_id
        )
        
        if not flashcards:
            raise HTTPException(status_code=400, detail="No flashcards available for quiz")
        
        # Create quiz session
        session = QuizSession(
            collection_id=request.collection_id,
            user_id=request.user_id,
            strategy=request.strategy,
            total_questions=len(flashcards)
        )
        db.add(session)
        db.flush()  # Get session ID
        
        # Create quiz questions
        questions = []
        for i, flashcard in enumerate(flashcards):
            question = QuizQuestion(
                session_id=session.id,
                flashcard_id=flashcard.id,
                question_index=i
            )
            questions.append(question)
            db.add(question)
        
        db.commit()
        
        logger.info(f"Started quiz session {session.id} with {len(flashcards)} questions")
        
        return {
            "session_id": session.id,
            "collection_id": request.collection_id,
            "total_questions": len(flashcards),
            "strategy": request.strategy,
            "questions": [
                {
                    "card_id": card.id,
                    "question": card.question,
                    "difficulty": card.difficulty,
                    "tags": card.tags
                }
                for card in flashcards
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quiz start failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Quiz start failed: {str(e)}")


@router.post("/quiz/check")
async def check_answer(
    request: QuizCheckRequest,
    db: Session = Depends(get_db),
    api_key: str = Depends(get_api_key)
):
    """
    Check a quiz answer and provide feedback
    
    Args:
        request: Quiz check request
        db: Database session
        api_key: User's Gemini API key
        
    Returns:
        Grading result with feedback
    """
    try:
        # Get flashcard
        flashcard = db.query(Flashcard).filter(Flashcard.id == request.card_id).first()
        if not flashcard:
            raise HTTPException(status_code=404, detail="Flashcard not found")
        
        # Grade the answer
        from app.core.grading import GradingService
        grading_service = GradingService()
        
        # Get context for grading if available
        context = ""
        if flashcard.source_chunk_ids:
            # Get chunk content for context
            chunks = db.query(Chunk).filter(Chunk.id.in_(flashcard.source_chunk_ids)).all()
            context = " ".join([chunk.content for chunk in chunks[:3]])  # Use first 3 chunks
        
        # Grade the answer
        grading_result = grading_service.grade_answer(
            question=flashcard.question,
            ideal_answer=flashcard.answer,
            user_answer=request.user_answer,
            context=context,
            api_key=api_key
        )
        
        # Update SM-2 parameters
        spaced_rep_service = SpacedRepetitionService()
        
        # Get or create review record
        review = db.query(Review).filter(
            Review.flashcard_id == request.card_id,
            Review.user_id == request.user_id
        ).first()
        
        if not review:
            # Create new review
            review = Review(
                flashcard_id=request.card_id,
                user_id=request.user_id,
                due_at=datetime.utcnow()
            )
            db.add(review)
            db.flush()
        
        # Update review with SM-2
        current_params = SM2Parameters(
            repetitions=review.repetitions,
            interval_days=review.interval_days,
            easiness_factor=review.easiness_factor,
            due_at=review.due_at
        )
        
        new_params = spaced_rep_service.update_review_after_answer(current_params, grading_result.score)
        
        # Update review record
        review.repetitions = new_params.repetitions
        review.interval_days = new_params.interval_days
        review.easiness_factor = new_params.easiness_factor
        review.due_at = new_params.due_at
        review.last_reviewed_at = datetime.utcnow()
        review.review_count += 1
        
        if grading_result.verdict == "correct":
            review.correct_count += 1
        
        db.commit()
        
        # Generate Socratic follow-up if needed
        socratic_question = None
        if grading_result.verdict in ["partial", "incorrect"]:
            try:
                socratic_result = grading_service.generate_socratic_followup(
                    question=flashcard.question,
                    user_answer=request.user_answer,
                    feedback=grading_result.feedback,
                    verdict=grading_result.verdict,
                    api_key=api_key
                )
                socratic_question = socratic_result.socratic_question
            except Exception as e:
                logger.warning(f"Failed to generate Socratic follow-up: {e}")
        
        logger.info(f"Graded answer for flashcard {request.card_id}: {grading_result.verdict}")
        
        return {
            "card_id": request.card_id,
            "score": grading_result.score,
            "verdict": grading_result.verdict,
            "feedback": grading_result.feedback,
            "ideal_answer": grading_result.ideal_answer,
            "socratic_question": socratic_question,
            "sm2_stats": {
                "repetitions": new_params.repetitions,
                "interval_days": new_params.interval_days,
                "easiness_factor": new_params.easiness_factor,
                "next_review": new_params.due_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quiz check failed: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Quiz check failed: {str(e)}")


@router.get("/quiz/sessions/{session_id}")
async def get_quiz_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Get quiz session details
    
    Args:
        session_id: Quiz session ID
        db: Database session
        
    Returns:
        Quiz session details
    """
    try:
        session = db.query(QuizSession).filter(QuizSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Quiz session not found")
        
        # Get questions
        questions = db.query(QuizQuestion).filter(QuizQuestion.session_id == session_id).all()
        
        return {
            "session_id": session.id,
            "collection_id": session.collection_id,
            "user_id": session.user_id,
            "strategy": session.strategy,
            "total_questions": session.total_questions,
            "completed_questions": session.completed_questions,
            "correct_answers": session.correct_answers,
            "started_at": session.started_at.isoformat(),
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            "questions": [
                {
                    "id": q.id,
                    "flashcard_id": q.flashcard_id,
                    "question_index": q.question_index,
                    "user_answer": q.user_answer,
                    "is_correct": q.is_correct,
                    "score": q.score,
                    "answered_at": q.answered_at.isoformat() if q.answered_at else None
                }
                for q in questions
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get quiz session: {e}")
        raise HTTPException(status_code=500, detail="Failed to get quiz session")


async def _select_flashcards_for_quiz(
    db: Session, collection_id: str, count: int, strategy: str, user_id: str
) -> List[Flashcard]:
    """Select flashcards for quiz based on strategy"""
    try:
        # Get all flashcards in collection
        all_flashcards = db.query(Flashcard).filter(Flashcard.collection_id == collection_id).all()
        
        if not all_flashcards:
            return []
        
        if strategy == "new":
            # Select flashcards with no reviews or low repetitions
            new_flashcards = []
            for card in all_flashcards:
                review = db.query(Review).filter(
                    Review.flashcard_id == card.id,
                    Review.user_id == user_id
                ).first()
                
                if not review or review.repetitions < 2:
                    new_flashcards.append(card)
            
            return new_flashcards[:count]
        
        elif strategy == "weakest":
            # Select flashcards with lowest easiness factor
            weakest_flashcards = []
            for card in all_flashcards:
                review = db.query(Review).filter(
                    Review.flashcard_id == card.id,
                    Review.user_id == user_id
                ).first()
                
                if review:
                    weakest_flashcards.append((card, review.easiness_factor))
                else:
                    weakest_flashcards.append((card, 2.5))  # Default easiness
            
            # Sort by easiness factor (lowest first)
            weakest_flashcards.sort(key=lambda x: x[1])
            return [card for card, _ in weakest_flashcards[:count]]
        
        else:  # mixed strategy
            # Mix of new, weak, and due cards
            mixed_flashcards = []
            
            # Get due cards
            due_cards = []
            for card in all_flashcards:
                review = db.query(Review).filter(
                    Review.flashcard_id == card.id,
                    Review.user_id == user_id
                ).first()
                
                if review and review.due_at <= datetime.utcnow():
                    due_cards.append(card)
            
            # Add due cards first
            mixed_flashcards.extend(due_cards[:count//2])
            
            # Add remaining from all flashcards
            remaining_count = count - len(mixed_flashcards)
            other_cards = [card for card in all_flashcards if card not in mixed_flashcards]
            mixed_flashcards.extend(other_cards[:remaining_count])
            
            return mixed_flashcards[:count]
        
    except Exception as e:
        logger.error(f"Failed to select flashcards for quiz: {e}")
        return []
