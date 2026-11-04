(() => {
  const byId = id => document.getElementById(id);
  const words = {
    en: {
      read: 'Read the findings', title: 'What does this analysis conclude?', close: 'Close findings',
      intro: 'This is a supply comparison, not a plan for new chargers. It covers 18 Brandenburg districts. Berlin stays separate. The register and population have different reference dates. They do not show change over time.',
      columns: ['Finding', 'Meaning', 'Next check'],
      findings: [
        ['Counts and rates answer different questions.', 'Potsdam-Mittelmark has 406 points and 18.3 per 10,000 residents. Ostprignitz-Ruppin has 245 points and 24.8. More points do not mean a higher resident rate.', 'Compare both measures before you rank places.'],
        ['One group changes the leading district.', 'Oder-Spree has 832 points and 46.4 per 10,000 residents. Remove the 513-point group hypothetically: 319 points, 17.8 per 10,000, rank 11 instead of 1. Residents stay fixed. This tests an assumption; it does not correct the register.', 'Check public access to this group.'],
        ['Capacity is not use.', 'Dahme-Spreewald has 42.922 nominal MW. Each installation counts once. This does not show delivered energy, queues, demand or spare capacity.', 'Get usage and access records before you suggest new supply.'],
        ['Some locations still need a check.', 'Geographical agreement is unresolved for 35 Brandenburg points. These district totals are diagnostic, not national validation.', 'Check these locations against source records.']
      ],
      active: 'Active view', versus: 'compared with', baseline: 'Registered', scenario: 'Hypothetical exclusion', all: 'All 18 districts stay visible', profile: 'District profile', profileNote: 'Select a place. Keep the whole region in view.', points: 'Points', rate: 'Per 10,000 residents', capacity: 'Nominal MW', rank: 'Resident-rate rank', residents: 'Residents', guide: 'Start with a question.', guideNote: 'Choose a finding, then test it in the charts.', actions: ['Compare counts and rates', 'Test the 513-point group', 'Compare nominal capacity'], workbench: 'The comparison workbench.', workbenchNote: 'Choose two districts. See how each measure changes the comparison.', profileHeadline: 'One place. The full picture.', profileDeck: 'Start with a district. Compare it with the rest.', guideHeadline: 'Read a finding. Test the numbers.', guideDeck: 'Follow a question from the report into the data.'
    },
    de: {
      read: 'Ergebnisse lesen', title: 'Was ergibt diese Analyse?', close: 'Ergebnisse schließen',
      intro: 'Dies ist ein Vergleich des Angebots, kein Ausbauplan. Er umfasst 18 Kreise in Brandenburg. Berlin bleibt getrennt. Register und Bevölkerung haben verschiedene Stichtage. Sie zeigen keine zeitliche Entwicklung.',
      columns: ['Ergebnis', 'Bedeutung', 'Nächster Schritt'],
      findings: [
        ['Anzahl und Quote beantworten andere Fragen.', 'Potsdam-Mittelmark hat 406 Ladepunkte und 18,3 je 10.000 Einwohner. Ostprignitz-Ruppin hat 245 Ladepunkte und 24,8. Mehr Ladepunkte bedeuten keine höhere Quote.', 'Beide Kennzahlen vor einer Rangfolge vergleichen.'],
        ['Eine Gruppe verändert die Spitze.', 'Oder-Spree hat 832 Ladepunkte und 46,4 je 10.000 Einwohner. Ohne die Gruppe mit 513 Punkten, rein hypothetisch: 319 Punkte, 17,8 je 10.000, Rang 11 statt 1. Die Bevölkerung bleibt gleich. Dies prüft eine Annahme, nicht die Richtigkeit des Registers.', 'Den öffentlichen Zugang zu dieser Gruppe prüfen.'],
        ['Leistung ist keine Nutzung.', 'Dahme-Spreewald hat 42,922 MW Nennleistung. Jede Installation zählt einmal. Das zeigt weder gelieferte Energie noch Warteschlangen, Bedarf oder freie Kapazität.', 'Vor Ausbauvorschlägen Nutzungs- und Zugangsdaten beschaffen.'],
        ['Einige Orte brauchen eine Prüfung.', 'Für 35 Brandenburger Ladepunkte ist die geografische Übereinstimmung ungeklärt. Die Kreissummen dienen der Prüfung, nicht einer bundesweiten Freigabe.', 'Diese Orte mit den Quelldaten abgleichen.']
      ],
      active: 'Aktive Ansicht', versus: 'im Vergleich mit', baseline: 'Registerstand', scenario: 'Hypothetischer Ausschluss', all: 'Alle 18 Kreise bleiben sichtbar', profile: 'Kreisprofil', profileNote: 'Einen Ort wählen. Die ganze Region im Blick behalten.', points: 'Ladepunkte', rate: 'Je 10.000 Einwohner', capacity: 'Nennleistung in MW', rank: 'Rang nach Einwohnerquote', residents: 'Einwohner', guide: 'Mit einer Frage beginnen.', guideNote: 'Ein Ergebnis wählen, dann in den Grafiken prüfen.', actions: ['Anzahl und Quote vergleichen', 'Die Gruppe mit 513 Punkten prüfen', 'Nennleistung vergleichen'], workbench: 'Der Vergleichsplatz.', workbenchNote: 'Zwei Kreise wählen. Den Vergleich mit jeder Kennzahl prüfen.', profileHeadline: 'Ein Ort. Das ganze Bild.', profileDeck: 'Mit einem Kreis beginnen. Mit der Region vergleichen.', guideHeadline: 'Ergebnis lesen. Zahlen prüfen.', guideDeck: 'Eine Frage aus dem Bericht in den Daten verfolgen.'
    }
  };
  const launcher = document.createElement('button');
  launcher.type = 'button'; launcher.id = 'findings-open'; launcher.className = 'findings-open';
  launcher.setAttribute('aria-haspopup', 'dialog'); launcher.setAttribute('aria-controls', 'findings');
  launcher.setAttribute('aria-expanded', 'false');
  const drawer = document.createElement('dialog'); drawer.id = 'findings'; drawer.className = 'findings';
  drawer.setAttribute('aria-labelledby', 'findings-title');
  drawer.innerHTML = '<header><h2 id="findings-title"></h2><button id="findings-close" type="button" autofocus></button></header><p id="findings-intro"></p><div id="findings-rows"></div>';
  document.body.append(launcher, drawer);
  const active = document.createElement('div'); active.id = 'active-view'; active.className = 'active-view';
  active.setAttribute('role', 'status'); active.setAttribute('aria-live', 'polite');
  byId('compare').after(active);
  const variant = document.body.dataset.design || 'current';
  if (variant === 'profile') {
    const profile = document.createElement('section'); profile.id = 'profile-card'; profile.className = 'profile-card';
    byId('compare').after(profile);
    profile.append(byId('instrument'));
    const heading = document.createElement('div'); heading.id = 'profile-heading'; profile.prepend(heading);
  }
  if (variant === 'guided') {
    const guide = document.createElement('section'); guide.id = 'guided-start'; guide.className = 'guided-start';
    byId('compare').before(guide);
  }
  if (variant === 'workbench') {
    const grid = document.createElement('div'); grid.className = 'workbench-grid';
    byId('spread').before(grid); grid.append(byId('spread'), byId('districts'));
  }
  function update(state) {
    const language = state.lang, copy = words[language];
    const format = (value, decimals = 0) => new Intl.NumberFormat(language === 'de' ? 'de-DE' : 'en-GB', { maximumFractionDigits: decimals, minimumFractionDigits: decimals }).format(value);
    const selected = window.COMBINED_DATA.districts.find(item => item.code === state.focus);
    const comparison = window.COMBINED_DATA.districts.find(item => item.code === state.comparison);
    const row = window.ChargeLogic.values(selected, state.excluded);
    launcher.textContent = copy.read; launcher.title = copy.title;
    byId('findings-title').textContent = copy.title;
    byId('findings-close').textContent = copy.close;
    byId('findings-intro').textContent = copy.intro;
    byId('findings-rows').innerHTML = copy.findings.map(finding => '<article class="finding-row"><h3>' + finding[0] + '</h3><p>' + finding[1] + '</p><p class="next-check"><strong>' + copy.columns[2] + ': </strong>' + finding[2] + '</p></article>').join('');
    active.textContent = copy.active + ': ' + selected.name + ' / ' + comparison.name + ' · ' + copy[state.metric === 'kw' ? 'capacity' : state.metric] + ' · ' + copy[state.excluded ? 'scenario' : 'baseline'] + '. ' + copy.all + '.';
    if (variant !== 'current') {
      byId('compare').querySelector('h1').textContent = copy[variant === 'workbench' ? 'workbench' : variant === 'profile' ? 'profileHeadline' : 'guideHeadline'];
      byId('compare').querySelector('.deck').textContent = copy[variant === 'workbench' ? 'workbenchNote' : variant === 'profile' ? 'profileDeck' : 'guideDeck'];
    }
    if (variant === 'profile') {
      byId('profile-heading').innerHTML = '<p class="section-index">' + copy.profile + '</p><h2>' + selected.name + '</h2><p>' + copy.profileNote + '</p><dl class="profile-stats">' + [['points', row.points, 0], ['rate', row.rate, 1], ['capacity', row.kw / 1000, Number.isInteger(row.kw) ? 3 : 4], ['rank', window.ChargeLogic.rank(window.COMBINED_DATA.districts, selected, 'rate', state.excluded), 0]].map(([key, value, decimals]) => '<div><dt>' + copy[key] + '</dt><dd>' + format(value, decimals) + (key === 'rank' ? ' / 18' : '') + '</dd></div>').join('') + '</dl>';
    }
    if (variant === 'guided') {
      byId('guided-start').innerHTML = '<div><p class="section-index">ChargeScope / Brandenburg</p><h2>' + copy.guide + '</h2><p>' + copy.guideNote + '</p></div><div class="guide-choices">' + copy.actions.map((label, index) => '<button type="button" data-question="' + index + '"><span>' + ['406 / 245', '832 → 319', '42.922 MW'][index] + '</span>' + label + '<b aria-hidden="true">↗</b></button>').join('') + '</div>';
      byId('guided-start').querySelector('[data-question="2"] span').textContent = format(42.922, 3) + ' MW';
    }
  }
  document.addEventListener('chargescope-render', event => update(event.detail));
  launcher.addEventListener('click', () => { drawer.showModal(); drawer.scrollTop = 0; launcher.setAttribute('aria-expanded', 'true'); byId('findings-close').focus(); });
  drawer.addEventListener('keydown', event => {
    if (event.key === 'Tab') { event.preventDefault(); byId('findings-close').focus(); }
  });
  byId('findings-close').addEventListener('click', () => drawer.close());
  drawer.addEventListener('close', () => { launcher.setAttribute('aria-expanded', 'false'); launcher.focus({ preventScroll: true }); });
  let outsideStart = false;
  const outside = event => { const bounds = drawer.getBoundingClientRect(); return event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom; };
  drawer.addEventListener('pointerdown', event => { outsideStart = event.target === drawer && outside(event); });
  drawer.addEventListener('click', event => { if (outsideStart && event.target === drawer && outside(event)) drawer.close(); outsideStart = false; });
  document.addEventListener('click', event => {
    const question = event.target.closest('[data-question]');
    if (!question) return;
    const index = Number(question.dataset.question);
    byId('reset').click();
    const focus = byId('focus'), comparison = byId('comparison');
    focus.value = ['12069', '12067', '12061'][index]; focus.dispatchEvent(new Event('change'));
    comparison.value = ['12068', '12068', '12065'][index]; comparison.dispatchEvent(new Event('change'));
    document.querySelector('[data-metric="' + (index === 2 ? 'kw' : index === 0 ? 'points' : 'rate') + '"]').click();
    if (index === 1) { byId('scenario').checked = true; byId('scenario').dispatchEvent(new Event('change')); }
    byId('focus').focus({ preventScroll: true }); byId('compare').scrollIntoView({ behavior: 'instant' });
  });
})();
