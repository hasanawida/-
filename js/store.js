/* Persistence layer.
   Two modes, chosen automatically:
   - SHARED (Supabase): with SUPABASE.url + SUPABASE.anonKey filled in and
     supabase-setup.sql run once in the Supabase SQL Editor — every phone sees
     one live competition (board + results poll every POLL_MS, writes are
     confirmed against the server).
   - LOCAL: with SUPABASE left empty, everything stays in this device's
     localStorage, exactly like the prototype.
   The rest of the app only talks to `Store`, so this is the only file that
   deals with where data lives. */

const SUPABASE = {
  url: 'https://rxnkuuhoerperfyibokn.supabase.co',
  anonKey: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJ4bmt1dWhvZXJwZXJmeWlib2tuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODM0NTQyMTQsImV4cCI6MjA5OTAzMDIxNH0.NeD81EG8EiYjHvzSiJ9Jhd_xqnvm6ppAvqY9yPaeEq0'
};

const POLL_MS = 30000; // paused while the tab is hidden; refreshed on return

const KEYS = {
  me: 'wc26-oranim',            // { name, picks, scores, submitted }
  board: 'wc26-oranim-board',   // { [deviceId]: { name, picks, scores } } — last known state
  results: 'wc26-oranim-results', // { results, adv, scores } — last known state
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
  snapshot: '',
  lastWriteAt: 0, // polls that started before the latest local write are discarded
  started: false
};

function sbHeaders(extra) {
  return Object.assign({
    apikey: SUPABASE.anonKey,
    Authorization: 'Bearer ' + SUPABASE.anonKey,
    'Content-Type': 'application/json'
  }, extra || {});
}

function lsSet(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) {}
}
function lsGet(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key) || 'null') || fallback; } catch (e) { return fallback; }
}

function sbFetchAll() {
  if (!cloud.enabled) return;
  const startedAt = Date.now();
  Promise.all([
    fetch(SUPABASE.url + '/rest/v1/participants?select=*', { headers: sbHeaders() }),
    fetch(SUPABASE.url + '/rest/v1/results?id=eq.1&select=*', { headers: sbHeaders() })
  ]).then(([pRes, rRes]) => {
    if (!pRes.ok || !rRes.ok) return null;
    return Promise.all([pRes.json(), rRes.json()]);
  }).then(data => {
    if (!data) return;
    // A local write happened while this poll was in flight — its response is
    // stale (it may not contain the write yet); drop it, the post-write
    // refresh will bring fresh data.
    if (cloud.lastWriteAt > startedAt) return;
    const [parts, resRows] = data;
    const board = {};
    parts.forEach(p => {
      board[p.id] = { name: p.name, picks: p.picks || {}, scores: p.scores || {}, submittedAt: p.submitted_at };
    });
    const row = resRows[0] || {};
    cloud.board = board;
    cloud.results = { results: row.results || {}, adv: row.adv || {}, scores: row.scores || {} };
    cloud.loaded = true;
    // Mirror to localStorage so a later offline load starts from the last
    // known shared state instead of this device's ancient private copy.
    lsSet(KEYS.board, board);
    lsSet(KEYS.results, cloud.results);
    const snap = JSON.stringify([cloud.board, cloud.results]);
    if (snap !== cloud.snapshot) {
      cloud.snapshot = snap;
      if (cloud.onChange) cloud.onChange();
    }
  }).catch(() => {});
}

/* Refetch shortly after a write lands so all local caches converge. */
function sbAfterWrite() {
  cloud.snapshot = ''; // force onChange on the refresh even if data looks same
  setTimeout(sbFetchAll, 400);
}

function sbUpsertParticipant(id, name, picks, scores) {
  cloud.lastWriteAt = Date.now();
  return fetch(SUPABASE.url + '/rest/v1/participants?on_conflict=id', {
    method: 'POST',
    headers: sbHeaders({ Prefer: 'resolution=merge-duplicates' }),
    body: JSON.stringify([{ id, name, picks: picks || {}, scores: scores || {} }])
  }).then(r => { if (r.ok) sbAfterWrite(); return r.ok; }).catch(() => false);
}

function sbRemoveParticipant(id) {
  cloud.lastWriteAt = Date.now();
  return fetch(SUPABASE.url + '/rest/v1/participants?id=eq.' + encodeURIComponent(id), {
    method: 'DELETE', headers: sbHeaders()
  }).then(r => { if (r.ok) sbAfterWrite(); return r.ok; }).catch(() => false);
}

function sbSaveResults(results, adv, scores) {
  cloud.lastWriteAt = Date.now();
  return fetch(SUPABASE.url + '/rest/v1/results?on_conflict=id', {
    method: 'POST',
    headers: sbHeaders({ Prefer: 'resolution=merge-duplicates' }),
    body: JSON.stringify([{ id: 1, results: results || {}, adv: adv || {}, scores: scores || {} }])
  }).then(r => { if (r.ok) sbAfterWrite(); return r.ok; }).catch(() => false);
}

/* ---- Store API (synchronous reads; cloud kept in an in-memory cache) ---- */

const Store = {
  loadMe() {
    return lsGet(KEYS.me, {});
  },
  saveMe(me) {
    lsSet(KEYS.me, me);
  },
  loadResults() {
    if (cloud.enabled && cloud.loaded) return cloud.results;
    const r = lsGet(KEYS.results, {});
    return r && r.results
      ? { results: r.results, adv: r.adv || {}, scores: r.scores || {} }
      : { results: r || {}, adv: {}, scores: {} };
  },
  /* Returns a promise resolving to true when the write is confirmed
     (always true in local mode). */
  saveResults(results, adv, scores) {
    lsSet(KEYS.results, { results, adv, scores });
    if (cloud.enabled) {
      cloud.results = { results, adv, scores };
      return sbSaveResults(results, adv, scores);
    }
    return Promise.resolve(true);
  },
  loadBoard() {
    if (cloud.enabled && cloud.loaded) return cloud.board;
    return lsGet(KEYS.board, {});
  },
  upsertParticipant(id, name, picks, scores) {
    const b = this.loadBoard();
    b[id] = { name, picks, scores, submittedAt: b[id] && b[id].submittedAt ? b[id].submittedAt : new Date().toISOString() };
    lsSet(KEYS.board, b);
    if (cloud.enabled) {
      cloud.board[id] = b[id];
      return sbUpsertParticipant(id, name, picks, scores);
    }
    return Promise.resolve(true);
  },
  removeParticipant(id) {
    const b = this.loadBoard();
    delete b[id];
    lsSet(KEYS.board, b);
    if (cloud.enabled) {
      delete cloud.board[id];
      return sbRemoveParticipant(id);
    }
    return Promise.resolve(true);
  },
  loadLang() {
    try { return localStorage.getItem(KEYS.lang) || ''; } catch (e) { return ''; }
  },
  saveLang(lang) {
    try { localStorage.setItem(KEYS.lang, lang); } catch (e) {}
  },
  deviceId() {
    if (this._id) return this._id;
    try {
      let id = localStorage.getItem(KEYS.id);
      if (!id) { id = 'u' + Math.random().toString(36).slice(2, 12); localStorage.setItem(KEYS.id, id); }
      this._id = id;
    } catch (e) {
      // Storage blocked (private mode / webview): a per-session random id —
      // unstable, but never shared between two people like a constant would be.
      this._id = 'tmp' + Math.random().toString(36).slice(2, 12);
    }
    return this._id;
  },
  /* Begin background sync (no-op in local mode). onChange fires whenever
     shared data changes. Polling pauses while the tab is hidden and resumes
     with an immediate refresh when it becomes visible again. */
  startSync(onChange) {
    if (!cloud.enabled || cloud.started) return;
    cloud.started = true;
    cloud.onChange = onChange;
    sbFetchAll();
    setInterval(() => { if (!document.hidden) sbFetchAll(); }, POLL_MS);
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) sbFetchAll();
    });
  },
  isShared() { return cloud.enabled; },
  isLoaded() { return !cloud.enabled || cloud.loaded; },
  refresh() { sbFetchAll(); }
};
