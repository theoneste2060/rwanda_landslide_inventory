# Rwanda landslide inventory: methods and findings

**Research cutoff:** 16 October 2026. **Coverage located:** 1963–March 2026. The inventory is a verified open-source compilation, not a complete national register. It contains **30 rows**: **24 event/district records representing 23 distinct episodes**, plus **6 site/assessment-area records** mapped within the May 2023 disaster. Two 7 May 2016 district-local catalog records describe the same broader rainfall episode; the six 2023 mapped assessment areas are nested within the national episode and are not six additional disaster events.

## Findings

Records range from historical reports in 1963, 1987 and May 1988 through contemporary news and humanitarian reporting. The older entries are sparse, often year-only, and have no coordinates. A 2015 National Risk Atlas table lists historical cases and district-level annual totals. It reports 74 landslide deaths, 22 injuries, 573 houses destroyed or damaged, and 656 hectares affected during 2011–2013; its detailed table aggregates by year and district rather than supplying dated individual event points. Those annual aggregates were retained in the source log and findings, not misrepresented as individual events in the master dataset. [1]

The strongest spatial clusters in the assembled records are in the western and northern highlands, including Karongi, Rubavu, Rutsiro, Nyabihu, Gakenke and Ngororero. This pattern reflects both terrain-related exposure and intensive reporting of major disasters; it is **not** a normalized district-risk ranking. The May 2018 Karongi event was mapped as 494 combined landslide/flash-flood features in one study and approximately 750 landslides over about 100 km² in a later study. The counts use different inventories and feature definitions and should not be summed. [2] [3]

The 2–3 May 2023 disaster is the clearest recent multi-district episode. Government, humanitarian, news and satellite sources confirm landslides and mudslides alongside flooding. Published casualty and damage totals vary with reporting date and whether they cover the compound disaster or landslides specifically. UNOSAT products map affected areas in Karongi and Rubavu, and the Rutsiro product identifies mapped landslide/mudslide locations. The six coordinate-bearing 2023 records in this inventory are **assessment-area centers** taken from the UNOSAT map reports, not landslide scar centroids; the satellite analysis was preliminary and not field-validated. [4] [5] [6]

## Coordinates and validation

**12 of 30 rows have coordinates.** Of those, six are source-reported catalog/GLIDE locations and six are UNOSAT image-center coordinates for assessment areas. The point accuracy breakdown is: one NASA catalog point with approximately ±50 km stated uncertainty; two with approximately ±25 km; one with approximately ±5 km; two source points with no published accuracy estimate; and six assessment-area centers based on 50 cm imagery, which describe image location rather than the position accuracy of an individual landslide. **18 records have no defensible single point**, so their latitude and longitude are blank. In particular, station coordinates in a Meteo Rwanda-hosted table, broad GLIDE points for multi-district episodes, and conflicting NASA catalog locations were not passed off as landslide coordinates.

All 12 points were checked against broad Rwanda bounds (latitude −2.84 to −1.05; longitude 28.86 to 30.90). District consistency was reviewed against the source descriptions and known place locations. This was not a full point-in-polygon boundary test. A nationwide DEM/slope test was not performed. Where precise official subnational boundaries were not available in the working environment, the map shows the source-backed points and their source-assigned districts without drawing guessed boundaries. Approximate and assessment-area coordinates are explicitly annotated in the dataset, GeoJSON and KML.

## Search and compilation

The search covered global/open inventories (NASA Global Landslide Catalog, HDX/OCHA GLIDE, DesInventar, EM-DAT, GDACS, GFDRR/UN-SPIDER, USGS and Copernicus EMS); Rwandan institutions (MINEMA, RMB, Meteo Rwanda, RWB, REMA, Rwanda National Police, NISR and district pages); academic papers and repositories; news and humanitarian reports; and remote-sensing and administrative-boundary resources. Search terms included English *landslide*, *mudslide*, *rockfall* and *slope failure*; French *glissement de terrain* and *éboulement*; and Kinyarwanda *inkangu*. The National Risk Atlas, open event tables, agency reports, research papers, and original news/humanitarian pages were reviewed. The companion source log gives each consulted source, URL, access date, and extraction or access note.

Structured NASA and GLIDE records were compared with reports and papers. The HDX Rwanda GLIDE CSV was downloaded and filtered. The NASA Global Landslide Catalog page and catalog-row evidence were reviewed, but the CSV endpoint failed during this run. A NASA-linked 2007 source page and a 2013 news page were not fully accessible; those records carry lower confidence or date/coordinate caveats. The Global Fatal Landslide Database and DesInventar accessible pages did not expose a usable row-level Rwanda export. EM-DAT, Copernicus EMS and USGS searches did not yield a row-level Rwanda inventory in the accessed material. MINEMA annual reports expose national/district aggregates, not incident-level locations. A public Zenodo 2018 polygon inventory and UNOSAT 2023 vector products were identified; the Zenodo shapefile download did not complete. The UNOSAT Product 3579 source package was downloaded and retained separately, but its mixed assessment layers were not treated wholesale as landslide scars. Susceptibility maps and studies, including REMA and a study reporting 980 past locations, were not converted into event points because their row-level event coordinates were not available in the accessed material. [7] [8] [9] [10]

Events were deduplicated by date, location, source description and shared disaster context. Repeated May 2023 reports were consolidated into one episode, with separately mapped sublocations retained only where UNOSAT supplied distinct assessment centers. Differing dates, casualty totals, coordinates and spatial coverage remain in the notes. Confidence describes the support for the event record; it does not mean that the coordinates are equally accurate.

## Gaps and recommendations

The inventory is strongly biased toward fatal events, large humanitarian emergencies, accessible news and modern satellite mapping. Underreporting is likely before formal national disaster reporting, and media availability creates clusters around 2007, 2016, 2018, 2020 and 2023. Annual district totals can conceal many small events. Many reports name a district or sector but no village; even named villages commonly lack event coordinates. The 2018 and 2023 remote-sensing inventories improve spatial coverage for specific episodes, but they are not a continuous national time series.

For a more complete operational inventory, request MINEMA’s incident-level disaster database and original 2011–2024 district records, including geocodes and data dictionaries. Ask RMB for historical geohazard/landslide event points, field-survey records, coordinate reference systems and any current monitoring exports. Ask REMA and the study authors for the source tables or shapefiles behind the 2000–2021 image/field inventories and the 2018 Karongi polygons. Obtain the full GLIDE and Global Fatal Landslide Database event exports and reconcile them with district incident reports. Finally, use official NISR/HDX district-sector-cell boundaries for point-in-polygon checks, then validate candidate points against DEM slope and imagery before treating them as site-level coordinates.

## Deliverables and interpretation

The master CSV and XLSX contain the same 30 records and source fields. The GeoJSON and KML contain only the 12 coordinate-bearing records. The map is a coordinate overview, not a district-boundary map. The raw-source ZIP preserves downloaded input files separately from processed outputs. Empty fields indicate that the source did not provide a value or that the available point could not safely be attributed to the landslide site.

Map symbol colors classify coordinate-location quality: orange marks mapped assessment-area centers or a catalog point with approximately ±5 km accuracy; red marks broad points or points with unknown accuracy. The assessment-area centers are not scar centroids. Event confidence remains a separate field in the inventory.

## References

[1]: https://www.gfdrr.org/sites/default/files/publication/National_Risk_Atlas_of_Rwanda_01.pdf "The National Risk Atlas of Rwanda"
[2]: https://nhess.copernicus.org/articles/22/3679/2022/ "Timing landslide and flash flood events from SAR satellite"
[3]: https://www.mdpi.com/2624-795X/5/4/49 "Exceptional Cluster of Simultaneous Shallow Landslides in Rwanda"
[4]: https://unosat.org/products/3575 "UNOSAT Product 3575: Karongi and Rutsiro assessment"
[5]: https://unosat.org/products/3579 "UNOSAT Product 3579: Sebaya River assessment"
[6]: https://reliefweb.int/report/rwanda/rwanda-floods-and-landslides-operational-update-mdrrw022 "IFRC Rwanda floods and landslides operational update"
[7]: https://data.nasa.gov/dataset/global-landslide-catalog-export "NASA Global Landslide Catalog Export"
[8]: https://data.humdata.org/dataset/rwa-glide-events "HDX Rwanda GLIDE Events"
[9]: https://www.minema.gov.rw/fileadmin/user_upload/Minema/Publications/Disaster_Effects/Annual_Disaster_Effects_Report_2024.pdf "MINEMA Disaster Effects Situation 2024"
[10]: https://www.rema.gov.rw/fileadmin/user_upload/REMA/Publications/Reports/Report_2_-_Landslide_Risks_Assessment_and_Mitigation_Report_3.pdf "REMA Landslide Risks Assessment and Mitigation Report"
