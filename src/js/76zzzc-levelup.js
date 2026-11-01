"use strict";
// A level gained (v18.0): its own jingle and its own fireworks, wherever it happens - in a fight, at camp, coming home
// from the Mage Tower, the cave or the Fortress, at the Joker's tables, or in Claudeablo. The jingle is seven tones,
// always the same so it's known at once: a rising G-C-E-G, a turn E-G, and a high C held with a shimmer under it, played
// on a bright bell voice (and quiet under the music's level, and silent when the sounds are off). The fireworks are
// the hero's own: small rockets go up behind their card on the party bar and burst in gold and the hero's colour, the
// card's border runs with light and pulses, and "Level N!" rises off it - no window, nothing to close. Two heroes
// levelling together take turns a beat apart, under one jingle. If the party bar isn't on screen (a solo run's own
// view), the burst goes up at the top of the view instead. With reduced motion asked for, the border glows only.
{ const COLS = { Knight: "#C8D0E0", Paladin: "#FFE070", Rogue: "#60D080", Ranger: "#80E060", Cleric: "#FFFFFF", Mage: "#80A0FF", Bard: "#FF80C0", Druid: "#80E0A0", Monk: "#FFB060", Necromancer: "#B080FF", Warlock: "#C060FF", Barbarian: "#FF7050" };
  let lastJingle = 0;
  // the jingle: G4 C5 E5 G5 - E5 G5 - C6 (held), a bell on each, a soft chord under the last
  CM.levelJingle = () => { const A = CM.audio, ctx = A && A.ctx; if (!ctx || A.enabled === false) return; const now = performance.now(); if (now - lastJingle < 900) return; lastJingle = now;
    const out = ctx.createGain(); out.gain.value = 0.9; out.connect(A.master || ctx.destination); const t0 = ctx.currentTime + 0.03, hz = (m) => 440 * Math.pow(2, (m - 69) / 12);
    const bell = (m, at, len, v) => { for (const [mul, g] of [[1, v], [2, v * 0.28], [3.01, v * 0.12]]) { const o = ctx.createOscillator(), e = ctx.createGain(); o.type = mul === 1 ? "triangle" : "sine"; o.frequency.value = hz(m) * mul; e.gain.setValueAtTime(0.0001, at); e.gain.exponentialRampToValueAtTime(g, at + 0.012); e.gain.exponentialRampToValueAtTime(0.0001, at + len); o.connect(e); e.connect(out); o.start(at); o.stop(at + len + 0.05); } };
    const notes = [[67, 0, 0.3], [72, 0.1, 0.3], [76, 0.2, 0.3], [79, 0.3, 0.42], [76, 0.48, 0.25], [79, 0.58, 0.4], [84, 0.74, 1.5]];
    for (const [m, at, len] of notes) bell(m, t0 + at, len, m === 84 ? 0.16 : 0.12);
    for (const m of [60, 64, 67]) { const o = ctx.createOscillator(), e = ctx.createGain(); o.type = "sine"; o.frequency.value = hz(m); e.gain.setValueAtTime(0.0001, t0 + 0.74); e.gain.exponentialRampToValueAtTime(0.035, t0 + 0.85); e.gain.exponentialRampToValueAtTime(0.0001, t0 + 2.2); o.connect(e); e.connect(out); o.start(t0 + 0.74); o.stop(t0 + 2.3); }
    for (let k = 0; k < 10; k++) bell(96 + (k % 3) * 2, t0 + 0.8 + k * 0.06, 0.18, 0.018);   // (the shimmer)
    setTimeout(() => { try { out.disconnect(); } catch (e) { /* gone */ } }, 3200); };
  // the fireworks, over a rectangle on the screen (a hero's card, or the top of the view)
  CM.levelBurst = (rect, colour, label) => { const calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches; if (calm || !rect) return;
    const pad = 70, cv = document.createElement("canvas"), W = rect.width + pad * 2, H = rect.height + pad * 2 + 40; cv.className = "lvburst"; cv.width = W; cv.height = H; Object.assign(cv.style, { left: `${rect.left - pad}px`, top: `${rect.top - pad - 40}px`, width: `${W}px`, height: `${H}px` }); document.body.appendChild(cv);
    const p = cv.getContext("2d"), cx0 = pad, cy0 = pad + 40, sparks = [], rockets = [], cols = ["#FFE070", "#FFF6C0", colour || "#FFB040"], t0 = performance.now();
    for (let k = 0; k < 4; k++) rockets.push({ at: k * 0.18, x: cx0 + rect.width * (0.15 + 0.7 * Math.random()), y: cy0 + rect.height, ty: 18 + Math.random() * (cy0 - 10), done: false });
    // sparks running round the card's edge
    for (let k = 0; k < 40; k++) { const s = (k / 40) * 2 * (rect.width + rect.height), along = s < rect.width ? [cx0 + s, cy0] : s < rect.width + rect.height ? [cx0 + rect.width, cy0 + s - rect.width] : s < 2 * rect.width + rect.height ? [cx0 + rect.width - (s - rect.width - rect.height), cy0 + rect.height] : [cx0, cy0 + rect.height - (s - 2 * rect.width - rect.height)];
      const ang = Math.atan2(along[1] - (cy0 + rect.height / 2), along[0] - (cx0 + rect.width / 2)); sparks.push({ x: along[0], y: along[1], vx: Math.cos(ang) * 40, vy: Math.sin(ang) * 40, life: 0.7, age: -Math.random() * 0.3, c: cols[k % 3], w: 2 }); }
    const frame = (now) => { const t = (now - t0) / 1000, dt = 1 / 60; p.clearRect(0, 0, W, H); p.globalCompositeOperation = "lighter";
      for (const r of rockets) { if (t < r.at || r.done) continue; const k = Math.min(1, (t - r.at) / 0.45), y = r.y + (r.ty - r.y) * (1 - Math.pow(1 - k, 2)); p.fillStyle = "#FFF6D0"; p.beginPath(); p.arc(r.x, y, 2, 0, Math.PI * 2); p.fill(); sparks.push({ x: r.x, y: y + 3, vx: (Math.random() - 0.5) * 20, vy: 30, life: 0.3, age: 0, c: "#FFD080", w: 1.3 });
        if (k >= 1) { r.done = true; for (let i = 0; i < 34; i++) { const a = (i / 34) * Math.PI * 2, sp = 60 + Math.random() * 50; sparks.push({ x: r.x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, life: 0.9 + Math.random() * 0.4, age: 0, c: cols[i % 3], w: 2 }); } } }
      for (let i = sparks.length - 1; i >= 0; i--) { const s = sparks[i]; s.age += dt; if (s.age < 0) continue; if (s.age >= s.life) { sparks.splice(i, 1); continue; } s.vx *= 0.97; s.vy = s.vy * 0.97 + 70 * dt; s.x += s.vx * dt; s.y += s.vy * dt; const a = 1 - s.age / s.life; p.globalAlpha = a; p.fillStyle = s.c; p.beginPath(); p.arc(s.x, s.y, s.w, 0, Math.PI * 2); p.fill(); }
      p.globalCompositeOperation = "source-over"; p.globalAlpha = 1;
      if (label) { const k = Math.min(1, t / 1.8); p.globalAlpha = k < 0.75 ? 1 : 1 - (k - 0.75) / 0.25; p.font = "bold 20px Georgia"; p.textAlign = "center"; p.lineWidth = 4; p.strokeStyle = "rgba(40,20,0,0.85)"; const y = cy0 - 6 - k * 30; p.strokeText(label, cx0 + rect.width / 2, y); p.fillStyle = "#FFE070"; p.fillText(label, cx0 + rect.width / 2, y); p.globalAlpha = 1; }
      if (t < 2.4) requestAnimationFrame(frame); else cv.remove(); };
    requestAnimationFrame(frame); };
  const queue = []; let busy = false;
  const next = (ui) => { const job = queue.shift(); if (!job) { busy = false; return; } busy = true; const { hero, level } = job, i = ui.game.party.indexOf(hero), card = i >= 0 ? ui.$("#party").children[i] : null, seen = card && card.offsetParent && card.getBoundingClientRect().width > 0;
    if (seen) { card.classList.remove("lvup"); void card.offsetWidth; card.classList.add("lvup"); setTimeout(() => card.classList.remove("lvup"), 2600); CM.levelBurst(card.getBoundingClientRect(), COLS[hero.cls], `Level ${level}!`); }
    else { const v = ui.$("#view") || document.body, r = v.getBoundingClientRect(); CM.levelBurst({ left: r.left + r.width / 2 - 110, top: r.top + 24, width: 220, height: 40 }, COLS[hero.cls], `${hero.name || "Level up"} - level ${level}!`); }
    setTimeout(() => next(ui), 450); };
  CM.UI.prototype.levelFlourish = function (hero, level) { CM.levelJingle(); queue.push({ hero, level: level || hero.level }); if (!busy) next(this); };
  // a solo character's own level (Claudeablo): the jingle and a burst at the top of the view
  CM.soloLevelFlourish = (name, level) => { CM.levelJingle(); const v = document.querySelector("#view") || document.body, r = v.getBoundingClientRect(); CM.levelBurst({ left: r.left + r.width / 2 - 110, top: r.top + 24, width: 220, height: 40 }, "#FFB040", `${name} - level ${level}!`); };
}
