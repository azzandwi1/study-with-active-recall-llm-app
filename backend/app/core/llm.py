import logging
from typing import Dict, Any, Optional
import google.generativeai as genai
from app.core.settings import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for interacting with Gemini LLM"""
    
    def __init__(self):
        self.model_name = settings.gen_model
    
    def generate_content(self, prompt: str, api_key: str, **kwargs) -> str:
        """
        Generate content using Gemini LLM
        
        Args:
            prompt: Input prompt
            api_key: User's Gemini API key
            **kwargs: Additional generation parameters
            
        Returns:
            Generated content as string
        """
        try:
            # Configure Gemini with user's API key
            genai.configure(api_key=api_key)
            
            # Initialize model
            model = genai.GenerativeModel(self.model_name)
            
            # Set generation parameters
            generation_config = genai.types.GenerationConfig(
                temperature=kwargs.get('temperature', 0.7),
                top_p=kwargs.get('top_p', 0.8),
                top_k=kwargs.get('top_k', 40),
                max_output_tokens=kwargs.get('max_output_tokens', 2048),
            )
            
            # Generate content
            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            if not response.text:
                raise ValueError("Empty response from LLM")
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"LLM content generation failed: {e}")
            raise
    
    def generate_structured_content(self, prompt: str, api_key: str, 
                                  expected_format: str = "JSON") -> Dict[str, Any]:
        """
        Generate structured content (JSON) using Gemini LLM
        
        Args:
            prompt: Input prompt
            api_key: User's Gemini API key
            expected_format: Expected output format
            
        Returns:
            Parsed structured content
        """
        try:
            # Add format instruction to prompt
            if expected_format.upper() == "JSON":
                prompt += "\n\nIMPORTANT: Respond ONLY with valid JSON. No additional text or explanation."
            
            # Generate content
            response_text = self.generate_content(prompt, api_key)
            
            # Parse JSON response
            import json
            try:
                return json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response text: {response_text}")
                raise ValueError(f"Invalid JSON response: {e}")
            
        except Exception as e:
            logger.error(f"Structured content generation failed: {e}")
            raise
    
    def validate_api_key(self, api_key: str) -> bool:
        """
        Validate if the provided API key is valid
        
        Args:
            api_key: Gemini API key to validate
            
        Returns:
            True if API key is valid
        """
        try:
            # Configure Gemini with the API key
            genai.configure(api_key=api_key)
            
            # Try to list models (simple validation)
            models = genai.list_models()
            
            # Check if our target model is available
            model_names = [model.name for model in models]
            target_model = f"models/{self.model_name}"
            
            return target_model in model_names
            
        except Exception as e:
            logger.error(f"API key validation failed: {e}")
            return False
    
    def get_model_info(self, api_key: str) -> Dict[str, Any]:
        """
        Get information about available models
        
        Args:
            api_key: User's Gemini API key
            
        Returns:
            Dictionary with model information
        """
        try:
            genai.configure(api_key=api_key)
            models = genai.list_models()
            
            model_info = {
                'available_models': [],
                'target_model': f"models/{self.model_name}",
                'target_model_available': False
            }
            
            for model in models:
                model_data = {
                    'name': model.name,
                    'display_name': model.display_name,
                    'description': model.description,
                    'supported_generation_methods': model.supported_generation_methods
                }
                model_info['available_models'].append(model_data)
                
                if model.name == model_info['target_model']:
                    model_info['target_model_available'] = True
            
            return model_info
            
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {
                'error': str(e),
                'available_models': [],
                'target_model': f"models/{self.model_name}",
                'target_model_available': False
            }
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text (rough approximation)
        
        Args:
            text: Text to estimate tokens for
            
        Returns:
            Estimated token count
        """
        # Rough estimation: 1 token ≈ 4 characters for English
        # This is a simple heuristic and may not be accurate
        return len(text) // 4
    
    def truncate_to_tokens(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit
        
        Args:
            text: Text to truncate
            max_tokens: Maximum token limit
            
        Returns:
            Truncated text
        """
        estimated_tokens = self.estimate_tokens(text)
        
        if estimated_tokens <= max_tokens:
            return text
        
        # Truncate proportionally
        ratio = max_tokens / estimated_tokens
        truncate_length = int(len(text) * ratio)
        
        # Try to truncate at word boundary
        truncated = text[:truncate_length]
        last_space = truncated.rfind(' ')
        
        if last_space > truncate_length * 0.8:  # If we can find a good word boundary
            return truncated[:last_space] + "..."
        else:
            return truncated + "..."
