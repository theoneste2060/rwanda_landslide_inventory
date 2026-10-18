# Machine learning for a Rwanda landslide early warning system with a small, biased inventory

**Evidence and feasibility report**  
**Prepared:** 18 October 2026  
**Scope:** Inventory v2, 88 event records; feasibility of rainfall-trigger forecasting and susceptibility mapping  
**Author:** Manus AI

## Executive summary

The 88-row inventory is useful for prioritizing data assembly and framing a pilot, but it is not a training dataset for a validated national landslide early warning system. The events are selected from reported disasters and fatal/damaging incidents, not a complete census. No non-event observations, measured rainfall, soil moisture, terrain, geology or land-cover predictors are included in the two supplied tables. The site table contains 1,071 rows, but these include duplicated polygon/centroid representations of a mixed-hazard 2018 inventory and six contextual assessment-area centers. The row count is therefore not the number of independent landslides or usable point labels. [1] [2] [3]

Running code on the supplied files confirms 88 events (1963–2026), with 66 day-precision dates. Of these, 56 also name at least one district, 43 name exactly one district, and 25 meet a conservative combination of day precision, exactly one district, a linked site and a rainfall/prolonged-rainfall trigger. Those 25 rows reduce to 21 distinct reported dates because four records share dates with another candidate row. This is at most a candidate event set, not 25 independent rainfall-trigger observations. The inventory contains 77 point rows, none with stated accuracy at or below 1 km; 28 point rows have no stated accuracy. The remaining stated point accuracies are coarse, in the 5–25 km range. None of the 494 polygon centroids is a surveyed landslide scar coordinate, and the 494 source polygons are explicitly mixed landslide/flash-flood features with no per-feature class in this extract. [1] [2] [3]

**Rainfall-trigger model (“when”).** The current tables cannot fit or validate a rainfall threshold or ML model: there are no rainfall sequences and no defensible event/non-event time windows. A later model could begin with pre-specified, simple intensity-duration and antecedent-rainfall baselines, using daily or subdaily Meteo Rwanda gauges and multiple gridded products. Rwanda-specific papers provide reference thresholds and product comparisons, but their reported discrimination is not an independent operational test. Uwihirwe et al. reported high true-positive rates together with substantial false-positive rates using an event inventory; Riveros et al. found product- and variable-dependent trade-offs in a 55-event analysis. These studies are useful benchmarks, not permission to claim that a new 88-row ML model is reliable. [10] [11]

**Susceptibility model (“where”).** The current tables cannot support a 30 m–1 km supervised susceptibility fit. Fine-resolution predictors would be attached to spatial labels whose stated error is generally 5–25 km, unknown for 28 points, or whose geometry represents a mixed-hazard polygon/derived centroid. Rwanda susceptibility papers using hundreds of locations are methodological precedents, but their random or unspecified validation designs do not establish that a model trained on 88 biased event records would generalize. Begin with a documented, physically interpretable benchmark and inventory expansion; treat positive-unlabeled or presence-only approaches as exploratory unless the reporting process and evaluation background can be defensibly modeled. [16] [17] [20] [21]

The appropriate near-term goal is a **data and shadow-verification pipeline**, not an automated public alert model. Establish a joint MINEMA–Meteo Rwanda incident/rainfall dataset, adjudicate duplicates and locations, obtain the 2018 and REMA inventories with lineage, and prospectively test a transparent baseline through at least one rainy season. A later operational system must communicate both alert level and uncertainty, define acceptable false-alarm and missed-event consequences with communities and authorities, and include preparedness and response—not just prediction. [14] [15] [38]

## 1. Scope and evidence approach

The analysis follows the requested sequence: first inspect the actual `events.csv` and `sites.csv` files and the repository’s data dictionary and QA report; then assess feasibility and review evidence. The input files were downloaded unchanged from the repository’s read-only v2 directory. The script in this deliverable recomputes the inventory counts and writes all readiness tables and plots. It does not modify repository data. [1] [2] [3]

Literature was reviewed by nine topic areas: rainfall thresholds; hydro-meteorological products; susceptibility methods; biased and positive-unlabeled data; physics-based methods; remote-sensing inventory mapping; operational EWS; rare-event validation; and uncertainty/alert design. The evidence table records one row per unique source retained from the review, with source type, sample size, validation, reported metric, caveat and project relevance. Quantitative claims are used only where source text or an authoritative article/report page was opened. Where full text or a metric was unavailable, the evidence table says so rather than inferring a result. Agency guidance, preprints and peer-reviewed research are distinguished.

The target is decision support for a future Rwanda EWS, not a causal attribution study or a claim that this inventory measures landslide incidence, return periods, or national risk. Event-report counts are affected by media access, disaster severity, administrative coverage and changes in reporting over time. Missing records are not evidence of no landslide. [2] [3] [9]

## 2. Data feasibility: measured readiness

### 2.1 Readiness table

All counts below are reproduced by `readiness_baseline.py` from the two supplied CSVs. “Candidate” means only that the table fields pass stated filters; it does not mean an event has a matched rainfall observation or is independent of another record.

| Task / filter | Rows | Interpretation |
|---|---:|---|
| Curated event rows | 88 | Reported episodes/claims; not an exhaustive occurrence census. |
| Day-precision date | 66 | Potentially matchable to daily rainfall, subject to date and event-definition error. |
| Day + any named district | 56 | A district can support coarse area-averaged rainfall matching, not precise cell assignment. |
| Day + exactly one district | 43 | Excludes multi-district rows; still does not prove the event point or rainfall cell. |
| Day + one district + linked site | 33 | Site linkage exists, but spatial accuracy may be coarse or unknown. |
| Day + one district + rainfall/prolonged-rainfall trigger | 33 | Trigger field is a curated classification, not a measured rainfall predictor. |
| Day + one district + linked site + rainfall/prolonged-rainfall trigger | 25 | Conservative potential temporal candidate pool; only 21 distinct dates. No rainfall series or negatives are supplied. |
| Distinct dates among day-precision rows with a named district | 48 | 56 event rows collapse to 48 reported dates; same date is a review flag, not proof of duplication. |
| Site rows | 1,071 | Geometry rows, not 1,071 independent landslides. |
| Point site rows | 77 | 28 have no stated accuracy; none has stated accuracy ≤1 km. |
| Point rows with stated accuracy ≤1 km | 0 | No point label is documented as precise enough for 30 m–1 km predictors. |
| Polygon centroids | 494 | Derived from the 2018 mixed-hazard polygons; not observed scar centroids. |
| Polygon rows | 494 | The extract does not label each feature as landslide versus flash flood. |
| UNOSAT AOI centers | 6 | Contextual assessment-area centers, not landslide occurrences. |

The table’s 25-row conservative temporal subset is the intersection of documented day date, one named district, a linked site and a rainfall/prolonged-rainfall trigger. A less restrictive district-average analysis could include up to 33 day-dated single-district rainfall/prolonged-rainfall records without requiring a site link. Neither count is a validated model sample: exact rainfall grid assignment, event duplication, completeness of reporting and negative time windows remain unresolved. Conversely, the 25 rows should not be misread as an objectively “usable” sample for training; they are the maximum candidate rows under explicit CSV filters. [1] [2]

### 2.2 Event completeness, clustering and duplicates

The date precision distribution is 66 day, 9 month, 11 range and 2 year records. Start-year counts show 77/88 rows (87.5%) in 2007–2020. There is one 2023 record and none in 2022 or 2024, but the current snapshot also contains one 2025 record and two 2026 records. The record concentration is therefore a property of the compiled reporting history, not an estimate of changing physical hazard. [1] [3]

Trigger labels are `rainfall` for 62 rows, `prolonged rainfall` for 2, `mining/quarrying` for 10, `unknown` for 12, and one each for construction/road-cut and flood-related triggers. Landslide type is `unknown` for 46 rows; the remaining rows include mudslide (16), slope failure associated with mining/road/construction (10), landslide cluster (8), shallow landslide (3), debris flow (3), mixed landslide-flood (1), and rockfall (1). These missing and heterogeneous labels constrain any task-specific subset; rainfall-related triggers should not be treated as independently measured rainfall-response pairs. [1] [2]

Among the 66 day-precision rows, 52 distinct dates are represented: ten date groups contain more than one row, with 14 records beyond one-per-date. Within the conservative 25-row rainfall candidate subset, 21 dates remain and three dates have repeated records, leaving four same-date excess rows. Some same-date records likely refer to separate districts or separately documented failures; other pairs may be duplicate source claims. The exact match decision must use the source crosswalk and primary reports, not a date-only merge. The QA report also flags spatially close cross-event coordinates and known district/sector overlay conflicts; coordinate proximity is not proof of duplication. [1] [3]

The requested note that “three same-date event pairs may be duplicates” is not equivalent to the actual CSV’s total collision count. The computed day-precision table has ten repeated-date groups. The three repeated-date groups in the strict rainfall candidate pool are a narrower subset. We therefore preserve all IDs and treat each same-day group as a manual-review flag until sources establish whether records describe the same event, multiple failures in one storm, or unrelated events. [1]

The date-start month counts for all rows peak in April (24) and May (25), but this combines day, month, year and range precision. Restricting to the 66 day-precision records, 41 start in March–May (62.1%). A nonparametric bootstrap resampling those 66 dated records gives a 95% interval of approximately 0.50–0.74 for the March–May share. This is only a descriptive calendar-season bootstrap; it is not evidence of a rainfall trigger threshold, seasonal incidence, or forecast skill because the inventory’s reporting process and observation effort are not constant. The included code explicitly labels this limitation. [1] [2]

District-level counts are also skewed. The largest numbers of records with named district references include Nyabihu (15), Rubavu (11), Musanze (10), Ngororero (10), Muhanga (9) and Karongi (9). Multi-district records contribute to multiple names, and locations with greater reporting or media coverage may be overrepresented. These figures must not be mapped or interpreted as district risk without population/exposure denominators, reporting-process correction and event deduplication. [1] [3]

**Effective sample size cannot be estimated as a single credible number from these tables.** There is no full rainfall-day panel, no observation-effort history, and no vetted grouping of all records into independent storms. The 25 strict candidate rows reduce to 21 distinct dates, but same-date events can share a storm and nearby locations can share the same rainfall grid. Spatial reporting bias and temporal dependence further reduce independent information. A claim that “n=88” or “n=25” is an effective sample size would therefore be unjustified. For analysis planning, treat 21 distinct dates as an upper-bound candidate count for the strict trigger pool, and treat effective information as lower and uncertain until sources and storm groups are audited. [1] [3] [9]

### 2.3 Spatial readiness and resolution mismatch

The QA report confirms 1,018 approximate rows, 47 coarse rows and 6 AOI-center rows across all geometries. It also confirms 577 CSV coordinate pairs, including the centroids and AOI centers. These geometry-row counts must not be confused with the 77 point sites. The 494 polygon/centroid pairs are one related feature set, not 988 separate occurrence labels. The combined 2018 polygon inventory has no per-feature hazard class in this extract, while the centroids are derived points. A pixel-level susceptibility model would risk creating hundreds of pseudo-replicated labels from one event source without proof each geometry is a landslide. [2] [3]

The 77 point rows include 28 without a stated accuracy; the remaining 49 have stated accuracies in the 5–25 km range. This is too coarse for assigning individual 30 m–1 km slope, lithology, land-cover or terrain predictors as though the point were an exact scar. At that positional error, one recorded point may overlap several landforms and gridded rainfall cells. A defensible first susceptibility product may be a broad administrative or catchment-level screening layer, but it must display scale and uncertainty, and it cannot be validated against the current location labels as a 30 m map. [1] [2] [3]

The dictionary identifies location accuracy separately from event confidence. Blank accuracy is unknown, not zero. The QA report records 13 district-overlay failures and three sector-overlay failures; records were retained with explanations rather than moved. The DEM screen is a QA flag, not geomorphic validation. Resolve these records before assigning fine-resolution covariates or using them as held-out positives. [2] [3]

### 2.4 Sample size, events per predictor and uncertainty

A classical “10 events per variable” rule is a rough warning, not a universal theorem or a replacement for formal sample-size planning. Even under the optimistic and currently unsupported assumption that all 25 strict candidates are independent positive events, ten positive events per estimated parameter would allow only about two freely estimated parameters. At 21 unique dates, the analogous rough limit is about two. The 88 raw rows would suggest eight parameters if every record were an independent outcome, but they are not: trigger events are a subset, duplicate dates and shared storms exist, and there are no negative time windows or confirmed spatial absences. The effective information available for model fitting is smaller than the raw count and may be much smaller. Use shrinkage or partial pooling only when the data and priors can be defended; regularization cannot repair biased labels or a missing outcome panel. [8] [10] [16] [17]

To illustrate how imprecise rare-event proportions are at these sample sizes, under a simple independent Bernoulli sample the worst-case 95% normal-approximation half-width for a proportion near 0.5 is about ±0.20 for n=25, ±0.21 for n=21, ±0.15 for n=43 and ±0.10 for n=88. These are generic precision illustrations, not measured alert rates or a formal model-power calculation. Dependence, label bias and imperfect ascertainment would widen uncertainty. The observed calendar bootstrap interval (0.50–0.74) is a separate, actual descriptive calculation. No bootstrap threshold or logistic-model stability analysis can be honestly run without real rainfall predictors and defensible event/non-event labels. [1] [8] [10]

Literature does not provide a universal minimum event count. Rossi et al. report an approximately 175-event figure for keeping threshold uncertainty below 10% in a particular central-Italy setting. That is a context-specific result, not a Rwanda power rule. Other rainfall-threshold studies have used hundreds of events; the Rwanda threshold papers used around 59 MPRE/60 daily conditions and still reported substantial false positives or lacked independent holdout evaluation. A threshold may be explored with fewer events if it is strongly constrained by physics and priors, but its uncertainty, transfer assumptions and validation limitations must be explicit. [8] [9] [10]

### 2.5 Data conflicts and cleaning protocol

Do not alter the source CSVs. Maintain a versioned analytical copy and a separate adjudication log with a stable event ID and reversible decisions.

1. **Preserve source lineage.** Retain original event/site IDs, source IDs, URLs, date text, exact wording and confidence rationale. Do not overwrite source geometry or casualty ranges.
2. **Review date groups and candidate duplicates.** For each repeated date, compare narrative, district, source IDs, trigger, casualty scope and coordinate. Assign a relation code: duplicate claim, same-storm distinct failures, multi-district episode, date uncertain, or unresolved. Never merge solely because dates match.
3. **Normalize event units.** Define whether the modeled outcome is a slope failure, source-reported event, district-day, storm-day or warning-zone-day. Retain parent storm/episode and child failure identifiers. Prevent child records from appearing in both train and test folds.
4. **Audit date precision.** Keep day/month/year/range as separate metadata. Do not convert “month” or “year” start dates to event days for rain matching. Carry timing windows for uncertain reports and test sensitivity to ±1 day where documented.
5. **Resolve location uncertainty.** Separate observed scar points, interpreted reference points, polygons, centroids and AOI centers. Preserve accuracy as an uncertainty radius. Use district/catchment averages or multiple-cell uncertainty integration for coarse locations; exclude unknown-precision points from fine-resolution claims.
6. **Resolve event mechanism.** Separate rainfall-triggered slides, mining/quarry/road failures, flood-related compound events, unknown triggers and mixed processes. Do not train a rainfall model on all types as if the response were homogeneous.
7. **Represent missingness and capture bias.** Unknown type, trigger, date, location and no reported record are not negatives. Retain unknown categories or exclude from specific analyses with a count table. Record likely reporting pathway and observation effort if obtainable.
8. **Freeze analytical versions.** Hash source files, date the adjudication table, preserve QA flags, and preregister all inclusion and split rules. Report changes as a row-level difference table.

The 2018 source inventory deserves special handling. The QA report describes 494 polygons plus 494 centroids from a mixed landslide/flash-flood product, with no per-feature class; the six UNOSAT AOI centers are contextual, and the one feature named “LandslideExtent” was described as flood water/new water and not field validated. These are not clean positive labels. [2] [3]

## 3. Literature review and method feasibility

### 3.1 Rainfall thresholds: frequentist, Bayesian and local evidence

Intensity-duration (ID) and event-duration (ED) thresholds are interpretable baselines. Caine’s global curve and the later global database/update by Guzzetti et al. are useful historical reference bounds, but they combine different climates, landslide processes, event definitions and reporting systems. Guzzetti et al. summarized 2,626 rainfall events. Such a pooled curve is not a calibrated Rwanda warning rule. [4] [5]

Frequentist ED work by Peruccacci et al. used 442 central-Italy rainfall events and reported bootstrap parameter uncertainty. Melillo et al. demonstrated reproducible automatic event reconstruction using 229 landslides and 169 gauges, but multiple rainfall conditions can be associated with a single landslide. Gariano et al. used a later-year 2012 back-analysis after 2002–2011 calibration, a more relevant temporal design than random cross-validation. Brunetti et al. compared Bayesian and frequentist threshold methods; their paper describes Bayesian inference as more suitable for small data and frequentist inference for larger data, but does not turn that observation into a universal sample-size guarantee. [6] [7] [8]

Berti et al. illustrate why a probability threshold depends on the reference area and on the definition of triggering versus non-triggering rainfall events. Their Italian analysis used a large catalogue and explicit event-detection sensitivity. A warning probability for a 65 km² unit is not automatically the probability for a 2,600 km² district or a 30 m slope. For Rwanda, spatial unit and warning action must be specified before the model is fitted. [7]

The closest East African analogue is Monsieurs et al., which analyzed 174 western-branch East African Rift events and used 143 non-mining calibration points after exclusions. The authors note an incomplete, spatially biased media inventory and rainfall product underestimation. In an illustrative pixel with six events, thresholds with no observed false negatives still produced above-threshold conditions on roughly 63–70% of days. That example is not regional skill; it demonstrates the trade-off and the danger of choosing a threshold based only on event capture. [9]

Two Rwanda studies matter most. Uwihirwe et al. tested precipitation and antecedent indices using 35 gauges and an inventory-derived set of 59 MPRE/60 daily conditions. The maximum-TSS event-volume threshold near 30 mm had TPR about 0.932 and FPR about 0.409; the Bayesian 12.5 mm/day RD1 threshold had TPR about 0.717 and FPR about 0.298. The values were fit/evaluated on the same 2006–2018 catalogue, not an independent prospective or geographic holdout. They are a local benchmark and show the operational cost of false alarms. [10]

Riveros et al. compared seven satellite/reanalysis precipitation products against 19 gauges and evaluated soil moisture at six stations. Their 55 accurately dated landslides (2007–2019) are fewer than the 88 current curated records. The study reported IMERG as most suitable among tested precipitation products in that dataset; 3-day rainfall AUC was around 0.72, modeled 50 cm root-zone soil moisture AUC around 0.74, and a bilinear moisture-rainfall model reduced false alarms by about 20% while reducing true alarms by about 8%. These are not independent ML forecasts. The source also used 5 km buffers around imprecise event locations. [11]

**Method implication.** If rainfall observations are assembled, start with a small number of predeclared predictors: event rainfall accumulation/duration, one or a few antecedent windows, and, if reliable, a soil-wetness state variable. Use the Rwanda published values as benchmarks or sensitivity priors, not fixed truth. A Bayesian hierarchical threshold model could partially pool by rainfall regime or susceptibility stratum and report uncertainty, but splitting 21 distinct candidate dates into many strata is not credible. Avoid selecting a different threshold for every district from a sparse catalogue.

### 3.2 Rainfall products and antecedent conditions

CHIRPS, IMERG and ERA5-family products differ in spatial/temporal resolution, gauge correction, retrieval and error structure. Their performance in mountainous East Africa is not interchangeable. Dinku et al.’s eastern African CHIRPS validation found strong regional variation and weak performance in mountainous and coastal areas; performance also depended on daily versus dekadal/monthly aggregation. A recent Ethiopian gauge comparison found CHIRPS more skillful than ERA5 in some highlands, while performance of both deteriorated for violent rainfall; false-alarm ratios exceeded 0.7 for events above 40 mm/day in the reported highland analysis. An IGAD-region comparison also reported season- and terrain-dependent product ranking. [12] [13]

For the Rwanda-specific Riveros study, IMERG outperformed the tested products overall against selected gauges, but the comparison is limited by 19 gauges, point-to-grid mismatch and a selected event catalogue. It does not verify ERA5-Land for Rwanda. No Rwanda head-to-head ERA5-Land independent gauge validation was verified in this review. Treat an ensemble or product-specific uncertainty ranges as more honest than declaring one gridded rainfall product ground truth. [11]

A practical observation system should acquire Meteo Rwanda gauge data with station history, quality flags, missingness, gauge coordinates/elevation and subdaily intensity if available. Compare products by elevation, season, accumulation window and intensity class. Gauge wind undercatch, point-to-grid mismatch, gauge influence in the satellite product, and sparse mountain stations can all distort validation. For soil moisture, distinguish surface satellite retrievals from root-zone modeled or in-situ measurements; depth and spatial support are not interchangeable. [11] [12] [13]

### 3.3 Susceptibility modeling with few or biased event locations

Logistic regression, GAMs, weights of evidence (WoE) and frequency ratio (FR) are interpretable first baselines when labels and predictors are defensible. Penalization or Bayesian priors can limit coefficient variance; they cannot correct an event-capture process that preferentially records fatalities or accessible locations. A model should use a small, preregistered predictor set linked to plausible slope processes and evaluate geographic transfer, not maximize random-split AUC.

Rwanda susceptibility studies provide context, not direct support for n=88. Nsengiyumva et al. compared WoE, FR, logistic regression and statistical index with 692 points and reported prediction/AUC rates of 92.7%, 86.9%, 81.2% and 79.5%, respectively; the accessible validation design did not establish a spatially independent test. Mind’je et al. used 423 locations and reported AUC success/prediction rates of 81.2%/84.6% under a random 75/25 point split. A separate Rwanda multi-criteria study compared a map against 980 locations and explicitly identified data shortage and lack of a complete national inventory. These larger, still imperfect datasets do not license fine-scale mapping from coarse labels. [16] [17]

Complex learners are not automatically better. In an Ecuador Andes comparison, logistic regression generalized better outside the training area than tree methods that overfit. Goetz et al.’s spatial comparison across Austria found most performance differences among LR, GAM, WoE, SVM and RF were not statistically significant; some complex methods produced spatial artifacts. A recent southern Peru study found random CV estimates 6–18% higher than spatial CV, and the optimism was more pronounced for complex SVM/RF/C5.0 models than LR/LDA. These results support simple baselines and spatial blocking; they do not prove LR will always win. [18] [19]

For the present labels, pixel-based supervised susceptibility is not justified because: (i) point error exceeds the predictor resolution; (ii) polygons are mixed hazard; (iii) many points are event references, not mapped initiation scars; (iv) “absence” is unobserved; and (v) event selection is biased. Candidate methods become defensible only after inventory expansion and a valid evaluation sample. A district-level FR/WoE surface or regularized logistic/GAM could be piloted as exploratory screening once labels and backgrounds are audited. Random forest or boosting should remain a secondary comparator, with depth/leaf constraints, nested tuning inside training folds, spatial CV, calibration and stability analysis.

### 3.4 Positive-unlabeled, presence-only and pseudo-absence methods

The current inventory is closer to a positive-only sample of reported incidents than a conventional case-control dataset. An unreported location or day is not a verified negative. Presence-only methods can compare event locations with sampled background, but output depends on how background is selected and on the process that determines where events are reported. Phillips et al. showed that target-group background can improve presence-only predictions and that background choice may affect performance as much as model choice. Warton et al. illustrate modeling observer/accessibility bias as a separate point-process component. These are ecological/statistical analogues, not a ready-made Rwanda landslide result. [20]

Pseudo-absence generation is a sensitivity choice, not a way to create truth. In one study, different pseudo-absence strategies all produced high AUC while the predicted high-probability area changed substantially. For Rwanda, background points should represent monitored, observable non-event units over a defined time and space; sample at-risk units with comparable access/reporting effort, and report how predictions change across defensible backgrounds. If true absence data are unavailable, use presence-only/PU language and do not report ordinary binary precision or specificity as if labels were complete. [21]

PU learning is potentially relevant if a known-positive set is paired with a defined unlabeled population and assumptions about class prevalence/reporting can be defended. Here the positive labels are themselves biased, and there is no event inventory ascertainment model or known class prior. PU methods do not remove that bias. Transfer learning is similarly conditional: a source-region model can help only if source and Rwanda covariate distributions and process/label definitions overlap. A 10-region landslide transfer study suggests domain adaptation can be useful, but target-domain similarity mattered; foreign labels cannot simply be treated as Rwanda labels. [22]

SMOTE and GAN-generated examples do not add independent real events or fix missing-not-at-random labels. If explored at all, apply augmentation only inside each training fold and compare with no augmentation under held-out events and spatial blocks. No verified source in this review demonstrates that SMOTE or GAN augmentation yields calibrated, spatially independent Rwanda EWS performance at n≈88. Synthetic data could produce false confidence by repeating the same few event geometries and rainfall regimes.

### 3.5 Physical and physics-informed approaches

Physics-based models can supply structure that a small event catalogue cannot learn reliably. SHALSTAB combines topographic convergence, steady-state subsurface flow and infinite-slope stability. SINMAP combines an infinite-slope stability calculation with steady-state hydrology and requires local calibration. TRIGRS models transient infiltration and pore pressure from rainfall through time, then computes cell-wise factor of safety. Their inputs include a DEM and grids/parameters for soil depth, unit weight, cohesion, friction angle, hydraulic conductivity/transmissivity, initial water table or pore pressure, and rainfall history. Model output is conditional on these assumptions, not an observed probability of failure. [23] [24]

Sparse-data experience shows both value and limits. TRIGRS was back-analyzed for two Kerala events; the study recovered plausible failure timing but reported low spatial accuracy and multiple parameter solutions. This is useful as a physically constrained timing hypothesis, not a tested operational forecast. Physics-informed ML could use factor-of-safety scenarios as features or compare occurrence records against physically screened backgrounds, but a factor-of-safety map is not a verified negative label. One Chinese study reported improved AUC after using physics-screened negatives, but its 104 positives and 104 negatives were randomly split and required thousands of borehole inputs. Its result cannot be transported to Rwanda as an expected gain. [25] [26]

Recommended role: first use terrain/hydrology models to organize expert review and identify locations where physical inputs can be obtained. Compare model agreement and sensitivity to uncertain soil parameters. Do not build a regional TRIGRS product until local soil/hydraulic parameters and rainfall histories exist. If a model is run, validate at event and spatial-block level and show uncertainty envelopes, not only a deterministic stability class.

### 3.6 Inventory expansion with satellite imagery

Inventory expansion may create much more value than increasing model complexity. Sentinel-1 SAR can detect some slope changes under cloud, but geometry, layover, aspect, vegetation, polarization and acquisition timing limit performance. In a 32-case Sentinel-1 amplitude study that included a Rwanda event, 27 cases were clearly identified, one only with prior coordinates and four were not visible; that is case-study detection, not a calibrated national accuracy estimate. Sentinel-1 should be combined with field reports and optical/topographic evidence, not treated as a complete cloud-proof detector. [28]

Sentinel-2 and PlanetScope support post-event scar mapping but clouds, haze, vegetation, shadows, seasonal change and bare-soil/road confusion are important in humid highlands. Landslide4Sense contains thousands of labeled image patches and a geographically mixed benchmark, yet the reported U-Net test F1 was 59.92% with precision 52.45% and recall 69.87%. HR-GLDD’s PlanetScope work reported average F1 around 0.70 overall but a 0.56 F1 unseen-event result for its DRC site. A Sentinel-2 change-detection preprint reported test F1 around 0.35 on held-out event patches. These examples show that high-performing benchmark models can degrade sharply on new events and that pixel F1 is not the same as warning skill. [27] [29]

A suitable Rwanda expansion study should: (1) start from an event report, not blind wall-to-wall predictions; (2) inspect pre/post imagery with SAR and optical sensors; (3) label scar, runout, flood and uncertain classes separately; (4) have independent local/geomorphological review; (5) record acquisition date, cloud/vegetation visibility and label confidence; (6) reserve entire events/districts for validation; and (7) release polygons with lineage and license. Foundation models and transfer learning are promising experiments, but the reviewed recent foundation-model result is a preprint on Landslide4Sense with modest improvements over U-Net and no Rwanda/SAR validation. It is a candidate for testing, not evidence that 88 points suffice. [27] [28] [29]

### 3.7 Operational EWS and guidance

Guzzetti et al.’s review of 26 regional, national and global systems found operational forecasting feasible but no accepted universal standard for performance verification. Piciullo et al. reviewed 115 rainfall-threshold papers: 38 used independent validation, 31 validated on calibration data and 46 had no predictive evaluation. Their duration-matrix approach highlights that a warning system is multi-level and area/time dependent; a standard 2×2 table can hide warning duration, event severity and operational consequences. [14] [15]

NASA LHASA demonstrates useful operational scale and the importance of label caveats. LHASA v1’s global system combined susceptibility and near-real-time rainfall; the validation inventory was media/report based and biased. LHASA v2 used XGBoost and multiple rainfall/soil-wetness/terrain features, with a temporal 2015–2018 development period and 2019–2020 evaluation period across seven mapped inventories. It reported an aggregated TPR of 93% versus 45% for v1.1, but unrecorded grid-days were assumed non-events in part of the design. A high TPR from a selected set of mapped inventories is not directly comparable to Rwanda’s incomplete event reports, and FAR/lead time must be examined separately. [15]

Italy’s SIGMA history shows iterative updating and threshold tailoring; comparisons over years reported false-alarm reductions after algorithm changes, but not a clean one-shot untouched holdout. Tuscany’s operational system uses hundreds of gauges and 25 zones with a forecast horizon of up to 48 hours; that horizon is not automatically the realized actionable warning lead time. The Rio de Janeiro municipal system used four warning levels and evaluated alert periods and events; it is not the national CEMADEN system. A low-resource Nepal pilot paired community records and sensors with thresholds but did not report verified independent operational POD/FAR. Colombia’s Inform@Risk case stresses community participation and governance, but was still in test mode rather than a proven ML warning system. [14] [15]

WMO/UNDRR’s people-centred framework has four pillars: risk knowledge; detection, monitoring, analysis and forecasting; warning dissemination and communication; preparedness and response. A Rwanda model is not an EWS unless warnings reach the right people, convey uncertainty and prompt tested action. Include low-tech redundancy, local-language channels, authority roles, accessible procedures, feedback and public complaint routes. [38] [39]

### 3.8 What the methods can and cannot do at n≈88

| Independent, adjudicated events | Justified starting point | Risky / exploratory | Not justified from event count alone |
|---:|---|---|---|
| ~20 | Descriptive inventory audit; physical reasoning; prespecified one-variable rainfall benchmark if rainfall/event windows are reliable; broad alert monitoring | Bayesian prior-driven threshold with very wide intervals; one-parameter model only; transfer as sensitivity analysis | Multivariable ML, tuning, susceptibility pixel classifier, district-specific thresholds, synthetic augmentation claims |
| ~50 | Simple ID/ED thresholds; one or two antecedent features; penalized logistic model only with valid negatives; bootstrap and leave-event-out | Small GAM, WoE/FR, RF/boosting benchmark with stringent constraints; PU/presence-only | Deep models from scratch, numerous interactions, many strata, precise subgroup calibration, deployment claims |
| ~100 | Small predeclared logistic/GAM or hierarchical threshold model; compare with simple baseline; spatial and future-time holdout if enough events | RF/boosting, Bayesian spatial models, transfer learning, event-type strata if supported | Unconstrained feature search; random CV as primary validation; treating pseudo-absences as known negatives |
| ~300 | Multiple interpretable predictors, modest regularized ML, a few prespecified strata; nested spatial/temporal validation | Boosting/RF and transfer with domain-shift checks; physical-surrogate ML | Fine-grain pixel labels without accurate polygons; national performance claim absent external/prospective validation |
| 1,000+ | Broader model comparison, event-type/season variation, calibrated probability and subgroup checks when the events are independent and well observed | Deep/foundation model fine-tuning, hierarchical regional transfer, physics-informed surrogates | Assuming count alone solves observation bias, spatial leakage, label error or nonstationarity |

The table is a planning guide, not a universal sample-size theorem. “Events” means independent, adjudicated triggering episodes with aligned predictor/label support, not raw rows or pixels. Effective sample size, class prevalence, number of model parameters, missingness, spatial coverage, predictor collinearity and deployment shift govern what can be fit. Even with 1,000 records, biased reporting and careless validation can produce misleading results. [8] [14] [18] [19] [22]

## 4. Staged pipeline and data acquisition priorities

### Stage 0 — lock the data definition

Create a versioned incident ledger with parent storm ID, event ID, source-claim ID, occurrence start/end, date precision, landslide process, trigger confidence, administrative location, geometry type, accuracy/error radius, casualty scope and source lineage. Keep event confidence separate from spatial precision. Have MINEMA and district staff adjudicate a stratified sample, with special review of repeated dates, 2018 polygons, district-overlay mismatches and mixed flood/landslide claims. Preserve the current inventory unchanged and publish an auditable crosswalk. [1] [2] [3]

### Stage 1 — rainfall-trigger baseline

**Inputs:** dated and adjudicated rainfall-related events; subdaily/daily gauge records with station metadata; CHIRPS/IMERG/ERA5-Land series and quality flags; district/catchment boundaries; event-location uncertainty; optional soil-moisture stations/model outputs; periods with documented observation coverage and credible non-event surveillance.

**Models:** event-duration or intensity-duration threshold; a simple antecedent rainfall index; a transparent rainfall-plus-wetness baseline; and a prior-constrained Bayesian variant only if the event definition and event/non-event windows are explicit. Compare with published Rwanda threshold values as benchmarks, not as pseudo-ground-truth. No rainfall data should be fabricated or backfilled without a source and quality flag.

**Outputs:** event-window match table; threshold curves with uncertainty bands; maps at the chosen warning-zone scale; probability/alert forecasts only if negatives and temporal alignment are defensible; held-out POD, FAR, CSI/TSS, PR-AUC, Brier and reliability diagnostics.

**Risks:** uncertain dates; rain-grid mismatch; under-reporting; same-storm dependence; product error; unobserved landslides; false alarms. If reliable negatives cannot be built, publish threshold association and uncertainty, not ordinary binary predictive performance.

### Stage 2 — susceptibility baseline

**Inputs:** validated landslide initiation polygons/points with precision and process labels; event or mapping dates; high-quality DEM; lithology/geology; soils and depth; land cover; roads/mining/human modification; hydrology; and an observation/background sampling design that matches reporting coverage.

**Models:** begin with a static physical/topographic screening layer and simple FR/WoE or regularized logistic/GAM baselines. A complex learner is only a comparator. Use presence-only or PU formulation if verified absences do not exist; label background as unlabeled. Only produce 30 m–1 km outputs if the validation locations are precise enough at that scale.

**Outputs:** exploratory relative susceptibility, uncertainty and extrapolation flags, predictor provenance, spatial-block performance, and held-out event maps. Do not call a relative score a probability unless calibrated against an appropriate target population.

**Risks:** positional error, polygon class ambiguity, pseudo-replication, covariate shift, inventory access bias, and apparent sharpness from high-resolution predictors attached to coarse labels.

### Stage 3 — combine hazard and susceptibility carefully

A simple trigger can be combined with susceptibility only after each component has separate validation. A high susceptibility location under low short-term rainfall is not necessarily an imminent alert; rainfall-trigger probability must be conditional on local susceptibility and current hydrologic state. Avoid multiplying two arbitrary scores and labeling the result “risk.” Where event counts cannot support calibrated probabilities, use transparent categorical evidence tiers and explicit “uncertain” state, with expert review.

### Stage 4 — shadow mode and prospective verification

Run the model silently through at least one rainy season, recording the forecast, model version, inputs, missing data, alert level, threshold, uncertainty and time. Have authorized reviewers compare forecasts with independently collected incidents and rainfall. Do not tune a threshold on the final prospective evaluation. Review alert duration, lead time, false alarms, missed events, event detection, spatial coverage and actionability. Repeat for additional seasons before public deployment if event count remains low. Conduct tabletop tests and community/agency exercises before any alert triggers protective action. [14] [15] [38]

### 4.1 Pre-registered validation protocol

1. **Freeze data and model target.** Name the unit (storm/event, district-day or warning-zone-day), date rule, location support, event-type inclusion, eligible observation period and the process for negative/background units. Document duplicates and unresolved events before examining test outcomes.
2. **Group correlated records.** Put same-storm, same-day, duplicate-source and same-polygon-family records in one group. Keep all derived polygon-centroid rows from one source feature in the same fold; preferably use only one representation for occurrence-level model fitting.
3. **Use spatial blocks.** Hold out whole districts/catchments or spatial blocks; select block size before fitting based on the deployment question and data support. Do not place neighboring pixels, points from the same polygon or records from one storm in both train and test. With too few independent areas/events, report that spatial validation is underpowered rather than relaxing to random row splits. [19] [32] [33]
4. **Use temporal tests.** Use leave-one-event/storm-out or leave-one-season-out sensitivity analysis when feasible, plus a chronologically later holdout. The current record’s most recent years are too sparse for a strong retrospective future-period test; report this limitation and prioritize prospective shadow mode. Never select model/hyperparameters on the final test period. [24]
5. **Benchmarks.** Compare (a) no-alert/climatological base rate; (b) simple rainfall threshold using Caine/global curve as a sensitivity comparator; (c) published Rwanda values from Uwihirwe et al.; (d) locally derived fixed ID/ED or antecedent-rainfall threshold; (e) a small regularized logistic/GAM; (f) optional RF/boosting constrained baseline; and (g) LHASA public output only where date, version, spatial unit and data availability can be matched. Do not claim model superiority if studies use different target definitions or observation periods. [4] [5] [10] [15]
6. **Metrics.** Report event-level POD/recall, false-alarm ratio (false alerts among alerts), false-positive rate (false alerts among non-event opportunities), CSI, TSS/Peirce skill, and precision-recall curve/AUPRC. Report ROC-AUC only as secondary discrimination, because class imbalance can make ROC plots appear reassuring. Add Brier score, reliability plot, calibration slope/intercept if a probability is claimed. Show alert duration and lead time separately. Use confidence intervals clustered by storm/season where possible; with very few groups, show raw counts and uncertainty rather than over-precise rates. [25] [26] [35]
7. **Threshold and permutation tests.** Set alert thresholds on training/validation data only and preregister acceptable false-alarm and missed-event ranges with response agencies and communities. Use a blocked permutation test that shuffles labels at the storm/area group level, not individual rows; compare model skill with base-rate/threshold baselines. The current inventory cannot support meaningful permutation testing because no environmental predictors and valid negative opportunities are supplied.
8. **Success criteria.** Before analysis, define minimum held-out event capture, maximum acceptable false-alarm burden per district/season, probability calibration tolerance, stability across rainfall products and threshold intervals, minimum lead time for a protective action, and what constitutes a material improvement over simple baselines. Do not invent numeric targets without risk-owner agreement and operational evidence.
9. **Prospective phase.** Shadow mode for at least one full rainy season, with independent event logging and no automated warning. Publish a season report of every alert and non-alert, missed event, data outage and model uncertainty. If criteria fail or cannot be assessed because too few events occur, retain decision support only and continue data collection.

### 4.2 Additional data to obtain, ranked by impact

| Priority | Data request | Why it matters / minimum fields |
|---|---|---|
| 1 | **MINEMA, districts and emergency services: event-level incident records** | Highest impact for event completeness and negative surveillance. Obtain all reported landslides and compound events, including nonfatal/small failures; event/parent storm IDs, date/time bounds, district/sector/village, coordinates and precision, source, process/trigger confidence, impacts, source scope and observation coverage. Retain unverified claims separately. |
| 2 | **Meteo Rwanda: gauge, AWS and radar/forecast archives** | Daily and subdaily precipitation, station coordinates/elevation, instrument metadata, missing periods, QC flags, service interruptions, intensity/duration, soil moisture where measured, and access/license terms. Needed for rainfall thresholds and independent product evaluation. |
| 3 | **Authors/data custodians: 2018 Karongi mixed-hazard polygon layer and 2024 study inventory** | Obtain actual geometries, class labels, mapping dates, source imagery, inclusion rules, CRS, validation, uncertainty, flood/landslide separation, and license. The QA report notes the 2024 study’s ~750 features are not openly attached in the inspected route; do not silently merge them. |
| 4 | **REMA: 2,544 initiation-point susceptibility layer** | Obtain point lineage, event dates (if any), precise definition of initiation versus mapped/known location, collection method, positional error, validation, CRS, completeness and reuse terms. Do not assume unlabeled points are dated event records. |
| 5 | **Rwanda Mines Board and road/infrastructure custodians** | Georeferenced mining/quarry/road-cut failures and infrastructure works; separate anthropogenic triggers from rainfall-triggered natural slopes. Include date, mechanism, excavation/maintenance context and reporting coverage. |
| 6 | **Geology, soils and terrain agencies/university partners** | DEM and hydrography with metadata; geology/lithology, soil texture/depth and geotechnical properties, land cover, mining/road exposure, slope units. Required for susceptibility or physical models and for scale-aware uncertainty. |
| 7 | **New SAR/optical inventory with field verification** | Event-conditioned Sentinel-1/2 and permitted PlanetScope mapping; separate source scar/runout/flood, imagery visibility, geolocation confidence, expert review, and whole-event held-out labels. Use SAR/optical fusion rather than one sensor. |
| 8 | **Targeted field sensors and community monitoring** | Rain gauges, soil moisture and slope movement at high-priority sites; community incident reports and observer effort. Install only where maintenance, calibration, power, communications and response ownership are funded. |

Share data under written agreements that specify custodian, reuse, publication, attribution, update cycle, quality flags and permitted public release. Protect precise household, fatality and vulnerable-site coordinates where disclosure creates harm; publish aggregated hazard information when possible. Obtain informed participation for community reporting and sensors, do not use reports to penalize communities, and provide feedback and grievance channels. Keep a clear separation between scientific uncertainty and official emergency decisions. The QA report’s first priorities—MINEMA incident records, Rwanda Mines Board, REMA and the unpublished inventories—align with these needs. [3]

## 5. What can and cannot honestly be claimed

### What can be claimed now

- The provided CSV snapshot has 88 curated event rows, 1,071 site/geometry rows, 66 day-precision records and the measured readiness filters documented in this report. [1]
- Event reporting is concentrated in 2007–2020 and in a subset of districts; these are inventory/reporting patterns, not normalized hazard rates. [1] [3]
- The strict temporal candidate set is 25 rows/21 distinct dates under explicit filters, before auditing source duplicates or matching actual rainfall. It is not the model sample size after independence/label review. [1]
- The current tables do not contain measured rainfall, soil moisture, terrain, geology or land cover and do not supply true absences. [1] [2]
- None of the 77 point rows has stated positional accuracy ≤1 km; the 2018 polygon/centroid pair is mixed-hazard and not a clean set of slide scars. [2] [3]
- Literature supports simple, physically interpretable threshold or susceptibility baselines, while emphasizing uncertainty, sampling bias and spatial/temporal validation. Rwanda-specific threshold/product papers are useful reference points but are not independent operational validation of a new model. [10] [11] [14] [19]

### What cannot be claimed now

- **No validated Rwanda rainfall-trigger ML model.** There are no rainfall predictors or verified negative event windows in the supplied tables.
- **No fine-resolution susceptibility map validated by these 88 records.** Location uncertainty and mixed-hazard geometry do not support 30 m–1 km point-level truth.
- **No nationwide probability, return period, district ranking or “risk” estimate.** The record is biased toward visible, fatal or damaging incidents and lacks exposure/reporting denominators.
- **No model accuracy, AUC, false-alarm rate, missed-event rate, lead time or calibration result.** None was estimated from the supplied event/site files. The calendar bootstrap is descriptive only.
- **No effective independent sample size of 88.** The strict candidate pool is 25 records and 21 distinct dates; storm-level and spatial dependence remain unresolved.
- **No claim that a high ROC-AUC from a related Rwanda paper proves transfer.** Prior Rwanda ML work used a different, expanded day-level dataset and random validation; row-level scores do not establish spatial/temporal independence or calibrated probabilities. [31]
- **No claim that synthetic data, transfer learning or complex ML solves missing labels.** These methods require valid evaluation and can reproduce the inventory’s bias.

False alarms and missed events have unequal, context-specific consequences. Too-frequent alerts can exhaust household resources, disrupt livelihoods, erode trust and lead to warning fatigue. A missed event can cost lives and damage homes or infrastructure. The current inventory cannot quantify either trade-off because it does not enumerate all alert opportunities, true negatives, warning actions or event outcomes. Alert levels must therefore be co-designed with MINEMA, Meteo Rwanda, districts and exposed communities, tested in shadow mode, and communicated with explicit confidence/uncertainty. A model score alone is not a public warning.

## 6. Reproducible baseline and deliverables

The baseline script reads the unchanged copies of `events.csv` and `sites.csv`, recomputes the readiness counts, writes year/month summaries and repeated-date review flags, produces two figures, and performs a fixed-seed bootstrap of the actual day-precision March–May share. It does not create rainfall values or claim threshold stability. An optional validation scaffold requires user-supplied real predictors and defensible labels; with no model dataset, it records “NOT RUN” and explains what is missing.

- [Reproducible report and analysis files directory](/home/ubuntu/rwanda_ews/)
- [Readiness baseline script](/home/ubuntu/rwanda_ews/readiness_baseline.py)
- [README and run instructions](/home/ubuntu/rwanda_ews/README.md)
- [Requirements](/home/ubuntu/rwanda_ews/requirements.txt)
- [Evidence table CSV](/home/ubuntu/rwanda_ews/evidence_table.csv)
- [Readiness table CSV](/home/ubuntu/rwanda_ews/outputs/readiness_table.csv)
- [Annual event-count figure](/home/ubuntu/rwanda_ews/outputs/events_by_year.png)
- [Monthly event-count figure](/home/ubuntu/rwanda_ews/outputs/events_by_month.png)
- [Calendar bootstrap output](/home/ubuntu/rwanda_ews/outputs/calendar_bootstrap.json)
- [Same-day manual review flags](/home/ubuntu/rwanda_ews/outputs/same_day_review_flags.csv)
- [Unchanged events.csv copy](/home/ubuntu/rwanda_ews/events.csv)
- [Unchanged sites.csv copy](/home/ubuntu/rwanda_ews/sites.csv)

Run with Python 3 and the packages in `requirements.txt`:

```bash
python3 readiness_baseline.py --events events.csv --sites sites.csv --out outputs
```

### References

[1]: https://github.com/theoneste2060/rwanda_landslide_inventory/tree/main/v2/repo_readonly/v2 "Rwanda landslide inventory v2 read-only tables"
[2]: https://raw.githubusercontent.com/theoneste2060/rwanda_landslide_inventory/main/v2/repo_readonly/v2/DATA_DICTIONARY.md "Rwanda landslide inventory v2 data dictionary"
[3]: https://raw.githubusercontent.com/theoneste2060/rwanda_landslide_inventory/main/v2/repo_readonly/v2/QA_REPORT.md "Rwanda landslide inventory v2 QA report"
[4]: https://doi.org/10.2307/520449 "The rainfall intensity-duration control of shallow landslides and debris flows"
[5]: https://doi.org/10.1007/s10346-007-0112-1 "The rainfall intensity-duration control of shallow landslides and debris flows: an update"
[6]: https://nhess.copernicus.org/articles/10/447/2010/ "Rainfall thresholds for the possible occurrence of landslides in Italy"
[7]: https://doi.org/10.1029/2012JF002367 "Probabilistic rainfall thresholds for landslide occurrence using a Bayesian approach"
[8]: https://doi.org/10.1016/j.geomorph.2017.02.001 "Statistical approaches for the definition of landslide rainfall thresholds and their uncertainty using rain gauge and satellite data"
[9]: https://nhess.copernicus.org/articles/19/775/2019/ "A susceptibility-based rainfall threshold approach for landslide occurrence in the western branch of the East African Rift"
[10]: https://doi.org/10.1007/s10346-020-01457-9 "Landslide precipitation thresholds in Rwanda"
[11]: https://doi.org/10.5194/nhess-22-3641-2022 "Potential of satellite-derived hydro-meteorological information for landslide initiation thresholds in Rwanda"
[12]: https://doi.org/10.1002/qj.3244 "Validation of the CHIRPS satellite rainfall estimates over eastern Africa"
[13]: https://doi.org/10.1007/s00703-024-01008-0 "Evaluation of ERA5 and CHIRPS rainfall estimates against observations across Ethiopia"
[14]: https://doi.org/10.1007/s10346-020-01486-4 "Standards for the performance assessment of territorial landslide early warning systems"
[15]: https://doi.org/10.1016/j.earscirev.2019.102973 "Geographical landslide early warning systems"
[16]: https://www.sciencedirect.com/science/article/pii/S0048969718351192 "Comparing probabilistic and statistical methods in landslide susceptibility modeling in Rwanda"
[17]: https://doi.org/10.1007/s10668-019-00557-4 "Landslide susceptibility and influencing factors analysis in Rwanda"
[18]: https://www.sciencedirect.com/science/article/abs/pii/S0098300415000904 "Evaluating machine learning and statistical prediction techniques for landslide susceptibility modeling"
[19]: https://doi.org/10.3390/rs17020213 "Random cross-validation produces biased assessment of machine learning performance in regional landslide susceptibility prediction"
[20]: https://doi.org/10.1890/07-2153.1 "Sample selection bias and presence-only distribution models"
[21]: https://doi.org/10.1371/journal.pone.0044486 "Pseudoabsence generation strategies for species distribution models"
[22]: https://doi.org/10.5194/gmd-15-8765-2022 "Transfer learning for landslide susceptibility modeling using domain adaptation and case-based reasoning"
[23]: https://doi.org/10.1029/93WR02979 "A physically based model for the topographic control on shallow landsliding"
[24]: https://pubs.usgs.gov/of/2008/1159/ "TRIGRS, version 2.0: a Fortran program for transient rainfall infiltration and grid-based regional slope-stability analysis"
[25]: https://doi.org/10.1007/s10346-018-1044-7 "Regional-scale back-analysis using TRIGRS in sparse data regions"
[26]: https://doi.org/10.1016/j.jrmge.2023.11.039 "Physics-informed optimization for a data-driven approach in landslide susceptibility evaluation"
[27]: https://doi.org/10.1109/JSTARS.2022.3220845 "The Outcome of the 2022 Landslide4Sense Competition"
[28]: https://doi.org/10.3390/rs11070760 "Sentinel-1 SAR amplitude imagery for rapid landslide detection"
[29]: https://doi.org/10.5194/essd-15-3283-2023 "HR-GLDD: a globally distributed dataset using generalized deep learning for rapid landslide mapping"
[30]: https://nhess.copernicus.org/articles/23/3261/2023/ "Landslide initiation thresholds in data-sparse regions: application to landslide early warning criteria in Sitka, Alaska"
[31]: https://doi.org/10.3390/ijerph17114147 "Rainfall-induced landslide prediction using machine learning models: the case of Ngororero District, Rwanda"
[32]: https://doi.org/10.1111/ecog.02881 "Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure"
[33]: https://doi.org/10.1111/2041-210X.13107 "blockCV: an R package for generating spatially or environmentally separated folds"
[34]: https://doi.org/10.1371/journal.pone.0118432 "The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets"
[35]: https://doi.org/10.1111/j.1467-9868.2007.00587.x "Probabilistic forecasts, calibration and sharpness"
[36]: https://arxiv.org/abs/2107.07511 "Conformal prediction: a gentle introduction"
[37]: https://www.sciencedirect.com/science/article/pii/S2212420914000910 "The Rio de Janeiro early warning system for rainfall-induced landslides: analysis of performance for the years 2010–2013"
[38]: https://wmo.int/activities/early-warnings-all/wmo-and-early-warnings-all-initiative "WMO and the Early Warnings for All initiative"
[39]: https://www.undrr.org/resource/developing-participatory-landslide-early-warning-system-informrisk-project-colombia "Developing a participatory landslide early warning system in Colombia"
