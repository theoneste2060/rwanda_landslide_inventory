#!/usr/bin/env python3
"""Reproducibly transform the read-only source inventory into Rwanda landslide v2.

Run from any working directory: python3 scripts/build_v2.py
Inputs in this folder are snapshots; source material is never edited.
"""
from __future__ import annotations
import csv, hashlib, json, math, re, shutil, tempfile, zipfile, warnings
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window
from shapely.geometry import Point, mapping, shape, GeometryCollection
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw_sources"
OUT = ROOT
INPUT = ROOT / "source_original_inventory_readonly.csv"
LOG_INPUT = ROOT / "source_log_original_readonly.csv"
EVENT_FIELDS = ["event_id","date_start","date_end","date_precision","event_name","provinces","districts","n_districts","primary_trigger","landslide_type","fatalities_min","fatalities_max","fatalities_note","injuries_min","injuries_max","people_affected","people_displaced","houses_destroyed","houses_damaged","infrastructure_notes","event_confidence","confidence_rationale","source_ids","notes"]
SITE_FIELDS = ["site_id","event_id","sector","cell","village","place_description","latitude","longitude","geometry_type","location_quality","accuracy_m","coordinate_method","source_crs","district_check","slope_check","source_id"]
SOURCE_FIELDS = ["source_id","title","publisher","date","url","access_date","license","access_status","what_was_extracted"]
VALID_TYPES = {"shallow landslide","debris flow","mudslide","rockfall","rotational/translational slide","landslide cluster","slope failure (mining/road/construction)","mixed landslide-flood","unknown"}
VALID_TRIGGERS = {"rainfall","prolonged rainfall","earthquake","mining/quarrying","construction/road cut","flood-related","unknown"}
URL_RE = re.compile(r"https?://[^\s<>\]\[\)\}\,;]+", re.I)
KNOWN_URLS = {
 "https://data.nasa.gov/dataset/global-landslide-catalog-export": ("NASA Global Landslide Catalog Export","NASA","2026"),
 "https://data.humdata.org/dataset/cod-ab-rwa": ("Rwanda Subnational Administrative Boundaries (COD-AB)","OCHA/HDX; source NISR","2025"),
}


def raw_events():
    with INPUT.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, strict=True))
    if len(rows) != 30:
        raise ValueError(f"Expected 30 original rows, got {len(rows)}")
    return rows


def clean_url(u):
    return u.rstrip(".,;:)\"'\u00bb")


def urls_in(text):
    return [clean_url(x) for x in URL_RE.findall(str(text or ""))]


def source_id(url):
    return "SRC-" + hashlib.sha256(url.encode("utf-8")).hexdigest()[:12].upper()


def parse_date(value):
    s = str(value or "").strip()
    if not s:
        return "", "", "year"
    if re.fullmatch(r"\d{4}", s):
        y = int(s); return f"{y:04d}-01-01", f"{y:04d}-12-31", "year"
    if re.fullmatch(r"\d{4}-\d{2}", s):
        y,m = map(int,s.split("-")); last=(pd.Period(f"{y:04d}-{m:02d}",freq="M").days_in_month)
        return f"{y:04d}-{m:02d}-01", f"{y:04d}-{m:02d}-{last:02d}", "month"
    if "/" in s:
        left,right=s.split("/",1)
        m=re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})",left)
        if m:
            y,mo,d=map(int,m.groups())
            if re.fullmatch(r"\d{2}",right): right=f"{y:04d}-{mo:02d}-{right}"
            elif re.fullmatch(r"\d{4}-\d{2}-\d{2}",right): pass
            elif re.fullmatch(r"\d{2}-\d{2}",right): right=f"{y:04d}-{right}"
            else: raise ValueError(f"Cannot parse date range {s}")
            start=datetime.strptime(left,"%Y-%m-%d").date(); end=datetime.strptime(right,"%Y-%m-%d").date()
            if end<start: raise ValueError(f"Date range reversed: {s}")
            return start.isoformat(),end.isoformat(),"range"
    try:
        dt=datetime.strptime(s,"%Y-%m-%d").date();return dt.isoformat(),"","day"
    except ValueError as e: raise ValueError(f"Cannot parse date {s!r}") from e


def norm_enum(row):
    typ=" ".join(str(row.get("landslide_type","")).lower().replace("/"," ").split())
    trigger=" ".join(str(row.get("trigger","")).lower().split())
    if any(w in typ for w in ["mining","quarry","road","construction"]): lt="slope failure (mining/road/construction)"
    elif "rockfall" in typ or "rock fall" in typ: lt="rockfall"
    elif "debris flow" in typ: lt="debris flow"
    elif "2023" in row.get("date","") or ("flood" in trigger and ("landslide" in typ or "mudslide" in typ)): lt="mixed landslide-flood"
    elif "cluster" in typ or ("landslide" in typ and ";" in row.get("district", "")): lt="landslide cluster"
    elif "mudslide" in typ: lt="mudslide"
    elif "translational" in typ or "rotational" in typ: lt="rotational/translational slide"
    elif "landslide" in typ or "slide" in typ: lt="unknown"
    else: lt="unknown"
    if "earthquake" in trigger: tr="earthquake"
    elif "mining" in trigger or "quarry" in trigger or "cliff destabilization" in trigger: tr="mining/quarrying"
    elif "construction" in trigger or "road cut" in trigger: tr="construction/road cut"
    elif "prolonged" in trigger or "waterlogged" in trigger: tr="prolonged rainfall"
    elif "rain" in trigger or "downpour" in trigger or "torrential" in trigger: tr="rainfall"
    elif "flood" in trigger or "overflow" in trigger: tr="flood-related"
    else: tr="unknown"
    assert lt in VALID_TYPES and tr in VALID_TRIGGERS
    return lt,tr


def parse_range(s, exclude_unattributed=False):
    s=str(s or "").strip()
    if not s: return "", ""
    if exclude_unattributed and any(t in s.lower() for t in ["not landslide-attributed","not attributed"]): return "", ""
    if re.search(r"\b0 recorded\b",s.lower()): return "0","0"
    m=re.search(r"(?<!\d)(\d[\d,]*)\s*[–—-]\s*(\d[\d,]*)",s)
    if m: return m.group(1).replace(",",""),m.group(2).replace(",","")
    nums=re.findall(r"(?<!\d)(\d[\d,]*)(?!\d)",s)
    if not nums:return "",""
    # Repeated reporting updates are bounds, never averaged.
    if any(x in s.lower() for x in ["initial", "later", "assessment", "contemporaneous", "totals differ"]):
        vals=[int(x.replace(",","")) for x in nums[:5]]
        return str(min(vals)),str(max(vals))
    return nums[0].replace(",",""),nums[0].replace(",","")


def numeric_count(text, patterns):
    s=str(text or "")
    for pat in patterns:
        m=re.search(pat,s,re.I)
        if m:return str(int(m.group(1).replace(",","")))
    return ""


def stable_names(value):
    return [x.strip() for x in str(value or "").split(";") if x.strip() and "plus other" not in x.lower()]


def load_sources(rows):
    src={}
    try: log=pd.read_csv(LOG_INPUT,dtype=str,keep_default_na=False)
    except Exception: log=pd.DataFrame()
    byurl={}
    for _,r in log.iterrows():
        url=clean_url(r.get("url",""))
        if url.startswith("http"):
            byurl[url]=r.to_dict()
            sid=source_id(url)
            src.setdefault(sid,{"source_id":sid,"title":r.get("title","") or urlparse(url).netloc,"publisher":r.get("publisher",""),"date":r.get("source_date_or_version",""),"url":url,"access_date":r.get("access_date","2026-10-16"),"license":r.get("license","") or "Not stated in retrieved metadata; consult source terms","access_status":r.get("access_status","") or "Consulted; outcome recorded in source log","what_was_extracted":r.get("what_was_searched_or_extracted","")})
    for row in rows:
        for key in ["source_1 (title, publisher, date, URL)","source_2","source_3"]:
            for url in urls_in(row.get(key,"")):
                meta=byurl.get(url,{})
                sid=source_id(url)
                if sid not in src:
                    title=meta.get("title","") or KNOWN_URLS.get(url,(urlparse(url).netloc,urlparse(url).netloc,""))[0]
                    pub=meta.get("publisher","") or KNOWN_URLS.get(url, ("",urlparse(url).netloc,""))[1]
                    src[sid]={"source_id":sid,"title":title,"publisher":pub,"date":meta.get("source_date_or_version","") or KNOWN_URLS.get(url,("","",""))[2],"url":url,"access_date":"2026-10-16","license":meta.get("license","") or "Not stated in retrieved metadata; consult source terms","access_status":meta.get("access_status","") or "URL cited in source inventory; access not independently rechecked in v2 build","what_was_extracted":meta.get("what_was_searched_or_extracted","") or "Cited for date, location, event type or impact as noted in linked event row."}
    # Explicit sources used for corrected values, admin QA and DEM.
    explicit=[
      ("https://reliefweb.int/report/rwanda/rwanda-rubavu-landslide-dref-operation-n%C2%B0-mdrrw006-final-report","Rwanda: Rubavu Landslide DREF operation n° MDRRW006 Final Report","IFRC","2010-11-22","IFRC report confirms the 26 March 2010 Mt Rubavu landslide, 14 deaths, 5,920 people made homeless in two Rubavu cells, and road/latrine/water-well damage; no destroyed-house count is stated.","IFRC web report; no separate dataset license located"),
      ("https://data.humdata.org/dataset/cod-ab-rwa","Rwanda - Subnational Administrative Boundaries (COD-AB)","OCHA/HDX; source NISR","2018 package","ADM2/ADM3 polygons used for point-in-polygon checks and basemap; boundary establishment date unknown; metadata says not reviewed in preceding 12 months.","CC BY-IGO"),
      ("https://spacedata.copernicus.eu/collections/copernicus-digital-elevation-model","Copernicus DEM GLO-30","Copernicus Data Space Ecosystem","GLO-30","Used for point-scale slope screening; slopes are not slide-scar validation and broad catalogue points are not terrain-site evidence.","Provider access/licensing terms; see source"),
      ("https://copernicus-dem-30m.s3.amazonaws.com/","Copernicus DEM GLO-30 public COG tiles","Copernicus DEM public AWS S3 mirror","Accessed 2026-10-16","GLO-30 COG tiles downloaded for Rwanda source points; tile hashes retained in QA_REPORT.md.","Copernicus DEM terms; see provider"),
      ("https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export/Global_Landslide_Catalog_Export_rows.csv","NASA Global Landslide Catalog Export CSV","NASA","Snapshot current to 2016-03-07","Full export downloaded; six Rwanda rows reconciled. NASA states this is a one-time legacy snapshot, not a current complete COOLR export.","NASA portal says license not specified; portal Terms and Conditions apply"),
      ("https://doi.org/10.5281/zenodo.7198322","Deijns et al. NHESS geomorphic-hazard event inventories (Rwanda component)","Zenodo / Deijns et al.","2022-10-14","Rwanda shapefile has 494 features in WGS 84 / UTM zone 35S; source inventory combines landslides and flash floods and does not include a feature-level hazard-class field.","CC BY 4.0")]
    for url,title,pub,dt,what,license in explicit:
        sid=source_id(url); src[sid]={"source_id":sid,"title":title,"publisher":pub,"date":dt,"url":url,"access_date":"2026-10-16","license":license,"access_status":"opened/downloaded and used","what_was_extracted":what}
    # Sources from any additional candidates supplied after independent research.
    add_path=ROOT/"additional_event_candidates.json"
    if add_path.exists():
        adds=json.loads(add_path.read_text(encoding="utf-8")).get("candidate_events",[])
        for ev in adds:
            for u in ev.get("source_urls",[]):
                if u.startswith("http"):
                    sid=source_id(u)
                    src.setdefault(sid,{"source_id":sid,"title":ev.get("source_title",urlparse(u).netloc),"publisher":ev.get("publisher",urlparse(u).netloc),"date":ev.get("source_date",""),"url":u,"access_date":"2026-10-16","license":"Not stated; consult source terms","access_status":"opened and independently checked","what_was_extracted":"Dated event information in the linked v2 event row."})
    return src


def make_events(rows, sources, district_to_prov):
    byid={r["event_id"]:r for r in rows}
    excluded_sites={f"RWA-LS-{i:04d}" for i in range(23,29)}
    merged={"RWA-LS-0012":"RWA-LS-0011"}
    out=[]
    for row in rows:
        oldid=row["event_id"]
        if oldid in excluded_sites or oldid in merged: continue
        r=dict(row)
        # Repair the verified one-cell offset beginning at the infrastructure field.
        if oldid=="RWA-LS-0006":
            r["infrastructure_affected"]="houses destroyed; small roads, latrines and water wells damaged"
            r["confidence"]="High"
            r["source_1 (title, publisher, date, URL)"]="IFRC, Rwanda: Rubavu Landslide DREF Final Report, 2010, https://reliefweb.int/report/rwanda/rwanda-rubavu-landslide-dref-operation-n%C2%B0-mdrrw006-final-report"
            r["source_2"]="https://data.nasa.gov/dataset/global-landslide-catalog-export"
            r["source_3"]="HDX GLIDE Rwanda event table, 2010-03-26, https://data.humdata.org/dataset/100527e3-cd37-4248-8998-310d22325f5f/resource/306f434f-65b7-4f57-8690-f3e1023db32c/download/rwa_glide_events.csv"
            r["notes"]="IFRC report confirms 26 March 2010, Rubavu Sector and 14 deaths; it reports 5,920 people made homeless in two cells and damaged roads, latrines and water wells. No house count, injury count or slide-site coordinate is given. NASA reference coordinate is coarse and reused near the 2018 catalog point; suppressed from the mapped sites table. Original row values retained in source_original_inventory_readonly.csv."
            r["houses_destroyed/damaged"]=""
            r["people_displaced"]="5,920 people made homeless; 1,184 families"
        date_start,date_end,precision=parse_date(r["date"])
        if oldid=="RWA-LS-0011":
            other=byid["RWA-LS-0012"]
            # The two catalog entries share one event date and are one episode with districts not casualty allocations.
            dist=stable_names(r.get("district",""))+stable_names(other.get("district",""))
            r["district"]="; ".join(dict.fromkeys(dist))
            r["province"]="; ".join(dict.fromkeys(stable_names(r.get("province",""))+stable_names(other.get("province",""))))
        districts=stable_names(r.get("district",""))
        provinces=[]
        for d in districts:
            p=district_to_prov.get(d)
            if p:provinces.append(p)
        if not provinces: provinces=stable_names(r.get("province",""))
        provinces=list(dict.fromkeys(provinces)); districts=list(dict.fromkeys(districts))
        fatal_text=r.get("fatalities","")
        fmin,fmax=parse_range(fatal_text,exclude_unattributed=True)
        injmin,injmax=parse_range(r.get("injuries",""))
        other_id_note=""
        if oldid=="RWA-LS-0011": other_id_note="Merged source row RWA-LS-0012 (same 2016-05-07 rainfall episode); fatalities are episode totals, not district allocation."
        origvals=f"Original date={r.get('date')}; type={r.get('landslide_type')}; trigger={r.get('trigger')}; fatality_text={fatal_text}; injury_text={r.get('injuries')}; displaced_text={r.get('people_displaced')}; houses_text={r.get('houses_destroyed/damaged')}; district_text={r.get('district')}; province_text={r.get('province')}; date_precision_text={r.get('date_precision')}"
        note=" | ".join([x for x in [r.get("notes",""),other_id_note,origvals] if x])
        source_urls=[]
        for col in ["source_1 (title, publisher, date, URL)","source_2","source_3"]: source_urls += urls_in(r.get(col,""))
        source_ids=list(dict.fromkeys(source_id(u) for u in source_urls if source_id(u) in sources))
        if oldid in {"RWA-LS-0005","RWA-LS-0006","RWA-LS-0008","RWA-LS-0011","RWA-LS-0014"}:
            nasa_sid=source_id("https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export/Global_Landslide_Catalog_Export_rows.csv")
            if nasa_sid not in source_ids:source_ids.append(nasa_sid)
        if not source_ids: raise ValueError(f"No source IDs for {oldid}")
        if oldid=="RWA-LS-0006":
            people_displaced="5920"; people_affected=""; houses_destroyed=""; houses_damaged=""
            infra="Roads, latrines and water wells damaged; IFRC does not state a house count."
            name="2010 Rubavu landslide (Mt Rubavu)"
        else:
            disp=r.get("people_displaced","")
            people_displaced=numeric_count(disp,[r"([\d,]+)\s+displaced",r"([\d,]+)\s+(?:people\s+)?homeless",r"([\d,]+)\s+people\s+made homeless"])
            affected=numeric_count(disp,[r"([\d,]+)\s+affected"])
            # Affected is not the same as displaced; keep distinct values.
            people_affected=affected
            house_text=r.get("houses_destroyed/damaged","")
            exact_destroy=numeric_count(house_text,[r"(?<![+\d])([\d,]+)\s+(?:houses?|homes?)\s+destroyed\b"])
            exact_damaged=numeric_count(house_text,[r"(?<![+\d])([\d,]+)\s+(?:houses?|homes?)\s+(?:partly\s+)?damaged\b"])
            if not exact_damaged:
                m=re.search(r"([\d,]+)\s+(?:partly\s+)?damaged/flooded houses",house_text,re.I)
                if m: exact_damaged=m.group(1).replace(",","")
            # Retain ambiguous multi-report totals as narrative, not a false point estimate.
            if any(x in house_text.lower() for x in ["+ houses",">", "varies", "dozens", "several"]): exact_destroy=""
            houses_destroyed=exact_destroy; houses_damaged=exact_damaged
            infra=r.get("infrastructure_affected","")
            name=f"{date_start[:4]} {', '.join(districts) if districts else 'Rwanda'} landslide/flood episode"
            if oldid=="RWA-LS-0022":name="May 2023 Rwanda floods and landslides"
            if oldid=="RWA-LS-0016":name="May 2018 Karongi landslide cluster"
        lt,tr=norm_enum(r)
        if oldid=="RWA-LS-0016":lt="landslide cluster"
        if oldid=="RWA-LS-0022":lt="mixed landslide-flood"
        if oldid=="RWA-LS-0006":lt="mudslide";tr="prolonged rainfall"
        urls_order=[]
        for col in ["source_1 (title, publisher, date, URL)","source_2","source_3"]:
            for u in urls_in(r.get(col,"")):
                if u not in urls_order:urls_order.append(u)
        source_text="; ".join([r.get("source_1 (title, publisher, date, URL)",""),r.get("source_2",""),r.get("source_3","")])
        rationale=f"{r.get('confidence','Low')} in the event record based on the source citation(s); location precision is assessed separately."
        out.append({"event_id":oldid,"date_start":date_start,"date_end":date_end,"date_precision":precision,"event_name":name,"provinces":"|".join(provinces),"districts":"|".join(districts),"n_districts":len(districts),"primary_trigger":tr,"landslide_type":lt,"fatalities_min":fmin,"fatalities_max":fmax,"fatalities_note":fatal_text,"injuries_min":injmin,"injuries_max":injmax,"people_affected":people_affected,"people_displaced":people_displaced,"houses_destroyed":houses_destroyed,"houses_damaged":houses_damaged,"infrastructure_notes":infra,"event_confidence":r.get("confidence","Low"),"confidence_rationale":rationale,"source_ids":"|".join(source_ids),"notes":note})
    # Incorporate only vetted, independently sourced, deduplicated additions.
    addfile=ROOT/"additional_event_candidates.json"
    if addfile.exists():
        additions=json.loads(addfile.read_text(encoding="utf-8")).get("candidate_events",[])
        for c in additions:
            if not c.get("source_urls") or not all(u.startswith("http") for u in c["source_urls"]):raise ValueError("Added event lacks verifiable source URL")
            ds=c.get("date_start",""); de=c.get("date_end",""); pr=c.get("date_precision","")
            if not ds or pr not in {"day","month","year","range"}:raise ValueError("Bad added event date")
            lt=c.get("landslide_type","unknown");tr=c.get("primary_trigger","unknown")
            if lt not in VALID_TYPES or tr not in VALID_TRIGGERS:raise ValueError("Bad added-event controlled vocabulary")
            sidlist=[source_id(u) for u in c["source_urls"]]
            out.append({"event_id":c["event_id"],"date_start":ds,"date_end":de,"date_precision":pr,"event_name":c.get("event_name",""),"provinces":c.get("provinces",""),"districts":c.get("districts",""),"n_districts":int(c.get("n_districts",0)),"primary_trigger":tr,"landslide_type":lt,"fatalities_min":c.get("fatalities_min",""),"fatalities_max":c.get("fatalities_max",""),"fatalities_note":c.get("fatalities_note",""),"injuries_min":c.get("injuries_min",""),"injuries_max":c.get("injuries_max",""),"people_affected":c.get("people_affected",""),"people_displaced":c.get("people_displaced",""),"houses_destroyed":c.get("houses_destroyed",""),"houses_damaged":c.get("houses_damaged",""),"infrastructure_notes":c.get("infrastructure_notes",""),"event_confidence":c.get("event_confidence","Medium"),"confidence_rationale":c.get("confidence_rationale",""),"source_ids":"|".join(sidlist),"notes":c.get("notes","")})
    return out


def read_boundaries(tmp):
    z=RAW/"rwa_admin_boundaries.zip"
    if not z.exists(): raise FileNotFoundError(z)
    dest=tmp/"boundaries";dest.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(z) as arc: arc.extractall(dest)
    def find(level): return next(dest.rglob(f"*adm{level}*.shp"))
    a1=gpd.read_file(find(1));a2=gpd.read_file(find(2));a3=gpd.read_file(find(3))
    return a1.to_crs(4326),a2.to_crs(4326),a3.to_crs(4326)


def sample_slope(lat,lon):
    if lat is None or lon is None or (isinstance(lat,float) and np.isnan(lat)): return "not tested: no usable coordinate"
    files=sorted((RAW/"dem").glob("*.tif"))
    for f in files:
        with rasterio.open(f) as ds:
            if not (ds.bounds.left<=lon<=ds.bounds.right and ds.bounds.bottom<=lat<=ds.bounds.top):continue
            row,col=ds.index(lon,lat)
            if row<1 or col<1 or row>=ds.height-1 or col>=ds.width-1:continue
            arr=ds.read(1,window=Window(col-1,row-1,3,3),masked=True).astype("float64")
            if np.ma.getmaskarray(arr).any():return "no DEM value (masked / water)"
            z=arr.filled(np.nan)
            # Central difference; convert longitude degrees to ground metres at sample latitude.
            dxdeg=ds.res[0];dydeg=ds.res[1]
            dx=dxdeg*111320*math.cos(math.radians(lat));dy=dydeg*110574
            dzdx=(z[1,2]-z[1,0])/(2*dx);dzdy=(z[2,1]-z[0,1])/(2*dy)
            deg=math.degrees(math.atan(math.hypot(dzdx,dzdy)))
            tag="near-flat <3°" if deg<3 else "slope >=3°"
            return f"{deg:.2f} deg, {tag}; Copernicus GLO-30 3x3 central difference (screen only)"
    return "not tested: no downloaded DEM tile covers coordinate"


def sites_from_original(rows,events,sources,districts,sectors):
    eventids={r["event_id"] for r in events}; out=[]; geoms=[]
    event_by={e["event_id"]:e for e in events}
    # Event/catalog reference coordinates, excluding the reused 2010/2018 Rubavu point.
    for r in rows:
        old=r["event_id"]
        if old in {f"RWA-LS-{i:04d}" for i in range(23,29)} or old in {"RWA-LS-0006","RWA-LS-0014","RWA-LS-0008","RWA-LS-0011","RWA-LS-0012"}:continue
        try: lat=float(r.get("latitude", ""));lon=float(r.get("longitude",""))
        except:continue
        canonical={"RWA-LS-0012":"RWA-LS-0011"}.get(old,old)
        if canonical not in eventids:continue
        acc=r.get("coordinate_accuracy_estimate","")
        m=re.search(r"±\s*(\d+)\s*km",acc)
        accuracy=float(m.group(1))*1000 if m else None
        quality="approximate" if accuracy is not None and accuracy<=5000 else "coarse"
        pt=Point(lon,lat); district=r.get("district","")
        matches=[str(x.ADM2_EN) for x in districts.itertuples() if x.geometry.covers(pt)]
        dcheck="pass" if district and any(district in m for m in matches) else ("not_tested" if not district else "fail")
        sid=source_id(urls_in(r.get("source_1 (title, publisher, date, URL)",""))[0]) if urls_in(r.get("source_1 (title, publisher, date, URL)","")) else ""
        row={"site_id":"SITE-"+old,"event_id":canonical,"sector":"","cell":"","village":"","place_description":r.get("place_description","")+f"; source catalog/inventory reference (not a scar centroid); stated accuracy: {acc}; original row {old}","latitude":lat,"longitude":lon,"geometry_type":"point","location_quality":quality,"accuracy_m":accuracy,"coordinate_method":"inventory","source_crs":r.get("original_CRS","WGS84"),"district_check":dcheck,"slope_check":sample_slope(lat,lon),"source_id":sid}
        out.append(row);geoms.append(pt)
    # Satellite image AOI centers: six mapped contexts, linked to the single May 2023 event.
    for r in rows:
        old=r["event_id"]
        if old not in {f"RWA-LS-{i:04d}" for i in range(23,29)}:continue
        lat=float(r["latitude"]);lon=float(r["longitude"]);pt=Point(lon,lat); ev="RWA-LS-0022"
        matches=[str(x.ADM2_EN) for x in districts.itertuples() if x.geometry.covers(pt)]
        dcheck="pass" if any(r.get("district","")==m for m in matches) else "fail"
        src_urls=urls_in(r.get("source_1 (title, publisher, date, URL)","")); sid=source_id(src_urls[0]) if src_urls else ""
        # Sector derived by polygon overlay is an analytical label, not a source-reported village/sector.
        sm=[str(x.ADM3_EN) for x in sectors.itertuples() if x.geometry.covers(pt)]
        sector=sm[0] if sm else ""
        out.append({"site_id":"SITE-"+old,"event_id":ev,"sector":sector,"cell":"","village":"","place_description":r.get("place_description","")+"; source-reported assessment-area center, not an observed scar centroid; sector derived from ADM3 overlay, not source-reported","latitude":lat,"longitude":lon,"geometry_type":"aoi_center","location_quality":"aoi_center","accuracy_m":"","coordinate_method":"UNOSAT","source_crs":"WGS84","district_check":dcheck,"slope_check":sample_slope(lat,lon),"source_id":sid});geoms.append(pt)
    return out,geoms


def sites_from_nasa_glc(events,sources,districts):
    """Add six NASA GLC source coordinates as reference points linked to existing event episodes."""
    path=RAW/"nasa_glc_export_rows.csv"
    df=pd.read_csv(path,low_memory=False)
    rwa=df[df["country_code"].astype(str).str.upper().eq("RW")]
    if len(rwa)!=6: raise ValueError(f"Expected six Rwanda NASA GLC snapshot rows, got {len(rwa)}")
    mappings={272:("RWA-LS-0005","Rubavu"),273:("RWA-LS-0005","Nyabihu"),4834:("RWA-LS-0008","Gakenke"),7716:("RWA-LS-0011","Gakenke"),7717:("RWA-LS-0011","Ngororero")}
    sid=source_id("https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export/Global_Landslide_Catalog_Export_rows.csv")
    site_rows=[];geometries=[]
    for _,r in rwa.iterrows():
        rid=int(r["event_id"])
        if rid==1593:
            # The 50 km NASA point is the same reused coarse reference near the 2018 GLIDE point; do not emit it as a site.
            continue
        if rid not in mappings: raise ValueError(f"Unexpected Rwanda NASA ID {rid}")
        event_id,district=mappings[rid]
        lon=float(r["longitude"]);lat=float(r["latitude"]);pt=Point(lon,lat)
        accuracy_text=str(r["location_accuracy"]);m=re.search(r"(\d+)\s*km",accuracy_text,re.I);accuracy=float(m.group(1))*1000 if m else None
        quality="approximate" if accuracy is not None and accuracy<=5000 else "coarse"
        matches=[str(x.ADM2_EN) for x in districts.itertuples() if x.geometry.covers(pt)]
        dcheck="pass" if district in matches else "fail"
        desc=f"NASA GLC row {rid}; {r.get('location_description','')}; catalog accuracy {accuracy_text}; event impacts describe the episode, not this point."
        if rid==273 and district not in matches:
            desc+=f" District QA mismatch retained: source location is Nyabihu but the published coordinate falls in {', '.join(matches) or 'no ADM2 polygon'}; NASA states 5 km accuracy, so do not move or relabel the point as a surveyed site."
        if rid==7716: desc+=" NASA row date is 2016-05-08 although its narrative reports the 2016-05-07 episode."
        site_rows.append({"site_id":f"SITE-NASA-GLC-{rid}","event_id":event_id,"sector":"","cell":"","village":"","place_description":desc,"latitude":lat,"longitude":lon,"geometry_type":"point","location_quality":quality,"accuracy_m":accuracy,"coordinate_method":"published","source_crs":"WGS84 lon/lat in NASA CSV (no explicit CRS field)","district_check":dcheck,"slope_check":sample_slope(lat,lon),"source_id":sid})
        geometries.append(pt)
    return site_rows,geometries


def sites_from_2018_inventory(tmp,districts,sectors):
    """Reproject 494 classless combined slide/flash-flood inventory polygons and centroids."""
    z=RAW/"zenodo_2018_karongi_inventory.zip"
    if not z.exists(): raise FileNotFoundError(z)
    dest=tmp/"zenodo_2018";dest.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(z) as arc:arc.extractall(dest)
    shp=next(dest.rglob("Rwanda.shp"))
    gdf=gpd.read_file(shp)
    if len(gdf)!=494: raise ValueError(f"Expected 494 Zenodo Rwanda features, got {len(gdf)}")
    source_id_2018=source_id("https://doi.org/10.5281/zenodo.7198322")
    gdf=gdf.to_crs("EPSG:4326")
    # Validate each source feature's recorded id, preserve all 494 without inferring a slide/flood class.
    sites=[];geometries=[]
    for _,feature in gdf.iterrows():
        geom=feature.geometry
        if geom is None or geom.is_empty: raise ValueError("Empty 2018 source polygon")
        if not geom.is_valid: geom=geom.buffer(0)
        fid=int(feature.get("id",len(sites)//2+1));cent=geom.centroid
        dmatch=[str(x.ADM2_EN) for x in districts.itertuples() if x.geometry.covers(cent)]
        smatch=[str(x.ADM3_EN) for x in sectors.itertuples() if x.geometry.covers(cent)]
        # Feature class cannot be separated: published inventory is a combined landslide-and-flash-flood event inventory.
        text=f"Zenodo 7198322 Rwanda feature id {fid}; combined 2018 landslide/flash-flood inventory; shapefile has no per-feature hazard-class field, so not individually confirmed as a slide scar; centroid boundary overlay district={dmatch[0] if dmatch else 'unmatched'}; sector={smatch[0] if smatch else 'unmatched'}."
        common={"event_id":"RWA-LS-0016","sector":smatch[0] if smatch else "","cell":"","village":"","place_description":text,"location_quality":"approximate","accuracy_m":"","source_crs":"WGS 84 / UTM zone 35S (source); geometry reprojected to EPSG:4326","district_check":"pass" if "Karongi" in dmatch else "fail","source_id":source_id_2018}
        sites.append({"site_id":f"SITE-KARONGI-2018-{fid:03d}-P","latitude":"","longitude":"","geometry_type":"polygon","coordinate_method":"inventory","slope_check":"see paired centroid row; polygon is mixed/unclassified hazard feature",**common});geometries.append(geom)
        sites.append({"site_id":f"SITE-KARONGI-2018-{fid:03d}-C","latitude":cent.y,"longitude":cent.x,"geometry_type":"centroid_of_polygon","coordinate_method":"derived","slope_check":sample_slope(cent.y,cent.x),**common});geometries.append(cent)
    return sites,geometries


def process_unosat(tmp,events,sources,districts,sectors,sites,geoms):
    """Audit all UNOSAT layers; only convert incontrovertible landslide footprint layers."""
    z=RAW/"unosat_rubavu_2023.zip"; dest=tmp/"unosat";dest.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(z) as arc:arc.extractall(dest)
    import shapefile,xml.etree.ElementTree as ET
    audit=[]
    for shp in sorted(dest.rglob("*.shp")):
        reader=shapefile.Reader(str(shp),encoding="utf-8")
        records=[rec.as_dict() for rec in reader.records()]
        prj=shp.with_suffix(".prj").read_text(errors="replace") if shp.with_suffix(".prj").exists() else ""
        xmlfile=shp.with_suffix(".shp.xml"); xmltext=""
        if xmlfile.exists():
            try:xmltext=" | ".join(x.strip() for x in ET.parse(xmlfile).getroot().itertext() if x.strip())
            except:xmltext=xmlfile.read_text(errors="replace")
        name=shp.name.lower(); typ="landslide" if "landslideextent" in name else ("flood" if "floodextent" in name else ("analysis" if "analysisextent" in name else "other"))
        attrs=records[0] if records else {}
        if typ=="analysis": classification="excluded_analysis_boundary"
        elif typ=="flood": classification="excluded_flood_extent"
        elif typ=="landslide":
            ambiguous=attrs.get("Water_Clas")=="Flood Water" or attrs.get("Field_Vali")=="Not yet field validated" or attrs.get("Confidence")=="To be evaluated"
            classification="ambiguous_reported_landslide_area_excluded_as_confirmed_site" if ambiguous else "genuine_landslide_extent"
            # Never silently promote the observed 246.915 ha flood-water classified feature to a slide polygon.
            if not ambiguous:
                gdf=gpd.read_file(shp).to_crs(4326)
                source_url="https://unosat.org/products/3579"; sid=source_id(source_url)
                for j,feat in gdf.iterrows():
                    geom=feat.geometry
                    sid_site=f"SITE-UNOSAT-3579-{j+1:03d}"
                    pt=geom.centroid; matches=[str(x.ADM2_EN) for x in districts.itertuples() if x.geometry.covers(pt)]
                    dist=matches[0] if matches else ""
                    sm=[str(x.ADM3_EN) for x in sectors.itertuples() if x.geometry.covers(pt)]
                    for suffix,geometry,gtype in [("-P",geom,"polygon"),("-C",pt,"centroid_of_polygon")]:
                        sidrow={"site_id":sid_site+suffix,"event_id":"RWA-LS-0022","sector":sm[0] if sm else "","cell":"","village":"","place_description":"UNOSAT mapped landslide extent; site geometry from validated landslide layer","latitude":pt.y if gtype=="centroid_of_polygon" else "","longitude":pt.x if gtype=="centroid_of_polygon" else "","geometry_type":gtype,"location_quality":"approximate","accuracy_m":"","coordinate_method":"derived","source_crs":"WGS84","district_check":"pass" if dist else "fail","slope_check":sample_slope(pt.y,pt.x),"source_id":sid}
                        sites.append(sidrow);geoms.append(geometry)
        else:classification="review_required"
        audit.append({"path":str(shp.relative_to(dest)),"filename_class":typ,"features":len(reader),"shape_type":str(reader.shapeType),"fields":[f[0] for f in reader.fields[1:]],"sample_attributes":attrs,"bbox":list(reader.bbox),"source_crs_prj":prj,"xml_metadata":xmltext,"reviewed_classification":classification,"review_rationale":"File-named LandslideExtent is not field validated and attributes classify the one 246.915 ha feature as Flood Water / New Water; excluded from confirmed sites. Analysis extents and FloodExtent polygons are excluded." if typ in {"analysis","flood","landslide"} else "Not classified."})
    (OUT/"unosat_layer_audit.json").write_text(json.dumps(audit,ensure_ascii=False,indent=2,default=str),encoding="utf-8")
    return audit


def source_and_additions(rows,events,sources):
    addfile=ROOT/"additional_event_candidates.json"
    if addfile.exists():
        for ev in json.loads(addfile.read_text(encoding="utf-8")).get("candidate_events",[]):
            for url in ev.get("source_urls",[]):
                sid=source_id(url)
                if sid not in sources:
                    sources[sid]={"source_id":sid,"title":ev.get("source_title",urlparse(url).netloc),"publisher":ev.get("publisher",urlparse(url).netloc),"date":ev.get("source_date",""),"url":url,"access_date":"2026-10-16","license":"Not stated; consult source terms","access_status":"opened and independently checked","what_was_extracted":"Event date, place or impacts in linked row."}
                if "lemonde.fr" in url:
                    sources[sid]["access_status"]="Partially accessible; paywall after visible opening section; only visible text used; no paywall/access control bypassed"
                    sources[sid]["what_was_extracted"]="Visible opening section supports the 2026-03-23 date, Kigarama/Ngororero location and two deaths; full article was not accessed."
    return sources


def outputs(events,sites,sources,site_geoms,a1,a2,a3,validation,unosat_audit,aux_tables=None):
    aux_tables=aux_tables or {}
    ev=pd.DataFrame(events,columns=EVENT_FIELDS)
    st=pd.DataFrame(sites,columns=SITE_FIELDS)
    sc=pd.DataFrame(sorted(sources.values(),key=lambda r:r["source_id"]),columns=SOURCE_FIELDS)
    ev.to_csv(OUT/"events.csv",index=False,encoding="utf-8")
    st.to_csv(OUT/"sites.csv",index=False,encoding="utf-8")
    sc.to_csv(OUT/"sources.csv",index=False,encoding="utf-8")
    pd.DataFrame(validation).to_csv(OUT/"site_validation.csv",index=False,encoding="utf-8")
    pd.DataFrame([{k:v for k,v in x.items() if k!="xml_metadata"} for x in unosat_audit]).to_csv(OUT/"unosat_layer_classification.csv",index=False,encoding="utf-8")
    # Site geometry dataset assembled in precisely the same order as the rows.
    sg=gpd.GeoDataFrame(st.copy(),geometry=site_geoms,crs="EPSG:4326")
    sg.to_file(OUT/"sites.geojson",driver="GeoJSON",index=False)
    # Events GeoJSON uses GeometryCollection of linked site geometries and explicit site IDs.
    features=[]
    for e in events:
        ids=[r["site_id"] for r in sites if r["event_id"]==e["event_id"]]
        geoms_for=[g for r,g in zip(sites,site_geoms) if r["event_id"]==e["event_id"] and g is not None]
        geometry=GeometryCollection(geoms_for) if geoms_for else None
        props={k:v for k,v in e.items() if k!="source_ids"};props["source_ids"]=e["source_ids"];props["site_ids"]="|".join(ids)
        features.append({"type":"Feature","id":e["event_id"],"geometry":mapping(geometry) if geometry else None,"properties":props})
    (OUT/"events.geojson").write_text(json.dumps({"type":"FeatureCollection","name":"Rwanda landslide events v2","crs":{"type":"name","properties":{"name":"urn:ogc:def:crs:OGC:1.3:CRS84"}},"features":features},ensure_ascii=False,default=str),encoding="utf-8")
    # KML preserves polygons and uses points for non-polygon locations/centroids.
    from xml.etree.ElementTree import Element,SubElement,ElementTree
    root=Element("kml",xmlns="http://www.opengis.net/kml/2.2");doc=SubElement(root,"Document");SubElement(doc,"name").text="Rwanda landslide sites v2 (WGS84)"
    for rec,geom in zip(sites,site_geoms):
        pm=SubElement(doc,"Placemark");SubElement(pm,"name").text=rec["site_id"]
        desc=SubElement(pm,"description");desc.text=f"event_id={rec['event_id']}; quality={rec['location_quality']}; source_id={rec['source_id']}"
        if geom is None: continue
        if geom.geom_type=="Polygon":
            poly=SubElement(pm,"Polygon");outer=SubElement(poly,"outerBoundaryIs");ring=SubElement(outer,"LinearRing");SubElement(ring,"coordinates").text=" ".join(f"{x},{y},0" for x,y in geom.exterior.coords)
        elif geom.geom_type in {"MultiPolygon","GeometryCollection"}:
            # Keep all rings in a MultiGeometry folder as individual polygons/points.
            mg=SubElement(pm,"MultiGeometry")
            polys=list(geom.geoms) if geom.geom_type=="MultiPolygon" else list(geom.geoms)
            for part in polys:
                if part.geom_type=="Polygon":
                    pol=SubElement(mg,"Polygon");ou=SubElement(pol,"outerBoundaryIs");ri=SubElement(ou,"LinearRing");SubElement(ri,"coordinates").text=" ".join(f"{x},{y},0" for x,y in part.exterior.coords)
                elif part.geom_type=="Point":
                    pt=SubElement(mg,"Point");SubElement(pt,"coordinates").text=f"{part.x},{part.y},0"
        elif geom.geom_type=="Point":
            pt=SubElement(pm,"Point");SubElement(pt,"coordinates").text=f"{geom.x},{geom.y},0"
    ElementTree(root).write(OUT/"sites.kml",encoding="utf-8",xml_declaration=True)
    # GeoPackage layers: event attribute table plus sites and administrative hierarchy.
    gpkg=OUT/"rwanda_landslide_v2.gpkg"
    if gpkg.exists():gpkg.unlink()
    eg=gpd.GeoDataFrame(ev.copy(),geometry=[None]*len(ev),crs="EPSG:4326")
    eg.to_file(gpkg,layer="events",driver="GPKG",index=False)
    sg.to_file(gpkg,layer="sites",driver="GPKG",index=False)
    for name,gdf in [("admin_provinces",a1),("admin_districts",a2),("admin_sectors",a3)]:gdf.to_file(gpkg,layer=name,driver="GPKG",index=False)
    # Choropleth-free district count/deaths table. Multi-district totals are not apportioned.
    dist_rows=[]
    for dname in sorted(set(a2["ADM2_EN"].astype(str))):
        subset=[e for e in events if dname in e["districts"].split("|")]
        local=[e for e in subset if int(e["n_districts"] or 0)==1]
        lo=[];hi=[]
        for e in local:
            if str(e["fatalities_min"]).isdigit():lo.append(int(e["fatalities_min"]))
            if str(e["fatalities_max"]).isdigit():hi.append(int(e["fatalities_max"]))
        dist_rows.append({"district":dname,"recorded_event_count":len(subset),"single_district_deaths_min":sum(lo) if lo else "","single_district_deaths_max":sum(hi) if hi else "","multi_district_events_with_unallocated_deaths":sum(1 for e in subset if int(e["n_districts"] or 0)>1 and (e["fatalities_min"] or e["fatalities_max"]))})
    dd=pd.DataFrame(dist_rows);dd.to_csv(OUT/"district_event_counts_deaths.csv",index=False)
    # Annual event count: each normalized episode counted once.
    ev["year"]=ev["date_start"].str[:4];annual=ev.groupby("year",dropna=False).size().reset_index(name="recorded_event_count")
    annual.to_csv(OUT/"annual_event_counts.csv",index=False)
    fig,ax=plt.subplots(figsize=(11,4.5),dpi=180);ax.bar(annual.year,annual.recorded_event_count,color="#356d79");ax.set_ylabel("Distinct event records");ax.set_xlabel("Year of date_start");ax.set_title("Rwanda landslide episodes in the compiled record (reporting counts, not normalized risk)");ax.tick_params(axis="x",rotation=45);ax.grid(axis="y",alpha=.25);fig.tight_layout();fig.savefig(OUT/"annual_event_counts.png",bbox_inches="tight");plt.close(fig)
    # National district basemap with point/poly geometry and coordinate quality.
    fig,ax=plt.subplots(figsize=(9.5,10.5),dpi=180)
    a2.plot(ax=ax,facecolor="#f3f5f1",edgecolor="#9ca79e",linewidth=.38,zorder=1)
    a1.boundary.plot(ax=ax,color="#344a40",linewidth=1.05,zorder=2)
    for _,row in sg.iterrows():
        q=row["location_quality"];geom=row.geometry
        c={"exact":"#16823b","approximate":"#f29e0b","coarse":"#9b3e7a","aoi_center":"#cf3d2d"}.get(q,"#555")
        e=next((x for x in events if x["event_id"]==row["event_id"]),None)
        deaths=0
        if e and int(e["n_districts"] or 0)==1 and str(e["fatalities_max"]).isdigit():deaths=int(e["fatalities_max"])
        size=28+min(80,math.sqrt(deaths)*7) if deaths else 28
        if geom.geom_type=="Polygon":
            x,y=geom.exterior.xy;ax.fill(x,y,facecolor=c,edgecolor=c,alpha=.25,linewidth=.6,zorder=4)
            p=geom.representative_point();x0,y0=p.x,p.y
        elif geom.geom_type=="Point":
            x0,y0=geom.x,geom.y;ax.scatter(x0,y0,s=size,c=c,edgecolor="white",linewidth=.6,zorder=5)
        else:continue
        # Polygon and paired-centroid labels would overlap hundreds of times in the Karongi cluster.
        # Keep readable IDs for point sites; all feature IDs remain in the table and GIS layers.
        if row["geometry_type"] in {"point","aoi_center"} and not row["site_id"].startswith("SITE-4TU-"):
            ax.annotate(row["site_id"].replace("SITE-",""),(x0,y0),xytext=(3,3),textcoords="offset points",fontsize=4.0,zorder=6)
    for _,r in a2.iterrows():
        p=r.geometry.representative_point();ax.text(p.x,p.y,str(r.get("ADM2_EN","")),fontsize=3.8,ha="center",va="center",color="#44514a",alpha=.75,zorder=3)
    from matplotlib.lines import Line2D
    handles=[Line2D([0],[0],marker='o',color='w',markerfacecolor=c,markersize=6,label=l) for l,c in [("Exact","#16823b"),("Approximate","#f29e0b"),("Coarse event/catalog point","#9b3e7a"),("Assessment-area center","#cf3d2d")]]
    ax.legend(handles=handles,loc="lower right",fontsize=6,framealpha=.95);ax.set_title("Rwanda recorded landslide events and mapped contexts\nMarker size reflects fatalities only for single-district events; colors show location quality",fontsize=11)
    ax.set_xlabel("Longitude (WGS84)");ax.set_ylabel("Latitude (WGS84)");ax.grid(alpha=.18);ax.set_aspect("equal",adjustable="box")
    fig.text(.01,.01,"Boundary source: NISR via OCHA/HDX COD-AB (2018 package, WGS84; metadata age/accuracy caveats apply). Counts reflect reporting and are not normalized risk. Coarse catalog points are event references, not slide-site coordinates. Compound-event deaths are not apportioned.",fontsize=5.8)
    fig.tight_layout(rect=(0,.035,1,1));fig.savefig(OUT/"rwanda_landslide_locations.png",bbox_inches="tight");plt.close(fig)
    # Excel workbook with analysis tables.
    with pd.ExcelWriter(OUT/"rwanda_landslide_v2.xlsx",engine="openpyxl") as xw:
        ev.drop(columns="year").to_excel(xw,sheet_name="Events",index=False)
        st.to_excel(xw,sheet_name="Sites",index=False)
        sc.to_excel(xw,sheet_name="Sources",index=False)
        dd.to_excel(xw,sheet_name="District counts",index=False)
        annual.to_excel(xw,sheet_name="Annual counts",index=False)
        pd.DataFrame(validation).to_excel(xw,sheet_name="Spatial QA",index=False)
        pd.DataFrame([{k:v for k,v in x.items() if k!="xml_metadata"} for x in unosat_audit]).to_excel(xw,sheet_name="UNOSAT layers",index=False)
        for _name,_table in aux_tables.items():
            _table.to_excel(xw,sheet_name=_name[:31],index=False)
        pd.DataFrame([{"topic":"Purpose","detail":"Curated Rwanda landslide events and mapped site contexts; one event may link to multiple sites."},{"topic":"Counts","detail":f"{len(ev)} events; {len(st)} sites; {int(st.latitude.astype(str).ne('').sum())} sites with coordinates."},{"topic":"Important caveat","detail":"Reporting-count patterns are not normalized hazard risk. Coarse catalog points are not slide-site coordinates; UNOSAT AOI centers are not slide centroids."},{"topic":"Licensing","detail":"Mixed source terms; no blanket open license is asserted. See LICENSE.md and sources.csv."}]).to_excel(xw,sheet_name="README",index=False)
    # Excel formatting for usability.
    from openpyxl import load_workbook
    from openpyxl.styles import Font,PatternFill,Alignment
    wb=load_workbook(OUT/"rwanda_landslide_v2.xlsx")
    for ws in wb.worksheets:
        ws.freeze_panes="A2";ws.auto_filter.ref=ws.dimensions
        for c in ws[1]:c.font=Font(bold=True,color="FFFFFF");c.fill=PatternFill("solid",fgColor="244B5A");c.alignment=Alignment(wrap_text=True,vertical="top")
        for col in ws.columns:
            letter=col[0].column_letter;ws.column_dimensions[letter].width=min(52,max(12,max((len(str(c.value or "")) for c in list(col)[:150]),default=12)))
        for row in ws.iter_rows(min_row=2):
            for c in row:c.alignment=Alignment(wrap_text=True,vertical="top")
    wb.save(OUT/"rwanda_landslide_v2.xlsx")


def validate(events,sites,sources,site_geoms,validation):
    err=[];eids=set();sids=set()
    for e in events:
        if e["event_id"] in eids:err.append("duplicate event_id "+e["event_id"])
        eids.add(e["event_id"])
        if e["primary_trigger"] not in VALID_TRIGGERS:err.append("invalid trigger "+e["event_id"])
        if e["landslide_type"] not in VALID_TYPES:err.append("invalid landslide_type "+e["event_id"])
        if e["event_confidence"] not in {"High","Medium","Low"}:err.append("invalid confidence "+e["event_id"])
        if e["date_precision"] not in {"day","month","year","range"}:err.append("invalid precision "+e["event_id"])
        for col in ["fatalities_min","fatalities_max","injuries_min","injuries_max","people_affected","people_displaced","houses_destroyed","houses_damaged","n_districts"]:
            v=e[col]
            if v not in (None,"") and not str(v).isdigit():err.append(f"non-numeric {col} {e['event_id']}={v}")
        for u in e["source_ids"].split("|"):
            if u and u not in sources:err.append("source FK missing "+u)
        try:datetime.strptime(e["date_start"],"%Y-%m-%d")
        except Exception:err.append("invalid date_start "+e["event_id"])
        if e["date_end"]:
            try:datetime.strptime(e["date_end"],"%Y-%m-%d")
            except Exception:err.append("invalid date_end "+e["event_id"])
    for site,geom in zip(sites,site_geoms):
        if site["site_id"] in sids:err.append("duplicate site_id "+site["site_id"])
        sids.add(site["site_id"])
        if site["event_id"] not in eids:err.append("orphan site "+site["site_id"])
        if site["location_quality"] not in {"exact","approximate","coarse","aoi_center"}:err.append("invalid quality "+site["site_id"])
        if site["geometry_type"] not in {"point","polygon","centroid_of_polygon","aoi_center"}:err.append("invalid geometry_type "+site["site_id"])
        if site["latitude"] not in (None,"") and site["longitude"] not in (None,""):
            lat=float(site["latitude"]);lon=float(site["longitude"])
            if not (-2.85<=lat<=-1.04 and 28.85<=lon<=30.91):err.append("coordinate outside Rwanda envelope "+site["site_id"])
        if site["district_check"] not in {"pass","fail","not_tested"}:err.append("invalid district QA status "+site["site_id"])
        if site["source_id"] and site["source_id"] not in sources:err.append("site source FK missing "+site["site_id"])
    # Spatial mismatches are acceptable only when the row-level QA table gives an explicit reason.
    explanations={x.get("site_id"):x.get("mismatch_explanation","") for x in validation}
    unexplained=[x["site_id"] for x in sites if x.get("district_check")=="fail" and not explanations.get(x["site_id"])]
    if unexplained:err.append("unexplained district polygon failures: "+", ".join(unexplained))
    unexplained_sector=[x.get("site_id") for x in validation if x.get("sector_check")=="fail" and not x.get("mismatch_explanation")]
    if unexplained_sector:err.append("unexplained sector polygon failures: "+", ".join(unexplained_sector))
    for s in sources.values():
        if not s["url"].startswith("http"):err.append("source URL missing "+s["source_id"])
    if err:
        (OUT/"validation_errors.txt").write_text("\n".join(err)+"\n",encoding="utf-8")
        raise SystemExit("Validation failed: "+"; ".join(err[:12]))
    (OUT/"validation_errors.txt").unlink(missing_ok=True)
    return {"errors":0,"events":len(events),"sites":len(sites),"coordinate_pairs":sum(bool(x.get("latitude") not in (None,"") and x.get("longitude") not in (None,"")) for x in sites),"sources":len(sources),"district_failures":sum(x["district_check"]=="fail" for x in sites),"sector_failures":sum(x.get("sector_check")=="fail" for x in validation)}


def main():
    rows=raw_events()
    # Guarantee strict CSV layout and the only known categorical/citation fault is repaired explicitly.
    with INPUT.open(encoding="utf-8-sig",newline="") as f:
        rawread=list(csv.reader(f,strict=True))
    if any(len(r)!=len(rawread[0]) for r in rawread):raise ValueError("Source CSV row-width fault; inspect original input.")
    if sum(1 for r in rows if r["confidence"] not in {"High","Medium","Low"})!=1 or not rows[5]["event_id"].endswith("0006"):
        raise ValueError("Unexpected original confidence defects; update audit and repairs before building.")
    with tempfile.TemporaryDirectory(prefix="rwa-v2-build-") as td:
        tmp=Path(td);a1,a2,a3=read_boundaries(tmp)
        district_to_prov={str(r.ADM2_EN):str(r.ADM1_EN) for r in a2.itertuples()}
        sources=load_sources(rows)
        events=make_events(rows,sources,district_to_prov)
        sites,site_geoms=sites_from_original(rows,events,sources,a2,a3)
        ns,ng=sites_from_nasa_glc(events,sources,a2);sites.extend(ns);site_geoms.extend(ng)
        zs,zg=sites_from_2018_inventory(tmp,a2,a3);sites.extend(zs);site_geoms.extend(zg)
        ua=process_unosat(tmp,events,sources,a2,a3,sites,site_geoms)
        sources=source_and_additions(rows,events,sources)
        from reconcile_auxiliary import augment_external
        aux_tables=augment_external(events,sites,site_geoms,sources,a2,a3,source_id,sample_slope,ROOT)
        for _name,_table in aux_tables.items():
            _table.to_csv(OUT/f"{_name}.csv",index=False,encoding="utf-8")
        # Spatial QA including both administrative levels and DEM slope.
        validation=[]
        for r,g in zip(sites,site_geoms):
            if g is None:continue
            pt=g if g.geom_type=="Point" else g.centroid
            dmatch=[str(x.ADM2_EN) for x in a2.itertuples() if x.geometry.covers(pt)]
            smatch=[str(x.ADM3_EN) for x in a3.itertuples() if x.geometry.covers(pt)]
            stated=[x for x in next(e for e in events if e["event_id"]==r["event_id"])["districts"].split("|") if x]
            if r["geometry_type"]=="point" and r["location_quality"]=="coarse":
                dstatus="pass" if any(x in dmatch for x in stated) else "fail"
            else:dstatus="pass" if (not stated or any(x in dmatch for x in stated)) else "fail"
            sector=r["sector"] or ""
            sstatus="not_tested" if not sector else ("pass" if sector in smatch else "fail")
            explanation=r.get("_mismatch_explanation", "")
            sector_explanation=r.get("_sector_mismatch_explanation", "")
            if sector and sstatus=="fail":
                explanation=(explanation+"; " if explanation else "")+(sector_explanation or f"Reported sector {sector}; point/polygon centroid overlays {smatch or ['no ADM3 polygon']}.")
            if r["site_id"]=="SITE-NASA-GLC-273":explanation="NASA GLC source label Nyabihu; point falls in OCHA/NISR ADM2 Ngororero. Catalog location_accuracy=5 km; mismatch is retained, not corrected by spatial guess."
            if dstatus=="fail" and not explanation:
                explanation=f"Reported event district(s) {stated}; point/polygon centroid overlays {dmatch or ['no ADM2 polygon']}; source coordinate retained and flagged, not moved or relabeled."
            validation.append({"site_id":r["site_id"],"event_id":r["event_id"],"reported_event_districts":"|".join(stated),"boundary_districts":"|".join(dmatch),"district_check":dstatus,"mismatch_explanation":explanation,"sector_value":sector,"boundary_sectors":"|".join(smatch),"sector_check":sstatus,"geometry_type":r["geometry_type"],"location_quality":r["location_quality"],"slope_check":r["slope_check"],"point_lon":pt.x,"point_lat":pt.y})
            r["district_check"]=dstatus
            if sector and not sstatus:r["sector"]=""
        # Detect close coordinates across different events. Coarse repeated pair is not emitted as site points.
        spatial=[]
        pointrows=[(r,g) for r,g in zip(sites,site_geoms) if g is not None and g.geom_type=="Point"]
        for i,(r1,p1) in enumerate(pointrows):
            for r2,p2 in pointrows[i+1:]:
                if r1["event_id"]!=r2["event_id"]:
                    # local equirectangular distance at Rwanda latitudes
                    dx=(p1.x-p2.x)*111320*math.cos(math.radians((p1.y+p2.y)/2));dy=(p1.y-p2.y)*110574;dist=math.hypot(dx,dy)
                    if dist<500:spatial.append({"site_id_1":r1["site_id"],"event_id_1":r1["event_id"],"site_id_2":r2["site_id"],"event_id_2":r2["event_id"],"distance_m":round(dist,1),"flag":"possible_near_duplicate_or_real_nearby_sites"})
        pd.DataFrame(spatial,columns=["site_id_1","event_id_1","site_id_2","event_id_2","distance_m","flag"]).to_csv(OUT/"near_duplicate_coordinates.csv",index=False)
        summary=validate(events,sites,sources,site_geoms,validation)
        outputs(events,sites,sources,site_geoms,a1,a2,a3,validation,ua,aux_tables)
        (OUT/"BUILD_SUMMARY.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2))

if __name__=="__main__":main()
