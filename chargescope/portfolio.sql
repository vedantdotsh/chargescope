CREATE TEMP VIEW scenario AS
SELECT * FROM (VALUES
  ('registered', 'Registered source-label baseline; cluster retained'),
  ('hypothetical_exclusion', 'Hypothetical exclusion of flagged Tesla coordinate cluster; access unverified')
) AS scenarios(scenario_id, scenario_label);

CREATE TEMP VIEW district_scenario AS
WITH totals AS (
  SELECT s.scenario_id, d.district_code,
    COUNT(i.installation_id) AS installations,
    COALESCE(SUM(i.declared_point_count) FILTER (WHERE i.groups_reconcile), 0) AS known_points,
    COUNT(i.installation_id) FILTER (
      WHERE NOT i.groups_reconcile OR i.declared_point_count IS NULL
    ) AS unknown_point_installations,
    SUM(i.nominal_kw) AS nominal_kw,
    COUNT(i.installation_id) FILTER (WHERE i.nominal_kw IS NULL) AS nominal_kw_missing_n,
    COUNT(i.installation_id) FILTER (WHERE i.assignment_outcome <> 'agreed') AS unresolved_installations,
    COALESCE(SUM(i.declared_point_count) FILTER (
      WHERE i.groups_reconcile AND i.assignment_outcome = 'agreed'), 0) AS agreed_known_points
  FROM district d CROSS JOIN scenario s
  LEFT JOIN installation_snapshot i ON i.label_ars = d.district_code
    AND (s.scenario_id = 'registered' OR NOT i.is_tesla_cluster)
  GROUP BY s.scenario_id, d.district_code
), rates AS (
  SELECT t.*, CASE WHEN unknown_point_installations = 0 THEN known_points END AS points,
    p.population, p.population_date,
    CASE WHEN p.population > 0 AND unknown_point_installations = 0
      THEN 10000.0 * known_points / p.population END AS points_per_10000_residents,
    CASE WHEN d.district_code = '11000' THEN 'Berlin context' ELSE 'Brandenburg' END AS region
  FROM totals t JOIN population p USING (district_code) JOIN district d USING (district_code)
), ranked AS (
  SELECT scenario_id, district_code,
    RANK() OVER (PARTITION BY scenario_id ORDER BY points_per_10000_residents DESC) AS brandenburg_rank
  FROM rates WHERE region = 'Brandenburg' AND points_per_10000_residents IS NOT NULL
)
SELECT rates.*, ranked.brandenburg_rank
FROM rates LEFT JOIN ranked USING (scenario_id, district_code);

CREATE TEMP VIEW region_scenario AS
SELECT scenario_id, region, COUNT(*) AS districts,
  SUM(installations) AS installations, SUM(known_points) AS known_points,
  SUM(unknown_point_installations) AS unknown_point_installations,
  CASE WHEN SUM(unknown_point_installations) = 0 THEN SUM(known_points) END AS points,
  SUM(nominal_kw) AS nominal_kw, SUM(nominal_kw_missing_n) AS nominal_kw_missing_n,
  SUM(unresolved_installations) AS unresolved_installations,
  SUM(agreed_known_points) AS agreed_known_points,
  CASE WHEN COUNT(*) FILTER (WHERE population IS NULL OR population <= 0) = 0
    THEN SUM(population) END AS population,
  CASE WHEN COUNT(*) FILTER (WHERE population IS NULL OR population <= 0) = 0
    AND SUM(unknown_point_installations) = 0
    THEN 10000.0 * SUM(known_points) / SUM(population) END AS points_per_10000_residents
FROM district_scenario GROUP BY scenario_id, region;

CREATE TEMP VIEW evidence_regional_comparison AS
SELECT * FROM region_scenario WHERE scenario_id = 'registered';

CREATE TEMP VIEW evidence_cluster_sensitivity AS
SELECT ds.*, d.district_name FROM district_scenario ds JOIN district d USING (district_code)
WHERE district_code IN (SELECT DISTINCT label_ars FROM installation_snapshot WHERE is_tesla_cluster);

CREATE TEMP VIEW evidence_geography AS
SELECT district_code, installations, points, agreed_known_points, unresolved_installations,
  points - agreed_known_points AS unresolved_known_points
FROM district_scenario WHERE scenario_id = 'registered';
