#!/usr/bin/env python3
"""Reproducible inventory readiness and validation scaffold for Rwanda landslides.

No rainfall, soil-moisture, terrain, or land-cover values are synthesized. The
bootstrap below describes uncertainty in the observed day-date calendar-month
mix only; it is not a rainfall-threshold fit or a hazard forecast.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, brier_score_loss,
    confusion_matrix, roc_auc_score)

RAIN = {'rainfall', 'prolonged rainfall'}

def readiness(events_path: Path, sites_path: Path):
    e = pd.read_csv(events_path).fillna('')
    s = pd.read_csv(sites_path).fillna('')
    e['date_start_dt'] = pd.to_datetime(e.date_start, errors='coerce')
    day = e.date_precision.eq('day')
    has_district = e.districts.astype(str).str.strip().ne('')
    one_district = pd.to_numeric(e.n_districts, errors='coerce').eq(1)
    site_link = e.event_id.isin(set(s.event_id))
    rain_trigger = e.primary_trigger.isin(RAIN)
    counts = [
      ('All curated event rows', len(e), 'Rows are reported episodes/claims; not exhaustive occurrences.'),
      ('Day precision', int(day.sum()), 'Necessary for event-day rainfall matching.'),
      ('Day + named district', int((day & has_district).sum()), 'Any nonblank normalized district.'),
      ('Day + exactly one district', int((day & one_district).sum()), 'Stricter district-level matching; multi-district events excluded.'),
      ('Day + one district + linked site', int((day & one_district & site_link).sum()), 'Site link does not guarantee fine spatial accuracy.'),
      ('Day + one district + rain/prolonged-rain trigger', int((day & one_district & rain_trigger).sum()), 'Trigger classification is not independent rainfall measurement.'),
      ('Day + one district + linked site + rain trigger', int((day & one_district & site_link & rain_trigger).sum()), 'Conservative potential event pool; still no measured rain predictor or true negatives.'),
      ('Unique event dates among day + named district', int(e.loc[day & has_district, 'date_start'].nunique()), 'Same-date records may be distinct events or duplicate claims.'),
      ('Site rows (all)', len(s), 'Includes polygons, polygon centroids and contextual AOI centers.'),
      ('Point site rows', int(s.geometry_type.eq('point').sum()), 'Point role only.'),
      ('Point rows with accuracy <= 1 km', int((s.geometry_type.eq('point') & pd.to_numeric(s.accuracy_m, errors='coerce').le(1000)).sum()), 'No such stated-accuracy point in this CSV.'),
      ('Point rows with accuracy unstated', int((s.geometry_type.eq('point') & s.accuracy_m.astype(str).str.strip().eq('')).sum()), 'Unknown must not be treated as zero error.'),
      ('Polygon centroid rows', int(s.geometry_type.eq('centroid_of_polygon').sum()), 'Derived from mixed-hazard polygons; not observed landslide scar centroids.'),
      ('Polygon rows', int(s.geometry_type.eq('polygon').sum()), 'Feature class is mixed/uncertain per QA; no valid 30 m point-label assumption.'),
      ('AOI centers', int(s.geometry_type.eq('aoi_center').sum()), 'Contextual assessment centers, not landslide occurrences.'),
    ]
    table = pd.DataFrame(counts, columns=['measure','count','interpretation'])
    e['year'] = e.date_start_dt.dt.year
    e['month'] = e.date_start_dt.dt.month
    years = e.groupby('year', dropna=False).size().rename('event_rows').reset_index()
    months = e.groupby('month', dropna=False).size().rename('event_rows').reset_index()
    dates = e.loc[day].groupby('date_start').size().rename('records_same_day').reset_index()
    repeated = dates[dates.records_same_day.gt(1)].copy()
    # The date is a flag for review, never an automatic merge criterion.
    return e, s, table, years, months, repeated

def wilson(k, n, z=1.96):
    if n <= 0: return (np.nan, np.nan)
    p=k/n; den=1+z*z/n
    mid=(p+z*z/(2*n))/den
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return mid-half, mid+half

def calendar_bootstrap(e, n_boot=5000, seed=20261018):
    """Resample actual day-precision events; quantify MAM share, not a model."""
    x=e.loc[e.date_precision.eq('day')].copy()
    months=pd.to_datetime(x.date_start, errors='coerce').dt.month.to_numpy()
    months=months[np.isfinite(months)]
    if not len(months): return {'n':0,'observed_mam_share':None,'bootstrap_ci_95':[None,None]}
    observed=float(np.isin(months,[3,4,5]).mean())
    rng=np.random.default_rng(seed)
    reps=np.empty(n_boot)
    for i in range(n_boot):
        sample=rng.choice(months, size=len(months), replace=True)
        reps[i]=np.isin(sample,[3,4,5]).mean()
    return {'n':len(months),'observed_mam_share':observed,
      'bootstrap_ci_95':[float(np.quantile(reps,.025)),float(np.quantile(reps,.975))],
      'warning':'Calendar-season descriptive bootstrap only; not rainfall-threshold or susceptibility-model stability.'}

def plot_counts(years, months, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    y=years.dropna().copy(); y['year']=y.year.astype(int)
    fig, ax=plt.subplots(figsize=(10,4)); ax.bar(y.year,y.event_rows,color='#4878a8')
    ax.set(xlabel='Year of date_start',ylabel='Curated event rows',title='Rwanda inventory records by start year (reporting count, not incidence)')
    fig.tight_layout(); fig.savefig(outdir/'events_by_year.png',dpi=180); plt.close(fig)
    m=months.dropna().copy(); m['month']=m.month.astype(int)
    fig, ax=plt.subplots(figsize=(8,4)); ax.bar(m.month,m.event_rows,color='#e1812c')
    ax.set(xticks=range(1,13),xlabel='Month of date_start',ylabel='Curated event rows',title='Records by start month (mixed date precision)')
    fig.tight_layout(); fig.savefig(outdir/'events_by_month.png',dpi=180); plt.close(fig)

def rare_event_metrics(y_true, prob, threshold=.5):
    y=np.asarray(y_true,dtype=int); p=np.asarray(prob,dtype=float); pred=p>=threshold
    tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    pod=tp/(tp+fn) if tp+fn else np.nan
    far=fp/(tp+fp) if tp+fp else np.nan
    csi=tp/(tp+fp+fn) if tp+fp+fn else np.nan
    specificity=tn/(tn+fp) if tn+fp else np.nan
    tss=pod+specificity-1 if np.isfinite(pod) and np.isfinite(specificity) else np.nan
    return {'n':len(y),'events':int(y.sum()),'POD':pod,'FAR':far,'CSI':csi,'TSS':tss,
      'Brier':brier_score_loss(y,p) if len(y) else np.nan,
      'PR_AUC':average_precision_score(y,p) if len(np.unique(y))>1 else np.nan,
      'ROC_AUC':roc_auc_score(y,p) if len(np.unique(y))>1 else np.nan}

def dummy_validation_workflow(data_csv: Path, outdir: Path):
    """Strictly optional scaffold. Requires user-supplied real predictors and labels.

    CSV contract: y (0/1), event_date (ISO), spatial_block (district or larger
    block), and predictor columns. This does not make pseudo-absences valid.
    """
    path=outdir/'dummy_validation_status.json'
    if not data_csv.exists():
        path.write_text(json.dumps({'status':'NOT RUN','reason':'No rainfall/terrain predictor dataset was supplied; no model or performance results fabricated.','required_columns':['y','event_date','spatial_block','one or more real predictor columns'],'workflow':'Time holdout and spatial grouped CV scaffold described in README.'},indent=2))
        return
    d=pd.read_csv(data_csv)
    required={'y','event_date','spatial_block'}
    if not required.issubset(d.columns): raise ValueError(f'Missing required columns: {sorted(required-set(d.columns))}')
    d['event_date']=pd.to_datetime(d.event_date,errors='raise')
    pred_cols=[c for c in d.columns if c not in required]
    if not pred_cols: raise ValueError('No predictor columns supplied.')
    if d[pred_cols].isna().any().any(): raise ValueError('Handle missing predictors explicitly before validation.')
    # Reserve latest 20% of dates as temporal test; event groups must not leak.
    cutoff=d.event_date.quantile(.8)
    train=d[d.event_date<cutoff]; test=d[d.event_date>=cutoff]
    if train.y.nunique()<2 or test.y.nunique()<2:
        path.write_text(json.dumps({'status':'NOT EVALUABLE','reason':'Temporal split lacks both classes in train or test.','cutoff':str(cutoff),'n_train':len(train),'n_test':len(test)},indent=2)); return
    model=LogisticRegression(C=.1,max_iter=2000,class_weight='balanced')
    model.fit(train[pred_cols],train.y.astype(int)); p=model.predict_proba(test[pred_cols])[:,1]
    result={'status':'USER DATA MODEL RUN','cutoff':str(cutoff),'temporal_metrics':rare_event_metrics(test.y,p),
      'warning':'Temporal holdout only; no probability/alert claim without calibration, spatial tests, valid absences, benchmark and prospective verification.'}
    # Spatial grouped CV placeholder/results only if at least 3 groups, and train/test grouped folds.
    groups=d.spatial_block.astype(str)
    if groups.nunique()>=3:
        gkf=GroupKFold(n_splits=min(5,groups.nunique())); fold=[]
        for tr,te in gkf.split(d[pred_cols],d.y,groups):
            if d.iloc[tr].y.nunique()<2 or d.iloc[te].y.nunique()<2: continue
            m=LogisticRegression(C=.1,max_iter=2000,class_weight='balanced')
            m.fit(d.iloc[tr][pred_cols],d.iloc[tr].y.astype(int))
            fold.append(rare_event_metrics(d.iloc[te].y,m.predict_proba(d.iloc[te][pred_cols])[:,1]))
        result['spatial_group_cv_fold_metrics']=fold
    # Permutation test: shuffle labels within temporal training set only; diagnostic of a fixed split.
    rng=np.random.default_rng(20261018); observed=result['temporal_metrics'].get('PR_AUC')
    null=[]
    if observed is not None and np.isfinite(observed):
        for _ in range(199):
            yp=rng.permutation(train.y.to_numpy(dtype=int))
            if len(np.unique(yp))<2: continue
            m=LogisticRegression(C=.1,max_iter=2000,class_weight='balanced').fit(train[pred_cols],yp)
            null.append(average_precision_score(test.y.astype(int),m.predict_proba(test[pred_cols])[:,1]))
        result['permutation_test']={'n':len(null),'null_PR_AUC_quantile_95':float(np.quantile(null,.95)) if null else None,'interpretation':'Exploratory label-shuffle diagnostic, not proof of external validity.'}
    path.write_text(json.dumps(result,indent=2,default=float))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--events',type=Path,default=Path(__file__).with_name('events.csv'))
    ap.add_argument('--sites',type=Path,default=Path(__file__).with_name('sites.csv'))
    ap.add_argument('--out',type=Path,default=Path(__file__).with_name('outputs'))
    ap.add_argument('--model-data',type=Path,default=Path('rainfall_terrain_model_data.csv'))
    args=ap.parse_args(); args.out.mkdir(parents=True,exist_ok=True)
    e,s,table,years,months,repeated=readiness(args.events,args.sites)
    table.to_csv(args.out/'readiness_table.csv',index=False)
    years.to_csv(args.out/'events_by_year.csv',index=False); months.to_csv(args.out/'events_by_month.csv',index=False)
    repeated.to_csv(args.out/'same_day_review_flags.csv',index=False)
    boot=calendar_bootstrap(e)
    (args.out/'calendar_bootstrap.json').write_text(json.dumps(boot,indent=2))
    plot_counts(years,months,args.out)
    dummy_validation_workflow(args.model_data,args.out)
    print(table.to_string(index=False)); print('\nCalendar-only bootstrap:',json.dumps(boot))
    print(f'Outputs written to {args.out}')
if __name__=='__main__': main()
