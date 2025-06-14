from typing import List
from pydantic import BaseModel


class CandidateExperience(BaseModel):
    company: str
    position: str
    duration: str


class CandidateReport(BaseModel):
    name: str
    skills: List[str]
    education: List[str]
    experience: List[CandidateExperience]
    questions: List[str]
