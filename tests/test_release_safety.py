import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from chargescope.pipeline import (EXPECTED_HEADER, GateFail, SchemaError, compile_release,
    normalize_register_frame, read_register_csv, write_release, verify_raw, EXPECTED_SHA256)
from test_contracts import make_row, release_from_rows, squares, metric_tables, frame


class ReleaseSafety(unittest.TestCase):
    def test_mixed_missing_labels_are_not_conflicts(self):
        rel = release_from_rows([make_row(), make_row(**{
            "Ladeeinrichtungs-ID": "2", "Kreis/kreisfreie Stadt": "Unknown district"})])
        row = rel.installation_snapshot.set_index("installation_id").loc["2"]
        self.assertEqual("unmapped_label", row["assignment_outcome"])

    def test_failed_gate_and_interrupted_write_preserve_current(self):
        good = release_from_rows([make_row()])
        bad = release_from_rows([make_row(**{"Anzahl Ladepunkte": "2"})])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = write_release(good, root)
            before = {p.name: p.read_bytes() for p in bundle.iterdir()}
            pointer = (root / "CURRENT.json").read_bytes()
            with self.assertRaises(GateFail):
                write_release(bad, root)
            self.assertEqual(pointer, (root / "CURRENT.json").read_bytes())
            self.assertTrue(list((root / "failed").glob("*/STATUS.txt")))
            with patch.object(pd.DataFrame, "to_csv", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    write_release(good, root)
            self.assertEqual(pointer, (root / "CURRENT.json").read_bytes())
            self.assertEqual(before, {p.name: p.read_bytes() for p in bundle.iterdir()})
            self.assertEqual(bundle, write_release(good, root))
            self.assertEqual(before, {p.name: p.read_bytes() for p in bundle.iterdir()})

    def test_duplicate_population_and_orphan_points_fail_before_join(self):
        rel = release_from_rows([make_row()])
        spatial = squares()
        _, districts, population = metric_tables(spatial)
        args = [rel.installation_snapshot, rel.point_snapshot, [], spatial, districts,
                pd.concat([population, population.iloc[:1]]), rel.source_snapshot, {}]
        with self.assertRaisesRegex(SchemaError, "duplicate district"):
            compile_release(*args, metric_codes=("12051", "12052"))
        args[5] = population
        args[1] = rel.point_snapshot.assign(installation_id="missing")
        with self.assertRaisesRegex(SchemaError, "orphan point"):
            compile_release(*args, metric_codes=("12051", "12052"))

    def test_all_unknown_capacity_is_null_in_sql_and_partial_coverage_visible(self):
        row = make_row(**{"Nennleistung Ladeeinrichtung [kW]": "", "Nennleistung Stecker1": ""})
        rel = release_from_rows([row])
        district = rel.district_metrics.set_index("district_code").loc["12051"]
        self.assertTrue(pd.isna(district["source_label_kw"]))
        self.assertEqual(1, district["source_label_kw_missing_n"])
        self.assertEqual(1, district["unknown_power_point_share"])
        self.assertIsNone(rel.conservation["national"]["installation_kw"])
        other = make_row(**{"Ladeeinrichtungs-ID": "2"})
        partial = release_from_rows([row, other]).district_metrics.set_index("district_code").loc["12051"]
        self.assertEqual(22, partial["source_label_kw"])
        self.assertEqual(1, partial["source_label_kw_missing_n"])

    def test_invalid_numbers_and_unknown_group_counts_remain_visible(self):
        for token in ("NaN", "Infinity", "-22"):
            inst, points, issues = normalize_register_frame(frame([make_row(**{
                "Nennleistung Ladeeinrichtung [kW]": token, "Nennleistung Stecker1": token})]), {})
            self.assertTrue(pd.isna(inst.iloc[0]["nominal_kw"]))
            self.assertTrue(pd.isna(points.iloc[0]["point_kw"]))
            self.assertIn("invalid_nominal_kw", {q["issue_code"] for q in issues})
        rel = release_from_rows([make_row(**{"Anzahl Ladepunkte": ""})])
        ledger = rel.conservation["national"]["point_accounting"]
        self.assertEqual(1, ledger["quarantined_point_groups"]["unknown_declared_count_installations"])
        self.assertTrue(rel.conservation["failed_gates"])

    def test_header_discovery_and_record_width(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "register.csv"
            row = make_row()
            with source.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.writer(handle, delimiter=";")
                writer.writerow(["Letzte Aktualisierung vom: 01.09.2026"])
                writer.writerow([" ".join(f"{i}. Ladepunkt" for i in range(1, 7))])
                writer.writerow(EXPECTED_HEADER)
                writer.writerow([row[k] for k in EXPECTED_HEADER])
            preamble, records = read_register_csv(source)
            self.assertEqual(2, len(preamble))
            self.assertEqual(1, len(records))
            with source.open("a", encoding="utf-8", newline="") as handle:
                csv.writer(handle, delimiter=";").writerow(["short row"])
            with self.assertRaisesRegex(SchemaError, "expected 47 columns"):
                read_register_csv(source)

    def test_bad_source_hash_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "manifest.json").write_text(json.dumps([
                {"filename": name, "sha256": sha} for name, sha in EXPECTED_SHA256.items()
            ]), encoding="utf-8")
            for name in EXPECTED_SHA256:
                (root / name).write_bytes(b"different snapshot")
            with self.assertRaises(GateFail):
                verify_raw(root)


if __name__ == "__main__":
    unittest.main()
