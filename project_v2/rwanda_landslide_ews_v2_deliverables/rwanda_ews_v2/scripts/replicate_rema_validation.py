#!/usr/bin/env python3
"""Comparable REMA shallow-susceptibility re-fit; refuses to synthesize real data.

Input is a PREPARED CSV containing exactly 2,544 positive initiation observations
and 2,544 non-landslide/background points by default. These must be the actual
REMA 2,544-point layer plus a documented 1:1 background sample. No labels,
absence points, predictors, dates, or spatial blocks are generated here.

The fixed numeric feature schema follows the REMA report's selected 30 m model
(all listed predictor families except lithology). This is a comparable re-fit,
not bit-for-bit replication: the exact original raster versions, stepwise
formula, pseudoabsence coordinates/seed and project code were not located.
Spatial blocks must be assigned before fitting and must keep nearby points and
related mapped-event/storm groups together as appropriate. An optional
image_year column enables a descriptive chronological holdout only when its
meaning is verified; image-bracket years are not daily event dates.
"""
from __future__ import annotations
import argparse
import importlib.util
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = Path(__file__).with_name("validation_workflow.py")
FEATURES = [
    "elevation_m", "slope_deg", "profile_curvature", "planar_curvature",
    "north_exposure", "east_exposure", "rejuvenated_landscape",
    "distance_to_rivers_m", "distance_to_faults_m", "pga_ms2",
    "road_within_50m", "clay_pct",
    "landuse_closed_agriculture", "landuse_open_agriculture",
    "landuse_irrigated", "landuse_forest", "landuse_open_land",
    "landuse_built_up",
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", required=True, help="Prepared real-data CSV; no labels/backgrounds are generated")
    ap.add_argument("--out", default="outputs/rema_replication_real")
    ap.add_argument("--label", default="label", help="1=REMA mapped initiation point; 0=sampled background point")
    ap.add_argument("--spatial-block", default="spatial_block", help="Predefined geographic block/group field")
    ap.add_argument("--year", default="image_year", help="Optional verified year field; skipped if absent")
    ap.add_argument("--features", default=",".join(FEATURES), help="Numeric feature columns; override only with documented schema")
    ap.add_argument("--expected-per-class", type=int, default=2544)
    ap.add_argument("--allow-nonexact-counts", action="store_true", help="Allow a documented non-2,544-per-class sensitivity table")
    ap.add_argument("--permutations", type=int, default=49)
    a = ap.parse_args()

    data = Path(a.data)
    if not data.exists():
        raise SystemExit(f"Input not found: {data}. Obtain and prepare licensed source data; no synthetic substitute is used.")
    df = pd.read_csv(data)
    features = [x.strip() for x in a.features.split(",") if x.strip()]
    required = [a.label, a.spatial_block, *features]
    missing = [x for x in required if x not in df.columns]
    if missing:
        raise SystemExit(f"Prepared CSV missing required columns: {missing}")
    df = df.dropna(subset=[a.label, a.spatial_block]).copy()
    labels = pd.to_numeric(df[a.label], errors="coerce")
    if labels.isna().any() or set(labels.unique()) != {0, 1}:
        raise SystemExit("label must contain only binary 0/1 values; 1=REMA initiation, 0=background.")
    counts = labels.value_counts().to_dict()
    expected = a.expected_per_class
    if not a.allow_nonexact_counts and (counts.get(1, 0) != expected or counts.get(0, 0) != expected):
        raise SystemExit(f"Expected {expected} positives and {expected} background points; found {counts}. "
                         "Use --allow-nonexact-counts only for an explicitly labelled sensitivity run.")
    for c in features:
        df[c] = pd.to_numeric(df[c], errors="coerce")
        if df[c].notna().sum() == 0:
            raise SystemExit(f"Feature {c!r} is entirely missing/non-numeric.")
    nblocks = df[a.spatial_block].nunique()
    if nblocks < 5:
        raise SystemExit(f"Need at least five spatial groups; found {nblocks}.")
    if a.year in df.columns:
        # Keep the temporal variable numeric but do not infer daily event timing.
        df[a.year] = pd.to_numeric(df[a.year], errors="coerce")

    spec = importlib.util.spec_from_file_location("validation_workflow", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    out = Path(a.out)
    metrics, delta, perm = module.run(
        df, a.label, features, a.spatial_block,
        a.year if a.year in df.columns else None,
        out, a.permutations, synthetic=False,
    )
    summary = {
        "synthetic": False,
        "status": "REAL INPUT ANALYSIS; only valid if input schema and source provenance are documented",
        "input": str(data.resolve()),
        "positive_rows": int(counts.get(1, 0)),
        "background_rows": int(counts.get(0, 0)),
        "spatial_blocks": int(nblocks),
        "features": features,
        "model_caveat": "Comparable fixed-feature logistic model; not bit-for-bit reproduction of the REMA stepwise fit.",
        "metrics": metrics,
        "random_minus_spatial_cluster_bootstrap_95ci": delta["paired_auc_drop_random_minus_spatial_95ci"],
        "permutation": perm,
    }
    import json
    (out / "replication_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
