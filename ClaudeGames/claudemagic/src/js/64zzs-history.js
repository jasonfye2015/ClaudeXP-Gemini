"use strict";
// The party's history at the Joker (v17.4): each visit with anything in it is written into the floor's books when the
// party leaves - when, how long, gold laid and paid back, up or down, tickets, the tables played, the best moment, the
// Joker level - the last two hundred kept. From them, and the floor's own books, the history page draws the record:
// the visits' ups and downs, the running total, the most played tables, tickets month by month, the Joker level over
// time. The window is 76zzx-history.js.
{ const HS = CM.HISTORY = { keep: 200 };
  const end0 = CM.Game.prototype.cgVisitEnd;
  HS.month = (t) => { const d = new Date(t); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`; };
  Object.assign(CM.Game.prototype, {
    hsStore() { const F = this.cgStore(); F.history = F.history || { visits: [] }; return F.history; },
    // a visit ended for good: into the books (a peek, or a quiet visit, isn't)
    cgVisitEnd(now, peek) { const V = this.cgVisit, out = end0.call(this, now, peek); if (out && !peek && !out.quiet && V && !this.cgPractice) { const H = this.hsStore();
        H.visits.push({ at: V.at, secs: out.secs, staked: out.staked, paid: out.paid, net: out.after - out.before, tickets: out.tickets, tables: out.tables.slice(0, 12), best: out.best || null, cards: out.cards.length, level: this.jkLevel ? this.jkLevel() : 1 });
        if (H.visits.length > HS.keep) H.visits.splice(0, H.visits.length - HS.keep); this.saveCasino && this.saveCasino(); } return out; },
    // the record, worked out for the page
    hsSummary() { const V = this.hsStore().visits, F = this.cgStore(), T = this.tkStore ? this.tkStore() : { earned: 0 }, months = {};
      for (const v of V) { const m = HS.month(v.at); months[m] = (months[m] || 0) + (v.tickets || 0); }
      let run = 0; const running = V.map((v) => (run += v.net));
      const played = Object.entries(F.played || {}).filter(([, n]) => n > 0).sort((a, b) => b[1] - a[1]);
      return { visits: V.length, secs: V.reduce((a, v) => a + v.secs, 0), net: run, staked: V.reduce((a, v) => a + v.staked, 0), tickets: T.earned || 0, level: this.jkLevel ? this.jkLevel() : 1,
        best: V.reduce((b, v) => (v.net > (b ? b.net : -Infinity) ? v : b), null), worst: V.reduce((b, v) => (v.net < (b ? b.net : Infinity) ? v : b), null), list: V, running, played, months: Object.entries(months).sort((a, b) => (a[0] < b[0] ? -1 : 1)) }; },
  });
}
