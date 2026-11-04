# ChargeScope design options

Open `review.html` to compare the preserved current design with three alternatives:

- **Comparison workbench** (`workbench/index.html`): compact controls; distribution and full-cohort charts side by side on wide screens.
- **District profile** (`profile/index.html`): selected district facts first, with the comparison beside them and the whole cohort below.
- **Findings first** (`guided/index.html`): three question-led starting points set the actual district, metric and scenario controls.

All four reuse the same data, numerical logic, language/theme preferences, gallery and findings drawer. Selections highlight the chosen and comparison districts without removing cohort members. Only language and appearance persist. No framework, account storage or backend is used.

The review embeds compressed images once. Standalone options load the original PNGs from `../website-combined/assets`. These are unscaled crops of genuine 2560px Power BI exports. The public download is the existing v1.0.0 PBIP source package, not a preloaded PBIX. Its pinned-data setup remains required.

Copy follows loose plain-language principles: short sentences, common verbs and consistent terms. No ASD-STE100 compliance or percentage score is claimed. Sources: https://www.asd-ste100.org/about.html ; visual guidance: https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md . Existing data attribution is unchanged. No live website has been deployed.

## Rebuild and check

From the repository root, run `python website-variations-v3/build.py` to regenerate the three standalone options and compact review from the shared website files. The build uses only the Python standard library. Run `node website-combined/logic.test.js` for numerical checks. With Python Playwright and its Chromium browser installed, run `python website-variations-v3/check.py` and `python website-variations-v3/check-extra.py` for the offline browser checks. They write local evidence under `.scratch/v3`, not into report or data folders.
