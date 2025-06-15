"""Enhanced main window with progress tracking and better error handling"""
import logging
import json
from pathlib import Path
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
import threading

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QTextEdit, QPushButton, 
    QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox, QProgressBar,
    QLabel, QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QGroupBox, QTreeWidget, QTreeWidgetItem, QStatusBar, QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent

from ..orchestrator import Orchestrator
from ..config import Config
from ..utils.ollama_client import OllamaClient
from ..utils.file_io import is_supported_file, load_resume
from .widgets import ResumeListWidget
from .dialogs import open_file

logger = logging.getLogger(__name__)


class ProcessingThread(QThread):
    """Thread for processing resumes in background"""
    progress_updated = pyqtSignal(int, int, str)  # current, total, filename
    processing_complete = pyqtSignal(list)  # results
    processing_error = pyqtSignal(str)  # error message
    
    def __init__(self, orchestrator: Orchestrator, resume_paths: List[Path], jd_text: str):
        super().__init__()
        self.orchestrator = orchestrator
        self.resume_paths = resume_paths
        self.jd_text = jd_text
    
    def run(self):
        """Run processing in background thread"""
        try:
            def progress_callback(current, total, filename):
                self.progress_updated.emit(current, total, filename)
            
            results = self.orchestrator.run_with_progress(
                self.resume_paths, self.jd_text, progress_callback
            )
            self.processing_complete.emit(results)
            
        except Exception as e:
            logger.error(f"Processing thread error: {e}")
            self.processing_error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.config = Config()
        self.ollama_client = OllamaClient(
            base_url=self.config.get('ollama.base_url', 'http://localhost:11434')
        )
        self.orchestrator = Orchestrator(
            model=self.config.get('ollama.model', 'llama3.1:8b')
        )
        
        # UI state
        self.resume_paths: List[Path] = []
        self.current_results: List = []
        self.processing_thread: Optional[ProcessingThread] = None
        
        self.setWindowTitle("Resume Selector v2.0")
        self.setGeometry(100, 100, 
                        self.config.get('ui.window_width', 1200),
                        self.config.get('ui.window_height', 800))
        
        self._setup_ui()
        self._check_ollama_connection()
    
    def _setup_ui(self):
        """Setup the user interface"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Toolbar
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)
        
        # Content area
        content_splitter = self._create_content_area()
        main_layout.addWidget(content_splitter)
        
        # Status bar
        self._create_status_bar()
        
        # Apply styling
        self._apply_styling()
    
    def _create_toolbar(self) -> QWidget:
        """Create toolbar with controls"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        
        # Model selection
        model_group = QGroupBox("AI Model")
        model_layout = QHBoxLayout(model_group)
        
        self.combo_model = QComboBox()
        self.combo_model.addItems([
            "llama3.1:8b", "llama3.1:70b", "llama3.2:3b", 
            "codellama:13b", "mistral:7b"
        ])
        self.combo_model.setCurrentText(self.config.get('ollama.model', 'llama3.1:8b'))
        model_layout.addWidget(self.combo_model)
        
        layout.addWidget(model_group)
        layout.addStretch()
        
        # Action buttons
        self.btn_load_jd = QPushButton("📄 Load Job Description")
        self.btn_load_jd.clicked.connect(self.load_jd)
        layout.addWidget(self.btn_load_jd)
        
        self.btn_run = QPushButton("▶️ Analyze Resumes")
        self.btn_run.clicked.connect(self.run_orchestration)
        self.btn_run.setEnabled(False)
        layout.addWidget(self.btn_run)
        
        self.btn_export = QPushButton("💾 Export Results")
        self.btn_export.clicked.connect(self.export_results)
        self.btn_export.setEnabled(False)
        layout.addWidget(self.btn_export)
        
        return toolbar
    
    def _create_content_area(self) -> QSplitter:
        """Create main content area with three panes"""
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left pane: Resume list
        left_pane = self._create_left_pane()
        splitter.addWidget(left_pane)
        
        # Center pane: Job description and resume preview
        center_pane = self._create_center_pane()
        splitter.addWidget(center_pane)
        
        # Right pane: Results
        right_pane = self._create_right_pane()
        splitter.addWidget(right_pane)
        
        # Set proportions
        splitter.setSizes([300, 400, 500])
        
        return splitter
    
    def _create_left_pane(self) -> QWidget:
        """Create left pane with resume list"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Resume list
        resume_group = QGroupBox("Resume Files")
        resume_layout = QVBoxLayout(resume_group)
        
        self.resume_list = ResumeListWidget()
        self.resume_list.files_dropped.connect(self.on_files_dropped)
        resume_layout.addWidget(self.resume_list)
        
        # Add files button
        btn_add_files = QPushButton("📁 Add Resume Files")
        btn_add_files.clicked.connect(self.add_resume_files)
        resume_layout.addWidget(btn_add_files)
        
        # Clear button
        btn_clear = QPushButton("🗑️ Clear All")
        btn_clear.clicked.connect(self.clear_resumes)
        resume_layout.addWidget(btn_clear)
        
        layout.addWidget(resume_group)
        
        # Resume count
        self.label_resume_count = QLabel("No resumes loaded")
        layout.addWidget(self.label_resume_count)
        
        return widget
    
    def _create_center_pane(self) -> QWidget:
        """Create center pane with job description and preview"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Job description section
        jd_group = QGroupBox("Job Description")
        jd_layout = QVBoxLayout(jd_group)
        
        self.jd_text = QTextEdit()
        self.jd_text.setPlaceholderText("Load or paste job description here...")
        self.jd_text.textChanged.connect(self.check_ready_state)
        jd_layout.addWidget(self.jd_text)
        
        layout.addWidget(jd_group)
        
        # Resume preview section  
        preview_group = QGroupBox("Resume Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        self.text_resume_preview = QTextEdit()
        self.text_resume_preview.setReadOnly(True)
        self.text_resume_preview.setPlaceholderText("Select a resume to preview...")
        preview_layout.addWidget(self.text_resume_preview)
        
        layout.addWidget(preview_group)
        
        return widget
    
    def _create_right_pane(self) -> QWidget:
        """Create right pane with results"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Results table
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_group)
        
        self.table_results = QTableWidget()
        self.table_results.setColumnCount(4)
        self.table_results.setHorizontalHeaderLabels([
            "Candidate", "Score", "Recommendation", "Top Skills"
        ])
        
        # Configure table
        header = self.table_results.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_results.setColumnWidth(1, 80)
        self.table_results.setColumnWidth(2, 100)
        
        self.table_results.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_results.itemSelectionChanged.connect(self.on_result_selected)
        
        results_layout.addWidget(self.table_results)
        layout.addWidget(results_group)
        
        # Details section
        details_group = QGroupBox("Candidate Details")
        details_layout = QVBoxLayout(details_group)
        
        self.text_details = QTextEdit()
        self.text_details.setReadOnly(True)
        self.text_details.setPlaceholderText("Select a candidate to see details...")
        details_layout.addWidget(self.text_details)
        
        layout.addWidget(details_group)
        
        return widget
    
    def _create_status_bar(self):
        """Create status bar with progress"""
        self.status_bar = self.statusBar()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Connection status
        self.label_connection = QLabel()
        self.status_bar.addPermanentWidget(self.label_connection)
        
        self.status_bar.showMessage("Ready")
    
    def _apply_styling(self):
        """Apply custom styling"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #d0d0d0;
                border-radius: 8px;
                margin: 5px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                background-color: #f5f5f5;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QTableWidget::item:selected {
                background-color: #3daee9;
                color: white;
            }
            QTextEdit {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
                font-family: 'Consolas', 'Monaco', monospace;
            }
            QComboBox {
                padding: 8px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
            }
        """)
    
    def _check_ollama_connection(self):
        """Check Ollama connection status"""
        if self.ollama_client.is_connected():
            self.label_connection.setText("🟢 Ollama Connected")
            self.label_connection.setStyleSheet("color: green;")
        else:
            self.label_connection.setText("🔴 Ollama Disconnected")
            self.label_connection.setStyleSheet("color: red;")
            QMessageBox.warning(
                self, "Ollama Connection",
                "Could not connect to Ollama. Please ensure Ollama is running.\n"
                "Visit https://ollama.ai for installation instructions."
            )
    
    def add_resume_files(self):
        """Add resume files via file dialog"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Resume Files", "",
            "Resume Files (*.pdf *.docx *.doc *.txt);;All Files (*)"
        )
        
        if files:
            new_paths = [Path(f) for f in files if is_supported_file(Path(f))]
            self.on_files_dropped(new_paths)
    
    def on_files_dropped(self, file_paths: List[Path]):
        """Handle dropped files"""
        for path in file_paths:
            if is_supported_file(path) and path not in self.resume_paths:
                self.resume_paths.append(path)
                self.resume_list.addItem(str(path))
        
        self.update_resume_count()
        self.check_ready_state()
    
    def clear_resumes(self):
        """Clear all resume files"""
        self.resume_paths.clear()
        self.resume_list.clear()
        self.text_resume_preview.clear()
        self.update_resume_count()
        self.check_ready_state()
    
    def update_resume_count(self):
        """Update resume count display"""
        count = len(self.resume_paths)
        self.label_resume_count.setText(f"{count} resume(s) loaded")
    
    def load_jd(self):
        """Load job description from file"""
        path = open_file(self, "Open Job Description", 
                        "Text Files (*.txt);;PDF Files (*.pdf);;Word Documents (*.docx);;All Files (*)")
        if path:
            try:
                text, success = load_resume(path)
                if success:
                    self.jd_text.setPlainText(text)
                    self.status_bar.showMessage(f"Job description loaded from {path.name}")
                else:
                    QMessageBox.warning(self, "Load Error", 
                                      f"Failed to load job description from {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error loading file: {str(e)}")
    
    def check_ready_state(self):
        """Check if ready to run analysis"""
        has_resumes = len(self.resume_paths) > 0
        has_jd = bool(self.jd_text.toPlainText().strip())
        is_connected = self.ollama_client.is_connected()
        
        self.btn_run.setEnabled(has_resumes and has_jd and is_connected)
    
    def run_orchestration(self):
        """Run the orchestration process"""
        if self.processing_thread and self.processing_thread.isRunning():
            QMessageBox.warning(self, "Processing", "Analysis is already running!")
            return
        
        jd_text = self.jd_text.toPlainText().strip()
        if not jd_text or not self.resume_paths:
            QMessageBox.warning(self, "Missing Data", 
                              "Please load resumes and job description first.")
            return
        
        # Update model
        selected_model = self.combo_model.currentText()
        self.orchestrator.model = selected_model
        
        # Start processing
        self.start_processing()
        
        # Create and start processing thread
        self.processing_thread = ProcessingThread(
            self.orchestrator, self.resume_paths, jd_text
        )
        self.processing_thread.progress_updated.connect(self.on_progress_update)
        self.processing_thread.processing_complete.connect(self.on_processing_complete)
        self.processing_thread.processing_error.connect(self.on_processing_error)
        self.processing_thread.start()
    
    def start_processing(self):
        """Start processing UI state"""
        self.btn_run.setEnabled(False)
        self.btn_run.setText("Processing...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(self.resume_paths))
        self.table_results.setRowCount(0)
        self.text_details.clear()
    
    def on_progress_update(self, current: int, total: int, filename: str):
        """Handle progress updates"""
        self.progress_bar.setValue(current)
        self.status_bar.showMessage(f"Processing {current}/{total}: {filename}")
    
    def on_processing_complete(self, results: List):
        """Handle processing completion"""
        self.current_results = results
        self.populate_results_table()
        self.finish_processing()
        
        if results:
            self.btn_export.setEnabled(True)
            QMessageBox.information(
                self, "Analysis Complete",
                f"Successfully analyzed {len(results)} candidates!"
            )
        else:
            QMessageBox.warning(
                self, "No Results", 
                "Analysis completed but no valid results were generated."
            )
    
    def on_processing_error(self, error_message: str):
        """Handle processing errors"""
        self.finish_processing()
        QMessageBox.critical(self, "Processing Error", 
                           f"Analysis failed:\n{error_message}")
    
    def finish_processing(self):
        """Finish processing UI state"""
        self.btn_run.setEnabled(True)
        self.btn_run.setText("▶️ Analyze Resumes")
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Ready")
        self.check_ready_state()
    
    def populate_results_table(self):
        """Populate results table"""
        self.table_results.setRowCount(len(self.current_results))
        
        for row, result in enumerate(self.current_results):
            # Candidate name
            name_item = QTableWidgetItem(result.name)
            self.table_results.setItem(row, 0, name_item)
            
            # Score with color coding
            score_item = QTableWidgetItem(f"{result.score:.1f}")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Color code by score
            if result.score >= 80:
                score_item.setBackground(Qt.GlobalColor.green)
            elif result.score >= 60:
                score_item.setBackground(Qt.GlobalColor.yellow)
            else:
                score_item.setBackground(Qt.GlobalColor.red)
            
            self.table_results.setItem(row, 1, score_item)
            
            # Recommendation
            rec_item = QTableWidgetItem(result.recommendation.title())
            rec_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_results.setItem(row, 2, rec_item)
            
            # Top skills
            skills_text = ", ".join(result.skills[:3])
            if len(result.skills) > 3:
                skills_text += "..."
            skills_item = QTableWidgetItem(skills_text)
            self.table_results.setItem(row, 3, skills_item)
        
        # Auto-select first row
        if self.current_results:
            self.table_results.selectRow(0)
    
    def on_result_selected(self):
        """Handle result selection"""
        selected_rows = self.table_results.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        if 0 <= row < len(self.current_results):
            result = self.current_results[row]
            self.display_candidate_details(result)
    
    def display_candidate_details(self, result):
        """Display detailed candidate information"""
        details = f"""CANDIDATE: {result.name}
FILENAME: {result.filename}
SCORE: {result.score:.1f}/100
RECOMMENDATION: {result.recommendation.upper()}

REASONING:
{result.reasoning}

STRENGTHS:
{chr(10).join('• ' + s for s in result.strengths)}

CONCERNS:
{chr(10).join('• ' + c for c in result.concerns)}

SKILLS:
{', '.join(result.skills)}

EDUCATION:
{chr(10).join('• ' + e for e in result.education)}

EXPERIENCE:
{chr(10).join(f'• {exp.position} at {exp.company} ({exp.duration})' for exp in result.experience)}

INTERVIEW QUESTIONS:
{chr(10).join(f'{i+1}. {q}' for i, q in enumerate(result.questions))}
"""
        self.text_details.setPlainText(details)
    
    def export_results(self):
        """Export results to JSON"""
        if not self.current_results:
            QMessageBox.warning(self, "No Results", "No results to export.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Results", "resume_analysis_results.json",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                export_data = {
                    "metadata": {
                        "total_candidates": len(self.current_results),
                        "model_used": self.combo_model.currentText(),
                        "timestamp": "2024-01-01T00:00:00Z"  # You can add actual timestamp
                    },
                    "results": [result.dict() for result in self.current_results]
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(
                    self, "Export Successful",
                    f"Results exported to:\n{file_path}"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self, "Export Error",
                    f"Failed to export results:\n{str(e)}"
                )
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.processing_thread and self.processing_thread.isRunning():
            reply = QMessageBox.question(
                self, "Processing in Progress",
                "Analysis is still running. Do you want to stop and exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.processing_thread.terminate()
                event.accept()
            else:
                event.ignore()
        else:
            self.config.save()
            event.accept()