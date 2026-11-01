"use strict";
// The floor's spoils (v17.9): time at the tables now counts as time in the dungeon. Every play (worth two tickets), and every ticket won by playing,
// teaches the whole party (experience to every hero standing, at a rate set by the party's highest level) and, every
// fifty tickets, turns up a piece of gear to wear - a weapon, armour, a shield, a helm, a ring, an amulet, boots or a
// cloak - made for the depth of the party's highest level, now and then enchanted. Tickets handed over rather than
// played for (the Almanac, the visit card, the Joker's bank, the books, the quests, the story, the daily wheel...)
// don't count, nor does practice. And the floor keeps a dungeon's pace whatever the stakes: the spoils come from at
// most 25 tickets a real minute, banked up to six minutes' worth so a big win still pays in full.
{ const SP = CM.SPOILS = { play: 2, per: 50, rate: 25, cap: 150, enchant: 0.15, xp: (L) => 0.4 + 0.35 * L,
    GEAR: ["weapon", "weapon", "armor", "armor", "shield", "helm", "ring", "amulet", "boots", "cloak"],
    SKIP: ["joker", "almanac", "visits", "books", "story", "week", "quests", "vip", "prizewheel", "loyalty", "achievements"] };
  const P = CM.Game.prototype, tk0 = P.tkAdd, st0 = P.cgStake;
  Object.assign(P, {
    spStore() { const F = this.cgStore(); F.spoils = F.spoils || { tk: 0, n: 0, xp: 0, items: 0, bucket: SP.cap, at: 0 }; return F.spoils; },
    spLevel() { return Math.max(1, ...(this.party || []).map((h) => h.level || 1)); },
    // tickets played for: the party's share of experience, and the gear that turns up
    spEarn(k, now) { const S = this.spStore(); now = now === undefined ? Date.now() : now;
      if (S.at) S.bucket = Math.min(SP.cap, S.bucket + ((now - S.at) / 60000) * SP.rate); S.at = now; const use = Math.min(k, Math.floor(S.bucket)); if (use <= 0) return null; S.bucket -= use;
      const L = this.spLevel(), xp = Math.max(1, Math.round(use * SP.xp(L))), heroes = (this.alive ? this.alive() : this.party || []), out = { xp, items: [] };
      for (const h of heroes) h.xp = (h.xp || 0) + xp; S.xp += xp; if (heroes.length && this.checkLevels) this.checkLevels();
      S.tk += use; while (S.tk >= SP.per) { S.tk -= SP.per; S.n += 1; const R = new CM.Random(CM.hashSeed(`${this.seed}:spoils:${S.n}`)), depth = Math.max(1, Math.min(CM.BOTTOM || 50, L));
        let it = CM.makeItem(depth, R, R.pick(SP.GEAR)); if (it && CM.affix && R.chance(SP.enchant)) it = CM.affix(it, depth + 2, R) || it;
        if (it) { this.gain([it], "casino"); out.items.push(it); S.items += 1; } }
      const res = this.cgRes = this.cgRes || { gold: 0, tickets: 0, cards: [] }; res.xp = (res.xp || 0) + xp; res.items = (res.items || []).concat(out.items);
      this.saveCasino && this.saveCasino(); return out; },
    cgStake(game, bet) { const why = st0.call(this, game, bet); if (!why && !this.cgPractice && !SP.SKIP.includes(game) && this.party && this.party.length) this.spEarn(SP.play); return why; },   // (a play counts too: the luck tables pay few tickets)
    tkAdd(n, why) { const k = tk0.call(this, n, why); if (k > 0 && !this.cgPractice && !SP.SKIP.includes(why) && this.party && this.party.length) this.spEarn(k); return k; },
  });
}
