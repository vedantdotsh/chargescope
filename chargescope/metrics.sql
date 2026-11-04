-- District metrics for the 19-key metric universe.
-- Registered baseline = source labels. Geographic totals = assignment_outcome = 'agreed' only.
-- SUM skips NULLs; pair every kW sum with the matching missing count. Missing is not zero.
-- High-power threshold 22 kW is the BNetzA published Schnellladepunkt split in this snapshot,
-- not a current-LSV legal definition.

WITH src AS (
  SELECT
    label_ars AS district_code,
    COUNT(*) AS source_label_installations,
    COALESCE(SUM(CASE WHEN groups_reconcile THEN declared_point_count END), 0) AS source_label_points,
    SUM(nominal_kw) AS source_label_kw,
    COUNT(*) FILTER (WHERE nominal_kw IS NULL) AS source_label_kw_missing_n,
    SUM(capped_kw) AS capped_kw_source_label,
    COUNT(*) FILTER (WHERE capped_kw IS NOT NULL) AS capped_kw_known_n,
    COUNT(*) FILTER (WHERE capped_kw IS NULL) AS capped_kw_missing_n,
    COALESCE(SUM(CASE WHEN groups_reconcile AND is_tesla_cluster THEN declared_point_count END), 0) AS tesla_gruenheide_points,
    SUM(CASE WHEN is_tesla_cluster THEN nominal_kw END) AS tesla_gruenheide_kw,
    COUNT(*) FILTER (WHERE is_tesla_cluster) AS tesla_gruenheide_installations
  FROM installation_snapshot
  WHERE label_ars IS NOT NULL
  GROUP BY 1
),
geo AS (
  SELECT
    spatial_ars AS district_code,
    COUNT(*) AS geographic_installations,
    COALESCE(SUM(CASE WHEN groups_reconcile THEN declared_point_count END), 0) AS geographic_points,
    SUM(nominal_kw) AS geographic_kw,
    COUNT(*) FILTER (WHERE nominal_kw IS NULL) AS geographic_kw_missing_n
  FROM installation_snapshot
  WHERE assignment_outcome = 'agreed'
  GROUP BY 1
),
incoming AS (
  SELECT
    spatial_ars AS district_code,
    COUNT(*) AS incoming_spatial_installations,
    COALESCE(SUM(CASE WHEN groups_reconcile THEN declared_point_count END), 0) AS incoming_spatial_points
  FROM installation_snapshot
  WHERE spatial_ars IS NOT NULL
    AND assignment_outcome <> 'agreed'
  GROUP BY 1
),
conflict AS (
  SELECT
    label_ars AS district_code,
    COUNT(*) AS conflict_installations,
    COALESCE(SUM(CASE WHEN groups_reconcile THEN declared_point_count END), 0) AS conflict_points
  FROM installation_snapshot
  WHERE assignment_outcome = 'conflict'
  GROUP BY 1
),
op AS (
  SELECT
    label_ars AS district_code,
    operator_raw,
    SUM(CASE WHEN groups_reconcile THEN declared_point_count ELSE 0 END) AS pts
  FROM installation_snapshot
  WHERE label_ars IS NOT NULL
    AND groups_reconcile
  GROUP BY 1, 2
),
op_tot AS (
  SELECT
    district_code,
    SUM(pts) AS validated_points,
    SUM(CASE WHEN operator_raw IS NULL OR operator_raw = '' THEN pts ELSE 0 END) AS unknown_operator_points,
    SUM(CASE WHEN operator_raw IS NOT NULL AND operator_raw <> '' THEN pts ELSE 0 END) AS known_operator_points
  FROM op
  GROUP BY 1
),
op_rank AS (
  SELECT
    district_code,
    operator_raw AS largest_operator_name,
    pts AS largest_operator_points,
    ROW_NUMBER() OVER (
      PARTITION BY district_code
      ORDER BY pts DESC, operator_raw
    ) AS rn
  FROM op
  WHERE operator_raw IS NOT NULL AND operator_raw <> ''
),
pt AS (
  SELECT
    i.label_ars AS district_code,
    COUNT(*) FILTER (WHERE i.groups_reconcile) AS parsed_validated_points,
    COUNT(*) FILTER (WHERE i.groups_reconcile AND p.point_kw IS NOT NULL) AS known_power_points,
    COUNT(*) FILTER (WHERE i.groups_reconcile AND p.point_kw IS NULL) AS unknown_power_points,
    COUNT(*) FILTER (WHERE i.groups_reconcile AND p.point_kw IS NOT NULL AND p.point_kw > 22) AS high_power_points
  FROM point_snapshot p
  JOIN installation_snapshot i USING (installation_id)
  WHERE i.label_ars IS NOT NULL
  GROUP BY 1
)
SELECT
  d.district_code,
  d.district_name,
  d.district_class,
  d.peer_group,
  d.boundary_vintage,
  p.population_date,
  p.cadastral_area_km2,
  p.population,
  COALESCE(s.source_label_installations, 0) AS source_label_installations,
  COALESCE(s.source_label_points, 0) AS source_label_points,
  s.source_label_kw,
  COALESCE(s.source_label_kw_missing_n, 0) AS source_label_kw_missing_n,
  COALESCE(s.source_label_kw_missing_n, 0) = 0 AS source_label_kw_complete,
  COALESCE(g.geographic_installations, 0) AS geographic_installations,
  COALESCE(g.geographic_points, 0) AS geographic_points,
  g.geographic_kw,
  COALESCE(g.geographic_kw_missing_n, 0) AS geographic_kw_missing_n,
  COALESCE(g.geographic_kw_missing_n, 0) = 0 AS geographic_kw_complete,
  COALESCE(inc.incoming_spatial_installations, 0) AS incoming_spatial_installations,
  COALESCE(inc.incoming_spatial_points, 0) AS incoming_spatial_points,
  COALESCE(c.conflict_installations, 0) AS conflict_installations,
  COALESCE(c.conflict_points, 0) AS conflict_points,
  s.capped_kw_source_label,
  COALESCE(s.capped_kw_known_n, 0) AS capped_kw_known_n,
  COALESCE(s.capped_kw_missing_n, 0) AS capped_kw_missing_n,
  COALESCE(pt.known_power_points, 0) AS known_power_points,
  COALESCE(pt.unknown_power_points, 0) AS unknown_power_points,
  COALESCE(pt.high_power_points, 0) AS high_power_points,
  '>22 kW point maximum; source split, not AC/DC classification' AS high_power_definition,
  COALESCE(s.tesla_gruenheide_installations, 0) AS tesla_gruenheide_installations,
  COALESCE(s.tesla_gruenheide_points, 0) AS tesla_gruenheide_points,
  s.tesla_gruenheide_kw,
  COALESCE(s.source_label_points, 0) - COALESCE(s.tesla_gruenheide_points, 0)
    AS source_label_points_ex_tesla_gruenheide,
  CASE
    WHEN p.population IS NULL OR p.population = 0 THEN NULL
    ELSE 10000.0 * COALESCE(s.source_label_points, 0) / p.population
  END AS points_per_10000_residents_source_label,
  CASE
    WHEN p.population IS NULL OR p.population = 0 THEN NULL
    ELSE 10000.0 * COALESCE(g.geographic_points, 0) / p.population
  END AS points_per_10000_residents_geographic,
  CASE
    WHEN p.cadastral_area_km2 IS NULL OR p.cadastral_area_km2 = 0 THEN NULL
    ELSE 100.0 * COALESCE(s.source_label_points, 0) / p.cadastral_area_km2
  END AS points_per_100_km2_source_label,
  CASE
    WHEN p.cadastral_area_km2 IS NULL OR p.cadastral_area_km2 = 0 THEN NULL
    ELSE 100.0 * COALESCE(g.geographic_points, 0) / p.cadastral_area_km2
  END AS points_per_100_km2_geographic,
  CASE
    WHEN p.population IS NULL OR p.population = 0 THEN NULL
    WHEN s.source_label_kw IS NULL THEN NULL
    ELSE 1000.0 * s.source_label_kw / p.population
  END AS kw_per_1000_residents_source_label,
  CASE
    WHEN p.population IS NULL OR p.population = 0 THEN NULL
    WHEN g.geographic_kw IS NULL THEN NULL
    ELSE 1000.0 * g.geographic_kw / p.population
  END AS kw_per_1000_residents_geographic,
  CASE
    WHEN pt.known_power_points IS NULL OR pt.known_power_points = 0 THEN NULL
    ELSE 1.0 * pt.high_power_points / pt.known_power_points
  END AS high_power_point_share,
  CASE
    WHEN pt.parsed_validated_points IS NULL OR pt.parsed_validated_points = 0 THEN NULL
    ELSE 1.0 * pt.unknown_power_points / pt.parsed_validated_points
  END AS unknown_power_point_share,
  CASE
    WHEN ot.known_operator_points IS NULL OR ot.known_operator_points = 0 THEN NULL
    ELSE 1.0 * r.largest_operator_points / ot.known_operator_points
  END AS largest_operator_point_share,
  r.largest_operator_name,
  CASE
    WHEN ot.validated_points IS NULL OR ot.validated_points = 0 THEN NULL
    ELSE 1.0 * ot.unknown_operator_points / ot.validated_points
  END AS unknown_operator_point_share,
  CASE
    WHEN COALESCE(s.source_label_points, 0) = 0 THEN NULL
    ELSE 1.0 * COALESCE(g.geographic_points, 0) / s.source_label_points
  END AS geographic_agreement_point_share,
  'EPSG:4326' AS coordinate_crs_assumption,
  'provisional_unverified' AS coordinate_crs_status,
  'cadastral KFL including inland water; not land-only area' AS area_definition
FROM district d
JOIN population p USING (district_code)
LEFT JOIN src s USING (district_code)
LEFT JOIN geo g USING (district_code)
LEFT JOIN incoming inc USING (district_code)
LEFT JOIN conflict c USING (district_code)
LEFT JOIN op_tot ot USING (district_code)
LEFT JOIN op_rank r ON r.district_code = d.district_code AND r.rn = 1
LEFT JOIN pt USING (district_code)
ORDER BY d.district_code;
