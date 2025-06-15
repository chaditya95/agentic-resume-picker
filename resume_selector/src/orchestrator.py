"""Enhanced orchestrator with better error handling and progress tracking"""
import asyncio
import logging
from typing import List, Optional, Callable, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from resume_selector.src.agents.parsing_agent import ParsingAgent
from resume_selector.src.agents.question_agent import QuestionAgent
from resume_selector.src.agents.scoring_agent import ScoringAgent
from resume_selector.src.models.schema import CandidateReport, CandidateExperience
from resume_selector.src.utils.ollama_client import OllamaClient
from resume_selector.src.utils.file_io import load_resumes
from pathlib import Path

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, model: str = "llama3.1:8b", 
                 parsing_agent: Optional[ParsingAgent] = None,
                 question_agent: Optional[QuestionAgent] = None,
                 scoring_agent: Optional[ScoringAgent] = None):
        
        self.model = model
        self.ollama_client = OllamaClient()
        
        # Initialize agents
        self.parsing_agent = parsing_agent or ParsingAgent(model, self.ollama_client)
        self.question_agent = question_agent or QuestionAgent(model, self.ollama_client)
        self.scoring_agent = scoring_agent or ScoringAgent(model, self.ollama_client)
        
        # Progress tracking
        self.progress_callback: Optional[Callable] = None
        self.is_processing = False
        
    def set_progress_callback(self, callback: Callable[[int, int, str], None]):
        """Set callback for progress updates"""
        self.progress_callback = callback
    
    def check_ollama_connection(self) -> bool:
        """Check if Ollama is running and model is available"""
        if not self.ollama_client.is_connected():
            logger.error("Ollama is not running")
            return False
        
        if not self.ollama_client.ensure_model_available(self.model):
            logger.error(f"Model {self.model} is not available")
            return False
        
        return True
    
    async def process_single_resume(self, resume_text: str, filename: str, jd_text: str) -> Optional[CandidateReport]:
        """Process a single resume through the full pipeline"""
        try:
            logger.info(f"Processing resume: {filename}")
            
            # Parse resume
            parsed = await self.parsing_agent.parse(resume_text)
            if not parsed or parsed.get('name') == 'Unknown':
                logger.warning(f"Failed to parse resume: {filename}")
                return None
            
            # Generate questions
            questions_data = await self.question_agent.generate_questions(jd_text)
            questions = [q.get('question', str(q)) for q in questions_data if q]
            
            # Score candidate
            scoring_result = await self.scoring_agent.score(parsed, jd_text)
            score = scoring_result.get('score', 0.0)
            
            # Create experience objects
            experience_list = []
            for exp in parsed.get('experience', []):
                if isinstance(exp, dict):
                    experience_list.append(CandidateExperience(
                        company=exp.get('company', ''),
                        position=exp.get('position', ''),
                        duration=exp.get('duration', '')
                    ))
            
            # Create report
            report = CandidateReport(
                name=parsed.get('name', 'Unknown'),
                skills=parsed.get('skills', []),
                education=parsed.get('education', []),
                experience=experience_list,
                questions=questions,
                score=score,
                reasoning=scoring_result.get('reasoning', ''),
                strengths=scoring_result.get('strengths', []),
                concerns=scoring_result.get('concerns', []),
                recommendation=scoring_result.get('recommendation', 'pass'),
                filename=filename
            )
            
            logger.info(f"Successfully processed {filename} - Score: {score}")
            return report
            
        except Exception as e:
            logger.error(f"Error processing resume {filename}: {e}")
            return None
    
    async def run(self, resume_paths: List[Path], jd_text: str) -> List[CandidateReport]:
        """Run the orchestrator on multiple resumes"""
        logger.info(f"Starting orchestrator with {len(resume_paths)} resumes")
        
        if not self.check_ollama_connection():
            raise RuntimeError("Ollama connection failed")
        
        # Load resume contents
        resume_data = load_resumes(resume_paths)
        logger.info(f"Successfully loaded {len(resume_data)} resumes")
        
        results = []
        total = len(resume_data)
        
        # Process each resume
        for i, (filename, content) in enumerate(resume_data):
            try:
                # Update progress
                if self.progress_callback:
                    self.progress_callback(i, total, filename)
                
                # Process resume
                report = await self.process_single_resume(content, filename, jd_text)
                if report:
                    results.append(report)
                
            except Exception as e:
                logger.error(f"Error processing {filename}: {e}")
        
        # Final progress update
        if self.progress_callback:
            self.progress_callback(total, total, "Complete")
        
        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        
        logger.info(f"Orchestrator completed. {len(results)} successful results.")
        return results
    
    def run_sync(self, resume_paths: List[Path], jd_text: str) -> List[CandidateReport]:
        """Synchronous version of run"""
        return asyncio.run(self.run(resume_paths, jd_text))
    
    def run_with_progress(self, resume_paths: List[Path], jd_text: str, 
                         progress_callback: Callable[[int, int, str], None]) -> List[CandidateReport]:
        """Run with progress tracking in separate thread"""
        self.set_progress_callback(progress_callback)
        self.is_processing = True
        
        try:
            results = self.run_sync(resume_paths, jd_text)
            return results
        finally:
            self.is_processing = False