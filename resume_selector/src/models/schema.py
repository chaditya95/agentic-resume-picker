from typing import List, Optional, Union, Any
from pydantic import BaseModel, Field, validator


class CandidateExperience(BaseModel):
    company: str = ""
    position: str = ""
    duration: str = ""


class CandidateReport(BaseModel):
    name: str = "Unknown"
    skills: List[str] = Field(default_factory=list)
    education: List[Union[str, dict]] = Field(default_factory=list)  # Allow both strings and dicts
    experience: List[CandidateExperience] = Field(default_factory=list)
    questions: List[Union[str, dict]] = Field(default_factory=list)  # Allow both strings and dicts
    score: float = Field(default=0.0, ge=0.0, le=100.0)
    reasoning: Optional[str] = ""
    strengths: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    recommendation: str = "pass"
    filename: Optional[str] = ""
    
    @validator('education', pre=True)
    def convert_education(cls, v):
        """Convert education entries to strings if they're dicts"""
        if not v:
            return []
        
        result = []
        for item in v:
            if isinstance(item, dict):
                # Convert dict to string representation
                if 'degree' in item and 'year' in item:
                    result.append(f"{item['degree']} ({item['year']})")
                else:
                    result.append(str(item))
            else:
                result.append(str(item))
        return result
    
    @validator('questions', pre=True)
    def convert_questions(cls, v):
        """Convert question entries to strings if they're dicts"""
        if not v:
            return []
        
        result = []
        for item in v:
            if isinstance(item, dict):
                # Extract question text from dict
                if 'question' in item:
                    result.append(item['question'])
                elif 'q' in item:
                    result.append(item['q'])
                else:
                    result.append(str(item))
            else:
                result.append(str(item))
        return result
    
    @validator('experience', pre=True)
    def convert_experience(cls, v):
        """Convert experience entries to CandidateExperience objects"""
        if not v:
            return []
        
        result = []
        for item in v:
            if isinstance(item, dict):
                result.append(CandidateExperience(
                    company=item.get('company', ''),
                    position=item.get('position', ''),
                    duration=item.get('duration', '')
                ))
            elif isinstance(item, CandidateExperience):
                result.append(item)
            else:
                # If it's a string, try to parse it
                result.append(CandidateExperience(
                    company="Unknown",
                    position=str(item),
                    duration=""
                ))
        return result

    class Config:
        # Allow extra fields and be more permissive
        extra = "ignore"
        validate_assignment = True