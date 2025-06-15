"""Configuration management for Resume Selector"""
import json
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class Config:
    """Application configuration manager"""
    
    def __init__(self):
        self.config_path = self._get_config_path()
        self._config = self._load_config()
    
    def _get_config_path(self) -> Path:
        """Get configuration file path"""
        # Try relative path first
        if Path("config.json").exists():
            return Path("config.json")
        
        # Try in resume_selector directory
        config_file = Path(__file__).parent.parent / "config.json"
        if config_file.exists():
            return config_file
        
        # Create default config
        return Path("config.json")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            else:
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "ollama": {
                "base_url": "http://localhost:11434",
                "model": "llama3.1:8b",
                "timeout": 30
            },
            "ui": {
                "window_width": 1200,
                "window_height": 800
            },
            "processing": {
                "max_concurrent_resumes": 3,
                "retry_attempts": 2
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
