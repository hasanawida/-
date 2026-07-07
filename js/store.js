/* Persistence layer.
   Two modes, chosen automatically:
   - SHARED (Supabase): fill in SUPABASE.url + SUPABASE.anonKey below and run
     supabase-setup.sql once in the Supabase SQL Editor — every phone then sees
     one live competition (board + results sync every few seconds).
   - LOCAL (default): with SUPABASE left empty, everything stays in this
     device's localStorage, exactly like the prototype.
   The rest of the app only talks to `Store`, so this is the only file that
   deals with where data lives. */

const SUPABASE = {
  url: 'https://rxnkuuhoerperfyibokn.supabase.co',
  anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ4bmt1dWhvZXJwZXJmeWlib2tuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NTQyMTQsImV4cCI6MjA5OTAzMDIxNH0.NeD81EG8EiYjHvzSiJ9Jhd_xqnvm6ppAvqY9yPaeEq0'
};

const KEYS = {
  me: 'wc26-oranim',            // { name, picks, scores, submitted }
  board: 'wc26-oranim-board',   // { [deviceId]: { name, picks, scores } }
  results: 'wc26-oranim-results', // { results: {matchId:'1'|'X'|'2'}, adv: {matchId: team}, scores: {matchId:{h,a}} }
  lang: 'wc26-oranim-lang',
  id: 'wc26-oranim-id'
};

/* ---- Supabase REST sync (no SDK — plain fetch against PostgREST) ---- */

const cloud = {
  enabled: !!(SUPABASE.url && SUPABASE.anonKey),
  board: {},
  results: { results: {}, adv: {}, scores: {} },
  loaded: false,
  onChange: null,
  snapshot: ''
};

function sbHeaders(extra) {
  return Object.assign({
    apikey: SUPABASE.anonKey,
    Authorization: 'Bearer ' + SUPABASE.anonKey,
    'Content-Type': 'application/json'
  }, extra || {});
}

function sbFetchAll() {
  if (!cloud.enabled) return;
  Promise.all([
    fetch(SUPABASE.url + '/rest/v1/participants?select=*', { headers: sbHeaders() }),
    fetch(SUPABASE.url + '/rest/v1/results?id=eq.1&select=*', { headers: sbHeaders() })
  ]).then(([pRes, rRes]) => {
    if (!pRes.ok || !rRes.ok) return null;
    return Promise.all([pRes.json(), rRes.json()]);
  }).then(data => {
    if (!data) return;
    const [parts, resRows] = data;
    const board = {};
    parts.forEach(p => {
      board[p.id] = { name: p.name, picks: p.picks || {}, scores: p.scores || {}, submittedAt: p.submitted_at };
    });
    const row = resRows[0] || {};
    cloud.board = board;
    cloud.results = { results: row.results || {}, adv: row.adv || {}, scores: row.scores || {} };
    cloud.loaded = true;
    const snap = JSON.stringify([cloud.board, cloud.results]);
    if (snap !== cloud.snapshot) {
      cloud.snapshot = snap;
      if (cloud.onChange) cloud.onChange();
    }
  }).catch(() => {});
}

function sbUpsertParticipant(id, name, picks, scores) {
  fetch(SUPABASE.url + '/rest/v1/participants?on_conflict=id', {
    method: 'POST',
    headers: sbHeaders({ Prefer: 'resolution=merge-duplicates' }),
    body: JSON.stringify([{ id, name, picks: picks || {}, scores: scores || {} }])
  }).catch(() => {});
}

function sbRemoveParticipant(id) {
  fetch(SUPABASE.url + '/rest/v1/participants?id=eq.' + encodeURIComponent(id), {
    method: 'DELETE', headers: sbHeaders()
  }).catch(() => {});
}

function sbSaveResults(results, adv, scores) {
  fetch(SUPABASE.url + '/rest/v1/results?on_conflict=id', {
    method: 'POST',
    headers: sbHeaders({ Prefer: 'resolution=merge-duplicates' }),
    body: JSON.stringify([{ id: 1, results: results || {}, adv: adv || {}, scores: scores || {} }])
  }).catch(() => {});
}

/* ---- Store API (synchronous reads; cloud kept in an in-memory cache) ---- */

const Store = {
  loadMe() {
    try { return JSON.parse(localStorage.getItem(KEYS.me) || '{}'); } catch (e) { return {}; }
  },
  saveMe(me) {
    try { localStorage.setItem(KEYS.me, JSON.stringify(me)); } catch (e) {}
  },
  loadResults() {
    if (cloud.enabled && cloud.loaded) return cloud.results;
    try {
      const r = JSON.parse(localStorage.getItem(KEYS.results) || '{}');
      return r && r.results
        ? { results: r.results, adv: r.adv || {}, scores: r.scores || {} }
        : { results: r || {}, adv: {}, scores: {} };
    } catch (e) { return { results: {}, adv: {}, scores: {} }; }
  },
  saveResults(results, adv, scores) {
    try { localStorage.setItem(KEYS.results, JSON.stringify({ results, adv, scores })); } catch (e) {}
    if (cloud.enabled) {
      cloud.results = { results, adv, scores };
      sbSaveResults(results, adv, scores);
    }
  },
  loadBoard() {
    if (cloud.enabled && cloud.loaded) return cloud.board;
    try { return JSON.parse(localStorage.getItem(KEYS.board) || '{}'); } catch (e) { return {}; }
  },
  upsertParticipant(id, name, picks, scores) {
    const b = this.loadBoard();
    b[id] = { name, picks, scores, submittedAt: b[id] && b[id].submittedAt ? b[id].submittedAt : new Date().toISOString() };
    try { localStorage.setItem(KEYS.board, JSON.stringify(b)); } catch (e) {}
    if (cloud.enabled) {
      cloud.board[id] = b[id];
      sbUpsertParticipant(id, name, picks, scores);
    }
  },
  removeParticipant(id) {
    const b = this.loadBoard();
    delete b[id];
    try { localStorage.setItem(KEYS.board, JSON.stringify(b)); } catch (e) {}
    if (cloud.enabled) {
      delete cloud.board[id];
      sbRemoveParticipant(id);
    }
  },
  loadLang() {
    try { return localStorage.getItem(KEYS.lang) || ''; } catch (e) { return ''; }
  },
  saveLang(lang) {
    try { localStorage.setItem(KEYS.lang, lang); } catch (e) {}
  },
  deviceId() {
    try {
      let id = localStorage.getItem(KEYS.id);
      if (!id) { id = 'u' + Math.random().toString(36).slice(2, 10); localStorage.setItem(KEYS.id, id); }
      return id;
    } catch (e) { return 'me'; }
  },
  /* Begin background sync (no-op in local mode). onChange fires whenever
     another device's data arrives, so the UI can refresh. */
  startSync(onChange) {
    if (!cloud.enabled) return;
    cloud.onChange = onChange;
    sbFetchAll();
    setInterval(sbFetchAll, 10000);
  },
  isShared() { return cloud.enabled; }
};
