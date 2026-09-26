# 🌍 Knowbuild 2.0 — GeoGPT: LLM-Powered Geospatial Analysis for QGIS

> **"ChatGPT for QGIS"** — Natural language satellite image processing, change detection, and spatial analytics inside QGIS.

[![QGIS](https://img.shields.io/badge/QGIS-3.0%2B-brightgreen.svg)](https://qgis.org/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4%20%2F%20GPT--3.5-orange.svg)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📌 Problem Statement
Satellite imagery holds key answers to environmental and urban questions—such as vegetation loss, flood damage, or urban expansion. However, deriving these insights currently requires deep GIS domain expertise, PyQGIS scripting, and raster band algebra skills.

**GeoGPT** bridges this gap by enabling urban planners, environmental analysts, and researchers to perform complex satellite data analytics in plain English (e.g. *"Show vegetation loss in Pune between 2015 and 2020"*).

---

## 🏗️ System Architecture

```
                       ┌──────────────────────────────────────────────┐
                       │            QGIS Plugin Sidebar               │
                       │           (PyQt Dock Widget)                 │
                       └──────┬────────────────────────┬──────────────┘
                              │ 1. NL Query            │ 4. Render Layers
                              ▼                        ▼
                       ┌──────────────┐        ┌──────────────┐
                       │  LLM Parser  │        │ QGIS Canvas  │
                       │  (OpenAI /   │        │ (PyQGIS      │
                       │   Fallback)  │        │  Renderer)   │
                       └──────┬───────┘        └──────▲───────┘
                              │ 2. JSON Plan          │ 3. GeoTIFF Rasters
                              ▼                        │ + Stats
                       ┌──────────────────────────────┴───────┐
                       │        Geo-processing Engine         │
                       │   (xarray, rasterio, numpy, pyqgis)  │
                       └──────────────────────┬───────────────┘
                                              │ Reads Bands
                                              ▼
                       ┌──────────────────────────────────────┐
                       │          Satellite Data Cube         │
                       │  (GeoTIFF Composites: 2015 & 2020)   │
                       └──────────────────────────────────────┘
```

---

## 🎨 Visualization & AI Solution Features

When a natural language query is executed, **GeoGPT** delivers a 3-part output inside QGIS:

1. **🗺️ Map Canvas Layer Rendering:** Dynamically styled raster layers (NDVI pseudocolor ramps and bright red vegetation loss masks).
2. **📊 Visual Land Cover Distribution Chart:** Embedded PyQt/Matplotlib pie chart showing percentage breakdown of **Vegetation Retained**, **Vegetation Lost**, and **Built-Up Areas**.
3. **💡 AI Key Findings & Actionable Solutions:** Natural language narrative synthesizing spatial metrics into concrete urban planning recommendations (eco-buffer zones, afforestation targets, and green roofing policies).

---

## 📂 Repository Structure

The codebase is modularized cleanly across independent python modules:

```
├── README.md                      # Comprehensive project guide & QGIS connection steps
├── requirements.txt               # External python dependencies
├── generate_dummy_data.py         # Standalone synthetic data cube generator
└── chatgpt_qgis_plugin/           # Main QGIS Plugin directory
    ├── __init__.py                # QGIS Plugin factory entrypoint
    ├── metadata.txt               # QGIS Plugin metadata descriptor
    ├── plugin.py                  # Core plugin class & QGIS GUI hooks
    ├── dock_widget.py             # PyQt5 Sidebar UI (Query box, settings & stats table)
    ├── llm_parser.py              # LLM Translation Engine & Rule-based fallback parser
    ├── geo_engine.py              # Raster engine (NDVI & change detection metrics)
    └── qgis_renderer.py           # PyQGIS canvas layer renderer & styling
```

---

## 🚀 Quick Start Guide

### Step 1: Clone Repository & Install Dependencies
```bash
git clone https://github.com/your-username/chatgpt-qgis.git
cd chatgpt-qgis
pip install -r requirements.txt
```

### Step 2: Generate Synthetic Satellite Datacube
If you do not have satellite imagery on hand, generate a pre-processed multi-spectral dataset (Pune 2015 & 2020) using:
```bash
python generate_dummy_data.py
```
This generates `data/pune_2015.tif` and `data/pune_2020.tif` containing 4 spectral bands (Blue, Green, Red, NIR).

---

## 🔌 Connecting & Loading Plugin in QGIS

### Method 1: Symbolic Link / Copy (Recommended)

Copy or symlink the `chatgpt_qgis_plugin` folder directly into your QGIS active plugins directory:

* **Windows:**
  `C:\Users\<Your-Username>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
* **macOS:**
  `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
* **Linux:**
  `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`

Example command on Windows PowerShell:
```powershell
Copy-Item -Recurse -Force .\chatgpt_qgis_plugin "$env:APPDATA\QGIS\QGIS3\profiles\default\python\plugins\chatgpt_qgis_plugin"
```

### Method 2: Enable Plugin in QGIS
1. Launch **QGIS**.
2. Go to top menu: **Plugins** ➔ **Manage and Install Plugins...**
3. Select **Installed** tab on the left.
4. Check the box next to **GeoGPT - LLM Geospatial Analysis**.
5. The **GeoGPT AI Analysis** icon will appear on your toolbar and under **Plugins ➔ GeoGPT Analysis**.

---

## 🎯 How to Use the Plugin

1. Click the **GeoGPT** icon on the QGIS toolbar to launch the sidebar.
2. *(Optional)* Paste your **OpenAI API Key** (`sk-...`). If left blank, the plugin automatically switches to its local **Deterministic Fallback Parser**.
3. Ensure the **Data Cube Path** points to your `data/` folder (or generated `pune_*.tif` files).
4. Type your query in plain English:
   * *"Show vegetation loss in Pune between 2015 and 2020"*
   * *"Compute NDVI for 2015"*
5. Click **⚡ Execute Analysis**.

### What Happens Behind the Scenes:
1. **LLM Translation:** The query is parsed into a structured JSON execution plan:
   ```json
   {
     "operation": "vegetation_loss",
     "region": "pune",
     "start_year": 2015,
     "end_year": 2020,
     "threshold": 0.15
   }
   ```
2. **Band Mathematics:** The backend computes Normalized Difference Vegetation Index:
   $$\text{NDVI} = \frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red}}$$
   $$\Delta \text{NDVI} = \text{NDVI}_{2020} - \text{NDVI}_{2015}$$
3. **QGIS Canvas Render:** The change mask is dynamically added to the map canvas using Single Band Pseudocolor styling.
4. **Summary Metrics:** Area lost ($km^2$) and percentage drop are computed and listed in the results panel.

---

## 🛠️ Tech Stack & Frameworks

* **Frontend / GUI:** PyQt5, PyQGIS (QGIS DockWidget Interface)
* **LLM Engine:** OpenAI API (GPT-4 / GPT-3.5-Turbo), Rule-Based Regex Fallback Parser
* **Geospatial Engine:** Python (`xarray`, `rasterio`, `numpy`)
* **Spatial Data:** 4-band satellite data cubes (EPSG:4326)

---

## 📜 License
Developed under MIT License for ALT-F4 Team — Knowbuild 2.0.
