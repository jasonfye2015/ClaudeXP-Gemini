"use strict";
// Gear score and auto-manage (v18.1).
// - Gear score: a number for each thing worn - its power (weighted by its slot: the weapon most, then the armour, the
//   off hand, the helm, then boots, cloak, rings, amulets and trinkets), its worth, and its rarity (fine, rare,
//   relic, unique more; cursed much less; a weapon a hero isn't at home with counts for less in their hands) - and so
//   for each hero (all they wear) and the party (all four).
// - Auto-manage (the pack's "Auto-manage: Y/N", kept in the settings): whenever gear comes into the pack - loot, a
//   chest, the casino's spoils - and when it's switched on, every known piece is put on the first hero, left to right,
//   who can wear it and is better for it by the gear score; what they took off goes back to the pack, and may suit the
//   next hero along. Unknown things are left alone (they might be cursed: identify them first), cursed ones too, and
//   nothing changes hands in a fight.
{ const GS = CM.GEARSCORE = { W: { weapon: 1.2, armor: 1.0, offhand: 0.8, helm: 0.6, boots: 0.5, cloak: 0.5, ring: 0.5, amulet: 0.5, trinket: 0.5 },
    RARITY: { common: 0, magic: 10, fine: 20, rare: 30, set: 30, relic: 45, unique: 60, cursed: -80 }, GEAR: ["weapon", "armor", "shield", "helm", "ring", "amulet", "trinket", "boots", "cloak"] };
  GS.slotOf = (it) => it.slot || (it.kind === "shield" ? "offhand" : it.kind);
  // a thing's score, in a hero's hands if one is given
  CM.itemScore = (it, h) => { if (!it || (it.props && it.props.fists)) return 0; const w = GS.W[GS.slotOf(it)] || 0.5, r = GS.RARITY[CM.rarityOf(it)] || 0;
    let s = (it.power || 0) * 10 * w + Math.sqrt(Math.max(0, it.value || 0)) * 2 + r; if (h && it.kind === "weapon" && CM.atHome && !CM.atHome(h, it)) s *= 0.7; return Math.max(0, Math.round(s)); };
  CM.gearScore = (h) => CM.SLOTS.reduce((a, slot) => a + CM.itemScore(h[slot], h), 0);
  CM.partyGearScore = (party) => (party || []).reduce((a, h) => a + CM.gearScore(h), 0);
  const P = CM.Game.prototype, gain0 = P.gain;
  Object.assign(P, {
    amOn() { return !!(this.settings && this.settings.autoManage); },
    amSet(on) { this.settings.autoManage = !!on; this.saveSettings && this.saveSettings(); return on ? this.amRun() : []; },
    // what this hero would gain by wearing that (taking off what's there, and a shield for a two-handed weapon)
    amGain(h, it) { if (!GS.GEAR.includes(it.kind) || it.unknown || (it.props && it.props.cursed) || CM.cantWear(h, it)) return 0; const slot = GS.slotOf(it), old = h[slot];
      if (old && old.props && old.props.cursed) return 0; let g = CM.itemScore(it, h) - CM.itemScore(old, h); if (slot === "weapon" && it.props && it.props.twohanded && h.offhand) g -= CM.itemScore(h.offhand, h); return g; },
    // everything known in the pack, to the first hero (left to right) it betters
    amRun() { if (this.replaying || this.mode === "combat" || !this.party || !this.bag) return []; const moved = []; let guard = 0, changed = true;
      while (changed && guard++ < 60) { changed = false;
        for (let row = 0; row < this.bag.length && !changed; row++) { const it = this.bag[row]; if (!GS.GEAR.includes(it.kind)) continue;
          for (const h of this.party) { if (this.amGain(h, it) <= 0) continue; const was = this.say; this.say = () => {}; let why; try { why = this.equip(h, row); } finally { this.say = was; }   // (logged as any equip: a film plays it back as it was done)
            if (!why) { moved.push({ hero: h.name, item: it.name }); changed = true; } break; } } }
      if (moved.length) { this.say(`Auto-manage: ${moved.map((m) => `${m.hero} puts on ${m.item}`).join("; ")}.`); this.emit && this.emit("change"); }
      return moved; },
    gain(items, how) { const out = gain0.call(this, items, how); if (this.amOn() && out && out.some((it) => GS.GEAR.includes(it.kind))) this.amRun(); return out; },
  });
}
