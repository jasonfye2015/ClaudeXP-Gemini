"use strict";
// The Tilewright's Table (the twenty-third big update - v13.3): tile-matching solitaire on the Gilded Joker's floor,
// with tiles of the game's own - three suits of nine (Coins, Runes, Blades), the four winds of the compass, the three
// elements (Fire, Frost, Holy), four potions and the four seasons (any potion matches any potion, any season any
// season): a hundred and forty-four, stacked in the Keep or the Tower. Take away matching pairs of free tiles - a tile
// is free when nothing lies on it and its left or its right side is open. Every deal is built backwards from a way to
// clear it, so a whole table can always be cleared; three shuffles help out of a dead end. One stake a table: a table
// cleared without a shuffle pays 1.6 times it (the Tower, an easier stack, 1.4) and a rare Claudescryption card, with one
// shuffle 0.9 (0.8) and a common card, with two 0.5, with three 0.3 - about even for a player who picks pairs at random; a table left pays back a little by how much was cleared. The window is 76l-mahjong.js.
CM.MJ = {
  SUITS: [["coins", "Coins"], ["runes", "Runes"], ["blades", "Blades"]], WINDS: ["N", "E", "S", "W"], ELEMENTS: ["fire", "frost", "holy"],
  POTIONS: ["heal", "mana", "luck", "haste"], SEASONS: ["spring", "summer", "autumn", "winter"],
  shuffles: 3, PAY: { keep: [1.6, 0.9, 0.5, 0.3], tower: [1.4, 0.8, 0.5, 0.3] }, partial: 0.5,   
};
const MJ = CM.MJ;
// the faces: 34 kinds four times over, the potions and seasons once each (each matching its own group)
MJ.faces = () => {
  const out = [];
  for (const [s] of MJ.SUITS) for (let n = 1; n <= 9; n++) for (let k = 0; k < 4; k++) out.push({ f: `${s}${n}`, g: `${s}${n}` });
  for (const w of MJ.WINDS) for (let k = 0; k < 4; k++) out.push({ f: `wind${w}`, g: `wind${w}` });
  for (const e of MJ.ELEMENTS) for (let k = 0; k < 4; k++) out.push({ f: e, g: e });
  for (const p of MJ.POTIONS) out.push({ f: `potion_${p}`, g: "potion" });
  for (const s of MJ.SEASONS) out.push({ f: `season_${s}`, g: "season" });
  return out;
};
// the layouts, in half-tile steps: [x, y, z] for each tile
MJ.LAYOUTS = {
  keep: (() => { const t = []; for (let y = 0; y <= 12; y += 2) for (let x = 0; x <= 22; x += 2) t.push([x, y, 0]); for (let y = 2; y <= 10; y += 2) for (let x = 2; x <= 20; x += 2) t.push([x, y, 1]); for (let y = 4; y <= 6; y += 2) for (let x = 8; x <= 14; x += 2) t.push([x, y, 2]); t.push([10, 5, 3], [12, 5, 3]); return t; })(),
  tower: (() => { const t = []; for (let y = 0; y <= 14; y += 2) for (let x = 0; x <= 14; x += 2) t.push([x, y, 0]); for (let y = 2; y <= 12; y += 2) t.push([-2, y, 0], [16, y, 0]); for (let x = 4; x <= 10; x += 2) t.push([x, -2, 0], [x, 16, 0]); t.push([-4, 7, 0], [18, 7, 0]);
    for (let y = 2; y <= 12; y += 2) for (let x = 2; x <= 12; x += 2) t.push([x, y, 1]); for (let y = 4; y <= 10; y += 2) for (let x = 4; x <= 10; x += 2) t.push([x, y, 2]); for (const y of [6, 8]) for (const x of [6, 8]) t.push([x, y, 3]); t.push([7, 6, 4], [7, 8, 4]); return t; })(),
};
MJ.NAMES = { keep: "The Keep", tower: "The Tower" };
MJ.Table = class {
  constructor(layout, seed) {
    this.layout = layout; this.rnd = new CM.Random(seed); this.shuffles = MJ.shuffles; this.removed = 0; this.stage = "play"; this.moves = [];
    this.tiles = MJ.LAYOUTS[layout].map(([x, y, z], i) => ({ i, x, y, z, f: null, g: null, gone: false }));
    this.deal();
  }
  live() { return this.tiles.filter((t) => !t.gone); }
  // free: nothing on it, and its left or right open
  isFree(t, set) {
    const L = set || this.live(); if (t.gone) return false;
    for (const o of L) { if (o === t) continue; if (o.z === t.z + 1 && Math.abs(o.x - t.x) < 2 && Math.abs(o.y - t.y) < 2) return false; }
    let left = false, right = false; for (const o of L) { if (o === t || o.z !== t.z || Math.abs(o.y - t.y) >= 2) continue; if (o.x === t.x - 2) left = true; if (o.x === t.x + 2) right = true; }
    return !(left && right);
  }
  free() { const L = this.live(); return L.filter((t) => this.isFree(t, L)); }
  // a deal built backwards: take away two free places at a time from the full table, giving each pair a face pair
  deal(onlyLive) {
    const places = onlyLive ? this.live() : this.tiles, faces = MJ.faces().filter(() => true);
    const pool = onlyLive ? this.live().map((t) => ({ f: t.f, g: t.g })) : faces;
    const pairs = []; const byG = {}; for (const p of pool) (byG[p.g] = byG[p.g] || []).push(p); for (const g of Object.keys(byG)) { const l = byG[g]; for (let k = 0; k + 1 < l.length; k += 2) pairs.push([l[k], l[k + 1]]); }
    for (let tries = 0; tries < 400; tries++) {
      const order = pairs.slice(); for (let i = order.length - 1; i > 0; i--) { const j = this.rnd.int(0, i); [order[i], order[j]] = [order[j], order[i]]; }
      let rest = places.slice(), ok = true; const plan = [];
      for (const pr of order) { const fr = rest.filter((t) => this.isFree(t, rest)); if (fr.length < 2) { ok = false; break; } const a = fr[this.rnd.int(0, fr.length - 1)]; let b; do b = fr[this.rnd.int(0, fr.length - 1)]; while (b === a); plan.push([a, pr[0]], [b, pr[1]]); rest = rest.filter((t) => t !== a && t !== b); }
      if (ok) { for (const [t, p] of plan) { t.f = p.f; t.g = p.g; } return true; }
    }
    return false;
  }
  match(a, b) { return a !== b && !a.gone && !b.gone && a.g === b.g; }
  take(a, b) {
    if (this.stage !== "play" || !this.match(a, b) || !this.isFree(a) || !this.isFree(b)) return false;
    a.gone = b.gone = true; this.removed += 2; this.moves.push([a.i, b.i]);
    if (!this.live().length) this.stage = "won"; return true;
  }
  pairsOpen() { const fr = this.free(), out = []; for (let i = 0; i < fr.length; i++) for (let j = i + 1; j < fr.length; j++) if (fr[i].g === fr[j].g) out.push([fr[i], fr[j]]); return out; }
  stuck() { return this.stage === "play" && !this.pairsOpen().length; }
  // a shuffle: the faces left dealt again, still clearable
  shuffle() { if (this.shuffles <= 0 || this.stage !== "play") return false; this.shuffles -= 1; this.deal(true); return true; }
};
Object.assign(CM.Game.prototype, {
  mjState() { return this.cgStore().mj || null; },
  mjTable() { const S = this.mjState(); if (!S || S.stage !== "play") return null; if (!this.mjLive || this.mjLive.key !== S.seed) { this.mjLive = new MJ.Table(S.layout, CM.hashSeed(S.seed)); this.mjLive.key = S.seed; if (S.saved) { const T = this.mjLive; S.saved.forEach(([f, g2, gone], i) => Object.assign(T.tiles[i], { f, g: g2, gone: !!gone })); T.shuffles = MJ.shuffles - (S.shuffled || 0); T.removed = T.tiles.filter((t) => t.gone).length; } } return this.mjLive; },
  mjSave() { const S = this.mjState(), T = this.mjLive; if (!S || !T) return; S.saved = T.tiles.map((t) => [t.f, t.g, t.gone ? 1 : 0]); S.shuffled = MJ.shuffles - T.shuffles; this.saveCasino && this.saveCasino(); },
  mjStart(bet, layout) {
    const S0 = this.mjState(); if (S0 && S0.stage === "play") return { error: "A table is laid out." };
    if (!MJ.LAYOUTS[layout]) layout = "keep"; const why = this.cgStake("mahjong", bet); if (why) return { error: why };
    const F = this.cgStore(); F.n += 1; F.mj = { stage: "play", bet: Math.floor(bet), layout, seed: `${this.seed}:mahjong:${F.n}` }; this.mjLive = null;
    this.saveCasino && this.saveCasino(); return F.mj;
  },
  // a pair taken (kept, so a table left mid-way comes back as it was)
  mjTake(i, j) { const T = this.mjTable(), S = this.mjState(); if (!T) return false; const ok = T.take(T.tiles[i], T.tiles[j]); if (ok) this.mjSave(); return ok; },
  mjShuffle() { const T = this.mjTable(), S = this.mjState(); if (!T || !T.shuffle()) return false; this.mjSave(); return true; },
  // the table ended - cleared, or left: what comes back
  mjSettle() {
    const S = this.mjState(), T = this.mjLive; if (!S || !T || S.stage !== "play") return null; let pay, card = null; const used = MJ.shuffles - T.shuffles, clean = used === 0;
    if (T.stage === "won") { pay = Math.round(S.bet * MJ.PAY[S.layout][used]); if (used <= 1) card = this.cgCard(clean, `The Tilewright's Table, cleared${clean ? " without a shuffle" : " with one shuffle"}!`, new CM.Random(CM.hashSeed(`${S.seed}:card`))); }
    else { const f = T.removed / T.tiles.length; pay = Math.round(S.bet * MJ.partial * f * f); }
    S.stage = "done"; S.last = { won: T.stage === "won", pay, card, removed: T.removed, clean, used }; this.cgPay("mahjong", pay); this.mjLive = null;
    this.saveCasino && this.saveCasino(); this.emit("change"); return S.last;
  },
});
