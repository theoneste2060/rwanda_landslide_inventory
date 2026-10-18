#!/usr/bin/env python3
"""Build v2 evidence table from v1 plus verified source records.

Ratings are source-verification grades, not an effect-size or study-bias grade:
1 = attempted source could not be opened/verified; 2 = citation/metadata only;
3 = authoritative abstract/partial primary source or record verified; 4 = full
primary report/article or public dataset schema directly inspected. Dedup key is
DOI when available, otherwise normalized URL. The source review does not retrieve
restricted material or infer unavailable fields.
"""
import csv, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/'input'/'evidence_table_v1.csv'
OUT=ROOT/'evidence_table.csv'
FIELDS=['topic','citation','doi_or_url','region','data_size','method','validation_design','key_metric','caveat','relevance','quality_rating_1to4','quality_rationale','source_type','verification_status']
DOI_RE=re.compile(r'10\.\d{4,9}/[^\s,;]+',re.I)

def clean_doi(s):
    if not s:return ''
    m=DOI_RE.search(s)
    if not m:return ''
    d=m.group(0).strip().rstrip('.,)]}')
    return d.lower().replace('%2f','/')

def key(row):
    d=clean_doi(row.get('doi_or_url',''))
    if d:return 'doi:'+d
    u=(row.get('doi_or_url','') or '').strip().lower().rstrip('/')
    return 'url:'+u

def old_grade(s):
    t=(s or '').lower()
    if any(x in t for x in ['not verifiable','unverified','could not be verified','not verified','inaccessible','not accessible','not established']):
        return 2
    if any(x in t for x in ['full text read','full article','full article text','full text','full publisher','full report','full article text read','open full','data schema directly','record/api']):
        return 4
    if any(x in t for x in ['abstract read','publisher landing','metadata','abstract','bibliographic','citation record']):
        return 3
    return 3

def grade_label(g):
    return {1:'Source could not be opened or verified; do not rely on unverified claims.',
            2:'Only citation/metadata or an inaccessible full-text route was verified; quantitative details are not inferred.',
            3:'An authoritative publisher/registry page or partial primary-source text was opened; claims are limited to visible content.',
            4:'Full primary source or public dataset record/schema was inspected directly; cited details are visible in the source.'}[int(g)]

def canon(row):
    x={k:(row.get(k,'') or '').strip() for k in FIELDS if k not in ('quality_rating_1to4','quality_rationale','verification_status')}
    q=row.get('quality_rating','')
    g=old_grade(q)
    x['quality_rating_1to4']=str(g)
    x['quality_rationale']=grade_label(g)
    x['verification_status']='Reviewed in prior evidence table; fixed grade maps to the documented v2 scale.'
    # Use the DOI for two existing publisher URL rows when DOI is deterministically known.
    if 'nhess.copernicus.org/articles/19/775/2019' in x['doi_or_url']:
        x['doi_or_url']='https://doi.org/10.5194/nhess-19-775-2019'
    return x

with INPUT.open(encoding='utf-8-sig',newline='') as f:
    old=[canon(r) for r in csv.DictReader(f)]

# Exact primary records newly verified in the present source review. The citation
# strings are unique; one distinct DOI/URL is retained per dataset/article.
extra=[
 dict(topic='regional_inventory',citation='Depicker, A., et al. (2021). Interactions between deforestation, landscape rejuvenation, and shallow landslides in the North Tanganyika–Kivu Rift region, Africa. Earth Surface Dynamics, 9, 445–462.',doi_or_url='https://doi.org/10.5194/esurf-9-445-2021',region='North Tanganyika–Kivu Rift (DRC, Rwanda, Burundi); western Rwanda subset used by REMA',data_size='Public Zenodo record contains 7,944 point geometries; the exact 2,544-point REMA input version is not independently verified as identical.',method='Multi-temporal very-high-resolution image interpretation; shallow failures represented by initiation points; point file fields: ID, area, dep_area, Year; geometry supplies coordinates.',validation_design='Not an EWS predictive validation study; inventory validation/completeness limits apply.',key_metric='2021 Nature Sustainability paper directly links this inventory to Zenodo record 5027004. Public file covers 2000–2019 and is CC BY 4.0.',caveat='No exact image-date pair or explicit type field in the public point table. Semantics/units for area and dep_area require author confirmation. Do not assume exact equivalence to REMA’s 2,544-point input.',relevance='Direct publicly accessible regional inventory candidate for susceptibility; insufficient day-level date precision for rainfall-trigger calibration.',quality_rating_1to4='4',quality_rationale=grade_label(4),source_type='Peer-reviewed open article plus official public dataset record/API and schema inspected.',verification_status='Publisher full text and official Zenodo record/file schema opened; open shapefile inspected.'),
 dict(topic='regional_inventory',citation='Depicker, A., et al. (2020). The added value of a regional landslide susceptibility assessment: the western branch of the East African Rift. Geomorphology, 353, 106886.',doi_or_url='https://doi.org/10.1016/j.geomorph.2019.106886',region='Western branch of East African Rift; Lake Kivu region',data_size='The paper describes an earlier 6,446-landslide catalogue; exact overlap with the later 7,944-point release not established.',method='Regional susceptibility assessment using an expanded landslide catalogue and conditioning factors.',validation_design='Study-specific validation; do not transfer its score to operational EWS.',key_metric='Publisher article and bibliographic record verified; a separately reusable data file/license for this earlier version was not established in this review.',caveat='Do not label the 6,446 catalogue as identical to the 7,944-point Zenodo release or the REMA 2,544 subset without a version crosswalk.',relevance='Shows a regional predecessor and the need to record inventory version/provenance.',quality_rating_1to4='3',quality_rationale=grade_label(3),source_type='Peer-reviewed publisher page and article text opened; complete inventory release/license not verified.',verification_status='Publisher source opened; data-version mapping remains unverified.'),
 dict(topic='regional_inventory',citation='Dewitte, O., et al. (2021). Spatial-temporal landslide inventories around Lake Kivu, DRC, Rwanda and Burundi. Landslides (article cited by the REMA report; DOI record).',doi_or_url='https://doi.org/10.1007/s10346-020-01452-0',region='Lake Kivu and neighbouring DRC, Rwanda, Burundi',data_size='Multi-temporal regional catalogue; the publication describes thousands of mapped features. Exact version/row count differs by inventory extract.',method='Multi-temporal Google Earth imagery and manually identified source/initiating locations; image-bracketed occurrence times.',validation_design='Inventory paper, not a prospective warning validation.',key_metric='Published source and the later Nature Sustainability data-availability statement point to the 7,944-point Zenodo inventory.',caveat='Point-level file has year only, not the image-date pair; a point geometry cannot encode landslide polygons/type unless separate data are acquired.',relevance='Useful provenance for the open regional point layer; request event polygons, image pairs, and attribute definitions if needed.',quality_rating_1to4='3',quality_rationale=grade_label(3),source_type='Peer-reviewed publisher page opened; linked public release checked through the later source paper.',verification_status='Publisher record and associated data citation verified; the source layer version crosswalk is unresolved.'),
 dict(topic='rwanda_report',citation='Rwanda Environment Management Authority (2022). Landslide Risks Assessment and Mitigation Report (Report 2).',doi_or_url='https://www.rema.gov.rw/fileadmin/user_upload/REMA/Publications/Reports/Report_2_-_Landslide_Risks_Assessment_and_Mitigation_Report_3.pdf',region='Four Rwanda sub-catchments and a western-Rwanda regional shallow-landslide inventory',data_size='22 old and 5 recent deep-seated landslides in four catchments; separate regional shallow-initiation training set of 2,544 mapped observations.',method='Visual multi-temporal Google Earth inventory; logistic susceptibility mapping; source-area hazard rates; desktop exposure; conceptual mitigation options.',validation_design='Random 10-fold cross-validation only for susceptibility; no spatial, temporal, external or prospective validation described.',key_metric='30 m logistic AUC 91.1% with lithology and 88.8% without lithology; selected model is described as the latter.',caveat='Random background points, interval-censored dates, mapped-inventory under-detection, no cited spatial CV, no direct vulnerability dataset, and assumption-based mitigation.',relevance='Core source for exact model/exposure/mitigation methods and limits; PDF page-numbered extraction accompanies this record.',quality_rating_1to4='4',quality_rationale=grade_label(4),source_type='Official REMA-hosted full report; all 68 pages extracted and tables/figures visually inspected.',verification_status='Original official PDF opened; numerical tables/figures checked against rendered pages.'),
 dict(topic='inventory_context',citation='Monsieurs, E., et al. (2018). Landslide inventory for hazard assessment in a data-poor context: a regional-scale approach in a tropical African environment. Landslides, 15, 2195–2209.',doi_or_url='https://doi.org/10.1007/s10346-018-1008-y',region='Western branch East African Rift / Kivu region',data_size='LIWEAR: 143 events with known location and date, 1968–2016, per publisher abstract.',method='Regional inventory assembly and event assessment in a data-poor setting.',validation_design='Not a prospective forecast validation.',key_metric='Publisher page describes the 143-event LIWEAR catalogue; supplementary material is presented as authorized-user access.',caveat='No unrestricted event-level spatial CSV/shapefile or reuse license was verified; do not bypass the publisher restriction.',relevance='Potential regional event catalogue; request permission/data dictionary and reuse terms from the authors/custodians.',quality_rating_1to4='3',quality_rationale=grade_label(3),source_type='Publisher landing page opened; supplement not retrieved.',verification_status='Abstract/metadata verified; event-level supplement access not obtained.'),
 dict(topic='rwanda_rain_thresholds',citation='Monsieurs, E., Dewitte, O. & Demoulin, A. (2019). A susceptibility-based rainfall threshold approach for landslide occurrence in the western branch of the East African Rift. Natural Hazards and Earth System Sciences, 19, 775–797.',doi_or_url='https://doi.org/10.5194/nhess-19-775-2019',region='Western branch East African Rift, DRC/Rwanda',data_size='174 events in 2001–2018; 29 mining events excluded and 143 used for threshold calibration.',method='Satellite-derived antecedent rainfall function coupled with landslide susceptibility; bootstrap uncertainty.',validation_design='Study-specific historical catalogue evaluation; not independent prospective district-level validation.',key_metric='Full NHESS article is openly accessible under CC BY 4.0; supplement is linked, but no standalone row-level event-coordinate file was verified here.',caveat='Published thresholds are region-specific; catalogue completeness and event/landslide definitions matter; do not assume row-level event data are openly reusable.',relevance='Method precedent for susceptibility-dependent rainfall thresholds; supports a cautious, spatially explicit design.',quality_rating_1to4='4',quality_rationale=grade_label(4),source_type='Peer-reviewed open NHESS full article and supplement route opened.',verification_status='Full article opened; article license verified; standalone event-layer status unresolved.'),
 dict(topic='historical_risk_data',citation='Depicker, A., et al. (2021). Historical dynamics of landslide risk from population and forest-cover changes in the Kivu Rift. Nature Sustainability, 4, 965–974.',doi_or_url='https://doi.org/10.1038/s41893-021-00757-9',region='Kivu Rift: DRC, Rwanda and Burundi',data_size='Underlying landslide inventory is explicitly linked to Zenodo 5027004; figure-source spreadsheet is separately linked to Figshare 14838825.',method='Historical risk analysis using forest-cover, population, susceptibility and landslide data.',validation_design='Historical risk analysis; not a day-level landslide-warning validation.',key_metric='The paper resolves the REMA report’s former “in review” reference as a published article and its Data Availability statement names public sources.',caveat='The separate Figshare Excel file contains figure-source data, not the full geospatial landslide catalogue.',relevance='Proves the existence of a public post-review inventory release and provides author contact routes.',quality_rating_1to4='4',quality_rationale=grade_label(4),source_type='Peer-reviewed Nature Sustainability publisher full text and data statement opened.',verification_status='Correct DOI/article and direct data-availability statement verified.'),
 dict(topic='open_figure_data',citation='Depicker, A., et al. (2021). Figure data for “Historical dynamics of landslide risk from population and forest-cover changes in the Kivu Rift”. Figshare record.',doi_or_url='https://doi.org/10.6084/m9.figshare.14838825.v1',region='Kivu Rift',data_size='One Excel workbook containing raw figure data for Figs. 3–5.',method='Figure-source data repository.',validation_design='Not applicable.',key_metric='Figshare API confirms CC BY 4.0.',caveat='This is not the individual landslide point/polygon layer.',relevance='Open reproducibility supplement for figures, distinct from the spatial inventory.',quality_rating_1to4='4',quality_rationale=grade_label(4),source_type='Official Figshare record and API metadata opened.',verification_status='Record, file name, DOI and CC BY 4.0 license verified.'),
 dict(topic='spatial_validation',citation='Roberts, D. R., et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. Ecography, 40, 913–929.',doi_or_url='https://doi.org/10.1111/ecog.02881',region='Methods; ecological/spatial data',data_size='Review and methodological simulations/examples.',method='Compares validation strategies for structured observations and prediction targets.',validation_design='Methodological review.',key_metric='Random folds can underestimate error when dependence leaks across train/test; blocking must match the intended prediction target.',caveat='No transferable numeric “AUC drop” for Rwanda; choose block scale from sampling geometry and deployment target.',relevance='Motivates spatially blocked validation of the REMA model.',quality_rating_1to4='4',quality_rationale=grade_label(4),source_type='Peer-reviewed publisher full text opened.',verification_status='Publisher primary article text opened.'),
 dict(topic='spatial_validation',citation='Rolain, T., et al. (2025). Random cross-validation produces biased assessment of machine learning performance in regional landslide susceptibility prediction. Remote Sensing, 17(2), 213.',doi_or_url='https://doi.org/10.3390/rs17020213',region='Landslide susceptibility; study-specific region',data_size='Study-specific case study; not Rwanda.',method='Compares random and spatial cross-validation for machine-learning landslide susceptibility prediction.',validation_design='Random versus spatial validation.',key_metric='Study reports random CV can overstate performance and spatial estimates can vary more; its effect size is not transferable to Rwanda.',caveat='Do not use its reported score gap as a correction factor for the REMA AUC.',relevance='Recent landslide-specific evidence for spatially separated testing.',quality_rating_1to4='4',quality_rationale=grade_label(4),source_type='Peer-reviewed MDPI full article opened.',verification_status='Publisher full article and methods/results sections opened.'),
 dict(topic='open_event_dataset',citation='Uwihirwe, J. (n.d.). Data underlying the research of Integration of observed and model derived groundwater levels in landslide threshold models in Rwanda. 4TU.ResearchData workbook snapshot.',doi_or_url='https://github.com/theoneste2060/rwanda_landslide_inventory/tree/main/datasets_v2/repo_readonly/v2/raw_sources/4tu_rwanda_inventory.xlsx',region='Rwanda',data_size='70 event-source rows; README describes the landslide inventory as 2006–2021; one worksheet with 35 columns.',method='Compiled event catalogue with event date/time, location, location accuracy, landslide category/trigger/size, impacts and source links; no mapped initiation polygons or image-date brackets.',validation_design='Not a predictive validation study; source rows require event/duplicate adjudication.',key_metric='Workbook and README inspected; the upstream raw-source manifest identifies the 4TU dataset record as CC0.',caveat='Coordinate accuracy varies and raw event-date formats/precision are heterogeneous; the public workbook is an upstream source snapshot, not a verified independent 70-storm sample.',relevance='Candidate rainfall-event catalogue after row-level date and location review; links provenance for records in the user’s 88-event table.',quality_rating_1to4='4',quality_rationale=grade_label(4),source_type='Workbook and bundled README/schema inspected directly; upstream repository manifest records access/license note.',verification_status='File fields and 70 source rows confirmed from packaged workbook; exact official 4TU record locator was not established in this review.'),
 dict(topic='mixed_hazard_inventory',citation='Deijns et al. (2022). SAR-timed geomorphic-hazard event inventories, Rwanda component. Zenodo dataset record 7198322.',doi_or_url='https://doi.org/10.5281/zenodo.7198322',region='Karongi, Rwanda (one of four regional African event inventories)',data_size='494 Rwanda polygon features in inspected shapefile; the Zenodo record describes around 2,500 mapped landslides and flash floods across all four regions.',method='SAR-informed geomorphic-hazard inventory; Rwanda layer is a polygon shapefile with id, Area, LandUsemaj, Aspectmean, Slopemean, ASC_MASKma, DSC_MASKma and Aspect fields.',validation_design='Inventory product; not a prospective warning validation.',key_metric='Official Zenodo API verifies public record and CC BY 4.0 license; the Rwanda polygon layer is in WGS 84 / UTM 35S.',caveat='No event date, image bracket, point-of-initiation field, or explicit per-feature landslide/flash-flood class field in the inspected DBF; not safe as a pure landslide label layer.',relevance='Potential ancillary spatial evidence only after feature-class and event-time reconciliation; not directly usable for rainfall thresholds.',quality_rating_1to4='4',quality_rationale=grade_label(4),source_type='Official Zenodo metadata/API plus public Rwanda shapefile schema inspection.',verification_status='Record, CC BY 4.0 license, file listing and inspected shapefile schema verified.'),
]

# Canonicalize old source duplicates by DOI/URL; for same-key items keep the most complete record.
by={}; removed=[]
for r in old:
    k=key(r)
    score=(int(r.get('quality_rating_1to4') or 0),sum(bool(r.get(f,'')) for f in FIELDS),sum(len(r.get(f,'') or '') for f in FIELDS))
    if k in by:
        prev=by[k]; pscore=(int(prev.get('quality_rating_1to4') or 0),sum(bool(prev.get(f,'')) for f in FIELDS),sum(len(prev.get(f,'') or '') for f in FIELDS))
        if score>pscore: removed.append(prev); by[k]=r
        else: removed.append(r)
    else: by[k]=r

# Update the old Monsieurs 2019 URL row to its canonical DOI, and avoid adding any duplicate.
# Add supplemental rows only when neither DOI nor exact citation title is already represented.
for r in extra:
    k=key(r)
    title=(r['citation'].split('. ',1)[-1]).lower()
    match=next((kk for kk,v in by.items() if kk==k or (title[:45] and title[:45] in (v.get('citation','')+' '+v.get('doi_or_url','')).lower())),None)
    if match:
        # Keep the better verified row and merge any new canonical locator/status.
        oldr=by[match]
        if int(r['quality_rating_1to4'])>int(oldr.get('quality_rating_1to4') or 0) or match==k:
            by.pop(match,None);by[k]=r
        continue
    by[k]=r

rows=list(by.values())
rows.sort(key=lambda r:(r['topic'],r['citation'].lower()))
with OUT.open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction='ignore');w.writeheader();w.writerows(rows)
with (ROOT/'duplicate_doi_review.csv').open('w',encoding='utf-8-sig',newline='') as f:
    dw=csv.DictWriter(f,fieldnames=['citation','doi_or_url','quality_rating_1to4','reason'],extrasaction='ignore');dw.writeheader()
    for r in removed: dw.writerow({**r,'reason':'Duplicate DOI/URL; canonical row retained once.'})
    dw.writerow({'citation':'Upstream source-registry aliases depicker_2020a and depicker_2020b',
                 'doi_or_url':'https://doi.org/10.1016/j.geomorph.2019.106886',
                 'quality_rating_1to4':'3',
                 'reason':'Both aliases resolve to the same Geomorphology article and 6,446-catalogue description; retained once in the evidence table. No separate 2020a/2020b data assets were verified.'})
print(f'Wrote {OUT}: {len(rows)} unique DOI/URL rows; removed {len(removed)} duplicate rows; added/updated primary source records.')
print(f'Wrote {ROOT/"duplicate_doi_review.csv"}')
