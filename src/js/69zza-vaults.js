"use strict";
// Secret floors (v37.4, UPGRADE_PLAN_32.md): about one floor in nine from the fourth hides a stair under a flagstone in
// a quiet corner. It is found by searching the square (Space on it), by the hound within two squares, or by a Rogue
// passing beside it (one time in two). It leads down to a small hand-made vault with its own story, its keeper - a ghost
// who tells it, in three parts, one each time spoken to - and its prize: the Drowned Chapel (a priest who would not
// leave; the Bell-Rope Charm), the Counting-House (a dwarf still at his ledgers; the Ledger Ring and his hoard), the
// Sealed Library (the last librarian; two tomes and the Reader's Circlet). Each vault once a run.
//   CM.VAULTS; CM.VAULT_NUMBERS; floor.vaultHidden = {k, kind}; things: vaultstair, vaultkeeper, vaultexit
{ const V = CM.VAULTS = {
    chapel: { name: "the Drowned Chapel", keeper: "Father Anselm, drowned", rows: ["###########", "#.........#", "#.#.#.#.#.#", "#.........#", "#.#.#.#.#.#", "#....K....#", "#.#.#.#.#.#", "#....P....#", "#.........#", "#....E....#", "###########"],
      story: ["\"The river came up through the floor in the spring of the plague year. They told me to go. I said a priest doesn't leave his chapel.\"", "\"I rang the bell for a whole night so the town would know. Nobody came. I think they heard, though. I like to think they heard.\"", "\"Take the bell-rope. It's the only thing in here that ever tried to save anyone.\""],
      prize: () => ({ name: "Bell-Rope Charm", base: "Bell-Rope Charm", kind: "amulet", slot: "amulet", power: 0, value: 700, unknown: false, props: { rarity: "unique", df: 2, resist: "fear", stats: { wis: 2 }, regen: 1 } }) },
    counting: { name: "the Counting-House", keeper: "Durgin Tallyhand, a dwarf ghost", rows: ["###########", "#.........#", "#.###.###.#", "#.#.....#.#", "#.#..K..#.#", "#.........#", "#.#..P..#.#", "#.#.....#.#", "#.###.###.#", "#....E....#", "###########"],
      story: ["\"Forty years I kept the Deep Halls' books. Every coin in, every coin out. Then the coins stopped coming in.\"", "\"They went down to see why, the miners. I stayed to write it down. It's all in the ledger: the day, the hour, the last entry.\"", "\"Take the ring and the chest. Somebody should spend it. That's what it's for.\""],
      prize: () => ({ name: "Ledger Ring", base: "Ledger Ring", kind: "ring", slot: "ring", power: 2, value: 800, unknown: false, props: { rarity: "unique", stat: "luck", killGold: 0.2 } }), gold: 600 },
    library: { name: "the Sealed Library", keeper: "Mistress Orla, the last librarian", rows: ["###########", "#.........#", "#.##.#.##.#", "#.........#", "#.##.#.##.#", "#....K....#", "#.##.#.##.#", "#....P....#", "#.##.#.##.#", "#....E....#", "###########"],
      story: ["\"When the king turned, the college sealed us in with the books. To keep them safe, they said. They meant to keep us quiet.\"", "\"I have read every one of them since. Twice. Some of them a great many times.\"", "\"Take the circlet and what's on the lectern. Read them somewhere with windows.\""],
      prize: () => ({ name: "Reader's Circlet", base: "Reader's Circlet", kind: "helm", slot: "helm", power: 2, value: 750, unknown: false, props: { rarity: "unique", stats: { int: 3 }, spellPower: 1 } }), tomes: 2 },
  };
  for (const k of Object.keys(V)) { const it = V[k].prize(); CM.BASES[it.name] = { id: it.name, kind: it.kind, slot: it.slot, tier: 4, group: it.kind }; }
  CM.VAULT_NUMBERS = { chapel: -1.91, counting: -1.92, library: -1.93 }; CM.VAULT_SPEC = {}; CM.VAULT_EVERY = 9;
  CM.isVault = (n) => Object.values(CM.VAULT_NUMBERS).includes(n);
  const key = (x, y) => `${x},${y}`, kindOf = (n) => Object.keys(CM.VAULT_NUMBERS).find((k) => CM.VAULT_NUMBERS[k] === n);
  CM.makeVault = function (number, seed) { const kind = kindOf(number), K = V[kind], rows = K.rows, N = rows.length, grid = [], things = {}; let pos = [5, 9];
    for (let y = 0; y < N; y++) { grid.push([]); for (let x = 0; x < N; x++) { const c = rows[y][x]; grid[y].push(c === "#" ? 1 : 0);
      if (c === "K") things[key(x, y)] = { type: "vaultkeeper", kind, told: 0 }; if (c === "P") things[key(x, y)] = { type: "chest", gold: K.gold || 120, items: [], vaultPrize: kind }; if (c === "E") { things[key(x, y)] = { type: "vaultexit" }; pos = [x, y]; } } }
    const decor = kind === "chapel" ? [] : null; if (decor) for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) if (grid[y][x] === 0 && !things[key(x, y)] && (x + y) % 2 === 0) decor.push({ kind: "water", x, y });
    return { number, grid, pos, facing: 0, things, features: {}, dark: [], seen: [], decor: decor || [], special: "vault", vault: kind }; };
  const mf0 = CM.makeFloor; CM.makeFloor = function (number, seed, gen) { if (CM.isVault(number)) return CM.makeVault(number, seed);
    const fl = mf0.call(this, number, seed, gen); if (!fl || fl.special || fl.number !== number || !(number >= 4 && number < 1000 && number % 1 === 0) || fl.mood || fl.puzzle) return fl;
    if (Object.values(fl.things).some((t) => ["guardian", "boss", "camp"].includes(t.type)) || CM.hashSeed(`${seed}:vault:${number}`) % CM.VAULT_EVERY !== 0) return fl;
    const N = fl.grid.length, corners = []; for (let y = 1; y < N - 1; y++) for (let x = 1; x < N - 1; x++) { if (fl.grid[y][x] !== 0 || fl.things[key(x, y)] || (fl.features || {})[key(x, y)] || (fl.pos[0] === x && fl.pos[1] === y)) continue; const walls = CM.DIRS.filter(([dx, dy]) => fl.grid[y + dy][x + dx] === 1).length; if (walls >= 3) corners.push(key(x, y)); }
    if (corners.length) fl.vaultHidden = { k: corners[CM.hashSeed(`${seed}:vaultat:${number}`) % corners.length], kind: Object.keys(V)[CM.hashSeed(`${seed}:vaultkind:${number}`) % 3] }; return fl; };
  const tf0 = CM.themeFor; CM.themeFor = (n) => (CM.isVault(n) && CM.VAULT_SPEC[n] ? tf0(CM.VAULT_SPEC[n].from) : tf0(n));
  const G = CM.Game.prototype;
  G.revealVault = function (how) { const fl = this.floor, H = fl && fl.vaultHidden; if (!H || fl.things[H.k]) return false; fl.things[H.k] = { type: "vaultstair", kind: H.kind }; this.sound && this.sound("unlock"); this.say(how); this.tally.vaultsFound = (this.tally.vaultsFound || 0) + 1; this.emit("change"); return true; };
  const look0 = G.look; G.look = function (...a) { const out = look0.apply(this, a), fl = this.floor, H = fl && fl.vaultHidden; if (!H || fl.things[H.k]) return out; const [hx, hy] = H.k.split(",").map(Number), d = Math.abs(hx - fl.pos[0]) + Math.abs(hy - fl.pos[1]);
    if (d <= 2 && this.petName && this.petName("dog")) this.revealVault(`${this.petName("dog")} scrabbles at a flagstone in the corner, whining - and under it, there's a stair going down.`);
    else if (d === 1 && this.alive().some((h) => h.cls === "Rogue") && CM.hashSeed(`${this.seed}:vaultrogue:${fl.number}:${this.steps || 0}`) % 2 === 0) this.revealVault(`${this.alive().find((h) => h.cls === "Rogue").name} taps a flagstone with a boot: it rings hollow. Under it, a stair.`);
    return out; };
  const use0 = G.use; G.use = function (...a) { const fl = this.floor; if (this.mode === "explore" && fl) { const k = key(fl.pos[0], fl.pos[1]), t = fl.things[k];
      if (!t && fl.vaultHidden && fl.vaultHidden.k === k) { this.logAct && this.logAct("use"); this.revealVault("You kneel and run a hand over the flags: one of them moves. Under it, a narrow stair going down into the dark."); return; }
      if (t && t.type === "vaultstair") { this.logAct && this.logAct("use"); const n = CM.VAULT_NUMBERS[t.kind]; if (this.ext("vaults")[t.kind]) { this.say("The stair goes down to a room you have already emptied."); return; }
        CM.VAULT_SPEC[n] = { from: fl.number, at: k }; this.ext("vaultFrom")[n] = { from: fl.number, at: k }; this.sound && this.sound("stairs"); this.enterFloor(n, "down"); this.say(`Down the hidden stair, into ${V[t.kind].name}.`); return; }
      if (t && t.type === "vaultkeeper") { this.logAct && this.logAct("use"); const K = V[t.kind]; this.say(`${K.keeper}: ${K.story[Math.min(t.told, K.story.length - 1)]}`); t.told = Math.min(K.story.length, t.told + 1); this.emit("change"); return; }
      if (t && t.type === "vaultexit") { this.logAct && this.logAct("use"); const F = this.ext("vaultFrom")[fl.number] || CM.VAULT_SPEC[fl.number] || { from: 4, at: null }; if (!Object.values(fl.things).some((x) => x.type === "chest")) this.ext("vaults")[fl.vault] = true;
        this.sound && this.sound("stairs"); this.enterFloor(F.from, "rope", F.at ? F.at.split(",").map(Number) : undefined); this.say("Back up the hidden stair."); return; }
      if (t && t.type === "chest" && t.vaultPrize) { const K = V[t.vaultPrize], keeper = Object.values(fl.things).find((x) => x.type === "vaultkeeper"); if (keeper && keeper.told < K.story.length) { this.say(`${K.keeper} watches you. Perhaps you should hear the whole of it first.`); return; }
        t.items = [K.prize()]; if (K.tomes && CM.TOMES) { const ids = Object.keys(CM.TOMES); for (let i = 0; i < K.tomes; i++) t.items.push(CM.tome(ids[CM.hashSeed(`${this.seed}:vaulttome:${i}`) % ids.length])); } delete t.vaultPrize; if (this.achieve) this.achieve("vaulter"); } }
    return use0.apply(this, a); };
  const say0 = G.say; G.say = function (text, ...a) { if (this.floor && this.floor.vault && typeof text === "string" && text.startsWith("A cave under the Wood")) return; return say0.call(this, text, ...a); };   /* (a vault is no cave of the Wood's) */
  CM.ACHIEVEMENTS.vaulter = { name: "Behind the Flagstone", what: "Hear a vault's keeper out and take its prize", title: "the Keeper's Heir" };
}
