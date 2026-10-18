# Changelog

## v2 — research snapshot 2026-10-17

- Preserved the provided source repository files as read-only copies in `source_original_inventory_readonly.csv` and `source_log_original_readonly.csv`; all v2 derivatives are isolated in this folder.
- Strict-parsed the original inventory: 30 data rows, 25 fields in the header, and all 30 rows have 25 fields. The one categorical/source alignment defect is `RWA-LS-0006`; no other row has a malformed column count or invalid confidence category.
- Repaired `RWA-LS-0006` from the IFRC/ReliefWeb report: restored the citation in source fields and set event confidence to High; retained 14 deaths and the 26 March 2010 date. Corrected impact parsing to 5,920 people made homeless (1,184 families), rather than conflating this with a house count; preserved roads, latrines and wells as infrastructure damage. No precise slide coordinate or house count is asserted.
- Recast the original 30 mixed rows into separate events and sites. Six UNOSAT assessment-area centers are linked to the May 2023 episode, not counted as events. Same-episode May 2016 source rows are merged without allocating multi-district totals.
- Standardized event type/trigger vocabularies, dates, impact bounds, district names, event confidence and source foreign keys. Original values and merge/correction details are retained in notes and source crosswalks.
- Added the public Rwanda 4TU inventory: reconciled all 70 rows (13 to original events, 49 new event groups, 4 excluded); emitted 53 usable 4TU point sites. A record with a blank country/coordinate field (OID 42) was admitted only after its embedded shape point was checked inside Rulindo and its cited event was verified. The record's erroneous January wording was corrected from direct IGIHE and RFE/RL reports to 3–5 May 2013; the 8–12 fatalities range preserves different source scopes rather than averaging them.
- Added six NASA Rwanda catalog rows to the crosswalk; retained five non-reused points and suppressed the broad 2010 reused catalog reference. Kept original event IDs, catalog accuracy statements and source locations.
- Added all 19 public GFLD v2 Rwanda feature records to the crosswalk; 18 point geometries emitted and one inconsistent point suppressed with its decision retained. Source-specific fatality/date differences are documented, not summed or averaged.
- Reconciled all 29 Rwanda GLIDE rows, including non-landslide hazards and unmatched candidates, and all 11 month-level claims in the 2018 paper event table. Source-row values and decisions are in separate reconciliation tables.
- Downloaded and included the 2018 Zenodo Rwanda mixed-hazard inventory (494 polygons); derived one centroid per polygon. No feature is falsely classified as a confirmed landslide scar because the file has no class field and combines landslides with flash floods.
- Audited all six UNOSAT 2023 layers and preserved a machine-readable classification. Excluded an unvalidated `LandslideExtent`-named feature whose attributes identify flood water/new water; retained six AOI centers as contextual sites only.
- Added NISR/OCHA district/sector polygon overlays, Copernicus GLO-30 point-slope screening, near-duplicate point checks, map, annual counts, district summary, GeoJSON/KML/GeoPackage and workbook.
- Added separate, explained spatial QA for 13 district mismatches and three sector mismatches; mismatched values are flagged, not moved or silently relabeled.
- Added a test script, README, data dictionary, QA report, citation metadata, source manifest and license recommendation. No blanket open license is asserted.

## Provenance and change policy

The original input snapshots are retained unchanged. Re-run the scripts against those snapshots to reproduce the v2 data products. Corrections should be made through explicit source-backed overrides and added to this log; never silently overwrite source-row values.
