# ML pipeline source

The source tree is split by responsibility so the eventual pipeline can be
extended region by region:

- `data/` — source adapters and dataset manifests.
- `preprocessing/` — cleaning plus spatial and temporal alignment.
- `features/` — rainfall windows, soil moisture, terrain, and historical-risk
  features.
- `models/` — training, testing, and explainability.
- `prediction/` — inference and risk-score orchestration.

Phase 1 contains no data downloaders, training code, or inference logic.