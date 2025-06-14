from typing import List, Dict, Any
import asyncio
from pathlib import Path
from importlib import import_module

PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "parsing_prompt.txt"


class ParsingAgent:
    def __init__(self, model: str) -> None:
        prompt = PROMPT_PATH.read_text()
        crewai = import_module("crewai")
        Agent = getattr(crewai, "Agent")
        self.agent = Agent(model=model, system_prompt=prompt)

    async def parse(self, resumes: List[str]) -> Dict[str, Any]:
        joined = "\n".join(resumes)
        response = await asyncio.to_thread(self.agent.run, joined)
        if isinstance(response, dict):
            return response
        return {}
