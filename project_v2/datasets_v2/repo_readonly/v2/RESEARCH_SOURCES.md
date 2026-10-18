# Research findings and source registry notes

**Research cut-off:** 2026-10-16. Original repository files remain unchanged in the clone; v2 reads the read-only snapshots in this folder.

## 2018 mapped event inventory

The 2018 Karongi event shapefile is publicly downloadable from [Zenodo record 7198322](https://doi.org/10.5281/zenodo.7198322). The raw input archive `raw_sources/zenodo_2018_karongi_inventory.zip` contains the four Rwanda shapefile components as downloaded from that record. The shapefile has **494 polygons**, uses WGS 84 / UTM zone 35S, and carries no feature-level landslide-versus-flash-flood class field. The source paper describes a combined landslide/flash-flood inventory. V2 therefore retains its polygons and derived centroids as **unclassified combined-hazard features**, not as 494 confirmed landslide scars. The Zenodo record states **CC BY 4.0**.

A separate 2024 study estimates approximately **750 landslides** in the Karongi cluster, but reports its data available on reasonable request rather than publishing the event polygons. It is a different mapping/counting approach and must not be added to the 494 mixed-feature count. [NHESS article / preprint](https://nhess.copernicus.org/articles/22/3679/2022/); [2024 study](https://www.mdpi.com/2624-795X/5/4/49).

## NASA Global Landslide Catalog

The full legacy NASA export was downloaded into `raw_sources/nasa_glc_export_rows.csv` from [the direct CSV URL](https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export/Global_Landslide_Catalog_Export_rows.csv). It contains **11,033 records**, including **six Rwanda rows**. NASA labels it a one-time export current to 2016-03-07, not a current complete COOLR inventory. The 2007 IFRC entries have two 5 km reference points; 2010 has a broad 50 km point; the 2013 point has unknown accuracy; the May 2016 Gakenke/Ngororero points are 25 km. These are catalogue/event references rather than mapped slide-scar centroids. Two points associated with 2010 and 2018 Rubavu are approximately 46 metres apart and are not emitted as site locations. NASA's portal says the export license is unspecified and portal Terms and Conditions apply. A Socrata-style JSON endpoint returned 404; no current complete COOLR export was located.

## Rwanda 4TU event inventory

The [4TU.ResearchData CC0 record](https://doi.org/10.4121/15040446.v1) offers a public Rwanda event/location workbook and a README. Both files were downloaded under `raw_sources/` (`4tu_rwanda_inventory.xlsx`, `4tu_rwanda_inventory_readme.txt`). Its description says the inventory spans 2006–2021; the README does not document CRS. The workbook includes source-row dates, references, location accuracy and coordinates and is being reconciled against the original 30 rows, NASA, GLIDE and GFLD records. Use source-specific counts as claims, not automatically as distinct events. The workbook is CC0.

## 980-location literature inventory and related products

The 2018 Rwanda susceptibility paper discusses approximately **980 historical landslide locations**, with mixed historical and field provenance and map-scale precision. No downloadable point table/GIS layer or a separate data license/CRS was located. Its main-disaster table contains 11 month-and-district rows, including rows for 2011, 2013 and 2017. Those month-level source claims are retained at month precision only where used; they are not given invented days or point coordinates. [Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC5858312/); [Table 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC5858312/table/ijerph-15-00243-t001/).

The REMA risk report describes 2,544 shallow-slide initiation points used for susceptibility analysis; these are not a dated event catalogue. The Piller thesis describes a 254-event national modelling set and 577 slides mapped in a western study area, but no event GIS file is listed and the thesis is in copyright. DesInventar's rendered profile shows aggregate cards, not downloadable row-level records in the inspected route. The LIWEAR publication describes a regional East African catalog but a direct downloadable Rwanda event export was not found. These routes are documented in `sources.csv`; no hazard/susceptibility prediction was promoted to an observed event.

## Global Fatal Landslide Database

A public ArcGIS REST query to the Global Fatal Landslide Database Version 2 point layer returned **19 Rwanda features** for 2004–2017. The research source is the public queryable service, not the paper's web viewer: [layer](https://services2.arcgis.com/Dn40vzt2R38VJsSS/arcgis/rest/services/NSLandslidepoints_04to17/FeatureServer/0?f=json). The record-level Rwanda export is preserved separately if used; its definitions, casualty semantics and match status are recorded in the source-event crosswalk. The source paper is [Froude & Petley (2018)](https://nhess.copernicus.org/articles/18/2161/2018/).

## UNOSAT 2023 shapefiles

All six layers in `raw_sources/unosat_rubavu_2023.zip` were opened and audited in `unosat_layer_audit.json`. Two are named `AnalysisExtent` and are analysis/AOI boundaries. Three are `FloodExtent` water polygons. The remaining polygon is named `LandslideExtent`, but its one feature has `Water_Clas = Flood Water`, `Water_Stat = New Water / Water Increase`, `Confidence = To be evaluated`, and `Field_Vali = Not yet field validated`; it is therefore **excluded from confirmed landslide geometry** and documented as an ambiguous candidate. The six AOI centers are retained as assessment-area locations, never as extra disasters or slide centroids. [UNOSAT Product 3579](https://unosat.org/products/3579).

## Event reports found in research

The Government of Rwanda reports **131 deaths** from the combined early-May 2023 floods and landslides; this remains an event-wide combined total, not a landslide-only or site-level count. An International Charter satellite product lists landslide/mudslide detections around Kibingo, Congonil, Kagana and Ghanga villages in Rutsiro, but the product is dated after the event and does not supply feature-level site coordinates in the inspected route. It is linked to the existing 2023 episode rather than added as another disaster. [Government report](https://www.gov.rw/blog-detail/official-statement-on-the-disaster-caused-by-the-heavy-rains-in-rwanda-on-2nd-and-3rd-may-2023); [Charter activation 816](https://disasterscharter.org/activations/flood-flash-in-rwanda-activation-816-).

A local-language source reports a **2026-03-23** fatal slope collapse in Kigarama, Ngororero; this is a distinct dated event candidate with two reported deaths, retained at district/village level without invented coordinates. [Le Monde report](https://www.lemonde.fr/planete/article/2026/06/04/au-rwanda-le-fleau-des-glissements-de-terrain-ici-la-terre-donne-et-reprend_6697489_3244.html).

The April 2022, April 2024 and April 2025 items describe combined rainfall/flood/landslide impacts but do not allocate all deaths to a specific landslide location in the inspected sources. They are not added as precise landslide events. A 2013 Burera family landslide account provides no precise incident date. A November 2011 high-risk-zones PDF route returned a download interstitial, so it was not used as an independently checked event citation.

## Additional routes and source limitations

The published REMA and 2018 academic susceptibility materials do not expose an event-level national shapefile in the accessed routes. The 2024 Figshare bundle relates to susceptibility materials and is not treated as an event inventory. The accessible 4TU data, direct NASA export, 2018 Zenodo geometries, public GLIDE table, public GFLD service, UNOSAT shapefiles and NISR/OCHA district/sector boundaries are retained in `raw_sources/` or documented in `sources.csv`. Dataset access success, failed routes and licensing notes are kept separate from event confidence.


## 2013-05 Rulindo heavy-rain / landslide episode (newly reconciled)

The 4TU workbook OID 42 has a blank country field and blank latitude/longitude attributes, but its embedded `Shape` value is `30.023501 -1.725002`; the point falls inside the NISR/OCHA Rulindo ADM2 polygon when interpreted as longitude/latitude. The cited IGIHE report (6 May 2013) says heavy rain affected Rulindo and ten people died; it specifically attributes eight deaths to landslides in Burega and Kinzuzi and describes two other rain-related deaths. Radio Free Europe/Radio Liberty’s Kinyarwanda service states the rain ran from 3–5 May 2013 and reports ten deaths in Rulindo. This report and the linked 4TU row support a 3–5 May event range, but the coordinate remains a coarse inventory/event reference, not a scar location. The 2018 paper’s Table 1 reports 12 deaths for a May 2013 Rulindo landslide disaster; the difference in scope/count is preserved as 8–12, not averaged. Sources: [IGIHE](https://igihe.com/amakuru/u-rwanda/article/rulindo-abantu-10-bahitanywe-n), [Radio Free Europe/Radio Liberty](https://www.radiyoyacuvoa.com/a/inkangu-yahitanye-abantu-10-muri-rulindi/1655451.html), [Kigali Today](https://kigalitoday.com/amakuru/mu-rwanda/article/rulindo-abantu-icumi-bahitanwe-n-imvura), and [2018 paper Table 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC5858312/table/ijerph-15-00243-t001/). The 4TU Shape field provides a WGS84-like coordinate display but does not state its CRS; the value is explicitly documented as interpreted and boundary-tested, not source-lat/lon metadata.
