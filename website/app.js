/* Vedant Patil · analysis portfolio.
   Every figure comes from window.STORY (data.js, the unchanged national-story.json). Motion is a pure
   function of scroll position, so it reverses; nothing runs while the page is idle. */
(function () {
  'use strict';
  // The one place the ChargeScope destination lives (same site, same tab). file:// has no directory index, so it names the page there.
  var PROJECT = 'chargescope/';
  var PROJECT_URL = location.protocol === 'file:' ? PROJECT + 'index.html' : PROJECT;
  var CAVEATS_URL = PROJECT + 'SOURCES.md';
  var MOVE = 50, MOVE_SOME = 20, COLS = 20;

  var S = window.STORY, D = S.districts, N = D.length, M = S.meta;
  var OS = D.filter(function (d) { return d.code === '12067'; })[0];
  var root = document.documentElement;
  var $ = function (q) { return document.querySelector(q); }, $$ = function (q) { return [].slice.call(document.querySelectorAll(q)); };
  var nf = new Intl.NumberFormat('en-GB');
  var day = function (iso) { return new Date(iso + 'T00:00:00Z').toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }); };
  var clamp = function (v) { return v < 0 ? 0 : v > 1 ? 1 : v; };
  var ease = function (t) { return t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2; };
  var motion = function () { return root.classList.contains('motion'); };

  // ---- figures ----
  var shift = function (d) { return Math.abs(d.rankGermany - d.rankWithoutTopGroup); };
  var status = M.status.toLowerCase().replace(/_/g, ' ');
  var F = {
    osName: OS.name, osState: S.states.filter(function (s) { return s.code === OS.state; })[0].name,
    rankA: OS.rankGermany, rankB: OS.rankWithoutTopGroup, nDistricts: N, nStates: S.states.length,
    osTop: nf.format(OS.topGroup.points), osPoints: nf.format(OS.points), dePoints: nf.format(S.germany.points),
    status: status.charAt(0).toUpperCase() + status.slice(1), regDate: day(M.charging.snapshotDate), popDate: day(M.population.referenceDate),
    source: M.charging.source, licence: M.charging.licence, attr: M.charging.attribution, popLicence: M.population.licence,
    moveT: MOVE
  };
  $$('[data-f]').forEach(function (el) { el.textContent = F[el.dataset.f]; });
  var TO = { project: PROJECT_URL, caveats: CAVEATS_URL };
  $$('[data-to]').forEach(function (a) { a.href = TO[a.dataset.to]; });
  var mv20 = D.filter(function (d) { return shift(d) >= MOVE_SOME; }).length;
  var mv50 = D.filter(function (d) { return shift(d) >= MOVE; }).length;

  // ---- the field: 400 marks, scattered -> registered order -> what-if order ----
  // Field state s runs 0..2: 0 scattered (fixed hash of the district code, not geography), 1 registered rank, 2 what-if rank.
  var FINAL = 2;
  var hash = function (str) { var h = 2166136261; for (var i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619); } return (h >>> 0) / 4294967296; };
  var osI = D.indexOf(OS);
  var marks = D.map(function (d) { return { a: d.rankGermany - 1, b: d.rankWithoutTopGroup - 1, mover: shift(d) >= MOVE, hx: hash(d.code), hy: hash(d.code + '/y') }; });
  var ROWS = Math.ceil(N / COLS);
  var fields = $$('canvas.field');
  var label = 'Grid of ' + N + ' districts in what-if order. ' + F.osName + ' in the accent colour at ' + F.rankB +
    '; an outline marks its registered rank ' + F.rankA + '. ' + mv50 + ' districts move ' + MOVE + ' or more places.';
  fields.forEach(function (c) { if (c.getAttribute('role') === 'img') c.setAttribute('aria-label', label); });
  $('.stage').setAttribute('aria-label', 'One mark per district, not geography. Scrolling gathers ' + N + ' scattered districts into registered rank order, then re-ranks all ' + N + ' in the national what-if. ' + F.osName + ' moves from rank ' + F.rankA + ' to ' + F.rankB + ' when every district’s largest single-site group is set aside.');
  $('.cap-0').textContent = N + ' districts, one mark each, in no order yet: not a map.';
  $('.cap-a').textContent = N + ' districts ordered by registered charging points per 10,000 residents, 1 = most.';
  $('.cap-b').textContent = 'The same ' + N + ', re-ranked with every district’s largest single-site group set aside.';

  function setup(c) {
    var w = c.clientWidth, full = c.dataset.field !== 'card';
    var pl = full ? 32 : 2, pr = full ? 30 : 2, pt = full ? 22 : 2, pb = full ? 4 : 2;
    // Canvases in flow get exactly the height of their square grid; the stage fills its sticky column.
    if (w && c.dataset.field !== 'stage') c.style.height = (w - pl - pr) / COLS * ROWS + pt + pb + 'px';
    var h = c.clientHeight;
    c._g = null;
    if (!w || !h) return;
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    c.width = Math.round(w * dpr); c.height = Math.round(h * dpr);
    c._ctx = c.getContext('2d'); c._ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    var g = Math.min((w - pl - pr) / COLS, (h - pt - pb) / ROWS);
    var cs = getComputedStyle(c), v = function (n) { return cs.getPropertyValue(n).trim(); };
    c._g = { w: w, h: h, g: g, ox: pl + (w - pl - pr - COLS * g) / 2, oy: pt, full: full };
    c._t = { bg: cs.backgroundColor, mark: v('--mark'), ink: v('--ink'), muted: v('--muted'), accent: v('--accent') };
    c._p = -1;
  }
  function cell(G, i) { return [G.ox + (i % COLS + .5) * G.g, G.oy + (Math.floor(i / COLS) + .5) * G.g]; }
  function scat(G, m) { return [G.ox + G.g / 2 + m.hx * (COLS - 1) * G.g, G.oy + G.g / 2 + m.hy * (ROWS - 1) * G.g]; }
  function bez(A, B, C, t) { var u = 1 - t; return [u * u * A[0] + 2 * u * t * C[0] + t * t * B[0], u * u * A[1] + 2 * u * t * C[1] + t * t * B[1]]; }
  function text(ctx, s, x, y, color, px, align, weight) {
    ctx.font = (weight || 400) + ' ' + px + 'px "Segoe UI",system-ui,sans-serif'; ctx.fillStyle = color; ctx.textAlign = align || 'left'; ctx.fillText(s, x, y);
  }
  function draw(c, s) {
    var G = c._g;
    if (!G || c._p === s) return;
    c._p = s;
    // Phase one (s 0..1) gathers the scatter into registered order, filling from rank 1; phase two (p 0..1) re-ranks to the what-if.
    var s1 = clamp(s), p = clamp(s - 1);
    var ctx = c._ctx, T = c._t, size = G.g * .66, half = size / 2, n, t, a, b, m;
    ctx.clearRect(0, 0, G.w, G.h);
    ctx.textBaseline = 'middle';
    for (n = 0; n < N; n++) {
      if (n === osI) continue;
      m = marks[n];
      if (p > 0) { t = ease(clamp((p - .35 * m.b / N) / .65)); a = cell(G, m.a); b = cell(G, m.b); }
      else { t = ease(clamp((s1 - .35 * m.a / N) / .65)); a = scat(G, m); b = cell(G, m.a); }
      ctx.fillStyle = p > 0 && m.mover && t > .5 ? T.ink : T.mark;
      ctx.fillRect(a[0] + (b[0] - a[0]) * t - half, a[1] + (b[1] - a[1]) * t - half, size, size);
    }
    // Oder-Spree settles into its registered cell, then travels along the accent trail to its what-if cell.
    var A = cell(G, marks[osI].a), B = cell(G, marks[osI].b), C = [Math.max(A[0], B[0]) + G.g * 3, (A[1] + B[1]) / 2];
    var Z = scat(G, marks[osI]), u = ease(s1), e = ease(p);
    var at = p > 0 ? bez(A, B, C, e) : [Z[0] + (A[0] - Z[0]) * u, Z[1] + (A[1] - Z[1]) * u];
    ctx.strokeStyle = T.accent; ctx.lineWidth = G.full ? 2 : 1.5;
    if (p > 0) {
      ctx.beginPath(); ctx.moveTo(A[0], A[1]);
      for (n = 1; n <= 32; n++) { var q = bez(A, B, C, e * n / 32); ctx.lineTo(q[0], q[1]); }
      ctx.stroke();
      ctx.strokeRect(A[0] - G.g * .48, A[1] - G.g * .48, G.g * .96, G.g * .96);
    }
    var big = size * 1.3;
    ctx.fillStyle = T.accent; ctx.fillRect(at[0] - big / 2, at[1] - big / 2, big, big);
    var fs = G.g < 15 ? 11 : 12;
    if (G.full && s1 > .9) {
      for (var r = 0; r < ROWS; r += 5) text(ctx, String(r * COLS + 1), G.ox - 7, G.oy + (r + .5) * G.g, T.muted, fs - 1, 'right');
      text(ctx, String(N), G.ox + COLS * G.g + 5, G.oy + (ROWS - .5) * G.g, T.muted, fs - 1, 'left');
      if (p > .5) text(ctx, 'registered ' + F.rankA, Math.min(A[0] + G.g * .5, G.w - 2), G.oy - 11, T.muted, fs - 1, 'right');
    }
    // Labels only while the accent mark is at rest: named in the scatter, then with its registered and what-if ranks.
    var lbl = !G.full ? (p > .85 ? F.rankA + ' → ' + F.rankB : '') :
      s1 < .15 ? F.osName : s1 < .85 ? '' : p < .15 ? F.osName + ' · ' + F.rankA : p > .85 ? F.osName + ' · ' + F.rankB : F.osName;
    if (lbl) pill(ctx, G, T, lbl, at, fs + 1);
  }
  // Label beside a mark on a background chip, so it never reads on top of other marks.
  function pill(ctx, G, T, s, at, px) {
    ctx.font = '600 ' + px + 'px "Segoe UI",system-ui,sans-serif';
    var w = ctx.measureText(s).width + 10, h = px + 8, right = at[0] - G.ox < COLS * G.g * .55;
    var x = right ? at[0] + G.g * .5 : at[0] - G.g * .5 - w, y = Math.max(2, Math.min(G.h - h - 2, at[1] - h / 2));
    ctx.fillStyle = T.bg; ctx.fillRect(x, y, w, h);
    text(ctx, s, x + 5, y + h / 2 + .5, T.accent, px, 'left', 600);
  }

  // ---- How I work: small figures, all from the payload ----
  function svg(w, h, body, aria) { return '<svg viewBox="0 0 ' + w + ' ' + h + '" role="img" aria-label="' + aria + '">' + body + '</svg>'; }
  var g = S.germany, units = [['Charging points', g.points], ['Connectors', g.connectorTokens], ['Installations', g.installations]];
  var umax = Math.max.apply(null, units.map(function (u) { return u[1]; }));
  $('#mini-q').innerHTML = svg(260, 84, units.map(function (u, i) {
    var bw = u[1] / umax * 112, y = i * 28;
    return '<text class="m-t" x="0" y="' + (y + 15) + '">' + u[0] + '</text><rect class="m-bar" x="92" y="' + (y + 5) + '" width="' + bw.toFixed(1) +
      '" height="12"/><text class="m-v" x="' + (98 + bw).toFixed(1) + '" y="' + (y + 15) + '">' + nf.format(u[1]) + '</text>';
  }).join(''), 'Germany: ' + units.map(function (u) { return nf.format(u[1]) + ' ' + u[0].toLowerCase(); }).join(', ') + '.');

  var top5 = D.slice().sort(function (a, b) { return b.points - a.points || a.code.localeCompare(b.code); }).slice(0, 5);
  var ry = function (r) { return 22 + (r - 1) / (N - 1) * 92; }, prev = -99;
  var lab = top5.map(function (d, i) { return { d: d, yl: 28 + i * 19, yr: ry(d.rankGermany) }; });
  lab.slice().sort(function (a, b) { return a.yr - b.yr; }).forEach(function (l) { l.yt = Math.max(l.yr, prev + 12); prev = l.yt; });
  var rr = top5.map(function (d) { return d.rankGermany; });
  $('#mini-d').innerHTML = svg(260, 124, '<text class="m-t" x="98" y="9" text-anchor="end">largest by count</text><text class="m-t" x="200" y="9" text-anchor="middle">per-resident rank</text>' +
    '<line class="m-axis" x1="200" y1="' + ry(1) + '" x2="200" y2="' + ry(N) + '"/>' + lab.map(function (l) {
      return '<text class="m-t" x="96" y="' + (l.yl + 4) + '" text-anchor="end">' + l.d.name + '</text><path class="m-line" d="M102 ' + l.yl + 'L200 ' + l.yr.toFixed(1) +
        '"/><circle class="m-hi" cx="200" cy="' + l.yr.toFixed(1) + '" r="2.6"/><text class="m-v" x="207" y="' + (l.yt + 4).toFixed(1) + '">' + l.d.rankGermany + '</text>';
    }).join(''), 'The five districts with the most charging points rank ' + rr.join(', ') + ' of ' + N + ' per 10,000 residents.');
  $('#mini-d-cap').textContent = 'The five largest by raw count rank between ' + Math.min.apply(null, rr) + ' and ' + Math.max.apply(null, rr) + ' of ' + N + ' per resident.';

  var edges = [0, 5, 10, MOVE_SOME, MOVE], bins = edges.map(function (lo, i) {
    var hi = edges[i + 1];
    return { t: hi ? lo + '–' + (hi - 1) : lo + '+', n: D.filter(function (d) { return shift(d) >= lo && (!hi || shift(d) < hi); }).length, hi: lo >= MOVE_SOME };
  });
  var bmax = Math.max.apply(null, bins.map(function (b) { return b.n; }));
  $('#mini-c').innerHTML = svg(260, 104, '<text class="m-t" x="0" y="9">districts by places moved in the what-if</text><line class="m-axis" x1="0" y1="82" x2="256" y2="82"/>' +
    bins.map(function (b, i) {
      var h = Math.max(1.5, b.n / bmax * 52), x = 4 + i * 51;
      return '<rect class="' + (b.hi ? 'm-hi' : 'm-bar') + '" x="' + x + '" y="' + (82 - h).toFixed(1) + '" width="40" height="' + h.toFixed(1) + '"/><text class="m-v" x="' + (x + 20) +
        '" y="' + (78 - h).toFixed(1) + '" text-anchor="middle">' + b.n + '</text><text class="m-t" x="' + (x + 20) + '" y="98" text-anchor="middle">' + b.t + '</text>';
    }).join(''), 'Places moved by all ' + N + ' districts in the what-if: ' + bins.map(function (b) { return b.t + ': ' + b.n; }).join(', ') + '.');
  $('#mini-c-cap').textContent = 'Same rule for all ' + N + ': ' + mv20 + ' move ' + MOVE_SOME + '+ places, ' + mv50 + ' move ' + MOVE + '+. ' +
    nf.format(M.unattributedPoints) + ' unmatched Hanau points stay in state totals, not reassigned.';

  $('#inline-cap').textContent = motion()
    ? 'Each square is one of ' + N + ' districts. Scrolling gathers them into registered rank order, then re-ranks them; ' + F.osName + ' is the accent square.'
    : 'Each square is one of ' + N + ' districts, in what-if order. The outline marks ' + F.osName + '’s registered rank ' + F.rankA + '; the trail leads to ' + F.rankB + '.';

  // ---- thread, rail, rise: read everything, then write ----
  var page = $('#page'), thread = $('.thread'), fill = $('.thread-fill'), turn = $('.turn'), feat = $('.feat'), projects = $('#projects');
  var nodes = $$('.node'), rail = $('.rail'), stops = $$('.stop'), rises = $$('.rise'), stage = $('.stage');
  var stageC = $('[data-field=stage]'), inlineC = $('[data-field=inline]'), cardC = $('[data-field=card]'), portalC = $('[data-field=portal]');
  var secs = $$('main section[id]'), navs = $$('.top nav a'), tTop = 0, tLen = 0, pending = false;

  function placeThread() {
    var tx = parseFloat(getComputedStyle(page).getPropertyValue('--tx'));
    var n0 = nodes[0], top = n0.offsetTop + n0.parentNode.offsetTop + 7;
    var end = projects.offsetTop + feat.offsetTop + 44;
    tTop = top; tLen = end - top;
    thread.style.top = top + 'px'; thread.style.height = tLen + 'px';
    turn.style.top = (end - 1) + 'px'; turn.style.left = tx + 'px';
    turn.style.width = (projects.offsetLeft + feat.offsetLeft - tx + 2) + 'px';
  }
  function frame() {
    pending = false;
    var vh = innerHeight, y = scrollY, atEnd = y + vh >= root.scrollHeight - 2, mo = motion();
    var pt = page.getBoundingClientRect().top;
    var nodeTops = nodes.map(function (n) { return n.getBoundingClientRect().top; });
    var secTops = secs.map(function (s) { return s.getBoundingClientRect().top; });
    var railTop = rail.getBoundingClientRect().top;
    var riseTops = rises.map(function (r) { return r.getBoundingClientRect().top; });
    var inTop = inlineC.clientWidth ? inlineC.getBoundingClientRect().top : 0;

    var cur = '';
    secTops.forEach(function (t, i) { if (t < vh * .45) cur = secs[i].id; });
    navs.forEach(function (a) { a.classList.toggle('on', a.getAttribute('href') === '#' + cur); });
    if (!mo) return;
    var d = atEnd ? 1 : clamp((vh * .6 - (pt + tTop)) / tLen);
    fill.style.setProperty('--d', d.toFixed(4));
    turn.style.setProperty('--e', clamp((vh * .6 - (pt + tTop + tLen)) / 50 + (atEnd ? 1 : 0)).toFixed(3));
    nodes.forEach(function (n, i) { n.classList.toggle('on', nodeTops[i] < vh * .6 || atEnd); });
    var m = ease(clamp((vh * .8 - railTop) / (vh * .45)));
    rail.style.setProperty('--m', m.toFixed(3));
    stops.forEach(function (s, i) { s.classList.toggle('on', m >= i / (stops.length - 1) * .97); });
    rises.forEach(function (r, i) { r.style.setProperty('--q', (atEnd ? 1 : ease(clamp((vh - riseTops[i]) / (vh * .35)))).toFixed(3)); });
    if (stageC._g) {
      // Scattered at the top; registered order as the proof arrives; then the what-if while the proof holds.
      var s0 = clamp((y - vh * .03) / (vh * .47)), ps = clamp((y - vh * .58) / (vh * .5));
      stage.style.setProperty('--s0', (1 - s0).toFixed(3));
      stage.style.setProperty('--p', ps.toFixed(3));
      draw(stageC, +(s0 + ps).toFixed(3));
    }
    // Phones: the in-flow field is scattered as it enters, ordered by mid-screen, re-ranked while fully in view.
    if (inlineC._g) draw(inlineC, +(FINAL * clamp((vh - inTop - inlineC.clientHeight / 2) / (vh * .55))).toFixed(3));
  }
  function queue() { if (!pending) { pending = true; requestAnimationFrame(frame); } }
  function layout() {
    fields.forEach(setup);
    placeThread();
    var mo = motion();
    if (!mo) { stage.style.setProperty('--s0', 0); stage.style.setProperty('--p', 1); draw(stageC, FINAL); draw(inlineC, FINAL); }
    draw(cardC, FINAL);
    if (portal.open) sizePortal();
    frame();
  }

  // ---- portal: the card opens into a full-viewport page, led by the thread ----
  var portal = $('#portal'), panel = $('.p-panel'), pline = $('.p-line'), pin = $('.p-in'), opener = null, keys = null, closing = false;
  function sizePortal() {
    setup(portalC); draw(portalC, FINAL);
    var go = $('.go'), y = go.offsetTop + go.offsetHeight / 2;
    $('.p-thread').style.height = y + 'px'; $('.p-node').style.top = (y - 7) + 'px';
  }
  function openPortal(btn) {
    opener = btn;
    var r = btn.closest('.card').getBoundingClientRect(), vw = root.clientWidth, vh = innerHeight;
    root.classList.add('modal');
    portal.showModal();
    sizePortal();
    if (!motion()) { keys = null; return; }
    var from = 'translate(' + r.left + 'px,' + r.top + 'px) scale(' + (r.width / vw) + ',' + (r.height / vh) + ')';
    var at = 'translate(' + r.left + 'px,' + r.top + 'px) ';
    keys = [
      [pline, [{ transform: at + 'scaleX(0)' }, { transform: at + 'scaleX(' + (r.width / vw).toFixed(4) + ')', offset: .32 }, { transform: 'translate(0px,0px) scaleX(1)' }]],
      [panel, [{ transform: from, opacity: 0 }, { transform: from, opacity: 1, offset: .32 }, { transform: 'none', opacity: 1 }]],
      [pin, [{ opacity: 0, transform: 'translateY(16px)' }, { opacity: 0, transform: 'translateY(16px)', offset: .6 }, { opacity: 1, transform: 'none' }]]
    ];
    keys.forEach(function (k) { k[0].animate(k[1], { duration: 820, easing: 'cubic-bezier(.65,0,.25,1)' }); });
  }
  function closePortal() {
    if (!portal.open || closing) return;
    if (!keys) { portal.close(); return; }
    closing = true;
    var anims = keys.map(function (k) { return k[0].animate(k[1], { duration: 480, easing: 'cubic-bezier(.65,0,.25,1)', direction: 'reverse', fill: 'forwards' }); });
    anims[1].finished.then(function () { portal.close(); anims.forEach(function (a) { a.cancel(); }); closing = false; });
  }
  $('.open').addEventListener('click', function (e) {
    if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || e.button !== 0) return;
    e.preventDefault();
    openPortal(e.currentTarget);
  });
  $('.p-close').addEventListener('click', closePortal);
  $('.p-back').addEventListener('click', closePortal);
  portal.addEventListener('cancel', function (e) { e.preventDefault(); closePortal(); });
  portal.addEventListener('close', function () { root.classList.remove('modal'); if (opener) opener.focus(); });

  addEventListener('scroll', queue, { passive: true });
  var rt = 0;
  addEventListener('resize', function () { clearTimeout(rt); rt = setTimeout(layout, 100); });
  matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', function (e) {
    root.classList.toggle('motion', !e.matches);
    rises.forEach(function (r) { r.style.removeProperty('--q'); });
    layout();
  });
  layout();
})();
