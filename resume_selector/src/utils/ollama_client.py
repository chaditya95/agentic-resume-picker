"""Ollama client for local LLM communication"""
import requests
import json
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for communicating with Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
    
    def is_connected(self) -> bool:
        """Check if Ollama is running"""
        try:
            response = self.session.get(f"{self.base_url}/api/version", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            return response.json().get('models', [])
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def generate(self, model: str, prompt: str, system: str = None) -> Optional[str]:
        """Generate text using Ollama"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 2000
                }
            }
            
            if system:
                payload["system"] = system
            
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '').strip()
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return None
    
    def ensure_model_available(self, model_name: str) -> bool:
        """Ensure model is available"""
        models = self.list_models()
        model_names = [m['name'] for m in models]
        return model_name in model_names