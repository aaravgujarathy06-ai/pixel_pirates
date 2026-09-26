"""
qgis_renderer.py
----------------
PyQGIS Canvas Renderer for Knowbuild 2.0.

Loads generated GeoTIFF raster result files into the active QGIS map canvas,
configures single-band pseudo-color raster styling/color ramps, and triggers canvas refresh.
"""

class QGISRenderer:
    def __init__(self, iface):
        """
        :param iface: QgisInterface instance passed from QGIS main window.
        """
        self.iface = iface

    def add_raster_layer(self, file_path: str, layer_name: str, is_loss_layer: bool = True):
        """
        Adds raster file to QGIS layer tree with styled color ramp.
        """
        try:
            from qgis.core import (
                QgsRasterLayer,
                QgsProject,
                QgsSingleBandPseudoColorRenderer,
                QgsColorRampShader,
                QgsRasterShader
            )
            from qgis.PyQt.QtGui import QColor
        except ImportError:
            print(f"[GeoGPT QGISRenderer] Notice: PyQGIS modules not available outside QGIS environment. Layer path: {file_path}")
            return None

        # Create QGIS Raster Layer
        layer = QgsRasterLayer(file_path, layer_name)
        if not layer.isValid():
            raise RuntimeError(f"Failed to load raster layer from path: {file_path}")

        # Configure Single Band Pseudocolor Styling
        shader = QgsRasterShader()
        color_ramp_shader = QgsColorRampShader()
        color_ramp_shader.setColorRampType(QgsColorRampShader.Interpolated)

        if is_loss_layer:
            # Transparent for 0 (no loss), Bright Red for 1 (loss)
            items = [
                QgsColorRampShader.ColorRampItem(0.0, QColor(0, 0, 0, 0), "No Change"),
                QgsColorRampShader.ColorRampItem(1.0, QColor(230, 25, 25, 220), "Vegetation Lost")
            ]
        else:
            # NDVI Color Ramp: Red (low vegetation) -> Yellow -> Green (dense vegetation)
            items = [
                QgsColorRampShader.ColorRampItem(-1.0, QColor(0, 0, 255, 255), "Water / Snow"),
                QgsColorRampShader.ColorRampItem(0.0, QColor(200, 200, 200, 255), "Bare Soil / Urban"),
                QgsColorRampShader.ColorRampItem(0.3, QColor(255, 255, 100, 255), "Moderate Veg"),
                QgsColorRampShader.ColorRampItem(0.8, QColor(0, 150, 0, 255), "Dense Vegetation")
            ]

        color_ramp_shader.setColorRampItemList(items)
        shader.setRasterShaderFunction(color_ramp_shader)

        renderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader)
        layer.setRenderer(renderer)

        # Add layer to QGIS map project
        QgsProject.instance().addMapLayer(layer)
        
        # Refresh map canvas & zoom to layer
        if self.iface:
            self.iface.setActiveLayer(layer)
            self.iface.zoomToActiveLayer()
            self.iface.mapCanvas().refresh()

        return layer
