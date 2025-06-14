from typing import List
import asyncio
from pathlib import Path
from importlib import import_module

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "question_prompt.txt"


class QuestionAgent:
    def __init__(self, model: str) -> None:
        prompt = PROMPT_PATH.read_text()
        crewai = import_module("crewai")
        Agent = getattr(crewai, "Agent")
        self.agent = Agent(model=model, system_prompt=prompt)

    async def generate_questions(self, jd_text: str) -> List[str]:
        response = await asyncio.to_thread(self.agent.run, jd_text)
        if isinstance(response, list):
            return response
        return []
