"use strict";
// Ghost whispers (v43.3, UPGRADE_PLAN_38.md): when the dead speak - a ghost on the floor, a vault's keeper telling its
// story - their words come with a whisper under them: breath shaped into syllables with no voice behind it, drifting
// from one side to the other and echoing a little, over a thin cold tone. As long as the words are, near enough. On
// CM.voice (its hiss), the "ghosts" level.
{ const VOW = ["a", "e", "i", "o", "u", "uh", "er"];
  CM.whisper = (text, seed) => { if (!CM.voice || CM.VOICE_LEVELS.ghosts <= 0) return; const words = String(text || "").split(/\s+/).filter(Boolean).length, n = Math.max(4, Math.min(26, Math.round(words * 0.7))), r = new CM.Random(CM.hashSeed(`whisper:${seed || text}`));
    let at = 0; for (let i = 0; i < n; i++) { const pan = Math.sin(i * 0.5 + r.next()) * 0.7, ms = 90 + r.next() * 140, v = VOW[Math.floor(r.next() * VOW.length)];
      CM.voice({ group: "ghosts", pitch: 200, ms, vowel: v, to2: VOW[Math.floor(r.next() * VOW.length)], vol: 0.1, breath: 1.6, hiss: true, pan, at });
      CM.voice({ group: "ghosts", pitch: 200, ms: ms * 1.2, vowel: v, vol: 0.045, breath: 1.6, hiss: true, pan: -pan, at: at + 0.22 });   /* (its echo) */
      at += ms / 1000 + 0.03 + (r.next() < 0.15 ? 0.25 : 0); }
    CM.voice({ group: "ghosts", pitch: 660, to: 600, ms: Math.min(6000, at * 1000 + 600), vowel: "u", vol: 0.018, wave: "sine", growl: 0.01, growlRate: 4 }); };
  const G = CM.Game.prototype;
  if (G.talkGhost) { const tg0 = G.talkGhost; G.talkGhost = function (thing, k, ...a) { const said = [], had = Object.prototype.hasOwnProperty.call(this, "say"), prev = this.say;
      this.say = function (t, ...b) { said.push(String(t)); return prev.call(this, t, ...b); };
      try { return tg0.call(this, thing, k, ...a); } finally { if (had) this.say = prev; else delete this.say; if (said.length) CM.whisper(said.join(" "), `${k}:${said[0].slice(0, 30)}`); } }; }
  const say0 = G.say; G.say = function (text, ...a) { const out = say0.call(this, text, ...a); if (typeof text === "string" && CM.VAULTS && this.floor && this.floor.vault) { const K = CM.VAULTS[this.floor.vault]; if (K && text.startsWith(`${K.keeper}:`)) CM.whisper(text, text.slice(0, 40)); } return out; };
}
