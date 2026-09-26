"""
dock_widget.py
--------------
PyQt UI Dock Widget for Knowbuild 2.0 (GeoGPT for QGIS).

Provides an interactive sidebar in QGIS with query inputs, API key settings,
datacube directory path selection, execution triggers, structured spatial metrics,
interactive visual charts, and AI solution recommendations.
Compatible with both QGIS 3 (PyQt5) and QGIS 4 (PyQt6 / PySide6).
"""

import os

try:
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtWidgets import (
        QDockWidget,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QTextEdit,
        QGroupBox,
        QProgressBar,
        QFileDialog,
        QFormLayout,
        QFrame,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QScrollArea
    )
except ImportError:
    from qgis.PyQt.QtCore import Qt, pyqtSignal
    from qgis.PyQt.QtWidgets import (
        QDockWidget,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QPushButton,
        QTextEdit,
        QGroupBox,
        QProgressBar,
        QFileDialog,
        QFormLayout,
        QFrame,
        QTableWidget,
        QTableWidgetItem,
        QHeaderView,
        QScrollArea
    )

# Safe enum lookup helpers for PyQt5 / PyQt6 compatibility in QGIS 3 & 4
def get_enum(obj, attr1, attr2=None):
    if hasattr(obj, attr1):
        return getattr(obj, attr1)
    if attr2 and hasattr(obj, attr2):
        nested = getattr(obj, attr2)
        if hasattr(nested, attr1):
            return getattr(nested, attr1)
    return 0

LEFT_DOCK = get_enum(Qt, 'LeftDockWidgetArea', 'DockWidgetArea')
RIGHT_DOCK = get_enum(Qt, 'RightDockWidgetArea', 'DockWidgetArea')
ALIGN_CENTER = get_enum(Qt, 'AlignCenter', 'AlignmentFlag')
ECHO_PASSWORD = get_enum(QLineEdit, 'Password', 'EchoMode')
ITEM_EDITABLE = get_enum(Qt, 'ItemIsEditable', 'ItemFlag')
RESIZE_STRETCH = get_enum(QHeaderView, 'Stretch', 'ResizeMode')

# Try importing Matplotlib for embedding inline charts inside PyQt
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except Exception:
    HAS_MATPLOTLIB = False


class GeoGPTDockWidget(QDockWidget):
    run_query_signal = pyqtSignal(str, str, str) # query, api_key, data_dir

    def __init__(self, parent=None):
        super().__init__("GeoGPT - Natural Language Geospatial AI", parent)
        self.setAllowedAreas(LEFT_DOCK | RIGHT_DOCK)
        self.init_ui()

    def init_ui(self):
        # Create scroll area container for rich UI layout
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        main_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        # 1. Header Banner
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: #0f172a;
                border-radius: 8px;
                padding: 10px;
            }
            QLabel {
                color: #f8fafc;
            }
        """)
        header_layout = QVBoxLayout(header)
        title = QLabel("🌍 GeoGPT Sidebar")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8;")
        subtitle = QLabel("AI Geospatial Analytics & Visual Solutions")
        subtitle.setStyleSheet("font-size: 11px; color: #94a3b8;")
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addWidget(header)

        # 2. Configuration Settings Group
        config_group = QGroupBox("Configuration & Data Cube")
        config_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
        config_layout = QFormLayout()

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(ECHO_PASSWORD)
        self.api_key_input.setPlaceholderText("Optional: sk-... (Uses Fallback Parser if empty)")
        
        # Data cube path selector
        data_path_layout = QHBoxLayout()
        default_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        self.data_dir_input = QLineEdit(default_data_dir)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_data_dir)
        data_path_layout.addWidget(self.data_dir_input)
        data_path_layout.addWidget(browse_btn)

        config_layout.addRow("OpenAI API Key:", self.api_key_input)
        config_layout.addRow("Data Cube Path:", data_path_layout)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # 3. Query Input Section
        query_group = QGroupBox("Natural Language Query")
        query_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
        query_layout = QVBoxLayout()

        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("e.g. Show vegetation loss in Pune between 2015 and 2020")
        self.query_input.setText("Show vegetation loss in Pune between 2015 and 2020")
        self.query_input.setMaximumHeight(70)
        
        self.run_btn = QPushButton("⚡ Execute Analysis & Solution")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: white;
                font-weight: bold;
                font-size: 13px;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.run_btn.clicked.connect(self._on_run_clicked)

        query_layout.addWidget(self.query_input)
        query_layout.addWidget(self.run_btn)
        query_group.setLayout(query_layout)
        layout.addWidget(query_group)

        # 4. Status & Progress Indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("QProgressBar::chunk { background-color: #38bdf8; }")
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: #64748b; font-size: 11px;")
        layout.addWidget(self.status_label)

        # 5. Results & Statistics Display Table
        results_group = QGroupBox("Analysis Metrics & Metrics")
        results_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
        results_layout = QVBoxLayout()

        self.stats_table = QTableWidget(0, 2)
        self.stats_table.setHorizontalHeaderLabels(["Metric", "Value"])
        self.stats_table.horizontalHeader().setSectionResizeMode(RESIZE_STRETCH)
        self.stats_table.setStyleSheet("QTableWidget { font-size: 11px; }")
        self.stats_table.setMinimumHeight(140)
        
        results_layout.addWidget(self.stats_table)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # 6. Visual Chart Section
        chart_group = QGroupBox("📊 Visual Land Cover Distribution")
        chart_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
        self.chart_layout = QVBoxLayout()
        
        self.chart_placeholder = QLabel("Run a query to generate visual chart.")
        self.chart_placeholder.setStyleSheet("color: #94a3b8; font-style: italic;")
        self.chart_placeholder.setAlignment(ALIGN_CENTER)
        self.chart_layout.addWidget(self.chart_placeholder)
        
        chart_group.setLayout(self.chart_layout)
        layout.addWidget(chart_group)

        # 7. AI Solution & Action Plan Card
        solution_group = QGroupBox("💡 AI Insights & Solution Recommendation")
        solution_group.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
        solution_layout = QVBoxLayout()

        self.solution_box = QLabel("Execution results and policy recommendations will appear here.")
        self.solution_box.setWordWrap(True)
        self.solution_box.setStyleSheet("""
            QLabel {
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                border-left: 4px solid #0284c7;
                border-radius: 6px;
                padding: 10px;
                font-size: 11px;
                color: #1e293b;
            }
        """)
        solution_layout.addWidget(self.solution_box)
        solution_group.setLayout(solution_layout)
        layout.addWidget(solution_group)

        layout.addStretch()
        main_widget.setLayout(layout)
        scroll.setWidget(main_widget)
        self.setWidget(scroll)

    def _browse_data_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Satellite Data Cube Directory")
        if dir_path:
            self.data_dir_input.setText(dir_path)

    def _on_run_clicked(self):
        query = self.query_input.toPlainText().strip()
        api_key = self.api_key_input.text().strip()
        data_dir = self.data_dir_input.text().strip()

        if not query:
            self.set_status("Error: Query cannot be empty.", is_error=True)
            return

        self.progress_bar.setValue(30)
        self.set_status("Parsing query & executing spatial engine...")
        self.run_query_signal.emit(query, api_key, data_dir)

    def set_status(self, text: str, is_error: bool = False):
        color = "#ef4444" if is_error else "#0284c7"
        self.status_label.setText(f"Status: {text}")
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px;")

    def display_results(self, stats: dict, solution_text: str = ""):
        self.progress_bar.setValue(100)
        self.stats_table.setRowCount(0)

        for row, (metric, val) in enumerate(stats.items()):
            self.stats_table.insertRow(row)
            item_key = QTableWidgetItem(str(metric))
            item_val = QTableWidgetItem(str(val))
            item_key.setFlags(item_key.flags() ^ ITEM_EDITABLE)
            item_val.setFlags(item_val.flags() ^ ITEM_EDITABLE)
            self.stats_table.setItem(row, 0, item_key)
            self.stats_table.setItem(row, 1, item_val)

        # Update AI Solution box
        if solution_text:
            self.solution_box.setText(solution_text)

        # Update Visual Chart
        self._render_chart(stats)
        self.set_status("Completed! Layer & visual insights added.")

    def _render_chart(self, stats: dict):
        """Renders dynamic visual pie chart of land cover change."""
        # Clear previous chart elements
        for i in reversed(range(self.chart_layout.count())):
            w = self.chart_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        chart_type = stats.get("Chart Type", "loss")

        if chart_type == "loss":
            ret_pct = stats.get("Chart Retained Pct", 28.0)
            loss_pct = stats.get("Chart Loss Pct", 6.0)
            built_pct = stats.get("Chart Builtup Pct", 66.0)
            labels = ['Veg Retained', 'Veg Lost', 'Built-Up / Bare']
            sizes = [ret_pct, loss_pct, built_pct]
            colors = ['#22c55e', '#ef4444', '#94a3b8']
            explode = (0, 0.1, 0)
        elif chart_type == "gain":
            ret_pct = stats.get("Chart Retained Pct", 28.0)
            gain_pct = stats.get("Chart Gain Pct", 4.0)
            built_pct = stats.get("Chart Builtup Pct", 68.0)
            labels = ['Veg Retained', 'Veg Gain', 'Built-Up / Bare']
            sizes = [ret_pct, gain_pct, built_pct]
            colors = ['#22c55e', '#3b82f6', '#94a3b8']
            explode = (0, 0.1, 0)
        else: # ndvi
            veg_pct = stats.get("Chart Veg Pct", 34.0)
            nonveg_pct = stats.get("Chart NonVeg Pct", 66.0)
            labels = ['Vegetation', 'Non-Vegetated']
            sizes = [veg_pct, nonveg_pct]
            colors = ['#22c55e', '#94a3b8']
            explode = (0.05, 0)

        if HAS_MATPLOTLIB:
            try:
                fig = Figure(figsize=(3.5, 2.2), dpi=100)
                ax = fig.add_subplot(111)
                fig.patch.set_facecolor('#f8fafc')

                wedges, texts, autotexts = ax.pie(
                    sizes,
                    explode=explode,
                    labels=labels,
                    autopct='%1.1f%%',
                    shadow=False,
                    startangle=140,
                    colors=colors,
                    textprops=dict(size=8)
                )

                ax.axis('equal')
                fig.tight_layout()

                canvas = FigureCanvas(fig)
                self.chart_layout.addWidget(canvas)
                return
            except Exception as e:
                print(f"[GeoGPT Chart Error] {e}")

        # Fallback simple visual bar container
        txt = " | ".join([f"{l}: {s}%" for l, s in zip(labels, sizes)])
        fallback_lbl = QLabel(txt)
        fallback_lbl.setStyleSheet("font-weight: bold; color: #1e293b; font-size: 11px;")
        fallback_lbl.setAlignment(ALIGN_CENTER)
        self.chart_layout.addWidget(fallback_lbl)
