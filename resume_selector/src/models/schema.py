"""Enhanced data models"""
from typing import List, Optional
from pydantic import BaseModel, Field


class CandidateExperience(BaseModel):
    company: str
    position: str
    duration: str
    description: Optional[str] = ""


class CandidateReport(BaseModel):
    name: str
    skills: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    experience: List[CandidateExperience] = Field(default_factory=list)
    questions: List[str] = Field(default_factory=list)
    score: float = Field(default=0.0, ge=0.0, le=100.0)
    reasoning: Optional[str] = ""
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    recommendation: str = "pass"
    filename: Optional[str] = ""
    
    class Config:
        schema_extra = {
            "example": {
                "name": "John Doe",
                "skills": ["Python", "Machine Learning", "AWS"],
                "education": ["BS Computer Science, MIT, 2020"],
                "experience": [
                    {
                        "company": "Tech Corp",
                        "position": "Software Engineer",
                        "duration": "2020-2023",
                        "description": "Developed ML pipelines"
                    }
                ],
                "questions": ["Tell me about your Python experience"],
                "score": 85.0,
                "reasoning": "Strong technical background with relevant experience",
                "strengths": ["Python expertise", "ML experience"],
                "concerns": ["Limited leadership experience"],
                "recommendation": "hire",
                "filename": "john_doe_resume.pdf"
            }
        }


class ProcessingResult(BaseModel):
    """Result of processing operation"""
    success: bool
    message: str
    reports: List[CandidateReport] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)