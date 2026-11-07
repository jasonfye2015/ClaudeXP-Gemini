"use strict";
// The coast and its shells (UPGRADE_PLAN_80.md, v131.0), the rules' side. Past the land's edge is the sea, not more
// forest (so the coast path has the water at its side); the coast path, the springhead, the north bridge and the
// mouth bridge by name. And shells on the sand: each tide - every four hours of the clock - leaves a fresh scatter of
// them along the Strand and the coast's sandy shore, by the seed and the tide, so a replay finds the same; walk onto
// one and the party picks it up. Cockles and whelks mostly, scallops, cowries, a piece of sea-glass, now and then a
// conch, and very rarely an oyster with a pearl in it. They sell; and Claude would like one of each for his shelf.
//   CM.SHELLS; CM.TIDE_HOURS; CM.tideOf(game); CM.shellsNow(game) -> [{ x, y, id }]; game.takeShell(x, y)
{ const P = CM.Game.prototype, C = CM.COAST, H = CM.SHORE, key = (x, y) => `${x},${y}`;
  CM.TIDE_HOURS = 4;
  CM.SHELLS = [
    { id: "cockle", name: "Cockle shell", value: 4, w: 30 }, { id: "whelk", name: "Spiral whelk", value: 6, w: 24 }, { id: "scallop", name: "Scallop shell", value: 8, w: 18 },
    { id: "glass", name: "Sea-glass", value: 10, w: 10 }, { id: "cowrie", name: "Cowrie", value: 16, w: 10 }, { id: "conch", name: "Conch", value: 45, w: 5 }, { id: "pearl", name: "Pearl", value: 120, w: 1.5 } ];
  for (const S of CM.SHELLS) CM.BASES[S.name] = { id: S.name, kind: "shell", slot: null, tier: 0, group: "stuff" };
  CM.shellItem = (id) => { const S = CM.SHELLS.find((s) => s.id === id); return { name: S.name, kind: "shell", shell: id, power: 0, value: S.value }; };
  // past the edge, the sea
  { const sa0 = CM.solidAt; CM.solidAt = (fl, x, y) => (fl && fl.number === -1 && CM.LAND_ISLE && fl.grid && fl.grid.length > H.sea && !CM.inBounds(fl, x, y) ? "sea" : sa0(fl, x, y)); }
  // names
  { const wp0 = CM.woodPlace; CM.woodPlace = function (fl, x, y) { if (fl && fl.number === -1 && fl.grid.length > H.sea) {
      if (x === C.northBridge[0] && y === C.northBridge[1]) return "the north bridge"; if (y === C.mouthBridge && x === CM.riverX(y)) return "the mouth bridge";
      if (y <= 1 && x >= C.spring[0] - 1 && x <= C.spring[1] + 1) return "the springhead";
      if (x === C.west || y === C.north || (y <= 2 && x >= C.detour[0][0] && x <= C.detour[2][0])) { const was = wp0.call(this, fl, x, y); return was && !["the Deep Wood", "the river's bank"].includes(was) ? was : "the coast path"; } }
    return wp0.call(this, fl, x, y); }; }
  // the tide's shells
  CM.tideOf = (g) => Math.floor(((g && g.clock) || 0) / (60 * CM.TIDE_HOURS));
  const sandCache = new WeakMap(), sandOf = (fl) => { if (sandCache.has(fl)) return sandCache.get(fl); const out = []; for (let y = 0; y < fl.grid.length; y++) for (let x = 0; x < fl.grid.length; x++) { const k = key(x, y); if (fl.grid[y][x] === 0 && fl.ground && fl.ground[k] === "sand" && !fl.things[k] && !(fl.features[k]) && !(CM.isPier && CM.isPier(x, y))) out.push([x, y]); } sandCache.set(fl, out); return out; };   // (not kept on the floor: it would be saved)
  CM.shellsNow = (g) => { const fl = g && g.floor; if (!fl || fl.number !== -1 || fl.grid.length <= H.sea) return []; const tide = CM.tideOf(g), sand = sandOf(fl); if (!sand.length) return [];
    const R = g.ext ? g.ext("shells") : {}; if (R.tide !== tide) { R.tide = tide; R.taken = []; }
    const rnd = new CM.Random(CM.hashSeed(`${g.seed}:shells:${tide}`)), total = CM.SHELLS.reduce((a, s) => a + s.w, 0), out = [], used = new Set();
    for (let i = 0; i < 14; i++) { const [x, y] = sand[Math.floor(rnd.next() * sand.length)], k = key(x, y); let r = rnd.next() * total, S = CM.SHELLS[0]; for (const s of CM.SHELLS) { if ((r -= s.w) < 0) { S = s; break; } }
      if (used.has(k) || R.taken.includes(k)) continue; used.add(k); out.push({ x, y, id: S.id }); }
    return out; };
  P.takeShell = function (x, y) { const s = CM.shellsNow(this).find((o) => o.x === x && o.y === y); if (!s) return false; const R = this.ext("shells"); R.taken.push(key(x, y));
    const it = CM.shellItem(s.id); this.bag.push(it); const T = this.tally || (this.tally = {}); T.shells = (T.shells || 0) + 1;
    this.say(s.id === "pearl" ? "An oyster, half-buried and shut tight - and when it's prised open, a pearl in it, pale as the moon. It goes in the pack very carefully." : s.id === "conch" ? "A conch, big as two fists, pink inside like a sunrise. Held up to an ear, it has the sea in it." : `${it.name}: picked up off the sand, and into the pack.`);
    this.sound && this.sound("coin"); this.emit("change"); return true; };
  { const em0 = P.emit; P.emit = function (ev, ...a) { const out = em0.call(this, ev, ...a); if (ev === "moved" && this.mode === "explore" && this.floor && this.floor.number === -1 && this.bag) this.takeShell(this.floor.pos[0], this.floor.pos[1]); return out; }; }
  // Claude would like one of each for his shelf
  const THANKS = { cockle: "\"A cockle. Look at the ridges on it - like someone combed it.\"", whelk: "\"A whelk - they spiral the same way, nearly always. Nobody knows why. I like that nobody knows.\"", scallop: "\"A scallop. Pilgrims used to wear these, in the old stories. I'll put it by the door.\"",
    glass: "\"Sea-glass. That was a bottle once. Somebody's bottle, somewhere else, before the sea had it.\" He holds it to the window.", cowrie: "\"A cowrie! People used to pay with these, in places. I'll keep it in case I ever need to buy something very small.\"",
    conch: "\"Oh.\" He holds the conch to his ear and goes quiet for a long moment. \"Yes. It's in there.\"", pearl: "Claude doesn't take the pearl. \"No - that's yours. Sell it, or keep it, or give it to someone. I'll just look at it a moment, if that's all right.\" He looks at it for quite a long moment." };
  CM.claudeTopics = (CM.claudeTopics || []).concat([(g) => { const V = g.vext("claude"), have = (g.bag || []).filter((i) => i.kind === "shell" && i.shell !== "pearl" && !(V.shelf || []).includes(i.shell)); return have.length ? [["shells", have.length === 1 ? "I brought you a shell" : "I brought you some shells"]] : []; }]);
  CM.claudeActs = Object.assign(CM.claudeActs || {}, { shells: (g, k, say) => { const V = g.vext("claude"); V.shelf = V.shelf || []; const lines = [];
      for (let i = g.bag.length - 1; i >= 0; i--) { const it = g.bag[i]; if (it.kind !== "shell" || V.shelf.includes(it.shell)) continue; if (it.shell === "pearl") { lines.push(THANKS.pearl); continue; } V.shelf.push(it.shell); g.bag.splice(i, 1); g.gold += 10; lines.push(THANKS[it.shell]); }
      say(`${lines.join(" ")} He finds each one a place on the shelf, and won't hear of not paying for them: ten gold apiece.${V.shelf.length >= CM.SHELLS.length - 1 ? " \"That's one of everything. The sea's been generous with you.\"" : ""}`); g.emit("change"); } });
}
