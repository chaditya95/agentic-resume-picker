"""Enhanced main entry point with better error handling"""
import sys
import logging
import os
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

# Add src to path for imports
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from resume_selector.src.ui.main_window import MainWindow
from resume_selector.src.config import Config

def setup_logging():
    """Setup application logging"""
    # Create logs directory
    log_dir = Path.home() / "AppData" / "Local" / "ResumeSelector" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "app.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def main() -> None:
    """Main application entry point"""
    logger = setup_logging()
    logger.info("Starting Resume Selector application")
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Resume Selector")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Resume Selector")
    
    # Enable high DPI support
    try:
        # PyQt6
        from PyQt6.QtCore import Qt
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # PyQt5 or other versions
        pass
    
    try:
        # Create main window
        window = MainWindow()
        window.show()
        
        logger.info("Application started successfully")
        
        # Run application
        sys.exit(app.exec())
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        if 'app' in locals():
            QMessageBox.critical(
                None, "Startup Error",
                f"Failed to start application:\n{str(e)}"
            )
        sys.exit(1)

if __name__ == "__main__":
    main()