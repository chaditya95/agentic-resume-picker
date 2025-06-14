import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3]))

from resume_selector.src.orchestrator import Orchestrator


class DummyParsingAgent:
    async def parse(self, resumes):
        return {"name": "Jane", "skills": ["python"], "education": [], "experience": []}


class DummyQuestionAgent:
    async def generate_questions(self, jd_text):
        return ["Q1"]


def test_orchestrator():
    orch = Orchestrator(parsing_agent=DummyParsingAgent(), question_agent=DummyQuestionAgent())
    report = orch.run_sync(["resume"], "jd")
    assert report.name == "Jane"
    assert report.questions == ["Q1"]
