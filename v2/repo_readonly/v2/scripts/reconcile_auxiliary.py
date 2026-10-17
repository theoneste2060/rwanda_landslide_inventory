#!/usr/bin/env python3
"""Reconcile source inventories against the curated Rwanda v2 event/site tables.

This module preserves source-row values in audit tables and only adds events with
an explicit source link (dataset DOI/document counts as a retrievable source).
"""
from __future__ import annotations
import json, math, re
from datetime import date, datetime
from pathlib import Path
import pandas as pd
import numpy as np
from shapely.geometry import Point


def _s(v):
    if v is None or (isinstance(v,float) and np.isnan(v)): return ""
    return str(v).strip()


def _num(v):
    s=_s(v)
    if not s or s.lower() in {"na","n/a","none","unknown","-","null"}: return ""
    m=re.search(r"-?\d[\d,]*",s)
    return str(int(m.group(0).replace(",",""))) if m else ""


def _bounds(values):
    ns=[int(x) for x in values if _s(x).isdigit()]
    return (str(min(ns)),str(max(ns))) if ns else ("","")


def _iso(v):
    if isinstance(v,(datetime,date,pd.Timestamp)): return v.date().isoformat() if isinstance(v,pd.Timestamp) else v.isoformat()[:10]
    s=_s(v)
    if not s:return ""
    try:return pd.to_datetime(s,errors="raise").date().isoformat()
    except Exception:return ""


def _add_source(sources,source_id,url,title,publisher,date_value,license,access_status,what):
    if not url or not str(url).startswith("http"):return ""
    sid=source_id(url)
    sources.setdefault(sid,{"source_id":sid,"title":title or url,"publisher":publisher or "","date":date_value or "","url":url,"access_date":"2026-10-16","license":license or "Not stated in retrieved metadata; consult source terms","access_status":access_status or "Cited in source dataset; access status documented in QA report","what_was_extracted":what or "Source record used in the linked event or reconciliation row."})
    return sid


def _add_event_source(event,url,source_id):
    if not url:return
    ids=[x for x in _s(event.get("source_ids")).split("|") if x]
    sid=source_id(url)
    if sid not in ids:ids.append(sid)
    event["source_ids"]="|".join(ids)


def _district_names(text,a2):
    t=" "+re.sub(r"[^a-z0-9]+"," ",_s(text).casefold())+" "
    found=[]
    for nm in sorted(set(a2["ADM2_EN"].astype(str)),key=len,reverse=True):
        key=" "+re.sub(r"[^a-z0-9]+"," ",nm.casefold()).strip()+" "
        if key.strip() and key in t and nm not in found:found.append(nm)
    return found


def _sector_names(text,a3):
    t=" "+re.sub(r"[^a-z0-9]+"," ",_s(text).casefold())+" "
    found=[]
    raw=_s(text).casefold()
    for nm in sorted(set(a3["ADM3_EN"].astype(str)),key=len,reverse=True):
        escaped=re.escape(nm).replace(r"\ ",r"\s+")
        if re.search(rf"\b{escaped}\s+sector\b|\bsector\s+{escaped}\b",raw,re.I) and nm not in found:found.append(nm)
    return found


def _place_parts(text):
    text=_s(text)
    def one(pattern):
        m=re.search(pattern,text,re.I)
        return m.group(1).strip(" ,.;") if m else ""
    village=one(r"(?:village|village of)\s+([\wÀ-ÿ'’ -]{2,50})")
    cell=one(r"([\wÀ-ÿ'’ -]{2,50})\s+cell\b")
    return village,cell


def _trigger_type(category,trigger):
    c=_s(category).casefold(); t=_s(trigger).casefold()
    if any(x in c for x in ["mining","quarry","road cut","construction"]): lt="slope failure (mining/road/construction)"
    elif "rock" in c and "fall" in c: lt="rockfall"
    elif "debris" in c: lt="debris flow"
    elif "mud" in c: lt="mudslide"
    elif "mixed" in c or "flood" in c: lt="mixed landslide-flood"
    elif "rotational" in c or "translational" in c: lt="rotational/translational slide"
    elif "cluster" in c: lt="landslide cluster"
    else: lt="unknown"
    if any(x in t for x in ["mine","mining","quarry","sand","illegal hillcutting","illegal slope cutting"]): tr="mining/quarrying"
    elif any(x in t for x in ["construction","road cut"]): tr="construction/road cut"
    elif "earthquake" in t: tr="earthquake"
    elif "prolonged" in t: tr="prolonged rainfall"
    elif "rain" in t or "downpour" in t or "torrential" in t or "water" in t: tr="rainfall"
    elif "flood" in t: tr="flood-related"
    else: tr="unknown"
    return lt,tr


def _accuracy(v):
    s=_s(v).casefold()
    m=re.search(r"(\d+(?:\.\d+)?)\s*km",s)
    if m:
        a=float(m.group(1))*1000
        return a,"approximate" if a<=5000 else "coarse"
    m=re.search(r"(\d+(?:\.\d+)?)\s*m",s)
    if m:
        a=float(m.group(1))
        return a,"exact" if a<=100 else ("approximate" if a<=5000 else "coarse")
    return "","coarse"


def _add_event_note(event,text):
    if not text:return
    old=_s(event.get("notes"))
    if text not in old:event["notes"]=(old+" | " if old else "")+text


def _event_by_id(events): return {e["event_id"]:e for e in events}


def augment_external(events,sites,geoms,sources,a2,a3,source_id,sample_slope,root):
    """Mutate the event/site/source lists and return audit tables for export."""
    root=Path(root); raw=root/"raw_sources"; tables={}; cross=[]
    fourtu_url="https://doi.org/10.4121/15040446.v1"
    glide_url="https://data.humdata.org/dataset/100527e3-cd37-4248-8998-310d22325f5f/resource/306f434f-65b7-4f57-8690-f3e1023db32c/download/rwa_glide_events.csv"
    gfld_url="https://services2.arcgis.com/Dn40vzt2R38VJsSS/arcgis/rest/services/NSLandslidepoints_04to17/FeatureServer/0?f=json"
    nasa_url="https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export/Global_Landslide_Catalog_Export_rows.csv"
    paper_url="https://pmc.ncbi.nlm.nih.gov/articles/PMC5858312/table/ijerph-15-00243-t001/"
    fourtu_sid=_add_source(sources,source_id,fourtu_url,"Data underlying the research of Integration of observed and model derived groundwater levels in landslide threshold models in Rwanda","4TU.ResearchData / J. Uwihirwe","2021","CC0 (record metadata; see 4TU record)","Downloaded workbook and README; row-level workbook used; no CRS stated in README","Workbook describes a 2006–2021 Rwanda landslide inventory; original OIDs, citations, date/impact values and lat/lon retained in 4TU_reconciliation.csv.")
    glide_sid=_add_source(sources,source_id,glide_url,"Rwanda GLIDE disaster event table","OCHA/HDX; GLIDE","accessed 2026-10-16","License not stated in retrieved metadata","Downloaded 29-row Rwanda CSV; all records reconciled; non-landslide hazards retained as excluded crosswalk entries","Event identifiers, dates, impact fields, comments and citations preserved in glide_reconciliation.csv.")
    gfld_sid=_add_source(sources,source_id,gfld_url,"Global Fatal Landslide Database Version 2 Rwanda point-layer query","Froude & Petley / ArcGIS REST service","2004–2017","Not stated in ArcGIS item metadata; consult provider terms","Downloaded public Rwanda-filtered feature export (19 points); original fields and report URLs preserved in GFLD reconciliation","Rwanda row-level event date, coordinates, fatalities, trigger, source links and location descriptions.")
    paper_sid=_add_source(sources,source_id,paper_url,"Table 1: Latest main disasters caused by landslides in Rwanda","International Journal of Environmental Research and Public Health","2018-01-31","CC BY 4.0 article license; table attribution required","Extracted all 11 month/district rows and impacts; no exact day or point coordinates invented","Month-level event claims, impact values, match decisions and non-additive notes.")
    # Register the NASA dataset source separately for crosswalk rows and event links.
    nasa_sid=_add_source(sources,source_id,nasa_url,"NASA Global Landslide Catalog Export CSV","NASA","Snapshot current to 2016-03-07","NASA portal license unspecified; portal terms apply","Six Rwanda rows reconciled against events; five non-reused source points are separately emitted by build_v2.py","Catalog event IDs, date, location_accuracy, descriptions and source event mapping.")

    # 4TU workbook row-level reconciliation.
    p4=raw/"4tu_rwanda_inventory.xlsx"
    df=pd.read_excel(p4,dtype=object)
    df=df[df["OBJECTID"].notna()].copy(); df["OBJECTID"]=df["OBJECTID"].astype(int)
    adj=json.loads((root/"4tu_adjudication.json").read_text(encoding="utf-8"))
    existing={int(k):v for k,v in adj["record_mapping_to_existing"].items()}
    exclusions={int(k):v for k,v in adj["excluded_records"].items()}
    overrides={int(k):v for k,v in adj["row_overrides"].items()}
    site_exclusions={int(k):v for k,v in adj["site_exclusions"].items()}
    groups=adj["new_event_groups"]
    oid_to_event={}
    for oid,eid in existing.items():oid_to_event[oid]=eid
    for i,oids in enumerate(groups,1):
        eid=f"RWA-LS-4TU-{i:03d}"
        for oid in oids:oid_to_event[int(oid)]=eid
    required=set(df["OBJECTID"].astype(int))
    handled=set(oid_to_event)|set(exclusions)
    if required!=handled: raise ValueError(f"4TU adjudication incomplete; unhandled={sorted(required-handled)}, unexpected={sorted(handled-required)}")
    district_to_prov={str(r.ADM2_EN):str(r.ADM1_EN) for r in a2.itertuples()}
    rowdict={int(r["OBJECTID"]):r.to_dict() for _,r in df.iterrows()}
    evmap=_event_by_id(events)
    # Apply explicit correction to original affected/injured fields from the 2006 crosswalk.
    e=evmap.get("RWA-LS-0004")
    if e:
        e["people_affected"]="2000"
        _add_event_note(e,"4TU OID 2 recorded 2,000 in injury_count; reconciled as people affected, not injuries, consistent with the original historical impact summary.")
    for oid,eid in existing.items():
        row=rowdict[oid]
        urls=[_s(row.get("source_link"))]
        urls=[u for u in urls if u.startswith("http")]
        _add_event_source(evmap[eid],fourtu_url,source_id)
        for u in urls:
            sid=_add_source(sources,source_id,u,_s(row.get("event_title")) or _s(row.get("source_name")),_s(row.get("source_name")),_iso(row.get("event_date")),"Not stated; source publisher terms apply","Cited in downloaded 4TU workbook; individually opened only where noted in research log","Event/date/location/impact claim from 4TU row.")
            _add_event_source(evmap[eid],u,source_id)
        ov=overrides.get(oid,{})
        if ov.get("decision_note"):_add_event_note(evmap[eid],"4TU crosswalk note: "+ov["decision_note"])
        cross.append({"source_system":"4TU","source_record_id":oid,"event_id":eid,"match_status":"matched_to_existing_event","matching_rule":"Manual crosswalk; date/district overlap and/or named catalog/source match; see adjudication file","source_event_date":_iso(row.get("event_date")),"source_title":_s(row.get("event_title")),"source_location":_s(row.get("location_description")),"source_url":_s(row.get("source_link")) or fourtu_url,"decision_note":ov.get("decision_note","")})
    new_rows=[]
    for i,oids in enumerate(groups,1):
        eid=f"RWA-LS-4TU-{i:03d}"; rs=[rowdict[int(o)] for o in oids]
        texts=" | ".join(_s(r.get(k)) for r in rs for k in ["event_title","event_description","location_description"] if _s(r.get(k)))
        override=next((overrides[int(o)] for o in oids if int(o) in overrides),{})
        dates=[_iso(r.get("event_date")) for r in rs if _iso(r.get("event_date"))]
        ds=min(dates) if dates else ""; de=max(dates) if dates and max(dates)!=min(dates) else ""
        precision="range" if de else "day"
        if override.get("date_start") is not None: ds=override["date_start"]
        if "date_end" in override: de=override["date_end"]
        if override.get("date_precision"):precision=override["date_precision"]
        reported=override.get("districts") or _district_names(texts,a2)
        reported=list(dict.fromkeys(str(x) for x in reported if str(x) in district_to_prov))
        provinces=list(dict.fromkeys(district_to_prov[x] for x in reported))
        titles=[_s(r.get("event_title")) for r in rs if _s(r.get("event_title"))]
        name=titles[0] if titles else f"{ds[:7] if ds else 'Undated'} 4TU inventory landslide record (OID {'/'.join(map(str,oids))})"
        cats=[_s(r.get("landslide_category")) for r in rs if _s(r.get("landslide_category"))]
        trigs=[_s(r.get("landslide_trigger")) for r in rs if _s(r.get("landslide_trigger"))]
        lt,tr=_trigger_type(cats[0] if cats else "",trigs[0] if trigs else "")
        # Preserve numeric source values; cross-row differences remain bounds, not averages.
        fvals=[_num(r.get("fatality_count")) for r in rs]
        ivals=[_num(r.get("injury_count")) for r in rs]
        fmin,fmax=_bounds(fvals); imin,imax=_bounds(ivals)
        if "fatalities_min" in override: fmin=override["fatalities_min"]; fmax=override.get("fatalities_max",fmin)
        if "injuries_min" in override: imin=override["injuries_min"]; imax=override.get("injuries_max",imin)
        fnote="; ".join(dict.fromkeys(v for v in fvals if v))
        if override.get("fatalities_note"):fnote=override["fatalities_note"]
        if oids==[35] and fvals and "8" in fvals:
            fmin=fmax="3"; fnote="GFLD/news source reports 3 deaths in Rutsiro; the 4TU/LIWEAR value 8 is the combined Rutsiro+Karongi report and is not assigned to this district-specific event. Original 8 preserved in 4TU_reconciliation.csv."
        if override.get("people_affected"): people_affected=override["people_affected"]
        else: people_affected=""
        houses_destroyed=""; houses_damaged=""; infrastructure=""
        desc="; ".join(dict.fromkeys(_s(r.get("event_description")) for r in rs if _s(r.get("event_description"))))
        if not fmin and re.search(r"\b(\d+)\s+(?:people|persons)\s+(?:were\s+)?killed\b",desc,re.I):
            fmin=fmax=re.search(r"\b(\d+)\s+(?:people|persons)\s+(?:were\s+)?killed\b",desc,re.I).group(1)
        if oids==[70]:
            houses_destroyed="39";houses_damaged="78";people_affected="631";fmin=fmax="0";imin=imax=""
            fnote="Zero fatalities explicitly stated by IGIHE; 39 homes destroyed, 78 damaged; 631 people in 117 affected families (395 sheltered, 236 not yet sheltered)."
            infrastructure="74 families/395 persons found accommodation; 43 families/236 persons still without accommodation."
        if oids==[65]:
            # Corrected date is in override; article webpage is JS-limited but its source metadata and workbook narrative corroborate date.
            pass
        if oids==[60]:
            # Source explicitly states nine commercial houses affected; the original workbook is the retrievable observation record.
            houses_damaged="9"; infrastructure="4TU source field says 'Eye observation'; no independently linked public article was supplied."
        if any(re.search(r"\broad\b|\bhighway\b|\bbridge\b|\bclassroom\b|\bhouse\b|\bhome\b",_s(r.get("event_description")),re.I) for r in rs):
            if not infrastructure: infrastructure="Source descriptions retained in 4TU_reconciliation.csv; impacts not reliably separable from narrative text."
        links=[_s(r.get("source_link")) for r in rs if _s(r.get("source_link")).startswith("http")]
        direct=[u for u in links if "doi.org/10.4121/" not in u and "doi.org/10.1007/s10346-018-1008-y" not in u]
        confidence="Medium" if direct or any("doi.org/10.1007/s10346-018-1008-y" in u for u in links) else "Low"
        if any("facebook.com" in u for u in direct):confidence="Low"
        rationale="Dated 4TU inventory row(s) with retrievable dataset DOI; direct event-specific report link present." if direct else "Dated 4TU inventory row(s) with retrievable dataset/publication source; no independently verified event-level link in the row."
        if oids==[1]:confidence="Low";rationale="4TU inventory reports a May 1988 Rubavu-area point with 10 fatalities, but this conflicts by district and impact with the original month-level Musanze event; kept separate and low-confidence pending primary record."
        if oids==[60]:confidence="Low";rationale="4TU workbook reports an eye observation with no external event URL; retained as a low-confidence inventory claim with the 4TU dataset as the retrievable document."
        notes=f"4TU workbook OID(s) {','.join(map(str,oids))}; original category={cats}; trigger={trigs}; accuracy={[_s(r.get('location_accuracy')) for r in rs]}. Source narrative preserved in 4TU_reconciliation.csv."
        if desc:notes+=" Event description: "+desc[:1000]
        if override.get("decision_note"):notes+=" | "+override["decision_note"]
        event={"event_id":eid,"date_start":ds,"date_end":de,"date_precision":precision,"event_name":name,"provinces":"|".join(provinces),"districts":"|".join(reported),"n_districts":len(reported),"primary_trigger":tr,"landslide_type":lt,"fatalities_min":fmin,"fatalities_max":fmax,"fatalities_note":fnote,"injuries_min":imin,"injuries_max":imax,"people_affected":people_affected,"people_displaced":"","houses_destroyed":houses_destroyed,"houses_damaged":houses_damaged,"infrastructure_notes":infrastructure,"event_confidence":confidence,"confidence_rationale":rationale,"source_ids":"|".join(dict.fromkeys([fourtu_sid]+[source_id(u) for u in links if source_id(u) in sources])),"notes":notes}
        # GFLD/literature source reconciliation is applied after this first-pass event creation.
        events.append(event);evmap[eid]=event
    # Add source records and construct mapped 4TU point sites.
    fourtu_site_ids=[]
    for _,r in df.iterrows():
        oid=int(r["OBJECTID"]); eid=oid_to_event.get(oid,""); ov=overrides.get(oid,{})
        url=_s(r.get("source_link")); url=url if url.startswith("http") else fourtu_url
        direct_sid=_add_source(sources,source_id,url,_s(r.get("event_title")) or _s(r.get("source_name")),_s(r.get("source_name")) or "4TU source citation",_iso(r.get("event_date")),"Not stated; source publisher terms apply" if url!=fourtu_url else "CC0 dataset record; source-row link absent", "Cited in the downloaded 4TU workbook; direct page access was checked for selected conflicts only" if url!=fourtu_url else "Downloaded 4TU workbook and README; source row is retrievable", "4TU source row with event details, location or impact.")
        lat=r.get("latitude");lon=r.get("longitude")
        lat=float(lat) if pd.notna(lat) and _s(lat) else None;lon=float(lon) if pd.notna(lon) and _s(lon) else None
        if oid==42 and lat is None and lon is None:
            # The workbook's geometry display is an explicit embedded point; its CRS is unstated.
            # The coordinate falls in Rwanda and overlays Rulindo when read as lon/lat.
            lat=-1.725002;lon=30.023501
        siteid=""; overlay=""; sector="";site_reason=site_exclusions.get(oid,"");dcheck="not_tested"
        text=" | ".join(_s(r.get(k)) for k in ["event_title","event_description","location_description"] if _s(r.get(k)))
        stated=_district_names(text,a2)
        if ov.get("districts"):stated=list(ov["districts"])
        if lat is not None and lon is not None:
            pt=Point(lon,lat); over=[str(x.ADM2_EN) for x in a2.itertuples() if x.geometry.covers(pt)]
            overlay="|".join(over); sector_over=[str(x.ADM3_EN) for x in a3.itertuples() if x.geometry.covers(pt)]
            acc,quality=_accuracy(r.get("location_accuracy"));sector_names=_sector_names(text,a3);sector=sector_names[0] if sector_names else ""
            mismatch_reason=""
            if not site_reason and eid:
                if not (-2.85<=lat<=-1.04 and 28.85<=lon<=30.91):site_reason="Coordinate falls outside Rwanda validation envelope."
                else:
                    if stated:
                        dcheck="pass" if any(x in over for x in stated) else "fail"
                        if dcheck=="fail": mismatch_reason=f"4TU source reports district(s) {stated}; coordinate overlays {over}; retained as a flagged inventory point."
                    else:dcheck="not_tested"
                    sector_mismatch=bool(sector and sector_over and sector not in sector_over)
                    if sector_mismatch:
                        mismatch_reason=(mismatch_reason+"; " if mismatch_reason else "")+f"4TU source sector {sector} differs from ADM3 overlay {sector_over}."
                    siteid=f"SITE-4TU-OID-{oid:02d}"
                    village,cell=_place_parts(text)
                    site={"site_id":siteid,"event_id":eid,"sector":sector,"cell":cell,"village":village,"place_description":f"4TU Rwanda inventory OID {oid}; source location: {_s(r.get('location_description'))}; original accuracy={_s(r.get('location_accuracy'))}; inventory point is not necessarily a slide-scar centroid.","latitude":lat,"longitude":lon,"geometry_type":"point","location_quality":quality,"accuracy_m":acc,"coordinate_method":"inventory","source_crs":"4TU Shape display, CRS unstated; interpreted as lon/lat after Rwanda extent and ADM2 checks","district_check":dcheck,"slope_check":sample_slope(lat,lon),"source_id":direct_sid,"_mismatch_explanation":mismatch_reason,"_sector_reported":bool(sector),"_sector_mismatch_explanation":f"Source sector {sector}; overlay sectors {sector_over}." if sector_mismatch else ""}
                    sites.append(site);geoms.append(pt);fourtu_site_ids.append(siteid)
            elif site_reason:
                pass
        status="excluded_not_admitted" if oid in exclusions else ("matched_to_existing_event" if oid in existing else "new_event_from_inventory_record")
        if site_reason and not siteid:site_status="suppressed_or_not_emitted"
        elif siteid:site_status="emitted"
        else:site_status="no_coordinate"
        override_note=ov.get("decision_note","")
        if oid in exclusions:override_note=exclusions[oid]
        if site_reason and oid not in site_exclusions:override_note=(override_note+"; " if override_note else "")+site_reason
        rowout={k:_s(r.get(k)) for k in df.columns if k is not None}
        rowout.update({"source_record_id":oid,"source_dataset_id":fourtu_sid,"normalized_event_id":eid,"match_status":status,"event_date_used":ov.get("date_start",_iso(r.get("event_date"))),"date_correction_note":override_note if ov else "","reported_districts_parsed":"|".join(stated),"boundary_districts":"|".join(over) if over else "","district_check":dcheck,"site_id_if_emitted":siteid,"site_status":site_status,"site_exclusion_reason":site_reason,"decision_note":override_note})
        new_rows.append(rowout)
        if eid and oid not in existing:
            cross.append({"source_system":"4TU","source_record_id":oid,"event_id":eid,"match_status":status,"matching_rule":"Row-level workbook and manual event adjudication","source_event_date":_iso(r.get("event_date")),"source_title":_s(r.get("event_title")),"source_location":_s(r.get("location_description")),"source_url":url,"decision_note":override_note})
    # Ensure source links from every mapped record are present on events.
    for oid,eid in oid_to_event.items():
        row=rowdict[oid]
        _add_event_source(evmap[eid],fourtu_url,source_id)
        u=_s(row.get("source_link"))
        if u.startswith("http"):_add_event_source(evmap[eid],u,source_id)
    # Direct independent RFE/RL source for the 2013 Rulindo event; the 4TU narrative has an erroneous January wording.
    rulindo_url="https://www.radiyoyacuvoa.com/a/inkangu-yahitanye-abantu-10-muri-rulindi/1655451.html"
    rulindo_event=next((e for e in events if e["event_id"]==oid_to_event.get(42)),None)
    if rulindo_event:
        voa_sid=_add_source(sources,source_id,rulindo_url,"Imvura y'Inkangu Yahitanye 10 mu karere ka Rulindo","Radio Free Europe/Radio Liberty - Kinyarwanda","2013-05-06","Publisher terms apply; article accessible","Opened; confirms May 3–5 2013 rainfall and ten deaths in Rulindo","Date range and total rain/landslide fatalities cross-check; casualty count is reconciled as 8–12 across 4TU-linked IGIHE and the 2018 paper table.")
        _add_event_source(rulindo_event,rulindo_url,source_id)
        rulindo_event["primary_trigger"]="rainfall"
        _add_event_note(rulindo_event,"4TU OID 42's embedded source narrative says January 2013, but its cited IGIHE article and RFE/RL source confirm 3–5 May 2013; date corrected from direct reporting. Eight of the ten deaths are specifically attributed to landslides by IGIHE; 2018 paper reports 12, retained as an upper source-specific bound.")
    # GFLD record-to-event mapping. The row-level export remains the authority for source values.
    gfpath=raw/"gfld_rwanda_2004_2017.geojson"; gf=json.loads(gfpath.read_text(encoding="utf-8"))
    fid_map={742:"RWA-LS-0077",743:oid_to_event[9],2217:oid_to_event[17],5005:oid_to_event[20],2218:"RWA-LS-0078",577:oid_to_event[21],2219:oid_to_event[25],2222:oid_to_event[28],744:"RWA-LS-0079",745:"RWA-LS-0080",746:oid_to_event[35],5006:"RWA-LS-0081",2220:"RWA-LS-0082",747:"RWA-LS-0083",2221:"RWA-LS-0084",2352:"RWA-LS-0011",5007:"RWA-LS-0011",2223:"RWA-LS-0013",2224:"RWA-LS-0085"}
    if len(gf.get("features",[]))!=19:raise ValueError("Expected 19 Rwanda GFLD records")
    gfld_rows=[]; gfld_site_ids=[]
    for feat in gf["features"]:
        p=feat["properties"];fid=int(p["FID"]);eid=fid_map[fid];x,y=feat["geometry"]["coordinates"]
        report_url=_s(p.get("Source_1"));report_url=report_url if report_url.startswith("http") else ""
        r_sid=_add_source(sources,source_id,report_url,f"GFLD-cited event report FID {fid}","Source cited in Global Fatal Landslide Database",str(p.get("Year","")),"Not stated; consult original publisher","Cited in downloaded public GFLD row; not individually opened unless noted in research findings","GFLD report URL linked to this Rwanda event record.") if report_url else ""
        _add_event_source(evmap[eid],gfld_url,source_id);_add_event_source(evmap[eid],report_url,source_id)
        loc=_s(p.get("Location_R")); expected=_district_names(loc,a2);pt=Point(float(x),float(y));over=[str(a.ADM2_EN) for a in a2.itertuples() if a.geometry.covers(pt)]
        mismatch=bool(expected and not any(n in over for n in expected))
        # Preserve broad point layers only when district-checkable; the known FID 2352 point is outside its reported Nemba location.
        emit=not (fid==2352)
        siteid=""
        if emit:
            siteid=f"SITE-GFLD-{fid}";dcheck="pass" if expected and not mismatch else ("fail" if expected and mismatch else "not_tested")
            detail=f"GFLD v2 feature FID {fid}; source location={loc}; original source point; precision field={p.get('Precision_')} (not interpreted as metres/accuracy); not a slide-scar survey coordinate."
            site={"site_id":siteid,"event_id":eid,"sector":(_sector_names(loc,a3) or [""])[0],"cell":"","village":"","place_description":detail,"latitude":float(y),"longitude":float(x),"geometry_type":"point","location_quality":"coarse","accuracy_m":"","coordinate_method":"published","source_crs":"WGS84 (GeoJSON source)","district_check":dcheck,"slope_check":sample_slope(float(y),float(x)),"source_id":r_sid or gfld_sid,"_mismatch_explanation":f"GFLD Location_R reports {expected}; point overlays {over}; point retained as a source record but district match fails." if mismatch else ""}
            sites.append(site);geoms.append(pt);gfld_site_ids.append(siteid)
        gfld_rows.append({"FID":fid,"event_id":eid,"event_date":datetime.utcfromtimestamp(int(p["Date"])/1000).date().isoformat() if p.get("Date") else "","trigger_raw":_s(p.get("Trigger_")),"fatalities_raw":_s(p.get("Fatalities")),"location_m":_s(p.get("Location_M")),"location_r":loc,"latitude":y,"longitude":x,"precision_raw_not_interpreted":_s(p.get("Precision_")),"source_1":report_url,"site_id_if_emitted":siteid,"site_emitted":emit,"boundary_districts":"|".join(over),"reported_districts":"|".join(expected),"district_check":"suppressed_known_mismatch" if fid==2352 else ("fail" if mismatch else ("pass" if expected else "not_tested")),"match_status":"matched_to_curated_or_4TU_event","decision_note":"FID 2352 is retained in crosswalk but point omitted: reported Nemba location conflicts with Kigali-area boundary overlay." if fid==2352 else (f"Source location {expected}; point overlay {over}." if mismatch else "Date and named location matched using source report and/or 4TU row; fatalities remain source-specific." if eid.startswith("RWA-LS-4TU-") else "Linked to an existing event based on date, district and source evidence; do not add GFLD fatalities to episode totals." )})
        cross.append({"source_system":"GFLD-v2","source_record_id":fid,"event_id":eid,"match_status":"matched_to_curated_or_4TU_event","matching_rule":"Event date ±3 days plus same district/location where applicable; see GFLD reconciliation","source_event_date":gfld_rows[-1]["event_date"],"source_title":_s(p.get("Report_1"))[:200],"source_location":loc,"source_url":report_url or gfld_url,"decision_note":gfld_rows[-1]["decision_note"]})
    # Reconcile documented GFLD date/casualty differences without averaging or adding counts.
    for oid, (d1,d2,f1,f2,reason) in {
        9:("2009-05-11","2009-05-13","8","8","4TU/New Times date 11 May versus GFLD date 13 May; exact same Gicumbi event and 8 deaths; keep date range."),
        17:("2010-06-07","2010-06-07","5","6","GFLD reports 5 deaths; 4TU/AllAfrica row reports 6; preserve source range."),
        20:("2011-05-05","2011-05-07","13","14","GFLD reports 13 deaths on May 5; 4TU and 2018 Table 1 report 14 for May/Nyabihu; keep date and fatality ranges."),
        28:("2011-12-06","2011-12-06","5","6","4TU/New Times reports 5 deaths; GFLD reports 6; preserve source range."),
    }.items():
        eid=oid_to_event[oid];e=evmap[eid];e["date_start"]=d1;e["date_end"]=d2;e["date_precision"]="range" if d1!=d2 else "day";e["fatalities_min"]=f1;e["fatalities_max"]=f2;_add_event_note(e,reason)
    # Rutsiro 2013: district-specific GFLD/news count overrides a combined 8-person 4TU tally.
    e=evmap[oid_to_event[35]];e["fatalities_min"]="3";e["fatalities_max"]="3";_add_event_note(e,"GFLD/AllAfrica report says 3 died in Rutsiro; 4TU value 8 summarizes separate Rutsiro+Karongi incidents and is not assigned to this district-specific row.")
    e=evmap["RWA-LS-0013"];e["date_start"]="2016-12-06";e["date_end"]="2016-12-07";e["date_precision"]="range";_add_event_note(e,"RNP/4TU date 6 Dec and GFLD date 7 Dec for same Gasabo event; date range retained.")
    gfld_df=pd.DataFrame(gfld_rows);tables["gfld_reconciliation"]=gfld_df

    # GLIDE: preserve all 29 Rwanda records, including unrelated hazards.
    glide=pd.read_csv(raw/"rwa_glide_events.csv",dtype=str,keep_default_na=False)
    glide_map={"LS-2010-000071-RWA":"RWA-LS-0006","FL-2012-000067-RWA":"RWA-LS-0007","FL-2015-000042-RWA":"RWA-LS-0009","FL-2018-000029-RWA":"RWA-LS-0014","FL-2021-000049-RWA":"RWA-LS-0021","FL-2023-000064-RWA":"RWA-LS-0022","FL-2011-000051-RWA":oid_to_event[20]}
    glide_rows=[]
    for _,r in glide.iterrows():
        gid=_s(r.get("glidenumber"));comment=_s(r.get("comments"));relevant=bool(re.search(r"land\s*slide|mudslide|landslide|slope failure|debris flow",(gid+" "+comment).casefold()))
        eid=glide_map.get(gid,"");status="matched" if eid else ("unmatched landslide-relevant GLIDE record" if relevant else "not a landslide source record")
        year=int(_num(r.get("year")) or 0);month=int(_num(r.get("month")) or 0);day=int(_num(r.get("day")) or 0)
        ds=f"{year:04d}-{month:02d}-{day:02d}" if year and month and day else (f"{year:04d}-{month:02d}" if year and month else str(year or ""))
        if eid:
            _add_event_source(evmap[eid],glide_url,source_id)
            if gid=="FL-2011-000051-RWA":_add_event_note(evmap[eid],"GLIDE record spans 25 Apr and mentions severe weather on 5 May in Nyabihu; used only as contextual source for the 5–7 May source event, not as a point location.")
        loc=_s(r.get("location"));status_note=""
        if gid=="FL-2007-000159-RWA":status_note="Broad flood record dated 14 Sep; 4TU/NASA event is dated 19 Sep (outside ±3-day rule) and districts/source hazard differ; not merged."
        elif gid=="FL-2019-000170-RWA":status_note="GLIDE flood record lists Ngororero/Gisagara/Rusizi on 6 Dec; the Musanze landslide is 5 Dec, with no same-district match; not merged."
        elif not eid and relevant:status_note="No source/event match satisfying date and location rule; retained as unmerged candidate."
        elif not eid:status_note="Unrelated GLIDE disaster type or no explicit landslide in comments; retained as excluded reconciliation row."
        glide_rows.append({"glide_id":gid,"docid":_s(r.get("docid")),"event_code":_s(r.get("event")),"event_name":_s(r.get("event_name")),"source_date_raw":"-".join([_s(r.get("year")),_s(r.get("month")),_s(r.get("day"))]),"source_date_normalized":ds,"location_raw":loc,"latitude_raw":_s(r.get("latitude")),"longitude_raw":_s(r.get("longitude")),"shape_type":_s(r.get("shape_type")),"fatalities_raw":_s(r.get("killed")),"injuries_raw":_s(r.get("injured")),"homeless_raw":_s(r.get("homeless")),"affected_raw":_s(r.get("affected")),"comments_raw":comment,"source_name_raw":_s(r.get("source")),"landslide_relevant":relevant,"matched_event_id":eid,"match_status":status,"dataset_source_id":glide_sid,"decision_note":status_note})
        cross.append({"source_system":"GLIDE","source_record_id":gid,"event_id":eid,"match_status":status,"matching_rule":"Manual GLIDE ID/date/district/source narrative match; all 29 records retained","source_event_date":ds,"source_title":_s(r.get("event_name")),"source_location":loc,"source_url":glide_url,"decision_note":status_note})
    tables["glide_reconciliation"]=pd.DataFrame(glide_rows)

    # NASA Rwanda catalog crosswalk (the builder separately emits valid non-reused points).
    nasa=pd.read_csv(raw/"nasa_glc_export_rows.csv",low_memory=False)
    rwa=nasa[nasa["country_code"].astype(str).str.upper().eq("RW")]
    nasa_map={272:"RWA-LS-0005",273:"RWA-LS-0005",1593:"RWA-LS-0006",4834:"RWA-LS-0008",7716:"RWA-LS-0011",7717:"RWA-LS-0011"}
    nasa_rows=[]
    for _,r in rwa.iterrows():
        rid=int(r["event_id"]);eid=nasa_map[rid];siteid=f"SITE-NASA-GLC-{rid}";emitted=any(s["site_id"]==siteid for s in sites)
        note=("50 km reference point overlaps the reused Rubavu catalog location; suppressed from sites." if rid==1593 else "Catalog point fails source-district overlay (NASA source label Nyabihu; boundary overlay Ngororero); explicitly retained as a flagged source point." if rid==273 else "NASA snapshot row linked by event ID/date and source narrative; location accuracy retained as catalog metadata.")
        _add_event_source(evmap[eid],nasa_url,source_id)
        nasa_rows.append({"NASA_event_id":rid,"event_id":eid,"event_date":_s(r.get("event_date")),"event_title":_s(r.get("title")),"location_description":_s(r.get("location_description")),"latitude":r.get("latitude"),"longitude":r.get("longitude"),"location_accuracy":_s(r.get("location_accuracy")),"source_url":nasa_url,"site_id_if_emitted":siteid if emitted else "","site_emitted":emitted,"match_status":"matched_to_event","decision_note":note})
        cross.append({"source_system":"NASA-GLC","source_record_id":rid,"event_id":eid,"match_status":"matched_to_existing_event","matching_rule":"NASA GLC event ID/date and cited event narrative","source_event_date":_s(r.get("event_date")),"source_title":_s(r.get("title")),"source_location":_s(r.get("location_description")),"source_url":nasa_url,"decision_note":note})
    if len(nasa_rows)!=6:raise ValueError("NASA crosswalk expected six Rwanda rows")
    tables["nasa_rwanda_reconciliation"]=pd.DataFrame(nasa_rows)

    # Table 1 claims. Values are source-specific; only exact-district/date matches are linked.
    lit=[
      ("2017-04","Muhanga",6,27,"55 houses destroyed","RWA-LS-0092","month-level candidate; no exact day/site"),
      ("2016-05","Gakenke",35,26,"67 roads and 29 bridges","RWA-LS-0011","month-level claim; not added to episode total"),
      ("2016-05","Muhanga",8,13,"5 roads damaged","RWA-LS-0090","month-level district candidate; possible wider-May overlap unresolved"),
      ("2016-05","Rubavu",4,5,"2 bridges destroyed","RWA-LS-0091","month-level district candidate; possible wider-May overlap unresolved"),
      ("2016-05","Ngororero",13,27,"4 classrooms destroyed","RWA-LS-0011","month-level claim; not added to episode total"),
      ("2015-04","Ngororero",10,13,"24 houses destroyed","RWA-LS-0089","month-level candidate; different district from Apr 3 event"),
      ("2013-03","Nyarugenge",4,3,"87 houses destroyed","RWA-LS-0086","month-level candidate; no exact day/site"),
      ("2013-04","Gasabo",3,7,"56 houses destroyed",oid_to_event[33],"month-level claim linked to Apr 15 4TU Gasabo row; casualty differences kept source-specific"),
      ("2013-05","Rulindo",12,7,"79 houses destroyed",oid_to_event[42],"month-level claim linked to 3–5 May Rulindo rain/landslide episode; casualty and scope conflict preserved"),
      ("2013-05","Rutsiro",5,2,"22 houses destroyed","RWA-LS-0088","month-level candidate; separate from April Rutsiro event"),
      ("2011-05","Nyabihu",14,11,"300 houses destroyed",oid_to_event[20],"month-level claim cross-supported by GFLD May 5 and 4TU May 7; event keeps May 5–7 range and 13–14 deaths")]
    litrows=[]
    for period,dist,deaths,inj,damage,eid,note in lit:
        start=f"{period}-01"; end=(pd.Period(period,freq="M").end_time.date().isoformat())
        litrows.append({"source_table":"2018 susceptibility paper Table 1","source_period":period,"date_start":start,"date_end":end,"date_precision":"month","district":dist,"fatalities":deaths,"injuries":inj,"other_damage":damage,"source_url":paper_url,"source_id":paper_sid,"matched_event_id":eid,"match_status":"matched_source_claim" if eid else "unmatched","decision_note":note})
        _add_event_source(evmap[eid],paper_url,source_id)
        _add_event_note(evmap[eid],f"2018 paper Table 1 source-specific month-level claim: {period} {dist}, {deaths} deaths, {inj} injured, {damage}; not summed with other source totals.")
        cross.append({"source_system":"2018-paper-Table-1","source_record_id":f"{period}-{dist}","event_id":eid,"match_status":"matched_source_claim","matching_rule":"Month/district match or explicit month-level candidate retained at month precision","source_event_date":period,"source_title":"Latest main disasters caused by landslides in Rwanda, Table 1","source_location":dist,"source_url":paper_url,"decision_note":note})
    tables["literature_claims"]=pd.DataFrame(litrows)

    # Source-specific record crosswalk and 4TU audit table.
    tables["4tu_reconciliation"]=pd.DataFrame(new_rows)
    tables["source_event_crosswalk"]=pd.DataFrame(cross)
    # Record a transparent summary for QA/report generation.
    summary={"4tu_rows":len(df),"4tu_existing_matches":len(existing),"4tu_new_event_groups":len(groups),"4tu_excluded_rows":len(exclusions),"gfld_rows":len(gfld_rows),"glide_rows":len(glide_rows),"nasa_rwanda_rows":len(nasa_rows),"literature_table_claims":len(litrows),"gflD_sites_emitted":len(gfld_site_ids),"4tu_sites_emitted":len(fourtu_site_ids)}
    (root/"AUXILIARY_RECONCILIATION_SUMMARY.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    return tables
