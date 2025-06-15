#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add paths
current_dir = Path(__file__).parent
resume_selector_src = current_dir / "resume_selector" / "src"
sys.path.insert(0, str(resume_selector_src))

print("Python path:")
for p in sys.path[:5]:
    print(f"  {p}")

print(f"\nCurrent directory: {current_dir}")
print(f"Resume selector src: {resume_selector_src}")
print(f"Src exists: {resume_selector_src.exists()}")

try:
    from PyQt6.QtWidgets import QApplication
    print("✓ PyQt6 import successful")
except ImportError as e:
    print(f"✗ PyQt6 import failed: {e}")
    print("Run: pip install PyQt6")
    sys.exit(1)

try:
    from ui.main_window import MainWindow
    print("✓ MainWindow import successful")
    
    # Create simple app
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    print("✓ Application started successfully")
    sys.exit(app.exec())
    
except ImportError as e:
    print(f"✗ MainWindow import failed: {e}")
    print("Let's check what files exist...")
    
    ui_dir = resume_selector_src / "ui"
    if ui_dir.exists():
        print(f"UI directory contents: {list(ui_dir.iterdir())}")
    else:
        print("UI directory doesn't exist!")

except Exception as e:
    print(f"✗ Other error: {e}")