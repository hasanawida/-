/* Match model & bracket auto-progression (see README "Match model & feed graph"). */

/* National colors for the 3-stripe flag badges; keys are canonical Hebrew team names. */
const FLAG_COLORS = {
  'צרפת': ['#0055A4', '#ffffff', '#EF4135'], 'מרוקו': ['#C1272D', '#006233', '#C1272D'],
  'ספרד': ['#AA151B', '#F1BF00', '#AA151B'], 'בלגיה': ['#2b2b2b', '#FDDA24', '#EF3340'],
  'נורווגיה': ['#BA0C2F', '#ffffff', '#00205B'], 'אנגליה': ['#f2f2f2', '#CE1124', '#f2f2f2'],
  'ארגנטינה': ['#75AADB', '#ffffff', '#75AADB'], 'מצרים': ['#CE1126', '#ffffff', '#2b2b2b'],
  'שווייץ': ['#DA291C', '#ffffff', '#DA291C'], 'קולומביה': ['#FCD116', '#003893', '#CE1126']
};
const TBD_COLORS = ['#3A342E', '#4A443C', '#3A342E'];

/* Feed graph: which two matches produce this match's teams. */
const FEEDS = { qf4: ['r16a', 'r16b'], sf1: ['qf1', 'qf2'], sf2: ['qf3', 'qf4'], fin: ['sf1', 'sf2'] };

/* Lock timestamps for fed matches (semi/final kickoffs are estimates — confirm before launch). */
const LOCK_ATS = {
  qf4: Date.parse('2026-07-12T04:00:00+03:00'),
  sf1: Date.parse('2026-07-14T22:00:00+03:00'),
  sf2: Date.parse('2026-07-15T22:00:00+03:00'),
  fin: Date.parse('2026-07-19T22:00:00+03:00')
};

/* Base match list for the current locale. Each entry: home/away = [canonical name, colors]. */
function buildMatches(t, tName) {
  const c = key => FLAG_COLORS[key];
  return [
    { id: 'r16a', round: t.r16, date: t.d_r16, home: ['ארגנטינה', c('ארגנטינה')], away: ['מצרים', c('מצרים')], locked: true, note: t.lockToday },
    { id: 'r16b', round: t.r16, date: t.d_r16, home: ['שווייץ', c('שווייץ')], away: ['קולומביה', c('קולומביה')], locked: true, note: t.lockToday },
    { id: 'qf1', round: t.qf + ' · ' + t.cBoston, date: t.d_qf1, lockAt: Date.parse('2026-07-09T23:00:00+03:00'), home: ['צרפת', c('צרפת')], away: ['מרוקו', c('מרוקו')] },
    { id: 'qf2', round: t.qf + ' · ' + t.cLA, date: t.d_qf2, lockAt: Date.parse('2026-07-10T22:00:00+03:00'), home: ['ספרד', c('ספרד')], away: ['בלגיה', c('בלגיה')] },
    { id: 'qf3', round: t.qf + ' · ' + t.cMiami, date: t.d_qf3, lockAt: Date.parse('2026-07-12T00:00:00+03:00'), home: ['נורווגיה', c('נורווגיה')], away: ['אנגליה', c('אנגליה')] },
    { id: 'qf4', round: t.qf + ' · ' + t.cKC, date: t.d_qf4, home: [tName('ארגנטינה') + ' / ' + tName('מצרים'), TBD_COLORS], away: [tName('שווייץ') + ' / ' + tName('קולומביה'), TBD_COLORS], locked: true, note: t.opensTonight },
    { id: 'sf1', round: t.sf + ' · ' + t.cDallas, date: t.d_sf1, home: [t.winnerQF + ' 1', TBD_COLORS], away: [t.winnerQF + ' 2', TBD_COLORS], locked: true, note: t.opensAfterQF },
    { id: 'sf2', round: t.sf + ' · ' + t.cAtlanta, date: t.d_sf2, home: [t.winnerQF + ' 3', TBD_COLORS], away: [t.winnerQF + ' 4', TBD_COLORS], locked: true, note: t.opensAfterQF },
    { id: 'fin', round: t.finRound + ' · ' + t.cNJ, date: t.d_fin, home: [t.winnerSF + ' 1', TBD_COLORS], away: [t.winnerSF + ' 2', TBD_COLORS], locked: true, note: t.opensAfterSF }
  ];
}

/* Resolves the bracket: fills fed matches from feeder results, applies auto-lock at
   lockAt, and annotates finished matches. Returns matches with { home, away, lockAt,
   locked, note, known } resolved. */
function resolveMatches(all, results, adv, now, t, tName) {
  const byId = {};
  all.forEach(m => { byId[m.id] = m; });
  const colors = {};
  all.forEach(m => { colors[m.home[0]] = m.home[1]; colors[m.away[0]] = m.away[1]; });

  const winner = id => {
    const m = byId[id];
    if (!m) return null;
    const f = FEEDS[id];
    const home = f ? winner(f[0]) : m.home[0];
    const away = f ? winner(f[1]) : m.away[0];
    const r = results[id];
    if (!r || !home || !away) return null;
    if (r === '1') return home;
    if (r === '2') return away;
    return adv[id] || null;
  };

  return all.map(m => {
    const f = FEEDS[m.id];
    let home = m.home, away = m.away, locked = !!m.locked, note = m.note || '', known = !f;
    const lockAt = m.lockAt || LOCK_ATS[m.id];
    if (f) {
      const h = winner(f[0]), a = winner(f[1]);
      known = !!(h && a);
      if (known) { home = [h, colors[h]]; away = [a, colors[a]]; locked = false; note = ''; }
    }
    if (lockAt && now >= lockAt) { locked = true; if (known && !note) note = t.lockStarted; }
    const r = results[m.id];
    if (r && known) {
      locked = true;
      note = t.ended + (r === 'X'
        ? t.draw + (adv[m.id] ? ' · ' + t.advancedWord + tName(adv[m.id]) : '')
        : t.winWord + tName(r === '1' ? home[0] : away[0]));
    }
    return { ...m, home, away, lockAt, locked, note, known };
  });
}
