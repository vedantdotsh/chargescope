import unittest
import tempfile
from pathlib import Path

import pandas as pd

from test_contracts import make_row, release_from_rows
from chargescope.portfolio import build_portfolio, replay_evidence
from chargescope.pipeline import GateFail, write_release


class PortfolioContracts(unittest.TestCase):
    def test_sql_pack_replays_csv_and_rejects_tampering(self):
        release = release_from_rows([make_row(**{"Ladeeinrichtungs-ID": "00001"})])
        release.district = pd.concat([
            release.district, release.district.iloc[[0]].assign(
                district_code="11000", district_name="Berlin", peer_group="berlin_context")
        ], ignore_index=True)
        release.population = pd.concat([
            release.population, release.population.iloc[[0]].assign(district_code="11000")
        ], ignore_index=True)
        with tempfile.TemporaryDirectory() as temporary:
            bundle = write_release(release, Path(temporary))
            result = replay_evidence(bundle)
            self.assertTrue(result["passed"])
            self.assertEqual(5, len(result["queries"]))
            with (bundle / "evidence_geography.csv").open("a", encoding="utf-8") as handle:
                handle.write("tampered\n")
            with self.assertRaisesRegex(GateFail, "modified"):
                replay_evidence(bundle)

    def test_grains_scenarios_and_sql_parity(self):
        first = make_row(**{
            "Anzahl Ladepunkte": "2", "Nennleistung Ladeeinrichtung [kW]": "30",
            "Steckertypen1": "AC Typ 2 Steckdose; AC Schuko",
            "Nennleistung Stecker1": "22; 22",
            "Steckertypen2": "AC Typ 2 Steckdose", "Nennleistung Stecker2": "22",
        })
        release = release_from_rows([first, make_row(**{"Ladeeinrichtungs-ID": "2"})])
        release.installation_snapshot.loc[0, "is_tesla_cluster"] = True
        tables, evidence = build_portfolio(release)
        self.assertEqual(2, len(tables["bi_installation"]))
        self.assertEqual(3, len(tables["bi_point"]))
        self.assertEqual(4, tables["bi_point"].n_connector_tokens.sum())
        metrics = tables["bi_district_scenario"].set_index(["scenario_id", "district_code"])
        baseline = metrics.loc[("registered", "12051")]
        alternative = metrics.loc[("hypothetical_exclusion", "12051")]
        self.assertEqual(3, baseline.points)
        self.assertEqual(52, baseline.nominal_kw)
        self.assertEqual(1, alternative.points)
        self.assertEqual(22, alternative.nominal_kw)
        self.assertTrue(tables["sql_parity"].passed.all())
        self.assertEqual(3, len(evidence["findings"]))
        self.assertFalse(evidence["validated_release_eligible"])
        again, repeated = build_portfolio(release)
        for name in tables:
            pd.testing.assert_frame_equal(tables[name], again[name])
        self.assertEqual(evidence, repeated)

    def test_unknowns_and_invalid_denominators_stay_null(self):
        release = release_from_rows([make_row(**{
            "Nennleistung Ladeeinrichtung [kW]": "", "Anzahl Ladepunkte": "",
        })])
        release.population.loc[0, "population"] = -1
        tables, _ = build_portfolio(release)
        metrics = tables["bi_district_scenario"].query("district_code == '12051'")
        self.assertTrue(metrics.nominal_kw.isna().all())
        self.assertTrue(metrics.points.isna().all())
        self.assertTrue(metrics.points_per_10000_residents.isna().all())
        self.assertTrue((metrics.unknown_point_installations == 1).all())
        self.assertTrue((metrics.nominal_kw_missing_n == 1).all())
        regions = tables["bi_region_scenario"]
        self.assertTrue(regions.points_per_10000_residents.isna().all())
        self.assertTrue(tables["sql_parity"].passed.all())

    def test_berlin_not_ranked_and_region_rate_uses_totals(self):
        release = release_from_rows([make_row()])
        berlin = release.district.iloc[[0]].assign(
            district_code="11000", district_name="Berlin", peer_group="berlin_context")
        release.district = pd.concat([release.district, berlin], ignore_index=True)
        release.population = pd.concat([
            release.population, release.population.iloc[[0]].assign(district_code="11000")
        ], ignore_index=True)
        tables, _ = build_portfolio(release)
        metrics = tables["bi_district_scenario"]
        self.assertTrue(metrics.query("district_code == '11000'").brandenburg_rank.isna().all())
        region = tables["bi_region_scenario"].query(
            "scenario_id == 'registered' and region == 'Brandenburg'").iloc[0]
        self.assertEqual(2.5, region.points_per_10000_residents)
        self.assertNotEqual(5, region.points_per_10000_residents)
        self.assertEqual({"11000", "12051", "12052"}, set(tables["bi_district"].district_code))
