"""
plugin.py
---------
Main QGIS Plugin Class (GeoGPTPlugin) for Knowbuild 2.0.

Hooks into QGIS GUI lifecycle, manages actions, toolbar icons, dock widget visibility,
and orchestrates query execution between LLMParser, GeoEngine, and QGISRenderer.
"""

import os
from .dock_widget import GeoGPTDockWidget
from .llm_parser import LLMParser
from .geo_engine import GeoEngine
from .qgis_renderer import QGISRenderer

try:
    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QAction, QMessageBox
    from PyQt5.QtGui import QIcon
except ImportError:
    from qgis.PyQt.QtCore import Qt
    from qgis.PyQt.QtWidgets import QAction, QMessageBox
    from qgis.PyQt.QtGui import QIcon

class GeoGPTPlugin:
    def __init__(self, iface):
        """
        :param iface: QgisInterface instance providing access to QGIS canvas and window.
        """
        self.iface = iface
        self.dock_widget = None
        self.action = None
        self.renderer = QGISRenderer(iface)

    def initGui(self):
        """Called by QGIS when plugin is loaded to setup GUI elements."""
        # Create action to toggle plugin dock widget
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()

        self.action = QAction(icon, "GeoGPT AI Analysis", self.iface.mainWindow())
        self.action.setStatusTip("Open GeoGPT AI-Powered Satellite Analysis Sidebar")
        self.action.triggered.connect(self.toggle_dock_widget)

        # Add toolbar icon and menu item under 'Plugins' menu
        self.iface.addPluginToMenu("&GeoGPT Analysis", self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self):
        """Called by QGIS when plugin is unloaded/disabled."""
        if self.action:
            self.iface.removePluginMenu("&GeoGPT Analysis", self.action)
            self.iface.removeToolBarIcon(self.action)
        if self.dock_widget:
            self.iface.removeDockWidget(self.dock_widget)
            self.dock_widget.deleteLater()

    def toggle_dock_widget(self):
        """Toggles visibility of the plugin sidebar inside QGIS."""
        if not self.dock_widget:
            self.dock_widget = GeoGPTDockWidget(self.iface.mainWindow())
            self.dock_widget.run_query_signal.connect(self.process_query)
            right_dock = getattr(Qt, 'RightDockWidgetArea', None)
            if right_dock is None and hasattr(Qt, 'DockWidgetArea'):
                right_dock = getattr(Qt.DockWidgetArea, 'RightDockWidgetArea', 2)
            self.iface.addDockWidget(right_dock or 2, self.dock_widget)

        self.dock_widget.show()
        self.dock_widget.raise_()

    def process_query(self, user_query: str, api_key: str, data_dir: str):
        """
        Executes end-to-end pipeline:
        1. LLM Translation -> JSON analysis plan
        2. Geo Engine -> Raster raster processing & metrics
        3. PyQGIS Renderer -> Add layer to canvas
        4. UI Update -> Populate summary statistics table
        """
        try:
            # Step 1: LLM Parsing
            parser = LLMParser(api_key=api_key)
            plan = parser.parse_query(user_query)

            # Step 2: Geo Engine Execution
            engine = GeoEngine(data_dir=data_dir)
            result = engine.execute_plan(plan)

            # Step 3: Add output layer to QGIS map canvas
            output_path = result["output_path"]
            layer_name = result["layer_name"]
            is_loss = "loss" in plan.get("operation", "")

            # Step 4: Generate AI Solution & Policy Recommendations
            solution_text = parser.generate_solution(user_query, result["summary_stats"])

            # Step 5: Display metrics, visual chart, & AI solution in Dock Widget
            self.dock_widget.display_results(result["summary_stats"], solution_text=solution_text)

        except Exception as e:
            error_msg = str(e)
            if self.dock_widget:
                self.dock_widget.set_status(f"Error: {error_msg}", is_error=True)
            print(f"[GeoGPT Error] {error_msg}")
