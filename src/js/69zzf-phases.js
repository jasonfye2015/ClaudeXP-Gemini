"use strict";
// Boss phases (v38.4, UPGRADE_PLAN_33.md): every guardian and the Lich King changes halfway through the fight - a new
// form of words and a tactic of its own - and the window turns the music and shows a card (76zzzzzzv-phases.js). The
// three shallow guardians keep the second forms they had (at a third, 62-combat.js); the rest, at half their health:
// the Drowned Queen calls her drowned court; the Mycelial Mind bursts with spores and puts the front row to sleep; the
// Crystal Tyrant grows a carapace (much harder to hurt); the Foundry Master stokes himself white-hot (his blows half again);
// the Bone Patriarch pulls himself together (a quarter of his health back, once); the Root of the World puts out new
// shoots (two more rootlings) and hardens; the Bell-Founder's Boy rings the bell (the party's heart shaken); the Lich
// King's crown blazes - two skeletons up and his blows harder.
//   CM.BOSS_PHASES[id]; foe.phase2
{ const P = CM.BOSS_PHASES = {
    queen: { text: "The Drowned Queen lifts her arms, and the water at her feet stands up into shapes: her court has come.", summon: ["Drowned", 2] },
    mind: { text: "The Mycelial Mind splits open in a cloud of pale spores. The front row's eyes grow heavy.", sleepFront: true },
    tyrant: { text: "The Crystal Tyrant cracks - and closes over itself in a new skin of crystal, thicker than the last.", df: 6 },
    master: { text: "The Foundry Master tears open his own furnace door. He burns white now, and the air shakes round him.", atk: 1.5 },
    patriarch: { text: "The Bone Patriarch pulls his scattered bones back to him with a sound like a cart of firewood falling.", heal: 0.25 },
    root: { text: "The Root of the World puts out new shoots from the stone, and its old wood hardens.", summon: ["Rootling", 2], df: 3 },
    bell: { text: "The Boy rings the bell. It isn't a sound so much as a weight, and everyone feels it in their chest.", morale: -15 },
    lich: { text: "The Lich King's crown blazes cold, and the dead stand up around the throne at his word.", skeletons: 2, atk: 1.25 },
  };
  const G = CM.Game.prototype;
  G.bossPhase = function (m) { const id = m.boss ? "lich" : m.guardian, Ph = P[id]; if (!Ph || m.phase2 || m.echo) return false; m.phase2 = true;
    this.say(Ph.text); if (Ph.atk) m.atk = Math.round(m.atk * Ph.atk); if (Ph.df) m.df = (m.df || 0) + Ph.df; if (Ph.heal) m.hp = Math.min(m.max, m.hp + Math.round(m.max * Ph.heal)); if (Ph.morale && this.cheer) this.cheer(Ph.morale, "the bell");
    if (Ph.summon) { const K = CM.monsterKind(Ph.summon[0]); if (K) for (let i = 0; i < Ph.summon[1]; i++) { const s = this.tune(CM.makeMonster(K, Math.max(3, this.floor ? this.floor.number : 5), new CM.Random(CM.hashSeed(`${this.seed}:phase:${id}:${i}`)))); s.summoned = true; this.foes.push(s); } }
    if (Ph.skeletons && this.summonSkeletons) this.summonSkeletons(Ph.skeletons);
    if (Ph.sleepFront) for (const h of this.alive().filter((x) => x.row === "front")) if (this.afflict) this.afflict(h, "sleep", "the spores");
    this.tally.phases = (this.tally.phases || 0) + 1; this.emit("fx", { kind: "bossphase", foe: m, text: Ph.text }); return true; };
  const ab0 = G.afterBlows; G.afterBlows = function (...a) { const out = ab0.apply(this, a); if (this.mode !== "combat") return out;
    for (const m of this.foes || []) { if (m.hp <= 0 || m.phase2) continue; const id = m.boss ? "lich" : m.guardian; if (!P[id]) { if (m.form2 && !m.phaseShown && CM.GUARDIANS[m.guardian]) { m.phaseShown = true; this.emit("fx", { kind: "bossphase", foe: m, text: CM.GUARDIANS[m.guardian].form2.text }); } continue; }
      if (m.hp <= m.max / 2) this.bossPhase(m); }
    return out; };
}
