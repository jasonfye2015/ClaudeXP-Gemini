"use strict";
// The vault under the island, and errands from town (the nineteenth update, phase 7 - v12.7). Under the island's
// highest hill (the map of four scraps marks it) lies a sealed vault of rune-cut stone (64n-claudecraft.js builds it):
// a room of spikes, a room of two lairs, and the hall of its guardian - the Hollow Mason, a golem of the island's own
// blocks (the game's own, not borrowed from anywhere), which pulls stones out of its hall's walls to mend itself. Its
// fall leaves a relic, the Mason's Plumb, and an achievement's title. The vault's stone wants a pick that would take
// silver, and breaks into rune-cut stone, which the Library asks for. Four errands from town want the island's things:
// the Smith iron, the tavern's cook meat, the Library a rune, the Guildhall's builders stone for the wall.
CM.MASON = { name: "The Hollow Mason", colour: "#8A8478", body: "wide", head: "helm", eyes: "#40E0FF", extras: ["shield"], skin: "stone", speed: 7 };
CM.MASON_RELIC = () => ({ name: "The Mason's Plumb", kind: "amulet", slot: "amulet", power: 5, value: 1600, props: { relic: true, df: 3, stat: "con", resist: "stone" } });
CM.VAULT = { level: 22, hp: 10, atk: 1.5, xp: 10, gold: 6, mendEvery: 6, mend: 0.1, trap: 0.12, trapEvery: 1 };
CM.CL.EXTRA = ["The Hollow Mason"]; CM.CL.ART = { "The Hollow Mason": CM.MASON };
Object.assign(CM.ACHIEVEMENTS, {
  stariron: { name: "A Star in the Stone", what: "Mine star-iron on the Claudecraft island", title: "the Star-Miner" },
  mason: { name: "The Hollow Mason Falls", what: "Fell the Hollow Mason in the vault under the island", title: "the Vaultbreaker" },
  homestead: { name: "A Home Through the Gate", what: "Make a homestead on the Claudecraft island", title: "of the Island" },
});
// the island's errands, alongside the townsfolk's (64b-people.js)
Object.assign(CM.ERRANDS, {
  isleiron: { giver: "the smith", building: "smith", kind: "isleiron", n: 6, island: true,
    ask: "\"They say the island through the Neather Gate has iron in its hills. Six chunks of it - or three bars, two chunks to a bar - and I'll pay you for the trouble.\"",
    done: "\"Island iron. It rings different.\" He weighs a piece in his hand. \"Good, though. Here.\"", reward: { gold: 90, renown: 12 } },
  islemeat: { giver: "the tavern's cook", building: "tavern", kind: "islemeat", n: 3, island: true,
    ask: "\"Deer and boar on that island, I hear, fat on grass nobody's grazed. Three cuts of it for my pot and you'll not regret it.\"",
    done: "\"Now that's meat.\" The pot is on before you've gone. \"Take this, and come by for a bowl.\"", reward: { gold: 50, renown: 10 } },
  islerune: { giver: "the librarian", building: "library", kind: "islerune", n: 1, island: true,
    ask: "\"Under the island's highest hill, they say, there is a vault cut with runes no one can read. Bring me a piece of its stone. Only a piece.\"",
    done: "\"Oh.\" The librarian does not look up for a long time. \"Oh, I know this hand. Take this - and thank you.\"", reward: { gold: 60, renown: 20, thing: "tome" } },
  islestone: { giver: "the Guildhall's builders", building: "guildhall", kind: "islestone", n: 128, island: true,
    ask: "\"The town wall wants mending, and island stone is square to start with. Two stacks of it - a hundred and twenty-eight blocks - in your satchels.\"",
    done: "\"Square as a die, every one.\" The foreman makes a mark. \"The wall thanks you, and so does the village.\"", reward: { gold: 30, renown: 25 } },
});
{ const P = CM.Game.prototype, B = CM.CC.B;
  const left0 = P.errandLeft, hand0 = P.handInErrand, mob0 = P.craftMakeMob, fell0 = P.craftFell, tick0 = P.craftTick, home0 = P.craftHomestead, break0 = P.craftBreak;
  const isleStone = new Set([B.STONE, B.COBBLE, B.BRICK]), meat = (i) => i.kind === "meat" && (i.meat === "Deer" || i.meat === "Boar");
  Object.assign(P, {
    errandLeft(giver) {
      const t = this.errands().taken[giver], R = CM.ERRANDS[giver]; if (!t || !R || !R.island) return left0.call(this, giver);
      if (R.kind === "isleiron") { const have = this.bag.filter((i) => i.kind === "ore" && i.ore === "iron").length + 2 * this.bag.filter((i) => i.kind === "bar" && i.bar === "iron").length; return have >= R.n ? "" : `${have} of ${R.n} island iron (a bar counts two)`; }
      if (R.kind === "islemeat") { const have = this.bag.filter(meat).length; return have >= R.n ? "" : `${have} of ${R.n} cuts of island deer or boar`; }
      if (R.kind === "islerune") return this.bag.some((i) => i.kind === "rune") ? "" : "a piece of the island vault's rune-cut stone";
      if (R.kind === "islestone") { const have = this.islandStock(isleStone); return have >= R.n ? "" : `${have} of ${R.n} island stone in the satchels`; }
      return "?";
    },
    handInErrand(giver) {
      const R = CM.ERRANDS[giver], t = this.errands().taken[giver]; if (!t || !R || !R.island) return hand0.call(this, giver);
      const why = hand0.call(this, giver); if (why) return why;
      if (R.kind === "isleiron") { let n = R.n; while (n >= 2) { const i = this.bag.findIndex((x) => x.kind === "bar" && x.bar === "iron"); if (i < 0) break; this.bag.splice(i, 1); n -= 2; } while (n > 0) { const i = this.bag.findIndex((x) => x.kind === "ore" && x.ore === "iron"); if (i < 0) { const b = this.bag.findIndex((x) => x.kind === "bar" && x.bar === "iron"); if (b < 0) break; this.bag.splice(b, 1); n -= 2; continue; } this.bag.splice(i, 1); n -= 1; } }
      if (R.kind === "islemeat") for (let n = 0; n < R.n; n++) { const i = this.bag.findIndex(meat); if (i >= 0) this.bag.splice(i, 1); }
      if (R.kind === "islerune") { const i = this.bag.findIndex((x) => x.kind === "rune"); if (i >= 0) this.bag.splice(i, 1); }
      if (R.kind === "islestone") this.islandTake(isleStone, R.n);
      return "";
    },
    craftMakeMob(kind, x, y, z, level) {
      if (kind !== CM.MASON.name) return mob0.call(this, kind, x, y, z, level);
      const L = this.craftLife(), m = CM.makeMonster(CM.MASON, level, L.rnd), w = new CM.CC.Walker(this.craft.world, [x, y, z], 0, 0); w.canFly = false;
      m.max = m.hp = m.max * CM.VAULT.hp; m.atk = Math.round(m.atk * CM.VAULT.atk); m.xp *= CM.VAULT.xp; m.gold *= CM.VAULT.gold;
      return { id: ++L.ids, kind: CM.MASON.name, K: CM.MASON, m, w, r: 0.75, h: 2.6, level, wild: false, hostile: true, cd: 1, shotT: 99, hitAt: -9, fellAt: null, wanderT: 0, walk: false, stuck: 0, last: [x, z], mason: true, mendT: CM.VAULT.mendEvery };
    },
    craftFell(o) {
      fell0.call(this, o); if (!o.mason) return; const K = this.craftStore(), L = this.craftLife();
      K.masonDown = true; const relic = CM.MASON_RELIC(); L.loot.push(relic); this.tally.mason = true;
      this.craftSay("The Hollow Mason comes apart, stone by stone, and is still. In what was its chest: the Mason's Plumb.");
      if (this.achieve) this.achieve("mason"); this.saveVillage && this.saveVillage();
    },
    craftHomestead(key) { const first = !this.craftStore().homestead, ok = home0.call(this, key); if (ok && first && this.achieve) this.achieve("homestead"); return ok; },
    craftBreak() { const cr = this.craft, hit = cr && cr.target[0], was = hit ? cr.world.get(...hit) : 0, b = break0.call(this); if (b && was === B.STARIRON_ORE && this.achieve) this.achieve("stariron"); return b; },
    // the vault's life: the spikes underfoot, the Mason waking in its hall, and its mending from the walls
    craftVault(dt) {
      const cr = this.craft, W = cr.world, v = W.vault, L = this.craftLife(), K = this.craftStore(), p = cr.walker.pos, h = cr.hero; if (!v) return;
      const under = W.get(Math.floor(p[0]), Math.floor(p[1] - 0.05), Math.floor(p[2]));
      L.trapT = Math.max(0, (L.trapT || 0) - dt);
      if (under === B.TRAP && cr.walker.onGround && L.trapT <= 0) { L.trapT = CM.VAULT.trapEvery; (L.events = L.events || []).push({ kind: "trap" }); this.craftHurt(Math.max(1, Math.round(h.max * CM.VAULT.trap)), "Spikes"); }
      const [hx0, hx1] = v.rooms[2], inHall = p[0] >= hx0 && p[0] <= hx1 + 1 && p[2] >= v.z0 && p[2] <= v.z1 + 1 && Math.abs(p[1] - v.guard.y) < 3;
      const mason = L.mobs.find((o) => o.mason && o.fellAt === null);
      if (!K.masonDown && !mason && inHall) { const o = this.craftMakeMob(CM.MASON.name, v.guard.x, v.guard.y + 0.01, v.guard.z, CM.VAULT.level + Math.min(8, K.nights || 0)); L.mobs.push(o); (L.events = L.events || []).push({ kind: "mason" }); this.craftSay("The far wall shifts. Stone pulls free of stone, and stands up: the Hollow Mason."); }
      if (mason) this.craftMend(mason, dt);
    },
    // the Mason mends: a stone pulled from its hall's walls, a tenth of its health back
    craftMend(o, dt) {
      if ((o.mendT -= dt) > 0) return false; o.mendT = CM.VAULT.mendEvery; if (o.m.hp >= o.m.max) return false;
      const W = this.craft.world, v = W.vault, [x0, x1] = v.rooms[2], cand = [];
      for (let x = x0 - 1; x <= x1 + 1; x++) for (let z = v.z0 - 1; z <= v.z1 + 1; z++) for (let y = v.guard.y; y <= v.guard.y + 3; y++) if (W.get(x, y, z) === B.VAULT && (x === x0 - 1 || x === x1 + 1 || z === v.z0 - 1 || z === v.z1 + 1)) cand.push([x, y, z]);
      if (!cand.length) return false; const [x, y, z] = cand[this.craftLife().rnd.int(0, cand.length - 1)];
      W.set(x, y, z, B.AIR); o.m.hp = Math.min(o.m.max, o.m.hp + Math.round(o.m.max * CM.VAULT.mend));
      (this.craftLife().events = this.craftLife().events || []).push({ kind: "mend", at: [x, y, z] }); this.craftSay("The Mason tears a stone from the wall and presses it into itself.");
      return [x, y, z];
    },
    craftTick(dt) { tick0.call(this, dt); if (this.craft) this.craftVault(dt); },
  });
}
