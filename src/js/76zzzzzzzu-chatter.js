"use strict";
// Hireling chatter (v43.4, UPGRADE_PLAN_38.md): those who come along make themselves heard now and then on the walk -
// the porter grunts under the pack, the torchbearer coughs in the smoke, a dog (the hired one or the party's own hound)
// barks or whuffs, the wizard mutters to himself, the cut-loose adventurer hums, and the pony on the lead snorts.
// One sound every half a minute or so, from behind the party; quiet in a fight. On CM.voice, the "followers" level.
{ const V = (o) => CM.voice && CM.voice(Object.assign({ group: "followers" }, o));
  const SOUND = {
    porter: () => { V({ pitch: 95, to: 80, ms: 260, vowel: "uh", vol: 0.12, breath: 0.6, pan: -0.15 }); V({ pitch: 90, to: 70, ms: 380, vowel: "o", vol: 0.06, breath: 0.9, hiss: true, at: 0.3, pan: -0.15 }); },
    torchbearer: () => { for (let i = 0; i < 3; i++) V({ pitch: 140, to: 120, ms: 110, vowel: "a", vol: 0.1 - i * 0.02, breath: 1.4, hiss: i > 0, at: i * 0.2, pan: 0.15 }); },
    dog: () => { const two = Math.random() < 0.6; V({ pitch: 330, to: 260, ms: 120, vowel: "o", to2: "uh", vol: 0.14, growl: 0.06, growlRate: 40, breath: 0.4 }); if (two) V({ pitch: 340, to: 250, ms: 130, vowel: "a", to2: "uh", vol: 0.13, growl: 0.06, growlRate: 40, breath: 0.4, at: 0.22 }); },
    whuff: () => V({ pitch: 200, ms: 260, vowel: "u", vol: 0.08, breath: 1.2, hiss: true }),
    wizard: () => { let at = 0; for (let i = 0; i < 6; i++) { V({ pitch: 125 + Math.random() * 20, to: 115, ms: 120 + Math.random() * 80, vowel: ["uh", "er", "o", "e"][i % 4], vol: 0.06, at, pan: 0.2 }); at += 0.18; } },
    adventurer: () => { const notes = [196, 220, 247, 220, 196]; notes.forEach((f, i) => V({ pitch: f, to: f, ms: 260, vowel: "u", vol: 0.05, wave: "triangle", at: i * 0.28, pan: -0.2 })); },
    pony: () => { V({ pitch: 160, to: 120, ms: 420, vowel: "o", vol: 0.09, breath: 1.6, hiss: true }); V({ pitch: 420, to: 300, ms: 300, vowel: "e", vol: 0.05, growl: 0.08, growlRate: 14, at: 0.1 }); } };
  CM.FOLLOWER_SOUNDS = SOUND;
  let next = 0;
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); if (!game || game.mode !== "explore" || !game.floor || !CM.voice || CM.VOICE_LEVELS.followers <= 0) return;
    if (!next) { next = now + 15000 + Math.random() * 20000; return; } if (now < next) return; next = now + 22000 + Math.random() * 30000;
    const who = [], f = game.follower; if (f && !f.away && SOUND[f.id]) who.push(f.id);
    if (game.petName && game.petName("dog")) who.push(Math.random() < 0.7 ? "dog" : "whuff"); if (game.petName && game.petName("pony") && !(CM.isDeep && CM.isDeep(game.floor.number))) who.push("pony");
    if (who.length) SOUND[who[Math.floor(Math.random() * who.length)]](); };
}
