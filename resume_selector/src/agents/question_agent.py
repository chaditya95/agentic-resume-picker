"""Enhanced question generation agent"""
import json
import logging
from typing import List, Dict, Any
from pathlib import Path

from ..utils.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "question_prompt.txt"

class QuestionAgent:
    def __init__(self, model: str = "llama3.1:8b", ollama_client: OllamaClient = None):
        self.model = model
        self.ollama_client = ollama_client or OllamaClient()
        self.system_prompt = self._load_prompt()
    
    def _load_prompt(self) -> str:
        """Load system prompt from file"""
        try:
            return PROMPT_PATH.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Failed to load prompt: {e}")
            return "Generate interview questions based on the job description."
    
    def _parse_json_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse JSON response from LLM"""
        try:
            response = response.strip()
            
            # Remove markdown formatting
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Find JSON array
            start = response.find('[')
            end = response.rfind(']')
            
            if start != -1 and end != -1:
                json_str = response[start:end+1]
                questions = json.loads(json_str)
                
                # Validate structure
                if isinstance(questions, list):
                    return questions
            
            return json.loads(response)
            
        except Exception as e:
            logger.error(f"Error parsing questions: {e}")
            return self._get_default_questions()
    
    def _get_default_questions(self) -> List[Dict[str, Any]]:
        """Return default questions on error"""
        return [
            {"level": "Easy", "question": "Tell me about your background.", "type": "behavioral"},
            {"level": "Easy", "question": "What interests you about this role?", "type": "behavioral"},
            {"level": "Medium", "question": "Describe a challenging project you worked on.", "type": "behavioral"},
            {"level": "Medium", "question": "How do you approach problem-solving?", "type": "technical"},
            {"level": "Hard", "question": "Design a system for handling high traffic.", "type": "technical"},
            {"level": "Hard", "question": "How would you handle a critical production issue?", "type": "behavioral"}
        ]
    
    async def generate_questions(self, jd_text: str) -> List[Dict[str, Any]]:
        """Generate interview questions based on job description"""
        try:
            if not self.ollama_client.is_connected():
                logger.error("Ollama is not connected")
                return self._get_default_questions()
            
            prompt = f"Job Description:\n\n{jd_text}"
            
            response = self.ollama_client.generate(
                model=self.model,
                prompt=prompt,
                system=self.system_prompt
            )
            
            if response:
                return self._parse_json_response(response)
            else:
                logger.error("No response from LLM")
                return self._get_default_questions()
                
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return self._get_default_questions()
    
    def generate_questions_sync(self, jd_text: str) -> List[Dict[str, Any]]:
        """Synchronous version"""
        import asyncio
        return asyncio.run(self.generate_questions(jd_text))