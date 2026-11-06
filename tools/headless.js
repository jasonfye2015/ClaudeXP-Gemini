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
const RULES = ["00-util.js", "10-data.js", "12-text.js", "13-lore.js", "14-items.js", "20-world.js", "21-gen1.js", "22-gen2.js", "23-town.js", "23b-wood.js", "23c-ore.js", "24-clock.js", "24b-calendar.js", "24c-light.js", "24e-calendar2.js", "24f-events.js", "25-saves.js", "26-surface.js", "27-props.js", "28-motion.js", "60-game.js", "61-explore.js", "61b-lairs.js", "61c-tower.js", "61d-magetower.js", "61f-cabin.js", "61g-cavemouth.js", "61h-fortress.js", "61i-redportal.js", "61j-pipe.js", "61k-gate.js", "61e-towerfloor.js", "62-combat.js", "63-camp.js", "64-meta.js", "64b-people.js", "64c-undercroft.js", "64d-bestiary.js", "64e-towerrun.js", "64f-towerfoes.js", "64g-towerking.js", "64h-cards.js", "64i-claudeita.js", "64j-fortress.js", "64k-claudeatro.js", "64l-claudeablo.js", "64m-claudebros.js", "64n-claudecraft.js", "64o-craftlife.js", "64q-craftcamp.js", "64r-craftvault.js", "64s-casinogames.js", "64t-casinoarcade.js", "64u-gemtray.js", "64v-mahjong.js", "64w-hexwand.js", "64x-gildedpit.js", "64y-runestack.js", "64z-cascade.js", "64za-lexicon.js", "64zb-conduit.js", "64zc-mint.js", "64zd-shelter.js", "64ze-manamine.js", "64zf-glimmer.js", "64zg-swarm.js", "64zh-hexmarch.js", "64zi-pane.js", "64zj-drift.js", "64zk-moat.js", "64zl-runestep.js", "64zm-claw.js", "64zn-pinball.js", "64zo-floorclub.js", "64zp-daily.js", "64zq-prizes.js", "64zr-arcfw.js", "64zs-wyrm.js", "64zt-crawler.js", "64zu-belfry.js", "64zv-lander.js", "64zw-rampart.js", "64zx-glimmerpop.js", "64zy-craps.js", "64zz-fair.js", "64zza-bard.js", "64zzb-patience.js", "64zzc-traps.js", "64zzd-luck.js", "64zze-fair2.js", "64zzf-arc2.js", "64zzg-holdem.js", "64zzh-bingo.js", "64zzi-floor.js", "64zzj-draws.js", "64zzk-floor2.js", "64zzl-lobby.js", "64zzm-result.js", "64zzn-joker.js", "64zzo-odds.js", "64zzp-practice.js", "64zzq-wardrobe.js", "64zzr-week.js", "64zzs-history.js", "64zzt-almanac.js", "64zzu-charms.js", "64zzv-jokerfloor.js", "64zzw-story.js", "64zzx-spoils.js", "64zzy-automanage.js", "64zzz-skilltree.js", "64zzza-links.js", "64zzzc-glyph.js", "65-village.js", "65c-crafthome.js", "66-auto.js", "67-home.js", "68-shops.js", "68b-forge.js", "69-halls.js", "69b-square.js", "69c-farm.js", "69d-cook.js", "69e-requests.js", "69f-worldmap.js", "69g-soloedge.js", "69h-renownlv.js", "69i-thread.js", "35b-croppack.js", "69j-fields.js", "69k-fieldcare.js", "69l-fieldhands.js", "69m-fieldseeds.js", "69n-fielduse.js", "69o-glyphdeep.js", "69p-portalcourt.js", "69q-waystone.js", "69r-portallooks.js", "69s-courtkeepers.js", "69t-interiors.js", "69u-compare.js", "69v-weather.js", "69w-breakables.js", "69x-pets.js", "69y-ext.js", "69z-cooking2.js", "69za-enchant.js", "69zb-stillbook.js", "69zc-furnish.js", "69zd-feats.js", "69ze-seasons.js", "69zf-again.js", "69zg-daily.js", "69zh-fireside.js", "69zi-rivals.js", "69zj-scars.js", "69zk-letters.js", "69zl-legends.js", "69zm-followranks.js", "69zn-tricks.js", "69zo-ponygear.js", "69zp-fear.js", "69zq-kennel.js", "69zr-market.js", "69zs-festgames.js", "69zt-remember.js", "69zu-works.js", "69zv-crier.js", "69zw-moods.js", "69zx-puzzles.js", "69zy-rivalband.js", "69zz-lostfound.js", "69zza-vaults.js", "69zzb-position.js", "69zzc-combos.js", "69zzd-habits.js", "69zze-surrender.js", "69zzf-phases.js", "69zzg-landmarks.js", "69zzi-levels.js", "69zzj-highground.js", "26b-buildings.js", "26c-wear.js", "26d-forestfloor.js", "26e-wooddetail.js", "26f-well.js", "26g-fences.js", "26h-lamps.js", "26i-wall.js", "26j-shaft.js", "26k-washing.js", "24d-weather.js", "69zzk-townlife.js", "69zzl-waterlife.js", "69zzm-trees.js", "64zzzd-foemarks.js", "64zzze-placelook.js", "35c-figures.js", "37-figures.js", "35d-plants.js", "37b-plants.js", "69zzn-meteors.js", "69zzo-fogs.js", "69zzp-mud.js", "69zzq-below.js", "69zzr-synergy.js", "69zzs-plants.js", "69zzt-clutter.js", "69zzu-basins.js", "69zzv-rockfalls.js", "69zzw-blooms.js", "69zzx-steam.js", "69zzy-migrate.js", "69zzz-setpieces.js", "69zzza-rooms2.js", "69zzzb-rooms3.js", "69zzzc-rooms4.js", "69zzzd-stage.js", "69zzze-stage2.js", "69zzzf-trials.js", "69zzzg-trials2.js"];

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
  CM.LOOKS = CM.LOOKS || { stone: {} };                                  // (the looks live with the art, which isn't loaded here; the one there, Stone - v44.6)
  CM.storage = storage;
  CM.store.set("settings", { skipWalk: true, season: "spring", autoLand: false });
  CM.matsOn = false; if (CM.FIELDSEEDS) CM.FIELDSEEDS.on = false;                                                      // (the buildings' needs from the other places: off for the older tests, which raise buildings for other reasons; the test of the needs turns them on)
  CM.weatherOfReal = CM.weatherOf; CM.weatherOf = () => "clear";        // (the tests' weather is clear unless a test asks for the real dice)
  CM.clockHour = () => 12;                                               // (the tests' town is always at noon)                        // (the tests and the simulator start at the shaft; the town has its own tests, and sim --town)
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
