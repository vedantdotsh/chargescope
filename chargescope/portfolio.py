"""Fixed-snapshot descriptive BI interface; not a validated planning release."""

import argparse
import json
import math
from pathlib import Path

import duckdb
import pandas as pd


SQL_PATH = Path(__file__).with_suffix(".sql")


def _records(table):
    return json.loads(table.to_json(orient="records", double_precision=15))


def _parity(release, district_scenario, region_scenario):
    checks = []
    for row in district_scenario.itertuples(index=False):
        selected = release.installation_snapshot.query("label_ars == @row.district_code")
        if row.scenario_id != "registered":
            selected = selected[~selected.is_tesla_cluster]
        unknown = int((~selected.groups_reconcile | selected.declared_point_count.isna()).sum())
        points = None if unknown else int(selected.declared_point_count.sum())
        capacity = selected.nominal_kw.dropna()
        capacity = sum(float(value) for value in capacity) if len(capacity) else None
        expected = {
            "installations": len(selected), "points": points, "nominal_kw": capacity,
            "unknown_point_installations": unknown,
            "nominal_kw_missing_n": int(selected.nominal_kw.isna().sum()),
            "points_per_10000_residents": (
                10000 * points / row.population
                if points is not None and pd.notna(row.population) and row.population > 0 else None
            ),
        }
        for metric, value in expected.items():
            actual = getattr(row, metric)
            passed = pd.isna(actual) if value is None else (
                pd.notna(actual) and math.isclose(float(actual), value, rel_tol=1e-12, abs_tol=1e-9))
            checks.append((row.scenario_id, row.district_code, metric, value, actual, bool(passed)))
    for row in region_scenario.itertuples(index=False):
        selected = district_scenario.query("scenario_id == @row.scenario_id and region == @row.region")
        valid = (selected.population.notna() & (selected.population > 0)).all()
        expected = (10000 * selected.known_points.sum() / selected.population.sum()
                    if valid and selected.unknown_point_installations.sum() == 0 else None)
        actual = row.points_per_10000_residents
        passed = pd.isna(actual) if expected is None else (
            pd.notna(actual) and math.isclose(actual, expected, rel_tol=1e-12))
        checks.append((row.scenario_id, row.region, "aggregate_rate", expected, actual, bool(passed)))
    return pd.DataFrame(checks, columns=[
        "scenario_id", "entity", "metric", "pandas_expected", "sql_actual", "passed"])


def build_portfolio(release):
    with duckdb.connect(":memory:") as connection:
        connection.execute(f"SET pandas_analyze_sample={max(len(release.installation_snapshot), 1000)}")
        for name in ("district", "population", "installation_snapshot"):
            connection.register(name, getattr(release, name))
        connection.execute(SQL_PATH.read_text(encoding="utf-8"))
        tables = {
            "bi_scenario": connection.sql("SELECT * FROM scenario ORDER BY scenario_id").df(),
            "bi_district_scenario": connection.sql(
                "SELECT * FROM district_scenario ORDER BY scenario_id, district_code").df(),
            "bi_region_scenario": connection.sql(
                "SELECT * FROM region_scenario ORDER BY scenario_id, region").df(),
        }
        evidence_tables = {
            name: connection.sql(f"SELECT * FROM evidence_{name} ORDER BY ALL").df()
            for name in ("regional_comparison", "cluster_sensitivity", "geography")
        }
    tables["bi_district"] = release.district.merge(
        release.population, on="district_code", validate="one_to_one").sort_values("district_code")
    tables["bi_installation"] = release.installation_snapshot.loc[
        release.installation_snapshot.label_ars.isin(release.district.district_code), [
            "installation_id", "label_ars", "operator_raw", "declared_point_count",
            "groups_reconcile", "nominal_kw", "is_tesla_cluster", "assignment_outcome",
            "spatial_ars", "raw_lat", "raw_lon",
        ]].rename(columns={"label_ars": "district_code"}).sort_values("installation_id")
    tables["bi_point"] = release.point_snapshot[
        release.point_snapshot.installation_id.isin(tables["bi_installation"].installation_id)
    ].sort_values(["installation_id", "source_slot"])
    tables["sql_parity"] = _parity(
        release, tables["bi_district_scenario"], tables["bi_region_scenario"])
    if not tables["sql_parity"].passed.all():
        from chargescope.pipeline import GateFail
        raise GateFail("portfolio SQL/pandas parity failed; CURRENT unchanged")
    findings = [
        {
            "id": "regional_comparison", "sql_view": "evidence_regional_comparison",
            "implication": "Use population-normalized registered provision alongside counts; Berlin is context, not a Brandenburg peer.",
            "limitations": "Different settlement patterns; population predates charging snapshot. Supply counts do not measure demand, access or utilization.",
        },
        {
            "id": "cluster_sensitivity", "sql_view": "evidence_cluster_sensitivity",
            "implication": "District position can depend materially on a co-located registered group; show baseline and hypothetical exclusion together.",
            "limitations": "Hypothetical only, not a correction or an assertion of restricted access. Coordinates are grouping evidence, not unique physical sites.",
        },
        {
            "id": "geography", "sql_view": "evidence_geography",
            "implication": "Label totals and agreement-only geographic totals answer different questions; retain unresolved records for verification.",
            "limitations": "Agreement is under provisional WGS84, not verified truth. Do not replace baseline totals or infer a supply shortfall.",
        },
    ]
    for finding in findings:
        name = finding["id"]
        tables[f"evidence_{name}"] = evidence_tables[name]
        finding["values"] = _records(evidence_tables[name])
    return tables, {
        "status": "DIAGNOSTIC_PILOT", "validated_release_eligible": False,
        "charging_snapshot": "2026-09-01", "population_date": "2025-12-31",
        "boundary_vintage": "2025-12-31", "open_gates": release.conservation["open_gates"],
        "source_snapshots": _records(release.source_snapshot), "findings": findings,
        "scenario_rule": "registered retains every source-labelled installation; hypothetical_exclusion removes only is_tesla_cluster=true, as flagged by the existing parser",
        "rank_rule": "Descending points per 10,000 residents across Brandenburg districts only; RANK ties share position; missing rates unranked",
    }


def write_portfolio(release, out_dir):
    tables, evidence = build_portfolio(release)
    for name, table in tables.items():
        table.to_csv(out_dir / f"{name}.csv", index=False)
    (out_dir / "portfolio.sql").write_bytes(SQL_PATH.read_bytes())
    (out_dir / "findings.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    model = {
        "status": "MODEL_SPEC_ONLY_NOT_DESKTOP_VERIFIED",
        "encoding": "UTF-8", "null_encoding": "empty CSV cell; never replace with zero",
        "text_columns": ["district_code", "spatial_ars", "installation_id", "scenario_id"],
        "tables": {name: {"rows": len(table), "columns": list(table.columns)}
                   for name, table in tables.items()},
        "grain": {
            "bi_district": "one row per district; population stored once",
            "bi_scenario": "one row per scenario",
            "bi_installation": "one source installation; nominal_kw counted once, registered baseline only",
            "bi_point": "one installation_id + source_slot; connector tokens are not points",
            "bi_district_scenario": "one district_code + scenario_id; do not sum across scenarios",
            "bi_region_scenario": "one region + scenario_id; disconnected QA table, not additive to district fact",
        },
        "relationships": [
            ["bi_district.district_code", "bi_installation.district_code", "1:* single"],
            ["bi_installation.installation_id", "bi_point.installation_id", "1:* single"],
            ["bi_district.district_code", "bi_district_scenario.district_code", "1:* single"],
            ["bi_scenario.scenario_id", "bi_district_scenario.scenario_id", "1:* single"],
        ],
        "required_filters": "Single-select scenario (default registered). Scenario filters aggregate fact only, not installation or point baseline detail.",
    }
    (out_dir / "bi_model.json").write_text(json.dumps(model, indent=2) + "\n", encoding="utf-8")


def replay_evidence(bundle):
    from chargescope.pipeline import GateFail, sha256_file

    manifest = json.loads((bundle / "run_manifest.json").read_text(encoding="utf-8"))
    if sha256_file(bundle / "run_manifest.json") != bundle.name:
        raise GateFail("bundle manifest modified or bundle directory renamed")
    for name, expected in manifest["files"].items():
        if sha256_file(bundle / name) != expected:
            raise GateFail(f"bundle file modified: {name}")
    text_types = {name: str for name in ("district_code", "label_ars", "spatial_ars", "installation_id")}
    queries = {}
    with duckdb.connect(":memory:") as connection:
        for name in ("district", "population", "installation_snapshot"):
            connection.register(name, pd.read_csv(bundle / f"{name}.csv", dtype=text_types))
        connection.execute((bundle / "portfolio.sql").read_text(encoding="utf-8"))
        for name in ("district_scenario", "region_scenario", "evidence_regional_comparison",
                     "evidence_cluster_sensitivity", "evidence_geography"):
            filename = name if name.startswith("evidence_") else f"bi_{name}"
            expected = pd.read_csv(bundle / f"{filename}.csv", dtype=text_types)
            actual = connection.sql(f"SELECT * FROM {name} ORDER BY ALL").df()
            expected = expected.sort_values(list(expected.columns), na_position="last").reset_index(drop=True)
            try:
                pd.testing.assert_frame_equal(
                    actual.convert_dtypes(), expected.convert_dtypes(),
                    check_dtype=False, rtol=1e-12, atol=1e-9)
            except AssertionError as error:
                raise GateFail(f"SQL replay mismatch: {name}: {error}") from error
            queries[name] = {"rows": len(actual), "passed": True}
    return {"passed": True, "queries": queries, "status": "DIAGNOSTIC_PILOT"}


def main():
    parser = argparse.ArgumentParser(description="Replay the pinned diagnostic SQL evidence pack")
    parser.add_argument("--bundle", type=Path, required=True)
    args = parser.parse_args()
    from chargescope.pipeline import GateFail
    try:
        result = replay_evidence(args.bundle)
    except (GateFail, OSError, ValueError) as error:
        parser.exit(2, f"EVIDENCE FAIL: {error}\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
