"use strict";
// The Gilded Pit (the twenty-fourth big update - v13.4): a room under the Gilded Joker, behind a door that locks. One
// hero goes down with the stake as coins; in the room are an old slot machine (the Old Lucky), the house's deposit box,
// a telephone and a trapdoor under the stool. Each deadline the house wants a debt paid into the box; the hero has so
// many spins of the Old Lucky to raise it. Its five reels by three pay for lines of three, four and five of a kind,
// for a column of three, for a diagonal, and ten times for a full grid alike; three of the Pit's eyes anywhere spoil a
// spin. Pay the debt (early, for more tickets) and the telephone offers lucky charms for tickets - a horseshoe, a
// four-leaf clover, a pocket watch... each bending the odds - and the hero may step out with the coins left or stay
// for the next deadline, a bigger debt. Miss a deadline and the trapdoor opens: the hero comes back up to the party
// with a tenth of their health, and the coins stay below. Charms are unlocked for good as deeper deadlines are
// reached; cards at the third and fifth deadlines and for a full grid. The window, a room in 3D: 76n-gildedpit.js.
CM.PT = {
  COLS: 5, ROWS: 3, deadlines: 5, spins: 7,
  SYMS: { lemon: [18, 2], cherry: [18, 2], clover: [14, 3], bell: [12, 3], diamond: [8, 5], chest: [8, 5], seven: [5, 7], eye: [3, 0] },
  MULT: { 3: 1, 4: 2, 5: 3, col: 1, diag: 1, grid: 10 },
  DEBT: [0.2, 0.45, 0.9, 1.6, 2.5], COST: [0.1, 0.13, 0.16, 0.2, 0.24],   
  CARD: { 3: "common", 5: "rare" },
  CHARMS: {
    horseshoe: ["Horseshoe", "Clovers come up more often", 1], goldlemon: ["Golden Lemon", "Lemons and cherries are worth one more", 1], pocketwatch: ["Pocket Watch", "Two more spins every deadline", 2],
    fourleaf: ["Four-Leaf Clover", "Clovers are worth three more", 1], amulet: ["Eye-Ward Amulet", "The Pit's eyes never come up", 2], magnet: ["Lodestone", "Diamonds and chests come up more often", 2],
    abacus: ["Abacus", "A tenth of your coins again at each deadline", 2], bellrope: ["Bell-Rope", "Bells are worth three more", 1], redseven: ["Red Seven", "Sevens are worth double", 2],
    mirror: ["Hand Mirror", "Diagonals pay double", 1], rabbitfoot: ["Rabbit's Foot", "Lines of four and five pay one more", 2], piggy: ["Piggy Bank", "A spin that pays nothing gives half its cost back", 2],
  },
  START: ["horseshoe", "goldlemon", "pocketwatch", "fourleaf"], UNLOCK: ["amulet", "magnet", "abacus", "bellrope", "redseven", "mirror", "rabbitfoot", "piggy"],
};
const PT = CM.PT;
// the symbols' weights and worths, with the charms
PT.table = (charms) => {
  const has = (c) => charms.includes(c), w = {}, v = {};
  for (const [s, [ww, vv]] of Object.entries(PT.SYMS)) { w[s] = ww; v[s] = vv; }
  if (has("horseshoe")) w.clover += 8; if (has("magnet")) { w.diamond += 4; w.chest += 4; } if (has("amulet")) w.eye = 0;
  if (has("goldlemon")) { v.lemon += 1; v.cherry += 1; } if (has("fourleaf")) v.clover += 3; if (has("bellrope")) v.bell += 3; if (has("redseven")) v.seven *= 2;
  return { w, v };
};
// a grid's worth, as a multiple of the spin's cost: [total, the lines that paid]
PT.score = (grid, charms) => {
  const { v } = PT.table(charms), has = (c) => charms.includes(c), lines = [], C = PT.COLS, R = PT.ROWS, eyes = grid.flat().filter((s) => s === "eye").length;
  if (eyes >= 3) return [0, [{ kind: "eyes" }]];
  const flat = grid.flat(); if (flat.every((s) => s === flat[0]) && flat[0] !== "eye") return [v[flat[0]] * PT.MULT.grid * 5, [{ kind: "grid", s: flat[0] }]];
  for (let r = 0; r < R; r++) { let c = 0; while (c < C) { const s = grid[r][c]; let e = c + 1; while (e < C && grid[r][e] === s) e++; const len = e - c; if (s !== "eye" && len >= 3) lines.push({ kind: "row", s, r, c, len, pay: v[s] * (PT.MULT[len] + (has("rabbitfoot") && len >= 4 ? 1 : 0)) }); c = e; } }
  for (let c = 0; c < C; c++) { const s = grid[0][c]; if (s !== "eye" && grid[1][c] === s && grid[2][c] === s) lines.push({ kind: "col", s, c, pay: v[s] * PT.MULT.col }); }
  for (let c = 0; c + 2 < C; c++) { for (const dir of [1, -1]) { const r0 = dir > 0 ? 0 : 2, s = grid[r0][c]; if (s !== "eye" && grid[r0 + dir][c + 1] === s && grid[r0 + 2 * dir][c + 2] === s) lines.push({ kind: "diag", s, c, dir, pay: v[s] * PT.MULT.diag * (has("mirror") ? 2 : 1) }); } }
  return [lines.reduce((t, l) => t + l.pay, 0), lines];
};
PT.Run = class {
  constructor(stake, seed, charms = []) { this.stake = stake; this.coins = stake; this.rnd = new CM.Random(seed); this.deadline = 1; this.charms = charms.slice(); this.tickets = 0; this.stage = "spin"; this.offers = []; this.spun = 0; this.newDeadline(); }
  cost() { return Math.max(1, Math.round(this.stake * PT.COST[this.deadline - 1])); }
  debt() { return Math.max(1, Math.round(this.stake * PT.DEBT[this.deadline - 1])); }
  newDeadline() { this.spinsLeft = PT.spins + (this.charms.includes("pocketwatch") ? 2 : 0); if (this.deadline > 1 && this.charms.includes("abacus")) this.coins += Math.floor(this.coins / 10); }
  roll() { const { w } = PT.table(this.charms), list = Object.entries(w), tot = list.reduce((t, [, x]) => t + x, 0); let r = this.rnd.next() * tot; for (const [s, x] of list) { if ((r -= x) < 0) return s; } return list[0][0]; }
  // a spin: its cost, the grid, what it paid; the end of the deadline's spins without the debt drops the hero
  spin() {
    if (this.stage !== "spin") return { error: "Not now." }; const cost = this.cost(), can = this.coins >= this.debt();
    if ((this.spinsLeft <= 0 || this.coins < cost) && !can) { this.stage = "dropped"; return { dropped: true, grid: null, lines: [], won: 0, cost: 0 }; }   // (no spin left to raise it, and not the debt: the trapdoor)
    if (this.spinsLeft <= 0) return { error: "No spins left: pay the debt." }; if (this.coins < cost) return { error: "Not enough coins for a spin: pay the debt." };
    this.coins -= cost; this.spinsLeft -= 1; this.spun += 1;
    const grid = []; for (let r = 0; r < PT.ROWS; r++) { const row = []; for (let c = 0; c < PT.COLS; c++) row.push(this.roll()); grid.push(row); }
    const [mult, lines] = PT.score(grid, this.charms); let won = mult * cost; if (!won && this.charms.includes("piggy")) won = Math.floor(cost / 2);
    this.coins += won; const jackpot = lines.some((l) => l.kind === "grid");
    const out = { grid, lines, won, cost, jackpot };
    if (this.spinsLeft <= 0 && this.coins < this.debt()) { this.stage = "dropped"; out.dropped = true; }
    else if (this.coins < this.cost() && this.coins < this.debt()) { this.stage = "dropped"; out.dropped = true; }
    return out;
  }
  // the debt paid into the box: tickets (one, and one more for every three spins left), and the telephone rings
  pay() {
    if (this.stage !== "spin" || this.coins < this.debt()) return false; this.coins -= this.debt(); this.tickets += 1 + Math.floor(this.spinsLeft / 3); this.paidAt = this.deadline;
    this.stage = this.deadline >= PT.deadlines ? "free" : "paid"; return true;
  }
  ring(pool) { const left = pool.filter((c) => !this.charms.includes(c)); this.offers = []; while (left.length && this.offers.length < 3) this.offers.push(left.splice(this.rnd.int(0, left.length - 1), 1)[0]); return this.offers; }
  buy(c) { const C = PT.CHARMS[c]; if (this.stage !== "paid" || !this.offers.includes(c) || this.tickets < C[2]) return false; this.tickets -= C[2]; this.charms.push(c); this.offers = this.offers.filter((x) => x !== c); return true; }
  next() { if (this.stage !== "paid") return false; this.deadline += 1; this.stage = "spin"; this.offers = []; this.newDeadline(); return true; }
};
Object.assign(CM.Game.prototype, {
  pitStore() { const F = this.cgStore(); F.pit = F.pit || {}; const P = F.pit; P.unlocked = P.unlocked || PT.START.slice(); P.best = P.best || 0; P.plays = P.plays || 0; return P; },
  pitRun() { const P = this.pitStore(); if (!P.run) return null; if (!this.pitLive || this.pitLive.__src !== P.run) { const R = new PT.Run(P.run.stake, 1); Object.assign(R, P.run); R.rnd = new CM.Random(CM.hashSeed(`${P.run.seed}:${P.run.spun}:${P.run.deadline}`)); this.pitLive = R; R.__src = P.run; } return this.pitLive; },
  pitKeep() { const P = this.pitStore(), R = this.pitLive; if (!R) return; const d = {}; for (const k of ["stake", "coins", "deadline", "charms", "tickets", "stage", "offers", "spun", "spinsLeft", "seed", "hero", "paidAt"]) d[k] = R[k]; P.run = d; R.__src = d; this.saveCasino && this.saveCasino(); },
  // one hero goes down
  pitStart(heroIndex, bet) {
    const P = this.pitStore(); if (P.run) return { error: "Someone is in the Pit already." }; const h = this.party[heroIndex]; if (!h || h.hp <= 0) return { error: "Choose a hero who can stand." };
    const why = this.cgStake("pit", bet); if (why) return { error: why };
    const F = this.cgStore(); F.n += 1; const seed = `${this.seed}:pit:${F.n}`, R = new PT.Run(Math.floor(bet), CM.hashSeed(seed)); R.seed = seed; R.hero = heroIndex; this.pitLive = R; P.plays += 1; this.pitKeep(); return R;
  },
  pitSpin() {
    const R = this.pitRun(); if (!R) return { error: "No one is in the Pit." }; R.rnd = new CM.Random(CM.hashSeed(`${R.seed}:${R.spun}:${R.deadline}`)); const out = R.spin(); if (out.error) return out;
    if (out.jackpot) out.card = this.cgCard(true, "The Old Lucky shows a full grid!", new CM.Random(CM.hashSeed(`${R.seed}:jackpot:${R.spun}`)));
    if (out.dropped) out.end = this.pitEnd("dropped"); else this.pitKeep(); return out;
  },
  pitPay() {
    const R = this.pitRun(), P = this.pitStore(); if (!R || !R.pay()) return null; const d = R.paidAt, out = { deadline: d, unlocked: null, card: null };
    if (d > P.best) { P.best = d; const u = PT.UNLOCK.find((c) => !P.unlocked.includes(c)); if (u) { P.unlocked.push(u); out.unlocked = u; } if (d >= 3) { const u2 = PT.UNLOCK.find((c) => !P.unlocked.includes(c)); if (u2) { P.unlocked.push(u2); out.unlocked2 = u2; } } }
    const kind = PT.CARD[d]; if (kind) out.card = this.cgCard(kind === "rare", `The Gilded Pit's deadline ${d} paid!`, new CM.Random(CM.hashSeed(`${R.seed}:card:${d}`)));
    if (R.stage === "paid") { R.rnd = new CM.Random(CM.hashSeed(`${R.seed}:ring:${d}`)); R.ring(P.unlocked); }
    if (R.stage === "free") out.end = this.pitEnd("free"); else this.pitKeep(); return out;
  },
  pitBuy(c) { const R = this.pitRun(); if (!R || !R.buy(c)) return false; this.pitKeep(); return true; },
  pitNext() { const R = this.pitRun(); if (!R || !R.next()) return false; this.pitKeep(); return true; },
  // out of the Pit: stepping out (or free after the last debt) with the coins; or dropped through the trapdoor
  pitEnd(how) {
    const R = this.pitRun(), P = this.pitStore(); if (!R) return null; const h = this.party[R.hero]; let pay = 0;
    if (how === "dropped") { if (h) h.hp = Math.max(1, Math.round(h.max * 0.1)); this.tally.pitDrops = (this.tally.pitDrops || 0) + 1; }
    else { if (how === "leave" && R.stage !== "paid") return null; pay = R.coins; this.cgPay("pit", pay); }
    P.run = null; P.last = { how, pay, deadline: R.deadline, hero: h ? h.name : "" }; this.pitLive = null; this.saveCasino && this.saveCasino(); this.saveRun && this.saveRun(); this.emit("change"); return P.last;
  },
});
