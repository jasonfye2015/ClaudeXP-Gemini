"use strict";
// Monster voices (v43.1, UPGRADE_PLAN_38.md): every kind has its own made voice in place of the few shared roars - the
// beasts growl, the small things shriek, the bones rattle, the serpents and the plants hiss, the walking dead moan, the
// big ones roar, the golems grind, and the people cry out like people - each kind pitched a little its own way by name,
// short and sharp when struck, long and falling at its death. The guardians are deeper and longer; the Lich King keeps
// his own. (On CM.voice, 76zzzzzzzq-voices.js; the "monsters" level.)
{ const FAM = [
    ["rattle", /Skeleton|Bone Colossus|Charnel/], ["hiss", /Eel|Wyrm|Wyvern|Spider|Weed Hag|Thorn Lotus|Mycelid/], ["grind", /Golem|Sentinel|Gargoyle|Mimic/],
    ["moan", /Zombie|Drowned|Ghoul|Hollow|Wraith|Bell-Ringer|Grave Lantern|Grave Priest/], ["shriek", /Rat|Kobold|Goblin|Imp|Wisp|Rootling|Sporeling|Marsh Light/],
    ["growl", /Wolf|Boar|Bear|Hound|Spore Beast|Deer/], ["person", /Elf|Sellsword|Wizard|Vampire|King/], ["roar", /./] ];
  const familyOf = (name) => (FAM.find(([, re]) => re.test(name)) || FAM[FAM.length - 1])[0];
  const V = (o) => CM.voice(Object.assign({ group: "monsters" }, o));
  const SAY = {
    growl: (P, die) => V(die ? { pitch: P * 1.1, to: P * 0.55, ms: 850, vowel: "o", to2: "u", vol: 0.24, growl: 0.14, growlRate: 24, breath: 0.4 } : { pitch: P, to: P * 0.85, ms: 300, vowel: "o", vol: 0.2, growl: 0.16, growlRate: 26, breath: 0.35 }),
    shriek: (P, die) => V(die ? { pitch: P * 1.2, to: P * 0.5, ms: 520, vowel: "i", to2: "e", vol: 0.15, breath: 0.2 } : { pitch: P * 1.25, to: P, ms: 150, vowel: "i", vol: 0.13, breath: 0.15 }),
    rattle: (P, die) => { const n = die ? 10 : 5; for (let i = 0; i < n; i++) V({ pitch: P * (1.4 - i * 0.03), to: P, ms: 40, vowel: "i", vol: 0.14, wave: "square", breath: 0.9, at: i * (die ? 0.06 + i * 0.008 : 0.045) }); if (die) V({ pitch: P * 0.5, to: P * 0.3, ms: 500, vowel: "o", vol: 0.08, breath: 0.5, at: 0.5 }); },
    hiss: (P, die) => V(die ? { pitch: P, to: P * 0.6, ms: 900, vowel: "i", to2: "er", vol: 0.16, breath: 1.4, hiss: true } : { pitch: P, ms: 360, vowel: "i", vol: 0.16, breath: 1.4, hiss: true }),
    moan: (P, die) => V(die ? { pitch: P * 1.1, to: P * 0.5, ms: 1200, vowel: "o", to2: "u", vol: 0.2, growl: 0.03, growlRate: 5, breath: 0.25 } : { pitch: P, to: P * 0.9, ms: 420, vowel: "uh", to2: "o", vol: 0.16, growl: 0.02, growlRate: 5 }),
    roar: (P, die) => V(die ? { pitch: P * 1.2, to: P * 0.45, ms: 1000, vowel: "a", to2: "o", vol: 0.26, growl: 0.1, growlRate: 18, breath: 0.5 } : { pitch: P * 1.05, to: P * 0.9, ms: 330, vowel: "a", vol: 0.22, growl: 0.12, growlRate: 20, breath: 0.4 }),
    grind: (P, die) => V(die ? { pitch: P, to: P * 0.4, ms: 1100, vowel: "o", vol: 0.2, wave: "square", growl: 0.3, growlRate: 9, breath: 0.6 } : { pitch: P, to: P * 0.85, ms: 380, vowel: "uh", vol: 0.16, wave: "square", growl: 0.35, growlRate: 11, breath: 0.4 }),
    person: (P, die) => V(die ? { pitch: P * 1.3, to: P * 0.6, ms: 750, vowel: "a", to2: "o", vol: 0.2, breath: 0.25 } : { pitch: P * 1.15, to: P * 0.9, ms: 180, vowel: "uh", vol: 0.16, breath: 0.3 }) };
  const BASE = { growl: 95, shriek: 520, rattle: 900, hiss: 300, moan: 120, roar: 82, grind: 55, person: 150 };
  CM.monsterVoice = (kind, what) => { const name = String(kind || ""), G = Object.values(CM.GUARDIANS || {}).find((x) => x.name === name), fam = G ? (G.undead ? "moan" : G.body === "beast" ? "growl" : "roar") : familyOf((CM.monsterKind(name) || {}).name || name);
    const P = BASE[fam] * (0.85 + ((CM.hashSeed(`mvoice:${name}`) >>> 0) % 1000) / 1000 * 0.35) * (G ? 0.72 : 1); SAY[fam](P, what === "die"); return fam; };
  CM.monsterFamily = (name) => familyOf(name);
  const prep = () => { const A = CM.audio; if (!A || !A.bark || A.voicedBark) return false; const b0 = A.bark;
    A.bark = function (kind, what) { if (!this.ctx || !this.enabled) return; if (kind === (CM.BOSS && CM.BOSS.name) || CM.VOICE_LEVELS.monsters <= 0 || !CM.voice) return b0.call(this, kind, what);
      const now = performance.now(); if (now - (this.lastBark || 0) < 180) return; this.lastBark = now; CM.monsterVoice(kind, what); };
    A.voicedBark = true; return true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (prep()) clearInterval(t); }, 300);
}
