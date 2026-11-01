"use strict";
// The South Fields, seeds from everywhere (v19.3, UPGRADE_PLAN_14.md phase 3). The shed sells the common seeds; the
// rest are found out in the world, each place with its own:
//   the dungeon's fights  - now and then a seed in the spoils: rhubarb, asparagus and artichoke near the top, coffee and
//                           pineapple in the middle depths, ember peppers from the deep
//   the Deep Wood          - a forage node sometimes gives a berry cane (blackberry, raspberry)
//   Leshy's table          - a game won, and he slips a seed across with the cards (kiwi, or another rare)
//   the Mage Tower         - mana-blossom, for floors climbed
//   Haven (Claudeablo)     - frost-berries, from the cathedral's cold gardens, for going deep enough
//   the island             - its warm side: coffee, pineapple or kiwi
//   Claudeita's cave       - moon-melon, for getting deep enough
//   the Fortress           - ember peppers from the Marshal's kitchen garden
//   the pipe               - coin-beans, a pod of copper for every level cleared
//   the Joker              - "A rare seed" at the prize counter
// The charmed crops (mana-blossom, frost-berry, ember pepper, moon-melon, coin-bean, the Joker's rose) glow in the
// field and fetch a high price. Cuttings: a crop picked at three stars or better sometimes gives a cutting, a seed
// that remembers its stars - a plot sown from it never picks worse.
{ const FD = CM.SOUTHFIELDS, FC = CM.FIELDCARE, FS = CM.FIELDSEEDS = { on: true, cutting: 0.34, fightChance: 0.06, woodChance: 0.2 };   // (on: false in the older tests, which count the pack)
  const RARE = [
    ["rhubarb", "Rhubarb", ["spring"], 6, 3, 4, 18], ["asparagus", "Asparagus", ["spring"], 7, 2, 4, 22], ["artichoke", "Artichoke", ["summer"], 7, 2, 0, 34],
    ["blackberry", "Blackberries", ["summer"], 6, 4, 3, 9], ["raspberry", "Raspberries", ["summer"], 6, 4, 3, 9], ["coffee", "Coffee", ["summer"], 8, 3, 3, 20],
    ["pineapple", "Pineapple", ["summer"], 10, 1, 0, 90], ["kiwi", "Kiwi", ["autumn"], 7, 3, 3, 14],
  ];
  // the charmed ones: [id, name, seasons, days, yield, regrows, price, the crop pack's frames they borrow, glow colour]
  const CHARMED = [
    ["manablossom", "Mana-blossom", ["spring", "summer", "autumn"], 6, 1, 4, 70, "tulip", "#80A0FF"], ["frostberry", "Frost-berries", ["autumn", "winter"], 7, 3, 4, 30, "blueberry", "#A0E8FF"],
    ["emberpepper", "Ember pepper", ["summer", "autumn"], 6, 2, 3, 40, "chili", "#FF8040"], ["moonmelon", "Moon-melon", ["summer", "autumn"], 9, 1, 0, 120, "melon", "#E0E0FF"],
    ["coinbean", "Coin-bean", ["spring", "summer", "autumn"], 5, 3, 3, 26, "beans", "#F0C040"], ["jokerrose", "The Joker's rose", ["spring", "summer", "autumn"], 6, 1, 5, 90, "rose", "#FF4060"],
  ];
  FS.RARE = RARE.map((r) => r[0]); FS.CHARMED = {};
  const add = (id, name, sow, days, yields, regrow, price) => { CM.CROPS[id] = { name, sow, days, yields, regrow, price, seedPrice: 0, rare: true, winter: sow.includes("winter") };
    CM.FOODS[id] = { name }; CM.INGREDIENTS[id] = { name, band: -1, food: true }; CM.BASES[name] = { id: name, kind: "ingredient", slot: null, tier: 0, group: "ingredient" }; CM.BASES[`${name} seed`] = { id: `${name} seed`, kind: "seed", slot: null, tier: 0, group: "stuff" }; };
  for (const r of RARE) add(...r);
  for (const [id, name, sow, days, yields, regrow, price, art, glow] of CHARMED) { add(id, name, sow, days, yields, regrow, price); CM.CROPS[id].charmed = true; FS.CHARMED[id] = { art, glow }; if (CM.cropPack && CM.cropPack.frames[art]) CM.cropPack.frames[id] = CM.cropPack.frames[art]; }
  FS.ALL = FS.RARE.concat(Object.keys(FS.CHARMED));
  const G = CM.Game.prototype;
  // a seed from a place (the dice by the seed and a count kept with the fields, so a replay finds the same)
  FS.roll = (g, what) => { const F = g.fields(); F.rolls = (F.rolls || 0) + 1; return (CM.hashSeed(`${g.seed}:fieldseeds:${what}:${F.rolls}`) % 10000) / 10000; };
  FS.pick = (g, list, what) => list[Math.floor(FS.roll(g, `${what}:which`) * list.length) % list.length];
  G.findSeeds = function (crop, n, where) { if (!FS.on) return []; const got = []; for (let i = 0; i < n; i++) got.push(CM.seed(crop)); this.gain(got, "seeds"); this.say(`${n > 1 ? `${n} ${CM.CROPS[crop].name.toLowerCase()} seeds` : `A ${CM.CROPS[crop].name.toLowerCase()} seed`} ${where} - for the South Fields.`); return got; };
  // the dungeon's spoils
  { const gain0 = G.gain; G.gain = function (items, how, ...a) { if (FS.on && how === "foe" && this.floor && this.floor.number >= 1 && FS.roll(this, "foe") < FS.fightChance) { const d = this.floor.number;
      const list = d <= 12 ? ["rhubarb", "asparagus", "artichoke"] : d <= 30 ? ["coffee", "pineapple", "artichoke"] : ["emberpepper", "pineapple", "coffee"]; items = (items || []).concat([CM.seed(FS.pick(this, list, "foe"))]); }
    return gain0.call(this, items, how, ...a); }; }
  // the Wood's nodes
  { const g0 = G.gather; if (g0) G.gather = function (thing, k) { const out = g0.call(this, thing, k); if (this.floor && this.floor.number === -1 && FS.roll(this, "wood") < FS.woodChance) this.findSeeds(FS.pick(this, ["blackberry", "raspberry"], "wood"), 1, "among the brambles"); return out; }; }
  // Leshy, a game won
  { const f0 = G.finishCardGame; G.finishCardGame = function (...a) { const r = f0.apply(this, a); if (r && r.won !== false && this.cardGame && this.cardGame.reward) this.findSeeds(FS.roll(this, "leshy") < 0.5 ? "kiwi" : FS.pick(this, FS.RARE, "leshy"), 1, "slid across the table with the cards"); return r; }; }
  // the solo places, on the way out
  { const t0 = G.leaveMageTower; if (t0) G.leaveMageTower = function (...a) { const n = this.towerRun ? this.towerRun.n || 0 : 0; const out = t0.apply(this, a); if (n >= 2) this.findSeeds("manablossom", 1 + Math.floor(n / 10), "from a window-box in the Tower"); return out; }; }
  { const c0 = G.leaveClaudeita; if (c0) G.leaveClaudeita = function (...a) { const d = this.caveRun && this.caveRun.depth ? this.caveRun.depth() : 0; const out = c0.apply(this, a); if (d >= 2) this.findSeeds("moonmelon", 1, "from the cave's pale garden"); return out; }; }
  { const f0 = G.leaveFortress; if (f0) G.leaveFortress = function (...a) { const n = this.fortRun ? this.fortRun.n || 0 : 0; const out = f0.apply(this, a); if (n >= 2) this.findSeeds("emberpepper", 1 + Math.floor(n / 8), "from the Marshal's kitchen garden"); return out; }; }
  { const h0 = G.leaveClaudeablo; G.leaveClaudeablo = function (...a) { const w = this.abloWorld, deep = w && w.player ? w.player.maxDepth || 0 : 0; const out = h0.apply(this, a); if (deep >= 3 && FS.roll(this, "haven") < 0.6) this.findSeeds("frostberry", 1, "from Haven's cold gardens"); return out; }; }
  { const c0 = G.leaveCraft; if (c0) G.leaveCraft = function (...a) { const was = Boolean(this.craft); const out = c0.apply(this, a); if (was && FS.roll(this, "island") < 0.5) this.findSeeds(FS.pick(this, ["coffee", "pineapple", "kiwi"], "island"), 1, "from the island's warm side"); return out; }; }
  { const b0 = G.leaveBros; G.leaveBros = function (how) { const r = this.brosRun, n = r ? (r.li || 0) + (r.cleared ? 1 : 0) : 0; const out = b0.call(this, how); if (n >= 1) this.findSeeds("coinbean", n, "rattling in a pipe-pod"); return out; }; }
  // the Joker's counter
  if (CM.PRIZE && CM.PRIZE.LIST && !CM.PRIZE.LIST.some((r) => r[0] === "seeds")) { CM.PRIZE.LIST.push(["seeds", "potions", "A rare seed", 60, "for the South Fields: a rare or charmed crop"]);
    const mk0 = CM.makeItem; CM.makeItem = function (depth, R, kind, ...a) { if (kind === "seeds") { const all = FS.ALL; return CM.seed(all[Math.floor((R ? R.next() : Math.random()) * all.length) % all.length]); } return mk0.call(this, depth, R, kind, ...a); }; }
  // cuttings: a good crop's stars, carried in its seed
  { const pick0 = G._fieldPick, sow0 = G._fieldSow; G._fieldPick = function (key) { const F = this.fields(), P = F.plots[key], crop = P && P.crop, q = crop ? FC.quality(this, key) : 0, giant = P && P.giant; const out = pick0.call(this, key);
      if (FS.on && !out && crop && q >= 3 && !giant && FS.roll(this, `cut:${key}`) < FS.cutting) { const s = CM.seed(crop); s.q = q; s.name = `${CM.CROPS[crop].name} cutting ${CM.stars ? CM.stars(q) : q}`; s.value = 20 + q * 8; this.gain([s], "fields"); } return out; };
    G._fieldSow = function (key, crop, i) { const it = this.bag[i], base = it && it.q ? it.q : 0; const out = sow0.call(this, key, crop, i); const P = this.fields().plots[key]; if (P) P.base = base; return out; };
    const q0 = FC.quality; FC.quality = (g, key) => { const P = g.fields().plots[key]; return Math.max(q0(g, key), P && P.crop && P.base ? Math.min(5, P.base) : 0); }; }
}
