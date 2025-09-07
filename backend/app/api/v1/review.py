from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import logging
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.models import Review, Flashcard, Collection
from app.core.sm2 import SpacedRepetitionService, SM2Parameters

logger = logging.getLogger(__name__)
router = APIRouter()


class ReviewScheduleRequest(BaseModel):
    user_id: str
    days_ahead: Optional[int] = 7


class ReviewStatsResponse(BaseModel):
    user_id: str
    total_due: int
    due_today: int
    due_this_week: int
    daily_schedule: dict
    estimated_time_minutes: int


@router.get("/review/schedule")
async def get_review_schedule(
    user_id: str,
    days_ahead: int = 7,
    db: Session = Depends(get_db)
):
    """
    Get review schedule for a user
    
    Args:
        user_id: User identifier
        days_ahead: Number of days to look ahead
        db: Database session
        
    Returns:
        Review schedule information
    """
    try:
        # Get all reviews for user
        reviews = db.query(Review).filter(Review.user_id == user_id).all()
        
        if not reviews:
            return {
                "user_id": user_id,
                "total_due": 0,
                "due_today": 0,
                "due_this_week": 0,
                "daily_schedule": {},
                "estimated_time_minutes": 0
            }
        
        # Calculate due cards
        current_time = datetime.utcnow()
        due_today = 0
        due_this_week = 0
        total_due = 0
        
        daily_schedule = {}
        
        # Initialize daily schedule
        for i in range(days_ahead):
            date = current_time + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            daily_schedule[date_str] = {
                "due_count": 0,
                "estimated_time": 0
            }
        
        # Process each review
        for review in reviews:
            if review.due_at <= current_time:
                total_due += 1
                
                # Check if due today
                if review.due_at.date() == current_time.date():
                    due_today += 1
                
                # Check if due this week
                week_end = current_time + timedelta(days=7)
                if review.due_at <= week_end:
                    due_this_week += 1
                
                # Add to daily schedule
                due_date_str = review.due_at.strftime('%Y-%m-%d')
                if due_date_str in daily_schedule:
                    daily_schedule[due_date_str]["due_count"] += 1
                    daily_schedule[due_date_str]["estimated_time"] += 2  # 2 minutes per card
        
        # Calculate total estimated time
        estimated_time_minutes = sum(day["estimated_time"] for day in daily_schedule.values())
        
        return {
            "user_id": user_id,
            "total_due": total_due,
            "due_today": due_today,
            "due_this_week": due_this_week,
            "daily_schedule": daily_schedule,
            "estimated_time_minutes": estimated_time_minutes
        }
        
    except Exception as e:
        logger.error(f"Failed to get review schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to get review schedule")


@router.get("/review/due")
async def get_due_cards(
    user_id: str,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get cards due for review
    
    Args:
        user_id: User identifier
        limit: Maximum number of cards to return
        db: Database session
        
    Returns:
        List of due cards with priority
    """
    try:
        # Get all reviews for user
        reviews = db.query(Review).filter(Review.user_id == user_id).all()
        
        if not reviews:
            return {"due_cards": []}
        
        # Use spaced repetition service to get due cards
        spaced_rep_service = SpacedRepetitionService()
        
        # Convert reviews to format expected by service
        review_data = []
        for review in reviews:
            review_data.append({
                "id": review.id,
                "flashcard_id": review.flashcard_id,
                "repetitions": review.repetitions,
                "interval_days": review.interval_days,
                "easiness_factor": review.easiness_factor,
                "due_at": review.due_at
            })
        
        # Get due cards
        due_cards = spaced_rep_service.get_due_cards(review_data)
        
        # Limit results
        due_cards = due_cards[:limit]
        
        # Get flashcard details
        flashcard_ids = [card["flashcard_id"] for card in due_cards]
        flashcards = db.query(Flashcard).filter(Flashcard.id.in_(flashcard_ids)).all()
        
        # Create flashcard lookup
        flashcard_lookup = {card.id: card for card in flashcards}
        
        # Format response
        formatted_cards = []
        for due_card in due_cards:
            flashcard = flashcard_lookup.get(due_card["flashcard_id"])
            if flashcard:
                formatted_cards.append({
                    "review_id": due_card["review_id"],
                    "flashcard_id": flashcard.id,
                    "question": flashcard.question,
                    "answer": flashcard.answer,
                    "difficulty": flashcard.difficulty,
                    "tags": flashcard.tags,
                    "priority": due_card["priority"],
                    "days_overdue": due_card["days_overdue"],
                    "sm2_stats": {
                        "repetitions": due_card["params"].repetitions,
                        "interval_days": due_card["params"].interval_days,
                        "easiness_factor": due_card["params"].easiness_factor,
                        "due_at": due_card["params"].due_at.isoformat()
                    }
                })
        
        return {
            "due_cards": formatted_cards,
            "total_due": len(formatted_cards)
        }
        
    except Exception as e:
        logger.error(f"Failed to get due cards: {e}")
        raise HTTPException(status_code=500, detail="Failed to get due cards")


@router.get("/review/stats/{user_id}")
async def get_review_stats(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get review statistics for a user
    
    Args:
        user_id: User identifier
        db: Database session
        
    Returns:
        Review statistics
    """
    try:
        # Get all reviews for user
        reviews = db.query(Review).filter(Review.user_id == user_id).all()
        
        if not reviews:
            return {
                "user_id": user_id,
                "total_cards": 0,
                "mastered_cards": 0,
                "learning_cards": 0,
                "new_cards": 0,
                "total_reviews": 0,
                "correct_reviews": 0,
                "accuracy_rate": 0.0,
                "average_easiness": 0.0,
                "longest_streak": 0
            }
        
        # Calculate statistics
        total_cards = len(reviews)
        mastered_cards = 0
        learning_cards = 0
        new_cards = 0
        total_reviews = 0
        correct_reviews = 0
        total_easiness = 0.0
        
        for review in reviews:
            total_reviews += review.review_count
            correct_reviews += review.correct_count
            total_easiness += review.easiness_factor
            
            # Categorize cards
            if review.repetitions >= 5 and review.easiness_factor >= 2.5:
                mastered_cards += 1
            elif review.repetitions >= 3 and review.easiness_factor >= 2.0:
                learning_cards += 1
            else:
                new_cards += 1
        
        # Calculate rates
        accuracy_rate = (correct_reviews / total_reviews * 100) if total_reviews > 0 else 0.0
        average_easiness = total_easiness / total_cards if total_cards > 0 else 0.0
        
        # Calculate streak (simplified - would need more complex logic for actual streaks)
        current_streak = 0
        longest_streak = 0
        
        # Sort reviews by last_reviewed_at
        sorted_reviews = sorted([r for r in reviews if r.last_reviewed_at], 
                              key=lambda x: x.last_reviewed_at, reverse=True)
        
        for review in sorted_reviews:
            if review.last_reviewed_at:
                days_since_review = (datetime.utcnow() - review.last_reviewed_at).days
                if days_since_review <= 1:  # Reviewed within last day
                    current_streak += 1
                else:
                    break
        
        longest_streak = current_streak  # Simplified calculation
        
        return {
            "user_id": user_id,
            "total_cards": total_cards,
            "mastered_cards": mastered_cards,
            "learning_cards": learning_cards,
            "new_cards": new_cards,
            "total_reviews": total_reviews,
            "correct_reviews": correct_reviews,
            "accuracy_rate": round(accuracy_rate, 2),
            "average_easiness": round(average_easiness, 2),
            "current_streak": current_streak,
            "longest_streak": longest_streak
        }
        
    except Exception as e:
        logger.error(f"Failed to get review stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get review stats")


@router.post("/review/reset/{flashcard_id}")
async def reset_review(
    flashcard_id: str,
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Reset review progress for a specific flashcard
    
    Args:
        flashcard_id: Flashcard ID to reset
        user_id: User identifier
        db: Database session
        
    Returns:
        Success confirmation
    """
    try:
        # Get review record
        review = db.query(Review).filter(
            Review.flashcard_id == flashcard_id,
            Review.user_id == user_id
        ).first()
        
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        # Reset to initial values
        review.repetitions = 0
        review.interval_days = 1
        review.easiness_factor = 2.5
        review.due_at = datetime.utcnow()
        review.review_count = 0
        review.correct_count = 0
        review.last_reviewed_at = None
        
        db.commit()
        
        logger.info(f"Reset review for flashcard {flashcard_id} and user {user_id}")
        
        return {
            "success": True,
            "message": "Review progress reset successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset review: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to reset review")
