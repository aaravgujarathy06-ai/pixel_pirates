"""
__init__.py
-----------
QGIS Plugin initialization entrypoint required by QGIS plugin loader.
"""

def classFactory(iface):
    """
    Load GeoGPTPlugin class from plugin.py
    
    :param iface: A QGIS interface instance (QgisInterface)
    """
    from .plugin import GeoGPTPlugin
    return GeoGPTPlugin(iface)
