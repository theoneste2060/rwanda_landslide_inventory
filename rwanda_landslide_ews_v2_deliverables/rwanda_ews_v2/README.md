# Rwanda Landslide EWS Feasibility — Version 2

This version expands the earlier readiness analysis with a page-referenced review of REMA’s 2022 landslide-risk report, an inventory/access crosswalk, an updated evidence table, a source audit, a revised event-count decision matrix, a tiered EWS concept, a preregistered REMA susceptibility-validation plan, and reproducible scripts. The earlier `rwanda_ews` project remains unchanged; this folder is the new versioned deliverable.

## Critical interpretation

The report distinguishes three different things: (1) the existing 88-row incident compilation, (2) REMA’s 2,544-point shallow initiation sample for static susceptibility, and (3) a separate public 7,944-point regional shallow-landslide update on Zenodo. Do not combine them or treat mapped point counts as independent, day-dated rainfall-triggering episodes. The supplied source registry’s labels `depicker_2020a` and `depicker_2020b` resolve to the same Geomorphology DOI; the 6,446-landslide catalogue is not established as a separate public data asset. The later 7,944-point Zenodo file is openly available under CC BY 4.0, but its exact equivalence to either the 6,446 catalogue or REMA’s 2,544-point input is unverified.

No real rainfall threshold, real-data cross-validation, operational probability or EWS skill estimate was generated in v2. The 2022 report gives a published static susceptibility/historical-rate analysis; it does not provide day-level image-bracket dates or a short-term rainfall-warning rule.

## Rights and redistribution

Read `input/LICENSE.md` before sharing raw inputs. The upstream repository explicitly states there is no single blanket open license for the compiled v2 tables; its sources have mixed or incomplete terms. The public 7,944-point Zenodo file has CC BY 4.0 terms; attribute the source and identify changes if redistributed or adapted. Do not redistribute third-party Google Earth, DigitalGlobe or CNES/Airbus imagery. Keep upstream attribution and licenses with any data extract. This project is an analysis package, not a legal determination of rights.

## Environment setup

Python 3.10 or newer is recommended. Create an isolated environment and install the listed dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The scripts write outputs under the paths passed to `--out`; run from this folder unless using absolute paths.

## Reproducible commands

Recompute the event/site readiness screens from the packaged source tables:

```bash
python scripts/readiness_baseline.py \
  --events input/events.csv \
  --sites input/sites.csv \
  --out outputs/readiness_real
```

Rebuild the source-evidence, data-access, dataset-crosswalk and page-referenced REMA-extraction tables:

```bash
python scripts/build_v2_evidence.py
python scripts/build_access_log.py
python scripts/build_dataset_crosswalk.py
python scripts/build_rema_extraction.py
```

Audit the public Zenodo point-layer schema, without assigning undocumented meanings to fields:

```bash
python scripts/inspect_zenodo_layer.py \
  --shapefile source/zenodo_5027004_extracted/landslide_data.shp \
  --out outputs/zenodo_layer_audit.json
```

Re-run the explicitly synthetic sample-size demonstration and validation scaffold:

```bash
python scripts/sample_size_demo.py --out outputs/synthetic_sample_size
python scripts/validation_workflow.py \
  --synthetic-demo \
  --out outputs/synthetic_validation \
  --permutations 49
```

The synthetic sample-size script simulates a log-log rainfall intensity-duration curve from synthetic event windows and reports the bootstrap interval width for curve intensity at 24 hours, plus repeated held-out AUC distributions for a separate balanced logistic case-control simulation. It does **not** estimate a real warning threshold, false-alarm rate, lead time or Rwanda model performance. The validation demonstration uses synthetic spatial blocks, synthetic rare events, a later-year holdout and a within-block label-permutation diagnostic. All output files are tagged as synthetic.

## Real-data REMA susceptibility comparison

`scripts/replicate_rema_validation.py` is deliberately strict. It does not create labels, background points, dates, predictors or spatial groups. The default input must be a **prepared, licensed CSV** with 2,544 mapped REMA initiation points and 2,544 documented background points. Required columns are:

- `label`: `1` for mapped REMA initiation point and `0` for sampled background point.
- `spatial_block`: prespecified geographic group identifier with at least five distinct groups. Assign groups before fitting and keep nearby/related points together where appropriate.
- Numeric predictors with these default exact names: `elevation_m`, `slope_deg`, `profile_curvature`, `planar_curvature`, `north_exposure`, `east_exposure`, `rejuvenated_landscape`, `distance_to_rivers_m`, `distance_to_faults_m`, `pga_ms2`, `road_within_50m`, `clay_pct`, `landuse_closed_agriculture`, `landuse_open_agriculture`, `landuse_irrigated`, `landuse_forest`, `landuse_open_land`, and `landuse_built_up`.
- Optional `image_year`, only if the field’s meaning is documented. Image-bracket year is not a day-level event date.

Example after obtaining and documenting permitted real inputs:

```bash
python scripts/replicate_rema_validation.py \
  --data prepared_rema_points_and_background.csv \
  --out outputs/rema_replication_real \
  --permutations 999
```

The script compares stratified random 10-fold CV with five-fold spatial GroupKFold, and can run a chronological holdout when a verified year field is present. It uses the default 2,544-per-class requirement unless `--allow-nonexact-counts` is explicitly used for a clearly labelled sensitivity run. The comparison is **comparable, not bit-for-bit reproduction**: original raster versions, stepwise-selection recipe, pseudo-absence coordinates/seed and code were not located. The paired spatial-block bootstrap interval is conditional on out-of-fold predictions/fold design; it does not capture all training, background-sampling or raster uncertainty. The within-block permutation test preserves each block’s event count and is an association diagnostic, not a causal test.

As of this report, the exact REMA 2,544-point layer and full predictor stack were not obtained, so no real replication output exists. The public 7,944-point Zenodo file is not a substitute without an author-provided version crosswalk and resolved field definitions.

## Main deliverables

- `report.md` — canonical, relative-link Markdown report.
- `report.pdf` — Typst-generated PDF version of the report.
- `evidence_table.csv` — unique DOI/URL evidence records with a fixed 1–4 verification scale and rationale.
- `duplicate_doi_review.csv` — legacy duplicate DOI rows plus the upstream Depicker 2020a/2020b alias collision.
- `rema_extraction_table.csv` — 38 page-referenced extraction rows for the REMA report’s methods, predictors, validation, hazard, exposure and mitigation results.
- `inventory_dataset_crosswalk.csv` — inventory/data records, including unavailable and open-but-not-equivalent sources.
- `data_access_log.csv` — 23 source-access and custodian-route records.
- `source_findings.md` — source-level verification notes and contact routes.
- `scripts/` — readiness analysis, source-table builders, Zenodo schema audit, synthetic simulations and strict real-data replication utility.
- `outputs/` — reproducible real-readiness outputs and synthetic-only demonstration outputs.
- `source/` and `input/` — the official REMA PDF, raw/derived inventory files, repository snapshots and provenance/licensing notes.

## Report and table references

The report cites external sources with numbered references. Its local links are relative to this folder. `rema_extraction_table.csv` records the REMA PDF and printed page for each extracted item; the two page-number systems differ by one on many pages because of the cover. The data-access and crosswalk tables distinguish article availability from primary-data availability, and distinguish article licenses from dataset licenses.
