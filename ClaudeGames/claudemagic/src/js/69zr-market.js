"use strict";
// Market days (v36.0, UPGRADE_PLAN_31.md): traders from away come to the Square, each on a fixed day of the run's week
// (the run's day, counted in sevens) - Hrodna of the Deep Halls with fine arms and armour on the second day, Saffi from
// the east with rare herbs, seeds and spice on the fourth, old Mott the tinker with wands, lamps and oddments on the
// sixth - and on the seventh, market day, all three and a bookseller with tomes, their stalls round the Square. Their
// stock is the week's, and dearer than the town's own; bought through the pack's shop as the peddler's is.
//   CM.TRADERS; CM.tradersOn(game) -> [id]; game.trade(id)
{ const TR = CM.TRADERS = {
    hrodna: { name: "Hrodna of the Deep Halls", day: 1, at: [20, 17], what: "fine arms and armour, dwarf-made", line: "Hrodna slaps the anvil-wood of her stall. \"Dwarf work. Your town smith couldn't make the hinges.\"" },
    saffi: { name: "Saffi from the East", day: 3, at: [24, 17], what: "rare herbs, rare seeds and spice", line: "Saffi lifts a lid and the whole Square smells of cardamom. \"From the river-country. You won't find it here twice.\"" },
    mott: { name: "Old Mott the tinker", day: 5, at: [24, 21], what: "wands, lamps and oddments", line: "Mott polishes a wand on his sleeve. \"Charged. Mostly. Try it on someone you don't like.\"" },
    books: { name: "The bookseller", day: 6, at: [20, 21], what: "tomes from far libraries", line: "The bookseller doesn't look up from her reading. \"Everything's for sale except this one.\"" },
  };
  CM.MARKET_DAY = 6;
  CM.tradersOn = (game) => { const d = ((CM.dayOf ? CM.dayOf(game) : 0) % 7 + 7) % 7; return Object.keys(TR).filter((id) => d === CM.MARKET_DAY ? true : TR[id].day === d); };
  const G = CM.Game.prototype, key = (x, y) => `${x},${y}`, week = (g) => Math.floor((CM.dayOf ? CM.dayOf(g) : 0) / 7);
  const stockFor = (g, id) => { const rnd = new CM.Random(CM.hashSeed(`${g.seed}:trader:${id}:${week(g)}`)), L = Math.max(3, (g.deepestReached ? g.deepestReached() : 3)), out = [], dear = (it, k) => { it.value = Math.round((it.value || 20) * k); return it; };
    if (id === "hrodna") for (let i = 0; i < 4; i++) { const it = CM.affix(CM.makeItem(L + 5, rnd, rnd.pick(["weapon", "armor", "helm", "shield"])), L + 10, rnd); it.unknown = false; out.push(dear(it, 1.6)); }
    if (id === "saffi") { const rare = Object.keys(CM.INGREDIENTS).filter((k) => CM.INGREDIENTS[k].rare); for (let i = 0; i < 3; i++) out.push(dear(CM.ingredient(rnd.pick(rare)), 2));
      const fs = (CM.FIELDSEEDS && CM.FIELDSEEDS.RARE) || []; for (let i = 0; i < 2 && fs.length; i++) { const c = rnd.pick(fs); if (CM.CROPS[c]) out.push(dear(CM.seed(c), 4)); }
      out.push(dear(CM.ingredient("honey" in CM.INGREDIENTS ? "honey" : rare[0]), 3)); }
    if (id === "mott") { const wands = Object.keys(CM.WANDS || {}); for (let i = 0; i < 2 && wands.length; i++) out.push(dear(CM.wand(rnd.pick(wands), 4 + rnd.int(0, 3)), 1.5)); out.push(dear(CM.lantern(), 1.2)); for (let i = 0; i < 2; i++) { const it = CM.affix(CM.makeItem(L + 3, rnd, rnd.pick(["ring", "amulet"])), L + 6, rnd); it.unknown = false; out.push(dear(it, 1.5)); } }
    if (id === "books") { const tomes = Object.keys(CM.TOMES || {}); for (let i = 0; i < 3 && tomes.length; i++) out.push(dear(CM.tome(rnd.pick(tomes)), 1.4)); out.push(CM.scroll ? dear(CM.scroll("mapping"), 1.2) : null); }
    return out.filter(Boolean); };
  // the stalls: on the floor while their day lasts
  const lay = (g) => { const fl = g.floor; if (!fl || fl.number !== 0) return; const on = new Set(CM.tradersOn(g));
    for (const [id, T] of Object.entries(TR)) { const k = key(...T.at), t = fl.things[k]; if (on.has(id)) { if (!t && fl.grid[T.at[1]][T.at[0]] === 0) fl.things[k] = { type: "trader", id, week: week(g) }; else if (t && t.type === "trader" && t.week !== week(g)) { t.week = week(g); t.stock = null; } }
      else if (t && t.type === "trader") delete fl.things[k]; } };
  G.trade = function (id) { const fl = this.floor, T = TR[id]; if (!T || !fl || fl.number !== 0) return "The traders are in the Square, on their days."; const k = key(...T.at), t = fl.things[k]; if (!t || t.type !== "trader") return `${T.name} isn't here today.`;
    if (!t.stock) t.stock = stockFor(this, id); this.stock = t.stock; this.peddling = k; this.say(T.line); this.openBag(true); return ""; };
  const em0 = G.emit; G.emit = function (ev, ...a) { if (ev === "floor" || ev === "change") lay(this); return em0.call(this, ev, ...a); };
  const use0 = G.use; G.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl && fl.number === 0) { const t = fl.things[key(fl.pos[0], fl.pos[1])]; if (t && t.type === "trader") { this.logAct && this.logAct("use"); this.trade(t.id); return; } } return use0.apply(this, a); };
}
