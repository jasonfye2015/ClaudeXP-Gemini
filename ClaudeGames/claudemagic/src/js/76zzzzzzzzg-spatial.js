"use strict";
// Spatial sound for headphones (v46.1, UPGRADE_PLAN_41.md): with "Headphones" ticked in Settings, the sounds that come
// from a place are placed around the head instead of only left and right - a monster heard behind is behind, the
// distant sounds come from all round and from above (drips, chimes) and below (the Root's groan, grinding stone).
// The Web Audio's own head model (an HRTF panner); off, the sounds pan as before.
{ CM.spatialOn = () => Boolean(CM.game && CM.game.settings && CM.game.settings.headphones);
  // a panner at an angle round the head (0 ahead, positive to the right), a height (-1 below .. 1 above) and a distance
  CM.hrtf = (ctx, az, el = 0, dist = 2) => { const p = ctx.createPanner(); p.panningModel = "HRTF"; p.distanceModel = "inverse"; p.refDistance = 1; p.rolloffFactor = 0.6;
    const x = Math.sin(az) * Math.cos(el * 1.2) * dist, y = Math.sin(el * 1.2) * dist, z = -Math.cos(az) * Math.cos(el * 1.2) * dist;
    if (p.positionX) { p.positionX.value = x; p.positionY.value = y; p.positionZ.value = z; } else p.setPosition(x, y, z); return p; };
  const prep = () => { const A = CM.audio; if (!A || !A.play3d || A.spatialWrapped) return false; const p0 = A.play3d;
    A.play3d = function (name, volume, pan, muffle, where) { if (!CM.spatialOn() || !where || where.ang === undefined || !this.ctx || !this.enabled || !this.buffers[name]) return p0.call(this, name, volume, pan, muffle);
      const ctx = this.ctx, src = ctx.createBufferSource(), g = ctx.createGain(); src.buffer = this.buffers[name]; g.gain.value = CM.clamp(volume, 0, 1) * 1.3; let node = src;
      if (where.wall) { const f = ctx.createBiquadFilter(); f.type = "lowpass"; f.frequency.value = 520; src.connect(f); node = f; }
      const P = CM.hrtf(ctx, where.ang, 0, 1 + (where.d || 2) * 0.4); node.connect(g); g.connect(P); P.connect(this.master); const R = this.room && this.room(); if (R) P.connect(R.send); src.start(); };
    A.spatialWrapped = true; return true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (prep()) clearInterval(t); }, 300);
  // the setting
  const wire = () => { const ui = CM.ui, g = CM.game; if (!ui || !g || !ui.$) return false; const anchor = ui.$("#set-uiVolume"); if (!anchor) return false; if (ui.$("#set-headphones")) return true;
    const r = document.createElement("div"); r.className = "row"; r.innerHTML = `<label for="set-headphones">Headphones - sounds from behind, above and below</label><input type="checkbox" id="set-headphones">`; anchor.closest(".row").insertAdjacentElement("afterend", r);
    const inp = r.querySelector("input"); inp.checked = Boolean(g.settings.headphones); inp.addEventListener("input", () => { g.settings.headphones = inp.checked; if (g.saveSettings) g.saveSettings(); }); return true; };
  const t2 = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (wire()) clearInterval(t2); }, 300);
}
