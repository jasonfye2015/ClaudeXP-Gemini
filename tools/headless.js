"use strict";
// The game's rules in Node, with no screen: 00-util, 10-data, 20-world, 25-saves and 60-64 loaded into a fresh
// context with a window and a localStorage of its own. The tests and the simulator drive CM.Game straight.
//
//   const { load } = require("./tools/headless");
//   const CM = load();                 // a fresh game world; CM.storage is its localStorage (a Map behind it)
//   const game = new CM.Game();
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const SRC = path.join(__dirname, "..", "src", "js");
const RULES = ["00-util.js", "10-data.js", "12-text.js", "13-lore.js", "14-items.js", "20-world.js", "21-gen1.js", "22-gen2.js", "25-saves.js", "60-game.js", "61-explore.js", "62-combat.js", "63-camp.js", "64-meta.js", "65-village.js", "66-auto.js"];

// a localStorage: quota is how many characters it holds before it throws, the way a full browser does
function makeStorage(quota = Infinity) {
  const map = new Map();
  const size = () => { let n = 0; for (const [k, v] of map) n += k.length + v.length; return n; };
  return {
    map,
    getItem(k) { return map.has(k) ? map.get(k) : null; },
    setItem(k, v) {
      v = String(v);
      const was = map.has(k) ? map.get(k).length : 0;
      if (size() - was + k.length + v.length > quota) { const e = new Error("QuotaExceededError"); e.name = "QuotaExceededError"; throw e; }
      map.set(k, v);
    },
    removeItem(k) { map.delete(k); },
    key(i) { return [...map.keys()][i] === undefined ? null : [...map.keys()][i]; },
    get length() { return map.size; },
    clear() { map.clear(); },
  };
}

// the sources, read once: a simulator run stays one version of the game even if the files change under it
const sources = {};
const source = (f) => (sources[f] = sources[f] || fs.readFileSync(path.join(SRC, f), "utf8"));

function load(opts = {}) {
  const storage = opts.storage || makeStorage(opts.quota);
  const ctx = { console, performance, localStorage: storage, btoa, atob, setTimeout, clearTimeout, Math, Date, JSON,
    TextEncoder, TextDecoder, Blob, Response, CompressionStream, DecompressionStream };   // (the link codec: a save deflated into a #fragment)
  ctx.window = ctx;
  vm.createContext(ctx);
  for (const f of RULES) vm.runInContext(source(f), ctx, { filename: f });
  const CM = ctx.CM;
  CM.LOOKS = CM.LOOKS || { drawn: {} };                                 // (the themes live with the art, which isn't loaded here)
  CM.storage = storage;
  return CM;
}

// the classic four with the dice taken out of them: the same party every time, so two runs of a seed can be compared
function fixedParty(CM, seed = "party") {
  const rnd = new CM.Random(CM.hashSeed(seed));
  return CM.CLASSIC.map((cls) => ({ cls, name: CM.randomName(rnd), stats: CM.rollStats(cls, rnd), row: CM.CLASSES[cls].row }));
}

// a fight played out by the game's own Auto hand (62-combat.js), turn after turn
function autoplayFight(CM, game, limit = 400) {
  let guard = 0;
  while (game.mode === "combat" && game.combat && guard++ < limit) {
    if (!game.combat.waiting) { game.advance(); continue; }
    game.combat.auto = false;                                            // (the bot never hands the reins back)
    if (!game.autoTurn()) break;
  }
}
module.exports = { load, makeStorage, autoplayFight, fixedParty, RULES };
