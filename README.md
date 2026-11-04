# ChargeScope

Compare registered charging provision across Brandenburg's 18 districts, with Berlin as separate context.

The registered Oder-Spree rate ranks first. Hypothetically excluding one flagged 513-point group moves it to eleventh. This is a sensitivity check, not a register correction or a before/after comparison. Public access is unverified. Supply counts do not establish demand, utilization, adequacy or investment suitability.

## Explore

- Open `website-combined/index.html` for English/German, light/dark, connected district comparisons, a boxplot and nominal-capacity charts.
- Four English Power BI slides are genuine Desktop PDF exports rendered at 2560px width. Gallery thumbnails are compressed; enlargement loads the full PNG. `review.html` is a compact self-contained preview and uses thumbnail-quality images only.
- The repository and release downloads are private. Sign into an account with repository access: https://github.com/vedantdotsh/chargescope . No public website is deployed.

## Power BI source project

The download contains `ChargeScope.pbip` **and both complete Report/SemanticModel folders**. It is not a PBIX and contains no imported cache, credentials, personal settings or raw registry data. It is not a one-click preloaded report.

1. Install current Power BI Desktop with Power BI Project support. Use a copy of this source package, not an already open working report.
2. Obtain the source files independently from their providers, retain their licenses, and verify the hashes in `data/source-manifest.json`. The BKG `aktuell` URL may advance: a newer download is not the pinned snapshot. Do not silently substitute it.
3. With Python 3.13, run `uv sync`, then `uv run python -m chargescope --raw <source-folder> --out <bundle-output>`. The source folder must contain the three pinned files and their original `manifest.json` acquisition record. `data/source-manifest.json` is a concise provider/hash inventory, not the full historical acquisition record. This can take time. A diagnostic/non-release status is intentional; inspect its conservation report rather than treating the process exit code as national validation. No raw data is bundled here.
4. Locate the resulting complete run folder. Its seven import CSVs must match `powerbi/portfolio-final/SOURCE_PACKAGE.json`. If the exact historical inputs are unavailable, the historical report cannot be refreshed faithfully; keep the screenshots as historical evidence instead.
5. Before opening Desktop, run `python tools/setup_powerbi.py --project powerbi/portfolio-final/ChargeScope.pbip --bundle <complete-run-folder>`. The script validates all seven hashes and changes only this exported model's `BundlePath`. No machine-specific source path is shipped.
6. Open that PBIP and select Refresh. Save only after successful refresh. Keep Report and SemanticModel adjacent. No refresh or Desktop reopen of this exported package has been claimed.

`powerbi/build_report.py` generates a new report from the pinned bundle; do not run its overwrite option on user-edited reports without a backup. `chargescope/metrics.sql`, `chargescope/portfolio.sql` and the Python modules contain the transformations. The source package omits the old report archive and internal acceptance logs, so historical-archive tests from the working project are not shipped as a purported self-contained suite.

## Definitions and sources

Rate = points / residents x 10,000. Regional rates use ratios of sums. District rankings exclude Berlin; ties share competition ranks. Quartiles use type 7 and observed whiskers within 1.5 IQR. Nominal capacity is counted once per installation, not per connector. Installation records are not unique physical sites. Thirty-five Brandenburg points have unresolved geographical agreement. Website aggregates are diagnostic, not a nationally validated release.

- Bundesnetzagentur.de charging register, reference 1 September 2026; source metadata records CC BY 4.0. https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/E-Mobilitaet/Ladesaeulenkarte/start.html
- Bundesamt fuer Kartographie und Geodaesie (BKG), VG250-EW, population reference 31 December 2025; source metadata records Datenlizenz Deutschland - Namensnennung - Version 2.0. https://gdz.bkg.bund.de/
- License texts: https://creativecommons.org/licenses/by/4.0/ and https://www.govdata.de/dl-de/by-2-0 . Retain any additional statistical attribution supplied with the independently obtained BKG package.

The website contains derived district aggregates and reformatted charts. The two source dates differ and do not form a time series. Raw-data redistribution has not been independently verified for this publication, so national raw files, installation/point extracts and imported model caches are deliberately absent. No new license or exclusive human-authorship claim is asserted over third-party material.

## Checks

`node website-combined/logic.test.js` checks the standalone numerical logic. The working-project finishing pass also exercises the website in Chromium and compares the saved PBIR/model against temporary generation. See `VERIFICATION.md` for the exact completed checks and limits.
