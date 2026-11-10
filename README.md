# ChargeScope

**When can you trust a charging-point ranking?** This analysis of Germany's public charging register tests how counts, population and concentrated supply change regional comparisons. Oder-Spree ranks **17 of 400** districts by charging points per 10,000 residents, but **285** when every district's largest single-site group is set aside and all districts are re-ranked; **37 districts move 20+ places**. Use rankings to decide where to investigate, not to conclude where provision is sufficient: show counts beside rates and check districts where one site carries a large share.

[Read the interactive analysis](https://analysis.madebyved.com/chargescope/) · [Portfolio](https://analysis.madebyved.com/) · [Download Power BI source](https://github.com/vedantdotsh/chargescope/releases/download/v1.0.0/ChargeScope-PowerBI-source.zip)

## What's in here

| Start here | What it shows |
| --- | --- |
| [Metrics SQL](chargescope/metrics.sql) · [Portfolio SQL](chargescope/portfolio.sql) | Aggregation, rates, rankings and report tables |
| [Python pipeline](chargescope/pipeline.py) · [Portfolio builder](chargescope/portfolio.py) · [CLI](chargescope/__main__.py) | Parsing, reconciliation, geographic diagnostics and reproducible outputs |
| [National aggregation](national/build_national_payload.py) · [Its tests](national/tests/test_national_payload.py) · [Public aggregates](data/national-story.json) | The separate computation feeding the national website |
| [Pipeline tests](tests) · [Power BI package tests](tools/test_source_package.py) | Synthetic contract, SQL parity and safety checks |
| [Power BI project](powerbi/portfolio-final/ChargeScope.pbip) · [Report generator](powerbi/build_report.py) | Four-page Brandenburg case study; source project, not a preloaded PBIX |
| [Slide 1](website/assets/power-bi-1.png) · [Slide 2](website/assets/power-bi-2.png) · [Slide 3](website/assets/power-bi-3.png) · [Slide 4](website/assets/power-bi-4.png) | English report exports |
| [ChargeScope source](website/project/src) · [Build](website/project/build.py) · [Browser tests](website/project/tests) · [Portfolio home](website/index.html) | The published website, with portable build paths |
| [Method and sources](SOURCES.md) · [Source inventory](data/source-manifest.json) | Definitions, pinned hashes, attribution and limits |

## Method in brief

- A **point** serves one vehicle at a time; connector entries are not extra points. An **installation** is one register record, not necessarily a physical site. Nominal kW is counted once per installation, not once per connector.
- Rate = points ÷ residents × 10,000; regional rates are ratios of sums. Competition ranks give ties the same position. Quartiles use type 7, with observed whiskers within 1.5 IQR.
- A **single-site group** contains records from one operator at one coordinate. It is a grouping rule, not a verified physical-site or access boundary.
- **Brandenburg:** exclude one flagged 513-point group in Oder-Spree. Its count changes from 832 to 319, rate from 46.4 to 17.8, and rank from 1 to 11 among 18 districts. Berlin is separate context, never ranked with Brandenburg.
- **Germany:** exclude every district's own largest group simultaneously, then re-rank all 400 districts. Oder-Spree moves 17 → 285; 37 move 20+ places. Neither test corrects the register or establishes public access.

## Limits

Registered supply is not demand, utilisation, availability or adequacy. The register (1 September 2026) and population (31 December 2025) have different dates. This is a **diagnostic pilot, not spatially validated**; label–coordinate agreement depends on an unconfirmed WGS84 assumption. Hanau's unmatched 249 points remain in Hessen's total but unassigned to any district; Main-Kinzig-Kreis's source-label rate is not a validated provision measure.

Current public access of single-site groups is unverified. In February 2024, [Tesla described its factory car-park chargers](https://twitter.com/gigafactories/status/1761071149142708363) as serving employees, visitors and guests and as public and free to use; [ecomento](https://ecomento.de/2024/02/27/deutsche-tesla-fabrik-bietet-ueber-500-oeffentliche-lademoeglichkeiten) and [electrive](https://www.electrive.net/2025/04/14/tesla-fabrik-gruenheide-hat-den-groessten-ladepark-der-welt) reported this too. Those statements do not verify access to each register record today.

## Reproduce

Python 3.13 and [uv](https://docs.astral.sh/uv/) are required. From the repository root:

~~~sh
uv sync
uv run pytest
uv run python website/project/build.py
uv run python website/project/run_gate.py
~~~

The browser gate uses installed **Google Chrome, headless only**, through Playwright; install Chrome separately. Open `website/index.html` to view the portfolio and `website/chargescope/index.html` for the analysis. The build checks the published aggregate hashes and needs no raw data.

`pytest` runs synthetic pipeline/SQL, national-rule and Power BI source-package checks. Source-backed tests explicitly skip without the pinned raw files and bundle. Historical Power BI archive/Desktop checks and website comparisons requiring private register evidence or earlier unpublished builds are **not shipped**. The portable website gate checks the aggregate payload, display, layout, motion and regressions sequentially; it also captures screenshots. It does not certify a refreshed Desktop report or independently reproduce the original raw-data snapshot.

To regenerate the data and refresh Power BI:

1. Obtain the three source files independently and verify [the inventory](data/source-manifest.json). The raw folder also needs the original `manifest.json` acquisition record: the concise public inventory is not that record. BKG's `aktuell` URL can advance; do not substitute a newer snapshot silently.
2. Run `uv run python -m chargescope --raw <source-folder> --out <bundle-output>`. Inspect the conservation report and diagnostic status, not just the exit code.
3. Run `uv run python national/build_national_payload.py --raw <source-folder> --bundle <complete-pinned-run-folder> --out <aggregate-output>`. The national builder checks the historical bundle and raw hashes. If those exact inputs are unavailable, use the published aggregates and slides rather than claim a faithful rebuild.
4. Verify the run's seven import CSVs against [SOURCE_PACKAGE.json](powerbi/portfolio-final/SOURCE_PACKAGE.json), then run `uv run python tools/setup_powerbi.py --project powerbi/portfolio-final/ChargeScope.pbip --bundle <complete-run-folder>` on a copy of the Power BI project.
5. Open the PBIP in Power BI Desktop with its Report and SemanticModel folders adjacent, refresh, and save only after a successful refresh. No imported cache or raw files are supplied. `powerbi/build_report.py` generates a report; avoid overwriting an edited report without a backup.

## Sources and licences

- **Bundesnetzagentur.de**, [charging register](https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/E-Mobilitaet/start.html), 1 September 2026. Source metadata records [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
- **Bundesamt für Kartographie und Geodäsie (BKG)**, [VG250-EW](https://gdz.bkg.bund.de/), population and boundaries at 31 December 2025. Source metadata records [Datenlizenz Deutschland – Namensnennung – Version 2.0](https://www.govdata.de/dl-de/by-2-0). Retain the additional statistical attribution supplied with the BKG package.

Raw data is **not redistributed**: redistribution rights have not been independently verified for this publication. Only derived district aggregates and reformatted charts are included, not installation/point extracts or model caches. No new licence or exclusive human-authorship claim is asserted over third-party material. Full definitions and caveats: [SOURCES.md](SOURCES.md).

**Vedant Patil** · [LinkedIn](https://linkedin.com/in/patilvedant)
