"""Tests for the national story payload. stdlib only.

Run:  python -I national/tests/test_national_payload.py

Group A tests the builder's own rules on synthetic records (no source files needed).
Group B re-derives facts from the original bytes with code that does not call the
builder, and cross-checks the builder against the pinned bundle that the validated
pandas/geopandas pipeline produced and against the deployed site data (read-only).
"""

from __future__ import annotations

import collections
import csv
import hashlib
import importlib.util
import json
import re
import sqlite3
import unittest
import zipfile
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
spec = importlib.util.spec_from_file_location("builder", HERE.parent / "build_national_payload.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

RAW = PROJECT / "data" / "raw"
BUNDLE = PROJECT / "data" / "work" / "pilot" / "runs" / builder.PINNED_BUNDLE
DEPLOYED = PROJECT / "data" / "historical-brandenburg.js"
SOURCES_PRESENT = all((RAW / n).exists() for n in ("reg_0901.csv", "stats.xlsx", "vg250ew.zip", "manifest.json")) \
    and BUNDLE.exists()

_cache: dict = {}


def payload():
    if "payload" not in _cache:
        _cache["payload"] = builder.build(RAW, BUNDLE)
    return _cache["payload"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def independent_rows():
    """Re-read the register without the builder: header found by position, DictReader, Fraction sums."""
    with (RAW / "reg_0901.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        for _ in range(10):
            next(handle)
        return list(csv.DictReader(handle, delimiter=";"))


def fraction(text: str) -> Fraction:
    text = text.strip().replace(".", "").replace(",", ".") if "," in text else text.strip()
    return Fraction(text)


def rec(declared=1, points=(Decimal(11),), nominal=Decimal(11), **kw):
    base = {"id": "x", "declared": declared, "reconciles": declared == len(points) and declared is not None,
            "nominal": nominal, "points": list(points), "connectorTokens": len(points), "coord": ("a", "b"),
            "operator": "op", "flagged": False}
    base.update(kw)
    return base


# ------------------------------------------------------------------ Group A: rules on synthetic data

class RuleTests(unittest.TestCase):
    def test_german_numbers(self):
        p = builder.parse_german_number
        self.assertEqual(p("3,7"), Decimal("3.7"))
        self.assertEqual(p("1.234,5"), Decimal("1234.5"))
        self.assertEqual(p("22"), Decimal(22))
        self.assertIsNone(p(""))
        self.assertIsNone(p("  "))
        with self.assertRaises(Exception):
            p("abc")

    def test_connector_tokens_do_not_create_points(self):
        kw, n_conn = builder.parse_point_slot("AC Typ 2; AC Schuko", "22; 22")
        self.assertEqual((kw, n_conn), (Decimal(22), 2))
        kw, n_conn = builder.parse_point_slot("CCS; CHAdeMO", "150; 50")
        self.assertEqual(kw, Decimal(150))  # highest connector on the point, still one point

    def test_nominal_capacity_counted_once_per_installation(self):
        two_points_22 = rec(declared=2, points=(Decimal(22), Decimal(22)), nominal=Decimal(44))
        agg = builder.aggregate([two_points_22])
        self.assertEqual(agg["kwDec"], Decimal(44))  # not 88, not points x nominal
        self.assertEqual(agg["pts"], 2)
        self.assertEqual(agg["inst"], 1)

    def test_missing_power_is_null_not_zero(self):
        agg = builder.aggregate([rec(nominal=None, points=(None,))])
        self.assertIsNone(agg["kwDec"])
        self.assertEqual(agg["kwMissingInst"], 1)
        self.assertEqual(agg["ptsPowerUnknown"], 1)
        row = builder.row_metrics(agg, 1000, Decimal("10.00"))
        self.assertIsNone(row["nominalKw"])
        self.assertIsNone(row["nominalKwPer1000Residents"])
        self.assertEqual(sum(row["pointsByPower"].values()), 0)

    def test_partial_power_coverage_is_exposed(self):
        agg = builder.aggregate([rec(nominal=Decimal(50)), rec(nominal=None, points=(None,))])
        self.assertEqual((agg["kwDec"], agg["kwKnownInst"], agg["kwMissingInst"]), (Decimal(50), 1, 1))

    def test_group_mismatch_is_quarantined_not_counted(self):
        bad = rec(declared=3, points=(Decimal(11),))
        agg = builder.aggregate([bad, rec()])
        self.assertEqual((agg["pts"], agg["ptsQuarantined"], agg["inst"]), (1, 3, 2))

    def test_rates_are_ratio_of_sums_and_na_on_bad_denominator(self):
        self.assertIsNone(builder.rate(5, 0, 10000))
        self.assertIsNone(builder.rate(5, None, 10000))
        self.assertAlmostEqual(builder.rate(5, 1000, 10000), 50.0)
        self.assertIsNone(builder.rate(None, 1000, 10000))

    def test_competition_ranks_ties_and_missing(self):
        ranks = builder.competition_ranks({"a": 3.0, "b": 3.0, "c": 1.0, "d": None})
        self.assertEqual(ranks, {"a": 1, "b": 1, "c": 3, "d": None})

    def test_power_class_edges(self):
        c = builder.power_class
        self.assertEqual([c(Decimal(x)) for x in ("3.7", "3.8", "15", "22", "22.1", "149", "150", "299", "300")],
                         ["le3_7", "gt3_7to15", "gt3_7to15", "gt15to22", "gt22to49", "gt59to149",
                          "gt149to299", "gt149to299", "gt299"])
        self.assertIsNone(c(None))

    def test_spacing_alias_is_unique_same_state_only(self):
        kreise = [
            {"ars": "09186", "name": "Pfaffenhofen a.d.Ilm", "bez": "Landkreis", "state": "09"},
            {"ars": "09999", "name": "Pfaffenhofen a. d. Ilm", "bez": "Landkreis", "state": "09"},  # ambiguous twin
            {"ars": "05111", "name": "Neumarkt i.d.OPf.", "bez": "Landkreis", "state": "05"},
            {"ars": "09373", "name": "Neumarkt i.d.OPf.", "bez": "Kreisfreie Stadt", "state": "09"},
        ]
        records = [{"label": "Landkreis Pfaffenhofen a.d. Ilm", "state": "Bayern"},
                   {"label": "Landkreis Neumarkt i.d. OPf.", "state": "Bayern"},
                   {"label": "Kreisfreie Stadt Hanau", "state": "Hessen"}]
        mapping, aliases, unmapped = builder.build_label_map(kreise, records, {"Bayern": "09", "Hessen": "06"})
        self.assertNotIn("Landkreis Pfaffenhofen a.d. Ilm", mapping)  # two candidates -> stays unmapped
        self.assertNotIn("Landkreis Neumarkt i.d. OPf.", mapping)     # only candidate is in another state
        self.assertEqual(set(unmapped), {"Landkreis Pfaffenhofen a.d. Ilm", "Landkreis Neumarkt i.d. OPf.",
                                         "Kreisfreie Stadt Hanau"})
        self.assertEqual(aliases, [])

    def test_quartiles_type7(self):
        s = builder.quartile_summary([1, 2, 3, 4, 5, 100])
        self.assertEqual((s["q1"], s["median"], s["q3"]), (2.25, 3.5, 4.75))
        self.assertEqual((s["whiskerHigh"], s["outliers"]), (5, 1))

    def test_duplicate_and_blank_ids_are_rejected(self):
        import tempfile
        header = ";".join(builder.EXPECTED_HEADER)
        preamble = "\n".join(["Ladesäulenregister"] + [""] * 6 + ["Letzte Aktualisierung vom: 01.09.2026", "", "x"])
        row = ["1"] + [""] * 46
        row[5], row[6], row[23], row[24] = "1", "11", "AC", "11"
        for rows, ok in (([row, row], False), ([["  "] + row[1:]], False), ([row], True)):
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "r.csv"
                body = "\n".join(";".join(r) for r in rows)
                path.write_bytes(("﻿" + preamble + "\n" + header + "\n" + body + "\n").encode("utf-8"))
                if ok:
                    builder.read_register(path)
                else:
                    with self.assertRaises(builder.GateFail):
                        builder.read_register(path)


# ------------------------------------------------------------------ Group B: original sources

@unittest.skipUnless(SOURCES_PRESENT, "pinned raw files and bundle required")
class SourceTests(unittest.TestCase):
    def test_raw_and_bundle_hashes(self):
        manifest = {r["filename"]: r["sha256"] for r in json.loads((RAW / "manifest.json").read_text(encoding="utf-8"))}
        for name, expected in builder.EXPECTED_SHA256.items():
            self.assertEqual(manifest[name], expected)
            self.assertEqual(sha(RAW / name), expected, name)
        self.assertEqual(sha(BUNDLE / "run_manifest.json"), builder.PINNED_BUNDLE)
        for name, expected in json.loads((BUNDLE / "run_manifest.json").read_text(encoding="utf-8"))["files"].items():
            self.assertEqual(sha(BUNDLE / name), expected, name)

    def test_tampered_hash_is_rejected(self):
        import tempfile, shutil
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp)
            (raw / "manifest.json").write_text((RAW / "manifest.json").read_text(encoding="utf-8"), encoding="utf-8")
            for name in builder.EXPECTED_SHA256:
                (raw / name).write_bytes(b"not the pinned bytes")
            with self.assertRaises(builder.GateFail):
                builder.verify_inputs(raw, BUNDLE)

    def test_csv_signature_independent(self):
        data = (RAW / "reg_0901.csv").read_bytes()
        self.assertTrue(data.startswith(b"\xef\xbb\xbf"))
        text = data.decode("utf-8-sig").split("\r\n")
        self.assertIn("Letzte Aktualisierung vom: 01.09.2026", text[7])
        self.assertEqual(len(text[10].split(";")), 47)
        self.assertEqual(len(independent_rows()), 116443)

    def test_national_totals_match_original_snapshot(self):
        rows = independent_rows()
        ids = [r["Ladeeinrichtungs-ID"] for r in rows]
        self.assertEqual(len(ids), len(set(ids)))
        declared = sum(int(r["Anzahl Ladepunkte"]) for r in rows)
        kw = sum(fraction(r["Nennleistung Ladeeinrichtung [kW]"]) for r in rows)
        g = payload()["germany"]
        self.assertEqual((g["installations"], g["points"]), (116443, 209136))
        self.assertEqual(declared, g["points"])
        self.assertEqual(kw, Fraction(9086797.5).limit_denominator(10))
        self.assertEqual(g["nominalKw"], 9086797.5)

    def test_point_groups_reconcile_independently(self):
        rows = independent_rows()
        mismatched = connector_tokens = filled_total = 0
        for r in rows:
            filled = [n for n in range(1, 7) if any(r[f"{k}{n}"].strip() for k in
                      ("Steckertypen", "Nennleistung Stecker", "EVSE-ID", "Public Key"))]
            filled_total += len(filled)
            mismatched += len(filled) != int(r["Anzahl Ladepunkte"])
            connector_tokens += sum(len([t for t in r[f"Steckertypen{n}"].split(";") if t.strip()]) for n in filled)
        self.assertEqual(mismatched, 0)
        self.assertEqual(filled_total, 209136)
        g = payload()["germany"]
        self.assertEqual(g["connectorTokens"], connector_tokens)
        self.assertGreater(connector_tokens, filled_total)  # a point is not a connector
        self.assertEqual(g["pointsQuarantinedGroupMismatch"], 0)

    def test_state_aggregates_match_independent_group_by(self):
        rows = independent_rows()
        inst, pts, kw = collections.Counter(), collections.Counter(), collections.defaultdict(Fraction)
        for r in rows:
            inst[r["Bundesland"]] += 1
            pts[r["Bundesland"]] += int(r["Anzahl Ladepunkte"])
            kw[r["Bundesland"]] += fraction(r["Nennleistung Ladeeinrichtung [kW]"])
        states = {s["name"]: s for s in payload()["states"]}
        self.assertEqual(set(states), set(inst))
        self.assertEqual(len(states), 16)
        for name, s in states.items():
            self.assertEqual((s["installations"], s["points"]), (inst[name], pts[name]), name)
            self.assertEqual(Fraction(s["nominalKw"]).limit_denominator(10), kw[name], name)

    def test_states_sum_to_national_and_districts_plus_unattributed_to_state(self):
        p = payload()
        g = p["germany"]
        for key in ("installations", "points", "pointsPowerUnknown", "nominalKwMissingInstallations"):
            self.assertEqual(sum(s[key] for s in p["states"]), g[key], key)
        self.assertAlmostEqual(sum(s["nominalKw"] for s in p["states"]), g["nominalKw"], places=3)
        self.assertEqual(sum(s["population"] for s in p["states"]), g["population"])
        for s in p["states"]:
            ds = [d for d in p["districts"] if d["state"] == s["code"]]
            un = [u for u in p["unattributedLabels"] if u["state"] == s["code"]]
            self.assertEqual(len(ds), s["districts"])
            self.assertEqual(sum(d["installations"] for d in ds) + sum(u["installations"] for u in un), s["installations"])
            self.assertEqual(sum(d["points"] for d in ds) + sum(u["points"] for u in un), s["points"])
            self.assertEqual(sum(d["population"] for d in ds), s["population"])
            self.assertAlmostEqual(sum(d["nominalKw"] for d in ds) + sum(u["nominalKw"] for u in un),
                                   s["nominalKw"], places=3)

    def test_pinned_bb_and_berlin(self):
        p = payload()
        states = {s["code"]: s for s in p["states"]}
        self.assertEqual((states["12"]["installations"], states["12"]["points"], states["12"]["nominalKw"]),
                         (3032, 5004, 278455.0))
        self.assertEqual((states["11"]["installations"], states["11"]["points"], states["11"]["nominalKw"]),
                         (4953, 7561, 211420.1))
        self.assertEqual(p["brandenburg"]["totals"]["registered"]["population"], 2551889)
        self.assertEqual(p["berlin"]["registered"]["population"], 3700577)

    def test_power_nominal_vs_point_sum_stay_separate(self):
        # nominal power is never rebuilt from point power: 41,524 installations report less than their point sum
        rows = independent_rows()
        point_sum = Fraction(0)
        for r in rows:
            for n in range(1, 7):
                tokens = [t for t in r[f"Nennleistung Stecker{n}"].split(";") if t.strip()]
                if tokens:
                    point_sum += max(fraction(t) for t in tokens)
        self.assertNotEqual(point_sum, Fraction(9086797.5).limit_denominator(10))
        self.assertEqual(payload()["germany"]["pointsPowerUnknown"], 0)
        self.assertEqual(payload()["germany"]["nominalKwMissingInstallations"], 0)

    def test_point_classes_match_pipeline_point_snapshot(self):
        counts = collections.Counter()
        with (BUNDLE / "point_snapshot.csv").open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row["point_kw"] != "":
                    counts[builder.power_class(Decimal(row["point_kw"]))] += 1
        expected = {k: counts.get(k, 0) for k, _ in builder.CLASS_EDGES}
        self.assertEqual(payload()["germany"]["pointsByClassBnetza"], expected)
        self.assertEqual(sum(expected.values()), 209136)

    def test_installations_match_pipeline_installation_snapshot(self):
        rows = {r["id"]: r for r in builder.read_register(RAW / "reg_0901.csv")[1]}
        checked = alias = 0
        with (BUNDLE / "installation_snapshot.csv").open(encoding="utf-8", newline="") as handle:
            for ref in csv.DictReader(handle):
                mine = rows[ref["installation_id"]]
                self.assertEqual(str(mine["declared"]), ref["declared_point_count"].split(".")[0])
                self.assertEqual(mine["nominal"], Decimal(ref["nominal_kw"]))
                self.assertEqual(mine["state"], ref["bundesland"])
                self.assertEqual(mine["label"], ref["kreis_label"])
                self.assertEqual(mine["flagged"], ref["is_tesla_cluster"] == "True")
                checked += 1
        self.assertEqual(checked, 116443)

    def test_label_mapping_matches_pipeline_and_alias_gap_is_explicit(self):
        p = payload()
        mapping = {}
        with (BUNDLE / "installation_snapshot.csv").open(encoding="utf-8", newline="") as handle:
            for ref in csv.DictReader(handle):
                mapping[ref["kreis_label"]] = ref["label_ars"]
        pipeline_unmapped = {label for label, ars in mapping.items() if ars == ""}
        mine_unmapped = set(p["meta"]["labelMapping"]["unmappedLabels"])
        aliases = {a["sourceLabel"] for a in p["meta"]["labelMapping"]["spacingAliases"]}
        self.assertEqual(pipeline_unmapped, mine_unmapped | aliases)  # nothing else changes
        self.assertEqual(len(aliases), 8)
        self.assertEqual(mine_unmapped, {"Kreisfreie Stadt Hanau"})
        for a in p["meta"]["labelMapping"]["spacingAliases"]:
            self.assertEqual(builder.normalize_label_name(a["sourceLabel"]), builder.normalize_label_name(a["vg250Name"]))
        for label, ars in mapping.items():  # exact labels agree with the pipeline's code
            if ars:
                self.assertTrue(any(d["code"] == ars for d in p["districts"]))
        self.assertEqual(sum(u["installations"] for u in p["unattributedLabels"]), 144)
        self.assertEqual(p["districts"][[d["code"] for d in p["districts"]].index("06435")]["labelGap"],
                         {"installations": 144, "points": 249})

    def test_geo_diagnostic_matches_pipeline_outcomes(self):
        p = payload()
        ledger = collections.Counter()
        with (BUNDLE / "assignment_ledger.csv").open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                if row["label_ars"]:
                    ledger[(row["label_ars"], row["assignment_outcome"])] += 1
        for d in p["districts"]:
            if d["code"] in {a["code"] for a in p["meta"]["labelMapping"]["spacingAliases"]} or d["code"] == "06435":
                continue  # alias districts are classified here but 'unmapped_label' in the pipeline
            self.assertEqual(d["geo"]["agree"], ledger[(d["code"], "agreed")], d["code"])
            self.assertEqual(d["geo"]["conflict"], ledger[(d["code"], "conflict")], d["code"])
            self.assertEqual(d["geo"]["noMatch"], ledger[(d["code"], "unmatched_spatial")], d["code"])
        for d in p["districts"]:
            self.assertEqual(d["geo"]["agree"] + d["geo"]["conflict"] + d["geo"]["noMatch"], d["installations"])

    def test_concentration_matches_pipeline_diagnostics(self):
        districts = {d["code"]: d for d in payload()["districts"]}
        with (BUNDLE / "concentration_diagnostics.csv").open(encoding="utf-8", newline="") as handle:
            ref = list(csv.DictReader(handle))
        self.assertEqual(len(ref), 19)
        for row in ref:
            mine = districts[row["district_code"]]["topGroup"]
            self.assertEqual(mine["points"], int(row["largest_cluster_points"]), row["district_code"])
            self.assertEqual(mine["installations"], int(row["largest_cluster_installations"]), row["district_code"])
            self.assertAlmostEqual(mine["pointShare"], float(row["largest_cluster_point_share"]), places=12)

    def test_denominators_unique_and_same_vintage(self):
        p = payload()
        codes = [d["code"] for d in p["districts"]]
        self.assertEqual(len(codes), 400)
        self.assertEqual(len(set(codes)), 400)
        self.assertTrue(all(len(c) == 5 for c in codes))
        self.assertEqual(len({s["code"] for s in p["states"]}), 16)
        self.assertEqual(p["meta"]["population"]["referenceDate"], "2025-12-31")
        self.assertEqual(p["meta"]["population"]["boundaryVintage"], "2025-12-31")
        self.assertEqual(sum(d["population"] for d in p["districts"]), p["germany"]["population"])
        self.assertEqual(p["germany"]["population"], 83467117)
        # independent read of the BKG attribute tables
        z = zipfile.ZipFile(RAW / "vg250ew.zip")
        self.assertEqual(z.read(builder.AKTUALITAET_MEMBER).decode().strip(), "31.12.2025")
        con = sqlite3.connect(":memory:")
        con.deserialize(z.read(builder.GPKG_MEMBER))
        official = dict(con.execute("select ARS, EWZ from vg250_krs where GF=4"))
        self.assertEqual({d["code"]: d["population"] for d in p["districts"]}, official)
        self.assertEqual(con.execute("select sum(EWZ) from vg250_lan where GF=4").fetchone()[0], 83467117)
        self.assertEqual(con.execute("select EWZ from vg250_sta where GF=4").fetchone()[0], 83467117)
        self.assertEqual(sum(p_ for c, p_ in official.items() if c.startswith("12")), 2551889)
        self.assertEqual(official["11000"], 3700577)
        con.close()

    def test_area_gaps_are_disclosed_not_hidden(self):
        gaps = payload()["meta"]["population"]["reconciliation"]["areaGapKm2LandMinusKreiseSum"]
        self.assertEqual(set(gaps), {"07", "13"})
        self.assertAlmostEqual(gaps["07"], 6.2, places=2)
        self.assertAlmostEqual(gaps["13"], 1.0, places=2)

    def test_rates_recompute_from_payload_numbers(self):
        p = payload()
        for row in p["states"] + p["districts"] + [p["germany"]]:
            self.assertAlmostEqual(row["pointsPer10kResidents"], 10000 * row["points"] / row["population"], places=9)
            self.assertAlmostEqual(row["nominalKwPer1000Residents"], 1000 * row["nominalKw"] / row["population"], places=6)
            self.assertAlmostEqual(row["pointsPerInstallation"], row["points"] / row["installations"], places=12)
        g = p["germany"]
        mean_of_state_rates = sum(s["pointsPer10kResidents"] for s in p["states"]) / 16
        self.assertNotAlmostEqual(g["pointsPer10kResidents"], mean_of_state_rates, places=3)  # ratio of sums

    def test_internal_distributions_conserve(self):
        p = payload()
        g = p["germany"]
        self.assertEqual(sum(g["pointsByPower"].values()), g["points"] - g["pointsPowerUnknown"])
        self.assertEqual(sum(g["installationsByPointCount"].values()), g["installations"])
        self.assertEqual(sum(y["installations"] for y in g["listedByCommissioningYear"]) +
                         g["commissioningDateMissingInstallations"], g["installations"])
        self.assertEqual(sum(y["points"] for y in g["listedByCommissioningYear"]), g["points"])
        self.assertEqual(sum(ppi * n for ppi, n in ((int(k), v) for k, v in g["installationsByPointCount"].items())),
                         g["points"])
        for row in p["states"] + p["districts"]:
            self.assertEqual(sum(row["pointsByPower"].values()), row["points"] - row["pointsPowerUnknown"])

    def test_statistics_workbook_is_context_only(self):
        s = payload()["statisticsContext"]
        self.assertEqual((s["installations"], s["points"]), (119416, 214334))
        self.assertAlmostEqual(s["nominalKw"], 9382671.4, places=1)
        self.assertEqual(s["states"]["12"], {"points": 5099, "nominalKw": 281910.6})
        g = payload()["germany"]
        self.assertLess(g["points"], s["points"])  # different population; never forced equal
        self.assertNotEqual(g["nominalKw"], s["nominalKw"])
        for cls, n in g["pointsByClassBnetza"].items():
            self.assertLessEqual(n, s["pointsByClass"][cls], cls)
            self.assertGreater(n / s["pointsByClass"][cls], 0.9, cls)
        for state in payload()["states"]:
            ctx = s["states"][state["code"]]
            self.assertLessEqual(state["points"], ctx["points"], state["name"])
            self.assertLessEqual(state["nominalKw"], ctx["nominalKw"] + 0.05, state["name"])
        # the workbook date serial is 1 Sep 2026
        z = zipfile.ZipFile(RAW / "stats.xlsx")
        self.assertIn(b"46266", z.read("xl/worksheets/sheet3.xml"))
        import datetime
        self.assertEqual(datetime.date(1899, 12, 30) + datetime.timedelta(days=46266), datetime.date(2026, 9, 1))

    def test_no_future_dated_commissioning(self):
        years = [y["year"] for y in payload()["germany"]["listedByCommissioningYear"]]
        self.assertEqual(max(years), 2026)
        rows = independent_rows()
        future = sum(1 for r in rows if (m := re.fullmatch(r"(\d\d)\.(\d\d)\.(\d{4})", r["Inbetriebnahmedatum"]))
                     and (int(m.group(3)), int(m.group(2)), int(m.group(1))) > (2026, 9, 1))
        self.assertEqual(future, 0)

    def test_brandenburg_and_berlin_match_pipeline_bundle(self):
        p = payload()["brandenburg"]
        ref = {}
        with (BUNDLE / "bi_district_scenario.csv").open(encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle):
                ref[(row["scenario_id"], row["district_code"])] = row
        for d in p["districts"]:
            for mine, scenario in ((d["registered"], "registered"), (d["hypothetical"], "hypothetical_exclusion")):
                r = ref[(scenario, d["code"])]
                self.assertEqual(mine["points"], int(float(r["points"])), d["code"])
                self.assertEqual(mine["installations"], int(r["installations"]), d["code"])
                self.assertEqual(mine["kw"], float(r["nominal_kw"]), d["code"])
                self.assertEqual(mine["population"], int(r["population"]), d["code"])
                self.assertEqual(mine["rate"], float(r["points_per_10000_residents"]), d["code"])
                self.assertEqual(mine["rank"], int(r["brandenburg_rank"]), d["code"])
        b = payload()["berlin"]["registered"]
        r = ref[("registered", "11000")]
        self.assertEqual((b["points"], b["installations"], b["kw"], b["rate"]),
                         (7561, 4953, 211420.1, float(r["points_per_10000_residents"])))

    @unittest.skipUnless(DEPLOYED.exists(), "deployed site data not present")
    def test_brandenburg_and_berlin_match_deployed_site_data(self):
        text = DEPLOYED.read_text(encoding="utf-8")
        site = json.loads(text[text.index("=") + 1:].rstrip().rstrip(";"))
        mine = {d["code"]: d for d in payload()["brandenburg"]["districts"]}
        self.assertEqual(len(site["districts"]), 18)
        for d in site["districts"]:
            for scenario in ("registered", "hypothetical"):
                for key in ("points", "population", "rate", "kw", "installations"):
                    self.assertEqual(mine[d["code"]][scenario][key], d[scenario][key], (d["code"], scenario, key))
            self.assertEqual(mine[d["code"]]["name"], d["name"])
        b = payload()["berlin"]["registered"]
        self.assertEqual((b["points"], b["population"], b["rate"]),
                         (site["berlin"]["points"], site["berlin"]["population"], site["berlin"]["rate"]))
        os_ = mine["12067"]
        self.assertEqual((os_["registered"]["rank"], os_["hypothetical"]["rank"]), (1, 11))
        self.assertEqual((os_["registered"]["points"], os_["hypothetical"]["points"]), (832, 319))
        flagged = payload()["brandenburg"]["flaggedGroup"]
        self.assertEqual((flagged["installations"], flagged["points"], flagged["nominalKw"], flagged["districts"]),
                         (513, 513, 5643.0, ["12067"]))

    def test_payload_has_no_identifying_values(self):
        strings = set()

        def walk(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    strings.add(k)
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)
            elif isinstance(node, str):
                strings.add(node)
        walk(payload())
        rows = independent_rows()
        sensitive = set()
        for r in rows:
            # Streets, house numbers, postcodes and site descriptions collide with town names and Kreis codes,
            # and integer-degree coordinates or one-digit public keys collide with state codes; those are covered
            # by the key check below. Identifiers, operators, long keys and decimal coordinates are matched exactly.
            sensitive.update([r["Ladeeinrichtungs-ID"], r["Betreiber"]])
            sensitive.update(v for v in (r["Breitengrad"], r["Längengrad"]) if "," in v)
            for n in range(1, 7):
                sensitive.update(v for v in (r[f"EVSE-ID{n}"], r[f"Public Key{n}"]) if len(v) >= 6)
        sensitive.discard("")
        collisions = strings & sensitive
        # An operator that is itself a public authority named like a Kreis shares that geographic name; the
        # payload carries the geographic name only, never an operator field. Any other collision is a leak.
        operators = {r["Betreiber"] for r in rows}
        geographic = {d["name"] for d in payload()["districts"]}
        self.assertEqual(collisions - (operators & geographic), set(), "payload contains an identifier value")
        self.assertEqual(collisions, {"Hochsauerlandkreis"})
        keys = set()

        def walk_keys(node):
            if isinstance(node, dict):
                for k, v in node.items():
                    keys.add(k)
                    walk_keys(v)
            elif isinstance(node, list):
                for v in node:
                    walk_keys(v)
        walk_keys(payload())
        banned = re.compile(r"(?i)^(id|installationid|operator\w*|betreiber|evse\w*|publickey\w*|street|house\w*|"
                            r"postcode|plz|lat|lon|latitude|longitude|coord|coords|address\w*)$")
        self.assertEqual({k for k in keys if banned.match(k)}, set())
        self.assertLessEqual(len(payload()["states"]) + len(payload()["districts"]), 416)  # aggregates only

    def test_deterministic_output(self):
        first = builder.to_json(builder.build(RAW, BUNDLE))
        second = builder.to_json(builder.build(RAW, BUNDLE))
        self.assertEqual(first, second)
        self.assertEqual(first, builder.to_json(payload()))
        import tempfile
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            self.assertEqual(builder.write_outputs(payload(), Path(a)), builder.write_outputs(payload(), Path(b)))
        shipped = HERE.parent / "national-story.json"
        if shipped.exists():
            self.assertEqual(shipped.read_text(encoding="utf-8"), first)

    def test_coverage_mw_flags_and_type_split(self):
        p = payload()
        for row in p["states"] + p["districts"] + [p["germany"]]:
            self.assertEqual(row["nominalKwCoverage"], 1.0)
            self.assertEqual(row["pointPowerCoverage"], 1.0)
            self.assertAlmostEqual(row["nominalMw"] * 1000, row["nominalKw"], places=6)
        self.assertAlmostEqual(p["germany"]["nominalMw"], 9086.7975, places=6)
        by = {d["code"]: d for d in p["districts"]}
        for d in p["districts"]:
            self.assertEqual("lowLabelCoordinateAgreement" in d["flags"], d["geo"]["agreeShare"] < 0.95, d["code"])
            self.assertEqual("concentratedCoLocation" in d["flags"], d["topGroup"]["pointShare"] >= 0.20, d["code"])
            self.assertEqual("smallPointCount" in d["flags"], d["points"] < 100, d["code"])
            self.assertEqual("labelGap" in d["flags"], "labelGap" in d, d["code"])
        self.assertEqual([c for c, d in by.items() if "labelGap" in d["flags"]], ["06435"])
        t = p["germany"]["byAdministrativeType"]
        self.assertEqual(t["city"]["districts"] + t["county"]["districts"], 400)
        self.assertEqual(t["city"]["population"] + t["county"]["population"], p["germany"]["population"])
        self.assertEqual(t["city"]["points"] + t["county"]["points"] + p["germany"]["unattributedPointsExcludedFromTypeRates"],
                         p["germany"]["points"])

    def test_without_top_group_sensitivity(self):
        p = payload()
        for d in p["districts"]:
            self.assertEqual(d["pointsWithoutTopGroup"], d["points"] - d["topGroup"]["points"])
            self.assertAlmostEqual(d["pointsPer10kWithoutTopGroup"],
                                   10000 * d["pointsWithoutTopGroup"] / d["population"], places=9)
            self.assertEqual(d["rankWithoutTopGroup"], 1 + sum(
                1 for o in p["districts"] if o["pointsPer10kWithoutTopGroup"] > d["pointsPer10kWithoutTopGroup"]))
        os_ = next(d for d in p["districts"] if d["code"] == "12067")
        self.assertEqual((os_["topGroup"]["points"], os_["pointsWithoutTopGroup"]), (513, 319))

    def test_status_is_diagnostic_and_gates_are_disclosed(self):
        meta = payload()["meta"]
        self.assertEqual(meta["status"], "DIAGNOSTIC_PILOT")
        self.assertFalse(meta["validatedReleaseEligible"])
        self.assertIn("coordinate_crs_provisional_wgs84", meta["openGates"])
        self.assertEqual(meta["unattributedInstallations"], 144)

    def test_ranks_are_competition_ranks(self):
        for table in ("states", "districts"):
            rows = payload()[table]
            key = "rank" if table == "states" else "rankGermany"
            for r in rows:
                expected = 1 + sum(1 for o in rows if o["pointsPer10kResidents"] > r["pointsPer10kResidents"])
                self.assertEqual(r[key], expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
