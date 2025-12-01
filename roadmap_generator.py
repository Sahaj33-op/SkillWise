# roadmap_generator.py
import google.generativeai as genai
import os
import time
from typing import Optional

class RoadmapGenerationError(Exception):
    """Custom exception for roadmap generation errors."""
    pass

def validate_prompt(prompt: str) -> bool:
    """Validate the prompt for roadmap generation."""
    if not prompt or not isinstance(prompt, str):
        return False
    if len(prompt) < 50:
        return False
    if len(prompt) > 4000:  # Gemini's context window limit
        return False
    return True

def generate_roadmap(prompt: str, max_retries: int = 3) -> str:
    """
    Generate a learning roadmap using Google's Gemini model.
    
    Args:
        prompt (str): The prompt for roadmap generation
        max_retries (int): Maximum number of retry attempts
        
    Returns:
        str: Generated roadmap text
        
    Raises:
        RoadmapGenerationError: If generation fails after retries
    """
    if not validate_prompt(prompt):
        raise RoadmapGenerationError("Invalid prompt. Please provide a detailed prompt between 50 and 4000 characters.")
    
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            
            if not response or not response.text:
                raise RoadmapGenerationError("Empty response from model")
                
            return response.text.strip()
            
        except Exception as e:
            last_error = str(e)
            retry_count += 1
            if retry_count < max_retries:
                time.sleep(2 ** retry_count)  # Exponential backoff
            continue
    
    # Try to list models to help debug
    available_models = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
    except Exception as list_err:
        available_models = [f"Could not list models: {str(list_err)}"]
    
    raise RoadmapGenerationError(f"Failed to generate roadmap after {max_retries} attempts. Last error: {last_error}. Available models: {available_models}")