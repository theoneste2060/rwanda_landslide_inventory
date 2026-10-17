v2 raw-source snapshots (one retained copy per source artifact; no duplicate raw_sources.zip)

Research/download date: 2026-10-16. Files are inputs/snapshots, not normalized deliverables. See ../sources.csv and ../RESEARCH_SOURCES.md for URLs, access outcomes, licenses and use details.

- 4tu_rwanda_inventory.xlsx — 4TU.ResearchData Rwanda inventory workbook (CC0 dataset record); 70 source rows, including original IDs and original values.
- 4tu_rwanda_inventory_readme.txt — README downloaded with the 4TU workbook.
- gfld_rwanda_2004_2017.geojson — Rwanda-filtered export of 19 public Global Fatal Landslide Database v2 point records; layer/source license not stated in accessed service metadata.
- nasa_glc_export_rows.csv — full legacy NASA Global Landslide Catalog export (11,033 rows; six Rwanda records), one-time snapshot current to 2016-03-07; license unspecified by NASA portal.
- rwa_glide_events.csv — HDX/OCHA Rwanda GLIDE event table (29 Rwanda records); source license not stated in retrieved metadata.
- zenodo_2018.json — downloaded Zenodo record metadata for the 2018 Rwanda component.
- zenodo_2018_karongi_inventory.zip — public 2018 Rwanda shapefile package (494 combined landslide/flash-flood inventory features; CC BY 4.0, WGS84 / UTM 35S source CRS).
- unosat_rubavu_2023.zip — UNOSAT Product 3579 shapefile package; all included layers are reviewed in ../unosat_layer_audit.json. One named LandslideExtent feature is excluded as confirmed scar geometry because attributes identify unvalidated flood water/new water.
- rwa_admin_boundaries.zip — NISR-sourced Rwanda ADM0–ADM4 COD-AB boundary package retrieved via OCHA/HDX; CC BY-IGO, WGS84. Metadata says boundary establishment date unknown and review was stale at download. Used for basemap and ADM2/ADM3 point-in-polygon QA.
- dem/Copernicus_DSM_COG_10_S02_00_E029_00_DEM.tif — Copernicus DEM GLO-30 tile used for point-scale slope screen.
- dem/Copernicus_DSM_COG_10_S02_00_E030_00_DEM.tif — Copernicus DEM GLO-30 tile used for point-scale slope screen.
- dem/Copernicus_DSM_COG_10_S03_00_E029_00_DEM.tif — Copernicus DEM GLO-30 tile used for point-scale slope screen.

Compressed source packages are retained once, not also extracted into this folder. Derived geometries, crosswalks and source-specific exports are stored outside `raw_sources/`. Preserve the source-specific terms; public access does not imply permission to redistribute.
