from typing import Dict
import asyncio
from pathlib import Path
from importlib import import_module

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "scoring_prompt.txt"

class ScoringAgent:
    def __init__(self, model: str) -> None:
        prompt = PROMPT_PATH.read_text()
        crewai = import_module("crewai")
        Agent = getattr(crewai, "Agent")
        self.agent = Agent(model=model, system_prompt=prompt)

    async def score(self, parsed_resume: Dict, jd_text: str) -> float:
        input_text = f"Job Description:\n{jd_text}\nResume:\n{parsed_resume}"
        response = await asyncio.to_thread(self.agent.run, input_text)
        try:
            return float(response)
        except Exception:
            return 0.0
