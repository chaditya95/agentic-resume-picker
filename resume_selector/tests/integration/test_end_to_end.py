import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from resume_selector.src.models.schema import CandidateReport
from resume_selector.src.orchestrator import Orchestrator


class DummyParsingAgent:
    async def parse(self, resumes):
        return {"name": "John", "skills": [], "education": [], "experience": []}


class DummyQuestionAgent:
    async def generate_questions(self, jd):
        return []


class DummyScoringAgent:
    async def score(self, parsed_resume, jd):
        return 42.0


def test_run_end_to_end():
    orch = Orchestrator(parsing_agent=DummyParsingAgent(), question_agent=DummyQuestionAgent(), scoring_agent=DummyScoringAgent())
    report = orch.run_sync(["res"], "jd")
    assert isinstance(report, CandidateReport)
    assert report.score == 42.0
