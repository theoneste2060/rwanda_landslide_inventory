#!/usr/bin/env python3
"""Spatial/temporal validation scaffold for landslide susceptibility data.

Real-data mode NEVER invents labels or background points. Input must be a prepared
CSV with a defensible binary label, genuine predictor columns, a spatial-block
column, and (optionally) a year column. Synthetic mode is explicitly opt-in and
all outputs are tagged SYNTHETIC.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss,
    confusion_matrix, roc_auc_score)
from sklearn.model_selection import GroupKFold, StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler


def make_synthetic(n=6000, seed=20261018):
    """Generate spatially clustered rare events solely to test the code path."""
    rng = np.random.default_rng(seed)
    lon = rng.uniform(0, 100, n)
    lat = rng.uniform(0, 100, n)
    year = rng.integers(2000, 2020, n)
    bx = np.floor(lon / 20).astype(int)
    by = np.floor(lat / 20).astype(int)
    block = (bx.astype(str) + "_" + by.astype(str))
    # Spatially structured covariates and latent block-level event propensity.
    terrain = (0.65*np.sin(lon/13) + 0.55*np.cos(lat/17)
               + rng.normal(0, 0.55, n))
    rain = rng.normal(0, 1, n) + 0.12*np.sin(lat/9) + 0.06*(year-2009.5)
    access = 0.45*np.cos(lon/11) + rng.normal(0, 0.8, n)
    latent = 0.70*np.sin(lon/24) + 0.70*np.cos(lat/27)
    logit = (-3.75 + 0.95*rain + 0.90*terrain + 0.25*access
             + 0.75*latent + 0.018*(year-2009.5))
    prob = 1/(1+np.exp(-logit))
    y = rng.binomial(1, prob)
    return pd.DataFrame({"y": y, "rain_feature": rain, "slope_feature": terrain,
                         "access_feature": access, "spatial_block": block,
                         "year": year, "x_synthetic": lon, "y_synthetic": lat})


def model():
    return make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                         LogisticRegression(max_iter=2000, C=1.0, solver="lbfgs"))


def predict_random(X, y, folds=10, seed=7301):
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    p = cross_val_predict(model(), X, y, cv=cv, method="predict_proba", n_jobs=1)[:, 1]
    return p


def predict_spatial(X, y, groups, folds=5):
    cv = GroupKFold(n_splits=folds)
    p = np.full(len(y), np.nan)
    for tr, te in cv.split(X, y, groups):
        if len(np.unique(y[tr])) < 2:
            raise ValueError("A spatial training fold contains only one class.")
        p[te] = model().fit(X.iloc[tr], y[tr]).predict_proba(X.iloc[te])[:, 1]
    if np.isnan(p).any():
        raise ValueError("Spatial CV did not predict every row.")
    return p


def metric_row(name, y, p, synthetic, n_train=None, n_test=None):
    y = np.asarray(y, dtype=int); p = np.asarray(p, dtype=float)
    pred = (p >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {"evaluation": name, "synthetic": bool(synthetic), "n_test": int(n_test or len(y)),
            "n_train": (None if n_train is None else int(n_train)),
            "positive_test": int(y.sum()), "negative_test": int((1-y).sum()),
            "roc_auc": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else np.nan,
            "average_precision": float(average_precision_score(y, p)) if y.sum() else np.nan,
            "brier_score": float(brier_score_loss(y, p)),
            "precision_at_0_5": float(tp/(tp+fp)) if tp+fp else 0.0,
            "recall_at_0_5": float(tp/(tp+fn)) if tp+fn else 0.0,
            "specificity_at_0_5": float(tn/(tn+fp)) if tn+fp else 0.0,
            "false_alarm_rate_at_0_5": float(fp/(fp+tn)) if fp+tn else np.nan}


def cluster_bootstrap(y, p_random, p_spatial, groups, n_boot=1000, seed=291):
    """Resample whole spatial blocks to quantify paired AUC/AP differences."""
    rng = np.random.default_rng(seed)
    y = np.asarray(y, dtype=int); groups = np.asarray(groups)
    unique = np.unique(groups)
    vals = []
    for _ in range(n_boot):
        picked = rng.choice(unique, size=len(unique), replace=True)
        idx = np.concatenate([np.flatnonzero(groups == g) for g in picked])
        if len(np.unique(y[idx])) < 2:
            continue
        ar = roc_auc_score(y[idx], p_random[idx]); ass = roc_auc_score(y[idx], p_spatial[idx])
        pr = average_precision_score(y[idx], p_random[idx]); ps = average_precision_score(y[idx], p_spatial[idx])
        vals.append((ar, ass, ar-ass, pr, ps, pr-ps))
    a = np.asarray(vals)
    if len(a) < 100:
        raise ValueError("Too few valid block-bootstrap draws; increase blocks or sample size.")
    names = ["random_auc", "spatial_auc", "random_minus_spatial_auc",
             "random_ap", "spatial_ap", "random_minus_spatial_ap"]
    return {name: [float(x) for x in np.quantile(a[:, i], [0.025, 0.975])]
            for i, name in enumerate(names)}, len(a)


def run(df, label, features, group_col, year_col, out, permutations, synthetic):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    required = [label, group_col, *features]
    missing = [c for c in required if c not in df.columns]
    if missing: raise ValueError(f"Missing required columns: {missing}")
    df = df.dropna(subset=[label, group_col]).copy()
    y = df[label].astype(int).to_numpy()
    if set(np.unique(y)) != {0, 1}:
        raise ValueError("The prepared evaluation table must contain both 0 and 1 labels.")
    X = df[features].apply(pd.to_numeric, errors="coerce")
    if X.isna().all(axis=0).any(): raise ValueError("At least one selected feature is entirely missing/non-numeric.")
    groups = df[group_col].astype(str).to_numpy()
    n_groups = len(np.unique(groups))
    if n_groups < 5: raise ValueError("At least five distinct spatial blocks are required.")

    pr = predict_random(X, y)
    ps = predict_spatial(X, y, groups)
    # These rows summarize out-of-fold predictions pooled across all held-out
    # observations; there is no single training size for the pooled score.
    metrics = [metric_row("random_stratified_10fold", y, pr, synthetic, None, len(y)),
               metric_row("spatial_group_5fold", y, ps, synthetic, None, len(y))]
    boot_ci, valid_boots = cluster_bootstrap(y, pr, ps, groups)
    for row, key in zip(metrics, ["random", "spatial"]):
        row["auc_cluster_bootstrap_95ci_low"], row["auc_cluster_bootstrap_95ci_high"] = boot_ci[f"{key}_auc"]
        row["ap_cluster_bootstrap_95ci_low"], row["ap_cluster_bootstrap_95ci_high"] = boot_ci[f"{key}_ap"]
    if year_col and year_col in df.columns:
        years = pd.to_numeric(df[year_col], errors="coerce")
        uniq = np.sort(years.dropna().unique())
        if len(uniq) >= 2:
            cut = uniq[max(1, int(np.floor(0.8*len(uniq))))]
            tr = np.flatnonzero(years.to_numpy() < cut)
            te = np.flatnonzero(years.to_numpy() >= cut)
            if len(tr) and len(te) and len(np.unique(y[tr])) == 2 and len(np.unique(y[te])) == 2:
                m = model().fit(X.iloc[tr], y[tr])
                pt = m.predict_proba(X.iloc[te])[:, 1]
                r = metric_row("temporal_latest_20pct_years", y[te], pt, synthetic, len(tr), len(te))
                r["temporal_cutoff_year"] = int(cut)
                metrics.append(r)
            else:
                metrics.append({"evaluation":"temporal_latest_20pct_years","synthetic":bool(synthetic),
                    "status":"not scored: train or test period lacks both classes"})
    pd.DataFrame(metrics).to_csv(out/"validation_metrics.csv", index=False)
    delta = {"paired_auc_drop_random_minus_spatial_95ci": boot_ci["random_minus_spatial_auc"],
             "paired_average_precision_drop_random_minus_spatial_95ci": boot_ci["random_minus_spatial_ap"],
             "valid_spatial_block_bootstrap_draws": valid_boots,
             "bootstrap_unit":"whole spatial blocks, sampled with replacement",
             "interpretation":"Uncertainty interval for this prepared dataset and split scheme; not a guarantee of future skill."}
    (out/"random_vs_spatial_cluster_bootstrap.json").write_text(json.dumps(delta, indent=2)+"\n")

    # Blocked permutation preserves each spatial block's event prevalence, then
    # tests whether spatially held-out predictors add discrimination beyond it.
    rng = np.random.default_rng(4421)
    observed_auc = roc_auc_score(y, ps)
    null = []
    for _ in range(permutations):
        yp = y.copy()
        for g in np.unique(groups):
            idx = np.flatnonzero(groups == g)
            yp[idx] = rng.permutation(yp[idx])
        pp = predict_spatial(X, yp, groups)
        if len(np.unique(yp)) == 2: null.append(float(roc_auc_score(yp, pp)))
    pval = (1 + sum(v >= observed_auc for v in null))/(1 + len(null))
    perm = {"synthetic":bool(synthetic), "observed_spatial_cv_auc":float(observed_auc),
            "permutations_requested":int(permutations), "valid_permutations":len(null),
            "upper_tail_permutation_p":float(pval), "null_auc_mean":float(np.mean(null)) if null else None,
            "null_auc_95pct":[float(x) for x in np.quantile(null,[.025,.975])] if null else None,
            "label_permutation":"within-spatial-block shuffle preserving each block's event count; spatial group-fold CV repeated for each shuffle",
            "warning":"Conditional association diagnostic only; it does not establish causality or operational skill, and its result depends on block definition."}
    (out/"permutation_test.json").write_text(json.dumps(perm, indent=2)+"\n")
    return metrics, delta, perm


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--data", help="Prepared CSV; no labels or absences are generated.")
    mode.add_argument("--synthetic-demo", action="store_true", help="Explicitly generate labelled synthetic data to test code only.")
    ap.add_argument("--out", default="validation_outputs")
    ap.add_argument("--label", default="y"); ap.add_argument("--features", default="rain_feature,slope_feature,access_feature")
    ap.add_argument("--spatial-block", default="spatial_block"); ap.add_argument("--year", default="year")
    ap.add_argument("--permutations", type=int, default=49)
    ap.add_argument("--synthetic-n", type=int, default=6000)
    args=ap.parse_args()
    synthetic=bool(args.synthetic_demo)
    df=make_synthetic(args.synthetic_n) if synthetic else pd.read_csv(args.data)
    metrics, delta, perm=run(df,args.label,[s.strip() for s in args.features.split(",") if s.strip()],
                             args.spatial_block,args.year,args.out,args.permutations,synthetic)
    print(json.dumps({"synthetic":synthetic,"output":str(Path(args.out).resolve()),
                      "metrics":metrics,"paired_delta_ci":delta,"permutation":perm},indent=2))

if __name__=="__main__": main()
