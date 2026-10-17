# Data dictionary

CSV files use UTF-8, comma delimiters and a header row. Empty values mean unknown, unavailable or not applicable as described below; they are not zero unless a source explicitly reports zero. Pipe (`|`) separates multiple values/foreign keys. WGS84 longitude/latitude order is used for GIS files; CSV coordinate columns are named latitude then longitude.

## `events.csv`

One row per curated episode or month-level event claim. `event_id` is the primary key.

| Field | Type / allowed values | Meaning |
|---|---|---|
| `event_id` | string | Stable v2 event identifier. Original IDs are retained where possible; 4TU-only IDs use `RWA-LS-4TU-nnn`. |
| `date_start`, `date_end` | ISO date string; `date_end` may be blank | Best supported start/end date. A blank end means same-day or not separately specified, according to `date_precision`. |
| `date_precision` | `day`, `month`, `year`, `range` | Precision of the source-reported date. Month/year records are stored using the first day in `date_start` and last day in `date_end` where applicable. |
| `event_name` | string | Concise source-derived label; may preserve the original inventory title. |
| `provinces`, `districts` | pipe-separated strings | Normalized administrative names; may be blank when the evidence does not establish a location. |
| `n_districts` | integer | Number of named/normalized districts; not a measure of affected area. |
| `primary_trigger` | `rainfall`, `prolonged rainfall`, `earthquake`, `mining/quarrying`, `construction/road cut`, `flood-related`, `unknown` | Controlled trigger category. Detail belongs in `notes`. |
| `landslide_type` | `shallow landslide`, `debris flow`, `mudslide`, `rockfall`, `rotational/translational slide`, `landslide cluster`, `slope failure (mining/road/construction)`, `mixed landslide-flood`, `unknown` | Controlled process/category. Do not infer a subtype when sources do not state it. |
| `fatalities_min`, `fatalities_max` | non-negative integer or blank | Source-supported event fatality bounds. Not apportioned across districts; conflicting source scopes are retained as ranges and explained in `fatalities_note`. |
| `fatalities_note` | string | Source-specific counts, scope conflicts and interpretation. |
| `injuries_min`, `injuries_max` | non-negative integer or blank | Source-supported injury bounds. |
| `people_affected`, `people_displaced` | non-negative integer or blank | Separate measures where sources support them. Narrative qualifiers remain in notes. |
| `houses_destroyed`, `houses_damaged` | non-negative integer or blank | Separate house impact counts; do not convert generic infrastructure damage into house totals. |
| `infrastructure_notes` | string | Narrative damage or service impact not safely normalized. |
| `event_confidence` | `High`, `Medium`, `Low` | Confidence in the event record, not spatial accuracy. |
| `confidence_rationale` | string | Basis for event confidence. |
| `source_ids` | pipe-separated `source_id` values | Foreign keys to `sources.csv`. |
| `notes` | string | Original values, merge/correction rationale, source conflicts and caveats. |

## `sites.csv`

One row per mapped location, polygon or mapped assessment context. `site_id` is the primary key; `event_id` links to `events.csv`.

| Field | Type / allowed values | Meaning |
|---|---|---|
| `site_id` | string | Stable site/feature identifier. |
| `event_id` | string | Foreign key to the associated event. |
| `sector`, `cell`, `village` | string | Named locality only where parsed/reported; blank where not established. Check administrative overlays in `site_validation.csv`. |
| `place_description` | string | Source wording and explicit note on whether the point is a reference, centroid or AOI center. |
| `latitude`, `longitude` | decimal degrees or blank | Explicit coordinate for point/centroid rows. Blank for polygon rows; geometry is in GeoJSON/GPKG/KML. |
| `geometry_type` | `point`, `polygon`, `centroid_of_polygon`, `aoi_center` | Role of the spatial feature. |
| `location_quality` | `exact`, `approximate`, `coarse`, `aoi_center` | Location precision class, independent of event confidence. `approximate` also describes derived centroids/polygons where the source does not assert a surveyed scar location. |
| `accuracy_m` | non-negative number or blank | Stated source uncertainty converted to metres when explicitly supplied. Blank is not zero. |
| `coordinate_method` | `published`, `inventory`, `UNOSAT`, `geocoded`, `derived` | Method/source of geometry. No coordinates were inferred from names in v2. |
| `source_crs` | string | Source CRS statement or explicit note that it is unstated/assumed only for transformation/QA. |
| `district_check` | `pass`, `fail`, `not_tested` | Point/centroid overlay against source-reported event district(s); detailed actual overlay and explanations are in `site_validation.csv`. |
| `slope_check` | string | Copernicus GLO-30 3×3 central-difference point screening, threshold flag, or reason not tested. Not a geomorphic validation. |
| `source_id` | source ID | Foreign key to `sources.csv`. |

## `sources.csv`

`source_id` is the primary key. Source status is about access, not event confidence.

| Field | Type | Meaning |
|---|---|---|
| `source_id` | string | Deterministic ID derived from the URL. |
| `title`, `publisher` | string | Source title and source organization/publisher. |
| `date` | string | Publication date, dataset version or snapshot date, as available. |
| `url` | URL | Public source/document/data route. |
| `access_date` | ISO date string | Date accessed/downloaded or reviewed for this compilation. |
| `license` | string | Reported license or explicit note that terms were not established. |
| `access_status` | string | Downloaded/opened, cited-only, limited, failed route or other retrieval outcome. |
| `what_was_extracted` | string | Fields/claims used and relevant caveats. |

## QA and reconciliation tables

- `site_validation.csv`: one spatial-QA row per site geometry, including event/source-reported districts, ADM2/ADM3 overlays, checks, explanation, slope string and tested coordinate.
- `near_duplicate_coordinates.csv`: pairs of point locations from different events closer than 500 m, with approximate local distance and review flag; proximity is not proof of duplication.
- `source_event_crosswalk.csv`: one row per source record/claim with match status, matching rule and decision note.
- `4tu_reconciliation.csv`: original 4TU row fields plus normalized event link, admission/match decision, coordinate overlay and site emission status.
- `gfld_reconciliation.csv`, `glide_reconciliation.csv`, `nasa_rwanda_reconciliation.csv`, `literature_claims.csv`: source-specific records and crosswalk decisions; reported impacts are not automatically summed into event totals.
- `district_event_counts_deaths.csv`: event-record counts by district; death sums include single-district rows only. Multi-district deaths remain unallocated.
- `annual_event_counts.csv`: count of event rows by `date_start` year; reporting frequency, not normalized hazard risk.
- `sites.geojson`, `events.geojson`, `sites.kml`, `rwanda_landslide_v2.gpkg`: spatial representations of these same records. EPSG:4326 is used for output geometries; see README caveats for mixed/unclassified polygons.
