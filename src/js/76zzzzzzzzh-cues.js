"use strict";
// Sound cues (v46.2, UPGRADE_PLAN_41.md): for those who play by ear, two settings - "Sound cues" gives three tones of
// their own: a falling warning when a trap the party knows of is close ahead, a rising chime when a chest, a key or a
// find comes within a few steps, and a slow pulse when a hero falls below a quarter of their health; "Say the cues
// aloud" speaks them too ("Trap ahead", "A chest nearby", "Mira is badly hurt"), in the computer's own voice.
{ const on = () => Boolean(CM.game && CM.game.settings && CM.game.settings.soundCues), speak = () => Boolean(CM.game && CM.game.settings && CM.game.settings.speakCues);
  const tone = (notes, wave = "triangle", vol = 0.12) => { const A = CM.audio; if (!A || !A.ctx || !A.enabled || !A.master) return; const c = A.ctx; let at = c.currentTime + 0.02;
    for (const [hz, d] of notes) { const o = c.createOscillator(), g = c.createGain(); o.type = wave; o.frequency.value = hz; g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(vol, at + 0.01); g.gain.exponentialRampToValueAtTime(0.0001, at + d); o.connect(g); g.connect(A.master); o.start(at); o.stop(at + d + 0.05); at += d * 0.8; } };
  const say = (text) => { if (!speak() || typeof speechSynthesis === "undefined") return; try { const u = new SpeechSynthesisUtterance(text); u.rate = 1.1; u.volume = 0.9; speechSynthesis.speak(u); } catch (e) { /* (no voice) */ } };
  const CUES = { trap: [[880, 0.12], [660, 0.12], [440, 0.22]], find: [[660, 0.09], [880, 0.09], [1320, 0.2]], hurt: [[110, 0.3], [110, 0.3]] };
  CM.cue = (kind, text) => { if (on()) tone(CUES[kind], kind === "hurt" ? "sine" : "triangle", kind === "hurt" ? 0.25 : 0.12); if (text) say(text); };
  const heard = new Set(), wasLow = new WeakMap(); let flAt = null;
  const FIND = { chest: "A chest", key: "A key", item: "Something on the floor", strongbox: "A strongbox", gem: "A gem", relic: "A relic", vaultstair: "A hidden stair" };
  setInterval(() => { const g = CM.game, fl = g && g.floor; if (!g || !fl || g.mode === "title" || (!on() && !speak())) return; if (flAt !== fl) { flAt = fl; heard.clear(); }
    const [px, py] = fl.pos, F = CM.DIRS[fl.facing] || [0, -1];
    if (g.mode === "explore") {
      for (let i = 1; i <= 3; i++) { const k = `${px + F[0] * i},${py + F[1] * i}`, f = (fl.features || {})[k]; if (!CM.isOpen || !CM.isOpen(fl, px + F[0] * i, py + F[1] * i)) break; if (f && f.known && ["trap", "pit", "trapdoor", "plate"].includes(f.type) && !heard.has(`t${k}`)) { heard.add(`t${k}`); CM.cue("trap", "Trap ahead"); break; } }
      for (const [k, t] of Object.entries(fl.things)) { if (!FIND[t.type] || heard.has(`f${k}`)) continue; const [x, y] = k.split(",").map(Number); if (Math.abs(x - px) + Math.abs(y - py) > 3) continue; heard.add(`f${k}`); CM.cue("find", `${FIND[t.type]} nearby`); break; } }
    for (const h of g.party || []) { if (!h) continue; const low = h.hp > 0 && h.max > 0 && h.hp / h.max < 0.25; if (low && !wasLow.get(h)) CM.cue("hurt", `${h.name} is badly hurt`); wasLow.set(h, low); } }, 400);
  const wire = () => { const ui = CM.ui, g = CM.game; if (!ui || !g || !ui.$) return false; const anchor = ui.$("#set-headphones"); if (!anchor) return false; if (ui.$("#set-soundCues")) return true; let after = anchor.closest(".row");
    for (const [key, label] of [["soundCues", "Sound cues - a tone for a trap ahead, a find nearby, a hero badly hurt"], ["speakCues", "Say the cues aloud"]]) { const r = document.createElement("div"); r.className = "row"; r.innerHTML = `<label for="set-${key}">${label}</label><input type="checkbox" id="set-${key}">`; after.insertAdjacentElement("afterend", r); after = r;
      const inp = r.querySelector("input"); inp.checked = Boolean(g.settings[key]); inp.addEventListener("input", () => { g.settings[key] = inp.checked; if (g.saveSettings) g.saveSettings(); if (inp.checked) CM.cue("find", key === "speakCues" ? "Cues will be spoken" : null); }); }
    return true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (wire()) clearInterval(t); }, 300);
}
