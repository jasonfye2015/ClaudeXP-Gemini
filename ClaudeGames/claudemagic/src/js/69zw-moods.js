"use strict";
// Floor moods (v37.0, UPGRADE_PLAN_32.md): about one floor in seven from the third down (by the run's seed, never a
// guardian's, a camp's or the king's) has a mood. Flooded: water standing in a third of the halls, and the torch burns
// half again as fast. Overgrown: roots and vines on the walls, and two more things growing to gather. Frozen: frost over
// everything, the party's breath showing, and the cold numbs the monsters - their blows a tenth weaker. Haunted: a pale
// fog and wisps, the dead a sixth harder to put down, and the heart sinks a little coming onto it. The look and the
// sound are the window's (76zzzzzzo-moods.js).
//   CM.MOODS; CM.moodOf(seed, number) -> id or null; floor.mood
{ const MD = CM.MOODS = {
    flooded: { name: "Flooded", line: "Water stands in the halls here, black and still, to the ankle and deeper. The torch hisses at every drip." },
    overgrown: { name: "Overgrown", line: "Something has grown down through the stone: roots thick as an arm, vines on every wall, a green smell in the dark." },
    frozen: { name: "Frozen", line: "Frost on the walls, frost on the floor, frost in your beard. Your breath hangs. Whatever lives here moves slowly in the cold." },
    haunted: { name: "Haunted", line: "A pale fog lies on this floor, and in it, now and then, a light that isn't yours. Somebody is crying, a long way off." },
  };
  CM.MOOD_EVERY = 7;
  CM.moodOf = (seed, number) => { if (!(number >= 3 && number < 1000 && number % 1 === 0)) return null; if (CM.hashSeed(`${seed}:mood:${number}`) % CM.MOOD_EVERY !== 0) return null; const ids = Object.keys(MD); return ids[CM.hashSeed(`${seed}:moodkind:${number}`) % ids.length]; };
  const mf0 = CM.makeFloor; CM.makeFloor = function (number, seed, gen) { const fl = mf0.call(this, number, seed, gen); if (!fl || fl.special || fl.number !== number) return fl;
    const things = Object.values(fl.things || {}); if (things.some((t) => ["guardian", "boss", "camp"].includes(t.type))) return fl;
    const m = CM.moodOf(seed, number); if (!m) return fl; fl.mood = m; const N = fl.grid.length, key = (x, y) => `${x},${y}`;
    if (m === "flooded") { fl.decor = fl.decor || []; for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) if (fl.grid[y][x] === 0 && !fl.things[key(x, y)] && !(fl.features || {})[key(x, y)] && CM.hashSeed(`${seed}:flood:${x}:${y}`) % 3 === 0) fl.decor.push({ kind: "water", x, y }); }
    if (m === "overgrown") { const cells = []; for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) if (fl.grid[y][x] === 0 && !fl.things[key(x, y)] && !(fl.features || {})[key(x, y)] && !(fl.pos[0] === x && fl.pos[1] === y)) cells.push(key(x, y));
      for (let i = 0; i < 2 && cells.length; i++) { const k = cells.splice(CM.hashSeed(`${seed}:overnode:${number}:${i}`) % cells.length, 1)[0]; fl.things[k] = { type: "node", band: CM.themeIndex(number) }; } }
    return fl; };
  const G = CM.Game.prototype, moodHere = (g) => (g.floor && g.floor.mood) || null;
  const em0 = G.emit; G.emit = function (ev, ...a) { if (ev === "floor" && this.floor && this.floor.mood && !this.ext("moodsMet")[this.floor.number]) { this.ext("moodsMet")[this.floor.number] = true; const M = MD[this.floor.mood];
      this.say(`${M.name}: ${M.line}`); if (this.floor.mood === "haunted") this.cheer && this.cheer(-5, "the haunting"); this.tally.moods = (this.tally.moods || 0) + 1; } return em0.call(this, ev, ...a); };
  const burn0 = G.burn; G.burn = function (...a) { const out = burn0.apply(this, a); if (moodHere(this) === "flooded" && this.light && this.light.kind === "torch" && !this.lightOut && (this.steps || 0) % 2 === 0 && this.light.left > 1) this.light.left -= 1; return out; };
  const tune0 = G.tune; G.tune = function (m) { if (!m || m.tuned) return tune0.call(this, m); const out = tune0.call(this, m), md = moodHere(this);
    if (out && md === "frozen") out.atk = Math.max(1, Math.round(out.atk * 0.9)); if (out && md === "haunted" && out.undead) { out.max = Math.round(out.max * 7 / 6); out.hp = Math.round(out.hp * 7 / 6); } return out; };
}
