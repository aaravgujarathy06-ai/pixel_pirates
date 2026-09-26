"""
qgis_renderer.py
----------------
PyQGIS Canvas Renderer for Knowbuild 2.0.

Loads generated GeoTIFF raster result files into the active QGIS map canvas,
configures single-band pseudo-color raster styling/color ramps, opacity, and triggers canvas refresh.
"""

class QGISRenderer:
    def __init__(self, iface):
        """
        :param iface: QgisInterface instance passed from QGIS main window.
        """
        self.iface = iface

    def add_raster_layer(self, file_path: str, layer_name: str, is_loss_layer: bool = True):
        """
        Adds raster file to QGIS layer tree with styled color ramp and opacity.
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
            print(f"[GeoGPT QGISRenderer] PyQGIS modules unavailable outside QGIS environment. Path: {file_path}")
            return None

        # Create QGIS Raster Layer
        layer = QgsRasterLayer(file_path, layer_name)
        if not layer.isValid():
            raise RuntimeError(f"Failed to load raster layer from path: {file_path}")

        # Configure Single Band Pseudocolor Shader
        shader = QgsRasterShader()
        color_ramp_shader = QgsColorRampShader()
        color_ramp_shader.setColorRampType(QgsColorRampShader.Interpolated)

        if is_loss_layer:
            # Multi-class Gradient for Change Detection (Transparent -> Orange -> Red -> Dark Crimson)
            items = [
                QgsColorRampShader.ColorRampItem(0.00, QColor(0, 0, 0, 0), "No Change"),
                QgsColorRampShader.ColorRampItem(0.15, QColor(255, 170, 0, 180), "Moderate Loss"),
                QgsColorRampShader.ColorRampItem(0.35, QColor(230, 25, 25, 220), "High Loss"),
                QgsColorRampShader.ColorRampItem(0.60, QColor(140, 0, 25, 255), "Severe Loss")
            ]
        else:
            # 4-Class High Contrast NDVI Ramp: Navy Blue -> Urban Gray -> Lime Green -> Emerald Forest
            items = [
                QgsColorRampShader.ColorRampItem(-0.50, QColor(20, 80, 190, 255), "Water Bodies"),
                QgsColorRampShader.ColorRampItem(0.10, QColor(180, 180, 180, 255), "Built-Up / Bare Soil"),
                QgsColorRampShader.ColorRampItem(0.35, QColor(160, 225, 60, 255), "Sparse Vegetation"),
                QgsColorRampShader.ColorRampItem(0.75, QColor(10, 130, 45, 255), "Dense Canopy Forest")
            ]

        color_ramp_shader.setColorRampItemList(items)
        shader.setRasterShaderFunction(color_ramp_shader)

        renderer = QgsSingleBandPseudoColorRenderer(layer.dataProvider(), 1, shader)
        layer.setRenderer(renderer)
        layer.setOpacity(0.85) # Semi-transparent layer blending

        # Add layer to QGIS map project
        QgsProject.instance().addMapLayer(layer)
        
        # Refresh map canvas & zoom to layer
        if self.iface:
            self.iface.setActiveLayer(layer)
            self.iface.zoomToActiveLayer()
            self.iface.mapCanvas().refresh()

        return layer
