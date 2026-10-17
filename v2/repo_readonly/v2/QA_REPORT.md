# QA report — Rwanda landslide inventory v2

**Research/build cut-off:** 2026-10-17. **Automated build result:** 0 errors. Run `python3 scripts/build_v2.py` and `python3 scripts/validate_v2.py` to reproduce/check outputs.

## Counts and input audit

| Measure | Result |
|---|---:|
| Original inventory rows | 30 |
| Original CSV header width | 25 fields |
| Original data-row widths | 30/30 have 25 fields |
| Confirmed row with field/citation alignment defect | 1 (`RWA-LS-0006`) |
| Invalid confidence/source alignment records after strict audit | 1, repaired in v2 |
| Compiled event records | 88 |
| Site/geometry records | 1,071 |
| Site rows with explicit latitude/longitude | 577 |
| Registered source records | 127 |
| Core build validation errors | 0 |

The 88 events comprise the 23-row first-pass episode table, 49 separately adjudicated 4TU event groups, and 16 independently sourced supplemental candidate records. This count is a compiled row count; month-level source claims and partially localized reports remain distinct when evidence does not prove they are the same incident.

Site geometry counts: 494 source polygons + 494 derived polygon centroids from the 2018 mixed-hazard file; 77 other point sites; and 6 UNOSAT assessment-area centers. Total = 1,071. The six AOI centers are not events. Coordinate quality at the site-row level: 1,018 approximate, 47 coarse and 6 AOI-center rows; site-level quality totals include polygon/centroid pairs and must not be mistaken for the number of point coordinates. There are 577 explicit coordinate pairs in CSV.

The complete 4TU reconciliation has 70 workbook rows: 13 matched to earlier event rows, 49 new event groups, 4 excluded records, 66 row-level crosswalk entries for admitted/matched rows and 53 emitted point sites. The excluded rows remain documented in the reconciliation table. The public GFLD layer contributes 19 crosswalk records (18 points emitted; one conflicting point suppressed). All 29 GLIDE rows, six NASA Rwanda rows and 11 literature-table claims are retained in source-specific crosswalks.

## Corrections and standardization

The sole original CSV issue is semantic column alignment in `RWA-LS-0006`, not a row-width parse error: the row has 25 cells but the IFRC citation appears in the confidence position, with subsequent fields displaced. It was repaired from the cited IFRC DREF report. No other original row failed the strict row-width/confidence/source checks.

Date, trigger and landslide process are normalized to controlled vocabularies; fatality/injury bounds are numeric and retain source-specific notes. The 2016 May cross-list is treated as one rainfall episode rather than summed into district casualty estimates. For 2013-05 Rulindo, 4TU OID 42's embedded shape point was boundary-tested because the latitude/longitude attributes and country field are blank. It is retained as a **coarse, interpreted inventory reference point**, not a scar coordinate. Its attached narrative says January, but the cited IGIHE and RFE/RL reports confirm 3–5 May. IGIHE specifically attributes eight of the ten rain-related deaths to landslides; the 2018 paper table gives 12 for May/Rulindo. The event stores 8–12 and explains the scope conflict.

## Spatial QA

Administrative overlay basemap: NISR-sourced Rwanda COD-AB through OCHA/HDX; output CRS EPSG:4326. Site-validation results:

- ADM2 district check: 1,058 pass, 13 fail, 0 not tested.
- ADM3 sector check: 1,024 pass, 3 fail, 44 not tested. Not-tested includes rows without a reliable explicitly stated sector.
- All 13 district mismatches and all three sector mismatches have an explanation in `site_validation.csv`; points were retained but not moved or silently relabeled. Known examples include a NASA 5 km Nyabihu-labeled point overlaying Ngororero, 4TU points whose listed district conflicts with the overlay, and three 4TU sector-name/overlay conflicts. Use the QA table for the site-by-site list.
- GLO-30 point screen: 570 slope values at or above 3°, six near-flat values below 3°, and one coordinate without a DEM test. This 3×3 central-difference screen is not a geomorphic validation. No imagery-based review of near-flat points was completed; those records are flagged for follow-up.
- `near_duplicate_coordinates.csv` contains all cross-event point pairs within 500 m, with distance and review flag. Close locations may be nearby real events or reused reference points; proximity alone does not decide a merge.
- All coordinates passed the broad Rwanda envelope test. The 2018 polygons are included as mapped geometries; polygon centroid coordinates are derived from the source polygons, not published slide-site observations.

The six UNOSAT AOI centers are explicitly contextual only. The single `LandslideExtent`-named product feature is field-unvalidated and its attributes classify it as flood water/new water, so no confirmed UNOSAT slide polygon is included. The 494-feature Zenodo file is a combined landslide/flash-flood inventory without a per-feature class. The separate 2024 study's approximately 750 mapped landslides are not added or summed because its mapped geometry was not openly downloadable in the inspected route.

## Output integrity

The workbook includes Events, Sites, Sources, README, District counts, Annual counts, Spatial QA, UNOSAT layers and source reconciliation sheets. GeoPackage layers are `events`, `sites`, `admin_provinces`, `admin_districts`, and `admin_sectors`, all in EPSG:4326. GeoJSON/KML outputs preserve linked geometries and identifiers. The event and annual/district counts are reporting counts, not normalized risk.

## Unresolved issues and access limits

- Obtain a current, complete NASA COOLR/Rwanda export; the retrieved NASA CSV is the legacy one-time catalog snapshot current to 2016-03-07.
- No publicly downloadable, event-level national layer was located for the paper's approximately 980 historical Rwanda landslide locations; the REMA 2,544 initiation points are a susceptibility-analysis input and are not treated as dated event records.
- The 2024 Karongi study's approximately 750-event geometry is described as available on reasonable request, not openly attached; it is not merged with the 494 mixed-hazard Zenodo features.
- DesInventar rendered summary pages did not expose a row-level downloadable Rwanda event file in the inspected route. The LIWEAR regional publication, additional theses, and some MINEMA/Rwanda Mines/REMA source files need data-owner access or additional follow-up.
- The National Risk Atlas aggregate 2011–2014 counts (74 deaths/573 houses) cannot safely be assigned to individual events from the aggregate summary alone.
- Combined flood/landslide deaths for 2023 and other compound events are not converted to landslide-only fatalities. Reports with undifferentiated casualties remain separately described.
- Three district and three sector mismatches need confirmation against event-level primary records; source coordinates were not altered. See the exact list and evidence in `site_validation.csv`.
- DEM slope screens do not resolve whether a point falls in water/wetland; inspect imagery/hydrography for the six near-flat results and the one untested location.

## Prioritized data requests

1. **MINEMA**: event-level incident database for 2011–2024 (dates, administrative levels, deaths/injuries, affected/displaced, source IDs, coordinates and precision).
2. **Rwanda Mines Board (RMB)**: georeferenced geohazard/landslide incident and abandoned-mine failure records, including source CRS and impact definitions.
3. **REMA**: the 2,544 initiation-point layer, accompanying event/date fields and methods/CRS/licensing; clarify whether records are occurrence points or susceptibility training labels.
4. **Authors/data custodians of the 2024 Karongi study**: the approximately 750-feature inventory, mapping dates, class definitions, CRS and license/permission terms.
5. **Authors of the 2018 susceptibility inventory**: the approximately 980 location table/layer with dates, source lineage, location precision, CRS and permission.
6. **Global Fatal Landslide Database maintainers**: maintained full Rwanda export and definitions, uncertainty, update history and reuse terms.
7. **Meteo Rwanda, OCHA, MINEMA and district offices**: dated event reports for 2022, 2024, 2025–2026 and historical 2011–2014 events with separately attributable landslide impacts.
8. **Event-source custodians**: reconcile the 13 ADM2/3 failed overlays and source/date/casualty conflicts, particularly the coarse 4TU/NASA points.

## Interpretation warning

This is a traceable, source-biased compilation, not a complete inventory, validated landslide-scar map, susceptibility product, return-period estimate or normalized risk measure. Counts reflect reporting and data access, which vary strongly by period and location.
