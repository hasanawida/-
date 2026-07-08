/* ליגת הניחושים — מונדיאל 2026 · Eshkolot Oranim care home
   Vanilla-JS port of the design prototype: full re-render on state changes,
   targeted updates for text inputs and the 1s countdown tick (to keep focus). */

const CONFIG = {
  adminPin: '2026',
  defaultLang: 'he',
  accent: '#F2B32B',
  hideLocked: false,
  showAdmin: true,
  points: { dir: 1, exact: 2 } // correct 1X2 = 1 pt; exact score adds +2 (3 total)
};

const state = {
  tab: 'picks',
  name: '',
  picks: {},
  scores: {},    // my exact-score picks: { matchId: {h, a} }
  submitted: false,
  toast: '',
  toastError: false,
  results: {},
  adv: {},
  resScores: {}, // admin-entered actual scores: { matchId: {h, a} }
  lang: '',
  adminUnlocked: false,
  pinInput: '',
  pinError: false,
  now: Date.now()
};

const root = document.getElementById('app');
let toastTimer = null;

/* ---------- helpers ---------- */

function esc(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

function lang() { return state.lang || CONFIG.defaultLang; }
function dir() { return lang() === 'en' ? 'ltr' : 'rtl'; }
function t() { return STRINGS[lang()] || STRINGS.he; }

function tName(nm) {
  const L = lang();
  if (L === 'he') return nm;
  return TEAM_T[nm] ? TEAM_T[nm][L] : nm;
}

function badgeHtml(colors, small) {
  const g = 'linear-gradient(135deg,' + colors[0] + ' 0 34%,' + colors[1] + ' 34% 67%,' + colors[2] + ' 67% 100%)';
  return '<span class="badge' + (small ? ' sm' : '') + '" style="background:' + g + '"></span>';
}

function resolved() {
  return resolveMatches(buildMatches(t(), tName), state.results, state.adv, state.now, t(), tName);
}

function score(picks, scores) {
  const res = state.results || {}, rs = state.resScores || {};
  return Object.keys(res).reduce((n, id) => {
    if (!res[id] || !picks || picks[id] !== res[id]) return n;
    n += CONFIG.points.dir;
    const mine = scores && scores[id], actual = rs[id];
    if (dirFromScore(mine) && dirFromScore(actual) && +mine.h === +actual.h && +mine.a === +actual.a) {
      n += CONFIG.points.exact;
    }
    return n;
  }, 0);
}

/* True when this participant nailed the exact score of a decided match. */
function exactHit(scores, mid) {
  const mine = scores && scores[mid], actual = (state.resScores || {})[mid];
  return !!(dirFromScore(mine) && dirFromScore(actual) && +mine.h === +actual.h && +mine.a === +actual.a && (state.results || {})[mid]);
}

let pickSyncTimer = null;
let lastMyWriteAt = 0; // guards the remote-removal unlock against write races
function persistMe() {
  Store.saveMe({ name: state.name, picks: state.picks, scores: state.scores, submitted: state.submitted });
  // Already on the board: quietly push pick changes to the shared backend
  // (debounced), so an edited pick counts even without re-tapping Submit.
  if (state.submitted && state.name.trim()) {
    clearTimeout(pickSyncTimer);
    pickSyncTimer = setTimeout(() => {
      lastMyWriteAt = Date.now();
      Store.upsertParticipant(Store.deviceId(), state.name.trim(), state.picks, state.scores);
    }, 1200);
  }
}

/* '1' | 'X' | '2' derived from an exact score, or null if incomplete. */
function dirFromScore(sc) {
  if (!sc || sc.h == null || sc.a == null || sc.h === '' || sc.a === '') return null;
  const h = +sc.h, a = +sc.a;
  return h > a ? '1' : h < a ? '2' : 'X';
}

/* Registered participants, with this device's live name/picks overriding its stored row. */
function participants() {
  const reg = Store.loadBoard();
  const myId = Store.deviceId();
  const parts = Object.entries(reg).map(([id, v]) => ({
    id,
    name: id === myId && state.name.trim() ? state.name.trim() : (v.name || '—'),
    picks: id === myId ? state.picks : (v.picks || {}),
    scores: id === myId ? state.scores : (v.scores || {}),
    isMe: id === myId
  }));
  if (!parts.some(p => p.isMe) && state.name.trim()) {
    parts.push({ id: myId, name: state.name.trim(), picks: state.picks, scores: state.scores, isMe: true });
  }
  return parts;
}

function standingsRows() {
  const rows = participants().map(p => ({ name: p.name, pts: score(p.picks, p.scores), isMe: p.isMe, picks: p.picks, scores: p.scores }));
  rows.sort((a, b) => b.pts - a.pts || a.name.localeCompare(b.name, lang()));
  return rows;
}

function cupChampion(all) {
  const rFin = (state.results || {}).fin;
  const finM = all.find(m => m.id === 'fin');
  if (!(rFin && finM && finM.known)) return '';
  return rFin === '1' ? finM.home[0] : rFin === '2' ? finM.away[0] : ((state.adv || {}).fin || '');
}

function countdownFor(m) {
  if (m.locked || !m.lockAt) return null;
  const diff = m.lockAt - state.now;
  if (diff <= 0) return null;
  const s = Math.floor(diff / 1000), d = Math.floor(s / 86400);
  const pad = x => String(x).padStart(2, '0');
  const hms = pad(Math.floor(s % 86400 / 3600)) + ':' + pad(Math.floor(s % 3600 / 60)) + ':' + pad(s % 60);
  const dayPart = d === 1 ? t().dayOne : d > 1 ? d + t().days : '';
  return { text: t().lockIn + dayPart + hms, urgent: diff < 3600000 };
}

function openPickCount(all) {
  return all.filter(m => !m.locked && state.picks[m.id]).length;
}

function submitState(all) {
  const open = openPickCount(all);
  const total = Object.keys(state.picks).filter(k => state.picks[k]).length;
  const count = open > 0 ? open : total;
  const canSubmit = count > 0 && state.name.trim().length > 1;
  const label = !state.name.trim() ? t().enterName :
    count === 0 ? t().pickOne :
    (state.submitted ? t().update : t().send) + (count === 1 ? t().guessOne : count + t().guesses);
  return { count, canSubmit, label };
}

/* ---------- screens ---------- */

function renderPicksScreen(all) {
  const shown = CONFIG.hideLocked ? all.filter(m => !m.locked) : all;
  const S = t();
  const finished = !!cupChampion(all);

  const cards = shown.map(m => {
    const pick = state.picks[m.id];
    const cd = countdownFor(m);
    const dis = m.locked ? ' disabled' : '';
    const btn = (v, cls) => 'class="pick-btn' + (pick === v ? ' selected' : '') + (cls || '') + '" data-action="pick" data-match="' + m.id + '" data-val="' + v + '"' + dis;
    return '' +
      '<div class="match-card' + (m.locked ? ' locked' : '') + '" data-mid="' + m.id + '">' +
        '<div class="match-head">' +
          '<span class="match-round">' + esc(m.round) + '</span>' +
          '<span class="match-date">' + esc(m.date) + '</span>' +
        '</div>' +
        (cd ? '<div class="countdown' + (cd.urgent ? ' urgent' : '') + '" data-countdown="' + m.id + '" dir="' + dir() + '">' + esc(cd.text) + '</div>' : '') +
        '<div class="pick-grid">' +
          '<button ' + btn('1') + '>' + badgeHtml(m.home[1]) +
            '<span class="pick-team">' + esc(tName(m.home[0])) + '</span><span class="pick-num">1</span></button>' +
          '<button ' + btn('X') + '><span class="pick-x">X</span>' +
            '<span class="pick-draw">' + esc(S.draw) + '</span><span class="pick-num">' + esc(S.min90) + '</span></button>' +
          '<button ' + btn('2') + '>' + badgeHtml(m.away[1]) +
            '<span class="pick-team">' + esc(tName(m.away[0])) + '</span><span class="pick-num">2</span></button>' +
        '</div>' +
        (m.known ? scoreRowHtml(m, (state.scores || {})[m.id], m.locked, false) : '') +
        (m.note ? '<div class="match-note">' + esc(m.note) + '</div>' : '') +
      '</div>';
  }).join('');

  const sub = submitState(all);
  const shareBtn = (sub.count > 0
    ? '<button class="wa-btn" data-action="share-picks">' + esc(S.shareWa) + '</button>' : '') +
    '<button class="wa-btn" data-action="share-app">' + esc(S.shareApp) + '</button>';

  const helpOpen = state.helpOpen;
  const helpCard = '' +
    '<div class="help-card' + (helpOpen ? ' open' : '') + '">' +
      '<div class="help-head" data-action="help"><span>' + esc(S.helpTitle) + '</span><span class="help-chev">\u25bc</span></div>' +
      '<div class="help-body">' +
        '<div class="help-what">' + esc(S.helpWhat) + '</div>' +
        [S.helpS1, S.helpS2, S.helpS3, S.helpS4, S.helpS5].map((txt, i) =>
          '<div class="help-step"><span class="help-step-num">' + (i + 1) + '</span><span>' + esc(txt) + '</span></div>').join('') +
        '<div class="help-scoring">' + esc(S.helpScoring) + '</div>' +
      '</div>' +
    '</div>';

  return '' +
    '<div class="screen-picks">' +
      (finished ? '<div class="finished-banner">' + esc(S.finishedBanner) + '</div>' : '') +
      helpCard +
      '<div class="name-card">' +
        '<span class="name-label">' + esc(S.yourName) + '</span>' +
        (state.submitted && state.name.trim()
          ? '<span class="name-fixed">' + esc(state.name) + '</span><span class="name-lock">\ud83d\udd12</span>'
          : '<input class="name-input" data-input="name" value="' + esc(state.name) + '" placeholder="' + esc(S.namePh) + '">') +
      '</div>' +
      (state.submitted && state.name.trim()
        ? '<div class="name-note">' + esc(S.nameLockedNote) + '</div>' : '') +
      cards + shareBtn +
    '</div>' +
    '<div class="submit-bar">' +
      '<button class="submit-btn' + (sub.canSubmit ? ' enabled' : '') + '" data-action="submit">' + esc(sub.label) + '</button>' +
    '</div>';
}

/* Two small numeric inputs for an exact score. isAdmin switches label + green accent. */
function scoreRowHtml(m, sc, locked, isAdmin) {
  const S = t();
  const dis = locked ? ' disabled' : '';
  const attr = isAdmin ? 'data-rscore' : 'data-score';
  const val = side => (sc && sc[side] != null && sc[side] !== '' ? esc(sc[side]) : '');
  // Grid matches the 1/X/2 button columns, so each score box sits directly
  // under its team's button — unambiguous in both RTL and LTR.
  return '<div class="score-label">' + esc(isAdmin ? S.adminScoreLabel : S.scoreLabel) + '</div>' +
  '<div class="score-row' + (isAdmin ? ' admin' : '') + '">' +
    '<input class="score-input" type="tel" inputmode="numeric" maxlength="2" ' + attr + '="' + m.id + '" data-side="h" value="' + val('h') + '"' + dis + '>' +
    '<span class="score-colon">:</span>' +
    '<input class="score-input" type="tel" inputmode="numeric" maxlength="2" ' + attr + '="' + m.id + '" data-side="a" value="' + val('a') + '"' + dis + '>' +
  '</div>';
}

/* "1 · France · 2:1 ⭐" — direction pick + optional exact score + star on exact hit. */
function pickChipLabel(m, v, sc) {
  const S = t();
  let label = v === 'X' ? 'X · ' + S.draw : v === '1' ? '1 · ' + tName(m.home[0]) : '2 · ' + tName(m.away[0]);
  if (dirFromScore(sc)) label += ' · ' + sc.h + ':' + sc.a;
  return label;
}

/* Per-match cards listing each participant's pick. includeUnlocked=true is the
   admin view (behind the PIN gate) — it also shows picks for open matches. */
function breakdownGroups(all, includeUnlocked) {
  const S = t();
  const parts = participants();
  return all.filter(m => m.known && (includeUnlocked || m.locked)).map(m => {
    const res = (state.results || {})[m.id];
    const prow = parts.filter(p => p.picks && p.picks[m.id]).map(p => {
      const v = p.picks[m.id];
      const label = pickChipLabel(m, v, (p.scores || {})[m.id]) + (exactHit(p.scores, m.id) ? ' \u2b50' : '');
      const ok = res ? v === res : null;
      const cls = ok === null ? '' : ok ? ' ok' : ' bad';
      return '<div class="breakdown-row"><span class="breakdown-name">' + esc(p.name) + '</span>' +
        '<span class="pick-chip' + cls + '">' + esc(label) + '</span></div>';
    });
    if (!prow.length) return '';
    return '<div class="breakdown-card">' +
      '<div class="breakdown-card-head">' +
        '<span class="breakdown-match">' + esc(tName(m.home[0]) + ' — ' + tName(m.away[0])) + '</span>' +
        '<span class="breakdown-round">' + esc(m.round) + '</span>' +
      '</div>' + prow.join('') + '</div>';
  }).filter(Boolean);
}

function renderBoardScreen(all) {
  const S = t();
  const rows = standingsRows();
  const champ = cupChampion(all);
  const finished = !!champ;

  const champNames = rows.length ? rows.filter(r => r.pts === rows[0].pts).map(r => r.name).join(' · ') : '';
  const champCard = finished && rows.length ? '' +
    '<div class="champ-card">' +
      '<span class="champ-label">' + esc(S.champLabel) + '</span>' +
      '<span class="champ-name">' + esc(champNames) + '</span>' +
      '<span class="champ-sub">' + esc(rows[0].pts + S.champSubA + tName(champ)) + '</span>' +
    '</div>' : '';

  const rowsHtml = rows.map((r, i) => {
    const expanded = state.expandedRow === r.name;
    let detail = '';
    if (expanded) {
      const lockedRows = all.filter(m => m.locked && m.known && r.picks && r.picks[m.id]).map(m => {
        const v = r.picks[m.id];
        const res = (state.results || {})[m.id];
        const ok = res ? v === res : null;
        const cls = ok === null ? '' : ok ? ' ok' : ' bad';
        const label = pickChipLabel(m, v, (r.scores || {})[m.id]) + (exactHit(r.scores, m.id) ? ' \u2b50' : '');
        return '<div class="breakdown-row"><span class="breakdown-name">' + esc(tName(m.home[0]) + ' \u2014 ' + tName(m.away[0])) + '</span>' +
          '<span class="pick-chip' + cls + '">' + esc(label) + '</span></div>';
      });
      const hiddenCount = all.filter(m => !m.locked && r.picks && r.picks[m.id]).length;
      detail = '<div class="row-detail">' +
        (lockedRows.length ? lockedRows.join('') : '<div class="row-detail-empty">' + esc(S.rowNoRevealed) + '</div>') +
        (hiddenCount ? '<div class="row-detail-note">' + esc(S.rowHiddenA + hiddenCount + S.rowHiddenB) + '</div>' : '') +
      '</div>';
    }
    return '' +
    '<div class="board-item">' +
      '<div class="board-row' + (r.isMe ? ' me' : '') + (expanded ? ' open' : '') + '" data-action="row" data-val="' + esc(r.name) + '">' +
        '<span class="rank' + (i < 3 ? ' r' + (i + 1) : '') + '">' + (i + 1) + '</span>' +
        '<span class="board-name">' + esc(r.name) + '</span>' +
        (r.isMe ? '<span class="you-badge">' + esc(S.youBadge) + '</span>' : '') +
        '<span class="board-pts">' + r.pts + '</span>' +
      '</div>' + detail +
    '</div>';
  }).join('');

  /* Picks are revealed per match only once it locks, to prevent copying. */
  const groups = breakdownGroups(all, false);
  return '' +
    '<div class="screen-board">' +
      '<div class="section-head">' +
        '<span class="section-title">' + esc(S.boardTitle) + '</span>' +
        '<span class="section-sub">' + esc(S.boardSub) + '</span>' +
      '</div>' +
      champCard +
      (rows.length ? rowsHtml : '<div class="empty-card">' + esc(S.boardEmptyText) + '</div>') +
      '<div class="board-footer">' + esc(S.footerA + rows.length + S.footerB) + '</div>' +
      '<button class="wa-btn" style="margin-top:4px" data-action="share-board">' + esc(S.shareWa) + '</button>' +
      '<div class="breakdown-wrap">' +
        '<div class="breakdown-head">' +
          '<span class="breakdown-title">' + esc(S.whoPicked) + '</span>' +
          '<span class="breakdown-note">' + esc(S.revealNote) + '</span>' +
        '</div>' +
        (groups.length ? groups.join('') : '<div class="breakdown-empty">' + esc(S.breakdownEmptyText) + '</div>') +
      '</div>' +
    '</div>';
}

function treeNode(m, isFinal) {
  const r = (state.results || {})[m.id];
  const advSel = (state.adv || {})[m.id];
  const winnerName = r ? (r === '1' ? m.home[0] : r === '2' ? m.away[0] : advSel || null) : null;
  const nameCls = nm =>
    winnerName ? (winnerName === nm ? 'winner' : 'loser') : (m.known ? 'known' : '');
  const meta = winnerName
    ? t().advancedTo + tName(winnerName)
    : (r === 'X' && !advSel ? t().pendingDraw : m.date);
  return '<div class="tree-node' + (isFinal ? ' final' : '') + '">' +
    '<div class="tree-team">' + badgeHtml(m.home[1], true) +
      '<span class="tree-name ' + nameCls(m.home[0]) + '">' + esc(tName(m.home[0])) + '</span></div>' +
    '<div class="tree-team">' + badgeHtml(m.away[1], true) +
      '<span class="tree-name ' + nameCls(m.away[0]) + '">' + esc(tName(m.away[0])) + '</span></div>' +
    '<div class="tree-meta">' + esc(meta) + '</div>' +
  '</div>';
}

function renderTreeScreen(all) {
  const S = t();
  const byId = {};
  all.forEach(m => { byId[m.id] = m; });
  const champ = cupChampion(all);
  const champChip = champ ? '' +
    '<div class="tree-champ-chip">' +
      '<span class="tree-champ-label">' + esc(S.worldChamp) + '</span>' +
      '<span class="tree-champ-name">' + esc(tName(champ)) + '</span>' +
    '</div>' : '';

  return '' +
    '<div class="screen-tree">' +
      '<div class="section-head">' +
        '<span class="section-title">' + esc(S.treeTitle) + '</span>' +
        '<span class="section-sub">' + esc(S.treeSub) + '</span>' +
      '</div>' +
      '<div class="tree-scroll"><div class="tree-cols">' +
        '<div class="tree-col"><div class="tree-col-title">' + esc(S.colQF) + '</div>' +
          '<div class="tree-col-body">' + ['qf1', 'qf2', 'qf3', 'qf4'].map(id => treeNode(byId[id])).join('') + '</div></div>' +
        '<div class="tree-col"><div class="tree-col-title">' + esc(S.colSF) + '</div>' +
          '<div class="tree-col-body">' + ['sf1', 'sf2'].map(id => treeNode(byId[id])).join('') + '</div></div>' +
        '<div class="tree-col"><div class="tree-col-title gold">' + esc(S.colFin) + '</div>' +
          '<div class="tree-col-body center">' + treeNode(byId.fin, true) + champChip + '</div></div>' +
      '</div></div>' +
      '<div class="tree-hint">' + esc(S.treeHint) + '</div>' +
    '</div>';
}

function renderPinScreen() {
  const S = t();
  return '' +
    '<div class="screen-pin">' +
      '<div class="pin-glyph">#</div>' +
      '<div class="pin-title">' + esc(S.adminArea) + '</div>' +
      '<div class="pin-hint">' + esc(S.adminPinHint) + '</div>' +
      '<input class="pin-input" data-input="pin" type="password" inputmode="numeric" maxlength="6" value="' + esc(state.pinInput) + '" placeholder="••••">' +
      (state.pinError ? '<div class="pin-error">' + esc(S.wrongPin) + '</div>' : '') +
      '<button class="pin-enter" data-action="try-pin">' + esc(S.enter) + '</button>' +
    '</div>';
}

/* Pull finished-match scores from TheSportsDB (free, keyless, browser-callable)
   and stage them for one-tap admin confirmation. FIFA World Cup league id 4429. */
function fetchLiveResults() {
  state.fetchState = 'loading';
  state.fetched = [];
  render();
  fetch('https://www.thesportsdb.com/api/v1/json/3/eventsseason.php?id=4429&s=2026')
    .then(r => { if (!r.ok) throw new Error('http'); return r.json(); })
    .then(data => {
      const events = (data && data.events) || [];
      const all = resolved();
      const found = [];
      all.filter(m => m.known).forEach(m => {
        const homeEn = ((TEAM_T[m.home[0]] || {}).en || m.home[0]).toLowerCase();
        const awayEn = ((TEAM_T[m.away[0]] || {}).en || m.away[0]).toLowerCase();
        const ev = events.find(e => {
          const eh = (e.strHomeTeam || '').toLowerCase(), ea = (e.strAwayTeam || '').toLowerCase();
          return (eh.includes(homeEn) && ea.includes(awayEn)) || (eh.includes(awayEn) && ea.includes(homeEn));
        });
        if (!ev || ev.intHomeScore == null || ev.intAwayScore == null) return;
        const swapped = (ev.strHomeTeam || '').toLowerCase().includes(awayEn);
        const h = +(swapped ? ev.intAwayScore : ev.intHomeScore);
        const a = +(swapped ? ev.intHomeScore : ev.intAwayScore);
        const cur = (state.resScores || {})[m.id];
        if (cur && +cur.h === h && +cur.a === a) return; // already applied
        found.push({ mid: m.id, h, a, title: tName(m.home[0]) + ' \u2014 ' + tName(m.away[0]) });
      });
      state.fetchState = found.length ? 'found' : 'none';
      state.fetched = found;
      render();
    })
    .catch(() => { state.fetchState = 'error'; render(); });
}

function applyFetched() {
  const results = { ...state.results };
  const resScores = { ...state.resScores };
  const adv = { ...state.adv };
  (state.fetched || []).forEach(fr => {
    resScores[fr.mid] = { h: fr.h, a: fr.a };
    const d = dirFromScore({ h: fr.h, a: fr.a });
    results[fr.mid] = d;
    if (d !== 'X') delete adv[fr.mid];
  });
  saveResultsState(results, adv, resScores);
  state.fetchState = '';
  state.fetched = [];
  showToast(t().fetchApplied);
}

function renderAdminScreen(all) {
  const S = t();
  const cards = all.filter(m => m.known).map(m => {
    const r = (state.results || {})[m.id];
    const sel = (state.adv || {})[m.id];
    const btn = v => 'class="pick-btn' + (r === v ? ' res-selected' : '') + '" data-action="result" data-match="' + m.id + '" data-val="' + v + '"';
    const advRow = r === 'X' ? '' +
      '<div class="adv-wrap">' +
        '<span class="adv-label">' + esc(S.drawWho) + '</span>' +
        '<div class="adv-row">' +
          '<button class="adv-btn' + (sel === m.home[0] ? ' on' : '') + '" data-action="adv" data-match="' + m.id + '" data-val="' + esc(m.home[0]) + '">' + esc(S.advancedWord + tName(m.home[0])) + '</button>' +
          '<button class="adv-btn' + (sel === m.away[0] ? ' on' : '') + '" data-action="adv" data-match="' + m.id + '" data-val="' + esc(m.away[0]) + '">' + esc(S.advancedWord + tName(m.away[0])) + '</button>' +
        '</div>' +
      '</div>' : '';
    return '' +
      '<div class="match-card">' +
        '<div class="match-head">' +
          '<span class="match-round admin">' + esc(m.round) + '</span>' +
          '<span class="match-date">' + esc(m.date) + '</span>' +
        '</div>' +
        '<div class="pick-grid">' +
          '<button ' + btn('1') + '>' + badgeHtml(m.home[1]) +
            '<span class="pick-team">' + esc(tName(m.home[0])) + '</span><span class="pick-num">1</span></button>' +
          '<button ' + btn('X') + '><span class="pick-x">X</span>' +
            '<span class="pick-draw">' + esc(S.draw) + '</span><span class="pick-num">' + esc(S.min90) + '</span></button>' +
          '<button ' + btn('2') + '>' + badgeHtml(m.away[1]) +
            '<span class="pick-team">' + esc(tName(m.away[0])) + '</span><span class="pick-num">2</span></button>' +
        '</div>' +
        scoreRowHtml(m, (state.resScores || {})[m.id], false, true) +
        advRow +
      '</div>';
  }).join('');

  const reg = Store.loadBoard();
  const partRows = Object.entries(reg).map(([id, v]) => {
    const pts = score(v.picks || {}, v.scores || {});
    const nPicks = Object.keys(v.picks || {}).filter(k => (v.picks || {})[k]).length;
    return '<div class="part-row">' +
      '<span class="board-name">' + esc(v.name || '—') + '</span>' +
      '<span class="part-meta">' + nPicks + ' · ' + pts + '</span>' +
      (state.armedRemove === id
        ? '<button class="remove-btn armed" data-action="remove-participant" data-val="' + esc(id) + '">' + esc(S.confirmRemove) + '</button>'
        : '<button class="remove-btn" data-action="remove-participant" data-val="' + esc(id) + '">\u2715</button>') +
    '</div>';
  }).join('');
  const partsSection = '' +
    '<div class="breakdown-wrap">' +
      '<div class="breakdown-head">' +
        '<span class="breakdown-title">' + esc(S.adminParticipants) + '</span>' +
        '<span class="breakdown-note">' + esc(S.adminPartNote) + '</span>' +
      '</div>' +
      (partRows || '<div class="breakdown-empty">' + esc(S.adminPicksEmpty) + '</div>') +
    '</div>';

  const groups = breakdownGroups(all, true);
  const picksSection = '' +
    '<div class="breakdown-wrap">' +
      '<div class="breakdown-head">' +
        '<span class="breakdown-title">' + esc(S.adminPicksTitle) + '</span>' +
        '<span class="breakdown-note">' + esc(S.adminPicksNote) + '</span>' +
      '</div>' +
      (groups.length ? groups.join('') : '<div class="breakdown-empty">' + esc(S.adminPicksEmpty) + '</div>') +
    '</div>';

  const fs = state.fetchState;
  let fetchCard = '<button class="fetch-btn" data-action="fetch-results"' + (fs === 'loading' ? ' disabled' : '') + '>' +
    esc(fs === 'loading' ? S.fetching : S.fetchResults) + '</button>';
  if (fs === 'none' || fs === 'error') {
    fetchCard += '<div class="fetch-msg">' + esc(fs === 'none' ? S.fetchNone : S.fetchErr) + '</div>';
  } else if (fs === 'found') {
    fetchCard += '<div class="fetch-preview">' +
      '<div class="fetch-title">' + esc(S.fetchFoundA + state.fetched.length + S.fetchFoundB) + '</div>' +
      state.fetched.map(fr => '<div class="fetch-row"><span>' + esc(fr.title) + '</span><b>' + fr.h + ':' + fr.a + '</b></div>').join('') +
      '<div class="fetch-actions">' +
        '<button class="fetch-apply" data-action="fetch-apply">' + esc(S.fetchApply) + '</button>' +
        '<button class="fetch-cancel" data-action="fetch-cancel">' + esc(S.fetchCancel) + '</button>' +
      '</div>' +
    '</div>';
  }

  return '' +
    '<div class="screen-admin">' +
      '<div class="admin-info">' + esc(S.adminInfo) + '</div>' +
      '<div class="fetch-card">' + fetchCard + '</div>' +
      cards +
      '<button class="reset-btn' + (state.armedRemove === 'reset-all' ? ' armed' : '') + '" data-action="reset-results">' +
        esc(state.armedRemove === 'reset-all' ? S.confirmRemove : S.resetResults) + '</button>' +
      partsSection +
      picksSection +
    '</div>';
}

/* ---------- full render ---------- */

function render() {
  const S = t();
  const all = resolved();
  const L = lang();

  document.documentElement.lang = L;
  document.documentElement.dir = dir();
  document.title = S.title;

  const langBtn = (l, label) =>
    '<button class="lang-btn' + (L === l ? ' active' : '') + '" data-action="lang" data-val="' + l + '">' + label + '</button>';
  const tabBtn = (tab, label) =>
    '<button class="tab-btn' + (state.tab === tab ? ' active' : '') + '" data-action="tab" data-val="' + tab + '">' + esc(label) + '</button>';

  let screen;
  if (state.tab === 'board') screen = renderBoardScreen(all);
  else if (state.tab === 'tree') screen = renderTreeScreen(all);
  else if (state.tab === 'admin') screen = state.adminUnlocked ? renderAdminScreen(all) : renderPinScreen();
  else screen = renderPicksScreen(all);

  root.innerHTML = '' +
    '<div class="lang-row">' + langBtn('he', 'עברית') + langBtn('ar', 'العربية') + langBtn('en', 'EN') + '</div>' +
    '<header class="app-header">' +
      '<div class="logo-tile"><img src="assets/logo.jpg" alt="אשכולות אורנים"></div>' +
      '<div class="head-text">' +
        '<div class="app-title">' + esc(S.title) + '</div>' +
        '<div class="app-subtitle">' + esc(S.subtitle) + '</div>' +
      '</div>' +
    '</header>' +
    '<div class="prize-banner">' +
      '<div class="prize-coin">₪</div>' +
      '<div class="prize-text">' +
        '<span class="prize-title">' + esc(S.prizeTitle) + '</span>' +
        '<span class="prize-sub">' + esc(S.prizeSub) + '</span>' +
      '</div>' +
    '</div>' +
    '<div class="tab-row">' +
      tabBtn('picks', S.tabPicks) + tabBtn('board', S.tabBoard) + tabBtn('tree', S.tabTree) +
      (CONFIG.showAdmin ? tabBtn('admin', S.tabAdmin) : '') +
    '</div>' +
    screen;
}

/* ---------- targeted updates (keep input focus, 1s tick) ---------- */

function updateSubmitBar() {
  const btn = root.querySelector('[data-action="submit"]');
  if (!btn) return;
  const sub = submitState(resolved());
  btn.textContent = sub.label;
  btn.classList.toggle('enabled', sub.canSubmit);
}

/* Render unless the user is typing; deferred renders are flushed by tick(). */
function safeRender() {
  const a = document.activeElement;
  if (a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA')) {
    state.pendingRender = true;
    return;
  }
  state.pendingRender = false;
  render();
}

let lockAtCache = null; // constant per session — match lock times don't change
function allLockAts() {
  if (!lockAtCache) lockAtCache = resolved().map(m => m.lockAt).filter(Boolean);
  return lockAtCache;
}

function tick() {
  const prev = state.now;
  state.now = Date.now();
  const a = document.activeElement;
  const typing = a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA');
  if (state.pendingRender && !typing) { safeRender(); return; }
  const crossed = allLockAts().some(ts => ts > prev && ts <= state.now);
  if (crossed) { safeRender(); return; } // a match just locked
  const els = root.querySelectorAll('[data-countdown]');
  if (!els.length) return; // nothing ticking on this screen — skip all work
  const all = resolved();
  els.forEach(el => {
    const m = all.find(x => x.id === el.getAttribute('data-countdown'));
    const cd = m && countdownFor(m);
    if (!cd) { el.textContent = ''; return; }
    el.textContent = cd.text;
    el.classList.toggle('urgent', cd.urgent);
  });
}

/* ---------- actions ---------- */

function showToast(msg, isError) {
  const old = document.querySelector('.toast');
  if (old) old.remove();
  const el = document.createElement('div');
  el.className = 'toast' + (isError ? ' error' : '');
  el.textContent = msg;
  document.body.appendChild(el);
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.remove(), 2600);
}

function tryPin() {
  if (state.pinInput === String(CONFIG.adminPin)) {
    state.adminUnlocked = true; state.pinInput = ''; state.pinError = false;
  } else {
    state.pinError = true; state.pinInput = '';
  }
  render();
}

function saveResultsState(results, adv, resScores) {
  state.results = results;
  state.adv = adv;
  state.resScores = resScores;
  Store.saveResults(results, adv, resScores);
}

function waShare(text) {
  const url = 'https://wa.me/?text=' + encodeURIComponent(text);
  let w = null;
  try { w = window.open(url, '_blank'); } catch (e) {}
  if (!w) location.href = url; // popup blocked (in-app browsers) — navigate instead
}

function sharePicksText(all) {
  const S = t();
  const pickLabelFor = m => {
    const v = state.picks[m.id];
    let lbl = v === 'X' ? 'X (' + S.draw + ')' : v === '1' ? tName(m.home[0]) : tName(m.away[0]);
    const sc = (state.scores || {})[m.id];
    if (dirFromScore(sc)) lbl += ' ' + sc.h + ':' + sc.a;
    return lbl;
  };
  const lines = all.filter(m => state.picks[m.id])
    .map(m => '- ' + tName(m.home[0]) + ' / ' + tName(m.away[0]) + ': ' + pickLabelFor(m)).join('\n');
  return S.title + '\n' + (state.name.trim() ? state.name.trim() + ' — ' : '') + S.shareMyPicks + '\n' + lines + '\n\n' + S.prizeTitle;
}

function shareAppText() {
  const S = t();
  return '⚽ ' + S.title + ' — ' + S.subtitle + ' 🏆\n' + S.inviteText + '\n' + location.href;
}

function shareBoardText() {
  const S = t();
  return S.title + '\n' + S.boardTitle + ':\n' +
    standingsRows().map((p, i) => (i + 1) + '. ' + p.name + ' — ' + p.pts).join('\n');
}

root.addEventListener('click', e => {
  const el = e.target.closest('[data-action]');
  if (!el || el.disabled) return;
  const action = el.getAttribute('data-action');
  const mid = el.getAttribute('data-match');
  const val = el.getAttribute('data-val');

  switch (action) {
    case 'lang':
      state.lang = val;
      Store.saveLang(val);
      render();
      break;
    case 'tab':
      state.tab = val;
      render();
      break;
    case 'pick': {
      const m = resolved().find(x => x.id === mid);
      if (!m || m.locked) return;
      const newPick = state.picks[mid] === val ? undefined : val;
      state.picks = { ...state.picks, [mid]: newPick };
      const scDir = dirFromScore((state.scores || {})[mid]);
      if (scDir && scDir !== newPick) { // cleared or contradicting → drop the exact score
        const scores = { ...state.scores };
        delete scores[mid];
        state.scores = scores;
      }
      persistMe();
      render();
      break;
    }
    case 'submit': {
      const sub = submitState(resolved());
      if (!sub.canSubmit) return;
      if (!Store.isLoaded()) { Store.refresh(); showToast(t().syncWait, true); return; }
      const myId = Store.deviceId();
      const nm = state.name.trim();
      const taken = Object.entries(Store.loadBoard())
        .some(([id, v]) => id !== myId && (v.name || '').trim().toLowerCase() === nm.toLowerCase());
      if (taken) { showToast(t().nameTaken, true); return; }
      lastMyWriteAt = Date.now();
      Store.upsertParticipant(myId, nm, state.picks, state.scores).then(okWrite => {
        if (!okWrite) { showToast(t().netErr, true); return; }
        lastMyWriteAt = Date.now();
        if (!state.submitted) { state.submitted = true; persistMe(); safeRender(); }
        showToast(t().toastSaved);
      });
      break;
    }
    case 'share-picks':
      waShare(sharePicksText(resolved()));
      break;
    case 'share-board':
      waShare(shareBoardText());
      break;
    case 'share-app':
      waShare(shareAppText());
      break;
    case 'help':
      state.helpOpen = !state.helpOpen;
      try { localStorage.setItem('wc26-oranim-help', state.helpOpen ? '' : '1'); } catch (err) {}
      render();
      break;
    case 'row':
      state.expandedRow = state.expandedRow === val ? null : val;
      render();
      break;
    case 'fetch-results':
      fetchLiveResults();
      break;
    case 'fetch-apply':
      applyFetched();
      break;
    case 'fetch-cancel':
      state.fetchState = '';
      state.fetched = [];
      render();
      break;
    case 'remove-participant': {
      if (state.armedRemove !== val) { // first tap arms; second tap (within 4s) deletes
        state.armedRemove = val;
        clearTimeout(state._armT);
        state._armT = setTimeout(() => { state.armedRemove = null; safeRender(); }, 4000);
        render();
        return;
      }
      clearTimeout(state._armT);
      state.armedRemove = null;
      Store.removeParticipant(val);
      if (val === Store.deviceId()) { state.submitted = false; persistMe(); }
      render();
      break;
    }
    case 'try-pin':
      tryPin();
      break;
    case 'result': {
      const cur = (state.results || {})[mid];
      const results = { ...state.results, [mid]: cur === val ? undefined : val };
      const adv = { ...state.adv };
      if (results[mid] !== 'X') delete adv[mid];
      const resScores = { ...state.resScores };
      const scDir = dirFromScore(resScores[mid]);
      if (scDir && scDir !== results[mid]) delete resScores[mid];
      saveResultsState(results, adv, resScores);
      render();
      break;
    }
    case 'adv': {
      const adv = { ...state.adv, [mid]: (state.adv || {})[mid] === val ? undefined : val };
      saveResultsState({ ...state.results }, adv, { ...state.resScores });
      render();
      break;
    }
    case 'reset-results':
      if (state.armedRemove !== 'reset-all') {
        state.armedRemove = 'reset-all';
        clearTimeout(state._armT);
        state._armT = setTimeout(() => { state.armedRemove = null; safeRender(); }, 4000);
        render();
        return;
      }
      clearTimeout(state._armT);
      state.armedRemove = null;
      saveResultsState({}, {}, {});
      render();
      break;
  }
});

/* Sync the gold/green selection classes of one match's three buttons in place
   (used by score typing so the input keeps focus — no full render). */
function refreshDirButtons(mid, action, cls) {
  const cur = action === 'pick' ? state.picks[mid] : (state.results || {})[mid];
  ['1', 'X', '2'].forEach(v => {
    const b = root.querySelector('[data-action="' + action + '"][data-match="' + mid + '"][data-val="' + v + '"]');
    if (b) b.classList.toggle(cls, cur === v);
  });
}

root.addEventListener('input', e => {
  const scoreEl = e.target.closest('[data-score],[data-rscore]');
  if (scoreEl) {
    const clean = scoreEl.value.replace(/\D/g, '').slice(0, 2);
    if (clean !== scoreEl.value) scoreEl.value = clean;
    const side = scoreEl.getAttribute('data-side');
    const isAdmin = scoreEl.hasAttribute('data-rscore');
    const mid = scoreEl.getAttribute(isAdmin ? 'data-rscore' : 'data-score');
    if (isAdmin) {
      const resScores = { ...state.resScores };
      const sc = { ...(resScores[mid] || {}) };
      if (clean === '') delete sc[side]; else sc[side] = +clean;
      if (sc.h == null && sc.a == null) delete resScores[mid]; else resScores[mid] = sc;
      const d = dirFromScore(resScores[mid]);
      const prev = (state.results || {})[mid];
      const results = { ...state.results };
      const adv = { ...state.adv };
      if (d) { results[mid] = d; if (d !== 'X') delete adv[mid]; }
      saveResultsState(results, adv, resScores);
      if (d && d !== prev && (d === 'X' || prev === 'X')) { render(); return; } // adv row appears/disappears
      refreshDirButtons(mid, 'result', 'res-selected');
    } else {
      const scores = { ...state.scores };
      const sc = { ...(scores[mid] || {}) };
      if (clean === '') delete sc[side]; else sc[side] = +clean;
      if (sc.h == null && sc.a == null) delete scores[mid]; else scores[mid] = sc;
      state.scores = scores;
      const d = dirFromScore(scores[mid]);
      if (d) state.picks = { ...state.picks, [mid]: d }; // exact score implies the 1X2 pick
      persistMe();
      refreshDirButtons(mid, 'pick', 'selected');
      updateSubmitBar();
    }
    return;
  }
  const el = e.target.closest('[data-input]');
  if (!el) return;
  if (el.getAttribute('data-input') === 'name') {
    state.name = el.value;
    persistMe();
    updateSubmitBar();
  } else if (el.getAttribute('data-input') === 'pin') {
    const clean = el.value.replace(/\D/g, '');
    if (clean !== el.value) el.value = clean;
    state.pinInput = clean;
    if (state.pinError) {
      state.pinError = false;
      const err = root.querySelector('.pin-error');
      if (err) err.remove();
    }
  }
});

root.addEventListener('keydown', e => {
  const el = e.target.closest('[data-input="pin"]');
  if (el && e.key === 'Enter') tryPin();
});

/* ---------- init ---------- */

(function init() {
  const me = Store.loadMe();
  state.name = me.name || '';
  state.picks = me.picks || {};
  state.scores = me.scores || {};
  state.submitted = !!me.submitted;
  const r = Store.loadResults();
  state.results = r.results;
  state.adv = r.adv;
  state.resScores = r.scores || {};
  state.lang = Store.loadLang();
  try { state.helpOpen = localStorage.getItem('wc26-oranim-help') !== '1'; } catch (err) { state.helpOpen = true; }
  render();
  setInterval(tick, 1000);
  // Shared-backend mode: pull the freshest shared data into state on every
  // sync change, then re-render (deferred while an input is focused so
  // typing is never interrupted — tick() flushes it as soon as it's safe).
  Store.startSync(() => {
    const r = Store.loadResults();
    state.results = r.results;
    state.adv = r.adv;
    state.resScores = r.scores || {};
    // If the admin removed this device's row remotely, unlock the name —
    // but never right after our own write (a poll can race the insert).
    if (state.submitted && !Store.loadBoard()[Store.deviceId()] &&
        Date.now() - lastMyWriteAt > 20000) {
      state.submitted = false;
      persistMe();
    }
    safeRender();
  });
  root.addEventListener('focusout', () => {
    if (state.pendingRender) setTimeout(() => { if (state.pendingRender) safeRender(); }, 80);
  });
  // Coming back from background (bfcache / screen off): clock and data are stale.
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) { state.now = Date.now(); Store.refresh(); safeRender(); }
  });
  window.addEventListener('pageshow', e => {
    if (e.persisted) { state.now = Date.now(); Store.refresh(); safeRender(); }
  });
})();
