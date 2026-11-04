(function (root) {
  const values = (district, excluded) => district[excluded ? 'hypothetical' : 'registered'];
  const rank = (districts, district, metric, excluded) => 1 + districts.filter(other => values(other, excluded)[metric] > values(district, excluded)[metric]).length;
  function distribution(districts, excluded) {
    const sorted = districts.map(district => values(district, excluded).rate).sort((first, second) => first - second);
    function quantile(probability) {
      const position = (sorted.length - 1) * probability;
      const lower = Math.floor(position);
      return sorted[lower] + (sorted[Math.min(lower + 1, sorted.length - 1)] - sorted[lower]) * (position - lower);
    }
    const q1 = quantile(.25), median = quantile(.5), q3 = quantile(.75);
    const iqr = q3 - q1;
    const inliers = sorted.filter(value => value >= q1 - 1.5 * iqr && value <= q3 + 1.5 * iqr);
    return { q1, median, q3, iqr, low: inliers[0], high: inliers[inliers.length - 1], outliers: sorted.filter(value => !inliers.includes(value)) };
  }
  function totals(districts, excluded) {
    const result = districts.reduce((total, district) => {
      const row = values(district, excluded);
      for (const key of ['points', 'population', 'kw', 'installations']) total[key] += row[key];
      return total;
    }, { points: 0, population: 0, kw: 0, installations: 0 });
    return { ...result, rate: result.points / result.population * 10000 };
  }
  const api = { values, rank, distribution, totals };
  if (typeof module !== 'undefined') module.exports = api;
  root.ChargeLogic = api;
})(typeof window !== 'undefined' ? window : globalThis);
