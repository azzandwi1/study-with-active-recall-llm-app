import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SM2Parameters:
    """SM-2 algorithm parameters for spaced repetition"""
    repetitions: int = 0
    interval_days: int = 1
    easiness_factor: float = 2.5
    due_at: datetime = None
    
    def __post_init__(self):
        if self.due_at is None:
            self.due_at = datetime.utcnow()


class SM2Algorithm:
    """
    SuperMemo 2 (SM-2) algorithm implementation for spaced repetition
    
    The SM-2 algorithm determines when to review flashcards based on:
    - Number of repetitions
    - Quality of recall (0-5 scale)
    - Easiness factor (how easy the card is to remember)
    - Interval between reviews
    """
    
    def __init__(self):
        self.min_easiness = 1.3
        self.max_easiness = 3.0
        self.initial_interval = 1
        self.initial_easiness = 2.5
    
    def calculate_next_review(self, quality: int, current_params: SM2Parameters) -> SM2Parameters:
        """
        Calculate next review parameters based on SM-2 algorithm
        
        Args:
            quality: Quality of recall (0-5 scale)
                0: Complete blackout
                1: Incorrect response; correct one remembered
                2: Incorrect response; where correct one seemed easy to recall
                3: Correct response; required serious thought
                4: Correct response; after hesitation
                5: Perfect response
            current_params: Current SM-2 parameters
            
        Returns:
            Updated SM2Parameters for next review
        """
        try:
            # Validate quality input
            if not 0 <= quality <= 5:
                raise ValueError(f"Quality must be between 0 and 5, got {quality}")
            
            # If quality < 3, reset repetitions and start over
            if quality < 3:
                return SM2Parameters(
                    repetitions=0,
                    interval_days=self.initial_interval,
                    easiness_factor=current_params.easiness_factor,
                    due_at=datetime.utcnow() + timedelta(days=self.initial_interval)
                )
            
            # Update easiness factor
            new_easiness = self._calculate_easiness_factor(quality, current_params.easiness_factor)
            
            # Update repetitions
            new_repetitions = current_params.repetitions + 1
            
            # Calculate new interval
            if new_repetitions == 1:
                new_interval = 1
            elif new_repetitions == 2:
                new_interval = 6
            else:
                new_interval = int(current_params.interval_days * new_easiness)
            
            # Calculate next due date
            next_due = datetime.utcnow() + timedelta(days=new_interval)
            
            return SM2Parameters(
                repetitions=new_repetitions,
                interval_days=new_interval,
                easiness_factor=new_easiness,
                due_at=next_due
            )
            
        except Exception as e:
            logger.error(f"SM-2 calculation failed: {e}")
            # Return safe fallback
            return SM2Parameters(
                repetitions=0,
                interval_days=1,
                easiness_factor=self.initial_easiness,
                due_at=datetime.utcnow() + timedelta(days=1)
            )
    
    def _calculate_easiness_factor(self, quality: int, current_easiness: float) -> float:
        """
        Calculate new easiness factor based on quality
        
        Args:
            quality: Quality of recall (0-5)
            current_easiness: Current easiness factor
            
        Returns:
            New easiness factor
        """
        # SM-2 easiness factor formula
        new_easiness = current_easiness + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        
        # Ensure easiness stays within bounds
        new_easiness = max(self.min_easiness, min(self.max_easiness, new_easiness))
        
        return round(new_easiness, 2)
    
    def quality_from_score(self, score: float) -> int:
        """
        Convert numerical score (0.0-1.0) to SM-2 quality (0-5)
        
        Args:
            score: Numerical score between 0.0 and 1.0
            
        Returns:
            SM-2 quality score (0-5)
        """
        if score >= 0.9:
            return 5  # Perfect response
        elif score >= 0.8:
            return 4  # Correct response; after hesitation
        elif score >= 0.6:
            return 3  # Correct response; required serious thought
        elif score >= 0.4:
            return 2  # Incorrect response; correct one seemed easy to recall
        elif score >= 0.2:
            return 1  # Incorrect response; correct one remembered
        else:
            return 0  # Complete blackout
    
    def get_review_priority(self, params: SM2Parameters, overdue_days: int = 0) -> float:
        """
        Calculate review priority for scheduling
        
        Args:
            params: SM-2 parameters
            overdue_days: How many days overdue the review is
            
        Returns:
            Priority score (higher = more urgent)
        """
        try:
            # Base priority from repetitions (fewer repetitions = higher priority)
            repetition_priority = 1.0 / max(params.repetitions + 1, 1)
            
            # Overdue penalty
            overdue_penalty = 1.0 + (overdue_days * 0.1)
            
            # Easiness factor (lower easiness = higher priority)
            easiness_priority = 1.0 / max(params.easiness_factor, 0.1)
            
            # Combine factors
            priority = repetition_priority * overdue_penalty * easiness_priority
            
            return round(priority, 3)
            
        except Exception as e:
            logger.error(f"Priority calculation failed: {e}")
            return 1.0
    
    def is_due_for_review(self, params: SM2Parameters, current_time: Optional[datetime] = None) -> bool:
        """
        Check if a card is due for review
        
        Args:
            params: SM-2 parameters
            current_time: Current time (defaults to now)
            
        Returns:
            True if card is due for review
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        return current_time >= params.due_at
    
    def get_days_until_due(self, params: SM2Parameters, current_time: Optional[datetime] = None) -> int:
        """
        Get number of days until next review
        
        Args:
            params: SM-2 parameters
            current_time: Current time (defaults to now)
            
        Returns:
            Days until due (negative if overdue)
        """
        if current_time is None:
            current_time = datetime.utcnow()
        
        delta = params.due_at - current_time
        return delta.days
    
    def get_review_statistics(self, params: SM2Parameters) -> Dict[str, Any]:
        """
        Get statistics about the current review state
        
        Args:
            params: SM-2 parameters
            
        Returns:
            Dictionary with review statistics
        """
        current_time = datetime.utcnow()
        days_until_due = self.get_days_until_due(params, current_time)
        is_due = self.is_due_for_review(params, current_time)
        priority = self.get_review_priority(params, max(0, -days_until_due))
        
        return {
            'repetitions': params.repetitions,
            'interval_days': params.interval_days,
            'easiness_factor': params.easiness_factor,
            'due_at': params.due_at.isoformat(),
            'is_due': is_due,
            'days_until_due': days_until_due,
            'priority': priority,
            'mastery_level': self._get_mastery_level(params)
        }
    
    def _get_mastery_level(self, params: SM2Parameters) -> str:
        """
        Determine mastery level based on SM-2 parameters
        
        Args:
            params: SM-2 parameters
            
        Returns:
            Mastery level string
        """
        if params.repetitions >= 5 and params.easiness_factor >= 2.5:
            return "mastered"
        elif params.repetitions >= 3 and params.easiness_factor >= 2.0:
            return "learning"
        elif params.repetitions >= 1:
            return "new"
        else:
            return "unseen"


class SpacedRepetitionService:
    """Service for managing spaced repetition using SM-2 algorithm"""
    
    def __init__(self):
        self.sm2 = SM2Algorithm()
    
    def update_review_after_answer(self, current_params: SM2Parameters, 
                                 score: float) -> SM2Parameters:
        """
        Update review parameters after a user answers a question
        
        Args:
            current_params: Current SM-2 parameters
            score: Answer score (0.0-1.0)
            
        Returns:
            Updated SM-2 parameters
        """
        try:
            # Convert score to SM-2 quality
            quality = self.sm2.quality_from_score(score)
            
            # Calculate new parameters
            new_params = self.sm2.calculate_next_review(quality, current_params)
            
            logger.info(f"Updated review parameters: quality={quality}, "
                       f"repetitions={new_params.repetitions}, "
                       f"interval={new_params.interval_days}, "
                       f"easiness={new_params.easiness_factor}")
            
            return new_params
            
        except Exception as e:
            logger.error(f"Review update failed: {e}")
            return current_params
    
    def get_due_cards(self, all_reviews: list, current_time: Optional[datetime] = None) -> list:
        """
        Get cards that are due for review
        
        Args:
            all_reviews: List of review objects with SM-2 parameters
            current_time: Current time (defaults to now)
            
        Returns:
            List of due cards sorted by priority
        """
        try:
            due_cards = []
            
            for review in all_reviews:
                # Convert to SM2Parameters
                params = SM2Parameters(
                    repetitions=review.get('repetitions', 0),
                    interval_days=review.get('interval_days', 1),
                    easiness_factor=review.get('easiness_factor', 2.5),
                    due_at=review.get('due_at', datetime.utcnow())
                )
                
                if self.sm2.is_due_for_review(params, current_time):
                    days_overdue = self.sm2.get_days_until_due(params, current_time)
                    priority = self.sm2.get_review_priority(params, abs(days_overdue))
                    
                    due_cards.append({
                        'review_id': review.get('id'),
                        'flashcard_id': review.get('flashcard_id'),
                        'priority': priority,
                        'days_overdue': abs(days_overdue),
                        'params': params
                    })
            
            # Sort by priority (highest first)
            due_cards.sort(key=lambda x: x['priority'], reverse=True)
            
            return due_cards
            
        except Exception as e:
            logger.error(f"Failed to get due cards: {e}")
            return []
    
    def get_review_schedule(self, user_id: str, days_ahead: int = 7) -> Dict[str, Any]:
        """
        Get review schedule for a user
        
        Args:
            user_id: User identifier
            days_ahead: Number of days to look ahead
            
        Returns:
            Dictionary with review schedule
        """
        try:
            # This would typically query the database
            # For now, return a placeholder structure
            schedule = {
                'user_id': user_id,
                'total_due': 0,
                'due_today': 0,
                'due_this_week': 0,
                'daily_schedule': {},
                'estimated_time_minutes': 0
            }
            
            # Calculate daily schedule for the next week
            current_time = datetime.utcnow()
            for i in range(days_ahead):
                date = current_time + timedelta(days=i)
                date_str = date.strftime('%Y-%m-%d')
                
                # This would be populated from actual database queries
                schedule['daily_schedule'][date_str] = {
                    'due_count': 0,
                    'estimated_time': 0
                }
            
            return schedule
            
        except Exception as e:
            logger.error(f"Failed to get review schedule: {e}")
            return {'error': str(e)}
