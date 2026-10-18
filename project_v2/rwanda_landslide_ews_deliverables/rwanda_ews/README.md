# Rwanda landslide inventory readiness baseline

This is a reproducible audit of the public v2 `events.csv` and `sites.csv` tables. It does not alter the source CSVs and does not invent rainfall, terrain, soil-moisture, or land-cover values. The checked copies are included here; the original repository remains the source of record.

## Run

Install Python 3 with `pandas`, `numpy`, `matplotlib`, and `scikit-learn`, then run:

```bash
python3 readiness_baseline.py --events events.csv --sites sites.csv --out outputs
```

The script writes `readiness_table.csv`, annual/monthly count tables, repeated-day review flags, two figures, a calendar-month bootstrap summary, and a `dummy_validation_status.json`. The bootstrap resamples only actual day-precision event records and estimates uncertainty in the observed March–May calendar-month share. It is not a rainfall threshold estimate, a prospective hazard model, or an ML performance result.

## Optional model-data scaffold

No model is run unless a user supplies `rainfall_terrain_model_data.csv` (or a path passed using `--model-data`). It must contain `y` (a defensible binary label), `event_date`, `spatial_block`, and genuine predictor columns. Do not treat unreported locations or times as true absences. The optional scaffold performs a latest-date holdout, grouped spatial folds, rare-event metrics and an exploratory label permutation diagnostic. Its output is not a substitute for a pre-registered, externally/temporally tested EWS evaluation. The current inventory contains no measured environmental predictors and no true negatives, so the default run correctly reports no model performance.

## Key interpretation

Rows are reported event claims, not an exhaustive sample. Multiple site rows can refer to one event; the 2018 set has 494 mixed landslide/flash-flood polygons and their 494 derived centroids. Neither these centroids nor AOI centers are observed scar locations. Blank spatial accuracy is unknown, not zero. Repeated dates are review flags and should not be merged automatically. Spatial and temporal effective sample sizes cannot be inferred reliably from this inventory alone because event reporting is biased and the observation process is unknown.

## Inputs

`events.csv` and `sites.csv` are downloaded unchanged from the repository's v2 read-only directory. See the linked source's `DATA_DICTIONARY.md` and `QA_REPORT.md` for definitions and QA caveats.
