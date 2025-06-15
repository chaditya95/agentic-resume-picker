# Resume Selector v2.0

AI-powered resume ranking and interview question generation tool using local LLMs via Ollama.

## 🚀 Features

- **Local AI Processing**: Complete offline operation using Ollama
- **Multi-format Support**: PDF, DOCX, DOC, and TXT resume files
- **Smart Scoring**: AI-driven resume ranking (0-100 scale) with detailed reasoning
- **Interview Questions**: Auto-generated questions tailored to each candidate
- **Modern UI**: Clean, intuitive interface with drag-and-drop support
- **Progress Tracking**: Real-time processing updates
- **Detailed Analysis**: Strengths, concerns, and hiring recommendations
- **Export Functionality**: JSON reports for integration with ATS systems

## 📋 Requirements

### System Requirements
- Windows 10/11, macOS 10.14+, or Linux
- 8GB RAM minimum (16GB recommended for larger models)
- 5GB free disk space

### Prerequisites
- **Ollama**: Must be installed and running
  - Download: https://ollama.ai
  - Recommended models: `llama3.1:8b` (fast) or `llama3.1:70b` (better quality)

## 🛠️ Installation

### Option 1: Pre-built Executable (Recommended)
1. Download the latest release from the releases page
2. Extract the package to your desired location
3. Run `ResumeSelector.exe` (Windows) or `ResumeSelector` (macOS/Linux)

### Option 2: Build from Source
```bash
# Clone the repository
git clone <your-repo-url>
cd resume_selector

# Install dependencies
pip install -r requirements.txt

# Run the application
python -m resume_selector.src.main

# Build executable
./build.sh
```

## 🚀 Quick Start

### 1. Setup Ollama
```bash
# Install and start Ollama
ollama serve

# Pull a model (choose one)
ollama pull llama3.1:8b      # Faster, good quality
ollama pull llama3.1:70b     # Slower, better quality
ollama pull llama3.2:3b      # Fastest, lower quality
```

### 2. Launch Resume Selector
- Run the executable or `python -m resume_selector.src.main`
- The app will check Ollama connection on startup

### 3. Load Your Data
- **Resumes**: Drag and drop resume files to the left panel, or use "Add Resume Files"
- **Job Description**: Click "Load Job Description" or paste directly into the text area

### 4. Configure Analysis
- **AI Model**: Select your preferred model from the dropdown
- **Processing**: The app will process resumes in parallel for speed

### 5. Run Analysis
- Click "▶️ Analyze Resumes" to start processing
- Watch real-time progress in the status bar
- Results appear sorted by score (highest first)

### 6. Review Results
- **Results Table**: Overview of all candidates with scores and recommendations
- **Candidate Details**: Click any row to see detailed analysis
- **Information Includes**:
  - Match score (0-100)
  - Hiring recommendation (Hire/Maybe/Pass)
  - Detailed reasoning
  - Strengths and concerns
  - Extracted skills and experience
  - Custom interview questions

### 7. Export Results
- Click "💾 Export Results" to save as JSON
- Share with hiring team or import into ATS

## 🎯 Usage Tips

### Model Selection
- **llama3.1:8b**: Best balance of speed and quality
- **llama3.1:70b**: Higher quality analysis, slower processing
- **llama3.2:3b**: Fastest processing, good for quick screening

### File Formats
- **PDF**: Best results with text-based PDFs (not scanned images)
- **DOCX/DOC**: Excellent text extraction including tables
- **TXT**: Perfect compatibility, fastest processing

### Performance Optimization
- **Concurrent Processing**: Adjust in config.json if needed
- **Memory**: Close other applications during large batch processing
- **Model Size**: Use smaller models for faster processing on limited hardware

### Best Practices
- **Job Descriptions**: More detailed JDs produce better matching
- **Resume Quality**: Well-formatted resumes yield better analysis
- **Batch Size**: Process 20-50 resumes at once for optimal performance

## ⚙️ Configuration

Edit `config.json` to customize:

```json
{
  "ollama": {
    "base_url": "http://localhost:11434",
    "model": "llama3.1:8b",
    "timeout": 60
  },
  "processing": {
    "max_concurrent_resumes": 3,
    "retry_attempts": 2
  }
}
```

## 🔧 Troubleshooting

### Common Issues

**"Ollama Disconnected"**
- Ensure Ollama is running: `ollama serve`
- Check if model is available: `ollama list`
- Verify URL in config.json

**"Processing Failed"**
- Check available RAM (models need 4-8GB)
- Try a smaller model
- Reduce concurrent processing in config

**"No Results Generated"**
- Verify resume files are readable
- Check job description is loaded
- Review logs in `~/AppData/Local/ResumeSelector/logs/app.log`

### Performance Issues

**Slow Processing**
- Use smaller model (llama3.2:3b)
- Reduce max_concurrent_resumes
- Close other applications

**High Memory Usage**
- Use quantized models when available
- Process fewer resumes at once
- Restart application between large batches

### File Issues

**"Failed to load resume"**
- Ensure file is not corrupted
- Try converting PDF to text format
- Check file permissions

## 🛡️ Privacy & Security

- **Offline Processing**: All analysis happens locally
- **No Data Transmission**: Resume content never leaves your machine
- **Secure Storage**: No permanent storage of sensitive data
- **Local Models**: AI processing via local Ollama installation

## 📊 Export Format

Results are exported as structured JSON:

```json
{
  "metadata": {
    "total_candidates": 25,
    "model_used": "llama3.1:8b",
    "timestamp": "2024-01-15T10:30:00Z"
  },
  "results": [
    {
      "name": "John Doe",
      "filename": "john_doe_resume.pdf",
      "score": 87.5,
      "recommendation": "hire",
      "reasoning": "Strong technical background...",
      "strengths": ["Python expertise", "ML experience"],
      "concerns": ["Limited leadership experience"],
      "skills": ["Python", "Machine Learning", "AWS"],
      "experience": [...],
      "questions": [...]
    }
  ]
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Ollama**: For providing easy local LLM deployment
- **PyQt6**: For the excellent desktop GUI framework
- **pdfminer.six**: For reliable PDF text extraction
- **python-docx**: For DOCX file processing

## 📞 Support

- **Issues**: Report bugs and feature requests on GitHub
- **Logs**: Check `~/AppData/Local/ResumeSelector/logs/app.log` for debugging
- **Ollama Help**: Visit https://ollama.ai for model installation

---