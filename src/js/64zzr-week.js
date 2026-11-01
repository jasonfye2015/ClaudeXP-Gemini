"use strict";
// The Joker's Week (v17.3): each real week (Monday to Sunday) one game of skill is the week's game - a cabinet (the
// furthest level counts) or the fairground or the pond (the best score). The residents and the floor's visitors post
// their bests on the week's board day by day; the party's best that week goes up beside them, and it earns double JXP
// there all week. When the week is out, the board is settled: first 1,500 gold, 300 tickets and a rare card; second 800,
// 200 and a stronger card; third 400, 150 and a card; fourth to tenth 60 tickets - collected on the week's page any
// time in the next four weeks. The window is 76zzw-floorlife.js.
{ const WK = CM.WEEK = { size: 14, keep: 4, PRIZES: [[1500, 300, "rare"], [800, 200, "better"], [400, 150, "common"]], rest: 60,
    RANGE: { darts: [350, 950], skee: [250, 720], rings: [12, 60], pond: [800, 9000] } };
  WK.games = () => ["darts", "skee", "rings", "pond"].concat(Object.keys(CM.ARC ? CM.ARC.reg : {}).sort());
  // the week of a date: its Monday, as a key
  WK.key = (now) => { const d = new Date(now || Date.now()); d.setHours(12, 0, 0, 0); d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
  WK.day = (now) => (new Date(now || Date.now()).getDay() + 6) % 7;   // (Monday 0 .. Sunday 6)
  WK.ends = (key) => { const [y, m, d] = key.split("-").map(Number); return new Date(y, m - 1, d + 7, 0, 0, 0).getTime(); };
  WK.prev = (key, n = 1) => { const [y, m, d] = key.split("-").map(Number); const t = new Date(y, m - 1, d - 7 * n, 12); return WK.key(t.getTime()); };
  WK.metric = (id) => (CM.ARC && CM.ARC.reg[id] ? "level" : "score");
  WK.game = (seed, key) => { const L = WK.games(), R = new CM.Random(CM.hashSeed(`${seed}:week:${key}`)); return L[R.int(0, L.length - 1)]; };
  WK.who = () => { const res = CM.HE ? Object.values(CM.HE.RES).map((r) => r.name) : []; return res.concat(CM.FLOOR ? CM.FLOOR.FOLK.filter((f) => !res.includes(f)) : []); };
  // the field's bests, each posted on a day of the week
  WK.field = (seed, key, id) => { const R = new CM.Random(CM.hashSeed(`${seed}:weekfield:${key}`)), who = R.shuffle(WK.who().slice()).slice(0, WK.size), lv = WK.metric(id) === "level", [a, b] = WK.RANGE[id] || [1, 14];
    return who.map((w) => { const k = Math.pow(R.next(), 1.6); return { who: w, val: lv ? 1 + Math.floor(13 * k) : Math.round(a + (b - a) * k), day: R.int(0, 6), resident: CM.HE ? Object.values(CM.HE.RES).some((r) => r.name === w) : false }; }); };
  const P = CM.Game.prototype, rec0 = P.cgRecord, jk0 = P.jkGain;
  Object.assign(P, {
    wkStore() { const F = this.cgStore(); F.week = F.week || { weeks: {} }; return F.week; },
    wkInfo(now) { now = now || Date.now(); const key = WK.key(now), id = WK.game(this.seed, key), S = this.wkStore(), W = S.weeks[key] || null; return { key, id, metric: WK.metric(id), mine: W ? W.best : null, day: WK.day(now), ends: WK.ends(key) }; },
    // the board as it stands: the field's posts so far (all of them once the week is out), and the party's best
    wkBoard(key, now) { now = now || Date.now(); const id = WK.game(this.seed, key), done = now >= WK.ends(key), day = done ? 6 : WK.day(now), W = this.wkStore().weeks[key];
      const rows = WK.field(this.seed, key, id).filter((e) => e.day <= day).map((e) => ({ ...e })); if (W && W.best !== null && W.best !== undefined) rows.push({ who: "You", val: W.best, you: true });
      rows.sort((a, b) => b.val - a.val || (b.you ? 1 : 0) - (a.you ? 1 : 0)); return rows; },
    wkPlace(key, now) { const i = this.wkBoard(key, now).findIndex((e) => e.you); return i < 0 ? null : i + 1; },
    cgRecord(table, score, level) { const r = rec0.call(this, table, score, level); if (!this.cgPractice) { const I = this.wkInfo(); if (table === I.id) { const v = I.metric === "level" ? level || 0 : Math.floor(score || 0), S = this.wkStore(), W = S.weeks[I.key] = S.weeks[I.key] || { best: null, game: I.id };
        if (W.best === null || v > W.best) { const before = this.wkPlace(I.key); W.best = v; const after = this.wkPlace(I.key); this.wkMoved = { before, after, val: v }; this.saveCasino && this.saveCasino(); } } } return r; },
    jkGain(n, why) { const I = this.wkInfo && this.cgStore ? this.wkInfo() : null; return jk0.call(this, I && why === I.id ? n * 2 : n, why); },
    // past weeks waiting to be paid
    wkWaiting(now) { now = now || Date.now(); const S = this.wkStore(), key = WK.key(now), out = []; for (let k = 1; k <= WK.keep; k++) { const p = WK.prev(key, k), W = S.weeks[p]; if (W && W.best !== null && !W.paid) out.push({ key: p, id: W.game, place: this.wkPlace(p, now) }); } return out; },
    wkClaim(key, now) { now = now || Date.now(); const S = this.wkStore(), W = S.weeks[key]; if (!W || W.best === null) return { error: "You didn't play that week's game." }; if (W.paid) return { error: "Already paid." }; if (now < WK.ends(key)) return { error: "The week isn't out yet." };
      const place = this.wkPlace(key, now), out = { place, gold: 0, tickets: 0, card: null }; W.paid = true;
      if (place <= 3) { const [g, t, tier] = WK.PRIZES[place - 1]; out.gold = g; out.tickets = t; this.gold += g; if (this.tkAdd) this.tkAdd(t, "week"); out.card = this.cgTierCard ? this.cgTierCard(tier, `The Joker's Week: ${["first", "second", "third"][place - 1]}!`, new CM.Random(CM.hashSeed(`${this.seed}:weekcard:${key}`))) : null; this.cgCelebrate && this.cgCelebrate(place === 1 ? 3 : 2, `The Joker's Week - ${["first", "second", "third"][place - 1]} place!`); }
      else if (place <= 10) { out.tickets = WK.rest; if (this.tkAdd) this.tkAdd(WK.rest, "week"); }
      this.saveCasino && this.saveCasino(); this.emit && this.emit("change"); return out; },
  });
}
