import logging
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from enum import Enum

logger = logging.getLogger(__name__)


class VerdictType(str, Enum):
    CORRECT = "correct"
    PARTIAL = "partial"
    INCORRECT = "incorrect"


class GradingResult(BaseModel):
    """Pydantic model for quiz grading results"""
    score: float = Field(..., ge=0.0, le=1.0, description="Score between 0.0 and 1.0")
    verdict: VerdictType = Field(..., description="Overall verdict of the answer")
    feedback: str = Field(..., min_length=10, description="Constructive feedback for the student")
    ideal_answer: Optional[str] = Field(None, description="Improved ideal answer if needed")
    
    @validator('score')
    def validate_score(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Score must be between 0.0 and 1.0')
        return v
    
    @validator('feedback')
    def validate_feedback(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Feedback must be at least 10 characters long')
        return v.strip()


class SocraticResult(BaseModel):
    """Pydantic model for Socratic follow-up results"""
    socratic_question: str = Field(..., min_length=10, description="Guiding question or hint")
    hint_type: str = Field(..., description="Type of hint provided")
    
    @validator('socratic_question')
    def validate_question(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Socratic question must be at least 10 characters long')
        return v.strip()


class GradingService:
    """Service for grading quiz answers and providing feedback"""
    
    def __init__(self):
        self.rubric_weights = {
            'accuracy': 0.4,      # How correct the answer is
            'completeness': 0.3,  # How complete the answer is
            'clarity': 0.2,       # How clear the answer is
            'relevance': 0.1      # How relevant to the question
        }
    
    def grade_answer(self, question: str, ideal_answer: str, user_answer: str, 
                    context: str = "", api_key: str = "") -> GradingResult:
        """
        Grade a user's answer using AI and structured rubric
        
        Args:
            question: The quiz question
            ideal_answer: The correct/ideal answer
            user_answer: The user's answer to grade
            context: Additional context for grading
            api_key: User's Gemini API key
            
        Returns:
            GradingResult with score, verdict, and feedback
        """
        try:
            # Generate AI grading
            ai_result = self._generate_ai_grading(question, ideal_answer, user_answer, context, api_key)
            
            # Validate and structure the result
            grading_result = self._validate_grading_result(ai_result)
            
            # Apply rubric-based adjustments if needed
            final_result = self._apply_rubric_adjustments(grading_result, user_answer, ideal_answer)
            
            return final_result
            
        except Exception as e:
            logger.error(f"Grading failed: {e}")
            # Return fallback grading
            return self._fallback_grading(user_answer, ideal_answer)
    
    def _generate_ai_grading(self, question: str, ideal_answer: str, user_answer: str, 
                           context: str, api_key: str) -> Dict[str, Any]:
        """Generate grading using AI"""
        try:
            from app.core.prompts import PromptBuilder
            from app.core.llm import LLMService
            
            # Build grading prompt
            prompt = PromptBuilder.build_grading_prompt(question, ideal_answer, user_answer, context)
            
            # Get AI response
            llm_service = LLMService()
            response = llm_service.generate_content(prompt, api_key)
            
            # Parse JSON response
            result = json.loads(response)
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI grading response: {e}")
            raise
        except Exception as e:
            logger.error(f"AI grading generation failed: {e}")
            raise
    
    def _validate_grading_result(self, ai_result: Dict[str, Any]) -> GradingResult:
        """Validate and structure AI grading result"""
        try:
            # Ensure required fields exist
            required_fields = ['score', 'verdict', 'feedback']
            for field in required_fields:
                if field not in ai_result:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate and create GradingResult
            return GradingResult(
                score=float(ai_result['score']),
                verdict=VerdictType(ai_result['verdict']),
                feedback=ai_result['feedback'],
                ideal_answer=ai_result.get('ideal_answer')
            )
            
        except Exception as e:
            logger.error(f"Grading result validation failed: {e}")
            raise
    
    def _apply_rubric_adjustments(self, grading_result: GradingResult, 
                                user_answer: str, ideal_answer: str) -> GradingResult:
        """Apply rubric-based adjustments to the grading result"""
        try:
            # Calculate rubric scores
            rubric_scores = self._calculate_rubric_scores(user_answer, ideal_answer)
            
            # Weight the rubric scores
            weighted_score = sum(
                score * weight for score, weight in zip(rubric_scores.values(), self.rubric_weights.values())
            )
            
            # Blend AI score with rubric score (70% AI, 30% rubric)
            final_score = (grading_result.score * 0.7) + (weighted_score * 0.3)
            
            # Adjust verdict if score changed significantly
            new_verdict = self._determine_verdict(final_score)
            
            # Update the result
            grading_result.score = round(final_score, 2)
            grading_result.verdict = new_verdict
            
            return grading_result
            
        except Exception as e:
            logger.error(f"Rubric adjustment failed: {e}")
            return grading_result
    
    def _calculate_rubric_scores(self, user_answer: str, ideal_answer: str) -> Dict[str, float]:
        """Calculate rubric-based scores for different criteria"""
        try:
            # Simple keyword-based scoring (could be enhanced with NLP)
            user_lower = user_answer.lower()
            ideal_lower = ideal_answer.lower()
            
            # Accuracy: Check for key terms from ideal answer
            ideal_terms = set(ideal_lower.split())
            user_terms = set(user_lower.split())
            accuracy = len(ideal_terms.intersection(user_terms)) / max(len(ideal_terms), 1)
            
            # Completeness: Length ratio (with reasonable bounds)
            completeness = min(len(user_answer) / max(len(ideal_answer), 1), 1.0)
            
            # Clarity: Check for proper sentence structure
            clarity = 1.0 if len(user_answer.split('.')) > 1 else 0.7
            
            # Relevance: Simple keyword matching
            relevance = min(accuracy * 1.2, 1.0)
            
            return {
                'accuracy': accuracy,
                'completeness': completeness,
                'clarity': clarity,
                'relevance': relevance
            }
            
        except Exception as e:
            logger.error(f"Rubric scoring failed: {e}")
            return {
                'accuracy': 0.5,
                'completeness': 0.5,
                'clarity': 0.5,
                'relevance': 0.5
            }
    
    def _determine_verdict(self, score: float) -> VerdictType:
        """Determine verdict based on score"""
        if score >= 0.8:
            return VerdictType.CORRECT
        elif score >= 0.4:
            return VerdictType.PARTIAL
        else:
            return VerdictType.INCORRECT
    
    def _fallback_grading(self, user_answer: str, ideal_answer: str) -> GradingResult:
        """Fallback grading when AI grading fails"""
        try:
            # Simple keyword-based fallback
            user_lower = user_answer.lower()
            ideal_lower = ideal_answer.lower()
            
            # Calculate simple similarity
            ideal_terms = set(ideal_lower.split())
            user_terms = set(user_lower.split())
            similarity = len(ideal_terms.intersection(user_terms)) / max(len(ideal_terms), 1)
            
            score = min(similarity * 1.2, 1.0)
            verdict = self._determine_verdict(score)
            
            feedback = self._generate_fallback_feedback(verdict, user_answer, ideal_answer)
            
            return GradingResult(
                score=score,
                verdict=verdict,
                feedback=feedback,
                ideal_answer=ideal_answer
            )
            
        except Exception as e:
            logger.error(f"Fallback grading failed: {e}")
            return GradingResult(
                score=0.0,
                verdict=VerdictType.INCORRECT,
                feedback="Terjadi kesalahan dalam penilaian. Silakan coba lagi.",
                ideal_answer=ideal_answer
            )
    
    def _generate_fallback_feedback(self, verdict: VerdictType, user_answer: str, ideal_answer: str) -> str:
        """Generate fallback feedback based on verdict"""
        if verdict == VerdictType.CORRECT:
            return "Jawaban Anda sudah benar! Pertahankan pemahaman yang baik ini."
        elif verdict == VerdictType.PARTIAL:
            return "Jawaban Anda sebagian benar. Coba pikirkan lebih dalam tentang konsep yang ditanyakan."
        else:
            return "Jawaban Anda belum tepat. Silakan pelajari kembali materi yang terkait dengan pertanyaan ini."
    
    def generate_socratic_followup(self, question: str, user_answer: str, 
                                 feedback: str, verdict: VerdictType, api_key: str) -> SocraticResult:
        """Generate Socratic follow-up question"""
        try:
            from app.core.prompts import PromptBuilder
            from app.core.llm import LLMService
            
            # Build Socratic prompt
            prompt = PromptBuilder.build_socratic_prompt(question, user_answer, feedback, verdict.value)
            
            # Get AI response
            llm_service = LLMService()
            response = llm_service.generate_content(prompt, api_key)
            
            # Parse and validate result
            result = json.loads(response)
            return SocraticResult(
                socratic_question=result['socratic_question'],
                hint_type=result['hint_type']
            )
            
        except Exception as e:
            logger.error(f"Socratic follow-up generation failed: {e}")
            # Return fallback
            return SocraticResult(
                socratic_question="Coba pikirkan kembali konsep yang mendasari pertanyaan ini.",
                hint_type="conceptual"
            )
