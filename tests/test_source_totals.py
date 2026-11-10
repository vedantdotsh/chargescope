import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RAW = ROOT / "data" / "raw"


def _have_stack() -> bool:
    try:
        import duckdb  # noqa: F401
        import geopandas  # noqa: F401
        import openpyxl  # noqa: F401
        import pandas  # noqa: F401
    except ImportError:
        return False
    return True


def _raw_ok() -> bool:
    return all((RAW / name).exists() for name in ("reg_0901.csv", "stats.xlsx", "vg250ew.zip", "manifest.json"))


@unittest.skipUnless(_have_stack() and _raw_ok(), "needs pandas/geopandas/duckdb/openpyxl and pinned data/raw files")
class SourceTotals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from chargescope.pipeline import (
            build_crosswalk,
            load_stats_context,
            load_vg250,
            normalize_register_frame,
            read_register_csv,
            verify_raw,
            _kw_sum,
        )

        cls.checked = verify_raw(RAW)
        cls.preamble, cls.frame = read_register_csv(RAW / "reg_0901.csv")
        cls.spatial, cls.district, cls.population = load_vg250(RAW / "vg250ew.zip")
        cls.crosswalk = build_crosswalk(cls.spatial)
        cls.inst, cls.points, cls.issues = normalize_register_frame(cls.frame, cls.crosswalk)
        cls.stats = load_stats_context(RAW / "stats.xlsx")
        cls._kw_sum = staticmethod(_kw_sum)

    def test_hashes_match_pinned_snapshot(self):
        from chargescope.pipeline import EXPECTED_SHA256, sha256_file

        for name, expected in EXPECTED_SHA256.items():
            self.assertEqual(sha256_file(RAW / name), expected)
        by_name = {row["filename"]: row["sha256"] for row in json.loads((RAW / "manifest.json").read_text(encoding="utf-8"))}
        self.assertEqual(by_name, EXPECTED_SHA256)

    def test_csv_preamble_and_47_columns(self):
        self.assertEqual(len(self.preamble), 10)
        self.assertIn("Letzte Aktualisierung vom: 01.09.2026", self.preamble[7])
        self.assertEqual(len(self.frame.columns), 47)
        self.assertEqual(len(self.frame), 116443)

    def test_unique_ids_and_group_reconciliation(self):
        self.assertEqual(self.inst["installation_id"].nunique(), 116443)
        self.assertEqual(int((~self.inst["groups_reconcile"]).sum()), 0)
        self.assertEqual(len(self.points), 209136)
        self.assertEqual(int(self.inst["declared_point_count"].sum()), 209136)

    def test_national_and_label_totals(self):
        self.assertEqual(self._kw_sum(self.inst["nominal_kw"]), 9086797.5)
        bb = self.inst[self.inst["bundesland"] == "Brandenburg"]
        be = self.inst[self.inst["bundesland"] == "Berlin"]
        self.assertEqual(len(bb), 3032)
        self.assertEqual(int(bb["declared_point_count"].sum()), 5004)
        self.assertEqual(self._kw_sum(bb["nominal_kw"]), 278455.0)
        self.assertEqual(len(be), 4953)
        tesla = self.inst[self.inst["is_tesla_cluster"]]
        self.assertEqual(len(tesla), 513)
        self.assertEqual(int(tesla["declared_point_count"].sum()), 513)
        self.assertEqual(self._kw_sum(tesla["nominal_kw"]), 5643.0)

    def test_crosswalk_is_bez_plus_gen(self):
        self.assertEqual(len(self.crosswalk), 400)
        self.assertEqual(self.crosswalk["Kreisfreie Stadt Ansbach"], "09561")
        self.assertEqual(self.crosswalk["Landkreis Ansbach"], "09571")
        unmapped = self.inst["label_ars"].isna().sum()
        self.assertEqual(int(unmapped), 1305)

    def test_vg250_metric_roster(self):
        self.assertEqual(len(self.district), 19)
        self.assertEqual(set(self.district["district_code"]), set(self.population["district_code"]))
        bb = self.population[self.population["district_code"] != "11000"]
        self.assertEqual(int(bb["population"].sum()), 2551889)
        self.assertAlmostEqual(float(bb["cadastral_area_km2"].sum()), 29654.20, places=2)
        berlin = self.population.set_index("district_code").loc["11000"]
        self.assertEqual(int(berlin["population"]), 3700577)

    def test_stats_are_context_not_equality(self):
        self.assertFalse(self.stats["equality_required"])
        self.assertEqual(int(self.stats["brandenburg_points"]), 5099)
        self.assertAlmostEqual(float(self.stats["brandenburg_kw"]), 281910.6, places=1)
        self.assertNotEqual(self.stats["brandenburg_points"], 5004)
        self.assertNotEqual(self.stats["brandenburg_kw"], 278455.0)

    def test_full_national_spatial_pilot(self):
        from chargescope.pipeline import compile_release, write_release

        snapshot = __import__("pandas").DataFrame(self.checked)
        release = compile_release(
            self.inst,
            self.points,
            self.issues,
            self.spatial,
            self.district,
            self.population,
            snapshot,
            self.stats,
        )
        nat = release.conservation["national"]
        self.assertEqual(nat["installations"], 116443)
        self.assertEqual(nat["outcome_sum_installations"], 116443)
        self.assertTrue(nat["conservation_ok"])
        self.assertEqual(len(release.district_metrics), 19)
        bb_metrics = release.district_metrics.query("district_code != '11000'")
        self.assertEqual(int(bb_metrics.source_label_installations.sum()), 3032)
        self.assertEqual(int(bb_metrics.source_label_points.sum()), 5004)
        self.assertAlmostEqual(float(bb_metrics.source_label_kw.sum()), 278455.0, places=1)
        self.assertEqual(int(bb_metrics.geographic_points.sum()), 4969)
        self.assertFalse(release.conservation["validated_release_eligible"])
        self.assertEqual(release.conservation["coordinate_crs_status"], "provisional_unverified")
        self.assertTrue(release.conservation["tesla_gruenheide"]["in_registered_baseline"])
        self.assertEqual(release.conservation["tesla_gruenheide"]["points"], 513)
        self.assertNotIn("stats_equality", release.conservation["failed_gates"])
        from chargescope.portfolio import build_portfolio
        tables, evidence = build_portfolio(release)
        self.assertEqual(38, len(tables["bi_district_scenario"]))
        self.assertEqual(7985, len(tables["bi_installation"]))
        self.assertEqual(12565, len(tables["bi_point"]))
        regions = tables["bi_region_scenario"].set_index(["scenario_id", "region"])
        baseline = regions.loc[("registered", "Brandenburg")]
        self.assertEqual(3032, baseline.installations)
        self.assertEqual(5004, baseline.points)
        self.assertEqual(278455, baseline.nominal_kw)
        self.assertEqual(2551889, baseline.population)
        self.assertEqual(4969, baseline.agreed_known_points)
        self.assertEqual(25, baseline.unresolved_installations)
        cluster = tables["evidence_cluster_sensitivity"].set_index("scenario_id")
        self.assertEqual(832, cluster.loc["registered", "points"])
        self.assertEqual(319, cluster.loc["hypothetical_exclusion", "points"])
        self.assertEqual(1, cluster.loc["registered", "brandenburg_rank"])
        self.assertEqual(11, cluster.loc["hypothetical_exclusion", "brandenburg_rank"])
        self.assertEqual(3, len(evidence["findings"]))
        self.assertTrue(tables["sql_parity"].passed.all())
        with tempfile.TemporaryDirectory() as tmp:
            bundle = write_release(release, Path(tmp))
            status = (bundle / "STATUS.txt").read_text(encoding="utf-8")
            self.assertTrue(status.startswith("DIAGNOSTIC_PILOT"))
            again = compile_release(
                self.inst,
                self.points,
                self.issues,
                self.spatial,
                self.district,
                self.population,
                snapshot,
                self.stats,
            )
            __import__("pandas").testing.assert_frame_equal(
                release.district_metrics, again.district_metrics
            )


if __name__ == "__main__":
    unittest.main()
