#!/usr/bin/env python3
"""SYNTHETIC ONLY: sample-size sensitivity for an ID curve and logistic AUC.

No Rwanda observations, rainfall records, predictors or fitted model results are
used. The rainfall component fits a simple log-log intensity-duration curve to
synthetic event windows and bootstraps its implied 24-hour intensity. This is an
illustration of parameter uncertainty, NOT an operational warning threshold:
there are no synthetic non-event rainfall opportunities in that component, and
it does not estimate false-alarm rate, lead time or event probability. The
logistic component is a separate balanced synthetic case-control simulation.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split


def synthetic_id_threshold(n, rng, bootstrap_draws):
    """Fit log(I)=a+b*log(D), then bootstrap I at D=24 h from event-only data."""
    duration_h = np.exp(rng.uniform(np.log(1.0), np.log(72.0), n))
    intensity_mm_h = 60.0 * duration_h**(-0.35) * np.exp(rng.normal(0.0, 0.25, n))
    x = np.log(duration_h)
    y = np.log(intensity_mm_h)
    xbar, ybar = x.mean(), y.mean()
    slope = np.sum((x-xbar)*(y-ybar)) / np.sum((x-xbar)**2)
    intercept = ybar - slope*xbar
    xref = np.log(24.0)
    estimate = float(np.exp(intercept + slope*xref))

    ix = rng.integers(0, n, size=(bootstrap_draws, n))
    xb = x[ix]
    yb = y[ix]
    xm = xb.mean(axis=1)
    ym = yb.mean(axis=1)
    denom = np.sum((xb-xm[:, None])**2, axis=1)
    numer = np.sum((xb-xm[:, None])*(yb-ym[:, None]), axis=1)
    slopes = np.divide(numer, denom, out=np.full_like(numer, np.nan), where=denom > 0)
    intercepts = ym - slopes*xm
    fitted_i24 = np.exp(intercepts + slopes*xref)
    lo, hi = np.nanquantile(fitted_i24, [0.025, 0.975])
    return estimate, float(lo), float(hi), float(hi-lo)


def logistic_once(n_per_class, rng):
    # Synthetic fixed-separation process: two predictors, balanced labels.
    x0 = rng.normal(loc=[0.0, 0.0], scale=[1.0, 1.0], size=(n_per_class, 2))
    x1 = rng.normal(loc=[0.9, 0.65], scale=[1.0, 1.0], size=(n_per_class, 2))
    X = np.vstack([x0, x1])
    y = np.r_[np.zeros(n_per_class, dtype=int), np.ones(n_per_class, dtype=int)]
    tr, te = train_test_split(np.arange(len(y)), test_size=.30, stratify=y,
                              random_state=int(rng.integers(1, 2**31-1)))
    m = LogisticRegression(max_iter=1000, C=1.0).fit(X[tr], y[tr])
    p = m.predict_proba(X[te])[:, 1]
    return float(roc_auc_score(y[te], p))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', default='synthetic_outputs')
    ap.add_argument('--sizes', default='20,50,100,300,1000')
    ap.add_argument('--replicates', type=int, default=250)
    ap.add_argument('--bootstrap', type=int, default=500)
    ap.add_argument('--seed', type=int, default=20261018)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    rows = []
    for n in [int(x) for x in a.sizes.split(',')]:
        widths, estimates, lows, highs, aucs = [], [], [], [], []
        for _ in range(a.replicates):
            est, lo, hi, width = synthetic_id_threshold(n, rng, a.bootstrap)
            estimates.append(est)
            lows.append(lo)
            highs.append(hi)
            widths.append(width)
            aucs.append(logistic_once(n, rng))
        rows.append({
          'synthetic': 'YES - no Rwanda observations used',
          'synthetic_event_count_per_id_curve': n,
          'synthetic_logistic_events_per_class_case_control': n,
          'total_synthetic_logistic_rows': 2*n,
          'synthetic_id_i24_median_mm_per_h': float(np.median(estimates)),
          'synthetic_id_i24_bootstrap_ci_low_median_mm_per_h': float(np.median(lows)),
          'synthetic_id_i24_bootstrap_ci_high_median_mm_per_h': float(np.median(highs)),
          'synthetic_id_i24_bootstrap_ci_width_median_mm_per_h': float(np.median(widths)),
          'synthetic_id_i24_bootstrap_ci_width_p05_mm_per_h': float(np.quantile(widths, .05)),
          'synthetic_id_i24_bootstrap_ci_width_p95_mm_per_h': float(np.quantile(widths, .95)),
          'heldout_logistic_auc_median': float(np.median(aucs)),
          'heldout_logistic_auc_simulation_p025': float(np.quantile(aucs, .025)),
          'heldout_logistic_auc_simulation_p975': float(np.quantile(aucs, .975)),
          'replicates': a.replicates, 'bootstrap_draws_per_replicate': a.bootstrap,
          'seed': a.seed,
        })
    df = pd.DataFrame(rows)
    df.to_csv(out/'synthetic_sample_size_results.csv', index=False)
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.5))
    x = df['synthetic_event_count_per_id_curve'].to_numpy()
    axs[0].plot(x, df['synthetic_id_i24_bootstrap_ci_width_median_mm_per_h'], 'o-', color='#147d92')
    axs[0].fill_between(x, df['synthetic_id_i24_bootstrap_ci_width_p05_mm_per_h'],
                        df['synthetic_id_i24_bootstrap_ci_width_p95_mm_per_h'], alpha=.2, color='#147d92')
    axs[0].set_xscale('log')
    axs[0].set_xlabel('Synthetic event count, n')
    axs[0].set_ylabel('Median bootstrap 95% CI width for I at 24 h (mm/h)')
    axs[0].set_title('SYNTHETIC: intensity-duration curve uncertainty')
    axs[1].errorbar(x, df['heldout_logistic_auc_median'],
      yerr=[df['heldout_logistic_auc_median']-df['heldout_logistic_auc_simulation_p025'],
            df['heldout_logistic_auc_simulation_p975']-df['heldout_logistic_auc_median']],
      fmt='o-', capsize=4, color='#bd5c26')
    axs[1].set_xscale('log')
    axs[1].set_ylim(.45, 1.0)
    axs[1].set_xlabel('Synthetic events per class (balanced 1:1 case-control)')
    axs[1].set_ylabel('Held-out ROC AUC')
    axs[1].set_title('SYNTHETIC: AUC varies less as n grows')
    for ax in axs:
        ax.grid(alpha=.25)
    fig.suptitle('SYNTHETIC DEMONSTRATION — not Rwanda data or operational skill', fontsize=12)
    fig.tight_layout()
    fig.savefig(out/'synthetic_sample_size_demo.png', dpi=180, bbox_inches='tight')
    (out/'SYNTHETIC_NOTICE.txt').write_text(
      'SYNTHETIC ONLY. No Rwanda observations, rainfall series, terrain labels, or model estimates are used.\n'
      'The rainfall curve is a fitted log-log intensity-duration relationship from synthetic event windows only; I at 24 h is a curve value, not a warning threshold. No non-event rain windows are simulated, so false alarms and event probability cannot be estimated.\n'
      'The logistic data are balanced case-control samples from a fixed two-feature process. The AUC range is the 2.5th–97.5th percentile across independent synthetic train/test replications, not a confidence interval for any real model.\n'
      'Use only to demonstrate sampling variability and test the code path.\n', encoding='utf-8')
    print(df.to_string(index=False))
    print(f'Wrote synthetic-only outputs to {out.resolve()}')

if __name__ == '__main__':
    main()
