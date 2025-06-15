"""
Enhanced Main Window - resume_selector/src/ui/main_window.py
"""
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
    QGroupBox, QTreeWidget, QTreeWidgetItem, QStatusBar, QApplication,
    QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QDragEnterEvent, QDropEvent

from ..orchestrator import Orchestrator
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
            
            self.orchestrator.set_progress_callback(progress_callback)
            results = self.orchestrator.run_sync(self.resume_paths, self.jd_text)
            self.processing_complete.emit(results)
            
        except Exception as e:
            logger.error(f"Processing thread error: {e}")
            self.processing_error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.ollama_client = OllamaClient()
        self.orchestrator = Orchestrator(model="llama3.1:8b")
        
        # UI state
        self.resume_paths: List[Path] = []
        self.current_results: List = []
        self.processing_thread: Optional[ProcessingThread] = None
        
        self.setWindowTitle("Resume Selector v2.0 - AI-Powered Resume Analysis")
        self.setGeometry(100, 100, 1600, 1000)  # Larger window
        
        self._setup_ui()
        self._check_ollama_connection()
    
    def _setup_ui(self):
        """Setup the enhanced user interface"""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Top toolbar
        toolbar = self._create_enhanced_toolbar()
        main_layout.addWidget(toolbar)
        
        # Main content area with new layout
        content_splitter = self._create_enhanced_content_area()
        main_layout.addWidget(content_splitter)
        
        # Status bar
        self._create_enhanced_status_bar()
        
        # Apply modern styling
        self._apply_modern_styling()
    
    def _create_enhanced_toolbar(self) -> QWidget:
        """Create enhanced toolbar with better model selection"""
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.Shape.StyledPanel)
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        
        layout = QHBoxLayout(toolbar)
        layout.setSpacing(15)
        
        # AI Model selection - Enhanced
        model_group = QGroupBox("🤖 AI Model")
        model_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                color: #495057;
            }
        """)
        model_layout = QVBoxLayout(model_group)
        
        self.combo_model = QComboBox()
        self.combo_model.addItems([
            "llama3.1:8b (Recommended)", 
            "llama3.1:70b (High Quality)", 
            "llama3.2:3b (Fast)",
            "codellama:13b (Code Focus)", 
            "mistral:7b (Alternative)"
        ])
        self.combo_model.setCurrentText("llama3.1:8b (Recommended)")
        self.combo_model.setMinimumWidth(200)
        self.combo_model.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 2px solid #e9ecef;
                border-radius: 6px;
                background-color: white;
                font-size: 13px;
            }
            QComboBox:focus {
                border-color: #007bff;
            }
        """)
        model_layout.addWidget(self.combo_model)
        
        layout.addWidget(model_group)
        layout.addStretch()
        
        # Action buttons - Enhanced
        button_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4CAF50, stop:1 #45a049);
                color: white;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                min-width: 140px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #45a049, stop:1 #3d8b40);
            }
            QPushButton:pressed {
                background: #3d8b40;
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #666666;
            }
        """
        
        self.btn_load_jd = QPushButton("📄 Load Job Description")
        self.btn_load_jd.clicked.connect(self.load_jd)
        self.btn_load_jd.setStyleSheet(button_style)
        layout.addWidget(self.btn_load_jd)
        
        self.btn_run = QPushButton("🚀 Analyze Resumes")
        self.btn_run.clicked.connect(self.run_orchestration)
        self.btn_run.setEnabled(False)
        self.btn_run.setStyleSheet(button_style.replace("#4CAF50", "#007bff").replace("#45a049", "#0056b3").replace("#3d8b40", "#004085"))
        layout.addWidget(self.btn_run)
        
        self.btn_export = QPushButton("💾 Export Results")
        self.btn_export.clicked.connect(self.export_results)
        self.btn_export.setEnabled(False)
        self.btn_export.setStyleSheet(button_style.replace("#4CAF50", "#6c757d").replace("#45a049", "#5a6268").replace("#3d8b40", "#495057"))
        layout.addWidget(self.btn_export)
        
        return toolbar
    
    def _create_enhanced_content_area(self) -> QSplitter:
        """Create enhanced content area with new layout"""
        main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_splitter.setHandleWidth(8)
        
        # Left panel (Resume files + Job Description)
        left_panel = self._create_left_panel()
        main_splitter.addWidget(left_panel)
        
        # Center panel (Resume preview) - MAXIMIZED
        center_panel = self._create_center_panel()
        main_splitter.addWidget(center_panel)
        
        # Right panel (Analysis results)
        right_panel = self._create_right_panel()
        main_splitter.addWidget(right_panel)
        
        # Set proportions: Left(300), Center(600), Right(500)
        main_splitter.setSizes([300, 600, 500])
        
        return main_splitter
    
    def _create_left_panel(self) -> QWidget:
        """Create left panel with resume files and job description"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Resume files section
        resume_group = QGroupBox("📁 Resume Files")
        resume_layout = QVBoxLayout(resume_group)
        
        self.resume_list = ResumeListWidget()
        self.resume_list.files_dropped.connect(self.on_files_dropped)
        self.resume_list.setMinimumHeight(200)
        resume_layout.addWidget(self.resume_list)
        
        # Resume action buttons
        resume_buttons = QHBoxLayout()
        
        btn_add_files = QPushButton("➕ Add Files")
        btn_add_files.clicked.connect(self.add_resume_files)
        btn_add_files.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        resume_buttons.addWidget(btn_add_files)
        
        btn_clear = QPushButton("🗑️ Clear")
        btn_clear.clicked.connect(self.clear_resumes)
        btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #c82333; }
        """)
        resume_buttons.addWidget(btn_clear)
        
        resume_layout.addLayout(resume_buttons)
        
        # Resume count
        self.label_resume_count = QLabel("No resumes loaded")
        self.label_resume_count.setStyleSheet("color: #6c757d; font-style: italic;")
        resume_layout.addWidget(self.label_resume_count)
        
        layout.addWidget(resume_group)
        
        # Job Description section (moved to left panel bottom)
        jd_group = QGroupBox("📄 Job Description")
        jd_layout = QVBoxLayout(jd_group)
        
        self.jd_text = QTextEdit()
        self.jd_text.setPlaceholderText("Load or paste job description here...")
        self.jd_text.textChanged.connect(self.check_ready_state)
        self.jd_text.setMinimumHeight(200)
        self.jd_text.setMaximumHeight(300)
        jd_layout.addWidget(self.jd_text)
        
        layout.addWidget(jd_group)
        
        return widget
    
    def _create_center_panel(self) -> QWidget:
        """Create center panel focused on resume preview"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Resume preview section - MAXIMIZED
        preview_group = QGroupBox("📋 Resume Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Add resume selection info
        self.label_current_resume = QLabel("Select a resume to preview...")
        self.label_current_resume.setStyleSheet("""
            QLabel {
                color: #495057;
                font-weight: bold;
                font-size: 14px;
                padding: 8px;
                background-color: #f8f9fa;
                border-radius: 4px;
            }
        """)
        preview_layout.addWidget(self.label_current_resume)
        
        self.text_resume_preview = QTextEdit()
        self.text_resume_preview.setReadOnly(True)
        self.text_resume_preview.setPlaceholderText("Resume content will appear here...")
        self.text_resume_preview.setStyleSheet("""
            QTextEdit {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 15px;
                background-color: white;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                line-height: 1.4;
            }
        """)
        preview_layout.addWidget(self.text_resume_preview)
        
        layout.addWidget(preview_group)
        
        return widget
    
    def _create_right_panel(self) -> QWidget:
        """Create right panel with analysis results"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # Results table
        results_group = QGroupBox("📊 Analysis Results")
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
        self.table_results.setColumnWidth(1, 70)
        self.table_results.setColumnWidth(2, 90)
        
        self.table_results.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_results.itemSelectionChanged.connect(self.on_result_selected)
        self.table_results.setAlternatingRowColors(True)
        self.table_results.setMinimumHeight(250)
        
        results_layout.addWidget(self.table_results)
        layout.addWidget(results_group)
        
        # Candidate details section
        details_group = QGroupBox("👤 Candidate Details")
        details_layout = QVBoxLayout(details_group)
        
        # Create scrollable area for details
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        self.text_details = QTextEdit()
        self.text_details.setReadOnly(True)
        self.text_details.setPlaceholderText("Select a candidate to see detailed analysis...")
        self.text_details.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                padding: 12px;
                background-color: white;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 12px;
            }
        """)
        
        scroll_area.setWidget(self.text_details)
        details_layout.addWidget(scroll_area)
        
        layout.addWidget(details_group)
        
        return widget
    
    def _create_enhanced_status_bar(self):
        """Create enhanced status bar"""
        self.status_bar = self.statusBar()
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                color: #495057;
            }
        """)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: #e9ecef;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 3px;
            }
        """)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Connection status
        self.label_connection = QLabel()
        self.status_bar.addPermanentWidget(self.label_connection)
        
        self.status_bar.showMessage("Ready")
    
    def _apply_modern_styling(self):
        """Apply modern styling to the application"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin: 8px 0;
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background-color: #ffffff;
                border-radius: 4px;
            }
            QTableWidget {
                gridline-color: #dee2e6;
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                selection-background-color: #007bff;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f3f4;
            }
            QTableWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QTableWidget QHeaderView::section {
                background-color: #f8f9fa;
                padding: 10px;
                border: none;
                border-bottom: 2px solid #dee2e6;
                font-weight: bold;
            }
            QTextEdit {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
                background-color: white;
                font-size: 13px;
            }
            QTextEdit:focus {
                border-color: #007bff;
            }
            QListWidget {
                border: 2px solid #e9ecef;
                border-radius: 8px;
                background-color: white;
                padding: 8px;
            }
            QSplitter::handle {
                background-color: #dee2e6;
                border-radius: 2px;
            }
            QSplitter::handle:hover {
                background-color: #007bff;
            }
        """)
    
    def _check_ollama_connection(self):
        """Check Ollama connection status"""
        if self.ollama_client.is_connected():
            self.label_connection.setText("🟢 Ollama Connected")
            self.label_connection.setStyleSheet("color: #28a745; font-weight: bold;")
        else:
            self.label_connection.setText("🔴 Ollama Disconnected")
            self.label_connection.setStyleSheet("color: #dc3545; font-weight: bold;")
            QMessageBox.warning(
                self, "Ollama Connection",
                "Could not connect to Ollama. Please ensure Ollama is running.\n"
                "Visit https://ollama.ai for installation instructions."
            )
    
    # [Keep all your existing methods: add_resume_files, on_files_dropped, clear_resumes, 
    #  update_resume_count, load_jd, check_ready_state, run_orchestration, etc.]
    
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
                self.resume_list.addItem(str(path.name))  # Show only filename
        
        self.update_resume_count()
        self.check_ready_state()
        
        # Auto-preview first resume if none selected
        if len(self.resume_paths) == 1:
            self.preview_resume(self.resume_paths[0])
    
    def clear_resumes(self):
        """Clear all resume files"""
        self.resume_paths.clear()
        self.resume_list.clear()
        self.text_resume_preview.clear()
        self.label_current_resume.setText("Select a resume to preview...")
        self.update_resume_count()
        self.check_ready_state()
    
    def update_resume_count(self):
        """Update resume count display"""
        count = len(self.resume_paths)
        self.label_resume_count.setText(f"{count} resume(s) loaded")
    
    def preview_resume(self, resume_path: Path):
        """Preview a resume in the center panel"""
        try:
            content, success = load_resume(resume_path)
            if success:
                self.text_resume_preview.setPlainText(content)
                self.label_current_resume.setText(f"📋 {resume_path.name}")
            else:
                self.text_resume_preview.setPlainText("Failed to load resume content.")
                self.label_current_resume.setText(f"❌ {resume_path.name} (Load Failed)")
        except Exception as e:
            logger.error(f"Error previewing resume: {e}")
            self.text_resume_preview.setPlainText(f"Error loading resume: {str(e)}")
    
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
        selected_model_text = self.combo_model.currentText()
        selected_model = selected_model_text.split(" ")[0]  # Extract model name
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
        self.btn_run.setText("🔄 Processing...")
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
        self.current_results = results if isinstance(results, list) else [results] if results else []
        self.populate_results_table()
        self.finish_processing()
        
        if self.current_results:
            self.btn_export.setEnabled(True)
            QMessageBox.information(
                self, "Analysis Complete",
                f"Successfully analyzed {len(self.current_results)} candidates!\n"
                f"Results are sorted by score (highest first)."
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
        self.btn_run.setText("🚀 Analyze Resumes")
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Ready")
        self.check_ready_state()
    
    def populate_results_table(self):
        """Populate results table with analysis results"""
        if not self.current_results:
            return
        
        self.table_results.setRowCount(len(self.current_results))
        
        for row, result in enumerate(self.current_results):
            try:
                # Handle both CandidateReport objects and dictionaries
                if hasattr(result, 'name'):
                    name = result.name
                    score = result.score
                    recommendation = getattr(result, 'recommendation', 'unknown')
                    skills = getattr(result, 'skills', [])
                elif isinstance(result, dict):
                    name = result.get('name', 'Unknown')
                    score = result.get('score', 0.0)
                    recommendation = result.get('recommendation', 'unknown')
                    skills = result.get('skills', [])
                else:
                    logger.error(f"Unexpected result type at row {row}: {type(result)}")
                    continue
                
                # Candidate name
                name_item = QTableWidgetItem(str(name))
                name_item.setToolTip(str(name))
                self.table_results.setItem(row, 0, name_item)
                
                # Score with color coding
                score_item = QTableWidgetItem(f"{float(score):.1f}")
                score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Color code by score
                if score >= 80:
                    score_item.setBackground(Qt.GlobalColor.green)
                    score_item.setForeground(Qt.GlobalColor.white)
                elif score >= 60:
                    score_item.setBackground(Qt.GlobalColor.yellow)
                    score_item.setForeground(Qt.GlobalColor.black)
                else:
                    score_item.setBackground(Qt.GlobalColor.red)
                    score_item.setForeground(Qt.GlobalColor.white)
                
                self.table_results.setItem(row, 1, score_item)
                
                # Recommendation
                rec_item = QTableWidgetItem(str(recommendation).title())
                rec_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Color code recommendation
                if recommendation.lower() == 'hire':
                    rec_item.setForeground(Qt.GlobalColor.darkGreen)
                elif recommendation.lower() == 'maybe':
                    rec_item.setForeground(Qt.GlobalColor.darkYellow)
                else:
                    rec_item.setForeground(Qt.GlobalColor.darkRed)
                
                self.table_results.setItem(row, 2, rec_item)
                
                # Top skills
                if isinstance(skills, list) and skills:
                    skills_text = ", ".join(str(s) for s in skills[:3])
                    if len(skills) > 3:
                        skills_text += "..."
                else:
                    skills_text = "No skills listed"
                skills_item = QTableWidgetItem(skills_text)
                skills_item.setToolTip(", ".join(str(s) for s in skills) if skills else "No skills")
                self.table_results.setItem(row, 3, skills_item)
                
            except Exception as e:
                logger.error(f"Error populating row {row}: {e}")
                # Add error row
                error_item = QTableWidgetItem(f"Error: {str(e)}")
                self.table_results.setItem(row, 0, error_item)
        
        # Auto-select first row if results exist
        if self.current_results and self.table_results.rowCount() > 0:
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
        try:
            # Handle both object and dict formats
            if hasattr(result, 'name'):
                name = result.name
                filename = getattr(result, 'filename', 'Unknown')
                score = result.score
                recommendation = getattr(result, 'recommendation', 'unknown')
                reasoning = getattr(result, 'reasoning', 'No reasoning')
                strengths = getattr(result, 'strengths', [])
                concerns = getattr(result, 'concerns', [])
                skills = getattr(result, 'skills', [])
                education = getattr(result, 'education', [])
                experience = getattr(result, 'experience', [])
                questions = getattr(result, 'questions', [])
            else:
                name = result.get('name', 'Unknown')
                filename = result.get('filename', 'Unknown')
                score = result.get('score', 0.0)
                recommendation = result.get('recommendation', 'unknown')
                reasoning = result.get('reasoning', 'No reasoning')
                strengths = result.get('strengths', [])
                concerns = result.get('concerns', [])
                skills = result.get('skills', [])
                education = result.get('education', [])
                experience = result.get('experience', [])
                questions = result.get('questions', [])
            
            # Format details with better structure
            details = f"""
<h2 style="color: #007bff; border-bottom: 2px solid #007bff; padding-bottom: 5px;">
🧑‍💼 {name}
</h2>

<div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
<h3 style="color: #495057; margin-top: 0;">📊 Analysis Summary</h3>
<p><strong>File:</strong> {filename}</p>
<p><strong>Score:</strong> <span style="font-size: 18px; font-weight: bold; color: {'#28a745' if score >= 80 else '#ffc107' if score >= 60 else '#dc3545'};">{score:.1f}/100</span></p>
<p><strong>Recommendation:</strong> <span style="font-weight: bold; color: {'#28a745' if recommendation.lower() == 'hire' else '#ffc107' if recommendation.lower() == 'maybe' else '#dc3545'};">{recommendation.upper()}</span></p>
</div>

<h3 style="color: #28a745;">💡 Reasoning</h3>
<p style="background-color: #f8f9fa; padding: 10px; border-radius: 6px; border-left: 4px solid #28a745;">
{reasoning}
</p>

<h3 style="color: #007bff;">💪 Strengths</h3>
<ul style="background-color: #f8f9fa; padding: 15px; border-radius: 6px;">
{chr(10).join(f'<li style="margin: 5px 0;">{s}</li>' for s in strengths) if strengths else '<li>None listed</li>'}
</ul>

<h3 style="color: #dc3545;">⚠️ Concerns</h3>
<ul style="background-color: #f8f9fa; padding: 15px; border-radius: 6px;">
{chr(10).join(f'<li style="margin: 5px 0;">{c}</li>' for c in concerns) if concerns else '<li>None listed</li>'}
</ul>

<h3 style="color: #6f42c1;">🛠️ Skills & Technologies</h3>
<div style="background-color: #f8f9fa; padding: 15px; border-radius: 6px;">
{', '.join(str(s) for s in skills[:15]) if skills else 'No skills listed'}
{('...' if len(skills) > 15 else '') if skills else ''}
</div>

<h3 style="color: #fd7e14;">🎓 Education</h3>
<ul style="background-color: #f8f9fa; padding: 15px; border-radius: 6px;">
{chr(10).join(f'<li style="margin: 5px 0;">{e}</li>' for e in education[:5]) if education else '<li>No education listed</li>'}
</ul>

<h3 style="color: #20c997;">💼 Experience</h3>
<ul style="background-color: #f8f9fa; padding: 15px; border-radius: 6px;">
{chr(10).join(f'<li style="margin: 8px 0;"><strong>{exp.position if hasattr(exp, "position") else exp.get("position", "Unknown")}</strong> at <em>{exp.company if hasattr(exp, "company") else exp.get("company", "Unknown")}</em> ({exp.duration if hasattr(exp, "duration") else exp.get("duration", "Unknown")})</li>' for exp in experience[:5]) if experience else '<li>No experience listed</li>'}
</ul>

<h3 style="color: #e83e8c;">❓ Suggested Interview Questions</h3>
<ol style="background-color: #f8f9fa; padding: 15px; border-radius: 6px;">
{chr(10).join(f'<li style="margin: 8px 0;">{q}</li>' for q in questions[:8]) if questions else '<li>No questions generated</li>'}
</ol>
"""
            
            self.text_details.setHtml(details)
            
        except Exception as e:
            logger.error(f"Error displaying candidate details: {e}")
            self.text_details.setPlainText(f"Error displaying details: {str(e)}")
    
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
                        "timestamp": "2024-01-01T00:00:00Z",
                        "application": "Resume Selector v2.0"
                    },
                    "results": [
                        result.dict() if hasattr(result, 'dict') else result 
                        for result in self.current_results
                    ]
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
                
                QMessageBox.information(
                    self, "Export Successful",
                    f"Results exported successfully to:\n{file_path}"
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
            event.accept()