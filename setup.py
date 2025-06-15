from setuptools import setup, find_packages

setup(
    name="resume_selector",
    version="2.0.0",
    packages=find_packages(),
    install_requires=[
        'PyQt6>=6.0.0',
        'PyQt6-Qt6>=6.0.0',
        'PyQt6-sip>=13.0.0',
        'requests>=2.25.0',
        'pydantic>=1.8.0',
        'python-docx>=0.8.11',
        'pdfminer.six>=20201018',
    ],
    python_requires='>=3.8',
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-powered resume ranking and interview question generation tool",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/resume-selector",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
