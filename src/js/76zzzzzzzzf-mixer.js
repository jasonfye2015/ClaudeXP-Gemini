"use strict";
// A mixer (v46.0, UPGRADE_PLAN_41.md): Settings has a slider for each kind of sound under the sound's own volume and the
// music's - Voices (the heroes, the monsters, the town, the ghosts, those who come along: CM.VOICE_LEVELS), Ambience
// (the dungeon's air, the weather, the distant sounds, the fire: one channel, CM.ambienceOut) and Interface (the
// windows' own sounds, CM.uiLevel). Kept with the other settings.
{ CM.MIX_DEFAULTS = { voicesVolume: 1, ambienceVolume: 1, uiVolume: 0.7 };
  let amb = null;
  CM.ambienceOut = () => { const A = CM.audio; if (!A || !A.ctx || !A.master) return A && A.master; if (!amb || amb.ctx !== A.ctx) { const g = A.ctx.createGain(); g.connect(A.master); amb = { ctx: A.ctx, g }; CM.applyMix(); } return amb.g; };
  CM.uiLevel = () => { const s = CM.game && CM.game.settings; return s && s.uiVolume !== undefined ? s.uiVolume : CM.MIX_DEFAULTS.uiVolume; };
  CM.applyMix = () => { const s = (CM.game && CM.game.settings) || {}, v = s.voicesVolume !== undefined ? s.voicesVolume : 1, a = s.ambienceVolume !== undefined ? s.ambienceVolume : 1;
    if (CM.VOICE_LEVELS) for (const k of Object.keys(CM.VOICE_LEVELS)) CM.VOICE_LEVELS[k] = v;
    const A = CM.audio; if (A && A.ctx) { if (amb && amb.ctx === A.ctx) amb.g.gain.setTargetAtTime(a, A.ctx.currentTime, 0.1); if (A.ambientGain) { A.ambientScale = a; A.ambientGain.gain.setTargetAtTime((A.ambientBase === undefined ? 0.5 : A.ambientBase) * a, A.ctx.currentTime, 0.2); } } };
  // the cave's own air: its level times the ambience's
  { const A = CM.audio; if (A && A._startAmbient) { const sa0 = A._startAmbient; A._startAmbient = function (...a) { const out = sa0.apply(this, a); if (this.ambientGain) { this.ambientBase = this.ambientGain.gain.value; this.ambientGain.gain.value = this.ambientBase * (this.ambientScale === undefined ? 1 : this.ambientScale); } return out; }; } }
  const ROWS = [["voicesVolume", "Voices (the heroes, the monsters, the town, the ghosts)"], ["ambienceVolume", "Ambience (the air, the weather, distant sounds, fire)"], ["uiVolume", "Interface (pages, coins, clicks)"]];
  const wire = () => { const ui = CM.ui, g = CM.game; if (!ui || !g || !ui.$) return false; const anchor = ui.$("#set-music-volume"); if (!anchor) return false; const row0 = anchor.closest(".row"); if (!row0 || ui.$("#set-voicesVolume")) return true;
    const vl = ui.$('label[for="set-volume"]'); if (vl) vl.textContent = "Sound volume (all but the music)";
    let after = row0; for (const [key, label] of ROWS) { const r = document.createElement("div"); r.className = "row"; r.innerHTML = `<label for="set-${key}">${label}</label><input type="range" id="set-${key}" min="0" max="100">`; after.insertAdjacentElement("afterend", r); after = r;
      const inp = r.querySelector("input"); inp.value = Math.round((g.settings[key] !== undefined ? g.settings[key] : CM.MIX_DEFAULTS[key]) * 100);
      inp.addEventListener("input", () => { g.settings[key] = inp.value / 100; CM.applyMix(); if (g.saveSettings) g.saveSettings(); if (key === "uiVolume" && CM.uiSound) CM.uiSound("tick"); }); }
    CM.applyMix(); return true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (wire()) clearInterval(t); }, 300);
}
