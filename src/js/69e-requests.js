"use strict";
// The town's asking (v18.4): the village puts its needs where every place can answer them.
// - The request board, by the well: three requests a real day, each from a different place - things to bring (island
//   timber or stone, metal bars, a gem, essences, the farm's food, meat, something from Haven, the Joker's tickets) or
//   things to do (win at Leshy's table, reach a floor, go down into Haven, come through the pipe, play at the Joker,
//   land a fish, win fights). Done, a request pays renown and gold; a new day posts new ones (one left undone stays
//   for a day more).
// - The buildings' needs: past their first levels, the village's buildings want things from the other places as well
//   as renown - the smith island bars and a gem, the library rune-cut stone, the shrine essences, the home island
//   timber and stone, the tavern meat, the merchant goods from Haven, the guildhall the Joker's tickets, the garden and
//   the farm the farm's food and the dungeon's essences. A build takes them from the pack (and the island satchels).
// The window is 76zzzf-requests.js.
{ const RQ = CM.TOWNREQ = { per: 3 };
  const bag = (g, test) => g.bag.filter(test).length, take = (g, test, n) => { for (let i = g.bag.length - 1; i >= 0 && n > 0; i--) if (test(g.bag[i])) { g.bag.splice(i, 1); n -= 1; } };
  const food = (i) => i.kind === "ingredient" && CM.INGREDIENTS[i.ingredient] && CM.INGREDIENTS[i.ingredient].food, haven = (i) => i.props && i.props.from === "Claudeablo";
  // the things a place can be asked for: [id, place, words, have(g), take(g)] - or for a deed, a counter that must rise by n
  const isle = (set) => [(g) => (g.islandStock ? g.islandStock(set) : 0), (g, n) => g.islandTake(set, n)];
  RQ.KINDS = [
    { id: "timber", place: "the island", n: 32, what: (n) => `${n} island timber (logs or planks)`, have: (g) => isle(CM.CC.TIMBER)[0](g), take: (g, n) => isle(CM.CC.TIMBER)[1](g, n) },
    { id: "stone", place: "the island", n: 32, what: (n) => `${n} island stone (stone, cobble or brick)`, have: (g) => isle(CM.CC.STONEWORK)[0](g), take: (g, n) => isle(CM.CC.STONEWORK)[1](g, n) },
    { id: "bars", place: "the island", n: 2, what: (n) => `${n} metal bars`, have: (g) => bag(g, (i) => i.kind === "bar"), take: (g, n) => take(g, (i) => i.kind === "bar", n) },
    { id: "gem", place: "the island", n: 1, what: () => "a gem", have: (g) => bag(g, (i) => i.kind === "gem"), take: (g, n) => take(g, (i) => i.kind === "gem", n) },
    { id: "essence", place: "the dungeon", n: 2, what: (n) => `${n} essences`, have: (g) => bag(g, (i) => i.kind === "essence"), take: (g, n) => take(g, (i) => i.kind === "essence", n) },
    { id: "food", place: "the farm", n: 4, what: (n) => `${n} of the farm's food`, have: (g) => bag(g, food), take: (g, n) => take(g, food, n) },
    { id: "meat", place: "the hunt", n: 3, what: (n) => `${n} cuts of meat`, have: (g) => bag(g, (i) => i.kind === "meat"), take: (g, n) => take(g, (i) => i.kind === "meat", n) },
    { id: "haven", place: "Haven", n: 1, what: () => "something brought back from Haven", have: (g) => bag(g, haven), take: (g, n) => take(g, haven, n) },
    { id: "tickets", place: "the Joker", n: 150, what: (n) => `${n} prize tickets`, have: (g) => (g.cgStore ? g.tkStore().n : 0), take: (g, n) => { g.tkStore().n -= n; } },
    { id: "cards", place: "Leshy's cabin", n: 1, deed: true, what: () => "a game won at Leshy's table", count: (g) => (g.cards ? g.cards().wins || 0 : 0) },
    { id: "floor", place: "the dungeon", n: 1, deed: true, what: () => "five floors more than the deepest so far, on one run", count: (g) => Math.max(0, ...(g.trail || []).map(([n]) => n)), goal: (g) => Math.max(5, Math.max(0, ...(g.trail || []).map(([n]) => n)) + 5) },
    { id: "ablo", place: "Haven", n: 1, deed: true, what: () => "a visit to Haven", count: (g) => (g.abloStore ? g.abloStore().visits || 0 : 0) },
    { id: "pipe", place: "the pipe", n: 1, deed: true, what: () => "a trip down the pipe", count: (g) => (g.tally.brosTrips || 0) + (g.tally.brosWins || 0) },
    { id: "joker", place: "the Joker", n: 5, deed: true, what: (n) => `${n} plays at the Joker's tables`, count: (g) => (g.cgStore ? Object.values(g.cgStore().played || {}).reduce((a, b) => a + b, 0) : 0) },
    { id: "fish", place: "the pond", n: 1, deed: true, what: () => "a fish landed at the Joker's pond", count: (g) => (g.pdStore ? g.pdStore().landed || 0 : 0) },
    { id: "fights", place: "the dungeon", n: 8, deed: true, what: (n) => `${n} fights won`, count: (g) => g.tally.fights || 0 },
  ];
  RQ.byId = Object.fromEntries(RQ.KINDS.map((k) => [k.id, k]));
  RQ.day = (now) => { const d = new Date(now || Date.now()); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
  RQ.GIVERS = ["the tavern-keeper", "the merchant", "the smith", "the librarian", "the priest", "the farmer's hand", "the chronicler", "the guildmaster"];
  // the buildings' needs: by building, by the level being raised to
  CM.VILLAGE_MATS = { smith: { 2: [["bars", 3]], 3: [["bars", 4], ["gem", 1]] }, library: { 4: [["stone", 48]], 5: [["essence", 2], ["haven", 1]] }, shrine: { 4: [["essence", 2]], 5: [["essence", 3], ["gem", 1]] },
    home: { 3: [["timber", 32]], 4: [["timber", 64], ["stone", 64]], 5: [["stone", 96], ["bars", 2]] }, tavern: { 2: [["meat", 4], ["food", 4]] }, merchant: { 3: [["haven", 1]], 4: [["haven", 2], ["tickets", 300]] },
    guildhall: { 3: [["tickets", 200]], 4: [["essence", 3], ["haven", 1]] }, garden: { 2: [["food", 4]], 3: [["essence", 2]] }, farm: { 3: [["food", 6]], 4: [["stone", 32]], 5: [["essence", 2], ["timber", 48]] } };
  CM.matsOn = true;
  CM.villageNeeds = (id, lvl) => (CM.matsOn === false ? [] : (CM.VILLAGE_MATS[id] || {})[lvl + 1] || []);
  CM.villageIdOf = (V) => Object.keys(CM.VILLAGE).find((k) => CM.VILLAGE[k] === V);
  // the needs in words, for a build's button: " and 3 metal bars (2 in hand)"
  CM.matsNote = (g, V, lvl) => { const id = typeof V === "string" ? V : CM.villageIdOf(V), need = id ? CM.villageNeeds(id, lvl) : []; return need.length ? `, and ${need.map(([k, n]) => `${RQ.byId[k].what(n)} (${Math.min(n, RQ.byId[k].have(g))} of ${n})`).join(", ")}` : ""; };
  const P = CM.Game.prototype, build0 = P.build;
  Object.assign(P, {
    build(id) { const lvl = this.villageLevel(id), need = CM.villageNeeds(id, lvl), short = need.filter(([k, n]) => RQ.byId[k].have(this) < n);
      const B = CM.VILLAGE[id]; if (B && lvl < B.costs.length && short.length) return `${B.name}'s next level wants ${short.map(([k, n]) => `${RQ.byId[k].what(n)} (${RQ.byId[k].have(this)} in hand)`).join(" and ")}, besides the renown.`;
      const why = build0.call(this, id); if (!why) { for (const [k, n] of need) RQ.byId[k].take(this, n); this.saveVillage && this.saveVillage(); } return why; },
    // ---- the request board ----
    rqStore() { this.village = this.village || {}; const S = this.village.requests = this.village.requests || { day: "", list: [], done: 0 }; return S; },
    rqList(now) { const S = this.rqStore(), day = RQ.day(now); if (S.day !== day) { const keep = S.list.filter((q) => !q.done && !q.carried).map((q) => Object.assign(q, { carried: true })).slice(0, 1), R = new CM.Random(CM.hashSeed(`${this.seed}:requests:${day}`)), places = new Set(keep.map((q) => RQ.byId[q.kind].place)), list = keep.slice();
        for (const K of R.shuffle(RQ.KINDS.slice())) { if (list.length >= RQ.per) break; if (places.has(K.place)) continue; places.add(K.place); const goal = K.goal ? K.goal(this) : K.n;
          list.push({ kind: K.id, n: goal, base: K.deed && !K.goal ? K.count(this) : 0, giver: R.pick(RQ.GIVERS), renown: 10 + R.int(0, 3) * 5, gold: 40 + R.int(0, 6) * 20, done: false }); }
        S.day = day; S.list = list; this.saveVillage && this.saveVillage(); } return S.list; },
    rqProgress(q) { const K = RQ.byId[q.kind]; if (!K) return 0; if (!K.deed) return Math.min(q.n, K.have(this)); if (K.goal) return K.count(this) >= q.n ? q.n : K.count(this); const c = K.count(this); if (c < q.base) q.base = 0; return Math.min(q.n, c - q.base); },
    rqDone(i) { const q = this.rqList()[i]; if (!q) return { error: "No such request." }; if (q.done) return { error: "Done already." }; if (this.rqProgress(q) < q.n) return { error: "Not done yet." };
      const K = RQ.byId[q.kind]; if (!K.deed) K.take(this, q.n); q.done = true; const S = this.rqStore(); S.done += 1; this.village.renown = (this.village.renown || 0) + q.renown; this.gold += q.gold; this.saveVillage && this.saveVillage(); this.sound && this.sound("coin"); this.emit && this.emit("change");
      return { renown: q.renown, gold: q.gold, giver: q.giver }; },
    rqWords(q) { const K = RQ.byId[q.kind]; return K ? K.what(q.n) : "?"; },
  });
  // the pipe's trips, counted (the request wants a trip, not only a win)
  { const lb = P.leaveBros; P.leaveBros = function (how) { if (this.brosRun) this.tally.brosTrips = (this.tally.brosTrips || 0) + 1; return lb.call(this, how); }; }
}
