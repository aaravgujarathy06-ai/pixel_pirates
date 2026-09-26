"""
geo_engine.py
-------------
Geospatial Data Cube Processing Engine for Knowbuild 2.0.

Executes analysis plans on satellite data cubes (xarray/rasterio/numpy)
and outputs resulting GeoTIFF rasters with summary spatial metrics.
"""

import os
import tempfile
import numpy as np

class GeoEngine:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir

    def execute_plan(self, plan: dict) -> dict:
        """
        Executes structured analysis plan on local satellite datacube.
        Returns dictionary containing output layer path, layer name, and summary metrics.
        """
        region = plan.get("region", "pune")
        operation = plan.get("operation", "vegetation_loss")
        start_year = plan.get("start_year", 2015)
        end_year = plan.get("end_year", 2020)
        threshold = plan.get("threshold", 0.15)

        # File paths for input satellite data
        file_start = os.path.join(self.data_dir, f"{region}_{start_year}.tif")
        file_end = os.path.join(self.data_dir, f"{region}_{end_year}.tif")

        if not os.path.exists(file_start):
            raise FileNotFoundError(f"Satellite data for {region} ({start_year}) not found at: {file_start}")
        if not os.path.exists(file_end):
            raise FileNotFoundError(f"Satellite data for {region} ({end_year}) not found at: {file_end}")

        try:
            import rasterio
            with rasterio.open(file_start) as src_start, rasterio.open(file_end) as src_end:
                meta = src_start.meta.copy()
                transform = src_start.transform
                crs = src_start.crs

                red_2015 = src_start.read(3).astype(np.float32)
                nir_2015 = src_start.read(4).astype(np.float32)
                red_2020 = src_end.read(3).astype(np.float32)
                nir_2020 = src_end.read(4).astype(np.float32)
        except ImportError:
            # Fallback reader for basic TIFF structure
            print("[GeoEngine] 'rasterio' not installed in Python env. Using fallback binary TIFF reader.")
            def read_tiff_bands(filepath):
                with open(filepath, 'rb') as f:
                    content = f.read()
                    raw_data = np.frombuffer(content, dtype='<u2')
                    # Extract pixel array from end of file
                    pixel_count = 500 * 500 * 4
                    data = raw_data[-pixel_count:].reshape((500, 500, 4))
                    red = data[:, :, 2].astype(np.float32)
                    nir = data[:, :, 3].astype(np.float32)
                    return red, nir
            
            red_2015, nir_2015 = read_tiff_bands(file_start)
            red_2020, nir_2020 = read_tiff_bands(file_end)
            transform = [0.0001, 0, 73.80, 0, -0.0001, 18.55]
            crs = None

        # Compute NDVI: (NIR - Red) / (NIR + Red)
        ndvi_2015 = self.compute_ndvi(red_2015, nir_2015)
        ndvi_2020 = self.compute_ndvi(red_2020, nir_2020)

        # Calculate pixel area in square meters (converting degrees/meters to area)
        # EPSG:4326 resolution ~ 10m x 10m (~0.0001 deg)
        res_x, res_y = abs(transform[0]), abs(transform[4])
        if crs and hasattr(crs, 'to_epsg') and crs.to_epsg() == 4326:
            # Approx 1 deg lat = 111.32 km -> converts degree pixel size to meters approx
            pixel_area_m2 = (res_x * 111320) * (res_y * 111320)
        else:
            pixel_area_m2 = (res_x * 111320) * (res_y * 111320) if res_x < 1 else res_x * res_y

        # Calculate exact pixel statistics for dynamic land cover chart
        total_px = float(ndvi_2015.size)
        veg_2015_px = float(np.sum(ndvi_2015 > 0.3))
        veg_2020_px = float(np.sum(ndvi_2020 > 0.3))

        retained_px = float(np.sum((ndvi_2015 > 0.3) & (ndvi_2020 > 0.3)))
        loss_px = float(np.sum((ndvi_2015 > 0.3) & (ndvi_2020 <= 0.3)))
        gain_px = float(np.sum((ndvi_2015 <= 0.3) & (ndvi_2020 > 0.3)))
        builtup_px = float(np.sum((ndvi_2015 <= 0.3) & (ndvi_2020 <= 0.3)))

        pct_retained = round((retained_px / total_px) * 100.0, 1)
        pct_loss = round((loss_px / total_px) * 100.0, 1)
        pct_gain = round((gain_px / total_px) * 100.0, 1)
        pct_builtup = round((builtup_px / total_px) * 100.0, 1)
        pct_veg_2015 = round((veg_2015_px / total_px) * 100.0, 1)
        pct_veg_2020 = round((veg_2020_px / total_px) * 100.0, 1)

        # Perform requested operation
        output_dir = tempfile.gettempdir()
        
        if operation == "vegetation_loss":
            change_ndvi = ndvi_2020 - ndvi_2015
            loss_mask = (change_ndvi < -threshold).astype(np.float32)
            loss_pixels = np.sum(loss_mask > 0)
            loss_area_sq_km = (loss_pixels * pixel_area_m2) / 1e6
            pct_change = (loss_pixels / max(veg_2015_px, 1.0)) * 100.0

            out_path = os.path.join(output_dir, f"{region}_vegetation_loss_{start_year}_{end_year}.tif")
            
            try:
                import rasterio
                meta.update(count=1, dtype=rasterio.float32, nodata=0.0)
                with rasterio.open(out_path, 'w', **meta) as dst:
                    dst.write(loss_mask, 1)
            except (ImportError, UnboundLocalError):
                out_path = os.path.join(output_dir, f"{region}_vegetation_loss_{start_year}_{end_year}.npy")
                np.save(out_path, loss_mask)

            return {
                "output_path": out_path,
                "layer_name": f"Vegetation Loss ({start_year}-{end_year})",
                "operation": "Vegetation Loss Detection",
                "summary_stats": {
                    "Region": region.capitalize(),
                    "Timeframe": f"{start_year} - {end_year}",
                    "Vegetation Area Lost": f"{loss_area_sq_km:.2f} sq km",
                    "Percentage Loss": f"{pct_change:.1f}%",
                    "Loss Pixel Count": int(loss_pixels),
                    "Threshold Used": f"NDVI drop > {threshold}",
                    "Chart Type": "loss",
                    "Chart Retained Pct": pct_retained,
                    "Chart Loss Pct": pct_loss,
                    "Chart Builtup Pct": pct_builtup
                }
            }

        elif operation == "ndvi_2015":
            out_path = os.path.join(output_dir, f"{region}_ndvi_{start_year}.tif")
            try:
                import rasterio
                meta.update(count=1, dtype=rasterio.float32)
                with rasterio.open(out_path, 'w', **meta) as dst:
                    dst.write(ndvi_2015, 1)
            except (ImportError, UnboundLocalError):
                out_path = os.path.join(output_dir, f"{region}_ndvi_{start_year}.npy")
                np.save(out_path, ndvi_2015)

            mean_ndvi = float(np.mean(ndvi_2015))
            return {
                "output_path": out_path,
                "layer_name": f"NDVI {start_year}",
                "operation": "NDVI Raster Computation",
                "summary_stats": {
                    "Region": region.capitalize(),
                    "Year": start_year,
                    "Mean NDVI": f"{mean_ndvi:.3f}",
                    "Min NDVI": f"{float(np.min(ndvi_2015)):.3f}",
                    "Max NDVI": f"{float(np.max(ndvi_2015)):.3f}",
                    "Chart Type": "ndvi",
                    "Chart Veg Pct": pct_veg_2015,
                    "Chart NonVeg Pct": round(100.0 - pct_veg_2015, 1)
                }
            }

        elif operation == "ndvi_2020":
            out_path = os.path.join(output_dir, f"{region}_ndvi_{end_year}.tif")
            try:
                import rasterio
                meta.update(count=1, dtype=rasterio.float32)
                with rasterio.open(out_path, 'w', **meta) as dst:
                    dst.write(ndvi_2020, 1)
            except (ImportError, UnboundLocalError):
                out_path = os.path.join(output_dir, f"{region}_ndvi_{end_year}.npy")
                np.save(out_path, ndvi_2020)

            mean_ndvi = float(np.mean(ndvi_2020))
            return {
                "output_path": out_path,
                "layer_name": f"NDVI {end_year}",
                "operation": "NDVI Raster Computation",
                "summary_stats": {
                    "Region": region.capitalize(),
                    "Year": end_year,
                    "Mean NDVI": f"{mean_ndvi:.3f}",
                    "Min NDVI": f"{float(np.min(ndvi_2020)):.3f}",
                    "Max NDVI": f"{float(np.max(ndvi_2020)):.3f}",
                    "Chart Type": "ndvi",
                    "Chart Veg Pct": pct_veg_2020,
                    "Chart NonVeg Pct": round(100.0 - pct_veg_2020, 1)
                }
            }

        else: # Fallback / Gain
            change_ndvi = ndvi_2020 - ndvi_2015
            gain_mask = (change_ndvi > threshold).astype(np.float32)
            gain_pixels = np.sum(gain_mask > 0)
            gain_area_sq_km = (gain_pixels * pixel_area_m2) / 1e6

            out_path = os.path.join(output_dir, f"{region}_vegetation_gain_{start_year}_{end_year}.tif")
            try:
                import rasterio
                meta.update(count=1, dtype=rasterio.float32, nodata=0.0)
                with rasterio.open(out_path, 'w', **meta) as dst:
                    dst.write(gain_mask, 1)
            except (ImportError, UnboundLocalError):
                out_path = os.path.join(output_dir, f"{region}_vegetation_gain_{start_year}_{end_year}.npy")
                np.save(out_path, gain_mask)

            return {
                "output_path": out_path,
                "layer_name": f"Vegetation Gain ({start_year}-{end_year})",
                "operation": "Vegetation Growth Detection",
                "summary_stats": {
                    "Region": region.capitalize(),
                    "Timeframe": f"{start_year} - {end_year}",
                    "Vegetation Area Gained": f"{gain_area_sq_km:.2f} sq km",
                    "Gain Pixel Count": int(gain_pixels),
                    "Chart Type": "gain",
                    "Chart Retained Pct": pct_retained,
                    "Chart Gain Pct": pct_gain,
                    "Chart Builtup Pct": pct_builtup
                }
            }

    @staticmethod
    def compute_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """Computes Normalized Difference Vegetation Index (NDVI)."""
        denominator = nir + red
        denominator[denominator == 0] = 1e-10
        ndvi = (nir - red) / denominator
        return np.clip(ndvi, -1.0, 1.0)
