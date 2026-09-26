"""
generate_dummy_data.py
----------------------
Synthetic Satellite Data Cube Generator for Knowbuild 2.0 (GeoGPT for QGIS).

Generates two 4-band GeoTIFF satellite composites for Pune (2015 and 2020)
simulating urban development and vegetation loss over time.

Bands:
  Band 1: Blue
  Band 2: Green
  Band 3: Red
  Band 4: Near Infrared (NIR)
"""

import os
import numpy as np

def create_synthetic_cube():
    output_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(output_dir, exist_ok=True)

    print("Generating synthetic satellite data cube for Pune (2015 & 2020)...")

    # Dimensions (500x500 pixels ~ 5km x 5km at 10m resolution)
    height, width = 500, 500
    
    # Pune bounding box approximation (EPSG:4326)
    # Longitude: 73.80 to 73.85, Latitude: 18.50 to 18.55
    min_x, max_x = 73.80, 73.85
    min_y, max_y = 18.50, 18.55
    pixel_size_x = (max_x - min_x) / width
    pixel_size_y = (max_y - min_y) / height

    # Base land layout generation
    np.random.seed(42)
    
    # Distance from center to create a river/lake feature and urban core
    x_coords = np.linspace(0, 1, width)
    y_coords = np.linspace(0, 1, height)
    xx, yy = np.meshgrid(x_coords, y_coords)

    # Base vegetation mask for 2015 (high NIR in green regions)
    vegetation_2015 = (np.sin(xx * 5) + np.cos(yy * 5) + np.random.normal(0, 0.2, (height, width))) > 0.1
    
    # 2020 simulates urban expansion replacing ~30% of vegetation with concrete/buildings
    urban_expansion = (xx > 0.4) & (xx < 0.8) & (yy > 0.3) & (yy < 0.7)
    vegetation_2020 = vegetation_2015.copy()
    vegetation_2020[urban_expansion] = False

    years = [2015, 2020]
    veg_states = [vegetation_2015, vegetation_2020]

    try:
        import rasterio
        from rasterio.transform import from_bounds

        transform = from_bounds(min_x, min_y, max_x, max_y, width, height)
        crs = "EPSG:4326"

        for year, veg in zip(years, veg_states):
            file_path = os.path.join(output_dir, f"pune_{year}.tif")
            
            # Construct 4 spectral bands (scaled 0 to 10000 surface reflectance)
            blue = np.where(veg, 300, 1200) + np.random.randint(0, 100, (height, width))
            green = np.where(veg, 800, 1400) + np.random.randint(0, 100, (height, width))
            red = np.where(veg, 400, 1600) + np.random.randint(0, 100, (height, width))
            # NIR: High reflectance (~4000) for healthy vegetation, low (~1000) for built-up
            nir = np.where(veg, 4500, 1100) + np.random.randint(0, 150, (height, width))

            data = np.stack([blue, green, red, nir]).astype(np.uint16)

            with rasterio.open(
                file_path,
                'w',
                driver='GTiff',
                height=height,
                width=width,
                count=4,
                dtype=data.dtype,
                crs=crs,
                transform=transform,
            ) as dst:
                for b_idx in range(4):
                    dst.write(data[b_idx], b_idx + 1)
                    dst.set_band_description(b_idx + 1, ["Blue", "Green", "Red", "NIR"][b_idx])

            print(f" -> Created GeoTIFF: {file_path}")

    except ImportError:
        print("Notice: 'rasterio' library not installed. Using pure-python GeoTIFF binary generator.")
        
        def save_simple_tif(filename, bands_data, min_x, max_x, min_y, max_y):
            import struct
            # Simple uncompressed 4-band 16-bit TIFF image
            h, w = bands_data[0].shape
            num_bands = len(bands_data)
            
            # Write uncompressed raw TIFF container
            # Header: II (Little endian), 42 (magic number), offset to IFD (8)
            header = b'II\x2a\x00\x08\x00\x00\x00'
            
            # IFD entries: ImageWidth, ImageLength, BitsPerSample, Compression, Photometric, StripOffsets, SamplesPerPixel, RowsPerStrip, StripByteCounts
            num_entries = 9
            ifd_offset = 8
            pixel_data_offset = ifd_offset + 2 + (num_entries * 12) + 4 + 12 # extra for BPS array
            
            bps_offset = ifd_offset + 2 + (num_entries * 12) + 4
            bps_bytes = struct.pack('<4H', 16, 16, 16, 16)
            
            strip_bytes = h * w * num_bands * 2
            
            entries = [
                (256, 3, 1, w),                       # ImageWidth
                (257, 3, 1, h),                       # ImageLength
                (258, 3, 4, bps_offset),              # BitsPerSample -> pointer to 4 shorts
                (259, 3, 1, 1),                       # Compression: 1 = Uncompressed
                (262, 3, 1, 2),                       # Photometric: 2 = RGB / Multi-spectral
                (273, 4, 1, pixel_data_offset),       # StripOffsets
                (277, 3, 1, num_bands),               # SamplesPerPixel
                (278, 3, 1, h),                       # RowsPerStrip
                (279, 4, 1, strip_bytes)              # StripByteCounts
            ]
            
            ifd = struct.pack('<H', num_entries)
            for tag, field_type, count, val in entries:
                ifd += struct.pack('<HHII', tag, field_type, count, val)
            ifd += struct.pack('<I', 0) # Next IFD offset (0)
            
            # Interleave band data (height, width, bands)
            raw_pixels = np.stack(bands_data, axis=-1).astype('<u2').tobytes()
            
            with open(filename, 'wb') as f:
                f.write(header)
                f.write(ifd)
                f.write(bps_bytes)
                f.write(raw_pixels)

        for year, veg in zip(years, veg_states):
            file_path = os.path.join(output_dir, f"pune_{year}.tif")
            blue = np.where(veg, 300, 1200)
            green = np.where(veg, 800, 1400)
            red = np.where(veg, 400, 1600)
            nir = np.where(veg, 4500, 1100)
            bands = [blue, green, red, nir]
            save_simple_tif(file_path, bands, min_x, max_x, min_y, max_y)
            print(f" -> Created GeoTIFF raster: {file_path}")

    print("\nData cube generation complete! Files stored in 'data/' directory.")

if __name__ == "__main__":
    create_synthetic_cube()
