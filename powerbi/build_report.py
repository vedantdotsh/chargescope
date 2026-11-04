"""Generate the native Power BI project from a pinned complete bundle."""
import argparse
import csv
import json
import math
import shutil
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "powerbi/portfolio-final"
RUN = "f92f3ed285d0a0d4eef184bafa823c0567215ca8d5aec0ec6751e24bd3b678d0"
BUNDLE = ROOT / "data/work/pilot/runs" / RUN
SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def literal(value):
    value = str(value).lower() if isinstance(value, bool) else "'" + value.replace("'", "''") + "'" if isinstance(value, str) else str(value) + "D"
    return {"expr": {"Literal": {"Value": value}}}


def fmt(**values):
    return [{"properties": {key: literal(value) for key, value in values.items()}}]


def field(table, name, measure=False):
    return {"Measure" if measure else "Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def projection(table, name, measure=False, label=None):
    return {"field": field(table, name, measure), "queryRef": table + "." + name, "displayName": label or name}


def category_filter(table, column, values, name):
    return {"name": name, "field": field(table, column), "type": "Categorical", "filter": {
        "Version": 2, "From": [{"Name": "f", "Entity": table, "Type": 0}],
        "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "f"}}, "Property": column}}],
        "Values": [[literal(value)["expr"]] for value in values]}}}]}}


def make_model():
    model = {"culture": "en-US", "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "dataAccessOptions": {"legacyRedirects": False, "returnErrorValuesAsNull": False}, "tables": [], "relationships": [],
        "annotations": [{"name": "__PBI_TimeIntelligenceEnabled", "value": "0"}],
        "expressions": [{"name": "BundlePath", "kind": "m", "expression": '"' + str(BUNDLE) + '" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'}]}
    specs = json.loads((BUNDLE / "bi_model.json").read_text(encoding="utf-8"))["tables"]
    integers = {"population", "source_slot", "declared_point_count", "n_connector_tokens", "installations", "districts", "unknown_point_installations", "nominal_kw_missing_n", "unresolved_installations", "brandenburg_rank"}
    decimals = {"nominal_kw", "point_kw", "cadastral_area_km2", "known_points", "points", "agreed_known_points", "points_per_10000_residents"}
    dates = {"boundary_vintage", "population_date", "reference_date"}
    booleans = {"groups_reconcile", "is_tesla_cluster"}
    for table in ["bi_district", "bi_scenario", "bi_district_scenario", "bi_installation", "bi_point", "bi_region_scenario", "source_snapshot"]:
        with (BUNDLE / (table + ".csv")).open(encoding="utf-8", newline="") as source:
            reader = csv.reader(source)
            names = next(reader)
            rows = list(reader)
        if table in specs:
            assert len(rows) == specs[table]["rows"]
        columns, transforms = [], []
        for name in names:
            dtype, mtype = ("int64", "Int64.Type") if name in integers else ("double", "type number") if name in decimals else ("dateTime", "type date") if name in dates else ("boolean", "type logical") if name in booleans else ("string", "type text")
            column = {"name": name, "dataType": dtype, "sourceColumn": name, "summarizeBy": "none", "isHidden": table in {"bi_district_scenario", "bi_region_scenario", "source_snapshot"} or name in integers | decimals | booleans}
            if name in dates:
                column["formatString"] = "yyyy-MM-dd"
            columns.append(column)
            conversion = '(value) => value'
            if name in dates:
                conversion = '(value) => if value = null then null else Date.FromText(value, [Format="yyyy-MM-dd", Culture="en-US"])'
            elif name in booleans:
                conversion = '(value) => if value = null then null else Logical.FromText(Text.Lower(value))'
            elif name in integers | decimals:
                conversion = '(value) => if value = null then null else Number.FromText(value, "en-US")'
            transforms.append('{"' + name + '", ' + conversion + ', ' + mtype + '}')
        expression = ["let", '    Source = Csv.Document(File.Contents(BundlePath & "\\' + table + '.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
            "    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
            '    Nulls = Table.ReplaceValue(Headers, "", null, Replacer.ReplaceValue, Table.ColumnNames(Headers)),',
            "    Typed = Table.TransformColumns(Nulls, {" + ", ".join(transforms) + "})", "in", "    Typed"]
        model["tables"].append({"name": table, "columns": columns, "isHidden": table in {"bi_region_scenario", "source_snapshot"},
            "partitions": [{"name": table, "mode": "import", "source": {"type": "m", "expression": expression}}]})
    for index, (many, key, one) in enumerate([("bi_district_scenario", "district_code", "bi_district"), ("bi_district_scenario", "scenario_id", "bi_scenario"), ("bi_installation", "district_code", "bi_district"), ("bi_point", "installation_id", "bi_installation")]):
        model["relationships"].append({"name": f"relationship_{index}", "fromTable": many, "fromColumn": key, "toTable": one, "toColumn": key, "fromCardinality": "many", "toCardinality": "one", "crossFilteringBehavior": "oneDirection", "isActive": True})
    # Disconnected district selector (no relationship): the synced slicer drives colours and the selected-district
    # cards only, so every chart keeps the full fixed cohort and all totals stay unfiltered.
    model["tables"].append({"name": "District selector", "columns": [
        {"name": "District", "dataType": "string", "sourceColumn": "[District]", "type": "calculatedTableColumn", "isNameInferred": True, "isDataTypeInferred": True, "summarizeBy": "none"},
        {"name": "district_code", "dataType": "string", "sourceColumn": "[district_code]", "type": "calculatedTableColumn", "isNameInferred": True, "isDataTypeInferred": True, "isHidden": True, "summarizeBy": "none"}],
        "partitions": [{"name": "District selector", "mode": "import", "source": {"type": "calculated",
        "expression": 'SELECTCOLUMNS(FILTER(bi_district, bi_district[district_class] IN {"kreisfreie_stadt", "landkreis"}), "District", bi_district[district_name], "district_code", bi_district[district_code])'}}]})
    model["tables"][1]["measures"] = make_measures()
    model["tables"][1]["columns"].append({"name": "scenario_short", "type": "calculated", "dataType": "string", "isDataTypeInferred": True, "summarizeBy": "none",
        "expression": 'IF(bi_scenario[scenario_id] = "registered", "Registered baseline", "Hypothetical exclusion")'})
    write(OUT / "ChargeScope.SemanticModel/model.bim", {"name": "ChargeScope", "compatibilityLevel": 1600, "model": model})
    write(OUT / "ChargeScope.SemanticModel/definition.pbism", {"version": "1.0", "settings": {}})


def make_measures():
    measures = {
        "Registered or Scenario Points": ('IF(HASONEVALUE(bi_scenario[scenario_id]) && SUM(bi_district_scenario[unknown_point_installations]) = 0, SUM(bi_district_scenario[points]))', "#,0"),
        "Population": ('IF(COUNTROWS(FILTER(bi_district, ISBLANK(bi_district[population]) || bi_district[population] <= 0)) = 0, SUM(bi_district[population]))', "#,0"),
        "Points per 10000 Residents": ('DIVIDE(10000 * [Registered or Scenario Points], [Population])', "0.0000"),
        "Installation kW": ('IF(HASONEVALUE(bi_scenario[scenario_id]) && SUM(bi_district_scenario[nominal_kw_missing_n]) = 0, SUM(bi_district_scenario[nominal_kw]))', "#,0.0"),
        "Installations": ('IF(HASONEVALUE(bi_scenario[scenario_id]), SUM(bi_district_scenario[installations]))', "#,0"),
        "Agreement-only known points": ('IF(HASONEVALUE(bi_scenario[scenario_id]), SUM(bi_district_scenario[agreed_known_points]))', "#,0"),
        "Unresolved installations": ('IF(HASONEVALUE(bi_scenario[scenario_id]), SUM(bi_district_scenario[unresolved_installations]))', "#,0"),
        "Unresolved known points": ('IF(HASONEVALUE(bi_scenario[scenario_id]), SUM(bi_district_scenario[known_points]) - SUM(bi_district_scenario[agreed_known_points]))', "#,0"),
        "Known points subtotal": ('IF(HASONEVALUE(bi_scenario[scenario_id]), SUM(bi_district_scenario[known_points]))', "#,0"),
        "Unknown point installations": ('IF(HASONEVALUE(bi_scenario[scenario_id]), SUM(bi_district_scenario[unknown_point_installations]))', "#,0"),
        "Missing kW installations": ('IF(HASONEVALUE(bi_scenario[scenario_id]), SUM(bi_district_scenario[nominal_kw_missing_n]))', "#,0"),
        "Brandenburg-wide snapshot rank": ('IF(HASONEVALUE(bi_scenario[scenario_id]) && HASONEVALUE(bi_district[district_code]), MAX(bi_district_scenario[brandenburg_rank]))', "0"),
        "Scenario status": ('IF(HASONEVALUE(bi_scenario[scenario_id]), IF(SELECTEDVALUE(bi_scenario[scenario_id]) = "registered", "REGISTERED baseline | group retained", "HYPOTHETICAL exclusion | access unverified"), "SELECT EXACTLY ONE SCENARIO | totals suppressed")', ""),
        "Baseline installation kW": ('IF(COUNTROWS(FILTER(bi_installation, ISBLANK(bi_installation[nominal_kw]))) = 0, SUM(bi_installation[nominal_kw]))', "#,0.0")}
    for prefix, scenario in [("Registered", "registered"), ("Hypothetical", "hypothetical_exclusion")]:
        for label, source in [("points", "Registered or Scenario Points"), ("rank", "Brandenburg-wide snapshot rank"), ("rate", "Points per 10000 Residents")]:
            measures[prefix + " " + label] = (f'CALCULATE([{source}], REMOVEFILTERS(bi_scenario), bi_scenario[scenario_id] = "{scenario}")', "0.0000" if label == "rate" else "#,0")
    for name in ["Registered or Scenario Points", "Population", "Points per 10000 Residents"]:
        measures["Berlin " + name] = (f'CALCULATE([{name}], REMOVEFILTERS(bi_district), bi_district[district_code] = "11000")', "0.0000" if name == "Points per 10000 Residents" else "#,0")
    # Additive redesign measures. Fixed-scope ones remove every district/scenario filter, so slicers and
    # cross-filters cannot relabel a selection as "Brandenburg"; Selected ones keep the user's district filter.
    bb = 'bi_district[district_class] IN {"kreisfreie_stadt", "landkreis"}'
    for prefix, scenario in [("Brandenburg fixed registered", "registered"), ("Brandenburg fixed hypothetical", "hypothetical_exclusion")]:
        for label, source in [("points", "Registered or Scenario Points"), ("residents", "Population"), ("rate", "Points per 10000 Residents")]:
            measures[f"{prefix} {label}"] = (f'CALCULATE([{source}], REMOVEFILTERS(bi_district), REMOVEFILTERS(bi_scenario), bi_scenario[scenario_id] = "{scenario}", {bb})', "0.0000" if label == "rate" else "#,0")
    for label, source in [("points", "Registered or Scenario Points"), ("residents", "Population"), ("rate", "Points per 10000 Residents")]:
        measures["Selected registered " + label] = (f'CALCULATE([{source}], REMOVEFILTERS(bi_scenario), bi_scenario[scenario_id] = "registered", KEEPFILTERS({bb}))', "0.0000" if label == "rate" else "#,0")
    oder = 'REMOVEFILTERS(bi_district), bi_district[district_code] = "12067"'
    measures.update({
        "Brandenburg fixed title": ('"Brandenburg, all 18 districts (fixed) · " & FORMAT([Brandenburg fixed registered points], "#,0") & " points / " & FORMAT([Brandenburg fixed registered residents], "#,0") & " residents"', ""),
        "Berlin title": ('"Berlin, separate context (not ranked) · " & FORMAT(CALCULATE([Berlin Registered or Scenario Points], REMOVEFILTERS(bi_scenario), bi_scenario[scenario_id] = "registered"), "#,0") & " points / " & FORMAT([Berlin Population], "#,0") & " residents"', ""),
        "Berlin registered rate": ('CALCULATE([Berlin Points per 10000 Residents], REMOVEFILTERS(bi_scenario), bi_scenario[scenario_id] = "registered")', "0.0000"),
        "Selected districts title": ('VAR names = CALCULATETABLE(VALUES(bi_district[district_name]), KEEPFILTERS(' + bb + '))\nVAR n = COUNTROWS(names)\nRETURN IF(n = 18, "Selected: none, so all 18 districts", "Selected (" & n & "): " & IF(n <= 3, CONCATENATEX(names, bi_district[district_name], ", ", bi_district[district_name], ASC), n & " districts")) & " · " & FORMAT([Selected registered points], "#,0") & " points / " & FORMAT([Selected registered residents], "#,0") & " residents"', ""),
        "Selected district code": ("SELECTEDVALUE('District selector'[district_code])", ""),
        # Selected district accented, all others grey; with no selection Oder-Spree (highest rate) stays highlighted.
        "District bar colour": ('VAR code = [Selected district code] RETURN IF(SELECTEDVALUE(bi_district[district_code]) = IF(ISBLANK(code), "12067", code), "#1D5FBF", "#A7B0BC")', ""),
        "Selected bar colour": ('VAR code = [Selected district code] RETURN IF(NOT ISBLANK(code) && SELECTEDVALUE(bi_district[district_code]) = code, "#1D5FBF", "#A7B0BC")', ""),
        "Selected row colour": ('VAR code = [Selected district code] RETURN IF(NOT ISBLANK(code) && SELECTEDVALUE(bi_district[district_code]) = code, "#DCE8F8")', ""),
        "Scenario bar colour": ('IF(SELECTEDVALUE(bi_scenario[scenario_id]) = "registered", "#1D5FBF", "#9DBFEA")', ""),
        "Registered unresolved points (non-zero)": ('VAR v = CALCULATE([Unresolved known points], REMOVEFILTERS(bi_scenario), bi_scenario[scenario_id] = "registered") RETURN IF(v <> 0, v)', "#,0"),
        "Oder-Spree rate change": (f'FORMAT(CALCULATE([Registered rate], {oder}), "0.0") & " → " & FORMAT(CALCULATE([Hypothetical rate], {oder}), "0.0")', ""),
        "Oder-Spree rank change": (f'FORMAT(CALCULATE([Registered rank], {oder}), "0") & " → " & FORMAT(CALCULATE([Hypothetical rank], {oder}), "0")', ""),
        "Oder-Spree title": (f'"Oder-Spree · " & FORMAT(CALCULATE([Registered points], {oder}), "#,0") & " → " & FORMAT(CALCULATE([Hypothetical points], {oder}), "#,0") & " points · " & FORMAT(CALCULATE([Population], {oder}), "#,0") & " residents"', ""),
        "Brandenburg rate change": ('FORMAT([Brandenburg fixed registered rate], "0.0") & " → " & FORMAT([Brandenburg fixed hypothetical rate], "0.0")', ""),
        "Brandenburg change title": ('"Brandenburg, all 18 districts · " & FORMAT([Brandenburg fixed registered points], "#,0") & " → " & FORMAT([Brandenburg fixed hypothetical points], "#,0") & " points"', "")})
    # Page 4: installation grain, registered. Reuses the guarded [Installations] and [Installation kW] (nominal kW summed
    # once per installation, blank if any is missing); points per installation is a ratio of sums.
    registered = 'REMOVEFILTERS(bi_scenario), bi_scenario[scenario_id] = "registered"'
    measures.update({
        "Registered installations": (f'CALCULATE([Installations], {registered})', "#,0"),
        "Registered capacity kW": (f'CALCULATE([Installation kW], {registered})', "#,0.0"),
        "Registered capacity MW": ('DIVIDE([Registered capacity kW], 1000)', "#,0.0"),
        "Registered points per installation": ('DIVIDE([Registered points], [Registered installations] - CALCULATE([Unknown point installations], ' + registered + '))', "0.00")})
    # One-line selected-district context per page. Values are taken at the selected district only (REMOVEFILTERS on
    # bi_district), so chart clicks on bi_district never change them; ranks stay fixed-cohort ranks of 18.
    stats = box_stats([row["rate"] for row in district_rows("registered")])
    at = "REMOVEFILTERS(bi_district), bi_district[district_code] = code"
    head = "VAR code = [Selected district code]\nVAR districtName = SELECTEDVALUE('District selector'[District])\n"
    v = lambda name, form: f'FORMAT(CALCULATE([{name}], {at}), "{form}")'
    position = ('SWITCH(TRUE(), r > {upper_fence!r}, "outlier above the box", r > {q3!r}, "above Q3 {q3:.1f}", r >= {median!r}, "between median {median:.1f} and Q3", '
                'r >= {q1!r}, "between Q1 {q1:.1f} and median", r >= {lower_fence!r}, "below Q1 {q1:.1f}", "outlier below the box")').format(**stats)
    unresolved = f'FORMAT(CALCULATE([Unresolved known points], {at}, REMOVEFILTERS(bi_scenario), bi_scenario[scenario_id] = "registered"), "#,0")'
    measures.update({
        "Selected district compare": (head + 'RETURN IF(ISBLANK(code), "Selected district: All · Oder-Spree, the highest rate, is highlighted", "Selected: " & districtName & " · " & '
            + v("Registered points", "#,0") + ' & " points · " & ' + v("Registered rate", "0.0") + ' & " per 10,000 · rank " & ' + v("Registered rank", "0") + ' & " of 18")', ""),
        "Selected district spread": (head + f'VAR r = CALCULATE([Registered rate], {at})\nRETURN IF(ISBLANK(code), "Selected district: All · the image is a fixed snapshot of all 18 districts", '
            '"Selected: " & districtName & " · " & FORMAT(r, "0.0") & " per 10,000 · rank " & ' + v("Registered rank", "0") + ' & " of 18 · " & ' + position + ' & " · the fixed image does not change")', ""),
        "Selected district test": (head + f'VAR p = CALCULATE([Registered points], {at})\nVAR ph = CALCULATE([Hypothetical points], {at})\n'
            'RETURN SWITCH(TRUE(), ISBLANK(code), "Selected district: All · exclusion stays fixed to Oder-Spree; baseline unchanged", '
            'code = "12067", "Selected: Oder-Spree, the subject of this page", "Selected: " & districtName & " · " & '
            'IF(p = ph, "same " & FORMAT(p, "#,0") & " points in both versions (none excluded)", FORMAT(p, "#,0") & " → " & FORMAT(ph, "#,0") & " points") & " · rank " & '
            + v("Registered rank", "0") + ' & " → " & ' + v("Hypothetical rank", "0") + ' & " of 18 · unresolved location: " & ' + unresolved + ' & " points")', ""),
        "Selected district installations": (head + 'RETURN IF(ISBLANK(code), "Selected district: All · the Total row covers all 18 districts", "Selected: " & districtName & " · " & '
            + v("Registered installations", "#,0") + ' & " installations · " & ' + v("Registered points", "#,0") + ' & " points · " & ' + v("Registered capacity MW", "0.0") + ' & " MW · " & '
            + v("Registered points per installation", "0.00") + ' & " points per installation")', "")})
    return [{"name": name, "expression": expression, "formatString": form} for name, (expression, form) in measures.items()]


def district_rows(scenario="registered"):
    """The 18 Brandenburg district rows of one scenario, joined to names; Berlin context excluded."""
    with (BUNDLE / "bi_district.csv").open(encoding="utf-8", newline="") as source:
        names = {row["district_code"]: row["district_name"] for row in csv.DictReader(source)}
    with (BUNDLE / "bi_district_scenario.csv").open(encoding="utf-8", newline="") as source:
        rows = [dict(row, district_name=names[row["district_code"]]) for row in csv.DictReader(source)
                if row["scenario_id"] == scenario and row["region"] == "Brandenburg"]
    assert len({row["district_code"] for row in rows}) == len(rows) == 18
    assert all(int(row["population"]) > 0 and int(row["unknown_point_installations"]) == 0 for row in rows)
    for row in rows:
        row["rate"] = 10000 * float(row["points"]) / int(row["population"])
        assert math.isclose(row["rate"], float(row["points_per_10000_residents"]), rel_tol=1e-12)
    return sorted(rows, key=lambda row: (-row["rate"], row["district_code"]))


def box_stats(values):
    """Box-plot statistics of equal-weight observations: Hyndman-Fan type 7 (inclusive) quartiles,
    whiskers at the most extreme observations inside the 1.5 x IQR fences, everything outside is an outlier."""
    values = sorted(values)
    q1, median, q3 = statistics.quantiles(values, n=4, method="inclusive")
    iqr = q3 - q1
    fences = (q1 - 1.5 * iqr, q3 + 1.5 * iqr)
    inside = [value for value in values if fences[0] <= value <= fences[1]]
    return {"n": len(values), "min": values[0], "q1": q1, "median": median, "q3": q3, "max": values[-1], "iqr": iqr,
            "lower_fence": fences[0], "upper_fence": fences[1], "lower_whisker": inside[0], "upper_whisker": inside[-1],
            "outliers": [value for value in values if value < fences[0] or value > fences[1]]}


def installation_rows():
    """Installation-grain totals per district from bi_installation.csv: nominal kW counted once per installation,
    never summed from points. Missing kW (blank or <= 0) and unknown point counts are counted, not zeroed.
    Asserted equal to the exported district and region metrics."""
    out = {}
    with (BUNDLE / "bi_installation.csv").open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    assert len({row["installation_id"] for row in rows}) == len(rows)
    for row in rows:
        d = out.setdefault(row["district_code"], {"installations": 0, "kw": 0.0, "kw_missing": 0, "points": 0, "points_unknown": 0})
        d["installations"] += 1
        if row["nominal_kw"] in ("", None) or float(row["nominal_kw"]) <= 0:
            d["kw_missing"] += 1
        else:
            d["kw"] += float(row["nominal_kw"])
        if row["declared_point_count"] in ("", None):
            d["points_unknown"] += 1
        else:
            d["points"] += int(row["declared_point_count"])
    with (BUNDLE / "bi_district_scenario.csv").open(encoding="utf-8", newline="") as source:
        exported = {row["district_code"]: row for row in csv.DictReader(source) if row["scenario_id"] == "registered"}
    assert set(out) == set(exported)
    for code, d in out.items():
        e = exported[code]
        assert (d["installations"], d["kw_missing"], d["points"], d["points_unknown"]) == (float(e["installations"]), float(e["nominal_kw_missing_n"]), float(e["points"]), float(e["unknown_point_installations"])), code
        assert math.isclose(d["kw"], float(e["nominal_kw"]), abs_tol=1e-6), code
        d["region"] = e["region"]
    with (BUNDLE / "bi_region_scenario.csv").open(encoding="utf-8", newline="") as source:
        regions = {row["region"]: row for row in csv.DictReader(source) if row["scenario_id"] == "registered"}
    totals = {}
    for name, region in regions.items():
        group = [d for d in out.values() if d["region"] == name]
        t = {key: sum(d[key] for d in group) for key in ("installations", "kw", "kw_missing", "points", "points_unknown")}
        assert (t["installations"], t["points"], t["kw_missing"], t["points_unknown"]) == (float(region["installations"]), float(region["points"]), float(region["nominal_kw_missing_n"]), float(region["unknown_point_installations"])), name
        assert math.isclose(t["kw"], float(region["nominal_kw"]), abs_tol=1e-6), name
        t["points_per_installation"] = t["points"] / (t["installations"] - t["points_unknown"])  # ratio of sums
        totals[name] = t
    return out, totals


def box_svg(rows, stats):
    """Static, fixed-cohort box plot with every district dot (approved page-2 design), 1232 x 560."""
    width, height, x0, x1 = 1232, 560, 48, 1184
    x = lambda value: x0 + (x1 - x0) * value / 50
    esc = lambda value: value.replace("&", "&amp;").replace("<", "&lt;")
    ink, ink2, muted, blue = "#111827", "#374151", "#5B6472", "#1D5FBF"
    box_y, box_h, strip, gap, radius, axis_y = 46, 110, 306, 38, 12, 472
    mid = box_y + box_h / 2
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="Segoe UI, sans-serif" font-size="16" fill="{ink2}">',
             '<rect width="100%" height="100%" fill="#ffffff"/>']
    for tick in range(0, 51, 10):
        parts.append(f'<line x1="{x(tick):.1f}" y1="28" x2="{x(tick):.1f}" y2="{axis_y}" stroke="{"#E5E7EB" if tick else "#9CA3AF"}"/>'
                     f'<text x="{x(tick):.1f}" y="{axis_y + 22}" text-anchor="middle" fill="{muted}">{tick}</text>')
    parts.append(f'<line x1="{x0}" y1="{axis_y}" x2="{x1}" y2="{axis_y}" stroke="#9CA3AF"/>'
                 f'<text x="{(x0 + x1) / 2}" y="{axis_y + 50}" text-anchor="middle" fill="{ink}" font-weight="600">Registered points per 10,000 residents</text>')
    for value in (stats["q1"], stats["median"], stats["q3"]):
        parts.append(f'<line x1="{x(value):.1f}" y1="{box_y + box_h}" x2="{x(value):.1f}" y2="{strip + 2.5 * gap}" stroke="#B8C2CF" stroke-dasharray="4 4"/>')
    lo, hi = x(stats["lower_whisker"]), x(stats["upper_whisker"])
    parts += [f'<line x1="{lo:.1f}" y1="{mid}" x2="{x(stats["q1"]):.1f}" y2="{mid}" stroke="#3F4C5F" stroke-width="2"/>',
              f'<line x1="{x(stats["q3"]):.1f}" y1="{mid}" x2="{hi:.1f}" y2="{mid}" stroke="#3F4C5F" stroke-width="2"/>',
              f'<line x1="{lo:.1f}" y1="{mid - 20}" x2="{lo:.1f}" y2="{mid + 20}" stroke="#3F4C5F" stroke-width="2"/>',
              f'<line x1="{hi:.1f}" y1="{mid - 20}" x2="{hi:.1f}" y2="{mid + 20}" stroke="#3F4C5F" stroke-width="2"/>',
              f'<rect x="{x(stats["q1"]):.1f}" y="{box_y}" width="{x(stats["q3"]) - x(stats["q1"]):.1f}" height="{box_h}" fill="#E3EBF5" stroke="#3F4C5F" stroke-width="2"/>',
              f'<line x1="{x(stats["median"]):.1f}" y1="{box_y}" x2="{x(stats["median"]):.1f}" y2="{box_y + box_h}" stroke="{ink}" stroke-width="4"/>',
              f'<text x="{x(stats["median"]):.1f}" y="{box_y - 12}" text-anchor="middle" fill="{ink}" font-weight="700">Median {stats["median"]:.1f}</text>',
              f'<text x="{x(stats["q1"]) - 6:.1f}" y="{box_y + box_h + 24}" text-anchor="end">Q1 {stats["q1"]:.1f}</text>',
              f'<text x="{x(stats["q3"]) + 6:.1f}" y="{box_y + box_h + 24}">Q3 {stats["q3"]:.1f}</text>',
              f'<text x="{lo - 8:.1f}" y="{mid + 6}" text-anchor="end">{stats["lower_whisker"]:.1f}</text>',
              f'<text x="{hi + 8:.1f}" y="{mid + 6}">{stats["upper_whisker"]:.1f}</text>']
    for value in stats["outliers"]:
        parts.append(f'<circle cx="{x(value):.1f}" cy="{mid}" r="9" fill="#ffffff" stroke="{blue}" stroke-width="2.5"/>'
                     f'<text x="{x(value):.1f}" y="{mid - 20}" text-anchor="middle" fill="{blue}" font-weight="600">Outlier</text>')
    # Deterministic beeswarm: rates are never moved; nearby dots take lanes 0, +1, -1, +2, -2 in rate order.
    last = {}
    for row in sorted(rows, key=lambda row: (row["rate"], row["district_code"])):
        px = x(row["rate"])
        lane = next(lane for lane in [0, 1, -1, 2, -2, 3, -3] if lane not in last or px - last[lane] >= 2 * radius + 4)
        last[lane] = px
        focus = row["district_code"] == "12067"
        parts.append(f'<circle cx="{px:.1f}" cy="{strip + lane * gap}" r="{radius}" fill="{blue if focus else "#6B7787"}" stroke="#ffffff" stroke-width="2"/>')
        if focus:
            parts.append(f'<text x="{px - radius - 10:.1f}" y="{strip + lane * gap + 6}" text-anchor="end" fill="{blue}" font-size="18" font-weight="700">{esc(row["district_name"])} {row["rate"]:.1f}</text>')
    parts.append(f'<text x="{x0}" y="{height - 8}" font-size="13" fill="{muted}">Fixed snapshot image: registered · all 18 Brandenburg districts · ignores clicks/filters; no tooltips.</text>')
    return "\n".join(parts + ["</svg>"]) + "\n"


def make_report():
    base = OUT / "ChargeScope.Report"
    registered, hypothetical = district_rows("registered"), district_rows("hypothetical_exclusion")
    assert registered[0]["district_code"] == "12067", "Copy below assumes Oder-Spree leads the registered ranking"
    stats = box_stats([row["rate"] for row in registered])
    with (BUNDLE / "bi_region_scenario.csv").open(encoding="utf-8", newline="") as source:
        region = {(row["scenario_id"], row["region"]): row for row in csv.DictReader(source)}
    bb_reg, berlin_reg = region[("registered", "Brandenburg")], region[("registered", "Berlin context")]
    oder = registered[0]
    oder_h = next(row for row in hypothetical if row["district_code"] == "12067")
    unresolved = [float(row["known_points"]) - float(row["agreed_known_points"]) for row in registered]
    installs, install_totals = installation_rows()
    bb_inst, berlin_inst = install_totals["Brandenburg"], install_totals["Berlin context"]
    assert not any(installs[row["district_code"]]["kw_missing"] or installs[row["district_code"]]["points_unknown"] for row in registered), "Page 4 copy states no missing kW or point counts"
    num = lambda value: f"{float(value):,.0f}"

    shutil.rmtree(base / "definition/pages", ignore_errors=True)
    shutil.rmtree(base / "StaticResources", ignore_errors=True)
    image = f"boxplot_registered_{RUN[:8]}.svg"
    (base / "StaticResources/RegisteredResources").mkdir(parents=True)
    (base / "StaticResources/RegisteredResources" / image).write_text(box_svg(registered, stats), encoding="utf-8")
    write(OUT / "boxplot-stats.json", {"bundle": RUN, "scenario": "registered", "observation": "one Brandenburg district (equal weight), Berlin excluded",
        "quantile_method": "Hyndman-Fan type 7 / statistics.quantiles(method='inclusive')", "whiskers": "most extreme observations inside 1.5 x IQR fences",
        "interactive": False, "image": "ChargeScope.Report/StaticResources/RegisteredResources/" + image, **stats,
        "districts": [{"district_code": row["district_code"], "district_name": row["district_name"], "rate": row["rate"]} for row in registered]})

    pages = [("compare", "1 Compare districts"), ("spread", "2 See the spread"), ("test", "3 Test the comparison"), ("installations", "4 Installation details"), ("district_detail", "District detail")]
    write(OUT / "ChargeScope.pbip", {"$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json", "version": "1.0", "artifacts": [{"report": {"path": "ChargeScope.Report"}}], "settings": {"enableAutoRecovery": True}})
    write(base / "definition.pbir", {"version": "4.0", "datasetReference": {"byPath": {"path": "../ChargeScope.SemanticModel"}}})
    write(base / "definition/report.json", {"$schema": SCHEMA + "report/3.1.0/schema.json", "themeCollection": {},
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources", "items": [{"name": image, "path": image, "type": "Image"}]}]})
    write(base / "definition/version.json", {"$schema": SCHEMA + "versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    write(base / "definition/pages/pages.json", {"$schema": SCHEMA + "pagesMetadata/1.0.0/schema.json", "pageOrder": [name for name, _ in pages], "activePageName": pages[0][0]})
    ink, ink2, muted = "#111827", "#374151", "#5B6472"

    for page_name, display in pages:
        page = base / "definition/pages" / page_name
        counter, interactions, height = 0, [], 720

        def visual(kind, title, x, y, width, height, roles=None, objects=None, filters=None, sort=None, alt=None, sync=None, link=None):
            nonlocal counter
            counter += 1
            name = f"{page_name}_{counter:02}"
            content = {"visualType": kind, "drillFilterOtherVisuals": True, "visualContainerObjects": {"title": fmt(show=bool(title), text=title or "", fontSize=12, bold=True)}}
            content["visualContainerObjects"]["title"][0]["properties"]["fontColor"] = {"solid": {"color": literal(ink)}}
            if alt:
                content["visualContainerObjects"]["general"] = fmt(altText=alt)
            if link:
                content["visualContainerObjects"]["visualLink"] = [{"properties": link}]
            if roles:
                content["query"] = {"queryState": {role: {"projections": items} for role, items in roles.items()}}
            if sort:
                content["query"]["sortDefinition"] = {"sort": [{"field": field("bi_scenario", sort, True), "direction": "Descending"}], "isDefaultSort": True}
            if objects:
                content["objects"] = objects
            if sync:
                content["syncGroup"] = {"groupName": sync, "fieldChanges": True, "filterChanges": True}
            value = {"$schema": SCHEMA + "visualContainer/2.1.0/schema.json", "name": name, "position": {"x": x, "y": y, "width": width, "height": height, "z": counter, "tabOrder": counter}, "visual": content}
            if filters:
                value["filterConfig"] = {"filters": filters}
            write(page / "visuals" / name / "visual.json", value)
            return name

        def text(lines, x, y, width, height, align="left"):
            """lines: (text, size in pt, colour, bold) paragraphs."""
            paragraphs = [{"textRuns": [{"value": body, "textStyle": {"fontSize": f"{size}pt", "fontFamily": "Segoe UI", "color": colour, **({"fontWeight": "bold"} if bold else {})}}], "horizontalTextAlignment": align} for body, size, colour, bold in lines if body]
            return visual("textbox", None, x, y, width, height, objects={"general": [{"properties": {"paragraphs": paragraphs}}]})

        def measure(name, label=None):
            return projection("bi_scenario", name, True, label)

        def bars(title, x, y, width, height, category, value, label, tooltips, filters, colour, precision, end=None, sort=None, names=True, size=12, alt=None):
            point = {"properties": {"fill": {"solid": {"color": {"expr": field("bi_scenario", colour, True)} if colour.endswith("colour") else literal(colour)}}}}
            if colour.endswith("colour"):
                point["selector"] = {"data": [{"dataViewWildcard": {"matchingOption": 1}}]}
            labels = fmt(show=True, fontSize=size, labelDisplayUnits=1)
            labels[0]["properties"]["labelPrecision"] = {"expr": {"Literal": {"Value": f"{precision}L"}}}
            labels[0]["properties"]["color"] = {"solid": {"color": literal(ink)}}
            labels[0]["properties"]["labelPosition"] = literal("OutsideEnd")
            axis = fmt(show=True, start=0, fontSize=10, showAxisTitle=False, gridlineShow=True)
            if end:
                axis[0]["properties"]["end"] = literal(end)
            return visual("clusteredBarChart", title, x, y, width, height,
                {"Category": [category], "Y": [measure(value, label)], **({"Tooltips": tooltips} if tooltips else {})},
                {"categoryAxis": fmt(show=names, fontSize=12, showAxisTitle=False, maxMarginFactor=40), "valueAxis": axis, "labels": labels,
                 "legend": fmt(show=False), "dataPoint": [point]}, filters, sort=sort or value, alt=alt)

        def header(title, how, headline=None, reference=None, caveat=None):
            text([(title, 18, ink, True), (how, 11, ink2, False)] + ([(caveat, 10, muted, False)] if caveat else []), 16, 8, 760, 90 if caveat is not None else 70)
            if headline:
                text([(headline, 12, ink, True)] + ([(reference, 11, muted, False)] if reference else []), 780, 8, 484, 64, "right")

        def button(label, action, x, y, width, destination=None):
            properties = {"show": literal(True), "type": literal(action)}
            if destination:
                properties.update({"drillthroughSection": literal(destination),
                    "enabledTooltip": literal("View the clicked district. Ctrl+click in Desktop edit mode."),
                    "disabledTooltip": literal("Select one district bar on this page first.")})
            objects = {"text": fmt(show=True), "fill": fmt(show=True), "outline": fmt(show=True),
                       "icon": fmt(show=False), "shape": fmt(tileShape="rectangle")}
            for state, background in [("default", "#245A92"), ("hover", "#1C4773"), ("selected", "#163858"), ("disabled", "#E5E7EB")]:
                text_properties = fmt(text=label, fontSize=12, fontFamily="Segoe UI", horizontalAlignment="center", verticalAlignment="middle")[0]["properties"]
                text_properties["fontColor"] = {"solid": {"color": literal(ink2 if state == "disabled" else "#FFFFFF")}}
                objects["text"].append({"properties": text_properties, "selector": {"id": state}})
                for name, colour_property in [("fill", "fillColor"), ("outline", "lineColor")]:
                    style = fmt(transparency=0, **({"weight": 1} if name == "outline" else {}))[0]
                    style["properties"][colour_property] = {"solid": {"color": literal(background)}}
                    style["selector"] = {"id": state}
                    objects[name].append(style)
            return visual("actionButton", None, x, y, width, 44,
                objects=objects, alt=label, link=properties)

        district = projection("bi_district", "district_name", label="District")
        bb = [category_filter("bi_district", "district_class", ["kreisfreie_stadt", "landkreis"], page_name + "_bb")]
        rate_tips = [measure("Registered points", "Registered points"), measure("Population", "Residents"), measure("Registered rate", "Points per 10,000 residents"), measure("Registered rank", "Rank of 18 by rate")]
        if page_name == "compare":
            header("Counts and rates rank differently", "How to read: Compare counts and rates in the same district order.",
                   f"Brandenburg  {num(bb_reg['points'])} points · {float(bb_reg['points_per_10000_residents']):.1f} per 10,000",
                   f"Berlin, reference only (not ranked)  {num(berlin_reg['points'])} · {float(berlin_reg['points_per_10000_residents']):.1f} per 10,000")
            bars("Registered charging points (count)", 16, 184, 672, 500, district, "Registered points", "Registered points", rate_tips[1:], bb, "District bar colour", 0, 900, sort="Registered rate",
                 alt="Bar chart: registered charging points by Brandenburg district, ordered by rate per 10,000 residents.")
            bars("Points per 10,000 residents", 696, 184, 568, 500, district, "Registered rate", "Points per 10,000 residents", rate_tips[:2] + rate_tips[3:], bb, "District bar colour", 1, 55, names=False,
                 alt="Bar chart: registered points per 10,000 residents by Brandenburg district, same order as the count chart.")
        elif page_name == "spread":
            header("Rates cluster; one district stands out", "How to read: Fixed box = middle half; line = median; dot = district.", "Registered · all 18 districts")
            visual("image", None, 24, 184, 1232, 488,
                objects={"general": [{"properties": {"imageUrl": {"expr": {"ResourcePackageItem": {"PackageName": "RegisteredResources", "PackageType": 1, "ItemName": image}}}}}],
                         "imageScaling": [{"properties": {"imageScalingType": literal("Fit")}}]},
                alt=f"Box plot of 18 Brandenburg district rates: Q1 {stats['q1']:.1f}, median {stats['median']:.1f}, Q3 {stats['q3']:.1f}, whiskers {stats['lower_whisker']:.1f} to {stats['upper_whisker']:.1f}; Oder-Spree {oder['rate']:.1f} is the only outlier.")
        elif page_name == "test":
            header("Oder-Spree without one flagged group", "How to read: Fixed Oder-Spree, not before and after.", caveat="")
            paired = bars("Oder-Spree, points per 10,000 residents", 16, 204, 728, 328, projection("bi_scenario", "scenario_short", label="Version"), "Points per 10000 Residents", "Points per 10,000 residents",
                [measure("Registered or Scenario Points", "Points"), measure("Population", "Residents"), measure("Brandenburg-wide snapshot rank", "Rank of 18")],
                [category_filter("bi_district", "district_code", ["12067"], "oder_spree")], "Scenario bar colour", 1, 55, size=18,
                alt="Two bars for Oder-Spree: registered rate and hypothetical rate without the flagged coordinate group.")
            text([(f"Rank {oder['brandenburg_rank']} → {oder_h['brandenburg_rank']} of 18", 16, ink, True),
                  (f"{num(oder['points'])} → {num(oder_h['points'])} points · residents unchanged", 12, ink2, False)], 16, 548, 728, 76)
            geo = bars(f"Unresolved location: {sum(unresolved):.0f} points", 776, 204, 488, 368, district, "Registered unresolved points (non-zero)", "Unresolved points (count)",
                [], bb, "District bar colour", 0, 25, alt="Bar chart: registered points whose district label and coordinates disagree, by district.")
            text([(f"Other {sum(value == 0 for value in unresolved)} districts: 0 · Berlin's {float(berlin_reg['known_points']) - float(berlin_reg['agreed_known_points']):.0f} not included", 12, ink2, False)], 776, 580, 488, 44)
            interactions = [{"source": paired, "target": geo, "type": "NoFilter"}, {"source": geo, "target": paired, "type": "NoFilter"}]
        elif page_name == "installations":
            height = 1300
            header("Capacity and installation size", "How to read: Compare nominal capacity and points per installation.",
                   f"Brandenburg  {bb_inst['kw'] / 1000:,.1f} MW · {bb_inst['points_per_installation']:.2f} points per installation",
                   "")
            inst_tips = [measure("Registered installations", "Installations"), measure("Registered points", "Points"), measure("Registered capacity kW", "Capacity (kW, nominal)")]
            bars("Registered capacity (MW, nominal)", 16, 184, 672, 500, district, "Registered capacity MW", "Capacity (MW, nominal)", inst_tips + [measure("Registered points per installation", "Points per installation")], bb, "Selected bar colour", 1, 50,
                 alt="Bar chart: nominal registered capacity in MW by Brandenburg district, largest first.")
            bars("Average points per installation", 696, 184, 568, 500, district, "Registered points per installation", "Points per installation", inst_tips + [measure("Registered capacity MW", "Capacity (MW, nominal)")], bb, "Selected bar colour", 2, 2.4,
                 sort="Registered capacity MW", names=False, alt="Bar chart: points per installation by Brandenburg district, same order as the capacity chart.")
            text([("Registered values · nominal kW counted once per installation, not usage", 12, ink, True)], 16, 736, 1248, 56)
            columns = [district, measure("Registered installations", "Installations"), measure("Registered points", "Points"),
                       measure("Registered capacity kW", "Capacity (kW, nominal)"), measure("Registered points per installation", "Points per installation")]
            shade = [{"properties": {"backColor": {"solid": {"color": {"expr": field("bi_scenario", "Selected row colour", True)}}}},
                      "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": column["queryRef"]}} for column in columns]
            visual("tableEx", None, 16, 796, 1248, 490, {"Values": columns},
                {"values": fmt(fontSize=11) + shade, "columnHeaders": fmt(fontSize=11, bold=True), "total": fmt(totals=True, fontSize=11, bold=True)}, bb,
                alt="Table: installations, points, nominal capacity in kW and points per installation for each Brandenburg district, with a Brandenburg total.")
        else:
            height = 440
            header("District detail", "How to read: Registered values for the district filter.")
            button("Back", "Back", 1104, 16, 160)
            visual("card", None, 16, 88, 1248, 88, {"Values": [measure("Selected districts title", "Clicked district")]},
                {"labels": fmt(fontSize=18, labelDisplayUnits=1), "categoryLabels": fmt(show=False), "wordWrap": fmt(show=True)},
                alt="Actual district filter and registered points and population. No filter means all 18 districts, not a selected district.")
            visual("tableEx", None, 16, 196, 1248, 128,
                {"Values": [district, measure("Registered points", "Points"), measure("Population", "Residents"),
                    measure("Registered rate", "Points / 10,000"), measure("Registered installations", "Installations"),
                    measure("Registered capacity kW", "Nominal kW"), measure("Registered points per installation", "Points / installation")]},
                {"values": fmt(fontSize=12), "columnHeaders": fmt(fontSize=12, bold=True), "total": fmt(totals=False)},
                alt="Clicked Brandenburg district: registered points, residents, rate, installation count, nominal capacity and points per installation.")
            text([("Back → click another bar to change district.", 11, ink2, False)], 16, 340, 1248, 56)
        if page_name in {"compare", "installations"}:
            button("View selected district", "Drillthrough", 1016, 88, 248, "district_detail")
        write(page / "page.json", {"$schema": SCHEMA + "page/2.0.0/schema.json", "name": page_name, "displayName": display,
            "displayOption": "FitToWidth" if height > 720 else "FitToPage", "width": 1280, "height": height, **({"visualInteractions": interactions} if interactions else {}),
            **({"type": "Drillthrough", "visibility": "HiddenInViewMode",
                "filterConfig": {"filters": [{"name": "district_drillthrough", "field": field("bi_district", "district_name"), "type": "Categorical", "howCreated": "Drillthrough"}, *bb]},
                "pageBinding": {"name": "district_detail_binding", "type": "Drillthrough", "referenceScope": "Default", "acceptsFilterContext": "None",
                    "parameters": [{"name": "district_parameter", "boundFilter": "district_drillthrough", "fieldExpr": field("bi_district", "district_name"), "asAggregation": False}]}}
               if page_name == "district_detail" else {})})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=BUNDLE, help="Complete preserved bundle; pinned run ID only")
    parser.add_argument("--replace-generated", action="store_true", help="Replace final generated files after archiving any Desktop edits")
    args = parser.parse_args()
    BUNDLE = args.bundle.resolve()
    assert BUNDLE.name == RUN and (BUNDLE / "bi_model.json").is_file(), "Use the complete pinned bundle"
    if (OUT / "ChargeScope.pbip").exists() and not args.replace_generated:
        parser.error("Final report exists; archive Desktop edits before using --replace-generated")
    make_model()
    make_report()
    print("Generated powerbi/portfolio-final/ChargeScope.pbip; refresh in Power BI Desktop before use")
