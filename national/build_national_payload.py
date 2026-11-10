#!/usr/bin/env python3
"""ChargeScope national story payload builder (stdlib only).

Aggregates the pinned 1 Sep 2026 Bundesnetzagentur register CSV nationally by
source-label Bundesland and Kreis, with BKG VG250-EW 31 Dec 2025 population as
the single denominator. Reads the BKG GeoPackage attribute tables with sqlite3
(no geometry decoded) and the statistics workbook with zipfile + ElementTree.

Reuses, but does not re-run, the validated pipeline: raw hashes are the pipeline's
pinned hashes; parsing rules mirror chargescope/pipeline.py; coordinate-derived
Kreis candidates are read from the hash-verified pinned bundle's assignment ledger.
Nothing here reinterprets or corrects geography. Output stays DIAGNOSTIC_PILOT.

Run:  python -I build_national_payload.py [--raw DIR] [--bundle DIR] [--out DIR]
"""

from __future__ import annotations

import argparse
import collections
import csv
import datetime
import hashlib
import json
import re
import sqlite3
import statistics
import sys
import xml.etree.ElementTree as ET
import zipfile
from decimal import Decimal
from pathlib import Path

GENERATOR = "national-story-data/0.1.0"
SCHEMA = "chargescope-national-story/1"
ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent

CHARGING_DATE = "2026-09-01"
POPULATION_DATE = "2025-12-31"
PINNED_BUNDLE = "f92f3ed285d0a0d4eef184bafa823c0567215ca8d5aec0ec6751e24bd3b678d0"
EXPECTED_SHA256 = {
    "reg_0901.csv": "cdd8e38f1fa7e8512bd97caa8cf77e9f875436be1f8fe3fe1f2bd9789a504c5b",
    "stats.xlsx": "866de63203c03b40e981ccc1158a09c8d47f9671597c8431021ca0ef3662fcae",
    "vg250ew.zip": "0ee5854c5e637e53362db9dcdf889ff9c57aa7f066a3b228f9fba14fcb570754",
}
# Pinned regression targets for the source snapshot.
PINNED_TOTALS = {
    "germany": (116443, 209136, Decimal("9086797.5")),
    "12": (3032, 5004, Decimal("278455.0")),  # Brandenburg, source label
    "11": (4953, 7561, Decimal("211420.1")),  # Berlin, source label
}
GPKG_MEMBER = "vg250-ew_ebenen_1231/DE_VG250.gpkg"
AKTUALITAET_MEMBER = "dokumentation/aktualitaet.txt"

BASE_HEADER = (
    "Ladeeinrichtungs-ID", "Betreiber", "Anzeigename (Karte)", "Status",
    "Art der Ladeeinrichtung", "Anzahl Ladepunkte", "Nennleistung Ladeeinrichtung [kW]",
    "Inbetriebnahmedatum", "Straße", "Hausnummer", "Adresszusatz", "Postleitzahl", "Ort",
    "Kreis/kreisfreie Stadt", "Bundesland", "Breitengrad", "Längengrad",
    "Standortbezeichnung", "Informationen zum Parkraum", "Bezahlsysteme", "Öffnungszeiten",
    "Öffnungszeiten: Wochentage", "Öffnungszeiten: Tageszeiten",
)
MAX_POINT_GROUPS = 6
EXPECTED_HEADER = BASE_HEADER + tuple(
    name for n in range(1, MAX_POINT_GROUPS + 1)
    for name in (f"Steckertypen{n}", f"Nennleistung Stecker{n}", f"EVSE-ID{n}", f"Public Key{n}")
)
TESLA_CLUSTER_RAW = ("52,391331", "13,79215")  # same flag as the pinned pipeline
BB_DISTRICTS = tuple(f"120{n}" for n in (51, 52, 53, 54, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73))
BERLIN = "11000"

# BNetzA published point power classes (statistics workbook, sheet 2 DEU): upper edges in kW.
CLASS_EDGES = (
    ("le3_7", Decimal("3.7")), ("gt3_7to15", Decimal(15)), ("gt15to22", Decimal(22)),
    ("gt22to49", Decimal(49)), ("gt49to59", Decimal(59)), ("gt59to149", Decimal(149)),
    ("gt149to299", Decimal(299)), ("gt299", None),
)
# Compact four-way grouping of those classes (same edges, merged).
GROUP_OF_CLASS = {
    "le3_7": "le22", "gt3_7to15": "le22", "gt15to22": "le22",
    "gt22to49": "gt22to149", "gt49to59": "gt22to149", "gt59to149": "gt22to149",
    "gt149to299": "gt149to299", "gt299": "gt299",
}
GROUPS = ("le22", "gt22to149", "gt149to299", "gt299")
# Display thresholds for per-district caution flags. Presentation choices, not scientific cut-offs.
FLAG_AGREE_BELOW = 0.95
FLAG_TOPGROUP_SHARE = 0.20
FLAG_SMALL_POINTS = 100
STATS_CLASS_LABELS = {
    "0 - 3,7 kW": "le3_7", "> 3,7 - 15 kW": "gt3_7to15", "> 15 - 22 kW": "gt15to22",
    "> 22 - 49 kW": "gt22to49", "> 49 - 59 kW": "gt49to59", "> 59 - 149 kW": "gt59to149",
    "> 149 - 299 kW": "gt149to299", "> 299 kW": "gt299",
}


class GateFail(Exception):
    """Abort: a source, schema or conservation check failed."""


# ---------------------------------------------------------------- small helpers

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_german_number(value) -> Decimal | None:
    """Same rule as pipeline.parse_german_number: decimal comma, blank means missing."""
    if value is None:
        return None
    text = str(value).strip().replace(" ", "")
    if text == "":
        return None
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    number = Decimal(text)
    if not number.is_finite():
        raise ValueError(f"non-finite number {value!r}")
    return number


def split_tokens(cell: str) -> list[str]:
    text = (cell or "").strip()
    return [part.strip() for part in text.split(";") if part.strip()] if text else []


def parse_point_slot(types_cell: str, power_cell: str):
    """Point maximum kW (None if unknown) and connector token count; mirrors the pipeline."""
    n_conn = len(split_tokens(types_cell))
    tokens = split_tokens(power_cell)
    if not tokens:
        return None, n_conn
    try:
        powers = [parse_german_number(tok) for tok in tokens]
    except Exception:
        return None, n_conn
    if any(p is None or p < 0 for p in powers):
        return None, n_conn
    return max(powers), n_conn


def power_class(kw: Decimal | None) -> str | None:
    if kw is None:
        return None
    for name, edge in CLASS_EDGES:
        if edge is None or kw <= edge:
            return name
    raise AssertionError("unreachable")


def normalize_label_name(name: str) -> str:
    return re.sub(r"[^0-9a-zäöüß]", "", name.casefold())


def rate(numerator, denominator, scale):
    """Ratio of sums scaled; None if the denominator is missing or not positive."""
    if numerator is None or denominator is None or denominator <= 0:
        return None
    if isinstance(denominator, Decimal):  # cadastral area: exact 2-dp decimal -> float once
        denominator = float(denominator)
    return scale * numerator / denominator


def competition_ranks(values: dict[str, float | None]) -> dict[str, int | None]:
    present = [v for v in values.values() if v is not None]
    return {key: (None if v is None else 1 + sum(1 for other in present if other > v))
            for key, v in values.items()}


def quartile_summary(values: list[float]) -> dict | None:
    if len(values) < 2:
        return None
    ordered = sorted(values)
    q1, median, q3 = statistics.quantiles(ordered, n=4, method="inclusive")  # type 7
    iqr = q3 - q1
    inliers = [v for v in ordered if q1 - 1.5 * iqr <= v <= q3 + 1.5 * iqr]
    return {
        "n": len(ordered), "min": ordered[0], "q1": q1, "median": median, "q3": q3,
        "max": ordered[-1], "whiskerLow": inliers[0], "whiskerHigh": inliers[-1],
        "outliers": sum(1 for v in ordered if v not in inliers),
    }


# ---------------------------------------------------------------- source verification

def verify_inputs(raw_dir: Path, bundle_dir: Path) -> dict:
    manifest = {row["filename"]: row for row in json.loads((raw_dir / "manifest.json").read_text(encoding="utf-8"))}
    out = {}
    for name, expected in EXPECTED_SHA256.items():
        if manifest.get(name, {}).get("sha256") != expected:
            raise GateFail(f"{name}: manifest hash differs from pinned snapshot; register a new snapshot first")
        path = raw_dir / name
        if path.stat().st_size != manifest[name]["bytes"]:
            raise GateFail(f"{name}: size differs from manifest")
        digest = sha256_file(path)
        if digest != expected:
            raise GateFail(f"{name}: sha256 {digest} != {expected}")
        out[name] = {"sha256": digest, "bytes": path.stat().st_size, "url": manifest[name]["url"],
                     "referenceDate": manifest[name]["reference_date"],
                     "licence": manifest[name]["license"], "attribution": manifest[name]["attribution"]}
    run_manifest = bundle_dir / "run_manifest.json"
    if sha256_file(run_manifest) != bundle_dir.name or bundle_dir.name != PINNED_BUNDLE:
        raise GateFail("pinned bundle id (sha256 of run_manifest.json) mismatch")
    files = json.loads(run_manifest.read_text(encoding="utf-8"))["files"]
    for name, expected in files.items():
        if sha256_file(bundle_dir / name) != expected:
            raise GateFail(f"pinned bundle file modified: {name}")
    out["bundle"] = {"id": bundle_dir.name, "filesVerified": len(files) + 1}
    return out


# ---------------------------------------------------------------- register CSV

def read_register(path: Path):
    """Return (preamble lines, list of installation records). Fails on any schema surprise."""
    with path.open("rb") as handle:
        if handle.read(3) != b"\xef\xbb\xbf":
            raise GateFail("CSV is not UTF-8 with BOM")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        preamble = []
        for line in handle:
            if tuple(next(csv.reader([line], delimiter=";"))) == EXPECTED_HEADER:
                break
            preamble.append(line.rstrip("\r\n"))
            if len(preamble) > 100:
                raise GateFail("CSV header signature not found")
        else:
            raise GateFail("CSV header signature mismatch")
        if len(preamble) != 10:
            raise GateFail(f"expected 10 preamble lines, found {len(preamble)}")
        if not any("Letzte Aktualisierung vom: 01.09.2026" in line for line in preamble):
            raise GateFail("CSV preamble date is not 01.09.2026")
        col = {name: i for i, name in enumerate(EXPECTED_HEADER)}
        records, seen = [], set()
        for ordinal, row in enumerate(csv.reader(handle, delimiter=";", strict=True), start=1):
            if len(row) != len(EXPECTED_HEADER):
                raise GateFail(f"record {ordinal}: expected 47 fields, found {len(row)}")
            iid = row[col["Ladeeinrichtungs-ID"]]  # text, never converted to a number
            if iid.strip() == "" or iid in seen:
                raise GateFail(f"record {ordinal}: blank or duplicate Ladeeinrichtungs-ID")
            seen.add(iid)
            records.append(parse_record(row, col, iid))
    if not records:
        raise GateFail("empty register")
    return preamble, records


def parse_record(row, col, iid: str) -> dict:
    declared_raw = row[col["Anzahl Ladepunkte"]].strip()
    declared = int(declared_raw) if declared_raw else None
    nominal = None
    nominal_raw = row[col["Nennleistung Ladeeinrichtung [kW]"]]
    try:
        nominal = parse_german_number(nominal_raw)
        if nominal is not None and nominal < 0:
            nominal = None
    except Exception:
        nominal = None
    points, tokens = [], 0
    for slot in range(1, MAX_POINT_GROUPS + 1):
        cells = [row[col[f"{k}{slot}"]] for k in ("Steckertypen", "Nennleistung Stecker", "EVSE-ID", "Public Key")]
        if any(c.strip() for c in cells):
            kw, n_conn = parse_point_slot(cells[0], cells[1])
            points.append(kw)
            tokens += n_conn
    reconciles = declared is not None and 1 <= declared <= MAX_POINT_GROUPS and declared == len(points)
    date = row[col["Inbetriebnahmedatum"]].strip()
    match = re.fullmatch(r"\d\d\.\d\d\.(\d{4})", date)
    return {
        "id": iid,
        "state": row[col["Bundesland"]],
        "label": row[col["Kreis/kreisfreie Stadt"]],
        "operator": row[col["Betreiber"]],
        "declared": declared,
        "reconciles": reconciles,
        "nominal": nominal,
        "points": points,           # per parsed slot: point max kW or None; one slot == one point
        "connectorTokens": tokens,  # informational only; never counted as points
        "year": int(match.group(1)) if match else None,
        "coord": (row[col["Breitengrad"]], row[col["Längengrad"]]),
        "flagged": (row[col["Breitengrad"]], row[col["Längengrad"]]) == TESLA_CLUSTER_RAW,
    }


# ---------------------------------------------------------------- BKG VG250-EW

def load_vg250(zip_path: Path):
    with zipfile.ZipFile(zip_path) as archive:
        if archive.read(AKTUALITAET_MEMBER).decode("ascii", "replace").strip() != "31.12.2025":
            raise GateFail("VG250 aktualitaet is not 31.12.2025")
        gpkg = archive.read(GPKG_MEMBER)
    con = sqlite3.connect(":memory:")
    con.deserialize(gpkg)
    cols = "ARS, GEN, BEZ, IBZ, EWZ, KFL, SN_L"
    srs = {r[0] for r in con.execute("select srs_id from gpkg_contents where table_name in ('vg250_krs','vg250_lan','vg250_sta')")}
    if srs != {25832}:
        raise GateFail(f"unexpected VG250 SRS {srs}")
    kreise = [dict(zip(("ars", "name", "bez", "ibz", "pop", "kfl", "sn_l"), r))
              for r in con.execute(f"select {cols} from vg250_krs where GF=4 order by ARS")]
    laender = [dict(zip(("ars", "name", "bez", "ibz", "pop", "kfl", "sn_l"), r))
               for r in con.execute(f"select {cols} from vg250_lan where GF=4 order by ARS")]
    sta = list(con.execute("select EWZ, KFL from vg250_sta where GF=4"))
    con.close()
    if len(kreise) != 400 or len({k["ars"] for k in kreise}) != 400 or any(len(k["ars"]) != 5 for k in kreise):
        raise GateFail("expected 400 unique 5-digit GF=4 Kreis codes")
    if len(laender) != 16 or len({s["ars"][:2] for s in laender}) != 16:
        raise GateFail("expected 16 unique GF=4 Land rows")
    if len(sta) != 1:
        raise GateFail("expected one GF=4 national row")
    for k in kreise:
        k["state"] = k["ars"][:2]
        k["kfl"] = Decimal(str(k["kfl"])).quantize(Decimal("0.01"))
    for s in laender:
        s["state"] = s["ars"][:2]
        s["kfl"] = Decimal(str(s["kfl"])).quantize(Decimal("0.01"))
    return kreise, laender, {"pop": sta[0][0], "kfl": Decimal(str(sta[0][1])).quantize(Decimal("0.01"))}


def reconcile_denominators(kreise, laender, national) -> dict:
    """Official same-vintage conservation: Kreise -> Laender -> Germany. Population must be exact."""
    by_state = collections.defaultdict(lambda: {"pop": 0, "kfl": Decimal(0), "n": 0})
    for k in kreise:
        by_state[k["state"]]["pop"] += k["pop"]
        by_state[k["state"]]["kfl"] += k["kfl"]
        by_state[k["state"]]["n"] += 1
    area_gaps = {}
    for s in laender:
        agg = by_state[s["state"]]
        if agg["pop"] != s["pop"]:
            raise GateFail(f"population: Kreise sum {agg['pop']} != Land {s['state']} {s['pop']}")
        if agg["kfl"] != s["kfl"]:
            area_gaps[s["state"]] = float(s["kfl"] - agg["kfl"])
    if sum(s["pop"] for s in laender) != national["pop"]:
        raise GateFail("population: Laender sum != Germany")
    if sum(k["pop"] for k in kreise) != national["pop"]:
        raise GateFail("population: Kreise sum != Germany")
    return {"districts": len(kreise), "states": len(laender), "population": national["pop"],
            "populationConserved": True, "areaGapKm2LandMinusKreiseSum": area_gaps,
            "areaKm2": float(national["kfl"])}


# ---------------------------------------------------------------- label mapping

def build_label_map(kreise, records, state_codes):
    """Source label -> district. Exact 'BEZ GEN' first; else a spacing/punctuation-only alias
    that is unique within the same BEZ and the same Bundesland. Everything else stays unmapped."""
    exact = {f"{k['bez']} {k['name']}": k for k in kreise}
    if len(exact) != len(kreise):
        raise GateFail("BEZ+GEN key is not unique")
    labels = collections.defaultdict(set)
    for r in records:
        labels[r["label"]].add(r["state"])
    mapping, aliases, unmapped = {}, [], []
    for label in sorted(labels):
        if label in exact:
            mapping[label] = (exact[label]["ars"], "exact")
            continue
        candidates = []
        for bez in {k["bez"] for k in kreise}:
            if label.startswith(bez + " "):
                gen_norm = normalize_label_name(label[len(bez) + 1:])
                candidates += [k for k in kreise if k["bez"] == bez and normalize_label_name(k["name"]) == gen_norm]
        same_state = [k for k in candidates if all(state_codes.get(s) == k["state"] for s in labels[label])]
        if len(same_state) == 1:
            k = same_state[0]
            mapping[label] = (k["ars"], "spacing_alias")
            aliases.append({"sourceLabel": label, "vg250Name": f"{k['bez']} {k['name']}", "code": k["ars"]})
        else:
            unmapped.append(label)
    return mapping, aliases, unmapped


# ---------------------------------------------------------------- aggregation

def aggregate(recs) -> dict:
    """Aggregate installations once each. Missing power stays missing: it is counted, never zero."""
    out = {"inst": 0, "pts": 0, "ptsQuarantined": 0, "kwDec": None, "kwKnownInst": 0, "kwMissingInst": 0,
           "ptsPowerUnknown": 0, "classes": collections.Counter(), "tokens": 0}
    for r in recs:
        out["inst"] += 1
        if r["reconciles"]:
            out["pts"] += r["declared"]
        else:
            out["ptsQuarantined"] += r["declared"] or 0
        if r["nominal"] is None:
            out["kwMissingInst"] += 1
        else:
            out["kwKnownInst"] += 1
            out["kwDec"] = (out["kwDec"] or Decimal(0)) + r["nominal"]
        if r["reconciles"]:
            out["tokens"] += r["connectorTokens"]
            for kw in r["points"]:
                if kw is None:
                    out["ptsPowerUnknown"] += 1
                else:
                    out["classes"][power_class(kw)] += 1
    return out


def row_metrics(agg: dict, pop: int | None, area: Decimal | None) -> dict:
    kw = agg["kwDec"]
    grouped = collections.Counter()
    for cls, n in agg["classes"].items():
        grouped[GROUP_OF_CLASS[cls]] += n
    known_pts = sum(agg["classes"].values())
    return {
        "installations": agg["inst"],
        "points": agg["pts"],
        "nominalKw": None if kw is None else float(kw),
        "nominalMw": None if kw is None else float(kw / 1000),
        "nominalKwMissingInstallations": agg["kwMissingInst"],
        "nominalKwCoverage": None if not agg["inst"] else agg["kwKnownInst"] / agg["inst"],
        "pointsPowerUnknown": agg["ptsPowerUnknown"],
        "pointPowerCoverage": None if not agg["pts"] else known_pts / agg["pts"],
        "pointsQuarantinedGroupMismatch": agg["ptsQuarantined"],
        "pointsByPower": {g: grouped[g] for g in GROUPS},
        "population": pop,
        "areaKm2": None if area is None else float(area),
        "pointsPer10kResidents": rate(agg["pts"], pop, 10000),
        "nominalKwPer1000Residents": None if kw is None or not pop else float(kw) * 1000 / pop,
        "pointsPer100Km2": rate(agg["pts"], area, 100),
        "pointsPerInstallation": None if not agg["inst"] else agg["pts"] / agg["inst"],
        "nominalKwPerInstallation": None if kw is None or not agg["kwKnownInst"] else float(kw) / agg["kwKnownInst"],
        "highPowerPointShare": None if not known_pts else (known_pts - grouped["le22"]) / known_pts,
        "_knownPoints": known_pts,
    }


def spatial_outcome(rec_ars, ledger_row) -> str:
    """Compare our source-label district with the pinned coordinate-derived candidate."""
    n = int(ledger_row["spatial_candidate_count"] or 0)
    if n > 1:
        return "noMatch"
    spatial = ledger_row["spatial_ars"]
    if not spatial:
        return "noMatch"
    return "agree" if spatial == rec_ars else "conflict"


def top_group(recs):
    """Largest same-coordinate, same-operator group by points (pipeline.concentration_diagnostics rule)."""
    groups = collections.defaultdict(lambda: [0, 0, set()])
    for r in recs:
        if not r["reconciles"]:
            continue
        g = groups[(r["coord"], r["operator"])]
        g[0] += r["declared"]
        g[1] += 1
    if not groups:
        return 0, 0
    key = max(groups, key=lambda k: (groups[k][0], groups[k][1], [-ord(c) for c in k[1]]))
    return groups[key][0], groups[key][1]


# ---------------------------------------------------------------- statistics workbook (context only)

def read_stats_context(path: Path, state_codes: dict) -> dict:
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
          "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
    with zipfile.ZipFile(path) as z:
        workbook = ET.fromstring(z.read("xl/workbook.xml"))
        rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        strings = ["".join(t.text or "" for t in si.iter(f"{{{ns['m']}}}t"))
                   for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", ns)]
        sheets = {s.get("name"): rels[s.get(f"{{{ns['r']}}}id")] for s in workbook.find("m:sheets", ns)}

        def grid(name):
            rows = []
            for row in ET.fromstring(z.read("xl/" + sheets[name])).iter(f"{{{ns['m']}}}row"):
                cells = {}
                for c in row.findall("m:c", ns):
                    v = c.find("m:v", ns)
                    if v is not None:
                        cells[re.sub(r"\d", "", c.get("r"))] = strings[int(v.text)] if c.get("t") == "s" else v.text
                rows.append(cells)
            return rows

        deu_name = next(n for n in sheets if n.startswith("2. ") and n.endswith("DEU"))
        bl_name = next(n for n in sheets if n.startswith("2. ") and n.endswith("BL"))
        deu, bl = grid(deu_name), grid(bl_name)
    context = {"populationDifferenceNote": "Statistics workbook also counts notification procedures not yet complete; "
               "it is a different population from the register CSV and is never combined with it."}
    for i, cells in enumerate(deu):
        label = cells.get("F")
        nxt = deu[i + 1] if i + 1 < len(deu) else {}
        if label == "Anzahl Ladeeinrichtungen":
            context["installations"] = int(nxt["H"])
        elif label == "Ladeleistung* in kW":
            context["nominalKw"] = round(float(nxt["H"]), 1)
        elif label == "Insgesamt":
            context["points"] = int(cells["H"])
        elif label in STATS_CLASS_LABELS:
            context.setdefault("pointsByClass", {})[STATS_CLASS_LABELS[label]] = int(cells["H"])
    states = {}
    block = 0  # first state block = points (J total), second = kW (I)
    seen = set()
    for cells in bl:
        name = cells.get("F")
        if name in state_codes:
            if name in seen:
                block, seen = 1, set()
            seen.add(name)
            code = state_codes[name]
            entry = states.setdefault(code, {})
            if block == 0:
                entry["points"] = int(cells["J"])
            else:
                entry["nominalKw"] = round(float(cells["I"]), 1)
    context["states"] = states
    if len(states) != 16 or any(len(v) != 2 for v in states.values()):
        raise GateFail("statistics workbook state tables not fully parsed")
    return context


# ---------------------------------------------------------------- build

def build(raw_dir: Path, bundle_dir: Path) -> dict:
    sources = verify_inputs(raw_dir, bundle_dir)
    preamble, records = read_register(raw_dir / "reg_0901.csv")
    kreise, laender, national_geo = load_vg250(raw_dir / "vg250ew.zip")
    denominators = reconcile_denominators(kreise, laender, national_geo)
    state_codes = {s["name"]: s["state"] for s in laender}
    unknown_states = {r["state"] for r in records} - set(state_codes)
    if unknown_states:
        raise GateFail(f"Bundesland values without VG250 Land: {sorted(unknown_states)}")
    label_map, aliases, unmapped_labels = build_label_map(kreise, records, state_codes)

    # coordinate-derived candidates from the pinned bundle; used only as a diagnostic
    with (bundle_dir / "assignment_ledger.csv").open(encoding="utf-8", newline="") as handle:
        ledger = {row["installation_id"]: row for row in csv.DictReader(handle)}
    if set(ledger) != {r["id"] for r in records}:
        raise GateFail("pinned assignment ledger ids differ from the register")

    for r in records:
        r["stateCode"] = state_codes[r["state"]]
        mapped = label_map.get(r["label"])
        r["district"] = mapped[0] if mapped and mapped[0][:2] == r["stateCode"] else None
        r["mapHow"] = mapped[1] if r["district"] else None
        led = ledger[r["id"]]
        r["spatial"] = spatial_outcome(r["district"], led) if r["district"] else None
        r["ledgerSpatialArs"] = led["spatial_ars"]

    by_state, by_district = collections.defaultdict(list), collections.defaultdict(list)
    unattributed = collections.defaultdict(list)
    for r in records:
        by_state[r["stateCode"]].append(r)
        if r["district"]:
            by_district[r["district"]].append(r)
        else:
            unattributed[(r["stateCode"], r["label"])].append(r)

    kreis_by_ars = {k["ars"]: k for k in kreise}
    land_by_code = {s["state"]: s for s in laender}

    germany = aggregate(records)
    # --- pinned regression targets and conservation (hard gates)
    expect = PINNED_TOTALS["germany"]
    if (germany["inst"], germany["pts"], germany["kwDec"]) != expect:
        raise GateFail(f"national totals {germany['inst'], germany['pts'], germany['kwDec']} != pinned {expect}")
    for code in ("12", "11"):
        a = aggregate(by_state[code])
        if (a["inst"], a["pts"], a["kwDec"]) != PINNED_TOTALS[code]:
            raise GateFail(f"state {code} totals differ from pinned snapshot")
    state_aggs = {code: aggregate(recs) for code, recs in by_state.items()}
    for key in ("inst", "pts", "ptsQuarantined", "kwKnownInst", "kwMissingInst", "ptsPowerUnknown", "tokens"):
        if sum(a[key] for a in state_aggs.values()) != germany[key]:
            raise GateFail(f"states do not sum to national for {key}")
    if sum((a["kwDec"] or Decimal(0)) for a in state_aggs.values()) != germany["kwDec"]:
        raise GateFail("states do not sum to national nominal kW")

    # --- districts
    district_rows, top_stats = {}, {}
    for code in sorted(kreis_by_ars):
        k = kreis_by_ars[code]
        recs = by_district.get(code, [])
        row = {"code": code, "name": k["name"], "type": k["bez"],
               "kind": "city" if k["ibz"] in (40, 41) else "county", "state": k["state"]}
        row.update(row_metrics(aggregate(recs), k["pop"], k["kfl"]))
        spatial = collections.Counter(r["spatial"] for r in recs)
        agree_pts = sum(r["declared"] for r in recs if r["spatial"] == "agree" and r["reconciles"])
        row["geo"] = {"agree": spatial["agree"], "conflict": spatial["conflict"], "noMatch": spatial["noMatch"],
                      "pointsAgree": agree_pts,
                      "agreeShare": None if not recs else spatial["agree"] / len(recs)}
        tg_pts, tg_inst = top_group(recs)
        row["topGroup"] = {"points": tg_pts, "installations": tg_inst,
                           "pointShare": None if not row["points"] else tg_pts / row["points"]}
        # symmetric sensitivity: every district loses its own largest co-located group
        row["pointsWithoutTopGroup"] = row["points"] - tg_pts
        row["pointsPer10kWithoutTopGroup"] = rate(row["points"] - tg_pts, k["pop"], 10000)
        district_rows[code] = row
    for field, key in (("pointsPer10kResidents", "rankGermany"), ("pointsPer10kWithoutTopGroup", "rankWithoutTopGroup")):
        for c, v in competition_ranks({c: r[field] for c, r in district_rows.items()}).items():
            district_rows[c][key] = v
    # presentation flags: thresholds are display choices, not scientific cut-offs (see meta.flagRules)
    for row in district_rows.values():
        flags = []
        if row["geo"]["agreeShare"] is not None and row["geo"]["agreeShare"] < FLAG_AGREE_BELOW:
            flags.append("lowLabelCoordinateAgreement")
        if row["topGroup"]["pointShare"] is not None and row["topGroup"]["pointShare"] >= FLAG_TOPGROUP_SHARE:
            flags.append("concentratedCoLocation")
        if row["points"] < FLAG_SMALL_POINTS:
            flags.append("smallPointCount")
        row["flags"] = flags
    # coordinate candidates of installations whose source label is not a VG250 Kreis: a disclosed gap,
    # never added to any district total
    for r in records:
        if not r["district"] and r["ledgerSpatialArs"] in district_rows:
            gap = district_rows[r["ledgerSpatialArs"]].setdefault("labelGap", {"installations": 0, "points": 0})
            gap["installations"] += 1
            gap["points"] += r["declared"] if r["reconciles"] else 0
            if "labelGap" not in district_rows[r["ledgerSpatialArs"]]["flags"]:
                district_rows[r["ledgerSpatialArs"]]["flags"].append("labelGap")

    # --- states
    state_rows = {}
    for code in sorted(land_by_code):
        s = land_by_code[code]
        recs = by_state[code]
        row = {"code": code, "name": s["name"]}
        row.update(row_metrics(state_aggs[code], s["pop"], s["kfl"]))
        attributed = [r for r in recs if r["district"]]
        spatial = collections.Counter(r["spatial"] for r in attributed)
        row["districts"] = sum(1 for k in kreise if k["state"] == code)
        row["districtAttributedInstallations"] = len(attributed)
        row["districtUnattributedInstallations"] = len(recs) - len(attributed)
        row["districtUnattributedPoints"] = sum(r["declared"] for r in recs if not r["district"] and r["reconciles"])
        row["geo"] = {"agree": spatial["agree"], "conflict": spatial["conflict"], "noMatch": spatial["noMatch"],
                      "agreeShare": None if not attributed else spatial["agree"] / len(attributed)}
        rates = [district_rows[k["ars"]]["pointsPer10kResidents"] for k in kreise if k["state"] == code]
        rates = [v for v in rates if v is not None]
        row["districtRate"] = None if not rates else {
            "n": len(rates), "min": min(rates), "median": statistics.median(rates), "max": max(rates)}
        context = None
        state_rows[code] = row
    for key, field in (("rank", "pointsPer10kResidents"),):
        ranks = competition_ranks({c: r[field] for c, r in state_rows.items()})
        for c, v in ranks.items():
            state_rows[c][key] = v

    # --- conservation: districts + unattributed == state, state by state
    for code, row in state_rows.items():
        d_inst = sum(district_rows[k["ars"]]["installations"] for k in kreise if k["state"] == code)
        d_pts = sum(district_rows[k["ars"]]["points"] for k in kreise if k["state"] == code)
        u = [r for (sc, _), recs in unattributed.items() if sc == code for r in recs]
        if d_inst + len(u) != row["installations"]:
            raise GateFail(f"state {code}: districts + unattributed installations != state")
        if d_pts + sum(r["declared"] for r in u if r["reconciles"]) != row["points"]:
            raise GateFail(f"state {code}: districts + unattributed points != state")

    unattributed_rows = []
    for (sc, label), recs in sorted(unattributed.items()):
        a = aggregate(recs)
        spatial_ars = collections.Counter(r["ledgerSpatialArs"] or "none" for r in recs)
        unattributed_rows.append({
            "state": sc, "sourceLabel": label, "reason": "label_not_in_vg250_kreis_list",
            "installations": a["inst"], "points": a["pts"],
            "nominalKw": None if a["kwDec"] is None else float(a["kwDec"]),
            "coordinateCandidateDistricts": dict(sorted(spatial_ars.items())),
        })

    # --- national block
    point_class_national = {name: germany["classes"].get(name, 0) for name, _ in CLASS_EDGES}
    ppi = collections.Counter(r["declared"] for r in records if r["reconciles"])
    commission = collections.defaultdict(lambda: [0, 0, Decimal(0)])
    undated = [0, 0, Decimal(0)]
    for r in records:
        slot = commission[r["year"]] if r["year"] else undated
        slot[0] += 1
        slot[1] += r["declared"] if r["reconciles"] else 0
        slot[2] += r["nominal"] or Decimal(0)
    district_rates = [r["pointsPer10kResidents"] for r in district_rows.values() if r["pointsPer10kResidents"] is not None]
    cities = [r["pointsPer10kResidents"] for r in district_rows.values() if r["kind"] == "city"]
    counties = [r["pointsPer10kResidents"] for r in district_rows.values() if r["kind"] == "county"]
    germany_row = row_metrics(germany, national_geo["pop"], national_geo["kfl"])
    germany_row.update({
        "pointsByClassBnetza": point_class_national,
        "connectorTokens": germany["tokens"],
        "installationsByPointCount": {str(n): ppi.get(n, 0) for n in range(1, MAX_POINT_GROUPS + 1)},
        "districtRateSpread": {"all": quartile_summary(district_rates), "city": quartile_summary(cities),
                               "county": quartile_summary(counties)},
        "listedByCommissioningYear": [
            {"year": y, "installations": v[0], "points": v[1], "nominalKw": float(v[2])}
            for y, v in sorted(commission.items())],
        "commissioningDateMissingInstallations": undated[0],
        "byAdministrativeType": {
            kind: {"districts": sum(1 for d in district_rows.values() if d["kind"] == kind),
                   "population": sum(d["population"] for d in district_rows.values() if d["kind"] == kind),
                   "points": sum(d["points"] for d in district_rows.values() if d["kind"] == kind),
                   "pointsPer10kResidents": rate(
                       sum(d["points"] for d in district_rows.values() if d["kind"] == kind),
                       sum(d["population"] for d in district_rows.values() if d["kind"] == kind), 10000)}
            for kind in ("city", "county")},
        "unattributedPointsExcludedFromTypeRates": sum(u["points"] for u in unattributed_rows),
    })
    for key in [k for k in germany_row if k.startswith("_")]:
        del germany_row[key]
    for table in (state_rows, district_rows):
        for row in table.values():
            row.pop("_knownPoints", None)

    # --- Brandenburg / Berlin: separate registered and hypothetical, same shape as the live site
    def scenario(recs, code, excluded):
        sel = [r for r in recs if not (excluded and r["flagged"])]
        a = aggregate(sel)
        pop = kreis_by_ars[code]["pop"]
        return {"points": a["pts"], "population": pop, "rate": rate(a["pts"], pop, 10000),
                "kw": None if a["kwDec"] is None else float(a["kwDec"]), "installations": a["inst"]}

    bb = []
    for code in BB_DISTRICTS:
        recs = by_district[code]
        bb.append({"code": code, "name": kreis_by_ars[code]["name"],
                   "hypothetical": scenario(recs, code, True), "registered": scenario(recs, code, False)})
    for scen in ("registered", "hypothetical"):
        for c, v in competition_ranks({d["code"]: d[scen]["rate"] for d in bb}).items():
            next(d for d in bb if d["code"] == c)[scen]["rank"] = v
    berlin_recs = by_district[BERLIN]
    flagged = [r for r in records if r["flagged"]]
    brandenburg = {
        "districts": bb,
        "totals": {s: {"installations": sum(d[s]["installations"] for d in bb),
                       "points": sum(d[s]["points"] for d in bb),
                       "kw": sum(d[s]["kw"] for d in bb),
                       "population": sum(d[s]["population"] for d in bb),
                       "rate": 10000 * sum(d[s]["points"] for d in bb) / sum(d[s]["population"] for d in bb)}
                   for s in ("registered", "hypothetical")},
        "hypotheticalRule": "Removes only installations whose raw coordinate pair equals the pinned flagged "
                            "Grünheide group (513 single-point installations, all labelled Oder-Spree). "
                            "A sensitivity test, not a correction and not a claim about public access.",
        "flaggedGroup": {"installations": len(flagged), "points": sum(r["declared"] for r in flagged),
                         "nominalKw": float(sum(r["nominal"] for r in flagged)),
                         "districts": sorted({r["district"] for r in flagged})},
    }
    berlin = {"code": BERLIN, "name": "Berlin", "role": "context only; never ranked with Brandenburg",
              "registered": scenario(berlin_recs, BERLIN, False)}
    ba = aggregate(berlin_recs)
    berlin["registered"]["nominalKwMissingInstallations"] = ba["kwMissingInst"]

    stats_context = read_stats_context(raw_dir / "stats.xlsx", state_codes)
    for (code, entry) in stats_context["states"].items():
        if state_rows[code]["points"] > entry["points"]:
            raise GateFail(f"register points exceed statistics workbook for state {code}; unexplained")

    meta = build_meta(sources, preamble, records, germany, denominators, label_map, aliases, unmapped_labels,
                      unattributed_rows, stats_context, ledger)
    payload = {
        "meta": meta,
        "germany": germany_row,
        "states": list(state_rows.values()),
        "districts": list(district_rows.values()),
        "unattributedLabels": unattributed_rows,
        "brandenburg": brandenburg,
        "berlin": berlin,
        "statisticsContext": stats_context,
    }
    return payload


def build_meta(sources, preamble, records, germany, denominators, label_map, aliases, unmapped_labels,
               unattributed_rows, stats_context, ledger) -> dict:
    outcomes = collections.Counter(row["assignment_outcome"] for row in ledger.values())
    return {
        "schema": SCHEMA,
        "generator": GENERATOR,
        "status": "DIAGNOSTIC_PILOT",
        "validatedReleaseEligible": False,
        "scope": "Germany, all 16 Bundesländer and 400 Kreise/kreisfreie Städte, aggregates only. "
                 "Register scope is Bundesnetzagentur's list of completed notification procedures, which is "
                 "smaller than the publicly accessible infrastructure.",
        "charging": {
            "snapshotDate": CHARGING_DATE,
            "source": "Bundesnetzagentur Ladesäulenregister, CSV list of 1 September 2026",
            "licence": sources["reg_0901.csv"]["licence"], "attribution": sources["reg_0901.csv"]["attribution"],
            "sha256": sources["reg_0901.csv"]["sha256"], "url": sources["reg_0901.csv"]["url"],
            "csv": {"encoding": "UTF-8 with BOM", "separator": ";", "preambleLines": len(preamble), "fields": 47,
                    "records": len(records), "decimalSeparator": ","},
        },
        "population": {
            "referenceDate": POPULATION_DATE, "boundaryVintage": POPULATION_DATE,
            "source": "BKG VG250-EW (layers vg250_krs / vg250_lan / vg250_sta, GF=4), fields EWZ and KFL",
            "licence": sources["vg250ew.zip"]["licence"], "attribution": sources["vg250ew.zip"]["attribution"],
            "sha256": sources["vg250ew.zip"]["sha256"], "url": sources["vg250ew.zip"]["url"],
            "note": "Population (31 Dec 2025) and charging register (1 Sep 2026) are different dates and are not "
                    "a time series. One denominator per Kreis; Land and Germany values are the official rows and "
                    "were verified to equal the sums of their Kreise exactly.",
            "reconciliation": denominators,
        },
        "context": {"statistics": {"sha256": sources["stats.xlsx"]["sha256"], "referenceDate": CHARGING_DATE,
                                    "licence": sources["stats.xlsx"]["licence"]}},
        "pinnedBundle": {"sha256": sources["bundle"]["id"], "use": "coordinate-derived Kreis candidates (assignment "
                         "ledger) as a disclosed diagnostic only; WGS84 is a provisional, unverified assumption",
                         "ledgerOutcomesNational": dict(sorted(outcomes.items()))},
        "units": {
            "points": "charging points, one per source point group (a point supports one vehicle at a time)",
            "installations": "register records (Ladeeinrichtung); not unique physical sites",
            "nominalKw": "sum of Nennleistung Ladeeinrichtung, counted once per installation; kW",
            "nominalMw": "nominalKw / 1000",
            "pointsPer10kResidents": "points / population x 10,000",
            "nominalKwPer1000Residents": "nominalKw / population x 1,000",
            "pointsPer100Km2": "points / cadastral area (KFL, includes inland water) x 100",
            "pointsPerInstallation": "ratio of sums, never a mean of ratios",
            "highPointPowerShare": "points above 22 kW / points with known power",
            "areaKm2": "VG250-EW cadastral area (KFL) rounded to 0.01 km2; includes inland water",
        },
        "definitions": {
            "installationVsPoint": "A point count is the declared Anzahl Ladepunkte, reconciled to the number of "
                                   "filled point groups. Connector tokens inside a group are not additional points.",
            "nominalCapacity": "Installation nominal power is never multiplied by points or connectors. It is "
                               "reported capacity, not delivered energy, availability or utilization.",
            "missingness": "Missing power stays missing (null) and is counted. nominalKwCoverage is the share of "
                           "installations with a nominal power; pointPowerCoverage the share of points with a known "
                           "power. In this snapshot both are 1.0 (nothing is missing, so nothing was imputed).",
            "pointPowerClasses": "Point maximum kW. Four groups: le22 (<=22), gt22to149, gt149to299, gt299. "
                                 "Edges follow Bundesnetzagentur's published classes. A point with several "
                                 "connectors uses its highest connector kW.",
            "districtAttribution": "Source label 'Kreis/kreisfreie Stadt' joined to VG250 'BEZ GEN'; "
                                   "8 labels differ only in spacing/punctuation and are mapped by a unique "
                                   "same-type same-Bundesland normalised match. Unmatched labels are listed in "
                                   "unattributedLabels, never dropped or reassigned.",
            "stateAttribution": "Source column Bundesland, matched exactly to VG250 Land names.",
            "geo": "Diagnostic only: whether the pinned coordinate-derived Kreis (provisional WGS84) agrees with "
                   "the source label. agreeShare is not accuracy; a label is not corrected by a coordinate.",
            "topGroup": "Largest group of installations sharing the same raw coordinate pair and operator, within "
                        "a district. A co-location diagnostic, not a physical site and not a private-access claim. "
                        "*WithoutTopGroup fields remove each district's own largest group (a symmetric sensitivity, "
                        "not a correction).",
            "labelGap": "Installations whose source label is not a VG250 Kreis but whose coordinate falls in this "
                        "district (provisional WGS84). Not added to the district's totals.",
            "commissioningYear": "Year of Inbetriebnahmedatum for installations listed in this snapshot; it is not "
                                 "a historical network or an opening/closing series. 2026 covers 1 Jan to 1 Sep only.",
            "rank": "Competition ranking, descending rate; ties share a position; missing rates unranked.",
            "quartiles": "Type-7 (statistics.quantiles inclusive); whiskers are observed values within 1.5 IQR.",
        },
        "labelMapping": {"spacingAliases": aliases, "unmappedLabels": unmapped_labels,
                         "exactLabels": sum(1 for _, how in label_map.values() if how == "exact"),
                         "labelsTotal": len(label_map) + len(unmapped_labels)},
        "geographicLimits": [
            "State figures use the source Bundesland column; district figures use source Kreis labels.",
            "District rankings are source-label rankings, not spatially validated; coordinate agreement is shown "
            "per district and is itself conditional on an unverified WGS84 assumption.",
            "Rates compare registered supply with residents. They are not demand, adequacy, ROI or placement advice.",
            "City-states (Berlin, Hamburg) and small independent cities have no hinterland, so their rates are not "
            "like-for-like with large counties; this is administrative type, not a rural/urban classification.",
        ],
        "flagRules": {
            "note": "Display thresholds for per-district caution flags. Presentation choices, not scientific cut-offs.",
            "lowLabelCoordinateAgreement": f"geo.agreeShare < {FLAG_AGREE_BELOW}",
            "concentratedCoLocation": f"topGroup.pointShare >= {FLAG_TOPGROUP_SHARE}",
            "smallPointCount": f"points < {FLAG_SMALL_POINTS}",
            "labelGap": "installations with an unmatched source label have coordinates in this district",
        },
        "openGates": ["coordinate_crs_provisional_wgs84", "unresolved_geographic_assignments",
                      "material_cluster_access_unverified"],
        "unattributedInstallations": sum(r["installations"] for r in unattributed_rows),
        "unattributedPoints": sum(r["points"] for r in unattributed_rows),
        "source": {"files": {k: v["sha256"] for k, v in sources.items() if k != "bundle"}},
    }


def to_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n"


def write_outputs(payload: dict, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    text = to_json(payload)
    (out_dir / "national-story.json").write_text(text, encoding="utf-8", newline="\n")
    (out_dir / "national-story-data.js").write_text(
        "window.NATIONAL_STORY=" + text.rstrip("\n") + ";\n", encoding="utf-8", newline="\n")
    return {name: sha256_file(out_dir / name) for name in ("national-story.json", "national-story-data.js")}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw", type=Path, default=ROOT / "data" / "raw")
    parser.add_argument("--bundle", type=Path, default=ROOT / "data" / "work" / "pilot" / "runs" / PINNED_BUNDLE)
    parser.add_argument("--out", type=Path, default=HERE)
    args = parser.parse_args(argv)
    try:
        payload = build(args.raw, args.bundle)
    except GateFail as exc:
        print(f"GATE FAIL: {exc}", file=sys.stderr)
        return 2
    hashes = write_outputs(payload, args.out)
    for name, digest in hashes.items():
        print(f"{digest}  {name}  ({(args.out / name).stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
