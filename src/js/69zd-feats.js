"use strict";
// The hall of feats (v33.0, UPGRADE_PLAN_28.md): twenty feats more, kept with the achievements (and so titles too),
// each looked for when something has happened - a floor reached, a fight won, a thing gained - and earned the first
// time it is true. The hall itself, a room of plaques at the Mage Tower's foot, is the window's (76zzzzzx-feats.js).
//   CM.FEATS2[id] -> test(game);  game.checkFeats()
{ const T = (g) => g.tally || {}, U = (g, k) => ((T(g).used || {})[k] || 0);
  const add = (id, name, what, title, test) => { CM.ACHIEVEMENTS[id] = { name, what, title }; CM.FEATS2[id] = test; };
  CM.FEATS2 = {};
  add("gourmand", "Gourmand", "Eat ten dishes in one expedition", "the Well-fed", (g) => U(g, "dish") >= 10);
  add("feaster", "Host of Feasts", "Lay three feasts in one expedition", "the Host", (g) => (T(g).feasts || 0) >= 3);
  add("shardhoard", "Shard-hoard", "Hold twenty relic shards at once", "the Hoarder of Shards", (g) => g.shards && g.shards() >= 20);
  add("pagefinder", "Page-finder", "Find five still pages in one expedition", "the Bookish", (g) => (T(g).pages || 0) >= 5);
  add("chests50", "Lid-lifter", "Open fifty chests in one expedition", "the Lid-lifter", (g) => (T(g).chests || 0) >= 50);
  add("kills300", "Three Hundred", "Slay three hundred in one expedition", "the Relentless", (g) => (T(g).kills || 0) >= 300);
  add("walker", "The Long Walk", "Walk ten thousand steps in one expedition", "the Wanderer", (g) => (T(g).steps || 0) >= 10000);
  add("threeguard", "Three Keepers", "Slay three guardians in one expedition", "the Keeper-slayer", (g) => new Set(T(g).guardians || []).size >= 3);
  add("sixguard", "Six Keepers", "Slay six guardians in one expedition", "the Warden-breaker", (g) => new Set(T(g).guardians || []).size >= 6);
  add("allguard", "Every Keeper", "Slay all nine guardians in one expedition", "the Unkept", (g) => new Set(T(g).guardians || []).size >= 9);
  add("champ10", "Champion's Bane", "Slay ten champions in one expedition", "the Champion's Bane", (g) => (T(g).champions || 0) >= 10);
  add("rich10k", "Treasury", "Hold 10,000 gold at once", "the Treasurer", (g) => (g.gold || 0) >= 10000);
  add("floor20", "Of the Palace", "Reach floor 70", "of the Palace", (g) => g.deepestReached && g.deepestReached() >= CM.LAST_FLOOR);
  add("floor40", "Of the Foundry", "Reach floor 90", "of the Foundry", (g) => g.deepestReached && g.deepestReached() >= CM.realOf(40));
  add("enchant3", "Thrice Inscribed", "Have three words put on things at the Tower in one expedition", "the Thrice-inscribed", (g) => (T(g).enchanted || 0) >= 3);
  add("stilled5", "The Still Runs", "Brew five things at the fields' still in one expedition", "the Stiller", (g) => (T(g).stilled || 0) >= 5);
  add("trophywall", "A Wall of Trophies", "Mount four trophies on the house's wall", "the Trophied", (g) => g.mounted && g.mounted().length >= 4);
  add("outfitted", "Well Outfitted", "Have every hero wear something rare or better at once", "the Outfitted", (g) => (g.party || []).length === 4 && g.party.every((h) => CM.equipped(h).some((it) => ["rare", "unique", "relic"].includes(CM.rarityOf(it)))));
  add("level20", "Twentieth Level", "Raise a hero to level twenty", "the Seasoned", (g) => (g.party || []).some((h) => h.level >= 20));
  add("allten", "A Party of Veterans", "Have every hero past level ten at once", "the Veteran", (g) => (g.party || []).length === 4 && g.party.every((h) => h.level > 10));
  const G = CM.Game.prototype;
  G.checkFeats = function () { if (!this.achievements || this.replaying || this.film) return; for (const [id, test] of Object.entries(CM.FEATS2)) { if (this.achievements[id]) continue; let ok = false; try { ok = test(this); } catch (e) { ok = false; } if (ok) this.achieve(id); } };
  const em0 = G.emit; G.emit = function (ev, ...a) { const out = em0.call(this, ev, ...a); if (ev === "floor" || ev === "mode" || ev === "levelup") this.checkFeats(); return out; };
  const wf0 = G.wonFight; G.wonFight = function (...a) { const out = wf0.apply(this, a); this.checkFeats(); return out; };
}
