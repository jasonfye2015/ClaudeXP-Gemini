"use strict";
// The migrations and the stirred deep (UPGRADE_PLAN_63.md set 2.1, release 6). When a storm or a tornado strikes
// above, the land's beasts come in off it: on the first two floors, every wandering group not yet met and not
// beside the party is reseeded for the event's length with the Wood's own - wolves, a boar, a bear, the bandits
// (23b-wood.js's kinds) - at the floor's level and the group's own size, never more; when the sky clears the
// floor's own kinds are back (a group already fought stays fought). The deep stirs: on a flooded floor (plan 63's
// basins) or in the Flooded Vaults under rain, the water's own kinds - the Drowned, the Weed Hag, the Rootling -
// come up fast: one fight in three with them opens with their strike sure. Never a kind from a deeper band, never a
// fight in progress changed, never a group beside the party.
//   CM.migrationNow(game) -> boolean;  CM.migrateStep(game, minutes)  (wrapped into CM.tickClock)
//   CM.stirredNow(game, fl) -> boolean
{ const skyOn = (game) => Boolean(game && game.tally && game.tally.ext && game.tally.ext.wx && game.tally.ext.wx.cur);   // (the sky is read only once the clock has made it: a fight's rules must not roll the weather's dice, or a run and its replay part)
  const M = CM.MIGRATE = { floors: [1, 2], bands: [["Wolf", "Wolf"], ["Wolf", "Wolf", "Wolf"], ["Boar"], ["Bear"], ["Sellsword", "Sellsword"]], waterKinds: ["Drowned", "Weed Hag", "Rootling"], stirSure: 1 / 3, apart: 2 };
  CM.migrationNow = (game) => { if (!game || !game.ext || !skyOn(game)) return false; const W = CM.aboveNow(game); return (W.kind === "storm" || W.kind === "tornado") && W.strength > 0.3; };
  const beasts = (fl, n, seed) => { const rnd = new CM.Random(CM.hashSeed(`${seed}:migrate:${fl.number}:${n}`)), band = M.bands[rnd.int(0, M.bands.length - 1)].filter((k) => CM.monsterKind(k)), out = []; for (let i = 0; i < Math.max(1, Math.min(n, band.length)); i++) out.push(CM.makeMonster(CM.monsterKind(band[i % band.length]), Math.max(1, fl.number), rnd)); return out; };
  CM.migrateStep = (game, minutes = 1) => { if (!game || !game.ext || !game.floor || game.mode !== "explore") return; const fl = game.floor; if (!M.floors.includes(fl.number)) return; const E = game.ext("migrate"), on = CM.migrationNow(game), W = CM.aboveNow(game), key = on ? `${fl.number}:${W.from}` : null;
    if (on && E[fl.number] !== key) { E[fl.number] = key; let n = 0; for (const [k, t] of Object.entries(fl.things)) { if (t.type !== "monsters" || t.still || t.migrated || !t.group || !t.group.length || t.group.some((m) => m.boss || m.guardian)) continue; const [x, y] = k.split(",").map(Number); if (Math.abs(x - fl.pos[0]) + Math.abs(y - fl.pos[1]) <= M.apart) continue;
        t.was = t.group; t.group = beasts(fl, t.group.length, game.seed + ":" + k); t.migrated = true; n++; }
      if (n && game.say) game.say("Wet fur and wild eyes in the dark: the storm has driven the land's beasts in off it, and the halls near the shaft are theirs for now."); }
    else if (!on && E[fl.number]) { delete E[fl.number]; let n = 0; for (const t of Object.values(fl.things)) if (t.type === "monsters" && t.migrated) { if (t.was && t.was.length) t.group = t.was; delete t.was; delete t.migrated; n++; } if (n && game.say) game.say("The sky has cleared above: the beasts slink back out to the land, and the halls are the floor's own again."); } };
  { const t0 = CM.tickClock; CM.tickClock = (game, minutes) => { t0(game, minutes); if (game && game.ext) CM.migrateStep(game, minutes); }; }
  CM.stirredNow = (game, fl) => { if (!game || !game.ext || !fl || !(fl.number >= 1)) return false; if (CM.floodNow && CM.floodNow(game) > 0 && CM.FLOOD && CM.FLOOD.floors.includes(fl.number)) return true; if (!skyOn(game)) return false; const W = CM.aboveNow(game); return CM.themeIndex(fl.number) === 1 && (W.kind === "rain" || W.kind === "storm") && W.strength > 0.3; };
  const P = CM.Game.prototype;
  { const sc0 = P.startCombat; P.startCombat = function (key, thing, theyCame) { const out = sc0.call(this, key, thing, theyCame); const c = this.combat; if (!c || !thing || !thing.group || !CM.stirredNow(this, this.floor)) return out; if (!thing.group.some((m) => M.waterKinds.includes(m.kind || m.name)) || c.sure) return out;
      if ((CM.hashSeed(`${this.seed}:stir:${this.floor.number}:${key}:${CM.clockOf(this)}`) >>> 0) % 1000 / 1000 < M.stirSure) { c.sure = true; c.stirred = true; this.say("The water's own come up fast out of the wet: they strike before anyone can set a foot."); } return out; }; }
}
