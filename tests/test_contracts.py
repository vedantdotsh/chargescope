import unittest
from decimal import Decimal
from pathlib import Path
import sys

import geopandas as gpd
import pandas as pd
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chargescope.pipeline import (
    COORDINATE_CRS_ASSUMPTION,
    COORDINATE_CRS_STATUS,
    EXPECTED_HEADER,
    DuplicateIdError,
    SchemaError,
    assign_installations,
    build_crosswalk,
    compile_release,
    normalize_register_frame,
    parse_point_slot,
    round_kfl,
)


def make_row(**overrides) -> dict:
    row = {name: "" for name in EXPECTED_HEADER}
    row.update(
        {
            "Ladeeinrichtungs-ID": "1",
            "Betreiber": "Op",
            "Status": "In Betrieb",
            "Art der Ladeeinrichtung": "Normalladeeinrichtung",
            "Anzahl Ladepunkte": "1",
            "Nennleistung Ladeeinrichtung [kW]": "22",
            "Kreis/kreisfreie Stadt": "Kreisfreie Stadt Brandenburg an der Havel",
            "Bundesland": "Brandenburg",
            "Breitengrad": "52,4",
            "Längengrad": "12,5",
            "Steckertypen1": "AC Typ 2 Steckdose",
            "Nennleistung Stecker1": "22",
        }
    )
    row.update(overrides)
    return row


def frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=list(EXPECTED_HEADER))


def squares():
    """Two adjacent WGS84 squares sharing lon=12.5. Injectable; no VG250."""
    a = box(12.0, 52.0, 12.5, 52.5)
    b = box(12.5, 52.0, 13.0, 52.5)
    c = box(11.0, 51.0, 11.4, 51.4)
    gdf = gpd.GeoDataFrame(
        [
            {
                "district_code": "12051",
                "GEN": "Brandenburg an der Havel",
                "BEZ": "Kreisfreie Stadt",
                "IBZ": 40,
                "EWZ": 1000,
                "KFL": 10.0,
                "geometry": a,
            },
            {
                "district_code": "12052",
                "GEN": "Cottbus",
                "BEZ": "Kreisfreie Stadt",
                "IBZ": 40,
                "EWZ": 3000,
                "KFL": 30.0,
                "geometry": b,
            },
            {
                "district_code": "09561",
                "GEN": "Ansbach",
                "BEZ": "Kreisfreie Stadt",
                "IBZ": 40,
                "EWZ": 1,
                "KFL": 1.0,
                "geometry": c,
            },
        ],
        crs="EPSG:4326",
    )
    # Include the intended shared-boundary midpoint before projection;
    # projecting only corners makes the straight projected edge miss it.
    gdf.geometry = gdf.geometry.segmentize(0.25)
    gdf = gdf.to_crs(25832)
    return gdf


def metric_tables(spatial):
    metric = spatial[spatial["district_code"].isin(["12051", "12052"])].copy()
    district = pd.DataFrame(
        [
            {
                "district_code": "12051",
                "district_name": "Brandenburg an der Havel",
                "district_class": "kreisfreie_stadt",
                "peer_group": "brandenburg_city",
                "ibz": 40,
                "boundary_vintage": "2025-12-31",
                "boundary_crs": "EPSG:25832",
            },
            {
                "district_code": "12052",
                "district_name": "Cottbus",
                "district_class": "kreisfreie_stadt",
                "peer_group": "brandenburg_city",
                "ibz": 40,
                "boundary_vintage": "2025-12-31",
                "boundary_crs": "EPSG:25832",
            },
        ]
    )
    population = pd.DataFrame(
        [
            {
                "district_code": "12051",
                "population": 1000,
                "population_date": "2025-12-31",
                "cadastral_area_km2": 10.0,
                "area_source": "test",
                "population_source": "test",
            },
            {
                "district_code": "12052",
                "population": 3000,
                "population_date": "2025-12-31",
                "cadastral_area_km2": 30.0,
                "area_source": "test",
                "population_source": "test",
            },
        ]
    )
    return metric, district, population


def release_from_rows(rows, spatial=None, population=None, district=None):
    spatial = squares() if spatial is None else spatial
    if district is None:
        _, district_df, population_df = metric_tables(spatial)
    else:
        district_df, population_df = district, population
    crosswalk = build_crosswalk(spatial)
    inst, points, issues = normalize_register_frame(frame(rows), crosswalk)
    snapshot = pd.DataFrame([{"filename": "test", "sha256": "x", "parser_version": "test"}])
    return compile_release(
        inst,
        points,
        issues,
        spatial,
        district_df,
        population_df,
        snapshot,
        {"equality_required": False, "brandenburg_kw": 281910.6, "brandenburg_points": 5099},
        metric_codes=("12051", "12052"),
    )


class ParseContracts(unittest.TestCase):
    def test_duplicate_ids_fail_gate(self):
        rows = [make_row(**{"Ladeeinrichtungs-ID": "dup"}), make_row(**{"Ladeeinrichtungs-ID": "dup"})]
        with self.assertRaises(DuplicateIdError):
            normalize_register_frame(frame(rows), {})

    def test_header_has_47_columns(self):
        self.assertEqual(len(EXPECTED_HEADER), 47)

    def test_capacity_counted_once(self):
        row = make_row(
            **{
                "Ladeeinrichtungs-ID": "1010338",
                "Anzahl Ladepunkte": "2",
                "Nennleistung Ladeeinrichtung [kW]": "22",
                "Steckertypen1": "AC Typ 2 Steckdose",
                "Nennleistung Stecker1": "22",
                "Steckertypen2": "AC Typ 2 Steckdose",
                "Nennleistung Stecker2": "22",
            }
        )
        inst, points, _ = normalize_register_frame(frame([row]), {})
        self.assertEqual(inst.loc[0, "nominal_kw"], 22.0)
        self.assertEqual(len(points), 2)
        self.assertEqual(points["point_kw"].sum(), 44.0)
        self.assertEqual(inst.loc[0, "capped_kw"], 22.0)

    def test_connectors_are_not_points(self):
        row = make_row(
            **{
                "Ladeeinrichtungs-ID": "1025447",
                "Anzahl Ladepunkte": "2",
                "Nennleistung Ladeeinrichtung [kW]": "172",
                "Art der Ladeeinrichtung": "Schnellladeeinrichtung",
                "Steckertypen1": "DC Fahrzeugkupplung Typ Combo 2 (CCS); DC CHAdeMO",
                "Nennleistung Stecker1": "150; 150",
                "Steckertypen2": "AC Typ 2 Steckdose",
                "Nennleistung Stecker2": "22",
            }
        )
        inst, points, _ = normalize_register_frame(frame([row]), {})
        self.assertEqual(len(points), 2)
        self.assertEqual(int(points["n_connector_tokens"].sum()), 3)
        self.assertEqual(inst.loc[0, "nominal_kw"], 172.0)
        self.assertEqual(points.loc[points["source_slot"] == 1, "point_kw"].iloc[0], 150.0)

    def test_one_power_two_types_is_one_point(self):
        kw, n_conn, flags = parse_point_slot(
            "AC Typ 2 Steckdose; AC Typ 2 Fahrzeugkupplung", "11"
        )
        self.assertEqual(kw, Decimal("11"))
        self.assertEqual(n_conn, 2)
        self.assertNotIn("unequal_connector_powers", flags)

    def test_repeated_power_tokens_are_not_summed(self):
        kw, n_conn, flags = parse_point_slot("AC Typ 2 Fahrzeugkupplung", "11; 11")
        self.assertEqual(kw, Decimal("11"))
        self.assertEqual(n_conn, 1)
        self.assertIn("connector_power_token_mismatch", flags)

    def test_unequal_connector_powers_use_maximum(self):
        kw, count, flags = parse_point_slot("CCS; CHAdeMO", "150; 50")
        self.assertEqual(kw, Decimal("150"))
        self.assertEqual(count, 2)
        self.assertIn("unequal_connector_powers", flags)

    def test_unknown_power_stays_null(self):
        row = make_row(
            **{
                "Nennleistung Ladeeinrichtung [kW]": "",
                "Nennleistung Stecker1": "",
                "Steckertypen1": "AC Typ 2 Steckdose",
            }
        )
        inst, points, _ = normalize_register_frame(frame([row]), {})
        self.assertTrue(pd.isna(inst.loc[0, "nominal_kw"]) or inst.loc[0, "nominal_kw"] is None)
        self.assertTrue(pd.isna(points.loc[0, "point_kw"]) or points.loc[0, "point_kw"] is None)
        self.assertFalse(inst.loc[0, "nominal_kw"] == 0)

    def test_inconsistent_groups_quarantine_and_block_validation(self):
        row = make_row(**{"Anzahl Ladepunkte": "2", "Steckertypen2": "", "Nennleistung Stecker2": ""})
        rel = release_from_rows([row])
        self.assertFalse(rel.installation_snapshot.loc[0, "groups_reconcile"])
        self.assertFalse(rel.conservation["validated_release_eligible"])
        self.assertIn("inconsistent_point_groups", rel.conservation["open_gates"])
        self.assertIn("inconsistent_point_groups", set(rel.quality_issue["issue_code"]))

    def test_anzahl_above_six_fails_schema(self):
        row = make_row(**{"Anzahl Ladepunkte": "7"})
        with self.assertRaises(SchemaError):
            normalize_register_frame(frame([row]), {})

    def test_crosswalk_uses_bez_plus_gen_not_gen_alone(self):
        spatial = squares()
        extra = gpd.GeoDataFrame(
            [
                {
                    "district_code": "09571",
                    "GEN": "Ansbach",
                    "BEZ": "Landkreis",
                    "IBZ": 43,
                    "EWZ": 1,
                    "KFL": 1.0,
                    "geometry": box(11.5, 51.0, 11.9, 51.4),
                }
            ],
            crs="EPSG:4326",
        ).to_crs(25832)
        spatial = pd.concat([spatial, extra], ignore_index=True)
        mapping = build_crosswalk(spatial)
        self.assertEqual(mapping["Kreisfreie Stadt Ansbach"], "09561")
        self.assertEqual(mapping["Landkreis Ansbach"], "09571")
        self.assertNotEqual(mapping["Kreisfreie Stadt Ansbach"], mapping["Landkreis Ansbach"])

    def test_kfl_half_up(self):
        self.assertEqual(round_kfl(2274.4999999999995), Decimal("2274.50"))


class AssignmentContracts(unittest.TestCase):
    def test_ambiguous_boundary_is_quarantined(self):
        row = make_row(**{"Ladeeinrichtungs-ID": "b", "Breitengrad": "52,25", "Längengrad": "12,5"})
        rel = release_from_rows([row])
        self.assertEqual(rel.installation_snapshot.loc[0, "assignment_outcome"], "ambiguous_spatial")
        self.assertEqual(int(rel.district_metrics["geographic_points"].sum()), 0)

    def test_conflict_does_not_override_label_or_spatial(self):
        row = make_row(
            **{
                "Ladeeinrichtungs-ID": "c",
                "Kreis/kreisfreie Stadt": "Kreisfreie Stadt Brandenburg an der Havel",
                "Breitengrad": "52,25",
                "Längengrad": "12,75",
            }
        )
        rel = release_from_rows([row])
        rec = rel.installation_snapshot.iloc[0]
        self.assertEqual(rec["label_ars"], "12051")
        self.assertEqual(rec["spatial_ars"], "12052")
        self.assertEqual(rec["assignment_outcome"], "conflict")
        m51 = rel.district_metrics.set_index("district_code").loc["12051"]
        m52 = rel.district_metrics.set_index("district_code").loc["12052"]
        self.assertEqual(int(m51["source_label_points"]), 1)
        self.assertEqual(int(m51["geographic_points"]), 0)
        self.assertEqual(int(m52["geographic_points"]), 0)
        self.assertEqual(int(m52["incoming_spatial_points"]), 1)

    def test_national_spatial_detects_incoming_foreign_label(self):
        row = make_row(
            **{
                "Ladeeinrichtungs-ID": "in",
                "Kreis/kreisfreie Stadt": "Kreisfreie Stadt Ansbach",
                "Bundesland": "Bayern",
                "Breitengrad": "52,25",
                "Längengrad": "12,25",
            }
        )
        rel = release_from_rows([row])
        rec = rel.installation_snapshot.iloc[0]
        self.assertEqual(rec["label_ars"], "09561")
        self.assertEqual(rec["spatial_ars"], "12051")
        self.assertEqual(rec["assignment_outcome"], "conflict")
        m51 = rel.district_metrics.set_index("district_code").loc["12051"]
        self.assertEqual(int(m51["source_label_points"]), 0)
        self.assertEqual(int(m51["incoming_spatial_points"]), 1)
        self.assertEqual(int(m51["geographic_points"]), 0)

    def test_unmapped_label_is_not_silently_aliased(self):
        row = make_row(
            **{
                "Ladeeinrichtungs-ID": "hanau",
                "Kreis/kreisfreie Stadt": "Kreisfreie Stadt Hanau",
                "Bundesland": "Hessen",
                "Breitengrad": "52,25",
                "Längengrad": "12,25",
            }
        )
        rel = release_from_rows([row])
        self.assertEqual(rel.installation_snapshot.loc[0, "assignment_outcome"], "unmapped_label")
        self.assertTrue(pd.isna(rel.installation_snapshot.loc[0, "label_ars"]))
        self.assertEqual(rel.installation_snapshot.loc[0, "spatial_ars"], "12051")
        self.assertEqual(int(rel.district_metrics.geographic_points.sum()), 0)

    def test_wgs84_is_disclosed_provisional(self):
        rel = release_from_rows([make_row()])
        self.assertEqual(rel.conservation["coordinate_crs_assumption"], COORDINATE_CRS_ASSUMPTION)
        self.assertEqual(rel.conservation["coordinate_crs_status"], COORDINATE_CRS_STATUS)
        self.assertFalse(rel.conservation["validated_release_eligible"])
        self.assertIn("provisional_unverified", rel.district_metrics["coordinate_crs_status"].iloc[0])


class MetricsContracts(unittest.TestCase):
    def test_zero_and_missing_denominators_are_na(self):
        spatial = squares()
        _, district, population = None, metric_tables(spatial)[1], metric_tables(spatial)[2]
        population = population.copy()
        population.loc[population["district_code"] == "12051", "population"] = 0
        population.loc[population["district_code"] == "12052", "population"] = pd.NA
        row = make_row(**{"Breitengrad": "52,25", "Längengrad": "12,25"})
        rel = release_from_rows([row], spatial=spatial, district=district, population=population)
        rates = rel.district_metrics["points_per_10000_residents_source_label"]
        self.assertTrue(rates.isna().all())

    def test_aggregate_ratio_is_not_mean_of_district_rates(self):
        rows = [
            make_row(**{"Ladeeinrichtungs-ID": "a", "Breitengrad": "52,25", "Längengrad": "12,25"}),
            make_row(
                **{
                    "Ladeeinrichtungs-ID": "b",
                    "Kreis/kreisfreie Stadt": "Kreisfreie Stadt Cottbus",
                    "Breitengrad": "52,25",
                    "Längengrad": "12,75",
                }
            ),
        ]
        rel = release_from_rows(rows)
        agg = rel.conservation["brandenburg_18_aggregate_points_per_10000"]
        mean = rel.conservation["brandenburg_18_unweighted_mean_points_per_10000"]
        self.assertAlmostEqual(agg, 10000.0 * 2 / 4000)
        self.assertNotAlmostEqual(agg, mean)

    def test_tesla_stays_in_registered_baseline(self):
        row = make_row(
            **{
                "Ladeeinrichtungs-ID": "t",
                "Kreis/kreisfreie Stadt": "Landkreis Oder-Spree",
                "Breitengrad": "52,391331",
                "Längengrad": "13,79215",
                "Betreiber": "Tesla Manufacturing Brandenburg SE",
            }
        )
        spatial = squares()
        os_poly = gpd.GeoDataFrame(
            [
                {
                    "district_code": "12067",
                    "GEN": "Oder-Spree",
                    "BEZ": "Landkreis",
                    "IBZ": 43,
                    "EWZ": 179142,
                    "KFL": 2256.79,
                    "geometry": box(13.7, 52.3, 13.9, 52.5),
                }
            ],
            crs="EPSG:4326",
        ).to_crs(25832)
        spatial = pd.concat([spatial, os_poly], ignore_index=True)
        district = pd.concat(
            [
                metric_tables(spatial)[1],
                pd.DataFrame(
                    [
                        {
                            "district_code": "12067",
                            "district_name": "Oder-Spree",
                            "district_class": "landkreis",
                            "peer_group": "brandenburg_county",
                            "ibz": 43,
                            "boundary_vintage": "2025-12-31",
                            "boundary_crs": "EPSG:25832",
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        population = pd.concat(
            [
                metric_tables(spatial)[2],
                pd.DataFrame(
                    [
                        {
                            "district_code": "12067",
                            "population": 179142,
                            "population_date": "2025-12-31",
                            "cadastral_area_km2": 2256.79,
                            "area_source": "test",
                            "population_source": "test",
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        # compile_release metric_codes still 12051/12052 in helper; call compile directly
        crosswalk = build_crosswalk(spatial)
        inst, points, issues = normalize_register_frame(frame([row]), crosswalk)
        snapshot = pd.DataFrame([{"filename": "test"}])
        rel = compile_release(
            inst,
            points,
            issues,
            spatial,
            district,
            population,
            snapshot,
            {"equality_required": False},
            metric_codes=("12051", "12052", "12067"),
        )
        self.assertTrue(rel.conservation["tesla_gruenheide"]["in_registered_baseline"])
        self.assertEqual(rel.conservation["tesla_gruenheide"]["points"], 1)
        os_row = rel.district_metrics.set_index("district_code").loc["12067"]
        self.assertEqual(int(os_row["source_label_points"]), 1)
        self.assertEqual(int(os_row["source_label_points_ex_tesla_gruenheide"]), 0)

    def test_stats_gap_is_not_a_gate(self):
        rel = release_from_rows([make_row()])
        self.assertFalse(rel.conservation["stats_context"]["equality_required"])
        self.assertNotIn("stats_equality", rel.conservation["failed_gates"])
        self.assertNotIn("stats_equality", rel.conservation["open_gates"])

    def test_repeat_run_equivalence(self):
        rows = [make_row(**{"Breitengrad": "52,25", "Längengrad": "12,25"})]
        a = release_from_rows(rows)
        b = release_from_rows(rows)
        pd.testing.assert_frame_equal(a.district_metrics, b.district_metrics)
        pd.testing.assert_frame_equal(
            a.installation_snapshot.reset_index(drop=True),
            b.installation_snapshot.reset_index(drop=True),
        )

    def test_national_conservation_counts_every_row(self):
        rows = [
            make_row(**{"Ladeeinrichtungs-ID": "1", "Breitengrad": "52,25", "Längengrad": "12,25"}),
            make_row(
                **{
                    "Ladeeinrichtungs-ID": "2",
                    "Kreis/kreisfreie Stadt": "Kreisfreie Stadt Ansbach",
                    "Bundesland": "Bayern",
                    "Breitengrad": "52,25",
                    "Längengrad": "12,25",
                }
            ),
        ]
        rel = release_from_rows(rows)
        self.assertEqual(rel.conservation["national"]["installations"], 2)
        self.assertEqual(rel.conservation["national"]["outcome_sum_installations"], 2)
        self.assertTrue(rel.conservation["national"]["conservation_ok"])


if __name__ == "__main__":
    unittest.main()
