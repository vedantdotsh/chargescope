// ChargeScope · a four-step argument: each step a heading, then its framed chart, then (below 1180 px) its story; on wide screens the story of the step in view sits in a side rail.
// After the four steps: what this means and about this project (static, no frame, camera or connector), then the supporting charts to explore (frames at rest).
(function(){
'use strict';
const K=window.K,{N,t,f,pct,date,esc,fill,ABBR}=K,G=N.germany,ST=N.states,DI=N.districts,BB=N.brandenburg;
K.words({v:{kick:'A data analysis of Germany’s public charging register',title:'When can you trust a charging-point ranking?',docTitle:'ChargeScope · When can you trust a charging-point ranking?',
 lead:'Oder-Spree ranks {a} of {districtCount} German districts for charging points per resident. Set aside every district’s largest single-site group (here {g} points) and re-rank: it ranks {b}.',
 lead2:'Four checks on {pts} registered points show which regional comparisons hold up.',scope:'Register {reg} · residents {pop}',
 figCap:'Oder-Spree: rank among {districtCount} German districts by charging points per resident',figA:'as registered',figB:'with every district’s largest single-site group set aside (here {g} points)',cue:'Scroll for the four checks',
 steps:['Step 1 of 4','Step 2 of 4','Step 3 of 4 · Brandenburg','Step 4 of 4'],kind:{city:'city',county:'county'},
 h2:'The most points is not the highest rate.',p2:'A count mostly measures how big a state is. Dividing by residents makes states comparable.',leg2:'Highlighted: Brandenburg and Berlin, used in Step 3.',
 h5:'A state’s rate hides its districts.',p5:'State rates run from {smin} to {smax} per 10,000. District rates run from {dmin} to {dmax}.',leg5:'○ Needs a check: a small count, one dominant site, or a location mismatch.',
 h7:'In Brandenburg, rank {bbRank} rests on one registered group.',p7:'{g} of Oder-Spree’s {p} points ({sh}) are single-point {kw} kW records registered to Tesla Manufacturing Brandenburg SE in Grünheide (Mark), at one coordinate.',leg7:'Single-site group: records from one operator at one coordinate. The register does not establish who can use each charger today; in February 2024 Tesla described its factory car-park chargers as public and free ({method}).',
 h8:'It is not only Oder-Spree.',p8:'Set aside each district’s largest single-site group and {n} of {districtCount} districts move {k} or more places.',
 wKick:'What this means',wH:'Use a ranking to decide where to look, not what to conclude.',
 wF:[['Counts and rates rank states differently.','{top} has the most points and ranks {r} of {stateCount} by rate.'],['Averages hide the spread.','District rates differ {x}-fold; state rates about {y}-fold.'],['One site can carry a rank.','{n} of {districtCount} districts move {k}+ places when their largest single-site group is set aside.']],
 wRec:'Before briefing a regional ranking: show counts beside rates, and check any district where one site holds a large share of the points.',wLim:'This measures registered supply only, not demand, use or access.',
 aKick:'About this project',aH:'How it was made',aL:['Data: Bundesnetzagentur charging register ({reg}, {inst} records) and BKG population by district ({pop}).','Pipeline: Python reconciles installations, points and connectors; DuckDB SQL computes report metrics. The website uses a separate, tested Python aggregation.','Report: a four-page Power BI case study on Brandenburg’s {bbCount} districts.'],
 xKick:'Explore the data',xH:'More from the register',xP:'Supporting views. They are not part of the argument above.',
 h1:'Where the points are',p1:'Arc length is registered points. Inner ring: states. Outer ring: districts.',
 h3:'Residents and points by district',p3:'{districtCount} districts on log scales. Diagonals mark equal rates.',
 h4:'Charging power by state',p4:'Highest connector power per point.',
 h6:'Points per installation',p6:'{share} of {n} installations have one or two points. An installation is one register record, not necessarily one site.',
 u1:'Registered points, {reg}',u3:'Residents ({pop}) and registered points, log scales',u4:'Share of registered points by highest connector power',
 u5:'Points per 10,000 residents, by district',u7:'Brandenburg’s {bbCount} districts · Berlin separate',u8:'Rank among {districtCount} districts, points per 10,000 residents',
 unitPts:'Registered points',unitRate:'Points per 10,000 residents ({pop})',unitInst:'Installations, by number of points',unitIp:'Points, by installation size',
 stateSel:'State',allStates:'Germany, all states',distSel:'District',noDist:'Choose a district',
 m2:[['points','Points'],['rate','Per 10,000 residents']],rkP:'rank {k} by points',rkR:['rank {k} by rate, the same as by points','rank {k} by rate, up {d} from rank {p} by points','rank {k} by rate, down {d} from rank {p} by points'],m5:[['all','All districts'],['flag','Needs a check ({n})']],m6:[['inst','Installations'],['pts','Points']],m8:[['20','20+ places ({n})'],['50','50+ places ({n})']],
 scenario:'Hypothetical scenario',registered:'As registered',without:'Without that group',view:'View',
 germany:'Germany',points:'points',perTen:'per 10,000',
 ctr:['registered points','{i} installations','{mw} MW nominal'],
 r1:'{name}: {pts} points ({share} of Germany) · {inst} installations · {mw} MW nominal',r1g:'Germany: {pts} points · {inst} installations · {mw} MW nominal',r1h:' · {h} points have no district match',
 r2s:'{name} · rank {a} of {stateCount} by points · rank {b} of {stateCount} by rate',
 r3g:'{districtCount} districts · median {med} per 10,000 · middle half {q1}–{q3}',r3s:'{name}: {n} districts · {min} to {max} per 10,000 · median {med}',
 dr:'{name} ({st}) · {type} · {pts} points · {res} residents · {rate} per 10,000 · rank {rk} of {districtCount}',flags:'Needs a check: {list}.',noFlag:'No check needed.',
 fl:{lowLabelCoordinateAgreement:'label–coordinate agreement under 95%',concentratedCoLocation:'one single-site group holds 20%+ of points',smallPointCount:'fewer than 100 points',labelGap:'{n} nearby Hanau-labelled points not added'},
 r5:'{districtCount} districts: {min} to {max} per 10,000, about {x}-fold. Middle half: {q1} to {q2}.',
 med5:'Median district {v}',st5:'State rate',
 r6:'Points per installation: Germany {g} · Brandenburg {b} · Berlin {be}',nPts:['1 point','{n} points'],
 axisX:'Residents',axisY:'Registered points',ray:'{r} per 10,000',rayG:'Germany {r}',
 osLine:'Oder-Spree: {r} per 10,000 residents · rank {k} of {bbCount} · {p}',ptsReg:'{n} registered points',ptsRem:'{n} of {m} registered points remain',
 regGhost:'Registered {r}',median:'Median',berlin:'Berlin, separate',
 left8:'As registered',right8:'Largest group set aside',r8:'{n} of {districtCount} districts move {k} or more places. Oder-Spree: rank {a} → {b}.',r8d:'{name}: rank {a} → {b}; largest group {g} of {p} points ({sh}).',r8l:'{name} · rank {a} → {b} · largest group {g} of {p} points ({sh})',
 tState:'All {stateCount} states, registered',tFlag:'Districts that need a check ({n})',tBB:'Brandenburg’s {bbCount} districts, registered',tMove:'Districts moving {k}+ places ({n})',
 cState:'State',cPts:'Points',cInst:'Installations',cMw:'MW',cRes:'Residents',cRate:'Per 10,000',cKw:'kW per 1,000',cHi:'>22 kW',cDist:'District',cFlags:'Check',cRank:'Rank',cRank2:'Set aside',cGroup:'Largest group',
 bbNote:'Without that group only Oder-Spree changes: {a} points, {r} per 10,000, rank {k}. Berlin is shown for context and is not ranked.',moveNote:'Each district’s own largest single-site group set aside; public access of these groups is unverified.',
 n2p:'{a} has the most points; by rate it ranks {r} of {stateCount}.',n2r:'{a} has the highest rate, {v} per 10,000; by points it ranks {r} of {stateCount}.',n2c:'Switch to per 10,000 residents to compare states of different size.',
 n2hi:'Highlighted ranks {mode}: Brandenburg, {b} of {stateCount}; Berlin, a city-state, {be} of {stateCount}.',n2g:'The dashed line is Germany, {g} per 10,000.',
 n2s:'{name}: {a} of {stateCount} by points, {b} by rate. Only Brandenburg and Berlin are highlighted here.',
 nd:'{d} ({st}): {rate} per 10,000, rank {rk} of {districtCount}.',ndx:'{d} lies outside {sel} (state: {pst}); it stays outlined at full strength.',
 n5a:['The highest district rate is about {x} times the lowest.','Middle half {q1} to {q2}; median {med}. Rings mark the {n} districts that need a check.'],
 n5f:['{n} districts need a check.','Location mismatch: {a} · one site 20%+: {b} · under 100 points: {c} · unmatched nearby label: {d}. A check is not an error; the rest are dimmed, not removed.'],
 n5s:'{name}: state rate {rate}; its districts {min} to {max}. Other states are muted.',n5u:'It needs no check and stays visible because it is picked.',
 n7:['As registered, Oder-Spree ranks {k} of {bbCount} at {r} per 10,000.','Without that group, Oder-Spree ranks {k} of {bbCount} at {r} per 10,000.'],
 n7p:'Without the {g} points registered to Tesla Manufacturing Brandenburg SE in Grünheide (Mark), Oder-Spree ranks {b} of {bbCount} in Brandenburg instead of {a}.',
 n7b:'Separately, set aside every district’s largest single-site group: rank {a} → {b} of {districtCount}.',n7c:'It does not say the records are wrong or private.',
 r7d:'{d} · {r} per 10,000 · rank {k} of {bbCount}',n7x:'Brandenburg only: {x} is outside this case study.',
 n8:['{n} of {districtCount} districts move {k}+ places.','Oder-Spree: {a} → {b}. Public access of these groups is unverified.'],
 n8s:'{name}: {m} of {n} districts move {k}+ places; all {districtCount} stay drawn.'}},
 {v:{kick:'Eine Datenanalyse des öffentlichen Ladesäulenregisters',title:'Wann ist ein Ladepunkt-Ranking belastbar?',docTitle:'ChargeScope · Wann ist ein Ladepunkt-Ranking belastbar?',
 lead:'Oder-Spree steht bei Ladepunkten je Einwohner auf Rang {a} von {districtCount} deutschen Kreisen. Ohne die jeweils größte Standortgruppe jedes Kreises (hier {g} Ladepunkte) steht es auf Rang {b}.',
 lead2:'Vier Prüfungen an {pts} registrierten Ladepunkten zeigen, welche regionalen Vergleiche tragen.',scope:'Register {reg} · Einwohner {pop}',
 figCap:'Oder-Spree: Rang unter {districtCount} deutschen Kreisen nach Ladepunkten je Einwohner',figA:'wie registriert',figB:'ohne die jeweils größte Standortgruppe jedes Kreises (hier {g} Ladepunkte)',cue:'Weiter zu den vier Prüfungen',
 steps:['Schritt 1 von 4','Schritt 2 von 4','Schritt 3 von 4 · Brandenburg','Schritt 4 von 4'],kind:{city:'Stadt',county:'Landkreis'},
 h2:'Die meisten Ladepunkte bedeuten nicht die höchste Quote.',p2:'Eine Anzahl misst vor allem, wie groß ein Land ist. Je Einwohner gerechnet werden Länder vergleichbar.',leg2:'Hervorgehoben: Brandenburg und Berlin, Thema in Schritt 3.',
 h5:'Die Quote eines Landes verdeckt seine Kreise.',p5:'Die Länderquoten reichen von {smin} bis {smax} je 10.000. Die Kreisquoten reichen von {dmin} bis {dmax}.',leg5:'○ Zu prüfen: wenige Ladepunkte, ein dominanter Standort oder abweichende Lage.',
 h7:'In Brandenburg hängt Rang {bbRank} an einer registrierten Gruppe.',p7:'{g} der {p} Ladepunkte in Oder-Spree ({sh}) sind Einzelpunkt-Datensätze mit {kw} kW, registriert auf die Tesla Manufacturing Brandenburg SE in Grünheide (Mark), an einer Koordinate.',leg7:'Standortgruppe: Datensätze eines Betreibers an einer Koordinate. Wer die einzelnen Ladepunkte heute nutzen kann, legt das Register nicht fest; im Februar 2024 beschrieb Tesla die Ladepunkte auf dem Werksparkplatz als öffentlich und kostenlos ({method}).',
 h8:'Es betrifft nicht nur Oder-Spree.',p8:'Ohne die jeweils größte Standortgruppe jedes Kreises verschieben sich {n} von {districtCount} Kreisen um {k} oder mehr Plätze.',
 wKick:'Was daraus folgt',wH:'Ein Ranking zeigt, wo man genauer hinsehen sollte, nicht, was daraus folgt.',
 wF:[['Anzahl und Quote ordnen die Länder verschieden.','{top} hat die meisten Ladepunkte und steht nach Quote auf Rang {r} von {stateCount}.'],['Durchschnitte verdecken die Streuung.','Die Kreisquoten unterscheiden sich um das {x}-Fache, die Länderquoten etwa um das {y}-Fache.'],['Ein Standort kann einen Rang tragen.','{n} von {districtCount} Kreisen verschieben sich um {k}+ Plätze, wenn ihre größte Standortgruppe herausgenommen wird.']],
 wRec:'Bevor Sie ein regionales Ranking weitergeben: Zeigen Sie Anzahl und Quote nebeneinander und prüfen Sie jeden Kreis, in dem ein Standort einen großen Teil der Ladepunkte hält.',wLim:'Gemessen wird nur das registrierte Angebot, nicht Bedarf, Nutzung oder Zugang.',
 aKick:'Über das Projekt',aH:'Wie es entstand',aL:['Daten: Ladesäulenregister der Bundesnetzagentur ({reg}, {inst} Datensätze) und BKG-Einwohner nach Kreis ({pop}).','Pipeline: Python gleicht Ladeeinrichtungen, Ladepunkte und Stecker ab; DuckDB-SQL berechnet Berichtskennzahlen. Die Website nutzt eine eigene, getestete Python-Aggregation.','Bericht: eine vierseitige Power-BI-Fallstudie zu Brandenburgs {bbCount} Kreisen.'],
 xKick:'Die Daten erkunden',xH:'Mehr aus dem Register',xP:'Ergänzende Ansichten. Sie gehören nicht zur Argumentation oben.',
 h1:'Wo die Ladepunkte sind',p1:'Bogenlänge: registrierte Ladepunkte. Innen Länder, außen Kreise.',
 h3:'Einwohner und Ladepunkte nach Kreis',p3:'{districtCount} Kreise auf logarithmischen Skalen. Diagonalen markieren gleiche Quoten.',
 h4:'Ladeleistung nach Land',p4:'Höchste Steckerleistung je Ladepunkt.',
 h6:'Ladepunkte je Ladeeinrichtung',p6:'{share} von {n} Ladeeinrichtungen haben ein oder zwei Ladepunkte. Eine Ladeeinrichtung ist ein Registerdatensatz, nicht unbedingt ein Standort.',
 u1:'Registrierte Ladepunkte, {reg}',u3:'Einwohner ({pop}) und registrierte Ladepunkte, logarithmisch',u4:'Anteil registrierter Ladepunkte nach höchster Steckerleistung',
 u5:'Ladepunkte je 10.000 Einwohner, nach Kreis',u7:'Brandenburgs {bbCount} Kreise · Berlin separat',u8:'Rang unter {districtCount} Kreisen, Ladepunkte je 10.000 Einwohner',
 unitPts:'Registrierte Ladepunkte',unitRate:'Ladepunkte je 10.000 Einwohner ({pop})',unitInst:'Ladeeinrichtungen nach Zahl der Ladepunkte',unitIp:'Ladepunkte nach Größe der Ladeeinrichtung',
 stateSel:'Land',allStates:'Deutschland, alle Länder',distSel:'Kreis',noDist:'Kreis wählen',
 m2:[['points','Ladepunkte'],['rate','Je 10.000 Einwohner']],rkP:'Rang {k} nach Anzahl der Ladepunkte',rkR:['Rang {k} nach Ladepunkten je 10.000 Einwohner, gleicher Rang wie nach Anzahl der Ladepunkte', 'Rang {k} nach Ladepunkten je 10.000 Einwohner, um {d} höher als Rang {p} nach Anzahl der Ladepunkte', 'Rang {k} nach Ladepunkten je 10.000 Einwohner, um {d} niedriger als Rang {p} nach Anzahl der Ladepunkte'],m5:[['all','Alle Kreise'],['flag','Zu prüfen ({n})']],m6:[['inst','Ladeeinrichtungen'],['pts','Ladepunkte']],m8:[['20','20+ Plätze ({n})'],['50','50+ Plätze ({n})']],
 scenario:'Hypothetisches Szenario',registered:'Wie registriert',without:'Ohne diese Gruppe',view:'Ansicht',
 germany:'Deutschland',points:'Ladepunkte',perTen:'je 10.000',
 ctr:['registrierte Ladepunkte','{i} Ladeeinrichtungen','{mw} MW Nennleistung'],
 r1:'{name}: {pts} Ladepunkte ({share} von Deutschland) · {inst} Ladeeinrichtungen · {mw} MW Nennleistung',r1g:'Deutschland: {pts} Ladepunkte · {inst} Ladeeinrichtungen · {mw} MW Nennleistung',r1h:' · {h} Ladepunkte ohne Kreiszuordnung',
 r2s:'{name} · Rang {a} von {stateCount} nach Ladepunkten · Rang {b} von {stateCount} nach Quote',
 r3g:'{districtCount} Kreise · Median {med} je 10.000 · mittlere Hälfte {q1}–{q3}',r3s:'{name}: {n} Kreise · {min} bis {max} je 10.000 · Median {med}',
 dr:'{name} ({st}) · {type} · {pts} Ladepunkte · {res} Einwohner · {rate} je 10.000 · Rang {rk} von {districtCount}',flags:'Zu prüfen: {list}.',noFlag:'Keine Prüfung nötig.',
 fl:{lowLabelCoordinateAgreement:'Übereinstimmung Bezeichnung–Koordinate unter 95 %',concentratedCoLocation:'eine Standortgruppe hält 20 %+ der Ladepunkte',smallPointCount:'weniger als 100 Ladepunkte',labelGap:'{n} nahe Ladepunkte mit Bezeichnung Hanau nicht hinzugezählt'},
 r5:'{districtCount} Kreise: {min} bis {max} je 10.000, etwa das {x}-Fache. Mittlere Hälfte: {q1} bis {q2}.',
 med5:'Median der Kreise {v}',st5:'Landesquote',
 r6:'Ladepunkte je Ladeeinrichtung: Deutschland {g} · Brandenburg {b} · Berlin {be}',nPts:['1 Ladepunkt','{n} Ladepunkte'],
 axisX:'Einwohner',axisY:'Registrierte Ladepunkte',ray:'{r} je 10.000',rayG:'Deutschland {r}',
 osLine:'Oder-Spree: {r} je 10.000 Einwohner · Rang {k} von {bbCount} · {p}',ptsReg:'{n} registrierte Ladepunkte',ptsRem:'{n} von {m} registrierten Ladepunkten verbleiben',
 regGhost:'Registerstand {r}',median:'Median',berlin:'Berlin, separat',
 left8:'Wie registriert',right8:'Größte Gruppe herausgenommen',r8:'{n} von {districtCount} Kreisen verschieben sich um {k} oder mehr Plätze. Oder-Spree: Rang {a} → {b}.',r8d:'{name}: Rang {a} → {b}; größte Gruppe {g} von {p} Ladepunkten ({sh}).',r8l:'{name} · Rang {a} → {b} · größte Gruppe {g} von {p} Ladepunkten ({sh})',
 tState:'Alle {stateCount} Länder, Registerstand',tFlag:'Kreise mit Prüfbedarf ({n})',tBB:'Brandenburgs {bbCount} Kreise, Registerstand',tMove:'Kreise mit {k}+ Plätzen Verschiebung ({n})',
 cState:'Land',cPts:'Ladepunkte',cInst:'Ladeeinrichtungen',cMw:'MW',cRes:'Einwohner',cRate:'Je 10.000',cKw:'kW je 1.000',cHi:'>22 kW',cDist:'Kreis',cFlags:'Prüfung',cRank:'Rang',cRank2:'Ohne Gruppe',cGroup:'Größte Gruppe',
 bbNote:'Ohne diese Gruppe ändert sich nur Oder-Spree: {a} Ladepunkte, {r} je 10.000, Rang {k}. Berlin wird zum Vergleich gezeigt und nicht gerankt.',moveNote:'Jeweils die größte Standortgruppe des Kreises herausgenommen; öffentlicher Zugang dieser Gruppen ist ungeprüft.',
 n2p:'{a} hat die meisten Ladepunkte; nach Quote steht es auf Rang {r} von {stateCount}.',n2r:'{a} hat die höchste Quote, {v} je 10.000; nach Anzahl steht es auf Rang {r} von {stateCount}.',n2c:'Mit der Ansicht je 10.000 Einwohner lassen sich Länder unterschiedlicher Größe vergleichen.',
 n2hi:'Hervorgehobene Ränge {mode}: Brandenburg, Rang {b} von {stateCount}; Berlin, ein Stadtstaat, Rang {be} von {stateCount}.',n2g:'Die gestrichelte Linie ist Deutschland, {g} je 10.000.',
 n2s:'{name}: Rang {a} von {stateCount} nach Ladepunkten, {b} nach Quote. Hervorgehoben sind hier nur Brandenburg und Berlin.',
 nd:'{d} ({st}): {rate} je 10.000, Rang {rk} von {districtCount}.',ndx:'{d} liegt außerhalb von {sel} (Land: {pst}); der Kreis bleibt umrandet und voll sichtbar.',
 n5a:['Die höchste Kreisquote ist etwa {x}-mal so hoch wie die niedrigste.','Mittlere Hälfte {q1} bis {q2}; Median {med}. Ringe markieren die {n} Kreise, die eine Prüfung brauchen.'],
 n5f:['{n} Kreise brauchen eine Prüfung.','Abweichende Lage: {a} · ein Standort 20 %+: {b} · unter 100 Ladepunkte: {c} · nahe Bezeichnung ohne Zuordnung: {d}. Eine Prüfung ist kein Fehler; die übrigen sind abgeblendet, nicht entfernt.'],
 n5s:'{name}: Landesquote {rate}; seine Kreise {min} bis {max}. Andere Länder sind gedämpft.',n5u:'Er braucht keine Prüfung und bleibt sichtbar, weil er gewählt ist.',
 n7:['Wie registriert steht Oder-Spree mit {r} je 10.000 auf Rang {k} von {bbCount}.','Ohne diese Gruppe steht Oder-Spree mit {r} je 10.000 auf Rang {k} von {bbCount}.'],
 n7p:'Ohne die {g} Ladepunkte, die auf die Tesla Manufacturing Brandenburg SE in Grünheide (Mark) registriert sind, steht Oder-Spree in Brandenburg auf Rang {b} statt {a} von {bbCount}.',
 n7b:'Separater Test: größte Standortgruppe je Kreis weglassen, Rang {a} → {b} von {districtCount}.',n7c:'Er sagt nicht, dass die Datensätze falsch oder privat sind.',
 r7d:'{d} · {r} je 10.000 · Rang {k} von {bbCount}',n7x:'Nur Brandenburg: {x} liegt außerhalb dieser Fallstudie.',
 n8:['{n} von {districtCount} Kreisen verschieben sich um {k}+ Plätze.','Oder-Spree: {a} → {b}. Öffentlicher Zugang dieser Gruppen ist ungeprüft.'],
 n8s:'{name}: {m} von {n} Kreisen verschieben sich um {k}+ Plätze; alle {districtCount} bleiben gezeichnet.'}});
const w=k=>{const values={districtCount:DI.length,stateCount:ST.length,bbCount:BB.districts.length,bbRank:BB.districts.find(d=>d.code==='12067').registered.rank},counts=value=>typeof value==='string'?value.replace(/\{(districtCount|stateCount|bbCount|bbRank)\}/g,(_,key)=>values[key]):Array.isArray(value)?value.map(counts):value;return counts(t('v')[k])};
const st={state:'',pick:'',m2:'points',m5:'all',m6:'inst',m8:'20',excluded:false};
const R=k=>K.root.querySelector('[data-r="'+k+'"]');
const txt=(x,y,v,c='',a='start')=>`<text x="${x.toFixed(1)}" y="${y.toFixed(1)}" text-anchor="${a}" class="${c}">${esc(v)}</text>`;
const tbl=k=>`<button type="button" class="k-btn" data-act="table" data-v="${k}" data-k="t${k}">${t('table')}</button>`;
const seg=(label,act,m,opts,cur)=>`<div class="k-seg v3-seg" role="group" aria-label="${esc(label)}">${opts.map(([v,l])=>`<button type="button" data-act="${act}" data-m="${m}" data-v="${v}" data-k="${m}${v}" aria-pressed="${cur===v}">${esc(l)}</button>`).join('')}</div>`;
const mode=(m,opts)=>seg(w('view'),'mode',m,opts,st[m]);
// A step: kicker, takeaway and why first, then the frame, then (below 1180 px) the story and the Table button. The connector joins the previous step's foot to this heading.
const step=(id,i,h,p,top,art,extra)=>`<section class="v3-room v3-step" id="${id}" aria-labelledby="${id}-h"><span class="v3-thread" aria-hidden="true"><span class="th-p"></span><span class="th-s"></span><span class="th-t"></span></span><div class="v3-label"><span class="v3-room-no">${esc(w('steps')[i])}</span><h2 id="${id}-h">${esc(h)}</h2><p>${esc(p)}</p></div><div class="v3-frame">${top}${art}</div><div class="v3-foot"><div class="v3-story" data-r="st${i}"></div>${extra}</div></section>`;
// A supporting chart in Explore: a heading, the frame at rest (no camera, connector or story) and one line.
const xp=(id,h,p,top,art,extra='')=>`<section class="v3-x" id="${id}" aria-labelledby="${id}-h"><h3 id="${id}-h">${esc(h)}</h3><div class="v3-frame">${top}${art}</div><p class="v3-x-p">${esc(p)}</p>${extra}</section>`;
const unit=(k,o)=>`<p class="v3-unit" data-r="${k}">${esc(fill(w(k),o||DATES()))}</p>`;
const DATES=()=>({reg:date(N.meta.charging.snapshotDate),pop:date(N.meta.population.referenceDate)});
// District names occur twice where a city and its surrounding county share one (22 pairs): those carry their kind wherever a name is shown.
const DUP=new Set(DI.filter((d,i)=>DI.findIndex(e=>e.name===d.name)!==i).map(d=>d.name));
const nm=d=>DUP.has(d.name)?`${d.name} (${w('kind')[d.kind]})`:d.name;
const stateSel=k=>`<label class="v3-sel"><span>${w('stateSel')}</span><select data-act="state" data-k="${k}"><option value="">${w('allStates')}</option>${ST.map(s=>`<option value="${s.code}"${s.code===st.state?' selected':''}>${esc(s.name)}</option>`).join('')}</select></label>`;
const distSel=k=>`<label class="v3-sel"><span>${w('distSel')}</span><select data-act="pick" data-k="${k}"><option value="">${w('noDist')}</option>${ST.map(s=>`<optgroup label="${esc(s.name)}">${DI.filter(d=>d.state===s.code).sort((a,b)=>nm(a).localeCompare(nm(b),'de')).map(d=>`<option value="${d.code}"${d.code===st.pick?' selected':''}>${esc(nm(d))}</option>`).join('')}</optgroup>`).join('')}</select></label>`;
// Figures derived once from the payload; text and charts both read them.
const hi=[...ST].sort((a,b)=>a.highPowerPointShare-b.highPowerPointShare),spread=G.districtRateSpread.all;
const move=k=>DI.filter(d=>Math.abs(d.rankGermany-d.rankWithoutTopGroup)>=k);
const OS=K.district('12067'),bbOS=BB.districts.find(d=>d.code==='12067'),fg=BB.flaggedGroup,flagged=DI.filter(d=>d.flags.length);
const two=G.installationsByPointCount['1']+G.installationsByPointCount['2'];
const kids=c=>DI.filter(d=>d.state===c);
const bbRank=ex=>BB.districts.map(d=>d[ex?'hypothetical':'registered']);
const bbMedian=ex=>{const v=bbRank(ex).map(r=>r.rate).sort((a,b)=>a-b);return(v[8]+v[9])/2};
let intro=true;const MOVE=20,byRate=[...ST].sort((a,b)=>a.pointsPer10kResidents-b.pointsPer10kResidents),topCount=[...ST].sort((a,b)=>b.points-a.points)[0];

function html(){const D=DATES(),r1=v=>f(v,1);document.title=w('docTitle');
 // The opening: question, then the finding as a figure. One quiet tick per district by rank, majors at 1, every hundred and the last; Oder-Spree's
 // registered rank is a light marker, and an orange arc carries it to its rank without the group, drawn once on first load with the orange marker
 // travelling beneath it. The figure is drawn for the eye; the sentence beside it (visually hidden) is what is read.
 const n=DI.length,a=OS.rankGermany,b=OS.rankWithoutTopGroup,g=f(OS.topGroup.points),at=r=>((r-.5)/n*100).toFixed(3)+'%',tick=r=>`M${r-.5} 0V1`;
 const ticks=Array.from({length:n},(_,i)=>tick(i+1)).join(''),scale=[...new Set([1,...Array.from({length:n/100|0},(_,i)=>100*(i+1)),n])];
 const hero=`<section class="v3-hero${intro?' is-intro':''}" id="top"><div class="v3-copy"><div class="v3-lead"><p class="v3-kick">${esc(w('kick'))}</p><h1>${esc(w('title'))}</h1><p class="v3-intro k-vh">${esc(fill(w('lead'),{a,g,b}))}</p>
<div class="v3-fig" aria-hidden="true" style="--from:${at(a)};--to:${at(b)}"><p class="v3-fig-cap">${esc(w('figCap'))}</p><div class="v3-fig-axis"><svg class="v3-ticks" viewBox="0 0 ${n} 1" preserveAspectRatio="none"><path d="${ticks}"/><path class="v3-major" d="${scale.map(tick).join('')}"/></svg>
<svg class="v3-arc" viewBox="0 0 100 10" preserveAspectRatio="none"><path d="M0 10C0 -3.33 100 -3.33 100 10"/></svg><i class="v3-fig-a"></i><i class="v3-fig-b"></i><i class="v3-fig-tip"></i><span class="v3-fig-ra">${a}</span><span class="v3-fig-rb">${b}</span></div>
<p class="v3-fig-scale">${scale.map(r=>`<span style="left:${at(r)}">${r}</span>`).join('')}</p><div class="v3-fig-nums"><p><b>${a}</b><span>${esc(w('figA'))}</span></p><p><b>${b}</b><span>${esc(fill(w('figB'),{g}))}</span></p></div></div>
<p class="v3-intro2">${esc(fill(w('lead2'),{pts:f(G.points)}))}</p></div><p class="v3-scope">${esc(fill(w('scope'),D))} · <button type="button" class="k-link" data-act="about" data-k="habout">${t('about')}</button> · <span class="v3-by">${t('by')}</span></p><p class="v3-cue" aria-hidden="true">${esc(w('cue'))}</p></div>
<div class="v3-pub" aria-hidden="true" inert><div class="v3-pub-k">${esc(w('kick'))}</div><div class="v3-pub-h">${esc(w('title'))}</div><div class="v3-pub-i">${esc(fill(w('lead'),{a,g,b}))}</div><div class="v3-pub-i2">${esc(fill(w('lead2'),{pts:f(G.points)}))}</div><div class="v3-pub-s">${esc(fill(w('scope'),D))} · <span>${t('about')}</span></div><div class="v3-pub-b">${t('by')}</div></div></section>`;intro=false;
 const wf=w('wF'),wv=[{top:topCount.name,r:topCount.rank},{x:f(spread.max/spread.min),y:f(byRate[15].pointsPer10kResidents/byRate[0].pointsPer10kResidents)},{n:move(MOVE).length,k:MOVE}];
 const what=`<section class="v3-end v3-what" id="findings" aria-labelledby="findings-h"><span class="v3-room-no">${esc(w('wKick'))}</span><h2 id="findings-h">${esc(w('wH'))}</h2><ol class="v3-find">${wf.map(([h,p],i)=>`<li><strong>${esc(h)}</strong> <span>${esc(fill(p,wv[i]))}</span></li>`).join('')}</ol><p class="v3-rec">${esc(w('wRec'))}</p><p>${esc(w('wLim'))} <button type="button" class="k-link" data-act="about" data-k="cabout">${t('about')}</button></p></section>`;
 const aboutS=`<section class="v3-end" id="about" aria-labelledby="about-h"><span class="v3-room-no" id="about-k">${esc(w('aKick'))}</span><h2 id="about-h">${esc(w('aH'))}</h2><ul class="v3-made">${w('aL').map(x=>`<li>${esc(fill(x,{...D,inst:f(G.installations)}))}</li>`).join('')}</ul><p class="v3-end-act"><button type="button" class="k-btn v3-end-open" data-act="report" data-k="erp" aria-haspopup="dialog" aria-describedby="about-k">${t('viewSlides')}</button>${K.links()}</p><p class="v3-by">${t('by')} · ${K.contact()}</p></section>`;
 return hero+
 step('r2',0,w('h2'),w('p2'),`<div class="v3-top"><p class="v3-unit" data-r="u2"></p>${mode('m2',w('m2'))}</div>`,`<div class="k-rows v3-rows" data-r="bars"></div><p class="v3-legend">${esc(w('leg2'))}</p><p class="v3-readout" data-r="ro2" aria-live="polite"></p>`,tbl('state'))+
 step('r5',1,w('h5'),fill(w('p5'),{smin:r1(byRate[0].pointsPer10kResidents),smax:r1(byRate[15].pointsPer10kResidents),dmin:r1(spread.min),dmax:r1(spread.max)}),`<div class="v3-top">${unit('u5')}${mode('m5',w('m5').map(([v,l])=>[v,fill(l,{n:flagged.length})]))}${distSel('d5')}</div>`,`<div data-r="spread" class="v3-chart"></div><p class="v3-legend">${esc(w('leg5'))}</p><p class="v3-readout" data-r="ro5" aria-live="polite"></p>`,tbl('flag'))+
 step('r7',2,w('h7'),fill(w('p7'),{g:f(fg.points),p:f(bbOS.registered.points),kw:f(fg.nominalKw/fg.installations),sh:pct(fg.points/bbOS.registered.points,0)}),`<div class="v3-top">${unit('u7')}${seg(w('scenario'),'scen','sc',[['0',w('registered')],['1',w('without')]],st.excluded?'1':'0')}</div>`,`<div data-r="strip" class="v3-chart"></div><p class="v3-legend">${esc(fill(w('leg7'),{method:t('about')}))}</p><p class="v3-readout" data-r="osline" aria-live="polite"></p><p class="v3-readout" data-r="ro7" aria-live="polite"></p>`,tbl('bb'))+
 step('r8',3,w('h8'),fill(w('p8'),{n:move(MOVE).length,k:MOVE}),`<div class="v3-top">${unit('u8')}${mode('m8',w('m8').map(([v,l])=>[v,fill(l,{n:move(+v).length})]))}</div>`,`<div data-r="slope" class="v3-chart"></div><p class="v3-readout" data-r="ro8" aria-live="polite"></p>`,tbl('move'))+
 what+aboutS+
 `<section class="v3-xs" id="explore" aria-labelledby="explore-h"><span class="v3-room-no">${esc(w('xKick'))}</span><h2 id="explore-h">${esc(w('xH'))}</h2><p class="v3-x-p">${esc(w('xP'))}</p>
${xp('r1',w('h1'),w('p1'),`<div class="v3-top">${unit('u1')}${stateSel('s1')}</div>`,`<div data-r="ring" class="v3-chart"></div><p class="v3-readout" data-r="ro1" aria-live="polite"></p>`)}
${xp('r3',w('h3'),w('p3'),`<div class="v3-top">${unit('u3')}${stateSel('s3')}</div>`,`<div data-r="scatter" class="v3-chart"></div><p class="v3-readout" data-r="ro3" aria-live="polite"></p>`)}
${xp('r4',w('h4'),w('p4'),`<div class="v3-top">${unit('u4')}</div>`,`<div data-r="mix" class="v3-mix"></div>`,tbl('state'))}
${xp('r6',w('h6'),fill(w('p6'),{share:pct(two/G.installations,0),n:f(G.installations)}),`<div class="v3-top"><p class="v3-unit" data-r="u6"></p>${mode('m6',w('m6'))}</div>`,`<div class="k-rows v3-rows" data-r="comp"></div><p class="v3-readout" data-r="ro6"></p>`)}</section>`}

// Explore · Two rings, arc length proportional to registered points: states inside, districts outside. Hanau's 249 unmatched points stay as a hatched gap in Hessen.
function ring(){const el=R('ring'),W=Math.max(280,el.clientWidth||600),ph=W<560,S=Math.min(W-(ph?52:96),520),R0=S/2,cx=W/2,cy=R0+(ph?26:34),H=S+(ph?52:68);
 const gs=.012,k=(2*Math.PI-gs*16)/G.points,P=(r,a)=>[cx+r*Math.cos(a),cy+r*Math.sin(a)],r1=R0*.47,r2=R0*.68,r3=R0*.72,r4=R0;
 const arc=(a,b,i,o)=>{const L=b-a>Math.PI?1:0,[x1,y1]=P(o,a),[x2,y2]=P(o,b),[x3,y3]=P(i,b),[x4,y4]=P(i,a);return`M${x1.toFixed(1)} ${y1.toFixed(1)}A${o} ${o} 0 ${L} 1 ${x2.toFixed(1)} ${y2.toFixed(1)}L${x3.toFixed(1)} ${y3.toFixed(1)}A${i} ${i} 0 ${L} 0 ${x4.toFixed(1)} ${y4.toFixed(1)}Z`};
 let a=-Math.PI/2+gs/2,g='',labs='';const taken=[],box={W,H,taken};
 ST.forEach((s,si)=>{const a0=a,a1=a+s.points*k,on=s.code===st.state,cls=`sb-s${si%2?' alt':''}${on?' is-on':''}${st.state&&!on?' is-dim':''}`,am=(a0+a1)/2;
  g+=`<path class="${cls}" d="${arc(a0,a1,r1,r2)}" data-act="state" data-v="${s.code}"><title>${esc(s.name)}: ${f(s.points)}</title></path>`;
  let b=a0;for(const d of kids(s.code)){const e=b+d.points*k;g+=`<path class="sb-d${si%2?' alt':''}${on?' is-on':''}${st.state&&!on?' is-dim':''}" d="${arc(b,e,r3,r4)}" data-act="state" data-v="${s.code}"><title>${esc(nm(d))} (${esc(s.name)}): ${f(d.points)}</title></path>`;b=e}
  if(s.districtUnattributedPoints){const e=b+s.districtUnattributedPoints*k;g+=`<path class="sb-gap" d="${arc(b,e,r3,r4)}"><title>${esc(N.unattributedLabels[0].sourceLabel)}: ${f(s.districtUnattributedPoints)}</title></path>`}
  const side=Math.cos(am)>.3?'start':Math.cos(am)<-.3?'end':'middle',cands=q=>[P(r4+14,am).concat([q]),P(r4+24,am).concat([q])].map(([x,y,a])=>[x,y+4,a]);
  const lab=[[s.name,cands(side)],[ABBR[s.code],cands('middle')]].map(([v,c])=>[v,K.label(v,c,{...box,taken:[...taken],px:12,wt:on?700:400})]).find(x=>x[1]);
  if(lab){const[v,o]=lab;K.label(v,[[o.x,o.y,o.a]],{...box,px:12,wt:on?700:400});labs+=txt(o.x,o.y,v,'sb-lab'+(on?' is-on':''),o.a)}
  a=a1+gs});
 // Centre lines only where they fit inside the hole.
 const C=w('ctr'),big=ph?22:30,fit=(v,px)=>K.measure(v,px)+8<=2*Math.sqrt(r1*r1-30*30)?v:'',c1=fit(C[0],12),c2=fit(fill(C[1],{i:f(G.installations)}),12),c3=fit(fill(C[2],{mw:f(G.nominalMw,0)}),12);
 el.innerHTML=`<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" data-hole="${r1.toFixed(1)}" role="img" aria-label="${esc(fill(w('r1g'),{pts:f(G.points),inst:f(G.installations),mw:f(G.nominalMw,1)}))}"><defs><pattern id="sb-hatch" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line y2="5" class="sb-hl"/></pattern></defs>
 <g class="sb-arcs">${g}</g>${labs}<g class="sb-ctr">${txt(cx,cy-4,f(G.points),'sb-big','middle')}${c1&&txt(cx,cy+16,c1,'sb-small','middle')}${ph?'':(c2&&txt(cx,cy+36,c2,'sb-small','middle'))+(c3&&txt(cx,cy+54,c3,'sb-small','middle'))}</g></svg>`;
 el.querySelector('.sb-big').style.fontSize=big+'px';
 const s=K.state(st.state);R('ro1').textContent=s?fill(w('r1'),{name:s.name,pts:f(s.points),share:pct(s.points/G.points),inst:f(s.installations),mw:f(s.nominalMw,1)})+(s.districtUnattributedPoints?fill(w('r1h'),{h:f(s.districtUnattributedPoints)}):''):fill(w('r1g'),{pts:f(G.points),inst:f(G.installations),mw:f(G.nominalMw,0)})}

// Step 1 · The same 16 rows ranked by count or by rate; re-sorting moves the rows. Each row carries its rank, and per 10,000 residents also its move
// from the rank by points (▲ up, ▼ down; spelled out in the rows' label). The line below holds only a chosen state.
function bars(){const r=st.m2==='rate',key=r?'pointsPer10kResidents':'points',items=[...ST].sort((a,b)=>b[key]-a[key]||a.name.localeCompare(b.name)).map(s=>{const p=K.rankBy(ST,'points',s),k=r?s.rank:p,d=p-s.rank;
  return{code:s.code,name:s.name,value:s[key],label:r?f(s[key],1):f(s[key]),cls:s.code==='12'?'is-hi':s.code==='11'?'is-be':'',rank:k,move:r?(d>0?'▲'+d:d<0?'▼'+-d:'='):'',say:r?fill(w('rkR')[d>0?1:d<0?2:0],{k,d:Math.abs(d),p}):fill(w('rkP'),{k})}});
 R('bars').classList.toggle('is-rate',r);
 R('u2').textContent=r?fill(w('unitRate'),DATES()):w('unitPts');
 K.rows(R('bars'),{items,max:r?35:45000,label:R('u2').textContent,ref:r?{value:G.pointsPer10kResidents,label:w('germany')+' '+f(G.pointsPer10kResidents,1)}:null});
 const s=K.state(st.state);R('ro2').textContent=s?fill(w('r2s'),{name:s.name,a:K.rankBy(ST,'points',s),b:s.rank}):''}

// Explore · Residents against points on log axes; equal-rate lines are parallel diagonals.
function scatter(){const el=R('scatter'),W=Math.max(280,el.clientWidth||600),ph=W<560,H=ph?340:440,m={l:ph?40:52,r:ph?10:18,t:28,b:44},pw=W-m.l-m.r,pH=H-m.t-m.b,de=K.s.lang==='de';
 const L=Math.log10,x0=L(3e4),x1=L(4e6),y0=L(40),y1=L(1e4),X=v=>m.l+(L(v)-x0)/(x1-x0)*pw,Y=v=>m.t+pH-(L(v)-y0)/(y1-y0)*pH;
 const fx=v=>v>=1e6?f(v/1e6)+(de?' Mio.':'M'):f(v/1e3)+(de?' Tsd.':'k');let g='';
 for(const v of ph?[5e4,2e5,1e6]:[5e4,1e5,2e5,5e5,1e6,2e6])g+=`<line class="v3-grid" x1="${X(v).toFixed(1)}" x2="${X(v).toFixed(1)}" y1="${m.t}" y2="${m.t+pH}"/>`+txt(X(v),m.t+pH+18,fx(v),'v3-tick','middle');
 for(const v of ph?[50,200,1000,5000]:[50,100,200,500,1000,2000,5000])g+=`<line class="v3-grid" x1="${m.l}" x2="${m.l+pw}" y1="${Y(v).toFixed(1)}" y2="${Y(v).toFixed(1)}"/>`+txt(m.l-6,Y(v)+4,f(v),'v3-tick','end');
 const rays=[10,G.pointsPer10kResidents,50],seg=r=>{const a=Math.max(3e4,40e4/r),b=Math.min(4e6,1e8/r);return[a,b]};
 for(const r of rays){const[a,b]=seg(r);g+=`<line class="v3-ray${r===rays[1]?' is-g':''}" x1="${X(a).toFixed(1)}" y1="${Y(r*a/1e4).toFixed(1)}" x2="${X(b).toFixed(1)}" y2="${Y(r*b/1e4).toFixed(1)}"/>`}
 g+=txt(m.l+pw,m.t+pH+38,w('axisX'),'v3-axis','end')+txt(4,16,w('axisY'),'v3-axis');
 const S=st.state,P=DI.map(d=>({d,x:X(d.population),y:Y(d.points),r:d.code===st.pick?6:(S&&d.state===S?(ph?3.4:4):(ph?2.4:3))}));
 const dots=[...P].sort((p,q)=>(p.d.state===S)-(q.d.state===S)||(p.d.code===st.pick)-(q.d.code===st.pick)).map(p=>`<circle class="sc-dot${S&&p.d.state!==S&&p.d.code!==st.pick?' is-dim':''}${S&&p.d.state===S?' is-in':''}${p.d.code===st.pick?' is-on':''}" style="--s:${((p.x-m.l)/pw).toFixed(3)}" cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="${p.r}" data-act="pick" data-v="${p.d.code}"><title>${esc(nm(p.d))}: ${f(p.d.pointsPer10kResidents,1)}</title></circle>`).join('');
 const box={W,H:m.t+pH,dots:P.filter(p=>!S||p.d.state===S||p.d.code===st.pick),taken:[{l:0,r:K.measure(w('axisY'),13)+8,t:0,b:20}]};
 const lab=(d,on)=>{const p=P.find(q=>q.d===d),o=K.label(nm(d),[[p.x+p.r+5,p.y+4,'start'],[p.x-p.r-5,p.y+4,'end'],[p.x,p.y-p.r-6,'middle'],[p.x,p.y+p.r+15,'middle']],{...box,wt:on?600:400});return o?txt(o.x,o.y,nm(d),'v3-lab'+(on?' is-on':''),o.a):''};
 // Labels: the chosen district, then either the state's extremes (never a label-gap district) or the largest district and the highest rate.
 const pool=S?kids(S).filter(d=>!d.flags.includes('labelGap')):DI,by=k=>[...pool].sort((a,b)=>b[k]-a[k]);
 const names=[...new Set([st.pick,...(S?[by('pointsPer10kResidents')[0],by('pointsPer10kResidents').at(-1)]:[by('population')[0],by('pointsPer10kResidents')[0]]).map(d=>d.code)].filter(Boolean))];
 let labs=names.map(c=>lab(K.district(c),c===st.pick)).join('');
 for(const r of rays){const[a,b]=seg(r),v=r===rays[1]?fill(w('rayG'),{r:f(r,1)}):fill(w('ray'),{r}),c=[];for(const fr of[.92,.84,.76,.68,.6,.5]){const xv=10**(L(a)+(L(b)-L(a))*fr),px=X(xv),py=Y(r*xv/1e4);c.push([px-6,py-6,'end'],[px+6,py+14,'start'])}
  const o=K.label(v,c,{...box,px:12});if(o)labs+=txt(o.x,o.y,v,'v3-raylab'+(r===rays[1]?' is-g':''),o.a)}
 el.innerHTML=`<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(fill(w('u3'),DATES()))}">${g}<g class="sc-dots">${dots}</g>${labs}</svg>`;
 const d=K.district(st.pick),s=K.state(S);R('ro3').textContent=d?dline(d):s?fill(w('r3s'),{name:s.name,n:s.districtRate.n,min:f(s.districtRate.min,1),max:f(s.districtRate.max,1),med:f(s.districtRate.median,1)}):fill(w('r3g'),{med:f(spread.median,1),q1:f(spread.q1,1),q3:f(spread.q3,1)})}
const dline=d=>fill(w('dr'),{name:nm(d),st:ABBR[d.state],type:d.type,pts:f(d.points),res:f(d.population),rate:f(d.pointsPer10kResidents,1),rk:d.rankGermany});
const flagText=d=>d.flags.length?fill(w('flags'),{list:d.flags.map(k=>fill(w('fl')[k],{n:f((d.labelGap||{}).points||0)})).join('; ')}):w('noFlag');

// Explore · Power mix: one 100% bar per state plus Germany, sorted by the share above 22 kW.
const PW=['le22','gt22to149','gt149to299','gt299'];
function mix(){const el=R('mix'),rows=[{...G,name:w('germany'),code:'DE'},...[...ST].sort((a,b)=>b.highPowerPointShare-a.highPowerPointShare)];
 const keys=['≤ 22 kW','> 22–149','> 149–299','> 299 kW'];
 el.innerHTML=`<p class="mx-key" aria-hidden="true">${keys.map((k,i)=>`<span><i class="c${i}"></i>${k}</span>`).join('')}</p><div class="mx-rows" role="img" aria-label="${esc(fill(w('u4'),{}))}: ${rows.map(r=>`${r.name} ${pct(r.highPowerPointShare)}`).join('; ')}">${rows.map((r,i)=>{const n=r.points-r.pointsPowerUnknown;
  return`<div class="mx-row${r.code==='DE'?' is-de':''}${r.code==='12'?' is-hi':''}" style="--s:${(i/rows.length).toFixed(3)}" title="${esc(r.name)}: ${PW.map((k,j)=>keys[j]+' '+f(r.pointsByPower[k])).join(' · ')}"><span class="mx-name">${esc(r.name)}</span><span class="mx-bar">${PW.map((k,j)=>`<i class="c${j}" style="width:${(r.pointsByPower[k]/n*100).toFixed(2)}%"></i>`).join('')}</span><span class="mx-val">${pct(r.highPowerPointShare)}</span></div>`}).join('')}</div>`}

// Step 2 · District spread within each state, on one shared rate axis. Districts that need a check are rings (shape, not colour alone).
function spreadChart(){const el=R('spread'),W=Math.max(280,el.clientWidth||600),ph=W<560,rh=ph?21:25,nw=ph?30:Math.max(...ST.map(s=>K.measure(s.name,13)))+14,m={l:nw+6,r:ph?10:16,t:30,b:30},H=m.t+16*rh+m.b,X=v=>m.l+v/110*(W-m.l-m.r);
 const order=[...ST].sort((a,b)=>b.pointsPer10kResidents-a.pointsPer10kResidents),fl=st.m5==='flag';let g='',dots='',labs='';
 for(const v of[0,25,50,75,100])g+=`<line class="v3-grid" x1="${X(v).toFixed(1)}" x2="${X(v).toFixed(1)}" y1="${m.t}" y2="${m.t+16*rh}"/>`+txt(X(v),H-10,f(v),'v3-tick','middle');
 const mv=fill(w('med5'),{v:f(spread.median,1)});g+=`<line class="sp-med" x1="${X(spread.median).toFixed(1)}" x2="${X(spread.median).toFixed(1)}" y1="${m.t-6}" y2="${m.t+16*rh}"/>`+txt(X(spread.median)+4,m.t-10,mv,'sp-medlab');
 const P=[];
 order.forEach((s,i)=>{const y=m.t+i*rh+rh/2,on=s.code===st.state;g+=txt(m.l-8,y+4,ph?ABBR[s.code]:s.name,'v3-tick sp-name'+(on?' is-on':''),'end')+`<line class="sp-st" x1="${X(s.pointsPer10kResidents).toFixed(1)}" x2="${X(s.pointsPer10kResidents).toFixed(1)}" y1="${(y-rh*.42).toFixed(1)}" y2="${(y+rh*.42).toFixed(1)}"><title>${w('st5')} ${f(s.pointsPer10kResidents,1)}</title></line>`;
  for(const d of kids(s.code)){const j=(((+d.code*9301+49297)%233280)/233280-.5)*rh*.55,x=X(d.pointsPer10kResidents),f1=d.flags.length>0,pk=d.code===st.pick;P.push({d,x,y:y+j,r:pk?6:3.4});
   dots+=`<circle class="sp-dot${f1?' is-flag':''}${pk?' is-on':''}${fl&&!f1&&!pk?' is-dim':''}${st.state&&!on&&!pk?' is-mute':''}" style="--s:${((x-m.l)/(W-m.l-m.r)).toFixed(3)}" cx="${x.toFixed(1)}" cy="${(y+j).toFixed(1)}" r="${pk?6:f1?3.6:3}" data-act="pick" data-v="${d.code}"><title>${esc(nm(d))}: ${f(d.pointsPer10kResidents,1)}${f1?' · '+esc(flagText(d)):''}</title></circle>`}});
 const pk=K.district(st.pick);if(pk){const p=P.find(q=>q.d===pk),o=K.label(nm(pk),[[p.x+9,p.y+4,'start'],[p.x-9,p.y+4,'end'],[p.x,p.y-10,'middle'],[p.x,p.y+18,'middle']],{W,H:m.t+16*rh+4,dots:[],taken:[{l:X(spread.median)-2,r:X(spread.median)+K.measure(mv,12)+8,t:0,b:m.t-4}],px:13,wt:600});if(o)labs=txt(o.x,o.y,nm(pk),'v3-lab is-on',o.a)}
 el.innerHTML=`<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(fill(w('r5'),R5()))}" class="${fl?'is-fl':''}">${g}<g class="sp-dots">${dots}</g>${labs}</svg>`;
 const s=K.state(st.state);R('ro5').textContent=pk?dline(pk)+' '+flagText(pk):s?fill(w('r3s'),{name:s.name,n:s.districtRate.n,min:f(s.districtRate.min,1),max:f(s.districtRate.max,1),med:f(s.districtRate.median,1)}):''}
const R5=()=>({min:f(spread.min,1),max:f(spread.max,1),x:f(spread.max/spread.min),q1:f(spread.q1,1),q2:f(spread.q3,1)});

// Explore · Installations by number of points; the same six rows show installations or the points they hold.
function comp(){const p=st.m6==='pts',c=G.installationsByPointCount,tot=p?G.points:G.installations,np=w('nPts');
 const items=Object.keys(c).map(n=>{const v=p?c[n]*n:c[n];return{code:'n'+n,name:fill(np[n==='1'?0:1],{n}),value:v,label:`${f(v)} · ${v/tot<.0005?'<'+pct(.001):pct(v/tot)}`,cls:+n<=2?'is-hi':''}});
 R('u6').textContent=w(p?'unitIp':'unitInst');K.rows(R('comp'),{items,max:p?160000:80000,label:R('u6').textContent});
 const b=K.state('12'),be=K.state('11');R('ro6').textContent=fill(w('r6'),{g:f(G.pointsPerInstallation,2),b:f(b.pointsPerInstallation,2),be:f(be.pointsPerInstallation,2)})}

// Step 3 · Brandenburg case: rate strip on a fixed 0–50 axis. Dots keep their nodes, so the scenario switch slides Oder-Spree along the axis.
function strip(){const el=R('strip'),W=Math.max(280,el.clientWidth||600),ph=W<560,rad=ph?7:9,H=ph?236:270,m={l:16,r:16},y0=(H-56)/2+30,X=v=>m.l+v/50*(W-m.l-m.r),ex=st.excluded,sc=ex?'hypothetical':'registered';
 const yB=H-48,vals=BB.districts.map(d=>({d,v:d[sc].rate})).sort((a,b)=>a.v-b.v),placed=[];
 for(const p of vals){p.x=X(p.v);let k=0,y=y0;const free=yy=>placed.every(q=>Math.hypot(q.x-p.x,q.y-yy)>=2*rad+2);while(!free(y)){k++;y=y0+(k%2?-1:1)*Math.ceil(k/2)*(2*rad+2)}p.y=y;placed.push(p)}
 const osReg=bbOS.registered.rate,ghost=fill(w('regGhost'),{r:f(osReg,1)}),ghostWidth=K.measure(ghost,12)+12,berl=fill('{b} {r}',{b:w('berlin'),r:f(BB_BERLIN().rate,1)});
 const med=bbMedian(ex),bx=X(BB_BERLIN().rate),os=vals.find(p=>p.d.code==='12067');
 if(el._W!==W||el._lang!==K.s.lang){el._W=W;el._lang=K.s.lang;let g='';for(const v of[0,10,20,30,40,50])g+=`<line class="v3-grid" x1="${X(v)}" x2="${X(v)}" y1="34" y2="${H-30}"/>`+txt(X(v),H-10,f(v),'v3-tick','middle');
  el.innerHTML=`<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img">${g}<g class="v3-med"><line y1="34" y2="${H-30}"/><text y="26" text-anchor="middle"></text></g><g class="v3-berlin" transform="translate(${bx.toFixed(1)} ${yB})"><path d="M0 -6l6 6l-6 6l-6 -6z"/>${txt(10,4,berl,'v3-tick')}</g><circle class="v3-ghost" r="${rad}" cx="${X(osReg).toFixed(1)}" cy="${y0}"/><text class="v3-ghostlab" x="${X(osReg).toFixed(1)}" y="${y0-rad-8}" text-anchor="end">${esc(ghost)}</text>${vals.map(p=>`<circle class="v3-s${p.d.code==='12067'?' is-os':''}" data-code="${p.d.code}" r="${rad}" cx="0" cy="0"><title></title></circle>`).join('')}<text class="v3-oslab" text-anchor="middle">Oder-Spree</text></svg>`}
 const svg=el.querySelector('svg'),rk=bbOS[sc].rank;svg.classList.toggle('is-ex',ex);svg.setAttribute('aria-label',`${w(ex?'without':'registered')}, ${fill(w('unitRate'),DATES())}, 0–50. ${w('median')} ${f(med,1)}. Oder-Spree ${f(os.v,1)}, ${w('cRank')} ${rk}.`);
 svg._x0=X(0);svg._y0=y0;
 for(const p of vals){const c=svg.querySelector(`[data-code="${p.d.code}"]`);c._x=p.x;c._y=p.y;c.style.transform=`translate(${p.x.toFixed(1)}px,${p.y.toFixed(1)}px)`;c.firstChild.textContent=`${p.d.name}: ${f(p.v,1)}`}
 const mg=svg.querySelector('.v3-med');mg.style.transform=`translateX(${X(med).toFixed(1)}px)`;mg.querySelector('text').textContent=`${w('median')} ${f(med,1)}`;
 const others=vals.filter(p=>p!==os).map(p=>({x:p.x,y:p.y,r:rad})).concat(ex?[{x:X(osReg),y:y0,r:rad}]:[]),ys=vals.map(p=>p.y),mw0=K.measure(w('median')+' '+f(med,1),12)+8;
 const taken=[{l:X(med)-mw0/2,r:X(med)+mw0/2,t:12,b:30},{l:bx-8,r:bx+14+K.measure(berl,12),t:yB-8,b:yB+8}].concat(ex?[{l:X(osReg)-ghostWidth,r:X(osReg)+6,t:y0-rad-22,b:y0-rad-4}]:[]);
 const o=K.label('Oder-Spree',[[os.x,os.y+rad+16,'middle'],[os.x,os.y-rad-6,'middle'],[os.x+rad+5,os.y+4,'start'],[os.x-rad-5,os.y+4,'end'],[os.x,Math.max(...ys)+rad+16,'middle'],[os.x,Math.min(...ys)-rad-6,'middle']],{W,H:H-24,dots:others.concat([{x:os.x,y:os.y,r:rad}]),taken,px:13,wt:600})||{x:os.x,y:os.y+rad+16,a:'middle'};
 const ol=svg.querySelector('.v3-oslab');ol.setAttribute('text-anchor',o.a);ol.style.transform=`translate(${o.x.toFixed(1)}px,${o.y.toFixed(1)}px)`;
 const r=bbOS[sc];R('osline').textContent=fill(w('osLine'),{r:f(r.rate,1),k:r.rank,p:ex?fill(w('ptsRem'),{n:f(r.points),m:f(bbOS.registered.points)}):fill(w('ptsReg'),{n:f(r.points)})});
 // A picked Brandenburg district, or a selection outside this case study, is named in this line rather than in the story.
 const S=K.state(st.state),D=K.district(st.pick),b=D&&BB.districts.find(x=>x.code===D.code),out=[S&&S.code!=='12'&&S.name,D&&!b&&nm(D)].filter(Boolean);
 R('ro7').textContent=[b&&b.code!=='12067'&&fill(w('r7d'),{d:b.name,r:f(b[sc].rate,1),k:b[sc].rank}),out.length&&fill(w('n7x'),{x:out.join(', ')})].filter(Boolean).join(' · ')}
const BB_BERLIN=()=>N.berlin.registered;

// Step 4 · Rank among 400, then with each district's own largest single-site group set aside (all districts at once). Movers are drawn, the rest stay faint.
function slope(){const el=R('slope'),W=Math.max(280,el.clientWidth||600),ph=W<560,m={l:ph?30:44,r:ph?30:44,t:40,b:20},xa=m.l,xb=W-m.r,k=+st.m8;
 // Column heads share one line when they fit, otherwise the right one drops below.
 const two=K.measure(w('left8'),13)+K.measure(w('right8'),13)+24>xb-xa;if(two)m.t=56;const H=(ph?360:440)+(two?16:0),Y=r=>m.t+(r-1)/399*(H-m.t-m.b);
 let g=txt(xa,18,w('left8'),'v3-axis','start')+txt(xb,two?36:18,w('right8'),'v3-axis','end');
 for(const r of[1,100,200,300,400])g+=txt(xa-6,Y(r)+4,f(r),'v3-tick','end')+txt(xb+6,Y(r)+4,f(r),'v3-tick','start');
 g+=`<line class="v3-grid" x1="${xa}" x2="${xa}" y1="${m.t}" y2="${H-m.b}"/><line class="v3-grid" x1="${xb}" x2="${xb}" y1="${m.t}" y2="${H-m.b}"/>`;
 const big=d=>Math.abs(d.rankGermany-d.rankWithoutTopGroup)>=k,ls=[...DI].sort((a,b)=>big(a)-big(b)||(a.code===st.pick)-(b.code===st.pick)||(a.code==='12067')-(b.code==='12067'));
 const lines=ls.map(d=>`<line pathLength="1" class="sl-l${big(d)?' is-mv':''}${d.code==='12067'?' is-os':''}${d.code===st.pick?' is-on':''}" style="--s:${((d.rankGermany-1)/399).toFixed(3)}" x1="${xa}" y1="${Y(d.rankGermany).toFixed(1)}" x2="${xb}" y2="${Y(d.rankWithoutTopGroup).toFixed(1)}"><title>${esc(nm(d))}: ${d.rankGermany} → ${d.rankWithoutTopGroup}</title></line>`).join('');
 const taken=[],box={W,H,taken};let labs='';
 for(const d of[...new Set([OS,K.district(st.pick)].filter(Boolean))]){const on=d.code===st.pick,a=K.label(`${nm(d)} ${d.rankGermany}`,[[xa+6,Y(d.rankGermany)-6,'start'],[xa+6,Y(d.rankGermany)+16,'start']],{...box,px:13,wt:600}),b=K.label(String(d.rankWithoutTopGroup),[[xb-6,Y(d.rankWithoutTopGroup)-6,'end'],[xb-6,Y(d.rankWithoutTopGroup)+16,'end']],{...box,px:13,wt:600});
  if(a)labs+=txt(a.x,a.y,`${nm(d)} ${d.rankGermany}`,'v3-lab is-on',a.a);if(b)labs+=txt(b.x,b.y,String(d.rankWithoutTopGroup),'v3-lab is-on',b.a)}
 el.innerHTML=`<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(R8())}">${g}<g class="sl-lines">${lines}</g><g class="sl-ends">${[OS,K.district(st.pick)].filter(Boolean).map(d=>`<circle r="4" cx="${xa}" cy="${Y(d.rankGermany).toFixed(1)}"/><rect x="${xb-4}" y="${(Y(d.rankWithoutTopGroup)-4).toFixed(1)}" width="8" height="8"/>`).join('')}</g>${labs}</svg>`;
 const d=K.district(st.pick);R('ro8').textContent=d&&d!==OS?fill(w('r8l'),{name:nm(d),a:d.rankGermany,b:d.rankWithoutTopGroup,g:f(d.topGroup.points),p:f(d.points),sh:pct(d.topGroup.pointShare)}):''}
const R8=()=>fill(w('r8'),{n:move(+st.m8).length,k:st.m8,a:OS.rankGermany,b:OS.rankWithoutTopGroup});

// The story for step i: a headline and one short paragraph, from the payload and the current selections. The takeaway above the frame never changes;
// the story carries the current figures, and the line inside the frame only what the reader has selected, so no sentence shows twice.
// Where a selection does not change a chart, the story says so instead of implying a filter; a district outside the chosen state is named as such.
function story(i){const S=K.state(st.state),D=K.district(st.pick),DS=D&&K.state(D.state),x=S&&D&&D.state!==S.code?fill(w('ndx'),{d:nm(D),pst:DS.name,sel:S.name}):'',r1=v=>f(v,1);
 const nd=d=>fill(w('nd'),{d:nm(d),st:ABBR[d.state],rate:r1(d.pointsPer10kResidents),rk:d.rankGermany});let h,ps;
 if(i===0){const r=st.m2==='rate',key=r?'pointsPer10kResidents':'points',top=[...ST].sort((a,b)=>b[key]-a[key])[0],rk=c=>K.rankBy(ST,key,K.state(c));
  h=fill(w(r?'n2r':'n2p'),{a:top.name,v:r1(top[key]),r:K.rankBy(ST,r?'points':'pointsPer10kResidents',top)});ps=[r?fill(w('n2g'),{g:r1(G.pointsPer10kResidents)}):w('n2c')];
  if(S)ps.push(fill(w('n2hi'),{b:rk('12'),be:rk('11'),mode:K.s.lang==='de'?(r?'nach Quote':'nach Ladepunkten'):(r?'by rate':'by points')}),fill(w('n2s'),{name:S.name,a:K.rankBy(ST,'points',S),b:S.rank}))}
 else if(i===1){if(st.m5==='flag'){const n=k=>flagged.filter(d=>d.flags.includes(k)).length;
   [h,ps]=[fill(w('n5f')[0],{n:flagged.length}),[fill(w('n5f')[1],{a:n('lowLabelCoordinateAgreement'),b:n('concentratedCoLocation'),c:n('smallPointCount'),d:n('labelGap')})]]}
  else[h,ps]=[fill(w('n5a')[0],R5()),[fill(w('n5a')[1],{...R5(),med:r1(spread.median),n:flagged.length})]];
  if(S)ps.push(fill(w('n5s'),{name:S.name,rate:r1(S.pointsPer10kResidents),min:r1(S.districtRate.min),max:r1(S.districtRate.max)}));
  if(D)ps.push((x?x+' ':'')+nd(D)+(st.m5==='flag'&&!D.flags.length?' '+w('n5u'):''))}
 // Step 3 keeps three sentences in every state (the registered group and its Brandenburg rank, the nationwide bridge, the caveat); its headline carries the scenario.
 else if(i===2){const o=bbOS[st.excluded?'hypothetical':'registered'];h=fill(w('n7')[st.excluded?1:0],{k:o.rank,r:r1(o.rate)});
  ps=[fill(w('n7p'),{g:f(fg.points),a:bbOS.registered.rank,b:bbOS.hypothetical.rank}),fill(w('n7b'),{a:OS.rankGermany,b:OS.rankWithoutTopGroup}),w('n7c')]}
 else{const k=+st.m8;h=fill(w('n8')[0],{n:move(k).length,k});ps=[fill(w('n8')[1],{a:OS.rankGermany,b:OS.rankWithoutTopGroup})];
  if(D&&D!==OS)ps.push(fill(w('r8d'),{name:nm(D),a:D.rankGermany,b:D.rankWithoutTopGroup,g:f(D.topGroup.points),p:f(D.points),sh:pct(D.topGroup.pointShare)}));
  if(S)ps.push(fill(w('n8s'),{name:S.name,m:kids(S.code).filter(d=>Math.abs(d.rankGermany-d.rankWithoutTopGroup)>=k).length,n:S.districts,k}))}
 return{h,ps:[ps.join(' ')]}}
const storyHtml=(i,tag,id)=>{const o=story(i);return`<${tag}${id?` id="${id}"`:''}>${esc(o.h)}</${tag}>${o.ps.map(p=>`<p>${esc(p)}</p>`).join('')}`};
// Every step's in-flow story is redrawn when a selection changes; the rail's only when the step in view or a selection changes (never per frame).
// The rail's foot holds its one control and is written once per render, so a step change never rebuilds anything focusable.
function tell(){K.root.querySelectorAll('.v3-story').forEach((el,i)=>el.innerHTML=storyHtml(i,'h3'));const a=K.root.querySelector('.k-rail');if(!a)return;
 if(!a.firstChild)a.innerHTML=`<div class="k-story"></div><p class="k-rail-foot"><button type="button" class="k-link" data-act="about" data-k="rabout">${t('about')}</button></p>`;
 railStory(M.room())}
function railStory(i){const a=K.root.querySelector('.k-rail .k-story');if(!a)return;a.parentElement.dataset.room=i;a.innerHTML=`<p class="k-rail-kick">${esc(w('steps')[i])}</p>`+storyHtml(i,'h2','k-rail-h')}

// Tables behind the charts, opened from each step's foot and from Explore.
const th=c=>`<th scope="col">${w(c)}</th>`;
const tables={
 state:()=>({title:w('tState'),html:`<div class="k-scroll"><table><caption>${esc(fill(w('u1'),DATES()))}; ${esc(fill(w('unitRate'),DATES()))}</caption><thead><tr>${['cState','cPts','cInst','cMw','cRes','cRate','cKw','cHi'].map(th).join('')}</tr></thead><tbody>${[...ST].sort((a,b)=>a.rank-b.rank).map(s=>`<tr><th scope="row">${esc(s.name)}</th><td>${f(s.points)}</td><td>${f(s.installations)}</td><td>${f(s.nominalMw,1)}</td><td>${f(s.population)}</td><td>${f(s.pointsPer10kResidents,1)} <span class="k-rk">#${s.rank}</span></td><td>${f(s.nominalKwPer1000Residents,1)}</td><td>${pct(s.highPowerPointShare)}</td></tr>`).join('')}</tbody><tfoot><tr><th scope="row">${w('germany')}</th><td>${f(G.points)}</td><td>${f(G.installations)}</td><td>${f(G.nominalMw,1)}</td><td>${f(G.population)}</td><td>${f(G.pointsPer10kResidents,1)}</td><td>${f(G.nominalKwPer1000Residents,1)}</td><td>${pct(G.highPowerPointShare)}</td></tr></tfoot></table></div>`}),
 flag:()=>({title:fill(w('tFlag'),{n:flagged.length}),html:`<div class="k-scroll"><table><thead><tr>${['cDist','cState','cRate','cPts','cFlags'].map(th).join('')}</tr></thead><tbody>${[...flagged].sort((a,b)=>a.state.localeCompare(b.state)||nm(a).localeCompare(nm(b),'de')).map(d=>`<tr><th scope="row">${esc(nm(d))}</th><td>${ABBR[d.state]}</td><td>${f(d.pointsPer10kResidents,1)}</td><td>${f(d.points)}</td><td class="k-wrap">${esc(d.flags.map(k=>fill(w('fl')[k],{n:f((d.labelGap||{}).points||0)})).join('; '))}</td></tr>`).join('')}</tbody></table></div>`}),
 bb:()=>({title:w('tBB'),html:`<div class="k-scroll"><table><thead><tr>${['cDist','cRate','cPts','cMw','cRes'].map(th).join('')}</tr></thead><tbody>${[...BB.districts].sort((a,b)=>a.registered.rank-b.registered.rank).map(d=>{const r=d.registered;return`<tr><th scope="row">${esc(d.name)}</th><td>${f(r.rate,1)} <span class="k-rk">#${r.rank}</span></td><td>${f(r.points)}</td><td>${f(r.kw/1000,1)}</td><td>${f(r.population)}</td></tr>`}).join('')}</tbody><tfoot><tr><th scope="row">${w('berlin')}</th><td>${f(N.berlin.registered.rate,1)}</td><td>${f(N.berlin.registered.points)}</td><td>${f(N.berlin.registered.kw/1000,1)}</td><td>${f(N.berlin.registered.population)}</td></tr></tfoot></table></div><p class="k-note">${esc(fill(w('bbNote'),{a:f(bbOS.hypothetical.points),r:f(bbOS.hypothetical.rate,1),k:bbOS.hypothetical.rank}))}</p>`}),
 move:()=>{const k=+st.m8,L=move(k).sort((a,b)=>Math.abs(b.rankGermany-b.rankWithoutTopGroup)-Math.abs(a.rankGermany-a.rankWithoutTopGroup)||nm(a).localeCompare(nm(b),'de'));return{title:fill(w('tMove'),{k,n:L.length}),html:`<div class="k-scroll"><table><thead><tr>${['cDist','cState','cRank','cRank2','cGroup'].map(th).join('')}</tr></thead><tbody>${L.map(d=>`<tr><th scope="row">${esc(nm(d))}</th><td>${ABBR[d.state]}</td><td>${d.rankGermany}</td><td>${d.rankWithoutTopGroup}</td><td>${f(d.topGroup.points)} / ${f(d.points)} · ${pct(d.topGroup.pointShare)}</td></tr>`).join('')}</tbody></table></div><p class="k-note">${esc(w('moveNote'))}</p>`}}};

// Scroll camera for the four steps. Every style it writes is a pure function of the scroll position, so reversing restores the earlier state,
// and at each hold the heading, frame and foot are untransformed with every mark at its true place. Native scrolling is never intercepted:
// one frame is requested per scroll or resize, nothing runs while idle, and reduced motion removes every written style. Explore frames are never posed.
const M=(()=>{const H=document.documentElement,mq=matchMedia('(prefers-reduced-motion: reduce)'),cl=(v,a=0,b=1)=>Math.max(a,Math.min(b,v)),ease=e=>e*e*(3-2*e);
 let on=!mq.matches,raf=0,cur=0,pin=null;H.classList.toggle('v3-motion',on);
 const top=el=>{let y=0;for(;el;el=el.offsetParent)y+=el.offsetTop;return y};
 const all=s=>[...K.root.querySelectorAll(s)],vars=(el,o)=>{for(const k in o)el.style.setProperty('--'+k,+o[k].toFixed(4))};
 // Layout ignores transforms, so these are the resting positions. A step's hold is the scroll position where its entry completes:
 // heading and frame centred together when they fit, the heading near the top when they do not.
 function geo(){const vh=H.clientHeight,hd=K.root.querySelector('.k-head').offsetHeight,av=vh-hd;
  return{vh,hd,av,y:scrollY,f:all('.v3-step').map(s=>{const f=s.querySelector('.v3-frame'),l=s.querySelector('.v3-label'),t=top(f),h=f.offsetHeight,lh=t-top(l),rest=hd+Math.max((av-h-lh)/2,12)+lh;
   return{s,f,l,o:s.querySelector('.v3-foot'),t,h,lh,rest,hold:Math.max(0,Math.round(t-rest))}})}}
 function clear(){all('.v3-copy,.v3-frame,.v3-label,.v3-foot,.v3-s,.v3-thread').forEach(e=>{if(!e.classList.contains('v3-s'))e.style.transform='';e.style.opacity='';e.style.translate='';e.style.top='';e.style.height='';if(e.classList.contains('v3-s'))e.style.transition='';
  for(const k of[...e.style])if(k.startsWith('--'))e.style.removeProperty(k)});all('.v3-frame').forEach(f=>f.classList.remove('is-asm'));const L=K.root.querySelector('.k-layout');L&&L.style.removeProperty('--rp')}
 // Chart marks assemble from one variable per frame (--a, 0–1) and their own stagger (--s); CSS draws them. At rest the class goes, so nothing is transformed.
 function asm(f,a){f.classList.toggle('is-asm',a<1);a<1?f.style.setProperty('--a',a.toFixed(4)):f.style.removeProperty('--a')}
 // A heading or foot offset by ty and faded to o; at rest nothing is written but full opacity.
 function lift(el,ty,o){el.style.transform=Math.abs(ty)>.05?`translate3d(0,${ty.toFixed(1)}px,0)`:'';el.style.opacity=o<1?o.toFixed(3):'1'}
 // Advance only when the incoming rendered chart crosses the reading line below the header.
 // Tab focus inside a step pins that step for as long as the page stays where the focus put it (a foot's Table button can rest past the midpoint).
 // Above Step 1's hold the layout is in its opening state (.is-pre): on wide screens the main column is centred on the viewport and the rail waits
 // beyond the right edge (kit.css), inert and hidden from assistive technology. With motion, --rp (0–1) carries both in by the hold; without, it switches there.
 function inView(G){const L=K.root.querySelector('.k-layout'),rl=L.querySelector('.k-rail'),pre=G.y<G.f[0].hold-1;
  if(L.classList.contains('is-pre')!==pre||rl.inert!==pre){L.classList.toggle('is-pre',pre);rl.inert=pre;pre?rl.setAttribute('aria-hidden','true'):rl.removeAttribute('aria-hidden')}let i=0;for(let j=1;j<G.f.length;j++)if(G.f[j].f.getBoundingClientRect().top<=G.hd+G.av*.4)i=j;if(pin&&Math.abs(G.y-pin.y)<2)i=pin.i;else pin=null;if(i!==cur){cur=i;railStory(i)}}
 function tick(){raf=0;if(!K.root.querySelector('.v3-step'))return;const G=geo();if(!on){inView(G);return;}const{vh,y}=G,F1=G.f[0],last=G.f.length-1;
  // Opening: the title recedes while Step 1's frame scales up from a small preview below it and its marks assemble; its heading rides on the frame's top edge.
  const e=F1.hold?cl(y/F1.hold):1,E=ease(e),copy=K.root.querySelector('.v3-copy'),k=ease(cl((e-.28)/.12)),L=K.root.querySelector('.k-layout');
  if(y<F1.hold-1)L.style.setProperty('--rp',E.toFixed(4));else L.style.removeProperty('--rp');
  copy.style.transform=`translate3d(0,${(y*.5).toFixed(1)}px,0)`+(k<1&&H.clientWidth>600?` scale(${(1+.16*k).toFixed(4)})`:'');copy.style.opacity=+(1-k).toFixed(3);vars(copy,{'exit-meta':1-ease(cl((e-.15)/.1))});
  const copyB=top(copy)+copy.offsetHeight,s0=cl(Math.min((vh-copyB-36)/F1.h,.56),.3,.56),c0=copyB+24+s0*F1.h/2,rc=F1.rest+F1.h/2;
  const s1=Math.exp(Math.log(s0)*(1-E)),ty1=(c0-rc)*(1-E)-(F1.hold-Math.min(y,F1.hold));
  cam(F1,0,G,e<1?{s:s1,ty:ty1,o:ease(cl((e-.25)/.15))}:null,last);vars(F1.f,{'cam-bg':cl((E-.25)/.5),'cam-chrome':1});asm(F1.f,cl((E-.2)/.65));F1.a=E;
  lift(F1.l,e<1?ty1+F1.h*(1-s1)/2:0,.85*ease(cl((e-.25)/.11))+.15*ease(cl((E-.7)/.3)));
  // Every later step rises and scales into place while its marks assemble; its heading leads, entering as the heading's top crosses the screen's foot.
  const enter=F=>cl((vh-(F.t-F.lh-y))/Math.max(1,vh-F.rest+F.lh));
  G.f.forEach((F,i)=>{if(!i)return;const a=enter(F),c=ease(cl(a/.7)),v=ease(cl(a/.6));F.a=a;cam(F,i,G,a<1?{s:.84+.16*c,ty:(1-c)*70,o:ease(cl(a/.45))}:null,last);
   vars(F.f,{'cam-chrome':cl((a-.45)/.45)});asm(F.f,cl(a/.85));lift(F.l,(1-v)*40,v)});
  // Step 3's strip keeps its data position in transform, so assembly uses translate and suspends the scenario transition until it lands.
  const F7=G.f.find(F=>F.f.querySelector('[data-r=strip]')),sv=F7&&F7.f.querySelector('[data-r=strip] svg');
  if(sv){const a7=cl(F7.a/.85),ds=[...sv.querySelectorAll('.v3-s')].sort((p,q)=>p._x-q._x);ds.forEach((c,i)=>{const g=ease(cl((a7-i/(ds.length-1)*.45)/.55));c.style.transition=g>=1?'':'none';c.style.translate=g>=1?'':`${((sv._x0-c._x)*(1-g)).toFixed(2)}px ${((sv._y0-c._y)*(1-g)).toFixed(2)}px`})}
  // Each foot (story and Table button) rises in after its frame and is complete, fully opaque, at that frame's hold.
  G.f.forEach(F=>{const v=ease(cl((F.a-.55)/.45));lift(F.o,(1-v)*56,v)});
  // Connectors are measured last, from rendered boxes after every pose above: from the previous step's foot to this step's heading.
  G.f.forEach((F,i)=>{const th=F.s.querySelector('.v3-thread'),sr=F.s.getBoundingClientRect(),lr=F.l.getBoundingClientRect();
   const to=lr.top-16,from=i?G.f[i-1].o.getBoundingClientRect().bottom+10:to-Math.min(96,to-G.hd),len=Math.max(0,to-from),d=i?cl(F.a/.8):cl((E-.82)/.18);
   th.style.opacity=i||d>0&&len>.5?'':'0';th.style.top=(from-sr.top).toFixed(2)+'px';th.style.height=len.toFixed(2)+'px';vars(th,{cap:i?1:cl((from-G.hd-6)/12),d,n:cl((d-.85)/.15),tip:d>0&&d<1?1:0})});inView(G)}
 // Entry pose, or after the hold a gentle recession (every step but the last) once the frame's foot passes the upper third.
 function cam(F,i,{hd,av,y},pose,last){if(!pose&&i<last){const x=ease(cl((hd+av*.35-(F.t+F.h-y))/(av*.35)));if(x>0)pose={s:1-.06*x,ty:-40*x,o:1-.5*x}}
  F.f.style.transform=pose?`translate3d(0,${pose.ty.toFixed(1)}px,0) scale(${pose.s.toFixed(4)})`:'';F.f.style.opacity=pose?pose.o.toFixed(3):'1'}
 const req=()=>{if(!raf)raf=requestAnimationFrame(tick)};
 function sync(){on=!mq.matches;H.classList.toggle('v3-motion',on);if(raf){cancelAnimationFrame(raf);raf=0}if(!on)clear();tick()}
 // Tab focus never lands on a transformed or receding element: scroll to where its frame or foot rests. Nothing outside the steps is ever posed.
 function reveal(el){const G=geo(),{vh,hd,av,y}=G,sec=el.closest('.v3-step'),last=G.f.length-1;let lo,hi,t,h;
  if(el.closest('.v3-copy')){if(y>1)scrollTo({top:0,behavior:'instant'});tick();return}
  if(!sec)return;const F=G.f.find(x=>x.s===sec),i=G.f.indexOf(F);
  if(el.closest('.v3-frame')){const r=el.getBoundingClientRect(),fr=F.f.getBoundingClientRect(),s=fr.width/F.f.offsetWidth||1;
   t=F.t+(r.top-fr.top)/s;h=r.height/s;lo=F.hold;hi=i<last?F.t+F.h-hd-av*.35:Infinity}
  else{t=top(el);h=el.offsetHeight;lo=F.hold;hi=Infinity}
  const want=cl(t+h/2-hd-av/2,lo,hi),seen=y>=lo-1&&y<=hi+1&&t-y>=hd+4&&t+h-y<=vh-4;if(!seen)scrollTo({top:Math.max(0,Math.round(want)),behavior:'instant'});tick()}
 addEventListener('scroll',req,{passive:true});addEventListener('resize',req);addEventListener('pageshow',e=>{if(e.persisted)sync()});
 mq.addEventListener('change',sync);new ResizeObserver(req).observe(document.body);
 // Only Tab moves the reader; focus restored after a dialog or a settings change stays where the reader is.
 let tabAt=-1e9;addEventListener('keydown',e=>{if(e.key==='Tab')tabAt=performance.now()},true);
 document.addEventListener('focusin',e=>{if(performance.now()-tabAt<800&&!e.target.closest('dialog'))requestAnimationFrame(()=>{if(on)reveal(e.target);const r=e.target.closest('.v3-step');if(r){pin={i:all('.v3-step').indexOf(r),y:scrollY};tick()}})});
 window.CSMotion={holds:()=>geo().f.map(F=>F.hold),room:()=>cur};
 return{update:tick,room:()=>cur}})();

function draw(){ring();bars();scatter();mix();spreadChart();comp();strip();slope();tell();M.update()}
const redraw=(...fs)=>{fs.forEach(fn=>fn());tell();M.update()};
K.start({html,draw,
 acts:{state:e=>{const v=e.tagName==='SELECT'?e.value:e.dataset.v;st.state=e.tagName!=='SELECT'&&v===st.state?'':v;K.root.querySelectorAll('select[data-act=state]').forEach(s=>s.value=st.state);redraw(bars,ring,scatter,spreadChart,strip)},
  pick:e=>{const v=e.tagName==='SELECT'?e.value:e.dataset.v;st.pick=e.tagName!=='SELECT'&&v===st.pick?'':v;K.root.querySelectorAll('select[data-act=pick]').forEach(s=>s.value=st.pick);redraw(scatter,spreadChart,strip,slope)},
  mode:e=>{st[e.dataset.m]=e.dataset.v;e.parentElement.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b===e)));redraw({m2:bars,m5:spreadChart,m6:comp,m8:slope}[e.dataset.m])},
  scen:e=>{st.excluded=e.dataset.v==='1';K.root.querySelectorAll('[data-act="scen"]').forEach(b=>b.setAttribute('aria-pressed',String(b===e)));redraw(strip)},
  table:e=>K.details(tables[e.dataset.v](),e)}});
})();
