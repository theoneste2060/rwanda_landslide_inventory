# Rwanda landslide inventory — v2

## Purpose and scope

This release audits and expands the supplied Rwanda landslide inventory. It separates reported disaster episodes (`events.csv`) from mapped point/polygon contexts (`sites.csv`), registers source URLs and source-specific access/licensing notes (`sources.csv`), and retains row-level crosswalks for the 4TU, GLIDE, NASA Global Landslide Catalog, Global Fatal Landslide Database and a peer-reviewed event table.

The compiled tables contain **88 event records, 1,071 site records and 127 source records** (research snapshot through 2026-10-17). The site table has **577 rows with explicit latitude/longitude values**; polygons are represented separately and many are paired with derived centroids. These are source/reporting records, not a complete census of Rwanda landslides or a risk model.

## Main files

- `events.csv`, `sites.csv`, `sources.csv`: normalized core tables.
- `rwanda_landslide_v2.xlsx`: workbook with core tables, README, district/annual summaries, spatial QA, UNOSAT audit and source-reconciliation sheets.
- `sites.geojson`, `sites.kml`, `events.geojson`, `rwanda_landslide_v2.gpkg`: GIS deliverables in WGS84 (EPSG:4326). The event GeoJSON links site IDs and collects linked geometries; the GeoPackage includes events, sites and NISR/OCHA administrative layers.
- `rwanda_landslide_locations.png`, `annual_event_counts.png`, `annual_event_counts.csv`, `district_event_counts_deaths.csv`: visualization and reporting summaries. These show *recorded reporting*, not normalized hazard or risk.
- `site_validation.csv`, `near_duplicate_coordinates.csv`, `unosat_layer_audit.json`, `TASK1_AUDIT.json`, `QA_REPORT.md`: QA evidence and unresolved cases.
- `4tu_reconciliation.csv`, `gfld_reconciliation.csv`, `glide_reconciliation.csv`, `nasa_rwanda_reconciliation.csv`, `literature_claims.csv`, `source_event_crosswalk.csv`: retained source-row details and match decisions.
- `raw_sources/`: one copy of downloaded raw inputs; see its `README_raw_sources.txt`.
- `scripts/`: reproducible generation and automated tests.

## Rebuild

Use Python 3.10+ and install dependencies in `requirements.txt`. From this directory run:

```bash
python3 scripts/build_v2.py
python3 scripts/validate_v2.py
```

The build reads the preserved original inventory/source-log snapshots and raw-source snapshots. It regenerates normalized tables, spatial exports, the map and workbook. See `CHANGELOG.md` for the corrections and `DATA_DICTIONARY.md` for fields and controlled values.

## Important interpretation limits

- Event confidence and coordinate quality are separate. A point may locate a broad event area and is not necessarily a landslide scar.
- All **494 polygons** from the 2018 Rwanda component of Zenodo 7198322 are retained with 494 paired centroids. The inventory combines landslides and flash floods and has no feature-level hazard class; none is asserted as a confirmed landslide scar. These 988 site rows are linked to the May 2018 Karongi cluster only as mixed-inventory mapping context.
- The 2023 UNOSAT `LandslideExtent`-named feature is field-unvalidated and its attributes classify it as flood water/new water. It is not promoted to a landslide polygon. Six assessment-area centers remain site contexts linked to the 2023 combined episode, not six extra events.
- Coarse catalog points are retained only when they add usable traceability. A known 2010 NASA point reused near the 2018 Rubavu reference point is omitted from mapped sites.
- Multi-district casualty totals are not allocated to districts. Source disagreements are retained as ranges/notes; totals are not averaged or summed across duplicate source reports.
- Boundary mismatches, including 13 district overlays and 3 explicit sector overlays, are listed and explained in `site_validation.csv`. Do not silently move a point based on an overlay.
- Copernicus GLO-30 slope is a point-scale screening based on a 3×3 central difference, not a landslide susceptibility analysis or scar validation. Near-flat results should be reviewed; imagery was not independently interpreted in this compilation.
- Boundary package metadata is NISR-sourced through OCHA/HDX and notes that the boundary establishment date is unknown and review is stale. Administrative results are a consistency screen, not proof of a site name.
- The report is not normalized by population, exposure, reporting effort or observation completeness.

## Citation and rights

See `CITATION.cff` and `LICENSE.md`. No blanket open license is claimed for the compiled derivative because source terms vary. Attribute source data as listed in `sources.csv` and comply with the linked providers' terms.
