#!/usr/bin/env python3
"""Test resume parsing and UI data handling with actual resume file"""
import sys
import os
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fix Windows console encoding
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

# Add paths
current_dir = Path(__file__).parent
resume_selector_src = current_dir / "resume_selector" / "src"
sys.path.insert(0, str(resume_selector_src))

# Add the project root to Python path
import sys
from pathlib import Path

# Get the project root directory (resume_selector's parent)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from resume_selector.src.models.schema import CandidateReport, CandidateExperience
    from resume_selector.src.agents.parsing_agent import ParsingAgent
    from resume_selector.src.utils.ollama_client import OllamaClient
    from resume_selector.src.utils.file_io import load_resume
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure you're running from the project root directory.")
    sys.exit(1)

async def test_resume_parsing(resume_path: Path) -> Dict[str, Any]:
    """Test parsing a resume file using ParsingAgent"""
    logger.info(f"Testing resume parsing for: {resume_path.name}")
    
    # Initialize Ollama client and parsing agent
    ollama_client = OllamaClient()
    parsing_agent = ParsingAgent("llama3.1:8b", ollama_client)
    
    # Load resume text
    resume_text, success = load_resume(resume_path)
    if not success:
        logger.error(f"Failed to load resume: {resume_path}")
        return {}
    
    # Parse resume
    parsed_data = await parsing_agent.parse(resume_text)
    logger.info(f"Parsed data for {resume_path.name}:")
    
    # Print basic info
    print("\n=== Parsed Resume ===")
    print(f"Name: {parsed_data.get('name', 'Unknown')}")
    print(f"Email: {parsed_data.get('email', 'N/A')}")
    print(f"Phone: {parsed_data.get('phone', 'N/A')}")
    
    # Print skills
    print("\nSkills:")
    for skill in parsed_data.get('skills', [])[:10]:  # Show first 10 skills
        print(f"- {skill}")
    
    # Print experience
    print("\nExperience:")
    for exp in parsed_data.get('experience', [])[:3]:  # Show first 3 experiences
        print(f"- {exp.get('position', 'Unknown')} at {exp.get('company', 'Unknown')} ({exp.get('duration', 'N/A')})")
    
    # Print education
    print("\nEducation:")
    for edu in parsed_data.get('education', [])[:3]:  # Show first 3 education items
        if isinstance(edu, dict):
            print(f"- {edu.get('degree', 'N/A')} - {edu.get('institution', 'N/A')} ({edu.get('year', 'N/A')})")
        else:
            print(f"- {edu}")
    
    return parsed_data

def create_test_report(parsed_data: Dict[str, Any]) -> CandidateReport:
    """Create a CandidateReport from parsed data"""
    logger.info("Creating test report from parsed data")
    
    # Convert experience to CandidateExperience objects
    experience = []
    for exp in parsed_data.get('experience', []):
        if isinstance(exp, dict):
            exp_obj = CandidateExperience(
                company=exp.get('company', 'Unknown'),
                position=exp.get('position', 'Unknown'),
                duration=exp.get('duration', 'N/A')
            )
            experience.append(exp_obj)
    
    # Create report
    report = CandidateReport(
        name=parsed_data.get('name', 'Unknown'),
        skills=parsed_data.get('skills', []),
        education=parsed_data.get('education', []),
        experience=experience,
        questions=["What's your experience with Python?"],
        score=85.0,
        reasoning="Strong technical background",
        strengths=["Good problem solver", "Team player"],
        concerns=["Limited industry experience"],
        recommendation="hire"
    )
    
    # Test attribute access
    print("\n[TEST] CandidateReport attribute access:")
    print(f"Name: {report.name}")
    print(f"Score: {report.score}")
    print(f"Skills: {report.skills}")
    print(f"Experience: {[f'{exp.position} at {exp.company}' for exp in report.experience]}")
    
    # Test dictionary conversion
    report_dict = report.dict()
    print("\n[TEST] Dictionary conversion:")
    print(f"Type: {type(report_dict)}")
    print(f"Name in dict: {report_dict.get('name')}")
    
    return report

async def test_result_handling(parsed_data: Dict[str, Any]):
    """Test handling of parsed results in the UI"""
    logger.info("Testing result handling with parsed data")
    
    # Create test report from parsed data
    report = create_test_report(parsed_data)
    
    # Test single result
    print("\n[TEST] Single Result:")
    print(f"Type: {type(report)}")
    print(f"Name: {report.name}")
    print(f"Skills: {', '.join(report.skills[:3])}...")
    
    # Test list of results
    results = [report, report]
    print("\n[TEST] List of Results:")
    print(f"Number of results: {len(results)}")
    print(f"First item type: {type(results[0])}")
    
    # Test dictionary conversion
    report_dict = report.dict()
    print("\n[TEST] Dictionary Conversion:")
    print(f"Type: {type(report_dict)}")
    print(f"Name in dict: {report_dict.get('name')}")
    print(f"Skills in dict: {report_dict.get('skills', [])[:3]}...")
    
    return results

async def main():
    print("=== Testing Resume Parsing and UI Data Handling ===\n")
    
    # Find the resume file
    resume_filename = "VENKATA ADITYA CHINTALA - AI Engineer.docx"
    
    # Try multiple possible locations
    possible_paths = [
        Path(resume_filename),  # Current directory
        project_root / resume_filename,  # Project root
        project_root / "resumes" / resume_filename,  # Resumes subdirectory
        project_root.parent / resume_filename  # Parent directory
    ]
    
    resume_path = None
    for path in possible_paths:
        if path.exists():
            resume_path = path
            break
            
    if not resume_path or not resume_path.exists():
        print("\n[ERROR] Could not find resume file. Tried the following locations:")
        for path in possible_paths:
            print(f"- {path.absolute()}")
        print("\nPlease ensure the resume file exists in one of these locations.")
        return
    
    try:
        # Test resume parsing
        parsed_data = await test_resume_parsing(resume_path)
        if not parsed_data:
            print("Error: Failed to parse resume")
            return
        
        # Test result handling with parsed data
        test_results = await test_result_handling(parsed_data)
        
        print("\n[SUCCESS] All tests completed!")
        print(f"Final results type: {type(test_results)}")
        print(f"Number of results: {len(test_results) if test_results else 0}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
