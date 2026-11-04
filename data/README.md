# Data boundary

This directory separates source downloads from derived data:

- `raw/` contains untouched downloads grouped by region and source.
- `processed/` contains cleaned and regridded regional data derived from raw.
- `final/` contains the merged ML-ready table once labeling and validation are
  complete.

Raw files must never be modified directly. Phase 1 creates only directory
placeholders; it does not download or fabricate datasets.