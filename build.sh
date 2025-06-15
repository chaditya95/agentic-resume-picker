#!/usr/bin/env bash
set -e

echo "🚀 Building Resume Selector executable..."

# Check if we're in the right directory
if [ ! -f "resume_selector/src/main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
pip install pyinstaller

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist

# Build with PyInstaller
echo "🔨 Building executable..."
pyinstaller \
    --onefile \
    --windowed \
    --name=ResumeSelector \
    --add-data="resume_selector/prompts:prompts" \
    --hidden-import=PyQt6 \
    --hidden-import=pdfminer.six \
    --hidden-import=docx \
    --hidden-import=requests \
    --hidden-import=pydantic \
    resume_selector/src/main.py

# Check if build was successful
if [ -f "dist/ResumeSelector" ] || [ -f "dist/ResumeSelector.exe" ]; then
    echo "✅ Build successful!"
    echo "📁 Executable location: dist/"
    
    # Create package directory
    mkdir -p dist/ResumeSelector_Package
    if [ -f "dist/ResumeSelector.exe" ]; then
        cp dist/ResumeSelector.exe dist/ResumeSelector_Package/
    else
        cp dist/ResumeSelector dist/ResumeSelector_Package/
    fi
    
    # Copy additional files
    cp -r resume_selector/prompts dist/ResumeSelector_Package/
    cp README.md dist/ResumeSelector_Package/ 2>/dev/null || echo "README.md not found, skipping..."
    
    echo "📦 Package created: dist/ResumeSelector_Package/"
    echo "🎉 Build process completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Test the executable"
    echo "2. Make sure Ollama is installed and running"
    echo "3. Distribute the package folder"
else
    echo "❌ Build failed - executable not found"
    exit 1
fi
 