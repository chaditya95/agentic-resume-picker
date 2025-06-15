import json
import logging
from typing import Dict, Any
from pathlib import Path

from ..utils.ollama_client import OllamaClient

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "scoring_prompt.txt"

class ScoringAgent:
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
            return "Score the candidate resume against the job description from 0-100."
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from LLM"""
        try:
            response = response.strip()
            
            # Remove markdown formatting
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
            
        except Exception as e:
            logger.error(f"Error parsing score response: {e}")
            return {
                "score": 0.0,
                "reasoning": "Failed to parse scoring response",
                "strengths": [],
                "concerns": ["Processing error"],
                "recommendation": "pass"
            }
    
    async def score(self, parsed_resume: Dict, jd_text: str) -> Dict[str, Any]:
        """Score resume against job description"""
        try:
            if not self.ollama_client.is_connected():
                logger.error("Ollama is not connected")
                return {"score": 0.0, "reasoning": "Ollama not connected", "strengths": [], "concerns": ["Connection error"], "recommendation": "pass"}
            
            # Format the input
            resume_summary = f"""
                                Candidate: {parsed_resume.get('name', 'Unknown')}
                                Skills: {', '.join(parsed_resume.get('skills', []))}
                                Experience: {len(parsed_resume.get('experience', []))} positions
                                Education: {', '.join(parsed_resume.get('education', []))}
                                Summary: {parsed_resume.get('summary', 'No summary available')}
                            """
            
            prompt = f"Job Description:\n{jd_text}\n\nCandidate Profile:\n{resume_summary}"
            
            response = self.ollama_client.generate(
                model=self.model,
                prompt=prompt,
                system=self.system_prompt
            )
            
            if response:
                return self._parse_json_response(response)
            else:
                logger.error("No response from LLM")
                return {"score": 0.0, "reasoning": "No response from AI", "strengths": [], "concerns": ["AI unavailable"], "recommendation": "pass"}
                
        except Exception as e:
            logger.error(f"Error in scoring: {e}")
            return {"score": 0.0, "reasoning": f"Scoring error: {str(e)}", "strengths": [], "concerns": ["Processing error"], "recommendation": "pass"}
    
    def score_sync(self, parsed_resume: Dict, jd_text: str) -> Dict[str, Any]:
        """Synchronous version"""
        import asyncio
        return asyncio.run(self.score(parsed_resume, jd_text))