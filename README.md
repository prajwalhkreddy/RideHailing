# NYC Ride-Hailing PhD Research

This repository is the modular research codebase for NYC ride-hailing demand prediction, routing, pricing, fleet simulation, and federated learning.

## Scope

- Dataset target: NYC, January 2026.
- Python version: 3.12.
- Unified environment: `ridehailing-phd`.

The existing NB1–NB5 notebooks are the reference implementation. They will subsequently be migrated into this modular codebase; they are intentionally not modified as part of this initial scaffold.

## Layout

- `config/`: configuration files.
- `data/raw/`, `data/interim/`, `data/processed/`: data organization.
- `models/demand/`, `models/routing/`, `models/pricing/`: model artifacts.
- `outputs/figures/`, `outputs/metrics/`, `outputs/logs/`: generated research outputs.
- `src/`: importable Python source package.
- `tests/`, `scripts/`, `notebooks/`, and `notebooks/legacy/`: supporting project areas.

No packages are installed by this repository. The first data/spatial milestone
is implemented below; subsequent research stages remain intentionally absent.

## First data/spatial milestone

The first executable milestone migrates only the legacy spatial preparation:
`NB1_Spatial_Info_Build.ipynb` supplies the EPSG:2263, 3,000 m square-grid
construction and North-to-South/West-to-East GridID ordering; `NB2_GridToTripAssignment`
supplies the seeded LocationID-to-GridID assignment. The January 2026 Yellow
Taxi input contains `PULocationID` and `DOLocationID`, but not coordinates.
Consequently, `scripts/build_grid.py` preserves NB2's deterministic seeded
zone-to-grid sampling and records that limitation in `grid_metadata.json`.
It does not misrepresent those assignments as coordinate-derived.

Run the stage locally with the existing `ridehailing-phd` environment:

```bash
python scripts/build_grid.py
python scripts/build_grid.py --validate
python scripts/build_grid.py --force
```

The script persists `cleaned_trips.parquet`, the authoritative
`grid_lookup.parquet`, grid mask, zone mappings, neighbor map, and metadata in
`data/processed/`. It does not implement NB3–NB5, TensorFlow, fleet logic,
routing, pricing, charging, simulation, or federated learning.

## NB3 demand preparation

`scripts/build_demand_master.py` modularizes the legacy NB3 tabular
demand-preparation workflow only. It creates the 14-column demand master table
needed by later tensor construction; it does not construct tensors, normalize
features, or train a CNN. The required Meteostat-derived processed weather file
is an explicit configured input and is never downloaded automatically.

## NB4 tensor generation

`scripts/build_cnn_dataset.py` converts the frozen NB3 master table into the
legacy NB4 float32 arrays and chronological 80/20 split. It preserves the
seven feature channels, zero-padded invalid grid positions, and one-step-ahead
raw-demand targets, but does not normalize data or import TensorFlow.

## NB5 CNN training

`scripts/train_cnn.py` reproduces the legacy NB5 baseline only: training-only
per-channel normalization, the three-layer same-padded CNN, early stopping,
and full padded-grid evaluation. It saves the frozen model and NB5-compatible
artifacts in `models/demand/`; `--validate` reloads and verifies them without
retraining. Padded positions intentionally remain unmasked to preserve the
reference implementation, which is a research limitation rather than a new
methodological choice.
