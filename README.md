# geopoly-simplify: Topology-Preserving Geological Map Simplification

<!-- Badges — replace placeholders once the repository and Zenodo record are live -->
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)

---

## Description

**geopoly-simplify** is a Python tool for simplifying polygon and line (fault) shapefiles
representing geological maps across multiple output scales, while rigorously preserving
topological integrity — producing outputs that contain no gaps between adjacent polygons,
no overlaps, and no broken alignments between the fault network and polygon boundaries.

The tool implements a **Modified Visvalingam-Whyatt (MVW)** algorithm within a
three-stage pipeline:

1. **Stage 0 — Topology pre-processing**: coordinate snapping, hairline overlap/gap
   correction, and bidirectional fault-polygon vertex alignment.
2. **Stage 1 — Fault network simplification**: MVW simplification of fault lines with
   all polygon-boundary vertices pinned as hard constraints.
3. **Stage 2 — Polygon simplification**: MVW simplification of polygon units with
   junction pinning, fault-vertex pinning, boundary preservation, unique geological
   contact pinning, and thin-body collapse prevention.

The tool was developed and tested on two Australian geological datasets:

- **GSWA** (Geological Survey of Western Australia) — Ninghan 1:500 000 geological map
- **GSSA** (Geological Survey of South Australia) — Flinders Ranges geological map

---

## Installation

**Requirements:** Python 3.9 or later.

Clone or download this repository, then install the dependencies:

```bash
pip install -r requirements.txt
```

The core dependencies are:

| Package | Minimum version |
|---------|----------------|
| fiona | 1.9 |
| shapely | 2.0 |
| geopandas | 0.14 |
| numpy | 1.24 |
| pandas | 2.0 |

No separate compilation step is required. All dependencies are available from PyPI.

---

## Quick-Start Examples

### Basic single-stage polygon simplification

Simplify a polygon shapefile without a fault network, using the Modified
Visvalingam-Whyatt algorithm at a 50 000 m² area threshold:

```python
from geopoly_simplify import vector_simplify_file_two_stage

result = vector_simplify_file_two_stage(
    input_file  = "geology_polygons.shp",
    output_file = "geology_polygons_simplified.shp",
    method      = "modified_visvalingam_whyatt",
    threshold   = 50_000,        # area threshold in m²
)

print(f"Features processed : {result['features_processed']}")
print(f"Features simplified: {result['features_simplified']}")
```

### Full three-stage pipeline with fault network

Run the complete topology-preserving pipeline — topology pre-processing,
fault simplification, and polygon simplification — at two scales:

```python
from geopoly_simplify import vector_simplify_file_two_stage

# --- Medium scale (e.g. 1:500 000) ---
result_500k = vector_simplify_file_two_stage(
    input_file        = "geology_polygons.shp",
    output_file       = "geology_500k.shp",
    method            = "modified_visvalingam_whyatt",
    threshold         = 500_000,          # 500 000 m² area threshold
    fault_file        = "faults.shp",     # fault network aligned with polygons
    boundary_preserve = "hard",           # pin exterior boundary vertices
    unit_field        = "CODE",           # geological unit identifier field
    preprocess        = True,             # run Stage 0 topology pre-processing
    snap_decimals     = 7,                # coordinate grid precision
)

# --- Small scale (e.g. 1:2 000 000) ---
result_2m = vector_simplify_file_two_stage(
    input_file        = "geology_polygons.shp",
    output_file       = "geology_2m.shp",
    method            = "modified_visvalingam_whyatt",
    threshold         = 2_000_000,        # 2 000 000 m² area threshold
    fault_file        = "faults.shp",
    boundary_preserve = "soft",           # allow exterior vertices to be removed
    unit_field        = "CODE",
    preprocess        = True,
    snap_decimals     = 7,
)

# Inspect contact preservation statistics
print(f"Contacts preserved (shape OK): {result_500k['n_contact_preserved']}")
print(f"Contacts minimal (2 verts)   : {result_500k['n_contact_minimal']}")
print(f"Contacts shape-lost (1 vert) : {result_500k['n_contact_shape_lost']}")
print(f"Contacts diverged            : {result_500k['n_contact_diverged']}")
```

See `examples/run_simplification.py` for a fully-commented walkthrough.

---

## Algorithm Overview

geopoly-simplify uses a **Modified Visvalingam-Whyatt (MVW)** algorithm embedded in a
three-stage topology-preserving pipeline.

- **Visvalingam-Whyatt core**: vertices are ranked by the area of the triangle they form
  with their two neighbours; those with the smallest effective area are removed first,
  in a min-heap priority queue, until the remaining vertex count satisfies the threshold.

- **Junction pinning**: every point where three or more features meet receives an
  infinite area weight and is never removed, preventing T-junction breaks and gaps.

- **Fault-polygon alignment**: fault vertices that coincide with polygon boundary vertices
  are pinned in both directions, so fault lines and polygon edges stay co-located after
  simplification.

- **Geological contact pinning**: for every unique pair of adjacent geological units, one
  representative vertex on the shared boundary is pinned, guaranteeing that the contact
  relationship is always detectable in the output.

- **Thin-body protection**: narrow polygons (fold stripes, dyke outlines) are
  pre-simplified at a conservative threshold; surviving intermediate vertices are pinned
  before the main simplification run, preventing interior collapse and cross-boundary gaps.

- **Self-intersection prevention**: a cross-product edge test vetoes any vertex removal
  that would create a self-intersecting ring; a `make_valid()` post-pass repairs any
  residual crossings.

- **Collapse fallback cascade**: if arc-mode MVW cannot produce a valid ring, the
  pipeline tries ring-mode MVW (with progressive threshold reduction), then
  neighbour-clipping, then writes the original geometry as a last resort.

- **Six available algorithms**: Decimation, Douglas-Peucker, Douglas-Peucker TP,
  Bend Simplification, Visvalingam-Whyatt, Modified Visvalingam-Whyatt. MVW is
  recommended for geological maps.

---

## Data Compatibility

- **Format**: Esri Shapefile (`.shp`). Input files are read and written via
  [Fiona](https://github.com/Toblerity/Fiona); any Fiona-supported driver can be
  adapted with minor changes.
- **Coordinate reference system**: any projected CRS with linear units in metres is
  supported. The `threshold` parameter is expressed in square metres (m²); ensure your
  data is in a metric projection before running the tool.
- **Geometry types**: `Polygon` and `MultiPolygon` for the polygon layer; `LineString`
  and `MultiLineString` for the fault layer.
- **Attribute schema**: the polygon layer must contain a field identifying geological
  units (default field name `CODE`, as used in GSWA datasets). Override with the
  `unit_field` parameter for other naming conventions.

### Tested datasets

| Dataset | Source | Coverage | Scale |
|---------|--------|----------|-------|
| Ninghan geological map | GSWA (Geological Survey of Western Australia) | Ninghan region, WA | 1:500 000 |
| Flinders Ranges geological map | GSSA (Geological Survey of South Australia) | Flinders Ranges, SA | varies |

---

## Citation

If you use geopoly-simplify in your research, please cite:

### APA

Joshi, R. (2025). *geopoly-simplify: Topology-preserving simplification of geological map
vector data* (Version 1.0.0) [Software]. Zenodo.
https://doi.org/10.5281/zenodo.XXXXXXX

### BibTeX

```bibtex
@software{joshi2025geopolysimplify,
  author    = {Joshi, Ranee},
  title     = {{geopoly-simplify}: Topology-Preserving Simplification of
               Geological Map Vector Data},
  year      = {2025},
  version   = {1.0.0},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.XXXXXXX},
  url       = {https://doi.org/10.5281/zenodo.XXXXXXX}
}
```

The MVW algorithm builds on:

- Visvalingam, M., & Whyatt, J. D. (1992). Line generalisation by repeated elimination
  of points. *The Cartographic Journal*, 30(1), 46-51.
  https://doi.org/10.1179/000870493786962263
- Douglas, D. H., & Peucker, T. K. (1973). Algorithms for the reduction of the number of
  points required to represent a digitized line or its caricature. *The Canadian
  Cartographer*, 10(2), 112-122. https://doi.org/10.3138/FM57-6770-U75U-7727

---

## Data Sources

The tool was developed and validated using datasets provided by:

- **Geological Survey of Western Australia (GSWA)** — Ninghan 1:500 000 geological map.
  Data accessed under the GSWA open data licence.
  https://www.dmp.wa.gov.au/Geological-Survey/Geological-Survey-262.aspx

- **Geological Survey of South Australia (GSSA)** — Flinders Ranges geological map.
  Data accessed under the GSSA open data licence.
  https://www.energymining.sa.gov.au/industry/geological-survey

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for
details.
