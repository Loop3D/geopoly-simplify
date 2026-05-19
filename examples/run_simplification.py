"""
run_simplification.py
=====================
Fully-commented example script for geopoly-simplify.

This script demonstrates three usage patterns:

  1. Basic single-stage simplification (polygon layer only, no fault network)
  2. Full three-stage pipeline with fault network at medium scale (1:500 000)
  3. Full three-stage pipeline with fault network at small scale (1:2 000 000)

Replace the placeholder file paths marked with <REPLACE> before running.

Requirements
------------
Install dependencies first:

    pip install -r requirements.txt

Then place geopoly_simplify.py on your Python path, or in the same
directory as this file, and import from it as shown below.

Usage
-----
    python run_simplification.py

All output shapefiles are written to the OUTPUT_DIR directory.
"""

import os
import sys

# ---------------------------------------------------------------------------
# Adjust this import to match the actual filename / module name on your system.
# If the script is in the same folder as this example, this import works
# without modification.
# ---------------------------------------------------------------------------
# Add the repo root (one level up from examples/) to the path so that
# geopoly_simplify.py can be found without installing the package.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
from geopoly_simplify import vector_simplify_file_two_stage


# ---------------------------------------------------------------------------
# FILE PATHS — pre-configured to use the bundled sample data.
# The input/ and output/ folders sit at the repo root alongside this script.
# ---------------------------------------------------------------------------

POLYGON_FILE = os.path.join(REPO_ROOT, "input",  "geology_500k.shp")
FAULT_FILE   = os.path.join(REPO_ROOT, "input",  "faults_500k.shp")
OUTPUT_DIR   = os.path.join(REPO_ROOT, "output")

# Attribute field that identifies geological units.  The bundled GSWA dataset
# uses "CODE"; adjust this for other naming conventions.
UNIT_FIELD = "CODE"

# ---------------------------------------------------------------------------
# Ensure the output directory exists
# ---------------------------------------------------------------------------
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ===========================================================================
# EXAMPLE 1 — Basic single-stage polygon simplification
# ===========================================================================
# Uses the Modified Visvalingam-Whyatt algorithm on the polygon layer only,
# without a fault network.  This is the simplest call and does not run the
# topology pre-processing or fault alignment stages.
#
# threshold = 50 000 m²  — vertices forming triangles smaller than this area
#                          are candidates for removal.  A good starting value
#                          for datasets in the 1:100 000 – 1:500 000 range.
# ---------------------------------------------------------------------------

print("=" * 60)
print("EXAMPLE 1: Basic single-stage polygon simplification")
print("=" * 60)

output_basic = os.path.join(OUTPUT_DIR, "geology_basic_50k.shp")

result_basic = vector_simplify_file_two_stage(
    input_file        = POLYGON_FILE,
    output_file       = output_basic,
    method            = "modified_visvalingam_whyatt",
    threshold         = 50000,        # 50 000 m² area threshold
    fault_file        = None,          # no fault network — single-stage only
    boundary_preserve = "hard",        # pin exterior boundary vertices
    unit_field        = UNIT_FIELD,
    preprocess        = False,         # skip topology pre-processing
)

# The return value is a dict summarising the run.
print(f"\nBasic simplification complete.")
print(f"  Output file        : {output_basic}")
print(f"  Algorithm          : {result_basic['method']}")
print(f"  Threshold          : {result_basic['threshold']:,} m²")
print(f"  Features processed : {result_basic['features_processed']}")
print(f"  Features simplified: {result_basic['features_simplified']}")


# ===========================================================================
# EXAMPLE 2 — Full three-stage pipeline at medium scale (threshold 500 000 m²)
# ===========================================================================
# Runs the complete pipeline:
#   Stage 0 — Topology pre-processing (coordinate snap, overlap/gap fix,
#              fault-polygon vertex alignment)
#   Stage 1 — Fault network simplification (polygon-boundary vertices pinned)
#   Stage 2 — Polygon simplification (junction, fault, and contact pinning)
#
# boundary_preserve = "hard"
#   Every vertex on the exterior map boundary is given an infinite area weight
#   and cannot be removed.  Use "hard" when the dataset has a rectangular or
#   irregular clipping boundary that must be preserved exactly.
#
# snap_decimals = 7
#   Coordinates are snapped to a 0.0000001-unit grid (suitable for data in
#   metres; effectively sub-millimetre precision).
# ---------------------------------------------------------------------------

print("\n" + "=" * 60)
print("EXAMPLE 2: Three-stage pipeline — medium scale (500 000 m²)")
print("=" * 60)

output_500k   = os.path.join(OUTPUT_DIR, "geology_500k.shp")
output_f_500k = os.path.join(OUTPUT_DIR, "faults_500k.shp")  # simplified faults

result_500k = vector_simplify_file_two_stage(
    input_file        = POLYGON_FILE,
    output_file       = output_500k,
    method            = "modified_visvalingam_whyatt",
    threshold         = 500000,       # 500 000 m² — suitable for 1:500 000
    fault_file        = FAULT_FILE,    # enables Stages 0 + 1
    boundary_preserve = "hard",        # exterior vertices pinned absolutely
    unit_field        = UNIT_FIELD,    # geological unit code field
    preprocess        = True,          # run Stage 0 topology pre-processing
    snap_decimals     = 7,             # coordinate precision grid
)

# ---- Interpreting the result dict ----------------------------------------
#
# result_500k contains the following keys after a three-stage run:
#
#   method                 : algorithm name used
#   threshold              : area threshold (m²) that was applied
#   features_processed     : total number of polygon features read from input
#   features_simplified    : features that were successfully simplified
#   n_contact_preserved    : contacts where the shared boundary retains >= 3
#                            vertices — shape is well preserved
#   n_contact_minimal      : contacts with exactly 2 shared vertices — the
#                            contact is present but reduced to a straight line
#   n_contact_shape_lost   : contacts with 1 shared vertex — the relationship
#                            is still recorded but spatial shape is lost
#   n_contact_diverged     : contacts where the two polygon boundaries no
#                            longer share any vertices — reduce the threshold
#                            if this number is non-zero
#   contacts               : dict of all unique CODE-pair contact info
#   contact_status         : per-contact status string after simplification
#   topo_stats             : topology pre-processing summary (Stage 0)
#
# The contact health numbers are the most important quality indicators.
# Aim for n_contact_diverged == 0 at all target scales.
# ---------------------------------------------------------------------------

print(f"\nMedium-scale simplification complete.")
print(f"  Output polygons : {output_500k}")
print(f"  Algorithm       : {result_500k['method']}")
print(f"  Threshold       : {result_500k['threshold']:,} m²")
print(f"  Features in / out: "
      f"{result_500k['features_processed']} / {result_500k['features_simplified']}")
print()
print("  Geological contact preservation report:")
print(f"    Preserved  (>= 3 shared vertices): {result_500k['n_contact_preserved']}")
print(f"    Minimal    (== 2 shared vertices): {result_500k['n_contact_minimal']}")
print(f"    Shape-lost (== 1 shared vertex)  : {result_500k['n_contact_shape_lost']}")
print(f"    Diverged   (0 shared vertices)   : {result_500k['n_contact_diverged']}")

if result_500k['n_contact_diverged'] > 0:
    print("\n  WARNING: Some contacts have diverged. Reduce the threshold or check")
    print("  whether fault-polygon alignment is correct in those areas.")


# ===========================================================================
# EXAMPLE 3 — Full three-stage pipeline at small scale (threshold 2 000 000 m²)
# ===========================================================================
# At small scales more aggressive simplification is needed.  Using
# boundary_preserve = "soft" allows exterior boundary vertices to be removed
# when their triangle area is below soft_tolerance (default: threshold / 10).
# This produces a smoother outline while still preferentially retaining
# exterior vertices compared to interior ones.
#
# Increasing the threshold will:
#   - reduce vertex count (smaller file, faster rendering)
#   - increase the risk of contact divergence for narrow or small polygons
#   - widen the gap between simplified and original geometry
#
# Monitor n_contact_diverged carefully when scaling up the threshold.
# ---------------------------------------------------------------------------

print("\n" + "=" * 60)
print("EXAMPLE 3: Three-stage pipeline — small scale (2 000 000 m²)")
print("=" * 60)

output_2m   = os.path.join(OUTPUT_DIR, "geology_2m.shp")
output_f_2m = os.path.join(OUTPUT_DIR, "faults_2m.shp")

result_2m = vector_simplify_file_two_stage(
    input_file        = POLYGON_FILE,
    output_file       = output_2m,
    method            = "modified_visvalingam_whyatt",
    threshold         = 2000000,     # 2 000 000 m² — suitable for 1:2 000 000
    fault_file        = FAULT_FILE,
    boundary_preserve = "soft",        # exterior vertices resist but can be removed
    soft_tolerance    = 200_000,       # exterior vertices removed only below this value
    unit_field        = UNIT_FIELD,
    preprocess        = True,
    snap_decimals     = 7,
)

print(f"\nSmall-scale simplification complete.")
print(f"  Output polygons : {output_2m}")
print(f"  Threshold       : {result_2m['threshold']:,} m²")
print(f"  Features in / out: "
      f"{result_2m['features_processed']} / {result_2m['features_simplified']}")
print()
print("  Geological contact preservation report:")
print(f"    Preserved  (>= 3 shared vertices): {result_2m['n_contact_preserved']}")
print(f"    Minimal    (== 2 shared vertices): {result_2m['n_contact_minimal']}")
print(f"    Shape-lost (== 1 shared vertex)  : {result_2m['n_contact_shape_lost']}")
print(f"    Diverged   (0 shared vertices)   : {result_2m['n_contact_diverged']}")

if result_2m['n_contact_diverged'] > 0:
    print("\n  WARNING: Some contacts have diverged at this scale.")
    print("  Consider reducing the threshold or inspecting individual diverged contacts")
    print("  via result_2m['contact_status'] for the CODE pairs concerned.")


# ===========================================================================
# TIPS FOR CHOOSING THRESHOLD VALUES
# ===========================================================================
#
# The threshold is an *area* in square metres (m²), not a distance.  Rough
# equivalences for geological mapping:
#
#   Target scale   | Suggested starting threshold
#   1:100 000      | 10 000 – 50 000 m²
#   1:500 000      | 250 000 – 750 000 m²
#   1:1 000 000    | 500 000 – 1 500 000 m²
#   1:2 000 000    | 1 000 000 – 3 000 000 m²
#
# Always check the contact health report and inspect output in a GIS viewer
# before finalising a threshold.  If n_contact_diverged > 0, reduce the
# threshold until all contacts are preserved or minimal.
#
# For GSWA-style datasets the field UNIT_FIELD = "CODE" is correct.
# For GSSA-style datasets check the attribute table and set UNIT_FIELD
# to the appropriate column name (e.g. "MAPUNIT", "SYMBOL", etc.).
# ===========================================================================

print("\nAll examples complete.")
