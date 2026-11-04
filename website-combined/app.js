(() => {
  const data = window.COMBINED_DATA;
  const logic = window.ChargeLogic;
  const byId = id => document.getElementById(id);
  const state = { focus: '12067', comparison: '12068', metric: 'rate', excluded: false, lang: document.documentElement.lang, theme: document.documentElement.dataset.theme, slide: 0 };
  const copy = {
    en: {
      skip: 'Skip to comparison', language: 'Language', appearance: 'Appearance', light: 'Light', dark: 'Dark', chapters: 'Explore the project', compare: 'Compare', spreadNav: 'See the spread', districts: 'Districts', report: 'The report', location: 'Brandenburg / Germany', headline: 'A number is only the beginning.', deck: 'Compare districts. See the spread. Question one assumption.', focus: 'Focus district', comparison: 'Compare with', measure: 'Comparison measure', rate: 'Resident rate', points: 'Point count', capacity: 'Nominal capacity', reset: 'Reset comparison', scenarioHeading: 'Does one group change the picture?', scenarioDetail: 'Oder-Spree’s 513-point group. Same residents in both scenarios.', exclude: 'Exclude group hypothetically', spreadKicker: '18 districts, one distribution', spreadTitle: 'Where does your district sit?', boxKey: 'Box: middle half; line: median. Each dot is a district.', cohortKicker: 'The whole cohort', cohortTitle: 'Two ways to read the same places.', selectHint: 'Select a district in either chart to connect the view.', countsRates: 'Counts & resident rates', countsHint: 'Sorted by resident rate. More points need not mean a higher rate.', capacityTitle: 'Nominal capacity by district', capacityHint: 'MW · installation capacity counted once. Not delivered energy.', baselineKey: 'Outline: registered baseline · fill: selected scenario', slides: 'Power BI slides', galleryIntro: 'Get the Power BI file below.', galleryNote: 'Report screenshots in English.', gallery: 'Power BI slides. Use arrow keys, Home or End; swipe to browse.', previous: 'Previous slide', next: 'Next slide', further: 'Take the project further', download: 'Download Power BI project', privateAccess: 'Public source project. Pinned data setup required; no preloaded PBIX.', repository: 'View on GitHub', fullSize: 'Open full size', sources: 'Data & attribution', enlarged: 'Enlarged Power BI slide', close: 'Close', registered: 'Registered', hypothetical: 'Hypothetical exclusion', unitRate: 'points / 10,000 residents', unitPoints: 'points', unitCapacity: 'nominal MW', residents: 'residents', installations: 'installation records', rank: 'Rank', of: 'of', higher: 'Higher value ranks first', baseline: 'Registered baseline', scopeOff: 'All charts: registered values · Brandenburg only; Berlin separate.', scopeOn: 'All charts: hypothetical exclusion · registered outlines retained; population unchanged.', berlin: 'Berlin, separate', district: 'District', countShort: 'Points', rateShort: 'Per 10,000 residents', low: 'Lower whisker', q1: 'Lower quartile', median: 'Median', q3: 'Upper quartile', high: 'Upper whisker', outlier: 'Outlier', select: 'Select', spreadAria: 'Box-and-whisker plot of resident rates across 18 Brandenburg districts', dotHint: 'Select a dot; Tab and Enter work too.', original: 'Report screenshot', slide: 'Slide', enlarge: 'Enlarge slide', noOutlier: 'No outliers', outlierSummary: 'Outlier: Oder-Spree', scopeShort: 'Brandenburg · 18 districts'
    },
    de: {
      skip: 'Zum Vergleich springen', language: 'Sprache', appearance: 'Darstellung', light: 'Hell', dark: 'Dunkel', chapters: 'Projekt erkunden', compare: 'Vergleichen', spreadNav: 'Verteilung', districts: 'Kreise', report: 'Der Bericht', location: 'Brandenburg / Deutschland', headline: 'Eine Zahl ist erst der Anfang.', deck: 'Kreise vergleichen. Die Verteilung sehen. Eine Annahme hinterfragen.', focus: 'Kreis im Fokus', comparison: 'Vergleichen mit', measure: 'Kennzahl für den Vergleich', rate: 'Je Einwohner', points: 'Ladepunkte', capacity: 'Nennleistung', reset: 'Vergleich zurücksetzen', scenarioHeading: 'Verändert eine Gruppe das Bild?', scenarioDetail: 'Die Gruppe mit 513 Ladepunkten in Oder-Spree. Gleiche Bevölkerungszahl in beiden Szenarien.', exclude: 'Gruppe hypothetisch ausschließen', spreadKicker: '18 Kreise, eine Verteilung', spreadTitle: 'Wo liegt Ihr Kreis?', boxKey: 'Box: mittlere Hälfte; Linie: Median. Jeder Punkt steht für einen Kreis.', cohortKicker: 'Alle 18 Kreise', cohortTitle: 'Dieselben Orte, zwei Perspektiven.', selectHint: 'Einen Kreis in einer der Grafiken auswählen, um die Ansichten zu verknüpfen.', countsRates: 'Anzahl & Einwohnerbezug', countsHint: 'Nach Ladepunkten je Einwohner sortiert. Mehr Ladepunkte bedeuten nicht immer eine höhere Quote.', capacityTitle: 'Nennleistung nach Kreis', capacityHint: 'MW · Leistung je Installation einmal gezählt. Keine abgegebene Energie.', baselineKey: 'Umriss: Registerstand · Füllung: gewähltes Szenario', slides: 'Power-BI-Folien', galleryIntro: 'Die Power-BI-Datei finden Sie unten.', galleryNote: 'Berichtsaufnahmen auf Englisch.', gallery: 'Power-BI-Folien. Pfeiltasten, Pos1 oder Ende nutzen; zum Blättern wischen.', previous: 'Vorherige Folie', next: 'Nächste Folie', further: 'Das Projekt weiterdenken', download: 'Power-BI-Projekt herunterladen', privateAccess: 'Öffentliches Quellprojekt. Dateneinrichtung nötig; keine vorgeladene PBIX-Datei.', repository: 'Auf GitHub ansehen', fullSize: 'In voller Größe öffnen', sources: 'Daten & Quellen', enlarged: 'Vergrößerte Power-BI-Folie', close: 'Schließen', registered: 'Registerstand', hypothetical: 'Hypothetischer Ausschluss', unitRate: 'Ladepunkte je 10.000 Einwohner', unitPoints: 'Ladepunkte', unitCapacity: 'MW Nennleistung', residents: 'Einwohner', installations: 'Installationsdatensätze', rank: 'Rang', of: 'von', higher: 'Höherer Wert steht vorn', baseline: 'Registerstand als Referenz', scopeOff: 'Alle Grafiken: Registerstand · nur Brandenburg; Berlin separat.', scopeOn: 'Alle Grafiken: hypothetischer Ausschluss · Registerstand als Umriss; Bevölkerungszahl unverändert.', berlin: 'Berlin, separat', district: 'Kreis', countShort: 'Ladepunkte', rateShort: 'Je 10.000 Einwohner', low: 'Unterer Whisker', q1: 'Unteres Quartil', median: 'Median', q3: 'Oberes Quartil', high: 'Oberer Whisker', outlier: 'Ausreißer', select: 'Auswählen', spreadAria: 'Boxplot der Ladepunkte je Einwohner in 18 brandenburgischen Kreisen', dotHint: 'Einen Punkt auswählen; auch mit Tab und Eingabe.', original: 'Berichtsaufnahme', slide: 'Folie', enlarge: 'Folie vergrößern', noOutlier: 'Keine Ausreißer', outlierSummary: 'Ausreißer: Oder-Spree', scopeShort: 'Brandenburg · 18 Kreise'
    }
  };
  const text = key => copy[state.lang][key];
  const escape = value => String(value).replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character]));
  const number = (value, decimals = 0) => new Intl.NumberFormat(state.lang === 'de' ? 'de-DE' : 'en-GB', { minimumFractionDigits: decimals, maximumFractionDigits: decimals }).format(value);
  const district = code => data.districts.find(item => item.code === code);
  const current = item => logic.values(item, state.excluded);
  const scenarioName = () => text(state.excluded ? 'hypothetical' : 'registered');
  const measureValue = (row, metric) => metric === 'kw' ? row.kw / 1000 : row[metric];
  const megawatts = kw => number(kw / 1000, Number.isInteger(kw) ? 3 : 4);
  const measureFormat = (row, metric) => metric === 'kw' ? megawatts(row.kw) : number(measureValue(row, metric), metric === 'points' ? 0 : 1);
  const measureUnit = metric => text(metric === 'rate' ? 'unitRate' : metric === 'kw' ? 'unitCapacity' : 'unitPoints');
  const maximum = metric => ({ rate: 50, points: 900, kw: 45 }[metric]);
  let returnFocus = null;
  let modalSlide = 0;
  function save(key, value) { try { localStorage.setItem('chargescope-' + key, value); } catch {} }
  function describe(item) {
    const row = current(item);
    return item.name + '\n' + scenarioName() + ' · ' + number(row.points) + ' ' + text('unitPoints') + ' · ' + number(row.rate, 1) + ' ' + text('unitRate') + '\n' + megawatts(row.kw) + ' ' + text('unitCapacity') + ' · ' + number(row.population) + ' ' + text('residents') + '\n' + text('baseline') + ': ' + number(item.registered.points) + ' ' + text('unitPoints') + ' · ' + number(item.registered.rate, 1) + ' ' + text('unitRate') + ' · ' + megawatts(item.registered.kw) + ' MW';
  }
  function translate() {
    document.documentElement.lang = state.lang;
    document.documentElement.dataset.theme = state.theme;
    document.querySelectorAll('[data-i18n]').forEach(element => { element.textContent = text(element.dataset.i18n); });
    document.querySelectorAll('[data-label]').forEach(element => element.setAttribute('aria-label', text(element.dataset.label)));
    document.querySelectorAll('[data-locale]').forEach(button => {
      button.setAttribute('aria-pressed', button.dataset.locale === state.lang);
      button.setAttribute('aria-label', button.dataset.locale === 'en' ? 'English' : 'Deutsch');
    });
    document.querySelectorAll('[data-theme-choice]').forEach(button => {
      button.setAttribute('aria-pressed', button.dataset.themeChoice === state.theme);
      button.setAttribute('aria-label', text(button.dataset.themeChoice));
    });
    const slides = [...byId('gallery').children];
    slides.forEach((button, index) => {
      button.setAttribute('aria-label', text('enlarge') + ' ' + number(index + 1));
      button.querySelector('img').alt = text('original') + ' · ' + text('slide') + ' ' + number(index + 1);
    });
    updateGallery();
    if (byId('lightbox').open) updateModal();
  }
  function renderInstrument() {
    byId('instrument').dataset.measure = state.metric;
    byId('instrument').innerHTML = '<div class="instrument-top"><span>' + escape(scenarioName()) + '</span><span>' + text('higher') + '</span></div>' + [state.focus, state.comparison].map((code, index) => {
      const item = district(code), row = current(item), baseline = item.registered;
      const rank = logic.rank(data.districts, item, state.metric, state.excluded);
      return '<div class="lane" data-lane="' + index + '"><div class="lane-top"><span>' + text(index ? 'comparison' : 'focus') + '</span><span data-rank="' + rank + '">' + text('rank') + ' ' + number(rank) + ' / 18</span></div><h3>' + escape(item.name) + '</h3><div class="readout"><strong data-value="' + measureValue(row, state.metric) + '">' + measureFormat(row, state.metric) + '</strong><span>' + measureUnit(state.metric) + '</span></div><div class="bench-track" aria-hidden="true"><span class="bench-fill" style="width:' + measureValue(row, state.metric) / maximum(state.metric) * 100 + '%"></span><span class="bench-baseline" style="width:' + measureValue(baseline, state.metric) / maximum(state.metric) * 100 + '%"></span></div><div class="bench-scale" aria-hidden="true"><span>0</span><span>' + number(maximum(state.metric)) + '</span></div><p class="registered-note">' + text('registered') + ': ' + measureFormat(baseline, state.metric) + ' · ' + number(row.population) + ' ' + text('residents') + '</p></div>';
    }).join('');
  }
  function renderBox() {
    const stats = logic.distribution(data.districts, state.excluded);
    const baseline = logic.distribution(data.districts, false);
    const width = Math.max(280, byId('boxplot').clientWidth - 28);
    const scale = value => 20 + value / 50 * (width - 40);
    const sorted = [...data.districts].sort((first, second) => current(first).rate - current(second).rate);
    const rows = [];
    const dots = sorted.map(item => {
      const value = current(item).rate, position = scale(value);
      let rowIndex = 0;
      while (rows[rowIndex]?.some(other => Math.abs(other - position) < 25)) rowIndex++;
      (rows[rowIndex] ||= []).push(position);
      const selected = item.code === state.focus;
      const comparing = item.code === state.comparison && !selected;
      return '<g class="' + (comparing ? 'is-comparison' : '') + '" role="button" tabindex="0" data-select="' + item.code + '" aria-pressed="' + selected + '" aria-label="' + escape(text('select') + ': ' + describe(item) + (comparing ? '\n' + text('comparison') : '')) + '" data-tip="' + escape(describe(item)) + '"><circle class="hit" cx="' + position + '" cy="' + (164 + rowIndex * 26) + '" r="13"/><circle class="dot' + (selected ? ' is-selected' : '') + (stats.outliers.includes(value) ? ' is-outlier' : '') + '" cx="' + position + '" cy="' + (164 + rowIndex * 26) + '" r="' + (selected ? 6 : 4.5) + '" pointer-events="none"/></g>';
    }).join('');
    const height = 192 + (rows.length - 1) * 26;
    const baselineShape = state.excluded ? '<g class="baseline" aria-hidden="true"><path d="M' + scale(baseline.low) + ',58V112 M' + scale(baseline.low) + ',85H' + scale(baseline.high) + ' M' + scale(baseline.high) + ',58V112"/><rect x="' + scale(baseline.q1) + '" y="54" width="' + (scale(baseline.q3) - scale(baseline.q1)) + '" height="62"/></g>' : '';
    byId('boxplot').innerHTML = '<svg class="boxplot" style="height:auto" viewBox="0 0 ' + width + ' ' + height + '" role="group" aria-label="' + text('spreadAria') + '"><text x="20" y="20">' + measureUnit('rate') + '</text>' + [0,10,20,30,40,50].map(tick => '<line class="grid" x1="' + scale(tick) + '" x2="' + scale(tick) + '" y1="43" y2="124"/><text text-anchor="middle" x="' + scale(tick) + '" y="141">' + number(tick) + '</text>').join('') + baselineShape + '<path class="whisker" d="M' + scale(stats.low) + ',68V102 M' + scale(stats.low) + ',85H' + scale(stats.high) + ' M' + scale(stats.high) + ',68V102"/><rect class="box" x="' + scale(stats.q1) + '" y="62" width="' + (scale(stats.q3) - scale(stats.q1)) + '" height="46"/><line class="median" x1="' + scale(stats.median) + '" x2="' + scale(stats.median) + '" y1="62" y2="108"/>' + dots + '</svg><p class="chart-caption">' + text(stats.outliers.length ? 'outlierSummary' : 'noOutlier') + ' · ' + text('dotHint') + '</p>';
    byId('boxplot').dataset.statistics = JSON.stringify(stats);
    byId('quartiles').innerHTML = ['low','q1','median','q3','high'].map(key => '<div><p>' + text(key) + '</p><strong data-stat="' + key + '">' + number(stats[key], 1) + '</strong></div>').join('');
  }
  function bar(row, baseline, metric) {
    return '<span class="bar-cell"><span class="bar-baseline" aria-hidden="true" style="width:' + measureValue(baseline, metric) / maximum(metric) * 100 + '%"></span><span class="bar-fill" aria-hidden="true" style="width:' + measureValue(row, metric) / maximum(metric) * 100 + '%"></span><span class="bar-value" data-value="' + measureValue(row, metric) + '">' + measureFormat(row, metric) + '</span></span>';
  }
  function renderCohort(target, metric) {
    const capacity = metric === 'kw';
    const sorted = [...data.districts].sort((first, second) => current(second)[metric] - current(first)[metric]);
    const header = '<div class="chart-head' + (capacity ? ' capacity-head' : '') + '"><span>' + text('district') + '</span>' + (capacity ? '<span>' + text('unitCapacity') + ' · 0–45</span>' : '<span>' + text('countShort') + ' · 0–900</span><span>' + text('rateShort') + ' · 0–50</span>') + '</div>';
    byId(target).innerHTML = header + sorted.map(item => {
      const selected = item.code === state.focus;
      const comparing = item.code === state.comparison && !selected;
      const description = text('select') + ': ' + describe(item) + (comparing ? '\n' + text('comparison') : '');
      return '<button class="district-row' + (capacity ? ' capacity-row' : '') + (selected ? ' is-selected' : '') + (comparing ? ' is-comparison' : '') + '" type="button" data-select="' + item.code + '" data-tip="' + escape(describe(item)) + '" aria-label="' + escape(description) + '" aria-pressed="' + selected + '"><span class="district-name">' + escape(item.name) + '</span>' + (capacity ? bar(current(item), item.registered, 'kw') : bar(current(item), item.registered, 'points') + bar(current(item), item.registered, 'rate')) + '</button>';
    }).join('');
  }
  function render() {
    const active = document.activeElement;
    const selectedFocus = active?.dataset.select;
    const focusArea = active?.closest('#boxplot, #counts-rates, #capacity')?.id;
    byId('tooltip').hidden = true;
    translate();
    byId('focus').value = state.focus;
    byId('comparison').value = state.comparison;
    byId('scenario').checked = state.excluded;
    document.querySelectorAll('[data-metric]').forEach(button => button.setAttribute('aria-pressed', button.dataset.metric === state.metric));
    renderInstrument(); renderBox(); renderCohort('counts-rates', 'rate'); renderCohort('capacity', 'kw');
    byId('scope').textContent = text(state.excluded ? 'scopeOn' : 'scopeOff');
    document.querySelectorAll('.scenario-badge').forEach(element => { element.textContent = scenarioName(); });
    const total = logic.totals(data.districts, state.excluded), berlin = data.berlin;
    byId('regional').innerHTML = '<span><strong>Brandenburg: ' + number(total.points) + ' ' + text('unitPoints') + '</strong> · ' + number(total.rate, 1) + ' / ' + number(10000) + '</span><span>' + text('berlin') + ': ' + number(berlin.points) + ' ' + text('unitPoints') + ' · ' + number(berlin.rate, 1) + ' / ' + number(10000) + '</span>';
    const item = district(state.focus), row = current(item);
    byId('selection-detail').innerHTML = '<div><h3>' + escape(item.name) + ' · ' + text('rank') + ' ' + number(logic.rank(data.districts, item, 'rate', state.excluded)) + ' / 18</h3><p>' + number(row.points) + ' ' + text('unitPoints') + ' · ' + number(row.population) + ' ' + text('residents') + ' · ' + megawatts(row.kw) + ' MW · ' + number(row.installations) + ' ' + text('installations') + '</p></div><strong>' + number(row.rate, 1) + ' / ' + number(10000) + '</strong>';
    document.dispatchEvent(new CustomEvent('chargescope-render', { detail: { ...state } }));
    if (selectedFocus && focusArea) byId(focusArea).querySelector('[data-select="' + selectedFocus + '"]')?.focus({ preventScroll: true });
  }
  function updateGallery() {
    byId('gallery-counter').textContent = number(state.slide + 1) + ' / ' + number(data.gallery.length);
    byId('gallery-prev').disabled = state.slide === 0;
    byId('gallery-next').disabled = state.slide === data.gallery.length - 1;
  }
  function goToSlide(index) {
    state.slide = Math.max(0, Math.min(data.gallery.length - 1, index));
    const slide = byId('gallery').children[state.slide];
    byId('gallery').scrollTo({ left: slide.offsetLeft - byId('gallery').children[0].offsetLeft, behavior: matchMedia('(prefers-reduced-motion:reduce)').matches ? 'instant' : 'smooth' });
    updateGallery();
  }
  function updateModal() {
    const item = data.gallery[modalSlide];
    byId('modal-image').src = item.src;
    byId('modal-full-size').href = item.src;
    byId('modal-image').alt = text('original') + ' · ' + text('slide') + ' ' + number(modalSlide + 1);
    byId('modal-counter').textContent = number(modalSlide + 1) + ' / ' + number(data.gallery.length);
    byId('modal-prev').disabled = modalSlide === 0;
    byId('modal-next').disabled = modalSlide === data.gallery.length - 1;
  }
  for (const id of ['focus','comparison']) {
    byId(id).innerHTML = data.districts.map(item => '<option value="' + item.code + '">' + escape(item.name) + '</option>').join('');
    byId(id).addEventListener('change', event => { state[id] = event.target.value; render(); });
  }
  byId('gallery').innerHTML = data.gallery.map((item, index) => '<button type="button" class="slide" data-slide="' + index + '"><img src="' + (item.thumbnail || item.src) + '" alt="" width="' + item.width + '" height="' + item.height + '" loading="lazy"></button>').join('');
  document.addEventListener('click', event => {
    const button = event.target.closest('button,[data-select]');
    if (!button) return;
    if (button.dataset.select) { state.focus = button.dataset.select; render(); }
    if (button.dataset.metric) { state.metric = button.dataset.metric; render(); }
    if (button.dataset.locale) { state.lang = button.dataset.locale; save('lang', state.lang); render(); }
    if (button.dataset.themeChoice) { state.theme = button.dataset.themeChoice; save('theme', state.theme); render(); }
    if (button.dataset.slide !== undefined) {
      modalSlide = Number(button.dataset.slide); returnFocus = button;
      updateModal(); byId('lightbox').showModal(); byId('modal-close').focus();
    }
  });
  byId('boxplot').addEventListener('keydown', event => {
    if ((event.key === 'Enter' || event.key === ' ') && event.target.dataset.select) { event.preventDefault(); state.focus = event.target.dataset.select; render(); }
  });
  byId('scenario').addEventListener('change', event => { state.excluded = event.target.checked; render(); });
  byId('reset').addEventListener('click', () => { Object.assign(state, { focus: '12067', comparison: '12068', metric: 'rate', excluded: false }); render(); });
  byId('gallery-prev').addEventListener('click', () => goToSlide(state.slide - 1));
  byId('gallery-next').addEventListener('click', () => goToSlide(state.slide + 1));
  byId('gallery').addEventListener('keydown', event => {
    if (!['ArrowLeft','ArrowRight','Home','End'].includes(event.key)) return;
    event.preventDefault();
    goToSlide(event.key === 'Home' ? 0 : event.key === 'End' ? data.gallery.length - 1 : state.slide + (event.key === 'ArrowRight' ? 1 : -1));
  });
  byId('gallery').addEventListener('scroll', () => {
    const gallery = byId('gallery'), first = gallery.children[0];
    const step = gallery.children[1].offsetLeft - first.offsetLeft;
    state.slide = Math.max(0, Math.min(data.gallery.length - 1, Math.round(gallery.scrollLeft / step)));
    updateGallery();
  }, { passive: true });
  byId('modal-close').addEventListener('click', () => byId('lightbox').close());
  let touchStart;
  byId('modal-image').addEventListener('touchstart', event => { touchStart = event.changedTouches[0]; }, { passive: true });
  byId('modal-image').addEventListener('touchend', event => {
    if (!touchStart) return;
    const end = event.changedTouches[0], distance = end.clientX - touchStart.clientX;
    if (Math.abs(distance) > 48 && Math.abs(distance) > Math.abs(end.clientY - touchStart.clientY)) {
      modalSlide = Math.max(0, Math.min(data.gallery.length - 1, modalSlide + (distance < 0 ? 1 : -1)));
      updateModal();
    }
    touchStart = undefined;
  }, { passive: true });
  byId('lightbox').addEventListener('close', () => { returnFocus?.focus({ preventScroll: true }); });
  for (const [id, direction] of [['modal-prev', -1], ['modal-next', 1]]) byId(id).addEventListener('click', () => { modalSlide += direction; updateModal(); });
  byId('lightbox').addEventListener('keydown', event => {
    if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) {
      event.preventDefault();
      modalSlide = event.key === 'Home' ? 0 : event.key === 'End' ? data.gallery.length - 1 : Math.max(0, Math.min(data.gallery.length - 1, modalSlide + (event.key === 'ArrowRight' ? 1 : -1)));
      updateModal();
    }
    if (event.key !== 'Tab') return;
    const buttons = [...byId('lightbox').querySelectorAll('button:not(:disabled),a[href]')];
    if (event.shiftKey && document.activeElement === buttons[0]) { event.preventDefault(); buttons.at(-1).focus(); }
    if (!event.shiftKey && document.activeElement === buttons.at(-1)) { event.preventDefault(); buttons[0].focus(); }
  });
  function tooltip(event) {
    const target = event.target.closest('[data-tip]');
    const tip = byId('tooltip');
    if (!target) { tip.hidden = true; return; }
    tip.textContent = target.dataset.tip;
    tip.hidden = false;
    const bounds = target.getBoundingClientRect();
    const left = event.clientX || bounds.left + bounds.width / 2;
    const top = event.clientY || bounds.top;
    tip.style.left = Math.max(12, Math.min(innerWidth - tip.offsetWidth - 12, left + 12)) + 'px';
    tip.style.top = Math.max(12, Math.min(innerHeight - tip.offsetHeight - 12, top + 15)) + 'px';
  }
  document.addEventListener('pointerover', tooltip);
  document.addEventListener('focusin', tooltip);
  document.addEventListener('pointerout', event => { if (!event.relatedTarget?.closest?.('[data-tip]')) byId('tooltip').hidden = true; });
  document.addEventListener('focusout', () => { byId('tooltip').hidden = true; });
  document.addEventListener('keydown', event => { if (event.key === 'Escape') byId('tooltip').hidden = true; });
  window.addEventListener('scroll', () => {
    const target = document.activeElement?.closest('[data-tip]');
    if (target) tooltip({ target });
    else byId('tooltip').hidden = true;
  }, { passive: true });
  let boxWidth = 0;
  new ResizeObserver(entries => {
    const width = entries[0].contentRect.width;
    if (Math.abs(width - boxWidth) > 1) { boxWidth = width; renderBox(); }
  }).observe(byId('boxplot'));
  render();
})();
