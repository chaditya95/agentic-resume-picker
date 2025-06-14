import asyncio
import logging
from typing import List, Optional

from .agents.parsing_agent import ParsingAgent
from .agents.question_agent import QuestionAgent
from .agents.scoring_agent import ScoringAgent
from .models.schema import CandidateReport, CandidateExperience

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(self, model: str = "ollama/llama3", parsing_agent: Optional[ParsingAgent] = None,
                 question_agent: Optional[QuestionAgent] = None,
                 scoring_agent: Optional[ScoringAgent] = None) -> None:
        self.parsing_agent = parsing_agent or ParsingAgent(model=model)
        self.question_agent = question_agent or QuestionAgent(model=model)
        self.scoring_agent = scoring_agent or ScoringAgent(model=model)

    async def run(self, resumes: List[str], jd_text: str) -> CandidateReport:
        logger.info("Running orchestrator")
        parsed = await self.parsing_agent.parse(resumes)
        questions = await self.question_agent.generate_questions(jd_text)
        score = await self.scoring_agent.score(parsed, jd_text)
        report = CandidateReport(
            name=parsed.get("name", "Unknown"),
            skills=parsed.get("skills", []),
            education=parsed.get("education", []),
            experience=[CandidateExperience(**exp) for exp in parsed.get("experience", [])],
            questions=questions,
            score=score,
        )
        return report

    def run_sync(self, resumes: List[str], jd_text: str) -> CandidateReport:
        return asyncio.run(self.run(resumes, jd_text))
