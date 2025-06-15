"""Enhanced parsing agent with proper CrewAI integration"""
import json
import logging
from typing import Dict, Any
from pathlib import Path

from ..utils.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "parsing_prompt.txt"

class ParsingAgent:
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
            return "Parse the resume and extract relevant information as JSON."
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM"""
        try:
            # Clean up response
            response = response.strip()
            
            # Remove markdown formatting if present
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]
            
            # Find JSON object
            start = response.find('{')
            end = response.rfind('}')
            
            if start != -1 and end != -1:
                json_str = response[start:end+1]
                return json.loads(json_str)
            
            return json.loads(response)
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return self._get_default_parse_result()
        except Exception as e:
            logger.error(f"Error parsing response: {e}")
            return self._get_default_parse_result()
    
    def _get_default_parse_result(self) -> Dict[str, Any]:
        """Return default parse result on error"""
        return {
            "name": "Unknown",
            "email": "",
            "phone": "",
            "skills": [],
            "education": [],
            "experience": [],
            "summary": "Failed to parse resume"
        }
    
    async def parse(self, resume_text: str) -> Dict[str, Any]:
        """Parse a single resume"""
        try:
            if not self.ollama_client.is_connected():
                logger.error("Ollama is not connected")
                return self._get_default_parse_result()
            
            prompt = f"Resume to parse:\n\n{resume_text}"
            
            response = self.ollama_client.generate(
                model=self.model,
                prompt=prompt,
                system=self.system_prompt
            )
            
            if response:
                return self._parse_json_response(response)
            else:
                logger.error("No response from LLM")
                return self._get_default_parse_result()
                
        except Exception as e:
            logger.error(f"Error in parse method: {e}")
            return self._get_default_parse_result()
    
    def parse_sync(self, resume_text: str) -> Dict[str, Any]:
        """Synchronous version of parse"""
        import asyncio
        return asyncio.run(self.parse(resume_text))