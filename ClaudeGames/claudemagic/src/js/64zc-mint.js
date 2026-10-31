"use strict";
// The Gilded Mint (the twenty-seventh big update - v13.7): an idle game on the Gilded Joker's floor. Strike the coin
// press for gold dust; spend the dust on those who mint it for you - apprentices, bellows, presses, alchemists, kilns,
// golems, star-forges and a dragon's hoard - each dearer than the last (a seventh again for each one owned); upgrades
// double a kind at 10, 25, 50 and 100 owned, and better hammers strike harder. Now and then a lucky coin glints: catch
// it for a burst. When the mint has made a million in all, it can be melted down for Gilded Seals (a twentieth more
// dust each, for good). It keeps minting while you are away (half as fast, up to eight hours). The real reward: gold
// and a Claudescryption card the first time the dust minted in all passes each mark (a hundred, a thousand ... a
// trillion) - common, then stronger, then rare. It costs nothing. The window is 76s-mint.js.
CM.MN = {
  KINDS: [["apprentice", "Apprentice", 15, 0.1], ["bellows", "Bellows", 100, 1], ["press", "Coin Press", 1100, 8], ["alchemist", "Alchemist", 12e3, 47], ["kiln", "Philosopher's Kiln", 13e4, 260],
    ["golem", "Gilded Golem", 1.4e6, 1400], ["forge", "Star-Forge", 2e7, 7800], ["hoard", "Dragon's Hoard", 3.3e8, 44000]],
  growth: 1.15, TIERS: [10, 25, 50, 100], HAMMERS: [[100, 2], [5e3, 4], [5e5, 8], [5e7, 16], [5e9, 32]], sealAt: 1e6, sealBonus: 0.05, away: 8 * 3600, awayRate: 0.5,
  MARKS: [1e2, 1e3, 1e4, 1e5, 1e6, 1e7, 1e8, 1e9, 1e10, 1e11, 1e12], gold: (i) => 20 + i * 18,
  luckyEvery: [60, 150], luckyFor: 30, luckyMult: 7,
};
const MN = CM.MN;
MN.fmt = (n) => { if (n < 1e3) return n < 10 ? (Math.floor(n * 10) / 10).toString() : Math.floor(n).toString(); const u = ["", "thousand", "million", "billion", "trillion", "quadrillion", "quintillion"], k = Math.min(u.length - 1, Math.floor(Math.log10(n) / 3)); return `${(n / Math.pow(1000, k)).toFixed(2)} ${u[k]}`; };
MN.cost = (k, owned) => Math.ceil(MN.KINDS[k][2] * Math.pow(MN.growth, owned));
MN.upCost = (k, tier) => MN.KINDS[k][2] * [10, 50, 500, 5000][tier];
MN.Mint = class {
  constructor(s) { Object.assign(this, { dust: 0, total: 0, allTime: 0, owned: MN.KINDS.map(() => 0), ups: MN.KINDS.map(() => 0), hammer: 0, seals: 0, clicks: 0, lucky: null, luckyUntil: 0, nextLucky: 90, t: 0, marks: 0 }, s || {}); }
  mult(k) { return Math.pow(2, this.ups[k]) * (1 + this.seals * MN.sealBonus) * (this.t < this.luckyUntil ? MN.luckyMult : 1); }
  rate() { return MN.KINDS.reduce((s, K, k) => s + this.owned[k] * K[3] * this.mult(k), 0); }
  baseRate() { return MN.KINDS.reduce((s, K, k) => s + this.owned[k] * K[3] * Math.pow(2, this.ups[k]) * (1 + this.seals * MN.sealBonus), 0); }
  perClick() { const hm = this.hammer ? MN.HAMMERS[this.hammer - 1][1] : 1; return (hm + this.baseRate() * 0.01 * this.hammer) * (this.t < this.luckyUntil ? MN.luckyMult : 1); }
  gain(n) { this.dust += n; this.total += n; this.allTime += n; }
  strike() { this.clicks += 1; const n = this.perClick(); this.gain(n); return n; }
  buy(k) { const c = MN.cost(k, this.owned[k]); if (this.dust < c) return false; this.dust -= c; this.owned[k] += 1; return true; }
  // upgrades open as the kind is owned: the next tier, while there is one
  upOpen(k) { const t = this.ups[k]; return t < MN.TIERS.length && this.owned[k] >= MN.TIERS[t]; }
  upgrade(k) { if (!this.upOpen(k)) return false; const c = MN.upCost(k, this.ups[k]); if (this.dust < c) return false; this.dust -= c; this.ups[k] += 1; return true; }
  hammerOpen() { return this.hammer < MN.HAMMERS.length; }
  buyHammer() { const H = MN.HAMMERS[this.hammer]; if (!H || this.dust < H[0]) return false; this.dust -= H[0]; this.hammer += 1; return true; }
  // time passes: the minting; a lucky coin glints now and then (and fades if not caught)
  update(dt, rnd) {
    this.t += dt; this.gain(this.rate() * dt);
    if (this.lucky && this.t > this.lucky.until) this.lucky = null;
    if (!this.lucky && this.t >= this.nextLucky) { this.lucky = { x: 0.15 + rnd.next() * 0.7, y: 0.15 + rnd.next() * 0.6, until: this.t + 12 }; this.nextLucky = this.t + MN.luckyEvery[0] + rnd.next() * (MN.luckyEvery[1] - MN.luckyEvery[0]); return "lucky"; }
    return null;
  }
  // a lucky coin caught: seven times everything for half a minute, or a lump of a quarter-hour's minting
  catchLucky(rnd) { if (!this.lucky) return null; this.lucky = null; if (rnd.chance(0.5)) { this.luckyUntil = this.t + MN.luckyFor; return { kind: "frenzy" }; } const n = Math.max(13, this.baseRate() * 900, this.dust * 0.1); this.gain(n); return { kind: "lump", n }; }
  sealsIfMelted() { return this.total >= MN.sealAt ? Math.floor(Math.sqrt(this.total / MN.sealAt)) : 0; }
  melt() { const s = this.sealsIfMelted(); if (!s) return 0; this.seals += s; Object.assign(this, { dust: 0, total: 0, owned: MN.KINDS.map(() => 0), ups: MN.KINDS.map(() => 0), hammer: 0, luckyUntil: 0 }); return s; }
  toJSON() { const o = {}; for (const k of ["dust", "total", "allTime", "owned", "ups", "hammer", "seals", "clicks", "nextLucky", "t", "marks", "luckyUntil"]) o[k] = this[k]; return o; }
};
Object.assign(CM.Game.prototype, {
  mnStore() { const F = this.cgStore(); F.mint = F.mint || {}; return F.mint; },
  mnLive() { const S = this.mnStore(); if (!this.mnMint) { this.mnMint = new MN.Mint(S.state); this.mnRnd = new CM.Random(CM.hashSeed(`${this.seed}:mint:${S.opens = (S.opens || 0) + 1}`)); } return this.mnMint; },
  // back again: what was minted while away (half as fast, at most eight hours)
  mnAway(nowMs) { const S = this.mnStore(), M = this.mnLive(); if (!S.at) { S.at = nowMs; return 0; } const secs = Math.max(0, Math.min(MN.away, (nowMs - S.at) / 1000)); S.at = nowMs; const n = M.baseRate() * secs * MN.awayRate; if (n > 0) M.gain(n); return n; },
  mnKeep(nowMs) { const S = this.mnStore(); if (this.mnMint) S.state = this.mnMint.toJSON(); if (nowMs) S.at = nowMs; this.saveCasino && this.saveCasino(); },
  // the marks passed: gold and a card the first time for each
  mnMarks() {
    const M = this.mnLive(), out = [];
    while (M.marks < MN.MARKS.length && M.allTime >= MN.MARKS[M.marks]) {
      const i = M.marks++, n = i + 1, gold = MN.gold(i); this.gold += gold; const F = this.cgStore(); F.paid.mint = (F.paid.mint || 0) + gold;
      const tier = n >= 10 ? "rare" : n >= 5 ? "better" : "common", card = this.cgTierCard(tier, `The Gilded Mint has made ${MN.fmt(MN.MARKS[i])} dust!`, new CM.Random(CM.hashSeed(`${this.seed}:mint:card:${i}`)));
      out.push({ mark: MN.MARKS[i], gold, card, tier });
    }
    if (out.length) { this.mnKeep(); this.emit("change"); }
    return out;
  },
});
