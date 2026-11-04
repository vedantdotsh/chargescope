"""ChargeScope Germany stage-B district pilot.

Parse the pinned 1 Sep 2026 register, assign every national installation to
VG250-EW districts, and emit 19 district rows plus conservation diagnostics.

WGS84 (EPSG:4326) is a disclosed provisional coordinate assumption, not a
verified BNetzA declaration. A successful run is DIAGNOSTIC_PILOT, never a
validated recommendation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import tempfile
import importlib.metadata
import zipfile
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

import duckdb
import geopandas as gpd
import pandas as pd
from openpyxl import load_workbook

PARSER_VERSION = "chargescope-pilot/0.1.0"
COORDINATE_CRS_ASSUMPTION = "EPSG:4326"
COORDINATE_CRS_STATUS = "provisional_unverified"
BOUNDARY_CRS = "EPSG:25832"
BOUNDARY_LAYER = "vg250_krs"
BOUNDARY_GF = 4
GPKG_MEMBER = "vg250-ew_ebenen_1231/DE_VG250.gpkg"
AKTUALITAET_MEMBER = "dokumentation/aktualitaet.txt"
BOUNDARY_VINTAGE = "2025-12-31"
CHARGING_SNAPSHOT_DATE = "2026-09-01"
POPULATION_DATE = "2025-12-31"
HIGH_POWER_KW = 22
TESLA_CLUSTER_RAW = ("52,391331", "13,79215")
MAX_POINT_GROUPS = 6
GERMANY_LAT = (47.0, 55.5)
GERMANY_LON = (5.5, 15.5)

EXPECTED_SHA256 = {
    "reg_0901.csv": "cdd8e38f1fa7e8512bd97caa8cf77e9f875436be1f8fe3fe1f2bd9789a504c5b",
    "stats.xlsx": "866de63203c03b40e981ccc1158a09c8d47f9671597c8431021ca0ef3662fcae",
    "vg250ew.zip": "0ee5854c5e637e53362db9dcdf889ff9c57aa7f066a3b228f9fba14fcb570754",
}

EXPECTED_HEADER = (
    "Ladeeinrichtungs-ID",
    "Betreiber",
    "Anzeigename (Karte)",
    "Status",
    "Art der Ladeeinrichtung",
    "Anzahl Ladepunkte",
    "Nennleistung Ladeeinrichtung [kW]",
    "Inbetriebnahmedatum",
    "Straße",
    "Hausnummer",
    "Adresszusatz",
    "Postleitzahl",
    "Ort",
    "Kreis/kreisfreie Stadt",
    "Bundesland",
    "Breitengrad",
    "Längengrad",
    "Standortbezeichnung",
    "Informationen zum Parkraum",
    "Bezahlsysteme",
    "Öffnungszeiten",
    "Öffnungszeiten: Wochentage",
    "Öffnungszeiten: Tageszeiten",
    "Steckertypen1",
    "Nennleistung Stecker1",
    "EVSE-ID1",
    "Public Key1",
    "Steckertypen2",
    "Nennleistung Stecker2",
    "EVSE-ID2",
    "Public Key2",
    "Steckertypen3",
    "Nennleistung Stecker3",
    "EVSE-ID3",
    "Public Key3",
    "Steckertypen4",
    "Nennleistung Stecker4",
    "EVSE-ID4",
    "Public Key4",
    "Steckertypen5",
    "Nennleistung Stecker5",
    "EVSE-ID5",
    "Public Key5",
    "Steckertypen6",
    "Nennleistung Stecker6",
    "EVSE-ID6",
    "Public Key6",
)

METRIC_CODES = (
    "12051",
    "12052",
    "12053",
    "12054",
    "12060",
    "12061",
    "12062",
    "12063",
    "12064",
    "12065",
    "12066",
    "12067",
    "12068",
    "12069",
    "12070",
    "12071",
    "12072",
    "12073",
    "11000",
)

EXPECTED_GEN = {
    "12051": "Brandenburg an der Havel",
    "12052": "Cottbus",
    "12053": "Frankfurt (Oder)",
    "12054": "Potsdam",
    "12060": "Barnim",
    "12061": "Dahme-Spreewald",
    "12062": "Elbe-Elster",
    "12063": "Havelland",
    "12064": "Märkisch-Oderland",
    "12065": "Oberhavel",
    "12066": "Oberspreewald-Lausitz",
    "12067": "Oder-Spree",
    "12068": "Ostprignitz-Ruppin",
    "12069": "Potsdam-Mittelmark",
    "12070": "Prignitz",
    "12071": "Spree-Neiße",
    "12072": "Teltow-Fläming",
    "12073": "Uckermark",
    "11000": "Berlin",
}

STATS_GAP_NOTE = (
    "Statistics workbook includes unfinished notification procedures; the CSV "
    "list contains completed procedures only. Same-date Brandenburg comparison "
    "is CSV 278,455.0 kW / 5,004 points versus statistics 281,910.6 kW / 5,099 "
    "points. Equality is not required and is not a release gate."
)

SQL_PATH = Path(__file__).with_name("metrics.sql")


class GateFail(Exception):
    """Abort before writing a release that could be mistaken for success."""


class HashMismatchError(GateFail):
    pass


class DuplicateIdError(GateFail):
    pass


class SchemaError(GateFail):
    pass


@dataclass
class Release:
    source_snapshot: pd.DataFrame
    district: pd.DataFrame
    population: pd.DataFrame
    installation_snapshot: pd.DataFrame
    point_snapshot: pd.DataFrame
    quality_issue: pd.DataFrame
    district_metrics: pd.DataFrame
    concentration_diagnostics: pd.DataFrame
    conservation: dict
    status_text: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_raw(raw_dir: Path) -> list[dict]:
    manifest_path = raw_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    by_name = {row["filename"]: row for row in manifest}
    missing = [name for name in EXPECTED_SHA256 if name not in by_name]
    if missing:
        raise HashMismatchError(f"manifest missing {missing}")
    checked = []
    for name, expected in EXPECTED_SHA256.items():
        rec = by_name[name]
        path = raw_dir / name
        if rec.get("sha256") != expected:
            raise HashMismatchError(
                f"{name}: manifest sha256 is a distinct snapshot; register it before use"
            )
        digest = sha256_file(path)
        size = path.stat().st_size
        if digest != expected:
            raise HashMismatchError(f"{name}: {digest} != {expected}")
        if rec.get("bytes") is not None and size != rec["bytes"]:
            raise HashMismatchError(f"{name}: size {size} != manifest {rec['bytes']}")
        rec = dict(rec)
        rec["verified_sha256"] = digest
        rec["verified_bytes"] = size
        checked.append(rec)
    return checked


def parse_german_number(value) -> Decimal | None:
    if value is None:
        return None
    text = str(value).strip().replace(" ", "")
    if text == "":
        return None
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        number = Decimal(text)
        if not number.is_finite():
            raise ValueError("non-finite number")
        return number
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"unparsable number {value!r}") from exc


def round_kfl(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def split_tokens(cell: str) -> list[str]:
    if cell is None:
        return []
    text = str(cell).strip()
    if text == "":
        return []
    return [part.strip() for part in text.split(";") if part.strip()]


def parse_point_slot(types_cell: str, power_cell: str) -> tuple[Decimal | None, int, list[str]]:
    type_tokens = split_tokens(types_cell)
    power_tokens = split_tokens(power_cell)
    flags: list[str] = []
    if type_tokens and power_tokens and len(type_tokens) != len(power_tokens):
        flags.append("connector_power_token_mismatch")
    if not power_tokens:
        return None, len(type_tokens), flags + ["unknown_point_power"]
    powers = [parse_german_number(tok) for tok in power_tokens]
    if any(p is not None and p < 0 for p in powers):
        raise ValueError("negative point power")
    if any(item is None for item in powers):
        return None, len(type_tokens), flags + ["unknown_point_power"]
    if len(powers) == 1:
        return powers[0], len(type_tokens), flags
    if len(set(powers)) == 1:
        return powers[0], len(type_tokens), flags
    flags.append("unequal_connector_powers")
    return max(powers), len(type_tokens), flags


def _is_filled(row: dict, slot: int) -> bool:
    return any(
        str(row.get(col, "")).strip()
        for col in (
            f"Steckertypen{slot}",
            f"Nennleistung Stecker{slot}",
            f"EVSE-ID{slot}",
            f"Public Key{slot}",
        )
    )


def assert_unique_ids(frame: pd.DataFrame) -> None:
    ids = frame["Ladeeinrichtungs-ID"].astype(str)
    if (ids.str.strip() == "").any():
        raise DuplicateIdError("blank Ladeeinrichtungs-ID")
    dups = ids[ids.duplicated(keep=False)].unique().tolist()
    if dups:
        raise DuplicateIdError(f"duplicate Ladeeinrichtungs-ID: {dups[:8]}")


def read_register_csv(path: Path) -> tuple[list[str], pd.DataFrame]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        preamble = []
        for line in handle:
            if tuple(next(csv.reader([line], delimiter=";"))) == EXPECTED_HEADER:
                break
            preamble.append(line.rstrip("\r\n"))
            if len(preamble) > 100:
                raise SchemaError("CSV header signature not found")
        else:
            raise SchemaError("CSV header signature mismatch")
        rows = []
        for ordinal, row in enumerate(csv.reader(handle, delimiter=";", strict=True), start=1):
            if len(row) != len(EXPECTED_HEADER):
                raise SchemaError(f"CSV record {ordinal}: expected 47 columns, found {len(row)}")
            rows.append(row)
    if not rows:
        raise SchemaError("empty register")
    if not any("Letzte Aktualisierung vom: 01.09.2026" in line for line in preamble):
        raise SchemaError("CSV preamble snapshot date mismatch")
    if not any(all(f"{n}. Ladepunkt" in line for n in range(1, 7)) for line in preamble):
        raise SchemaError("CSV preamble is missing six point-group labels")
    frame = pd.DataFrame(rows, columns=EXPECTED_HEADER)
    return preamble, frame


def build_crosswalk(districts: pd.DataFrame) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for bez, gen, ars in zip(districts["BEZ"], districts["GEN"], districts["district_code"]):
        key = f"{bez} {gen}"
        ars_text = str(ars)
        if key in mapping and mapping[key] != ars_text:
            raise SchemaError(f"non-unique BEZ+GEN crosswalk key {key!r}")
        mapping[key] = ars_text
    return mapping


def normalize_register_frame(
    frame: pd.DataFrame, crosswalk: dict[str, str] | None = None
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    assert_unique_ids(frame)
    issues: list[dict] = []
    installations = []
    points = []
    for ordinal, rec in enumerate(frame.to_dict("records"), start=1):
        iid = str(rec["Ladeeinrichtungs-ID"])
        anzahl_raw = str(rec["Anzahl Ladepunkte"]).strip()
        if anzahl_raw == "":
            declared = None
            issues.append(_issue(iid, "missing_declared_point_count", "quarantine", "registered_points"))
        else:
            try:
                declared = int(anzahl_raw)
            except ValueError as exc:
                raise SchemaError(f"{iid}: unparsable Anzahl Ladepunkte {anzahl_raw!r}") from exc
        if declared is not None and not 1 <= declared <= MAX_POINT_GROUPS:
            raise SchemaError(f"{iid}: Anzahl Ladepunkte {declared} outside 1..{MAX_POINT_GROUPS}")
        try:
            nominal = parse_german_number(rec["Nennleistung Ladeeinrichtung [kW]"])
            if nominal is not None and nominal < 0:
                raise ValueError("negative installation power")
        except ValueError:
            nominal = None
            issues.append(_issue(iid, "invalid_nominal_kw", "quarantine", "installation_kw"))
        if str(rec["Nennleistung Ladeeinrichtung [kW]"]).strip() == "":
            issues.append(_issue(iid, "unknown_nominal_kw", "retain_missing", "installation_kw"))
        filled_slots = [slot for slot in range(1, 7) if _is_filled(rec, slot)]
        parsed_n = len(filled_slots)
        reconcile = declared is not None and parsed_n == declared
        if not reconcile:
            issues.append(
                _issue(
                    iid,
                    "inconsistent_point_groups",
                    "quarantine_no_validated_release",
                    "registered_points",
                    detail=f"declared={declared} parsed_groups={parsed_n}",
                )
            )
        sum_point_max = Decimal("0")
        point_power_complete = parsed_n > 0
        for slot in filled_slots:
            try:
                point_kw, n_conn, flags = parse_point_slot(
                    rec.get(f"Steckertypen{slot}", ""),
                    rec.get(f"Nennleistung Stecker{slot}", ""),
                )
            except ValueError:
                point_kw, n_conn, flags = None, len(split_tokens(rec.get(f"Steckertypen{slot}", ""))), [
                    "invalid_point_power"
                ]
            if point_kw is None:
                point_power_complete = False
            else:
                sum_point_max += point_kw
            for flag in flags:
                issues.append(_issue(iid, flag, "flag", "point_power", detail=f"slot={slot}"))
            points.append(
                {
                    "installation_id": iid,
                    "source_slot": slot,
                    "raw_types": rec.get(f"Steckertypen{slot}", ""),
                    "raw_power": rec.get(f"Nennleistung Stecker{slot}", ""),
                    "evse_id": rec.get(f"EVSE-ID{slot}", ""),
                    "n_connector_tokens": n_conn,
                    "point_kw": point_kw,
                }
            )
        if parsed_n == 0:
            point_power_complete = False
            sum_point_max_out = None
        else:
            sum_point_max_out = sum_point_max if point_power_complete else None
        capped = None
        if nominal is not None and point_power_complete and reconcile:
            capped = min(nominal, sum_point_max)
        raw_lat = str(rec["Breitengrad"])
        raw_lon = str(rec["Längengrad"])
        try:
            lat = float(parse_german_number(raw_lat)) if raw_lat.strip() else None
        except ValueError:
            lat = None
            issues.append(_issue(iid, "invalid_latitude", "quarantine", "assignment"))
        try:
            lon = float(parse_german_number(raw_lon)) if raw_lon.strip() else None
        except ValueError:
            lon = None
            issues.append(_issue(iid, "invalid_longitude", "quarantine", "assignment"))
        if raw_lat.strip() and "," not in raw_lat:
            issues.append(_issue(iid, "integer_degree_coordinate", "flag", "assignment", detail="lat"))
        if raw_lon.strip() and "," not in raw_lon:
            issues.append(_issue(iid, "integer_degree_coordinate", "flag", "assignment", detail="lon"))
        kreis = str(rec["Kreis/kreisfreie Stadt"])
        label_ars = None if crosswalk is None else crosswalk.get(kreis)
        if crosswalk is not None and label_ars is None:
            issues.append(_issue(iid, "unmapped_label", "quarantine", "source_label_totals", detail=kreis))
        installations.append(
            {
                "installation_id": iid,
                "source_record_ordinal": ordinal,
                "operator_raw": rec["Betreiber"],
                "status": rec["Status"],
                "art": rec["Art der Ladeeinrichtung"],
                "declared_point_count": declared,
                "parsed_group_count": parsed_n,
                "groups_reconcile": reconcile,
                "nominal_kw": nominal,
                "sum_point_max_kw": sum_point_max_out,
                "capped_kw": capped,
                "kreis_label": kreis,
                "bundesland": rec["Bundesland"],
                "label_ars": label_ars,
                "street": rec["Straße"],
                "house_number": rec["Hausnummer"],
                "postcode": rec["Postleitzahl"],
                "city": rec["Ort"],
                "raw_lat": raw_lat,
                "raw_lon": raw_lon,
                "lat": lat,
                "lon": lon,
                "is_tesla_cluster": (raw_lat, raw_lon) == TESLA_CLUSTER_RAW,
            }
        )
    inst_df = pd.DataFrame(installations)
    point_df = pd.DataFrame(points, columns=["installation_id", "source_slot", "raw_types",
        "raw_power", "evse_id", "n_connector_tokens", "point_kw"])
    return inst_df, point_df, issues


def _issue(entity_id: str, code: str, handling: str, affected: str, detail: str = "") -> dict:
    severity = "gate" if handling in {"quarantine_no_validated_release"} else "warning"
    if handling == "quarantine":
        severity = "quarantine"
    return {
        "entity_type": "installation",
        "entity_id": entity_id,
        "issue_code": code,
        "severity": severity,
        "handling": handling,
        "affected_metrics": affected,
        "detail": detail,
    }


def _geom_ok(lat, lon) -> bool:
    if lat is None or lon is None:
        return False
    if not math.isfinite(lat) or not math.isfinite(lon):
        return False
    return -90 <= lat <= 90 and -180 <= lon <= 180


def _candidate_map(joined: gpd.GeoDataFrame) -> dict[str, tuple[str, ...]]:
    if joined.empty or "district_code" not in joined.columns:
        return {}
    matched = joined.dropna(subset=["district_code"])
    if matched.empty:
        return {}
    return (
        matched.groupby("installation_id")["district_code"]
        .agg(lambda s: tuple(sorted(set(s.astype(str)))))
        .to_dict()
    )


def assign_installations(inst: pd.DataFrame, districts_spatial: gpd.GeoDataFrame) -> pd.DataFrame:
    """Spatially test every installation against the full GF=4 Kreis layer."""
    out = inst.copy()
    germany = []
    geom_ok = []
    for lat, lon in zip(out["lat"], out["lon"]):
        ok = _geom_ok(lat, lon)
        geom_ok.append(ok)
        germany.append(
            ok and GERMANY_LAT[0] <= lat <= GERMANY_LAT[1] and GERMANY_LON[0] <= lon <= GERMANY_LON[1]
        )
    out["geom_ok"] = geom_ok
    out["in_germany_bbox"] = germany
    usable = out[out["geom_ok"]].copy()
    within_map: dict[str, tuple[str, ...]] = {}
    inter_map: dict[str, tuple[str, ...]] = {}
    if not usable.empty:
        pts = gpd.GeoDataFrame(
            usable[["installation_id"]],
            geometry=gpd.points_from_xy(usable["lon"], usable["lat"]),
            crs=COORDINATE_CRS_ASSUMPTION,
        )
        pts = pts.to_crs(districts_spatial.crs)
        layer = districts_spatial[["district_code", "geometry"]]
        within_map = _candidate_map(gpd.sjoin(pts, layer, predicate="within", how="left"))
        inter_map = _candidate_map(gpd.sjoin(pts, layer, predicate="intersects", how="left"))
    spatial_ars = []
    cand_count = []
    cand_text = []
    method = []
    outcomes = []
    for iid, label, ok in zip(out["installation_id"], out["label_ars"], out["geom_ok"]):
        label = None if pd.isna(label) else label
        if not ok:
            spatial_ars.append(None)
            cand_count.append(0)
            cand_text.append("")
            method.append("invalid_geometry")
            outcomes.append("invalid_geometry")
            continue
        cands = inter_map.get(iid) or ()
        used = "within" if within_map.get(iid) else ("intersects" if cands else "none")
        n = len(cands)
        unique = cands[0] if n == 1 else None
        spatial_ars.append(unique)
        cand_count.append(n)
        cand_text.append(";".join(cands))
        method.append(used)
        if n > 1:
            outcomes.append("ambiguous_spatial")
        elif label and unique and label == unique:
            outcomes.append("agreed")
        elif label and unique and label != unique:
            outcomes.append("conflict")
        elif not label:
            outcomes.append("unmapped_label")
        else:
            outcomes.append("unmatched_spatial")
    out["spatial_ars"] = spatial_ars
    out["spatial_candidate_count"] = cand_count
    out["spatial_candidates"] = cand_text
    out["spatial_method"] = method
    out["assignment_outcome"] = outcomes
    return out


def load_vg250(zip_path: Path, *, strict_roster: bool = True) -> tuple[gpd.GeoDataFrame, pd.DataFrame, pd.DataFrame]:
    import tempfile

    with zipfile.ZipFile(zip_path) as archive:
        aktualitaet = archive.read(AKTUALITAET_MEMBER).decode("ascii", errors="replace").strip()
        if aktualitaet != "31.12.2025":
            raise SchemaError(f"VG250 aktualitaet {aktualitaet!r} != 31.12.2025")
        with tempfile.TemporaryDirectory() as tmp:
            gpkg = archive.extract(GPKG_MEMBER, tmp)
            raw = gpd.read_file(gpkg, layer=BOUNDARY_LAYER)
            spatial = raw.loc[raw["GF"] == BOUNDARY_GF].copy()
            spatial["geometry"] = spatial.geometry.copy()
    if int(spatial.crs.to_epsg() or 0) != 25832 and str(spatial.crs) not in {BOUNDARY_CRS, "EPSG:25832"}:
        raise SchemaError(f"unexpected vg250_krs CRS {spatial.crs}")
    if not bool(spatial.geometry.is_valid.all()):
        raise SchemaError("invalid vg250_krs geometry; no silent make_valid")
    spatial["district_code"] = spatial["ARS"].astype(str)
    if (spatial["district_code"].str.len() != 5).any():
        raise SchemaError("GF=4 ARS length is not 5; do not pad")
    if spatial["district_code"].nunique() != len(spatial) or len(spatial) != 400:
        raise SchemaError("expected 400 unique GF=4 Kreis rows")
    if spatial["district_code"].duplicated().any():
        raise SchemaError("duplicate ARS after GF=4")
    metric = spatial[spatial["district_code"].isin(METRIC_CODES)].copy()
    if strict_roster:
        got = set(metric["district_code"])
        if got != set(METRIC_CODES):
            raise SchemaError(f"metric roster mismatch: missing {set(METRIC_CODES) - got}")
        names = metric.set_index("district_code")["GEN"].to_dict()
        if names != EXPECTED_GEN:
            raise SchemaError(f"VG250 GEN mismatch vs main.md roster: {names}")
        bb = metric[metric["district_code"] != "11000"]
        if int(bb["EWZ"].sum()) != 2_551_889:
            raise SchemaError("Brandenburg EWZ sum != 2551889")
        kfl_sum = sum((round_kfl(v) for v in bb["KFL"]), Decimal("0.00"))
        if kfl_sum != Decimal("29654.20"):
            raise SchemaError(f"Brandenburg rounded KFL {kfl_sum} != 29654.20")
        berlin = metric.loc[metric["district_code"] == "11000"].iloc[0]
        if int(berlin["EWZ"]) != 3_700_577:
            raise SchemaError("Berlin EWZ != 3700577")
    district_rows = []
    population_rows = []
    for _, row in metric.sort_values("district_code").iterrows():
        code = str(row["district_code"])
        ibz = int(row["IBZ"])
        if code == "11000":
            peer = "berlin_context"
            klass = "berlin_context"
        elif ibz == 40:
            peer = "brandenburg_city"
            klass = "kreisfreie_stadt"
        elif ibz == 43:
            peer = "brandenburg_county"
            klass = "landkreis"
        else:
            raise SchemaError(f"unexpected IBZ {ibz} for {code}")
        district_rows.append(
            {
                "district_code": code,
                "district_name": row["GEN"],
                "district_class": klass,
                "peer_group": peer,
                "ibz": ibz,
                "boundary_vintage": BOUNDARY_VINTAGE,
                "boundary_crs": BOUNDARY_CRS,
            }
        )
        population_rows.append(
            {
                "district_code": code,
                "population": int(row["EWZ"]),
                "population_date": POPULATION_DATE,
                "cadastral_area_km2": float(round_kfl(row["KFL"])),
                "area_source": "VG250-EW vg250_krs KFL",
                "population_source": "VG250-EW vg250_krs EWZ",
            }
        )
    return spatial, pd.DataFrame(district_rows), pd.DataFrame(population_rows)


def load_stats_context(path: Path) -> dict:
    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        bl = next(s for s in wb.sheetnames if s.startswith("2. ") and s.endswith("BL"))
        deu = next(s for s in wb.sheetnames if s.startswith("2. ") and s.endswith("DEU"))
        s42 = next(s for s in wb.sheetnames if s.startswith("4.2"))
        context = {
            "equality_required": False,
            "explanation": STATS_GAP_NOTE,
            "bl_sheet": bl,
            "deu_sheet": deu,
            "workbook_stand": "2026-09-01",
        }
        for row in wb[bl].iter_rows(values_only=True):
            values = list(row)
            if "Brandenburg" not in values:
                continue
            nums = [v for v in values if isinstance(v, (int, float)) and not isinstance(v, bool)]
            if len(nums) >= 3 and nums[0] + nums[1] == nums[2]:
                context["brandenburg_nlp"] = int(nums[0])
                context["brandenburg_slp"] = int(nums[1])
                context["brandenburg_points"] = int(nums[2])
            elif nums and float(nums[0]) > 10000:
                context["brandenburg_kw"] = float(nums[0])
        saw_install_header = False
        for row in wb[deu].iter_rows(values_only=True):
            values = list(row)
            if any(isinstance(v, str) and v == "Anzahl Ladeeinrichtungen" for v in values):
                saw_install_header = True
                continue
            if saw_install_header:
                ints = [v for v in values if isinstance(v, int)]
                if ints:
                    context["national_installations_unfinished_included"] = ints[0]
                    saw_install_header = False
            if any(isinstance(v, str) and v == "Insgesamt" for v in values):
                ints = [v for v in values if isinstance(v, int)]
                if ints:
                    context["national_points_unfinished_included"] = ints[0]
            floats = [v for v in values if isinstance(v, float) and v > 1_000_000]
            if floats and "national_kw_unfinished_included" not in context:
                context["national_kw_unfinished_included"] = float(floats[0])
        dates = []
        for row in wb[s42].iter_rows(max_row=8, values_only=True):
            dates.extend(v for v in row if isinstance(v, datetime))
        if dates:
            context["sheet_42_last_date"] = max(dates).date().isoformat()
        return context
    finally:
        wb.close()


def _kw_sum(series) -> Decimal | None:
    total = None
    for value in series:
        if value is None or (isinstance(value, float) and (pd.isna(value) or math.isnan(value))):
            continue
        total = (total or Decimal("0")) + Decimal(str(value))
    return total


def concentration_diagnostics(inst: pd.DataFrame, metric_codes: tuple[str, ...]) -> pd.DataFrame:
    rows = []
    scoped = inst[inst["label_ars"].isin(metric_codes) & inst["groups_reconcile"]]
    for code, group in scoped.groupby("label_ars"):
        total_points = int(group["declared_point_count"].fillna(0).sum())
        clustered = (
            group.groupby(["raw_lat", "raw_lon", "operator_raw"], dropna=False)
            .agg(
                n_installations=("installation_id", "count"),
                n_points=("declared_point_count", "sum"),
                kw=("nominal_kw", lambda s: s.sum(min_count=1)),
            )
            .reset_index()
            .sort_values(["n_points", "n_installations", "operator_raw"], ascending=[False, False, True])
        )
        top = clustered.iloc[0]
        tesla_pts = int(group.loc[group["is_tesla_cluster"], "declared_point_count"].fillna(0).sum())
        rows.append(
            {
                "district_code": code,
                "largest_cluster_lat": top["raw_lat"],
                "largest_cluster_lon": top["raw_lon"],
                "largest_cluster_operator": top["operator_raw"],
                "largest_cluster_installations": int(top["n_installations"]),
                "largest_cluster_points": int(top["n_points"]),
                "largest_cluster_kw": top["kw"],
                "largest_cluster_point_share": (float(top["n_points"]) / total_points) if total_points else None,
                "tesla_gruenheide_points": tesla_pts,
                "tesla_cluster_in_registered_baseline": True,
            }
        )
    columns = ["district_code", "largest_cluster_lat", "largest_cluster_lon",
        "largest_cluster_operator", "largest_cluster_installations", "largest_cluster_points",
        "largest_cluster_kw", "largest_cluster_point_share", "tesla_gruenheide_points",
        "tesla_cluster_in_registered_baseline"]
    return pd.DataFrame(rows, columns=columns).sort_values("district_code").reset_index(drop=True)


def compile_release(
    inst: pd.DataFrame,
    points: pd.DataFrame,
    issues: list[dict],
    districts_spatial: gpd.GeoDataFrame,
    district: pd.DataFrame,
    population: pd.DataFrame,
    source_snapshot: pd.DataFrame,
    stats_context: dict,
    metric_codes: tuple[str, ...] = METRIC_CODES,
) -> Release:
    for name, table in (("district", district), ("population", population)):
        if table["district_code"].isna().any() or table["district_code"].duplicated().any():
            raise SchemaError(f"{name}: missing or duplicate district code")
        if set(table["district_code"]) != set(metric_codes):
            raise SchemaError(f"{name}: metric roster mismatch")
    if inst.empty or inst["installation_id"].duplicated().any():
        raise SchemaError("empty or duplicate installation input")
    if points.duplicated(["installation_id", "source_slot"]).any():
        raise SchemaError("duplicate point identity")
    if not set(points["installation_id"]).issubset(set(inst["installation_id"])):
        raise SchemaError("orphan point")
    actual_groups = points.groupby("installation_id").size().reindex(inst["installation_id"], fill_value=0)
    if actual_groups.tolist() != inst["parsed_group_count"].tolist():
        raise SchemaError("point conservation mismatch by installation")
    assigned = assign_installations(inst, districts_spatial)
    extra_issues = []
    for iid, outcome, in_bbox in zip(
        assigned["installation_id"], assigned["assignment_outcome"], assigned["in_germany_bbox"]
    ):
        if outcome in {"conflict", "ambiguous_spatial", "unmapped_label", "unmatched_spatial", "invalid_geometry"}:
            extra_issues.append(_issue(iid, outcome, "quarantine", "geographic_totals"))
        if not in_bbox:
            extra_issues.append(_issue(iid, "outside_germany_bbox", "flag", "assignment"))
    extra_issues.append(
        {
            "entity_type": "snapshot",
            "entity_id": CHARGING_SNAPSHOT_DATE,
            "issue_code": "coordinate_crs_provisional_wgs84",
            "severity": "open_gate",
            "handling": "disclose_no_validated_release",
            "affected_metrics": "geographic_totals",
            "detail": COORDINATE_CRS_ASSUMPTION,
        }
    )
    quality = pd.DataFrame(issues + extra_issues)
    assigned = assigned.sort_values("installation_id").reset_index(drop=True)
    points = points.sort_values(["installation_id", "source_slot"]).reset_index(drop=True)
    quality = quality.sort_values(["entity_type", "entity_id", "issue_code", "detail"]).reset_index(drop=True)
    con = duckdb.connect(":memory:")
    # Inspect every Decimal value so a late high-power record cannot overflow
    # a decimal type inferred from DuckDB's default first-1,000-row sample.
    con.execute(f"SET pandas_analyze_sample={max(len(assigned), len(points), 1000)}")
    con.register("district", district)
    con.register("population", population)
    con.register("installation_snapshot", assigned)
    con.register("point_snapshot", points if not points.empty else pd.DataFrame(
        columns=["installation_id", "source_slot", "point_kw", "n_connector_tokens"]
    ))
    metrics = con.execute(SQL_PATH.read_text(encoding="utf-8")).df()
    con.close()
    conc = concentration_diagnostics(assigned, metric_codes)
    n_in = len(assigned)
    outcome_counts = assigned["assignment_outcome"].value_counts().to_dict()
    declared_points = int(assigned["declared_point_count"].fillna(0).sum())
    validated_points = int(assigned.loc[assigned["groups_reconcile"], "declared_point_count"].fillna(0).sum())
    parsed_points = 0 if points.empty else len(points)
    kw = _kw_sum(assigned["nominal_kw"])
    outcome_sum = int(sum(outcome_counts.values()))
    inconsistent_n = int((~assigned["groups_reconcile"]).sum())
    conservation_ok = outcome_sum == n_in and parsed_points == int(assigned["parsed_group_count"].sum())
    open_gates = ["coordinate_crs_provisional_wgs84"]
    failed_gates = []
    if inconsistent_n:
        open_gates.append("inconsistent_point_groups")
        failed_gates.append("validated_release_blocked_by_inconsistent_point_groups")
    if not conservation_ok:
        failed_gates.append("conservation")
    if (assigned["assignment_outcome"] != "agreed").any():
        open_gates.append("unresolved_geographic_assignments")
    if assigned["is_tesla_cluster"].any():
        open_gates.append("material_cluster_access_unverified")
    validated = False
    bb = assigned[assigned["bundesland"] == "Brandenburg"]
    be = assigned[assigned["bundesland"] == "Berlin"]
    conservation = {
        "status": "DIAGNOSTIC_PILOT",
        "validated_release_eligible": validated,
        "open_gates": open_gates,
        "failed_gates": failed_gates,
        "coordinate_crs_assumption": COORDINATE_CRS_ASSUMPTION,
        "coordinate_crs_status": COORDINATE_CRS_STATUS,
        "high_power_kw_threshold": HIGH_POWER_KW,
        "national": {
            "installations": n_in,
            "declared_points": declared_points,
            "validated_points": validated_points,
            "parsed_point_rows": parsed_points,
            "installation_kw": float(kw) if kw is not None else None,
            "assignment_outcomes": {k: int(v) for k, v in outcome_counts.items()},
            "outcome_sum_installations": outcome_sum,
            "conservation_ok": conservation_ok,
            "unassigned_or_unresolved_installations": n_in - int(outcome_counts.get("agreed", 0)),
            "unassigned_installation_share": (n_in - int(outcome_counts.get("agreed", 0))) / n_in if n_in else None,
        },
        "source_label_brandenburg": {
            "installations": int(len(bb)),
            "points": int(bb["declared_point_count"].fillna(0).sum()),
            "kw": _kw_sum(bb["nominal_kw"]),
        },
        "source_label_berlin": {
            "installations": int(len(be)),
            "points": int(be["declared_point_count"].fillna(0).sum()),
            "kw": _kw_sum(be["nominal_kw"]),
        },
        "stats_context": stats_context,
        "tesla_gruenheide": {
            "installations": int(assigned["is_tesla_cluster"].sum()),
            "points": int(assigned.loc[assigned["is_tesla_cluster"], "declared_point_count"].fillna(0).sum()),
            "kw": _kw_sum(assigned.loc[assigned["is_tesla_cluster"], "nominal_kw"]),
            "in_registered_baseline": True,
        },
        "metric_universe_codes": list(metric_codes),
        "crosswalk": "BEZ + ' ' + GEN; GEN alone is not unique",
        "spatial_coverage": "all parsed installations vs all GF=4 Kreise",
    }
    buckets = assigned.assign(conservation_bucket=[
        "quarantined_point_groups" if not valid else
        "assigned" if outcome == "agreed" else "unresolved_geography"
        for valid, outcome in zip(assigned["groups_reconcile"], assigned["assignment_outcome"])
    ])
    conservation["national"]["point_accounting"] = {
        name: {"installations": len(group),
               "known_declared_points": int(group["declared_point_count"].fillna(0).sum()),
               "unknown_declared_count_installations": int(group["declared_point_count"].isna().sum())}
        for name, group in buckets.groupby("conservation_bucket", sort=True)
    }
    accounted = sum(v["known_declared_points"] for v in conservation["national"]["point_accounting"].values())
    if accounted != declared_points:
        raise SchemaError("declared point conservation failed")
    unresolved_points = int(assigned.loc[assigned["assignment_outcome"] != "agreed", "declared_point_count"].fillna(0).sum())
    conservation["national"]["unresolved_known_declared_points"] = unresolved_points
    conservation["national"]["unresolved_point_share"] = unresolved_points / declared_points if declared_points else None
    if stats_context.get("brandenburg_points") is not None:
        conservation["stats_context"]["points_minus_csv"] = stats_context["brandenburg_points"] - conservation["source_label_brandenburg"]["points"]
    if stats_context.get("brandenburg_kw") is not None and conservation["source_label_brandenburg"]["kw"] is not None:
        conservation["stats_context"]["kw_minus_csv"] = Decimal(str(stats_context["brandenburg_kw"])) - conservation["source_label_brandenburg"]["kw"]
    bb_pop = population[population["district_code"] != "11000"]
    if not bb_pop.empty and "source_label_points" in metrics.columns:
        bb_metrics = metrics[metrics["peer_group"] != "berlin_context"]
        pop_sum = int(bb_metrics["population"].sum())
        pts_sum = int(bb_metrics["source_label_points"].sum())
        mean_rate = bb_metrics["points_per_10000_residents_source_label"].mean()
        conservation["brandenburg_18_aggregate_points_per_10000"] = (
            None if pop_sum == 0 or bb_metrics["population"].isna().any()
            or (bb_metrics["population"] <= 0).any() else 10000.0 * pts_sum / pop_sum
        )
        conservation["brandenburg_18_unweighted_mean_points_per_10000"] = (
            None if pd.isna(mean_rate) else float(mean_rate)
        )
    status = [
        "DIAGNOSTIC_PILOT",
        "validated_release_eligible=false",
        f"coordinate_crs_assumption={COORDINATE_CRS_ASSUMPTION}",
        f"coordinate_crs_status={COORDINATE_CRS_STATUS}",
        "open_gates=" + ",".join(open_gates),
        "failed_gates=" + (",".join(failed_gates) if failed_gates else ""),
        "tesla_gruenheide_retained_in_registered_baseline=true",
        "stats_equality_required=false",
    ]
    return Release(
        source_snapshot=source_snapshot,
        district=district,
        population=population,
        installation_snapshot=assigned,
        point_snapshot=points,
        quality_issue=quality,
        district_metrics=metrics,
        concentration_diagnostics=conc,
        conservation=conservation,
        status_text="\n".join(status) + "\n",
    )


def _write_tables(release: Release, out_dir: Path) -> dict:
    release.source_snapshot.to_csv(out_dir / "source_snapshot.csv", index=False)
    release.district.to_csv(out_dir / "district.csv", index=False)
    release.population.to_csv(out_dir / "population.csv", index=False)
    release.installation_snapshot.to_csv(out_dir / "installation_snapshot.csv", index=False)
    release.point_snapshot.to_csv(out_dir / "point_snapshot.csv", index=False)
    release.quality_issue.to_csv(out_dir / "quality_issue.csv", index=False)
    release.district_metrics.to_csv(out_dir / "district_metrics.csv", index=False)
    release.concentration_diagnostics.to_csv(out_dir / "concentration_diagnostics.csv", index=False)
    ledger_columns = ["installation_id", "kreis_label", "bundesland", "label_ars", "raw_lat",
        "raw_lon", "spatial_ars", "spatial_candidates", "spatial_candidate_count",
        "spatial_method", "assignment_outcome", "declared_point_count", "groups_reconcile"]
    release.installation_snapshot[ledger_columns].to_csv(out_dir / "assignment_ledger.csv", index=False)
    (out_dir / "metrics.sql").write_bytes(SQL_PATH.read_bytes())
    (out_dir / "conservation_report.json").write_text(
        json.dumps(release.conservation, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    (out_dir / "STATUS.txt").write_text(release.status_text, encoding="utf-8")
    from chargescope.portfolio import write_portfolio
    write_portfolio(release, out_dir)
    manifest = {
        "parser_version": PARSER_VERSION,
        "coordinate_crs_assumption": COORDINATE_CRS_ASSUMPTION,
        "coordinate_crs_status": COORDINATE_CRS_STATUS,
        "files": {p.name: sha256_file(p) for p in sorted(out_dir.iterdir())},
        "inputs": release.source_snapshot.astype(object).where(pd.notna(release.source_snapshot), None).to_dict("records"),
        "dependencies": {name: importlib.metadata.version(name) for name in
            ("pandas", "geopandas", "duckdb", "openpyxl", "shapely", "pyproj", "pyogrio")},
        "code": {p.name: sha256_file(p) for p in sorted(Path(__file__).parent.iterdir())
                 if p.suffix in {".py", ".sql"}},
        "lock_sha256": sha256_file(Path(__file__).parents[1] / "uv.lock"),
        "validated_release_eligible": False,
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    return manifest


def write_release(release: Release, out_dir: Path) -> Path:
    """Write an immutable diagnostic bundle, then atomically update its pointer.

    Failed data gates retain a separate diagnostic bundle and never change CURRENT.
    No validated/public release path is used by this pilot.
    """
    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".stage-", dir=out_dir) as tmp:
        staged = Path(tmp) / "bundle"
        staged.mkdir()
        manifest = _write_tables(release, staged)
        release_id = sha256_file(staged / "run_manifest.json")
        failed = bool(release.conservation["failed_gates"])
        category = "failed" if failed else "runs"
        target = out_dir / category / release_id
        target.parent.mkdir(exist_ok=True)
        if target.exists():
            expected_files = set(manifest["files"]) | {"run_manifest.json"}
            if {p.name for p in target.iterdir()} != expected_files:
                raise GateFail("existing diagnostic bundle has missing or extra files")
            for name in expected_files:
                if sha256_file(target / name) != sha256_file(staged / name):
                    raise GateFail(f"existing diagnostic bundle was modified: {name}")
        else:
            os.replace(staged, target)
        if failed:
            raise GateFail(f"data gates failed; diagnostics retained at {target}; CURRENT unchanged")
        pointer = Path(tmp) / "CURRENT.json"
        pointer.write_text(json.dumps({"path": target.relative_to(out_dir).as_posix(),
            "status": "DIAGNOSTIC_PILOT", "validated_release_eligible": False}, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(pointer, out_dir / "CURRENT.json")
    return target


def run(raw_dir: Path, out_dir: Path) -> Release:
    checked = verify_raw(raw_dir)
    preamble, frame = read_register_csv(raw_dir / "reg_0901.csv")
    spatial, district, population = load_vg250(raw_dir / "vg250ew.zip")
    crosswalk = build_crosswalk(spatial)
    inst, points, issues = normalize_register_frame(frame, crosswalk)
    try:
        stats_context = load_stats_context(raw_dir / "stats.xlsx")
    except (KeyError, ValueError, OSError) as exc:
        stats_context = {"equality_required": False, "explanation": STATS_GAP_NOTE, "parse_error": str(exc)}
    source_snapshot = pd.DataFrame(
        [
            {
                "filename": rec["filename"],
                "url": rec.get("url"),
                "reference_date": rec.get("reference_date"),
                "sha256": rec["verified_sha256"],
                "bytes": rec["verified_bytes"],
                "license": rec.get("license"),
                "attribution": rec.get("attribution"),
                "parser_version": PARSER_VERSION,
                "retrieved_at": rec.get("retrieved_at"),
                "preserved_at": rec.get("preserved_at"),
                "acquisition_note": rec.get("acquisition_note"),
                "row_count": len(frame) if rec["filename"] == "reg_0901.csv" else len(spatial) if rec["filename"] == "vg250ew.zip" else None,
                "schema": json.dumps(list(EXPECTED_HEADER) if rec["filename"] == "reg_0901.csv" else list(spatial.columns) if rec["filename"] == "vg250ew.zip" else list(stats_context), ensure_ascii=False),
                "csv_preamble": "\n".join(preamble) if rec["filename"] == "reg_0901.csv" else "",
            }
            for rec in checked
        ]
    )
    release = compile_release(
        inst, points, issues, spatial, district, population, source_snapshot, stats_context
    )
    write_release(release, out_dir)
    return release


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="ChargeScope Germany diagnostic district pilot (no website/BI)."
    )
    parser.add_argument("--raw", default="data/raw")
    parser.add_argument("--out", default="data/work/pilot")
    args = parser.parse_args(argv)
    try:
        release = run(Path(args.raw), Path(args.out))
    except GateFail as exc:
        print(f"GATE FAIL: {exc}")
        return 2
    print(release.status_text, end="")
    print(f"wrote {args.out}")
    if release.conservation.get("failed_gates"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
