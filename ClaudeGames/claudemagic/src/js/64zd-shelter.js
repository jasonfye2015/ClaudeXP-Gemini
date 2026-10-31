"use strict";
// Mana Shelter (the twenty-seventh big update - v13.7): a warren dug under the Gilded Joker, run in real time. Rooms
// are built on its floors, a stair down one side: a Mana Well (whose mana keeps the other rooms going), a Kitchen
// (bread), a Spring (water), Living Quarters (room for more, and where two who share them raise a child), Storerooms,
// a Beacon that draws wanderers in, and a Training Hall. Residents work the rooms; each has Might, Grace and Wit, and a
// room goes faster for the one its work wants (the Well might, the Kitchen grace, the Spring and the Beacon wit). A
// room's work waits in it until it is gathered (a click), and gathering pays Marks to build and dig with. Everyone eats
// and drinks; with bread or water gone, work goes at half pace. It goes on while you are away (four hours at most).
// The real reward: gold and a Claudescryption card the first time the warren holds 6, 10, 15, 20, 25, 30, 40 and 50.
// It costs nothing. The window is 76t-shelter.js.
CM.SHL = {
  SLOTS: 4, FLOORS: 10, away: 4 * 3600, eat: 0.03, drink: 0.03, burn: 0.02, child: 220, grow: 150, wander: 160, train: 120,
  ROOMS: {
    well: { name: "Mana Well", res: "mana", stat: "might", cycle: 30, amount: 12, cost: 100, colour: "#3A5AA0" },
    kitchen: { name: "Kitchen", res: "bread", stat: "grace", cycle: 30, amount: 12, cost: 100, colour: "#A0602A" },
    spring: { name: "Spring", res: "water", stat: "wit", cycle: 30, amount: 12, cost: 100, colour: "#2A8AA0" },
    quarters: { name: "Living Quarters", cost: 120, colour: "#8A4A6A", cap: 8 },
    store: { name: "Storeroom", cost: 80, colour: "#6A5A3A", store: 60, noStaff: true },
    beacon: { name: "Beacon", stat: "wit", cost: 300, colour: "#A08A2A" },
    hall: { name: "Training Hall", cost: 400, colour: "#5A3A2A" },
  },
  STATS: ["might", "grace", "wit"], ICON: { mana: "🔷", bread: "🍞", water: "💧" }, MARKS: [6, 10, 15, 20, 25, 30, 40, 50],
  gold: (i) => 25 + i * 15, digCost: (f) => 200 * f, upCost: (lvl) => 220 * lvl,
  NAMES: "Ada Bram Cael Dora Edda Finn Gwen Hal Ida Jory Kit Lark Mira Ned Oda Pell Quin Rhea Sol Tam Una Vale Wren Yew Zara Bryn Cora Dell Esme Fen Gil Hett Ivo Juno Kell Lio Moss Nell Orrin Pip Rook Sage Tilda Ulf Vix Wynn".split(" "),
};
const SHL = CM.SHL;
SHL.staffMax = (lvl) => 1 + lvl;
SHL.Warren = class {
  constructor(seed, saved) {
    Object.assign(this, { t: 0, n: 0, floors: 1, marks: 150, stock: { mana: 40, bread: 40, water: 40 }, rooms: [], folk: [], ids: 0, events: [], best: 0, paid: 0 }, saved || {});
    this.seed = seed;
    if (!saved) { const R = this.rnd(); [["quarters", 0, 0], ["well", 0, 1], ["kitchen", 0, 2], ["spring", 0, 3]].forEach(([k, f, s]) => this.rooms.push({ id: ++this.ids, k, f, s, lvl: 1, prog: 0, ready: 0, timer: 0 }));
      for (let i = 0; i < 5; i++) this.folk.push(this.newFolk(R)); [1, 2, 3, 0, 0].forEach((ri, i) => { this.folk[i].room = this.rooms[ri].id; }); this.best = 5; }   // (one at each work, two sharing the quarters)
  }
  rnd() { return new CM.Random(CM.hashSeed(`${this.seed}:${this.n++}`)); }
  newFolk(R, parents) {
    const st = {}; for (const k of SHL.STATS) st[k] = parents ? Math.max(1, Math.min(10, Math.round((parents[0].st[k] + parents[1].st[k]) / 2) + R.int(-1, 1))) : R.int(1, 5);
    return { id: ++this.ids, name: SHL.NAMES[R.int(0, SHL.NAMES.length - 1)], st, room: null, age: parents ? 0 : SHL.grow, trainT: 0 };
  }
  room(id) { return this.rooms.find((r) => r.id === id); }
  at(f, s) { return this.rooms.find((r) => r.f === f && r.s === s); }
  staff(r) { return this.folk.filter((p) => p.room === r.id && p.age >= SHL.grow); }
  pop() { return this.folk.length; }
  cap() { return this.rooms.filter((r) => r.k === "quarters").reduce((t, r) => t + SHL.ROOMS.quarters.cap * r.lvl, 0); }
  storeCap() { return 60 + this.rooms.filter((r) => r.k === "store").reduce((t, r) => t + SHL.ROOMS.store.store * r.lvl, 0) + this.rooms.filter((r) => SHL.ROOMS[r.k].res).length * 15; }
  weary() { return this.stock.bread <= 0 || this.stock.water <= 0; }
  cost(k) { return Math.round(SHL.ROOMS[k].cost * Math.pow(1.25, this.rooms.filter((r) => r.k === k).length)); }
  // a room built on an empty place of a dug floor
  build(k, f, s) { if (!SHL.ROOMS[k] || f >= this.floors || s < 0 || s >= SHL.SLOTS || this.at(f, s)) return "There is no room there."; const c = this.cost(k); if (this.marks < c) return `That wants ${c} marks.`; this.marks -= c; const r = { id: ++this.ids, k, f, s, lvl: 1, prog: 0, ready: 0, timer: 0 }; this.rooms.push(r); this.events.push({ kind: "build", r }); return ""; }
  dig() { if (this.floors >= SHL.FLOORS) return "As deep as the warren goes."; const c = SHL.digCost(this.floors); if (this.marks < c) return `Digging deeper wants ${c} marks.`; this.marks -= c; this.floors += 1; this.events.push({ kind: "dig" }); return ""; }
  upgrade(id) { const r = this.room(id); if (!r || r.lvl >= 3) return "As grand as it can be."; const c = SHL.upCost(r.lvl); if (this.marks < c) return `That wants ${c} marks.`; this.marks -= c; r.lvl += 1; this.events.push({ kind: "upgrade", r }); return ""; }
  assign(pid, rid) { const p = this.folk.find((x) => x.id === pid), r = rid ? this.room(rid) : null; if (!p || p.age < SHL.grow) return false; if (r && (SHL.ROOMS[r.k].noStaff || this.staff(r).length >= SHL.staffMax(r.lvl))) return false; p.room = r ? r.id : null; return true; }
  // the best idle resident for a room's work
  bestIdle(r) { const st = SHL.ROOMS[r.k].stat; return this.folk.filter((p) => !p.room && p.age >= SHL.grow).sort((a, b) => (st ? b.st[st] - a.st[st] : 0))[0] || null; }
  speed(r) { const R = SHL.ROOMS[r.k], st = this.staff(r); if (!st.length) return 0; const sum = R.stat ? st.reduce((t, p) => t + p.st[R.stat], 0) : st.length * 3; return (1 + sum / 8) * (this.weary() ? 0.5 : 1) * (r.k !== "well" && this.stock.mana <= 0 ? 0 : 1); }
  // what is waiting in a room, gathered: into the stores (to their limit), and marks for it
  collect(id) { const r = this.room(id); if (!r || !r.ready) return 0; const res = SHL.ROOMS[r.k].res, n = r.ready, room = Math.max(0, this.storeCap() - this.stock[res]), got = Math.min(n, room); this.stock[res] += got; r.ready = 0; this.marks += Math.ceil(n / 2); this.events.push({ kind: "collect", r, res, n: got }); return got; }
  update(dt, away = false) {
    this.t += dt; const P = this.pop(), k = away ? 0.5 : 1;
    this.stock.bread = Math.max(0, this.stock.bread - P * SHL.eat * dt * k); this.stock.water = Math.max(0, this.stock.water - P * SHL.drink * dt * k);
    this.stock.mana = Math.max(0, this.stock.mana - this.rooms.filter((r) => r.k !== "well" && r.k !== "store" && this.staff(r).length).length * SHL.burn * dt * k);
    for (const p of this.folk) if (p.age < SHL.grow) { p.age += dt; if (p.age >= SHL.grow) this.events.push({ kind: "grown", p }); }
    for (const r of this.rooms) {
      const R = SHL.ROOMS[r.k], sp = this.speed(r);
      if (R.res) { if (r.ready || !sp) continue; r.prog += (dt * sp) / R.cycle; if (r.prog >= 1) { r.prog = 0; r.ready = R.amount * r.lvl; this.events.push({ kind: "ready", r }); } }
      else if (r.k === "quarters" && this.staff(r).length >= 2 && this.pop() < this.cap()) { r.timer += dt * (this.weary() ? 0.5 : 1); if (r.timer >= SHL.child) { r.timer = 0; const st = this.staff(r), c = this.newFolk(this.rnd(), [st[0], st[1]]); this.folk.push(c); this.events.push({ kind: "born", p: c }); } }
      else if (r.k === "beacon" && sp && this.pop() < this.cap()) { r.timer += dt * sp; if (r.timer >= SHL.wander) { r.timer = 0; const c = this.newFolk(this.rnd()); this.folk.push(c); this.events.push({ kind: "wanderer", p: c }); } }
      else if (r.k === "hall") for (const p of this.staff(r)) { p.trainT += dt * (this.weary() ? 0.5 : 1); if (p.trainT >= SHL.train / r.lvl) { p.trainT = 0; const lo = SHL.STATS.slice().sort((a, b) => p.st[a] - p.st[b])[0]; if (p.st[lo] < 10) { p.st[lo] += 1; this.events.push({ kind: "trained", p, stat: lo }); } } }
    }
    this.best = Math.max(this.best, this.pop());
  }
  toJSON() { const o = {}; for (const k of ["t", "n", "floors", "marks", "stock", "rooms", "folk", "ids", "best", "paid"]) o[k] = this[k]; return JSON.parse(JSON.stringify(o)); }
};
Object.assign(CM.Game.prototype, {
  shStore() { const F = this.cgStore(); F.shelter = F.shelter || {}; return F.shelter; },
  shLive() { const S = this.shStore(); if (!this.shWarren) this.shWarren = new SHL.Warren(`${this.seed}:shelter`, S.state); return this.shWarren; },
  // back again: the warren's time while away, a second at a time (four hours at most)
  shAway(nowMs) { const S = this.shStore(), W = this.shLive(); if (!S.at) { S.at = nowMs; return 0; } const secs = Math.floor(Math.max(0, Math.min(SHL.away, (nowMs - S.at) / 1000))); S.at = nowMs; for (let i = 0; i < secs; i++) W.update(1, true); W.events = []; return secs; },
  shKeep(nowMs) { const S = this.shStore(); if (this.shWarren) S.state = this.shWarren.toJSON(); if (nowMs) S.at = nowMs; this.saveCasino && this.saveCasino(); },
  // the warren's numbers passed: gold and a card the first time for each
  shMarks() {
    const W = this.shLive(), out = [];
    while (W.paid < SHL.MARKS.length && W.best >= SHL.MARKS[W.paid]) {
      const i = W.paid++, gold = SHL.gold(i); this.gold += gold; const F = this.cgStore(); F.paid.shelter = (F.paid.shelter || 0) + gold;
      const tier = i >= 6 ? "rare" : i >= 3 ? "better" : "common", card = this.cgTierCard(tier, `Mana Shelter houses ${SHL.MARKS[i]}!`, new CM.Random(CM.hashSeed(`${this.seed}:shelter:card:${i}`)));
      out.push({ mark: SHL.MARKS[i], gold, card, tier });
    }
    if (out.length) { this.shKeep(); this.emit("change"); }
    return out;
  },
});
