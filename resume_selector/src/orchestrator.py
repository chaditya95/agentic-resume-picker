"""Enhanced orchestrator with proper imports and error handling"""
import asyncio
import logging
import traceback
from typing import List, Optional, Callable, Dict, Any, Tuple
from pathlib import Path

from .agents.parsing_agent import ParsingAgent
from .agents.question_agent import QuestionAgent
from .agents.scoring_agent import ScoringAgent
from .models.schema import CandidateReport, CandidateExperience
from .utils.ollama_client import OllamaClient
from .utils.file_io import load_resumes, load_resume

logger = logging.getLogger(__name__)

class Orchestrator:
    def __init__(self, model: str = "llama3.1:8b", 
                 parsing_agent: Optional[ParsingAgent] = None,
                 question_agent: Optional[QuestionAgent] = None,
                 scoring_agent: Optional[ScoringAgent] = None):
        
        self.model = model
        self.ollama_client = OllamaClient()
        
        # Initialize agents with proper error handling
        try:
            self.parsing_agent = parsing_agent or ParsingAgent(model, self.ollama_client)
            self.question_agent = question_agent or QuestionAgent(model, self.ollama_client)
            self.scoring_agent = scoring_agent or ScoringAgent(model, self.ollama_client)
            logger.info("Orchestrator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            raise
        
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
            if not parsed or not isinstance(parsed, dict):
                logger.warning(f"Failed to parse resume: {filename}")
                return None
            
            logger.info(f"Parsed resume {filename}: {parsed.get('name', 'Unknown')}")
            
            # Generate questions
            try:
                questions_data = await self.question_agent.generate_questions(jd_text)
                # Extract question text from the response
                questions = []
                if isinstance(questions_data, list):
                    for q in questions_data:
                        if isinstance(q, dict):
                            questions.append(q.get('question', q.get('q', str(q))))
                        else:
                            questions.append(str(q))
                else:
                    questions = ["Tell me about your background"]
                    
                logger.info(f"Generated {len(questions)} questions for {filename}")
            except Exception as e:
                logger.error(f"Error generating questions for {filename}: {e}")
                questions = ["Tell me about your background", "What are your strengths?"]
            
            # Score candidate
            try:
                scoring_result = await self.scoring_agent.score(parsed, jd_text)
                if isinstance(scoring_result, dict):
                    score = float(scoring_result.get('score', 0.0))
                    reasoning = scoring_result.get('reasoning', 'No reasoning provided')
                    strengths = scoring_result.get('strengths', [])
                    concerns = scoring_result.get('concerns', [])
                    recommendation = scoring_result.get('recommendation', 'pass')
                else:
                    score = float(scoring_result) if scoring_result else 0.0
                    reasoning = f"Score: {score}"
                    strengths = []
                    concerns = []
                    recommendation = 'hire' if score >= 70 else 'maybe' if score >= 50 else 'pass'
                    
                logger.info(f"Scored resume {filename}: {score}")
            except Exception as e:
                logger.error(f"Error scoring resume {filename}: {e}")
                score = 0.0
                reasoning = f"Scoring failed: {str(e)}"
                strengths = []
                concerns = ["Processing error"]
                recommendation = 'pass'
            
            # Create experience objects
            experience_list = []
            try:
                for exp in parsed.get('experience', []):
                    if isinstance(exp, dict):
                        experience_list.append(CandidateExperience(
                            company=exp.get('company', 'Unknown'),
                            position=exp.get('position', 'Unknown'),
                            duration=exp.get('duration', 'Unknown')
                        ))
            except Exception as e:
                logger.error(f"Error processing experience for {filename}: {e}")
            
            # Create report
            report = CandidateReport(
                name=parsed.get('name', 'Unknown'),
                skills=parsed.get('skills', [])[:10],  # Limit to 10 skills
                education=parsed.get('education', []),
                experience=experience_list,
                questions=questions[:6],  # Limit to 6 questions
                score=score,
                reasoning=reasoning,
                strengths=strengths,
                concerns=concerns,
                recommendation=recommendation,
                filename=filename
            )
            
            logger.info(f"Successfully processed {filename} - Score: {score}")
            return report
            
        except Exception as e:
            logger.error(f"Error processing resume {filename}: {e}")
            traceback.print_exc()
            return None
    
    async def run(self, resumes: List[str], jd_text: str) -> List[CandidateReport]:
        logger.info("Running orchestrator with %d resumes and model %s", len(resumes), self.model)
        results = []
        
        for i, resume_text in enumerate(resumes, 1):
            try:
                if self.progress_callback:
                    self.progress_callback(i, len(resumes), f"Resume {i}")
                
                # Parse resume
                parsed = await self.parsing_agent.parse(resume_text)
                logger.info(f"Parsed result for resume {i}: {parsed}")
                
                if not parsed or parsed.get('name') == 'Unknown':
                    logger.warning(f"Failed to parse resume {i}")
                    continue
                
                # Generate questions
                questions_data = await self.question_agent.generate_questions(jd_text)
                questions = [q.get('question', str(q)) for q in questions_data if q]
                
                # Score candidate
                score_result = await self.scoring_agent.score(parsed, jd_text)
                logger.info(f"Score result for resume {i}: {score_result}")
                
                # Handle different score result formats
                if isinstance(score_result, dict):
                    score = score_result.get('score', 0.0)
                else:
                    try:
                        score = float(score_result)
                    except (ValueError, TypeError):
                        score = 0.0
                
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
                    reasoning=score_result.get('reasoning', '') if isinstance(score_result, dict) else '',
                    strengths=score_result.get('strengths', []) if isinstance(score_result, dict) else [],
                    concerns=score_result.get('concerns', []) if isinstance(score_result, dict) else [],
                    recommendation=score_result.get('recommendation', 'pass') if isinstance(score_result, dict) else 'pass'
                )
                
                logger.info(f"Created report for {report.name}")
                results.append(report)
                
            except Exception as e:
                logger.error(f"Error processing resume {i}: {e}")
                continue
                
        return results
    
    def run_sync(self, resume_paths: List[Path], jd_text: str) -> List[CandidateReport]:
        """Synchronous version that always returns a list"""
        try:
            # Read resume files
            resume_contents = []
            for path in resume_paths:
                try:
                    content, success = load_resume(path)
                    if success:
                        resume_contents.append((path.name, content))
                    else:
                        logger.error(f"Failed to load resume: {path}")
                except Exception as e:
                    logger.error(f"Error reading resume {path}: {e}")
            
            if not resume_contents:
                logger.warning("No valid resume contents to process")
                return []
            
            # Process resumes
            filenames, contents = zip(*resume_contents)
            results = asyncio.run(self.run(contents, jd_text))
            
            logger.info(f"run_sync completed with {len(results)} results")
            return results if isinstance(results, list) else [results] if results else []
            
        except Exception as e:
            logger.error(f"run_sync failed: {e}")
            traceback.print_exc()
            return []
    
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