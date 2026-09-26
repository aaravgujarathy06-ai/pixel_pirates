"""
dock_widget.py
--------------
PyQt UI Dock Widget for Knowbuild 2.0 (GeoGPT for QGIS).

Provides an interactive, ultra-premium sidebar in QGIS with query inputs, API key settings,
datacube directory path selection, execution triggers, structured spatial metrics,
interactive visual donut charts, and AI solution recommendations.
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
        super().__init__("GeoGPT - AI Geospatial Intelligence", parent)
        self.setAllowedAreas(LEFT_DOCK | RIGHT_DOCK)
        self.init_ui()

    def init_ui(self):
        # Create scroll area container for rich UI layout
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background-color: #f8fafc; border: none; }")

        main_widget = QWidget()
        main_widget.setObjectName("MainWidget")
        main_widget.setStyleSheet("QWidget#MainWidget { background-color: #f8fafc; }")
        
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(14)

        # 1. Glassmorphism Header Banner
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0f172a, stop:1 #1e293b);
                border-radius: 10px;
                padding: 12px;
                border: 1px solid #334155;
            }
            QLabel {
                color: #f8fafc;
            }
        """)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(10, 10, 10, 10)
        
        title = QLabel("🌍 GeoGPT Analytics Hub")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #38bdf8; font-family: 'Segoe UI', sans-serif;")
        subtitle = QLabel("Natural Language Satellite AI & Spatial Decision Support")
        subtitle.setStyleSheet("font-size: 11px; color: #94a3b8;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addWidget(header)

        # Base GroupBox Styling
        group_style = """
            QGroupBox {
                font-weight: bold;
                font-size: 11px;
                color: #0284c7;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                background-color: #ffffff;
                margin-top: 12px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
                background-color: #ffffff;
            }
        """

        # 2. Configuration Settings Group
        config_group = QGroupBox("⚙️ Environment & Datacube Settings")
        config_group.setStyleSheet(group_style)
        config_layout = QFormLayout()
        config_layout.setContentsMargins(10, 14, 10, 10)

        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(ECHO_PASSWORD)
        self.api_key_input.setPlaceholderText("Optional: sk-... (Uses Fallback Parser if empty)")
        self.api_key_input.setStyleSheet("QLineEdit { background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px; font-size: 11px; } QLineEdit:focus { border: 1px solid #0284c7; background-color: #ffffff; }")

        # Data cube path selector
        data_path_layout = QHBoxLayout()
        default_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
        self.data_dir_input = QLineEdit(default_data_dir)
        self.data_dir_input.setStyleSheet("QLineEdit { background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px; font-size: 11px; } QLineEdit:focus { border: 1px solid #0284c7; background-color: #ffffff; }")

        browse_btn = QPushButton("Browse...")
        browse_btn.setStyleSheet("QPushButton { background-color: #f1f5f9; color: #334155; border: 1px solid #cbd5e1; border-radius: 6px; padding: 5px 10px; font-size: 11px; font-weight: bold; } QPushButton:hover { background-color: #e2e8f0; }")
        browse_btn.clicked.connect(self._browse_data_dir)
        
        data_path_layout.addWidget(self.data_dir_input)
        data_path_layout.addWidget(browse_btn)

        config_layout.addRow("OpenAI Key:", self.api_key_input)
        config_layout.addRow("Data Cube:", data_path_layout)
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # 3. Query Input Section
        query_group = QGroupBox("💬 Natural Language Spatial Query")
        query_group.setStyleSheet(group_style)
        query_layout = QVBoxLayout()
        query_layout.setContentsMargins(10, 14, 10, 10)

        self.query_input = QTextEdit()
        self.query_input.setPlaceholderText("e.g. Show vegetation loss in Pune between 2015 and 2020")
        self.query_input.setText("Show vegetation loss in Pune between 2015 and 2020")
        self.query_input.setMaximumHeight(70)
        self.query_input.setStyleSheet("QTextEdit { background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px; font-size: 11px; color: #0f172a; } QTextEdit:focus { border: 1px solid #0284c7; background-color: #ffffff; }")

        self.run_btn = QPushButton("⚡ Execute Analysis & AI Strategy")
        self.run_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #0369a1);
                color: white;
                font-weight: bold;
                font-size: 13px;
                padding: 10px;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0369a1, stop:1 #075985);
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
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setStyleSheet("QProgressBar { border: none; background-color: #e2e8f0; border-radius: 3px; } QProgressBar::chunk { background-color: #0284c7; border-radius: 3px; }")
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Status: System Ready")
        self.status_label.setStyleSheet("color: #64748b; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.status_label)

        # 5. Results & Statistics Display Table
        results_group = QGroupBox("📋 Spatial Analytics Metrics")
        results_group.setStyleSheet(group_style)
        results_layout = QVBoxLayout()
        results_layout.setContentsMargins(10, 14, 10, 10)

        self.stats_table = QTableWidget(0, 2)
        self.stats_table.setHorizontalHeaderLabels(["Metric Parameter", "Computed Value"])
        self.stats_table.horizontalHeader().setSectionResizeMode(RESIZE_STRETCH)
        self.stats_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                gridline-color: #f1f5f9;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #f1f5f9;
                color: #334155;
                font-weight: bold;
                font-size: 11px;
                padding: 6px;
                border: none;
            }
        """)
        self.stats_table.setMinimumHeight(140)
        
        results_layout.addWidget(self.stats_table)
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)

        # 6. Visual Chart Section
        chart_group = QGroupBox("📊 Land Cover Distribution Donut")
        chart_group.setStyleSheet(group_style)
        self.chart_layout = QVBoxLayout()
        self.chart_layout.setContentsMargins(10, 14, 10, 10)

        self.chart_placeholder = QLabel("Execute a spatial query to generate visual donut breakdown.")
        self.chart_placeholder.setStyleSheet("color: #94a3b8; font-style: italic; font-size: 11px;")
        self.chart_placeholder.setAlignment(ALIGN_CENTER)
        self.chart_layout.addWidget(self.chart_placeholder)
        
        chart_group.setLayout(self.chart_layout)
        layout.addWidget(chart_group)

        # 7. AI Solution & Action Plan Card
        solution_group = QGroupBox("💡 AI Policy Strategy & Urban Action Plan")
        solution_group.setStyleSheet(group_style)
        solution_layout = QVBoxLayout()
        solution_layout.setContentsMargins(10, 14, 10, 10)

        self.solution_box = QLabel("Spatial execution report and AI policy recommendations will generate here.")
        self.solution_box.setWordWrap(True)
        self.solution_box.setStyleSheet("""
            QLabel {
                background-color: #f8fafc;
                border: 1px solid #cbd5e1;
                border-left: 4px solid #0284c7;
                border-radius: 6px;
                padding: 12px;
                font-size: 11px;
                color: #0f172a;
                line-height: 1.4;
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
        dir_path = QFileDialog.getExistingDirectory(self, "Select Datacube Directory")
        if dir_path:
            self.data_dir_input.setText(dir_path)

    def _on_run_clicked(self):
        query = self.query_input.toPlainText().strip()
        api_key = self.api_key_input.text().strip()
        data_dir = self.data_dir_input.text().strip()

        if not query:
            self.set_status("Error: Query cannot be empty.", is_error=True)
            return

        self.progress_bar.setValue(35)
        self.set_status("Executing spatial raster engine...")
        self.run_query_signal.emit(query, api_key, data_dir)

    def set_status(self, text: str, is_error: bool = False):
        color = "#ef4444" if is_error else "#0284c7"
        self.status_label.setText(f"Status: {text}")
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px;")

    def display_results(self, stats: dict, solution_text: str = ""):
        self.progress_bar.setValue(100)
        self.stats_table.setRowCount(0)

        display_keys = [k for k in stats.keys() if not k.startswith("Chart ")]

        for row, metric in enumerate(display_keys):
            val = stats[metric]
            self.stats_table.insertRow(row)
            item_key = QTableWidgetItem(str(metric))
            item_val = QTableWidgetItem(str(val))
            item_key.setFlags(item_key.flags() ^ ITEM_EDITABLE)
            item_val.setFlags(item_val.flags() ^ ITEM_EDITABLE)
            
            # Format value styling
            item_key.setStyleSheet("font-weight: bold; color: #334155;")
            item_val.setStyleSheet("color: #0284c7; font-weight: bold;")
            
            self.stats_table.setItem(row, 0, item_key)
            self.stats_table.setItem(row, 1, item_val)

        # Update AI Solution box
        if solution_text:
            self.solution_box.setText(solution_text)

        # Update Visual Donut Chart
        self._render_chart(stats)
        self.set_status("Complete! Raster layer & visual decision support updated.")

    def _render_chart(self, stats: dict):
        """Renders dynamic high-end visual donut chart of land cover change."""
        for i in reversed(range(self.chart_layout.count())):
            w = self.chart_layout.itemAt(i).widget()
            if w:
                w.deleteLater()

        chart_type = stats.get("Chart Type", "loss")

        if chart_type == "loss":
            ret_pct = stats.get("Chart Retained Pct", 28.0)
            loss_pct = stats.get("Chart Loss Pct", 6.0)
            built_pct = stats.get("Chart Builtup Pct", 66.0)
            labels = ['Retained', 'Loss', 'Built-Up']
            sizes = [ret_pct, loss_pct, built_pct]
            colors = ['#10b981', '#f43f5e', '#64748b']
        elif chart_type == "gain":
            ret_pct = stats.get("Chart Retained Pct", 28.0)
            gain_pct = stats.get("Chart Gain Pct", 4.0)
            built_pct = stats.get("Chart Builtup Pct", 68.0)
            labels = ['Retained', 'Gain', 'Built-Up']
            sizes = [ret_pct, gain_pct, built_pct]
            colors = ['#10b981', '#3b82f6', '#64748b']
        else: # ndvi
            veg_pct = stats.get("Chart Veg Pct", 34.0)
            nonveg_pct = stats.get("Chart NonVeg Pct", 66.0)
            labels = ['Vegetation', 'Non-Veg']
            sizes = [veg_pct, nonveg_pct]
            colors = ['#10b981', '#64748b']

        if HAS_MATPLOTLIB:
            try:
                fig = Figure(figsize=(3.5, 2.3), dpi=100)
                ax = fig.add_subplot(111)
                fig.patch.set_facecolor('#ffffff')

                # Donut ring styling
                wedges, texts, autotexts = ax.pie(
                    sizes,
                    labels=labels,
                    autopct='%1.1f%%',
                    startangle=140,
                    colors=colors,
                    pctdistance=0.75,
                    wedgeprops=dict(width=0.38, edgecolor='#ffffff', linewidth=2),
                    textprops=dict(size=8, color='#1e293b')
                )

                # Center Donut Label Annotation
                ax.text(0, 0, 'Land Cover\nBreakdown', ha='center', va='center', fontsize=8, fontweight='bold', color='#334155')

                for autotext in autotexts:
                    autotext.set_color('#ffffff')
                    autotext.set_weight('bold')
                    autotext.set_fontsize(7)

                ax.axis('equal')
                fig.tight_layout()

                canvas = FigureCanvas(fig)
                self.chart_layout.addWidget(canvas)
                return
            except Exception as e:
                print(f"[GeoGPT Chart Error] {e}")

        # Fallback simple visual badge bar container
        txt = " | ".join([f"{l}: {s}%" for l, s in zip(labels, sizes)])
        fallback_lbl = QLabel(txt)
        fallback_lbl.setStyleSheet("font-weight: bold; color: #0284c7; font-size: 11px; background-color: #f0f9ff; padding: 8px; border-radius: 6px; border: 1px solid #bae6fd;")
        fallback_lbl.setAlignment(ALIGN_CENTER)
        self.chart_layout.addWidget(fallback_lbl)
