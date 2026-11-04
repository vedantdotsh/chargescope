# ChargeScope - data and attribution / Daten und Quellen

## English

The website uses 36 derived district/scenario aggregates from the pinned diagnostic pilot. Berlin is separate from the 18 Brandenburg districts and never enters their distribution or ranking. This is not a nationally validated release.

- Bundesnetzagentur.de charging register: reference 1 September 2026; source metadata records CC BY 4.0. https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/E-Mobilitaet/Ladesaeulenkarte/start.html
- Bundesamt fuer Kartographie und Geodaesie (BKG), VG250-EW population: reference 31 December 2025; source metadata records dl-de/by-2.0. https://gdz.bkg.bund.de/
- Licenses: https://creativecommons.org/licenses/by/4.0/ and https://www.govdata.de/dl-de/by-2-0 . Retain additional statistical attribution in independently obtained BKG data.

Rate = points / residents x 10,000. Regional rates use ratios of sums. Descending competition ranks share positions for ties. Capacity is counted once per installation: kW / 1,000 = MW. Installation records are not unique physical sites. Nominal capacity is not delivered energy.

The boxplot uses type-7 quartiles and observed whiskers within 1.5 IQR fences. All 18 districts are equally weighted. Vertical dot packing prevents overlap without changing horizontal rates. The hypothetical distribution is recalculated; registered outlines remain visible.

The flagged 513-point Oder-Spree group changes 832 to 319 points, 22,057 to 16,414 nominal kW and 717 to 204 installation records. Population remains 179,142. This is not a corrected register or a claim about public access. Thirty-five Brandenburg points have unresolved geographical agreement. Different source dates do not form a time series. No demand, utilization, adequacy, ROI or site-suitability conclusion follows.

Four English slides come from the Power BI Desktop PDF export of 4 November 2026, rendered at 2560px width. No chart pixels were redrawn. Standalone enlargement loads the full PNG; the self-contained preview embeds compressed thumbnails only. The source-project download includes the Report and SemanticModel, but not raw data or imported cache: data setup and a successful Desktop refresh are required. The GitHub repository and v1.0.0 release are public.

## Deutsch

Alle 18 brandenburgischen Kreise werden verglichen; Berlin bleibt separat. Die 36 Kreis-/Szenarioaggregate sind ein diagnostischer Pilot, keine national validierte Freigabe. Quellen: Bundesnetzagentur.de, Registerstand 1. September 2026 (CC BY 4.0), und BKG VG250-EW, Bevoelkerungsstand 31. Dezember 2025 (dl-de/by-2.0). Zusaetzliche statistische Quellenangaben des BKG-Pakets beibehalten.

Quote = Ladepunkte / Einwohner x 10.000. Landesquoten entstehen aus Summen, nicht aus dem Mittel der Kreisquoten. Quartile: Typ 7; Whisker: beobachtete Werte innerhalb 1,5 IQR. Nennleistung wird je Installation einmal gezaehlt; Installationsdatensaetze sind keine eindeutigen Standorte. Der hypothetische Ausschluss ist keine Registerkorrektur. Oeffentlicher Zugang, Nutzung und Bedarf sind nicht nachgewiesen. Unterschiedliche Stichtage ergeben keine Zeitreihe.

Die vier Power-BI-Aufnahmen bleiben Englisch. Die Vollansicht verwendet die vollaufgeloesten PNGs; die kompakte Vorschau nur verkleinerte Bilder. Das Power-BI-Quellprojekt erfordert eigene Daten und eine erfolgreiche Aktualisierung. GitHub-Repository und Version v1.0.0 sind öffentlich.
