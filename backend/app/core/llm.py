import logging
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from google.genai import errors
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
            import time
            
            # Create client with user's API key
            client = genai.Client(api_key=api_key)
            
            # Proactively truncate overly large prompts
            input_token_limit = kwargs.get('input_token_limit', 6000)
            if self.estimate_tokens(prompt) > input_token_limit:
                prompt = self.truncate_to_tokens(prompt, input_token_limit)
            
            # Retry with exponential backoff on transient/empty responses
            max_attempts = kwargs.get('max_attempts', 3)
            backoff_base = kwargs.get('backoff_base', 0.8)
            last_error: Optional[Exception] = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    response = client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=kwargs.get('temperature', 0.7),
                            top_p=kwargs.get('top_p', 0.8),
                            top_k=kwargs.get('top_k', 40),
                            max_output_tokens=kwargs.get('max_output_tokens', 2048),
                        )
                    )
                    if response and getattr(response, 'text', None):
                        return response.text.strip()
                    last_error = ValueError("Empty response from LLM")
                    logger.warning("Received empty response from LLM; retrying...")
                except errors.APIError as e:
                    last_error = e
                    # Retry on common transient statuses
                    retryable_codes = {429, 500, 502, 503, 504}
                    if getattr(e, 'code', None) in retryable_codes:
                        logger.warning(f"LLM API error {e.code}; attempt {attempt}/{max_attempts} will retry")
                    else:
                        logger.error(f"LLM API error: {e.code} - {e.message}")
                        raise
                except Exception as e:
                    last_error = e
                    logger.warning(f"LLM content generation attempt {attempt} failed: {e}")
                
                # Backoff before next attempt
                if attempt < max_attempts:
                    sleep_seconds = (backoff_base ** attempt) * 1.5
                    time.sleep(sleep_seconds)
            
            # If all attempts failed
            raise last_error or RuntimeError("LLM content generation failed")
            
        except errors.APIError as e:
            logger.error(f"LLM API error: {e.code} - {e.message}")
            raise
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
            import re
            
            # Clean the response text - remove markdown code blocks if present
            cleaned_text = response_text.strip()
            
            # Remove markdown code blocks
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]  # Remove ```json
            elif cleaned_text.startswith('```'):
                cleaned_text = cleaned_text[3:]   # Remove ```
            
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]  # Remove trailing ```
            
            cleaned_text = cleaned_text.strip()
            
            # Try to find the first complete JSON array or object
            # Look for the first '[' or '{' and try to find the matching closing bracket
            start_idx = -1
            for i, char in enumerate(cleaned_text):
                if char in '[{':
                    start_idx = i
                    break
            
            if start_idx != -1:
                # Find the matching closing bracket
                bracket_count = 0
                end_idx = -1
                for i in range(start_idx, len(cleaned_text)):
                    if cleaned_text[i] in '[{':
                        bracket_count += 1
                    elif cleaned_text[i] in ']}':
                        bracket_count -= 1
                        if bracket_count == 0:
                            end_idx = i
                            break
                
                if end_idx != -1:
                    cleaned_text = cleaned_text[start_idx:end_idx + 1]
            
            try:
                return json.loads(cleaned_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Original response text: {response_text}")
                logger.error(f"Cleaned response text: {cleaned_text}")
                
                # Try to fix common JSON issues
                try:
                    # Remove any trailing commas before closing brackets
                    import re
                    fixed_text = re.sub(r',(\s*[}\]])', r'\1', cleaned_text)
                    return json.loads(fixed_text)
                except json.JSONDecodeError:
                    # Attempt partial array/object recovery for truncated outputs
                    try:
                        def recover_array(text: str) -> str:
                            # Build an array from fully closed objects within a possibly truncated JSON array
                            objs = []
                            i = 0
                            n = len(text)
                            # find opening '['
                            while i < n and text[i] != '[':
                                i += 1
                            if i == n:
                                return text
                            i += 1
                            while i < n:
                                # skip whitespace and commas
                                while i < n and text[i] in ' \n\r\t,':
                                    i += 1
                                if i >= n or text[i] != '{':
                                    break
                                # capture object
                                start = i
                                brace = 0
                                in_str = False
                                esc = False
                                while i < n:
                                    ch = text[i]
                                    if in_str:
                                        if esc:
                                            esc = False
                                        elif ch == '\\':
                                            esc = True
                                        elif ch == '"':
                                            in_str = False
                                    else:
                                        if ch == '"':
                                            in_str = True
                                        elif ch == '{':
                                            brace += 1
                                        elif ch == '}':
                                            brace -= 1
                                            if brace == 0:
                                                i += 1
                                                objs.append(text[start:i])
                                                break
                                    i += 1
                                if brace != 0:
                                    # truncated object; stop
                                    break
                            return '[' + ','.join(objs) + ']'
                        
                        if cleaned_text.strip().startswith('['):
                            recovered = recover_array(cleaned_text)
                            return json.loads(recovered)
                        elif cleaned_text.strip().startswith('{'):
                            # Trim to last closing brace for single object
                            last = cleaned_text.rfind('}')
                            if last != -1:
                                return json.loads(cleaned_text[:last+1])
                    except Exception:
                        pass
                    
                    # Final attempt: ask model to continue truncated JSON and merge
                    try:
                        client = genai.Client(api_key=api_key)
                        # Detect if looks truncated (no closing bracket)
                        looks_array = cleaned_text.strip().startswith('[') and not cleaned_text.strip().endswith(']')
                        looks_object = cleaned_text.strip().startswith('{') and not cleaned_text.strip().endswith('}')
                        if looks_array or looks_object:
                            tail = cleaned_text[-500:]
                            continuation_prompt = (
                                "The following JSON was truncated. Continue ONLY the JSON continuation to complete it. "
                                "Do not repeat earlier content. No prose, no code fences. Ensure valid JSON closure.\n\n"
                                f"Truncated tail (for context):\n{tail}\n\n"
                                "Output: the continuation only."
                            )
                            cont_resp = client.models.generate_content(
                                model=self.model_name,
                                contents=continuation_prompt,
                                config=types.GenerateContentConfig(
                                    temperature=0.2,
                                    max_output_tokens=kwargs.get('continuation_max_tokens', 512),
                                )
                            )
                            cont_text = (getattr(cont_resp, 'text', '') or '').strip()
                            # Clean fences from continuation
                            if cont_text.startswith('```json'):
                                cont_text = cont_text[7:]
                            elif cont_text.startswith('```'):
                                cont_text = cont_text[3:]
                            if cont_text.endswith('```'):
                                cont_text = cont_text[:-3]
                            cont_text = cont_text.strip()
                            merged = cleaned_text + cont_text
                            # Try same fixes on merged
                            merged_fixed = re.sub(r',(\s*[}\]])', r'\1', merged)
                            # Try to find complete structure bounding
                            start_idx = -1
                            for i, ch in enumerate(merged_fixed):
                                if ch in '[{':
                                    start_idx = i
                                    break
                            if start_idx != -1:
                                # find matching
                                depth = 0
                                end_idx = -1
                                in_str = False
                                esc = False
                                for i in range(start_idx, len(merged_fixed)):
                                    ch = merged_fixed[i]
                                    if in_str:
                                        if esc:
                                            esc = False
                                        elif ch == '\\':
                                            esc = True
                                        elif ch == '"':
                                            in_str = False
                                    else:
                                        if ch == '"':
                                            in_str = True
                                        elif ch in '[{':
                                            depth += 1
                                        elif ch in ']}':
                                            depth -= 1
                                            if depth == 0:
                                                end_idx = i
                                                break
                                if end_idx != -1:
                                    merged_fixed = merged_fixed[start_idx:end_idx+1]
                            return json.loads(merged_fixed)
                    except Exception:
                        pass
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
            # Create client with the API key
            client = genai.Client(api_key=api_key)
            
            # Try to list models (simple validation)
            models = client.models.list()
            
            # Check if our target model is available
            model_names = [model.name for model in models]
            target_model = f"models/{self.model_name}"
            
            return target_model in model_names
            
        except errors.APIError as e:
            logger.error(f"API key validation failed: {e.code} - {e.message}")
            return False
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
            client = genai.Client(api_key=api_key)
            models = client.models.list()
            
            model_info = {
                'available_models': [],
                'target_model': f"models/{self.model_name}",
                'target_model_available': False
            }
            
            for model in models:
                model_data = {
                    'name': model.name,
                    'display_name': getattr(model, 'display_name', model.name),
                    'description': getattr(model, 'description', ''),
                    'supported_generation_methods': getattr(model, 'supported_generation_methods', [])
                }
                model_info['available_models'].append(model_data)
                
                if model.name == model_info['target_model']:
                    model_info['target_model_available'] = True
            
            return model_info
            
        except errors.APIError as e:
            logger.error(f"Failed to get model info: {e.code} - {e.message}")
            return {
                'error': f"{e.code}: {e.message}",
                'available_models': [],
                'target_model': f"models/{self.model_name}",
                'target_model_available': False
            }
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
