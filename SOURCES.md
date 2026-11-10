# ChargeScope: data, licences and method / Daten, Lizenzen und Methode

Status: DIAGNOSTIC_PILOT, `validatedReleaseEligible: false`. Aggregates for Germany, 16 states and 400 districts. Not spatially validated and not a planning release. The site shows a compact version of this in "Method & sources".

## Sources

- Bundesnetzagentur, Ladesäulenregister, CSV list of 1 September 2026 (SHA-256 `cdd8e38f1fa7e8512bd97caa8cf77e9f875436be1f8fe3fe1f2bd9789a504c5b`): 116,443 installations, 209,136 charging points, 9,086,797.5 nominal kW. Attribution: Bundesnetzagentur.de. Licence: CC BY 4.0. https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/E-Mobilitaet/start.html
- Bundesamt für Kartographie und Geodäsie (BKG), VG250-EW, population and boundaries of 31 December 2025 (SHA-256 `0ee5854c5e637e53362db9dcdf889ff9c57aa7f066a3b228f9fba14fcb570754`): 83,467,117 residents. Licence: Datenlizenz Deutschland – Namensnennung – Version 2.0 (dl-de/by-2.0). Attribution as recorded in the payload (`meta.population.attribution`): "Bundesamt fuer Kartographie und Geodaesie; statistical attribution retained in package". https://gdz.bkg.bund.de/
- Licences: https://creativecommons.org/licenses/by/4.0/ and https://www.govdata.de/dl-de/by-2-0. Licence text is inherited from the project manifest and was not re-checked online for this build.
- Aggregates shipped on the site: `data/national-story.json` (same content as `data/national-story.js`), schema `chargescope-national-story/1`. No coordinates, operators, register IDs, EVSE IDs, public keys or addresses.

## Method

- A point is one source point group (one vehicle at a time); connector entries are not points. An installation is one register record, not a physical site.
- Nominal kW is counted once per installation. It is reported capacity, not energy, use or availability. 1,000 kW = 1 MW.
- Rate = points ÷ residents × 10,000, as a ratio of sums. Ranks are competition ranks; ties share a position. Quartiles are type 7; whiskers reach observed values within 1.5 IQR.
- Above 22 kW: a point's highest connector power is above 22 kW (Bundesnetzagentur class edges). A power class, not coverage.
- States use the source `Bundesland` column. Districts use the source `Kreis/kreisfreie Stadt` label matched to VG250 `BEZ GEN`; eight Bavarian labels differ only by spacing and are matched by a unique same-type, same-state normalised name.
- Hanau: 144 installations and 249 points labelled "Kreisfreie Stadt Hanau" are in Hessen's state total but in no district. They were not reassigned. Main-Kinzig-Kreis's source-label rate (17.5) is therefore not a validated rate and is never presented as low provision.
- Label–coordinate agreement is a diagnostic only, conditional on an unconfirmed WGS84 assumption. 13 districts fall below 95%.
- Brandenburg case study: the hypothetical exclusion leaves out one flagged coordinate group of 513 single-point, 11 kW installations in Oder-Spree: 832 → 319 points, 46.4 → 17.8 per 10,000, rank 1 → 11 of 18. Berlin is separate context and never ranked with Brandenburg.
- National sensitivity: every district's own largest same-coordinate, same-operator group is set aside at the same time and the 400 districts are re-ranked. Oder-Spree moves from rank 17 to 285. 37 districts move 20 or more places, 7 move 50 or more.
- Neither sensitivity is a correction or a claim about public access.

## Interpretation limits

- No demand, adequacy, return on investment, utilisation or availability conclusion follows.
- Register (1 Sep 2026) and population (31 Dec 2025) have different dates; nothing is a time series.
- The register lists completed notification procedures only. The Bundesnetzagentur statistics workbook (214,334 points) also counts procedures not yet complete; it is a different population and is not reconciled with the register.
- Open checks: coordinate reference system, unresolved geographic assignments, public access of large co-located groups.

## Report and download

The four English slides are screenshots of the Power BI report for the Brandenburg case study (18 districts), not the national figures. The source project is public on GitHub with a v1.0.0 release (https://github.com/vedantdotsh/chargescope/releases/tag/v1.0.0); it is a PBIP source project that needs your own data setup and refresh, and contains no preloaded PBIX.

## DE

Diagnostischer Pilot, räumlich nicht validiert. Quellen: Bundesnetzagentur, Ladesäulenregister vom 1. September 2026 (CC BY 4.0, Bundesnetzagentur.de); BKG VG250-EW, Bevölkerungsstand 31. Dezember 2025 (dl-de/by-2.0). Quote = Ladepunkte ÷ Einwohner × 10.000. Länder nach Quellspalte Bundesland, Kreise nach Quellbezeichnung. Hanau (249 Ladepunkte) zählt zu Hessen, aber zu keinem Kreis. Beide Sensitivitäten sind keine Korrektur und keine Aussage über Zugang. Keine Aussage zu Bedarf, Angemessenheit, Rendite, Auslastung oder Verfügbarkeit. Die Power-BI-Folien zeigen die Brandenburg-Fallstudie.
