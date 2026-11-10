// ChargeScope shell: state, words, menu, dialogs, report rail and number helpers. Adapted from the variants' shared kit;
// every figure now comes from window.NATIONAL_STORY (the national aggregate payload, shipped unchanged).
(function(){
'use strict';
const N=window.NATIONAL_STORY;
const read=k=>{try{return localStorage.getItem('chargescope-site-'+k)}catch{return null}};
const save=(k,v)=>{try{localStorage.setItem('chargescope-site-'+k,v)}catch{}};
// One appearance, Graphite dark; only the language is a stored choice. Retired theme and palette preferences (stored or ?palette=) are never read.
const s={lang:read('lang')==='de'?'de':'en'};
const SLIDES=['Counts and rates rank differently','Rates cluster; one district stands out','Oder-Spree without one flagged group','Capacity and installation size']
 .map((title,i)=>({title,src:`assets/power-bi-${i+1}.png`,thumb:`assets/power-bi-${i+1}-thumb.webp`,width:2466,height:i===3?2505:1387}));
// Contact: the two profile links from the author's CV, shown in About and the footer. No email or phone.
// Back to the analysis portfolio one level up; file:// has no directory index, so it names the page there.
const HOME=location.protocol==='file:'?'../index.html':'../';
const CONTACT=[['linkedin','https://linkedin.com/in/patilvedant'],['ghProfile','https://github.com/vedantdotsh']];
// Method sources for the Oder-Spree group: [label key, URL]. Company statement first, then contemporaneous and later reporting.
const OS_SRC=[['srcTesla','https://twitter.com/gigafactories/status/1761071149142708363'],['srcEcomento','https://ecomento.de/2024/02/27/deutsche-tesla-fabrik-bietet-ueber-500-oeffentliche-lademoeglichkeiten'],
 ['srcElectrive','https://www.electrive.net/2025/04/14/tesla-fabrik-gruenheide-hat-den-groessten-ladepark-der-welt']];
const W={
en:{skip:'Skip to content',settings:'Settings',language:'Language',by:'Analysis by Vedant Patil',close:'Close',linkedin:'LinkedIn',ghProfile:'GitHub profile',home:'All analyses',
 table:'Table',about:'Method & sources',report:'Report',reportLabel:'Report: Brandenburg case study, Power BI',reportKick:'Case study · Brandenburg',reportH:'The Power BI report',
 reportNote:'Four slides on Brandenburg’s 18 districts, in English.',viewSlides:'View the Power BI slides',download:'Download Power BI project',github:'Source on GitHub',
 enlarge:'Enlarge slide',slide:'Slide',previous:'Previous slide',next:'Next slide',fullSize:'Open full size',
 aboutH:[['Status',['Diagnostic pilot: aggregates only, not spatially validated, not a planning release.']],
  ['Sources',['Bundesnetzagentur charging register, list of {regDate}: {inst} installations, {pts} points, {kw} nominal kW. Bundesnetzagentur.de, CC BY 4.0.',
   'BKG VG250-EW residents, {popDate}: {pop} residents in 16 states and 400 districts. BKG, dl-de/by-2.0.','The two dates differ; nothing here is a time series.']],
  ['Definitions',['Point: one source point group, one vehicle at a time. The {tok} connector entries are not points.','Installation: one register record, not a physical site.',
   'Nominal kW: counted once per installation. Capacity, not energy, use or availability.','Rate: points ÷ residents × 10,000, as a ratio of sums.',
   'Above 22 kW: a point’s highest connector power. A power class, not coverage or availability.']],
  ['Geography',['States: the source Bundesland column. Districts: by source label (the Kreis column) matched to VG250, not spatially validated.',
   '{alias} Bavarian labels differ from VG250 only by spacing and were matched by name: {aliases}.',
   'Hanau: {hInst} installations and {hPts} points are in Hessen’s total but in no district, because the label is not a VG250 district. They were not reassigned, so Main-Kinzig-Kreis ({mk} by label) is not a validated rate.',
   '{low} districts have under 95% label–coordinate agreement. Coordinates are assumed WGS84, which is unconfirmed.',
   'Open checks: the coordinate reference system, unresolved assignments, and public access of large single-site groups.']],
  ['Sensitivities',['Brandenburg: one {bbG}-point single-site group in Oder-Spree (records from one operator at one coordinate) left out; Berlin is shown beside it for context and never ranked. Germany: each district’s own largest single-site group set aside. Each is a sensitivity, not a correction, and not an access claim.']],
  ['Oder-Spree group',['Register: all {bbG} records are attributed to Tesla Manufacturing Brandenburg SE in Grünheide (Mark), postcode 15537, house number 1. The street is spelled “Tesla Straße” in all but one record and “Tesla Str.” in one, so the address strings are not identical. Each record is a single-point {bbKw} kW installation listed as free of charge; only one gives opening hours (24/7). The register does not establish who can use each charger today.',
   ['In February 2024 Tesla described the chargers in the Giga Berlin car park as serving employees, visitors and guests, and wrote that all are “public and free to use”; ecomento (February 2024) and electrive (April 2025) reported the same. None of these sources maps each register record to a parking bay, and current access was not verified.',OS_SRC]]],
  ['Not measured',['Demand, adequacy, return on investment, utilisation or availability.']],
  ['Kept separate',['The Bundesnetzagentur statistics workbook ({sPts} points) also counts procedures not yet complete. It is a different population and is not reconciled with the register.']]],
 srcTesla:'Tesla on X, 23 Feb 2024',srcEcomento:'ecomento, 27 Feb 2024',srcElectrive:'electrive, 14 Apr 2025',dataJson:'Aggregates (JSON)',sources:'SOURCES.md'},
de:{skip:'Zum Inhalt',settings:'Einstellungen',language:'Sprache',by:'Analyse: Vedant Patil',close:'Schließen',linkedin:'LinkedIn',ghProfile:'GitHub-Profil',home:'Alle Analysen',
 table:'Tabelle',about:'Methode & Quellen',report:'Bericht',reportLabel:'Bericht: Fallstudie Brandenburg, Power BI',reportKick:'Fallstudie · Brandenburg',reportH:'Der Power-BI-Bericht',
 reportNote:'Vier Folien zu Brandenburgs 18 Kreisen, auf Englisch.',viewSlides:'Power-BI-Folien ansehen',download:'Power-BI-Projekt herunterladen',github:'Quellprojekt auf GitHub',
 enlarge:'Folie vergrößern',slide:'Folie',previous:'Vorherige Folie',next:'Nächste Folie',fullSize:'In voller Größe öffnen',
 aboutH:[['Status',['Diagnostischer Pilot: nur Aggregate, räumlich nicht validiert, keine Planungsgrundlage.']],
  ['Quellen',['Ladesäulenregister der Bundesnetzagentur, Liste vom {regDate}: {inst} Ladeeinrichtungen, {pts} Ladepunkte, {kw} kW Nennleistung. Bundesnetzagentur.de, CC BY 4.0.',
   'BKG VG250-EW, Einwohner zum {popDate}: {pop} Einwohner in 16 Ländern und 400 Kreisen. BKG, dl-de/by-2.0.','Die Stichtage unterscheiden sich; nichts hier ist eine Zeitreihe.']],
  ['Begriffe',['Ladepunkt: eine Ladepunktgruppe der Quelle, ein Fahrzeug zur Zeit. Die {tok} Steckereinträge sind keine Ladepunkte.','Ladeeinrichtung: ein Registerdatensatz, kein physischer Standort.',
   'Nennleistung: einmal je Ladeeinrichtung gezählt. Kapazität, keine Energie, Nutzung oder Verfügbarkeit.','Quote: Ladepunkte ÷ Einwohner × 10.000, als Verhältnis der Summen.',
   'Über 22 kW: die höchste Steckerleistung eines Ladepunkts. Eine Leistungsklasse, keine Abdeckung oder Verfügbarkeit.']],
  ['Geografie',['Länder: Quellspalte Bundesland. Kreise: nach Quellbezeichnung (Spalte Kreis), mit VG250 abgeglichen, räumlich nicht validiert.',
   '{alias} bayerische Bezeichnungen weichen von VG250 nur in Leerzeichen ab und wurden über den Namen zugeordnet: {aliases}.',
   'Hanau: {hInst} Ladeeinrichtungen und {hPts} Ladepunkte zählen zu Hessen, aber zu keinem Kreis, weil die Bezeichnung kein VG250-Kreis ist. Sie wurden nicht umgeordnet; der Main-Kinzig-Kreis ({mk} nach Bezeichnung) ist daher keine validierte Quote.',
   '{low} Kreise liegen unter 95 % Übereinstimmung zwischen Bezeichnung und Koordinate. Die Koordinaten werden als WGS84 angenommen; das ist unbestätigt.',
   'Offene Prüfungen: Koordinatenbezugssystem, ungeklärte Zuordnungen und öffentlicher Zugang großer Standortgruppen.']],
  ['Sensitivitäten',['Brandenburg: eine Standortgruppe mit {bbG} Ladepunkten in Oder-Spree (Datensätze eines Betreibers an einer Koordinate) weggelassen; Berlin wird daneben zum Vergleich gezeigt und nie gerankt. Deutschland: die jeweils größte Standortgruppe jedes Kreises herausgenommen. Beides ist eine Sensitivität, keine Korrektur und keine Aussage über Zugang.']],
  ['Gruppe in Oder-Spree',['Register: Alle {bbG} Datensätze sind der Tesla Manufacturing Brandenburg SE in Grünheide (Mark) zugeordnet, Postleitzahl 15537, Hausnummer 1. Die Straße ist in allen Datensätzen bis auf einen „Tesla Straße“ geschrieben und in einem „Tesla Str.“; die Adressangaben sind also nicht wortgleich. Jeder Datensatz ist eine Ladeeinrichtung mit einem Ladepunkt und {bbKw} kW, als kostenlos gelistet; nur einer nennt Öffnungszeiten (24/7). Wer die einzelnen Ladepunkte heute nutzen kann, legt das Register nicht fest.',
   ['Im Februar 2024 beschrieb Tesla die Ladepunkte auf dem Parkplatz der Giga Berlin als Angebot für Beschäftigte, Besucher und Gäste und schrieb, alle seien „public and free to use“; ecomento (Februar 2024) und electrive (April 2025) berichteten ebenso. Keine dieser Quellen ordnet jeden Registerdatensatz einem Stellplatz zu; der heutige Zugang wurde nicht geprüft.',OS_SRC]]],
  ['Nicht gemessen',['Bedarf, Angemessenheit, Rendite, Auslastung oder Verfügbarkeit.']],
  ['Getrennt gehalten',['Die Statistik-Arbeitsmappe der Bundesnetzagentur ({sPts} Ladepunkte) zählt auch noch nicht abgeschlossene Verfahren. Sie ist eine andere Grundgesamtheit und wird nicht mit dem Register abgeglichen.']]],
 srcTesla:'Tesla auf X, 23.02.2024',srcEcomento:'ecomento, 27.02.2024',srcElectrive:'electrive, 14.04.2025',dataJson:'Aggregate (JSON)',sources:'SOURCES.md'}};
const t=k=>W[s.lang][k]??W.en[k]??k;
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const loc=()=>s.lang==='de'?'de-DE':'en-GB';
const f=(v,d=0)=>new Intl.NumberFormat(loc(),{minimumFractionDigits:d,maximumFractionDigits:d}).format(v);
const pct=(v,d=1)=>f(v*100,d)+(s.lang==='de'?' %':'%');
const date=iso=>new Intl.DateTimeFormat(loc(),{day:'numeric',month:'short',year:'numeric',timeZone:'UTC'}).format(new Date(iso+'T00:00:00Z'));
const fill=(x,o)=>String(x).replace(/\{(\w+)\}/g,(_,k)=>o[k]??'');

// Lookups into the payload. Codes are strings; null means unknown.
const state=c=>N.states.find(x=>x.code===c),district=c=>N.districts.find(x=>x.code===c);
const ABBR={'01':'SH','02':'HH','03':'NI','04':'HB','05':'NW','06':'HE','07':'RP','08':'BW','09':'BY','10':'SL','11':'BE','12':'BB','13':'MV','14':'SN','15':'ST','16':'TH'};
const rankBy=(rows,key,row)=>1+rows.filter(o=>o[key]>row[key]).length;
const AF=()=>{const G=N.germany,m=N.meta,h=N.unattributedLabels[0];return{regDate:date(m.charging.snapshotDate),popDate:date(m.population.referenceDate),inst:f(G.installations),pts:f(G.points),
 kw:f(G.nominalKw,1),pop:f(G.population),tok:f(G.connectorTokens),alias:m.labelMapping.spacingAliases.length,aliases:m.labelMapping.spacingAliases.map(a=>district(a.code).name).join(', '),
 hInst:f(h.installations),hPts:f(h.points),mk:f(district(Object.keys(h.coordinateCandidateDistricts)[0]).pointsPer10kResidents,1),
 low:N.districts.filter(d=>d.flags.includes('lowLabelCoordinateAgreement')).length,bbG:f(N.brandenburg.flaggedGroup.points),bbKw:f(N.brandenburg.flaggedGroup.nominalKw/N.brandenburg.flaggedGroup.installations),sPts:f(N.statisticsContext.points)}};
const about=()=>{const F=AF();return t('aboutH').map(([h,items])=>`<h3>${esc(h)}</h3><ul class="k-method">${items.map(x=>Array.isArray(x)?`<li>${esc(fill(x[0],F))} ${x[1].map(([k,h])=>`<a href="${h}">${t(k)}</a>`).join(' · ')}</li>`:`<li>${esc(fill(x,F))}</li>`).join('')}</ul>`).join('')+
 `<p class="k-files"><a href="data/national-story.json" download>${t('dataJson')}</a><a href="SOURCES.md">${t('sources')}</a></p>`};

const dlgs=()=>`<dialog class="k-dlg" id="k-dt" aria-labelledby="k-dt-h"><div class="k-dlg-bar"><h2 id="k-dt-h"></h2><button type="button" class="k-btn" data-act="close">${t('close')}</button></div><div class="k-dlg-body"></div></dialog>
<dialog class="k-dlg k-drawer" id="k-rp" aria-labelledby="k-rp-h"></dialog><dialog class="k-dlg k-lb" id="k-lb"></dialog>`;
const header=()=>`<a class="k-skip" href="#main">${t('skip')}</a><header class="k-head"><a class="k-brand" href="#top">ChargeScope</a>
<button type="button" class="k-btn k-rp-btn" data-act="report" data-k="rpbtn" aria-haspopup="dialog" aria-label="${t('reportLabel')}">${t('report')}</button>
<div class="k-menu"><button type="button" class="k-btn k-menu-btn" data-act="menu" data-k="menu" aria-expanded="false" aria-controls="k-pop"><span class="k-vh">${t('settings')}: </span>${s.lang.toUpperCase()}</button>
<div class="k-pop" id="k-pop" hidden><div role="group" aria-label="${t('language')}"><span class="k-pop-h" aria-hidden="true">${t('language')}</span>${[['en','English'],['de','Deutsch']].map(([v,l])=>`<button type="button" lang="${v}" data-act="lang" data-v="${v}" data-k="l${v}" aria-pressed="${s.lang===v}">${l}</button>`).join('')}</div>
<button type="button" class="k-pop-about" data-act="about" data-k="mabout">${t('about')}</button></div></div></header>`;
const contact=()=>CONTACT.map(([k,h])=>`<a class="k-ct" href="${h}">${t(k)}</a>`).join(' · ');
const home=()=>`<p class="k-home"><a class="k-btn" href="${HOME}" data-k="home"><span aria-hidden="true">←</span> ${t('home')}</a></p>`;
const footer=()=>`<footer class="k-foot"><span>ChargeScope · ${t('by')} · ${contact()}</span><span class="k-foot-l"><button type="button" class="k-link" data-act="about" data-k="fabout">${t('about')}</button><a href="https://github.com/vedantdotsh/chargescope">GitHub</a></span></footer>`;
const links=()=>`<a class="k-dl" href="https://github.com/vedantdotsh/chargescope/releases/download/v1.0.0/ChargeScope-PowerBI-source.zip">${t('download')}</a><a class="k-gh" href="https://github.com/vedantdotsh/chargescope">${t('github')}</a>`;
// The report panel: a drawer dialog from the header Report button at every width and from the About section. (The wide-screen rail carries the step story, written by app.js.)
let slide=0;
const report=(p,hid)=>{const g=SLIDES[slide],n=SLIDES.length;return`<p class="k-rail-kick">${t('reportKick')}</p><h2${hid?` id="${hid}"`:''}>${t('reportH')}</h2><p class="k-rail-note">${t('reportNote')}</p>
<button type="button" class="k-slide" data-act="slide" data-i="${slide}" data-k="${p}s" aria-label="${t('enlarge')} ${slide+1} / ${n}: ${esc(g.title)}"><img src="${g.thumb}" width="${g.width}" height="${g.height}" alt=""></button>
<p class="k-slide-t" lang="en">${esc(g.title)}</p>
<div class="k-gnav"><button type="button" class="k-btn" data-act="gstep" data-v="-1" data-k="${p}p" aria-label="${t('previous')}">‹</button><span aria-live="polite">${slide+1} / ${n}</span><button type="button" class="k-btn" data-act="gstep" data-v="1" data-k="${p}n" aria-label="${t('next')}">›</button></div>
<p class="k-rail-links">${links()}</p><button type="button" class="k-link" data-act="about" data-k="${p}a">${t('about')}</button>`};
const drawDrawer=()=>{root.querySelector('#k-rp').innerHTML=`<div class="k-dlg-bar"><span class="k-vh" id="k-rp-h">${t('reportH')}</span><span aria-hidden="true">${t('reportKick')}</span><button type="button" class="k-btn" data-act="close" data-k="dclose">${t('close')}</button></div><div class="k-dlg-body">${report('d')}</div>`};

// Ranked rows keyed by id: re-sorting moves the same nodes, so the change animates. Screen readers get the order as one label.
// An item may bring its own rank and a short move mark for the rank cell, and a phrase (say) that spells them out in the label.
function rows(el,{items,max,ref,label}){const key=items.map(i=>i.code).sort().join();
 if(el._key!==key){el._key=key;el.innerHTML=`<div class="k-ref" hidden><span></span></div>`+items.map(i=>`<div class="k-row" data-code="${i.code}"><span class="k-rank"></span><span class="k-name"></span><span class="k-track"><span class="k-fill"></span></span><span class="k-val"></span></div>`).join('')}
 el.setAttribute('role','img');el.setAttribute('aria-label',label+': '+items.map((i,x)=>`${x+1}. ${i.name} ${i.label}${i.say?', '+i.say:''}`).join('; '));el.style.setProperty('--n',items.length);
 items.forEach((it,x)=>{const r=el.querySelector(`[data-code="${it.code}"]`);r.style.setProperty('--i',x);r.className='k-row '+(it.cls||'');r.title=it.name+': '+it.label+(it.say?' · '+it.say:'');
  r.querySelector('.k-rank').innerHTML=`<b>${it.rank??String(x+1).padStart(2,'0')}</b><i>${esc(it.move||'')}</i>`;r.querySelector('.k-name').textContent=it.name;r.querySelector('.k-val').textContent=it.label;
  r.querySelector('.k-fill').style.width=Math.min(100,it.value/max*100).toFixed(2)+'%'});
 const rf=el.querySelector('.k-ref');rf.hidden=!ref;if(ref){rf.style.setProperty('--x',(ref.value/max).toFixed(4));rf.firstChild.textContent=ref.label}}

// Label placement: the first candidate [x,y,anchor] that stays inside the box and clear of every dot and label already placed.
const cx=document.createElement('canvas').getContext('2d');
const measure=(x,px,wt=400)=>{cx.font=`${wt} ${px}px "Segoe UI",system-ui,sans-serif`;return cx.measureText(x).width};
function label(text,cands,{W,H,dots=[],taken=[],px=13,wt=400}){const tw=measure(text,px,wt)+4;
 for(const [x,y,a] of cands){const l=a==='start'?x:a==='end'?x-tw:x-tw/2,b={l,r:l+tw,t:y-px,b:y+3};
  if(b.l<0||b.r>W||b.t<0||b.b>H)continue;if(dots.some(d=>d.x+d.r>b.l&&d.x-d.r<b.r&&d.y+d.r>b.t&&d.y-d.r<b.b))continue;if(taken.some(o=>o.l<b.r&&o.r>b.l&&o.t<b.b&&o.b>b.t))continue;
  taken.push(b);return{x,y,a}}
 return null}

let app=null,root=null,lb=0,lastW=0;const back=[];
function apply(){document.documentElement.lang=s.lang}
function render(){const a=document.activeElement,k=a&&a.dataset&&a.dataset.k,menuOpen=!!root.querySelector('.k-pop:not([hidden])');
 root.innerHTML=header()+`<div class="k-layout"><main id="main">${app.html()}</main><aside class="k-rail" aria-labelledby="k-rail-h"></aside></div>`+home()+footer()+dlgs();
 app.draw();if(menuOpen)toggleMenu(true);if(k){const n=root.querySelector('[data-k="'+k+'"]');n&&n.focus({preventScroll:true})}}
function toggleMenu(open){const b=root.querySelector('.k-menu-btn'),p=root.querySelector('#k-pop');open=open??p.hidden;p.hidden=!open;b.setAttribute('aria-expanded',String(open))}
function set(p){Object.assign(s,p);if('lang'in p)save('lang',s.lang);apply();render()}
// Each dialog remembers its opener and the scroll position; closing returns focus there without moving the page.
function openDlg(id,tr){const d=root.querySelector(id);back.push({el:tr||document.activeElement,y:scrollY});d.showModal();d.scrollTop=0;const c=d.querySelector('[data-act="close"]');c&&c.focus()}
function details(x,tr){const d=root.querySelector('#k-dt');d.querySelector('#k-dt-h').textContent=x.title;d.querySelector('.k-dlg-body').innerHTML=x.html;openDlg('#k-dt',tr)}
function drawLb(){const d=root.querySelector('#k-lb'),g=SLIDES[lb],n=SLIDES.length;d.setAttribute('aria-label',`${t('reportKick')}, ${t('slide')} ${lb+1} / ${n}`);
 d.innerHTML=`<div class="k-dlg-bar"><span aria-live="polite">${t('slide')} ${lb+1} / ${n} · <span lang="en">${esc(g.title)}</span></span><span class="k-lb-nav"><button type="button" class="k-btn" data-act="lb" data-v="-1" aria-label="${t('previous')}">‹</button><button type="button" class="k-btn" data-act="lb" data-v="1" aria-label="${t('next')}">›</button><a class="k-btn" href="${g.src}" target="_blank" rel="noopener">${t('fullSize')}</a><button type="button" class="k-btn" data-act="close">${t('close')}</button></span></div><img src="${g.src}" width="${g.width}" height="${g.height}" alt="${esc(t('reportKick')+': '+g.title)}">`}
const lbMove=v=>{lb=(lb+v+SLIDES.length)%SLIDES.length;drawLb();const b=root.querySelector('#k-lb [data-act="lb"][data-v="'+(v<0?-1:1)+'"]');b&&b.focus()};
const focusK=k=>{const n=root.querySelector('[data-k="'+k+'"]');n&&n.focus({preventScroll:true})};
const acts={menu:()=>toggleMenu(),lang:e=>{set({lang:e.dataset.v});toggleMenu(false);root.querySelector('.k-menu-btn').focus({preventScroll:true})},close:e=>e.closest('dialog').close(),
 about:e=>{const opener=e.closest('.k-pop')?root.querySelector('.k-menu-btn'):e;toggleMenu(false);details({title:t('about'),html:about()},opener)},report:e=>{drawDrawer();openDlg('#k-rp',e)},
 slide:e=>{lb=Number(e.dataset.i);drawLb();openDlg('#k-lb',e)},lb:e=>lbMove(Number(e.dataset.v)),
 gstep:e=>{slide=(slide+Number(e.dataset.v)+SLIDES.length)%SLIDES.length;drawDrawer();focusK(e.dataset.k)}};
function start(a){app={details:{},acts:{},...a};root=document.getElementById('site');apply();
 const run=(x,e)=>{const fn=acts[x.dataset.act]||app.acts[x.dataset.act];fn&&fn(x,e)};
 root.addEventListener('click',e=>{const x=e.target.closest('[data-act]');if(x&&x.tagName!=='SELECT')run(x,e);
  if(!e.target.closest('.k-menu')&&!root.querySelector('#k-pop').hidden)toggleMenu(false);
  if(e.target.tagName==='DIALOG'){const b=e.target.getBoundingClientRect();if(e.clientX<b.left||e.clientX>b.right||e.clientY<b.top||e.clientY>b.bottom)e.target.close()}});
 root.addEventListener('change',e=>{if(e.target.tagName==='SELECT'&&e.target.dataset.act)run(e.target,e)});
 root.addEventListener('keydown',e=>{if(e.key==='Escape'&&!root.querySelector('#k-pop').hidden){toggleMenu(false);root.querySelector('.k-menu-btn').focus()}
  if(e.target.closest&&e.target.closest('#k-lb')&&['ArrowLeft','ArrowRight'].includes(e.key)){e.preventDefault();lbMove(e.key==='ArrowLeft'?-1:1)}});
 root.addEventListener('close',e=>{if(e.target.tagName!=='DIALOG')return;const b=back.pop();if(!b)return;if(b.el&&b.el.matches('.k-menu-btn'))toggleMenu(true);b.el&&b.el.isConnected&&b.el.focus({preventScroll:true});
  if(Math.abs(scrollY-b.y)>1)scrollTo({top:b.y,behavior:'instant'})},true);
 new ResizeObserver(()=>{const w=root.clientWidth;if(w!==lastW){lastW=w;app.draw()}}).observe(root);
 // The first render draws at this width, so the observer's initial callback redraws only if the width has changed since.
 render();lastW=root.clientWidth}
window.K={N,s,t,f,pct,date,esc,fill,state,district,ABBR,rankBy,rows,label,measure,links,contact,start,focusK,details,about,
 words:(en,de)=>{Object.assign(W.en,en);Object.assign(W.de,de)},get root(){return root}};
})();
