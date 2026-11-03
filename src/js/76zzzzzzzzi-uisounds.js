"use strict";
// The interface's own sounds (v46.3, UPGRADE_PLAN_41.md): a soft click under every button; a page turned when a book-like
// window opens or one of its pages is chosen (the Journal, the codex, the plates, the lore, the library); a soft thump
// for the other windows; the map unrolling (and rolled up again); and coins clinking when gold changes hands in a
// window - a purchase, a sale. At the Interface slider's level (CM.uiLevel, 76zzzzzzzzf-mixer.js).
{ const live = () => { const A = CM.audio; return A && A.ctx && A.enabled && A.master; };
  let noise = null; const N = (c) => { if (!noise) { const n = c.sampleRate, b = c.createBuffer(1, n, n), d = b.getChannelData(0); for (let i = 0; i < n; i++) d[i] = Math.random() * 2 - 1; noise = b; } return noise; };
  const out = (c) => { const g = c.createGain(); g.gain.value = CM.uiLevel ? CM.uiLevel() : 0.7; g.connect(CM.audio.master); return g; };
  const hiss = (c, d, at, dur, vol, hz, to, q = 1, type = "bandpass") => { const s = c.createBufferSource(), f = c.createBiquadFilter(), g = c.createGain(); s.buffer = N(c); f.type = type; f.frequency.setValueAtTime(hz, at); if (to) f.frequency.exponentialRampToValueAtTime(to, at + dur); f.Q.value = q;
    g.gain.setValueAtTime(0.0001, at); g.gain.exponentialRampToValueAtTime(vol, at + Math.min(0.03, dur / 3)); g.gain.exponentialRampToValueAtTime(0.0001, at + dur); s.connect(f); f.connect(g); g.connect(d); s.start(at, Math.random() * 0.5); s.stop(at + dur + 0.05); };
  const ping = (c, d, at, hz, dur, vol) => { const o = c.createOscillator(), g = c.createGain(); o.frequency.value = hz; g.gain.setValueAtTime(vol, at); g.gain.exponentialRampToValueAtTime(0.0001, at + dur); o.connect(g); g.connect(d); o.start(at); o.stop(at + dur + 0.05); };
  const SOUND = {
    tick: (c, d, at) => { hiss(c, d, at, 0.03, 0.12, 2400, null, 4); ping(c, d, at, 1200, 0.04, 0.02); },
    page: (c, d, at) => { hiss(c, d, at, 0.22, 0.12, 1800, 4200, 0.8); hiss(c, d, at + 0.12, 0.12, 0.06, 3000, 1500, 0.8); },
    open: (c, d, at) => { hiss(c, d, at, 0.12, 0.14, 300, null, 1, "lowpass"); ping(c, d, at, 180, 0.12, 0.05); },
    close: (c, d, at) => { hiss(c, d, at, 0.08, 0.1, 400, null, 1, "lowpass"); },
    unroll: (c, d, at) => { hiss(c, d, at, 0.45, 0.13, 900, 3800, 0.7); for (let i = 0; i < 5; i++) hiss(c, d, at + 0.05 + i * 0.07, 0.03, 0.05, 2500 + i * 300, null, 5); },
    rollup: (c, d, at) => hiss(c, d, at, 0.3, 0.1, 3600, 900, 0.7),
    coins: (c, d, at) => { for (let i = 0; i < 4; i++) { const t = at + i * 0.05 + Math.random() * 0.03; ping(c, d, t, 2800 + Math.random() * 1600, 0.12, 0.05); ping(c, d, t, 5200 + Math.random() * 1500, 0.06, 0.02); } } };
  CM.UI_SOUNDS = SOUND;
  CM.uiSound = (kind) => { if (!live() || !SOUND[kind] || (CM.uiLevel && CM.uiLevel() <= 0)) return; try { const c = CM.audio.ctx; SOUND[kind](c, out(c), c.currentTime + 0.005); } catch (e) { /* (quiet) */ } };
  const BOOKS = /journal|lore|library|chronicler|codex|plates|musicroom|calendar/;
  const U = CM.UI.prototype;
  { const od0 = U.openDialog; U.openDialog = function (sel, ...a) { const was = this.$(sel) && this.$(sel).classList.contains("on"); this.uiQuiet = true; let out0; try { out0 = od0.call(this, sel, ...a); } finally { this.uiQuiet = false; } if (!was && sel !== "#bigmap") CM.uiSound(BOOKS.test(sel) ? "page" : "open"); return out0; }; }
  { const cd0 = U.closeDialogs; U.closeDialogs = function (...a) { const any = this.root && this.root.querySelector && this.root.querySelector(".dialog.on"), map = this.$ && this.$("#bigmap") && this.$("#bigmap").classList.contains("on"), out0 = cd0.apply(this, a); if (this.uiQuiet) return out0; if (map) CM.uiSound("rollup"); else if (any) CM.uiSound("close"); return out0; }; }
  if (U.toggleBigMap) { const tb0 = U.toggleBigMap; U.toggleBigMap = function (...a) { const opening = !(this.$("#bigmap") && this.$("#bigmap").classList.contains("on")), out0 = tb0.apply(this, a); if (opening) CM.uiSound("unroll"); return out0; }; }
  // a soft click under every button; a page for the Journal's own page buttons
  let lastClick = 0;
  document.addEventListener("click", (e) => { const b = e.target && e.target.closest && e.target.closest("button"); if (!b) return; const now = performance.now(); if (now - lastClick < 40) return; lastClick = now; CM.uiSound(b.closest(".boards") ? "page" : "tick"); }, true);
  // coins: gold changing hands while a window is open
  let gold = null; setInterval(() => { const g = CM.game, ui = CM.ui; if (!g || !ui || !ui.root) return; const now = g.gold; if (gold !== null && now !== gold && ui.root.querySelector(".dialog.on")) CM.uiSound("coins"); gold = now; }, 150);
}
