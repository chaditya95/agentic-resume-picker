#!/usr/bin/env python3
"""Test the fixed models"""
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if os.name == 'nt':  # Windows
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

# Add paths
current_dir = Path(__file__).parent
resume_selector_src = current_dir / "resume_selector" / "src"
sys.path.insert(0, str(resume_selector_src))

from models.schema import CandidateReport, CandidateExperience

# Test with problematic data from logs
test_data = {
    "name": "VENKATA ADITYA CHINTALA",
    "skills": ["AI", "Python"],
    "education": [{"degree": "Master of Science", "year": "2019"}],  # This was causing the error
    "experience": [
        {
            "company": "Some Company",
            "position": "Engineer",
            "duration": "2019-2023"
        }
    ],
    "questions": ["What is your experience?"],
    "score": 85.0
}

try:
    report = CandidateReport(**test_data)
    print("[SUCCESS] Model validation successful!")
    print(f"Name: {report.name}")
    print(f"Education: {report.education}")
    print(f"Score: {report.score}")
    print(f"Experience: {len(report.experience)} entries")
    print("[SUCCESS] All data properly converted!")
except Exception as e:
    print(f"[ERROR] Model validation failed: {e}")
    import traceback
    traceback.print_exc()