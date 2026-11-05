"use strict";
// Meteors and the ore - the window's side (v75.0, UPGRADE_PLAN_61.md part 5): the rules (69zzn-meteors.js) are
// stepped as the clock goes; in the minutes before a strike the birds go up all at once (the night goes quiet); the
// strike itself is a streak of fire down the sky to its square, a flash, a crack and a rumble, the ground shaken, a
// burst of dust, embers and stones, and an orange glow in the crater that fades over the minutes. Below ground it is
// a shock through the stone and a dust-fall. The crater goes into the floor's mesh (26-surface.js) and the ore
// chunk lies in it as a thing until the party steps onto it.
{ const P = 128, pic = (draw) => { const c = document.createElement("canvas"); c.width = c.height = P; draw(c.getContext("2d")); return c; };
  const PICS = {
    "life:meteorite": (p) => { p.fillStyle = "rgba(0,0,0,0.35)"; p.beginPath(); p.ellipse(P / 2, P * 0.86, P * 0.42, P * 0.09, 0, 0, Math.PI * 2); p.fill();   // its shadow
      p.fillStyle = "#1E1C20"; p.beginPath(); p.moveTo(P * 0.14, P * 0.8); p.lineTo(P * 0.22, P * 0.46); p.lineTo(P * 0.42, P * 0.3); p.lineTo(P * 0.66, P * 0.26); p.lineTo(P * 0.86, P * 0.5); p.lineTo(P * 0.88, P * 0.8); p.closePath(); p.fill();
      p.fillStyle = "#34323A"; p.beginPath(); p.moveTo(P * 0.22, P * 0.46); p.lineTo(P * 0.42, P * 0.3); p.lineTo(P * 0.56, P * 0.5); p.lineTo(P * 0.36, P * 0.62); p.closePath(); p.fill();   // a lit facet
      p.fillStyle = "#2A282E"; p.beginPath(); p.moveTo(P * 0.56, P * 0.5); p.lineTo(P * 0.66, P * 0.26); p.lineTo(P * 0.86, P * 0.5); p.lineTo(P * 0.72, P * 0.6); p.closePath(); p.fill();
      p.strokeStyle = "#D8E8FF"; p.lineWidth = 3; p.beginPath(); p.moveTo(P * 0.58, P * 0.52); p.lineTo(P * 0.7, P * 0.62); p.lineTo(P * 0.66, P * 0.74); p.stroke();   // the bright grain where it broke
      p.fillStyle = "#F0F6FF"; for (const [x, y] of [[0.3, 0.52], [0.48, 0.42], [0.76, 0.56], [0.62, 0.7]]) { p.beginPath(); p.arc(P * x, P * y, 2.2, 0, Math.PI * 2); p.fill(); } },
    "life:meteor": (p) => { const g = p.createRadialGradient(P / 2, P / 2, 2, P / 2, P / 2, P / 2); g.addColorStop(0, "rgba(255,255,245,1)"); g.addColorStop(0.3, "rgba(255,225,150,0.95)"); g.addColorStop(0.6, "rgba(255,140,50,0.5)"); g.addColorStop(1, "rgba(200,60,20,0)"); p.fillStyle = g; p.fillRect(0, 0, P, P); } };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const name of Object.keys(PICS)) if (set.index[name] === undefined) { set.index[name] = set.layers.length; set.layers.push(pic(PICS[name])); } return set; }; }
  { const s0 = CM.art.isSurfaceLayer; CM.art.isSurfaceLayer = (name) => PICS[name] !== undefined || s0(name); }
  // the ore chunk on its square, warm for a while
  CM.thingSprites = Object.assign(CM.thingSprites || {}, { meteorite: (t, x, y) => { const g = CM.game, m = g ? CM.clockOf(g) - (t.at || 0) : 999; return [{ x, y, layer: "life:meteorite", w: 0.5, h: 0.42, glow: Math.max(0, 0.7 * (1 - m / 12)) }]; } });
  // the sounds: a whistle down the sky, and the crack and rumble
  const whistle = (secs) => { const A = CM.audio; if (!A || !A.ctx || !A.enabled || !A.master) return; try { const ctx = A.ctx, o = ctx.createOscillator(), g = ctx.createGain(), t0 = ctx.currentTime; o.type = "sine"; o.frequency.setValueAtTime(1700, t0); o.frequency.exponentialRampToValueAtTime(220, t0 + secs);
      g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(0.09, t0 + secs * 0.3); g.gain.exponentialRampToValueAtTime(0.0001, t0 + secs); o.connect(g); g.connect(A.master); o.start(t0); o.stop(t0 + secs + 0.05); } catch (er) { /* quiet */ } };
  const rumble = (far) => { const A = CM.audio; if (!A || !A.ctx || !A.enabled || !A.master) return; try { const ctx = A.ctx, rate = ctx.sampleRate, secs = far ? 4.5 : 3.8, n = Math.floor(rate * secs), b = ctx.createBuffer(1, n, rate), d = b.getChannelData(0); let lp = 0, lp2 = 0, s = 777;
      for (let i = 0; i < n; i++) { s = (s * 1103515245 + 12345) & 0x7fffffff; const w = s / 0x7fffffff * 2 - 1, t = i / rate; lp += (w - lp) * (far ? 0.02 : 0.05); lp2 += (lp - lp2) * 0.06;
        const crack = far ? 0 : Math.exp(-t * 18) * w * 0.5, env = Math.min(1, t / (far ? 0.4 : 0.03)) * Math.exp(-t * (far ? 0.7 : 1.0)) * (1 + 0.5 * Math.sin(t * 5.3) * Math.sin(t * 1.9)); d[i] = (lp2 * 10 + crack) * env; }
      const src = ctx.createBufferSource(), g = ctx.createGain(); src.buffer = b; g.gain.value = far ? 0.45 : 0.75; src.connect(g); g.connect(A.master); src.start(); } catch (er) { /* quiet */ } };
  // the strike, seen: the streak down the sky, then the burst (the parts start past the air's fade-in, age 0.4, or they are faint)
  let fall = null, flash = 0, felt = 0, warnedFor = 0, lastClock = null;
  const dirWord = (fl, x, y) => { const dx = x + 0.5 - fl.pos[0] - 0.5, dy = y + 0.5 - fl.pos[1] - 0.5; return Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? "east" : "west") : (dy > 0 ? "south" : "north"); };
  const parts = () => (CM.air && CM.air.parts) || null, r = Math.random;
  const burst = (x, z) => { const A = parts(); if (!A) return;
    for (let i = 0; i < 44; i++) { const a = r() * Math.PI * 2, sp = 1.2 + r() * 2.2; A.push({ kind: "smoke", age: 0.4, seed: r() * 10, sway: 0.6 + r(), swayAmp: 0.1, windy: 0.4, vx: Math.cos(a) * sp, vy: 0.5 + r() * 1.2, vz: Math.sin(a) * sp, life: 2.5 + r() * 2, size: 0.3 + r() * 0.25, grow: 0.12, glow: 0, alpha: 0.8, x: x + Math.cos(a) * 0.2, z: z + Math.sin(a) * 0.2, y: 0.2 + r() * 0.4, top: 8, far: true, layer: "air:smoke", drag: 1.6 }); }
    for (let i = 0; i < 28; i++) { const a = r() * Math.PI * 2, sp = 2 + r() * 4; A.push({ kind: "debris", age: 0.4, seed: r() * 10, sway: 0, swayAmp: 0, windy: 0, vx: Math.cos(a) * sp, vy: 2.5 + r() * 4, vz: Math.sin(a) * sp, life: 1.6 + r(), size: 0.07 + r() * 0.07, glow: 0, alpha: 1, x, z, y: 0.3, top: 12, far: true, layer: "air:debris", drag: 0.8, grav: 7 }); }
    for (let i = 0; i < 40; i++) { const a = r() * Math.PI * 2, sp = 0.6 + r() * 2.5; A.push({ kind: "ember", age: 0.4, seed: r() * 10, sway: 1 + r(), swayAmp: 0.2, windy: 0.3, vx: Math.cos(a) * sp, vy: 1.5 + r() * 3, vz: Math.sin(a) * sp, life: 1.2 + r() * 1.8, size: 0.05 + r() * 0.05, glow: 2, alpha: 1, x, z, y: 0.3, top: 10, far: true, layer: "air:ember", drag: 1.2, grav: 2.5 }); } };
  const birdsUp = (eye, night) => { const A = parts(); if (!A || night) return; for (let i = 0; i < 14; i++) { const a = r() * Math.PI * 2, d = 10 + r() * 22, s = 5 + r() * 3, x = eye[0] + Math.cos(a) * d, z = eye[2] + Math.sin(a) * d; A.push({ kind: "bird", age: 0, seed: r() * 10, sway: 0.6 + r(), swayAmp: 0, windy: 0, vx: Math.cos(a) * s, vy: 1.2 + r() * 1.5, vz: Math.sin(a) * s, life: 14, size: 0.7, far: true, top: 60, flap: true, glow: 0, alpha: 1, x, z, y: 3 + r() * 3, layer: "air:bird" }); } };
  const onStrike = (game, s) => { const r0 = CM.renderer, fl = game.floor; if (!r0 || !fl) return;
    if (s.felt || fl.number !== s.floor) { felt = 1; setTimeout(() => { r0.shake(0.7); rumble(true); }, 400); game.say("A shock comes down through the stone, and dust from the roof. Something fell, above - heavy, and from a long way up."); return; }
    const to = [s.x + 0.5, s.y + 0.5], a = Math.atan2(to[1] - fl.pos[1] - 0.5, to[0] - fl.pos[0] - 0.5) + (r() - 0.5) * 1.2; fall = { t: 0, dur: 1.15, to, from: [to[0] + Math.cos(a) * 16, 24, to[1] + Math.sin(a) * 16], s, head: null }; whistle(fall.dur); };
  const impact = (game, F) => { const r0 = CM.renderer, fl = game.floor, [x, z] = F.to; fall = null; if (F.head) F.head.life = 0; flash = 1; if (r0) r0.shake(1); rumble(false); burst(x, z);
    const d = Math.abs(F.s.x - fl.pos[0]) + Math.abs(F.s.y - fl.pos[1]); game.say(`A star falls! It strikes the ground to the ${dirWord(fl, F.s.x, F.s.y)}, ${d} paces off, with a crack that shakes the teeth${F.s.fires ? " - and the trees beside it are alight" : ""}.`); };
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r0, dt, now) => { if (bf0) bf0(game, r0, dt, now); if (!game || !game.floor || !game.ext || game.mode === "title") { lastClock = null; return; } const fl = game.floor, t = CM.clockOf(game);
    if (!game._meteorHooked) { game._meteorHooked = true; game.on("meteor", (s) => onStrike(game, s)); }
    if (lastClock !== null && t > lastClock && t - lastClock < 600) CM.meteorStep(game, t - lastClock); lastClock = t;
    if (fl.meteorVersion !== (game.meteorVersion || 0) || fl.craters === undefined) { fl.craters = CM.cratersOf(game, fl); fl.meteorVersion = game.meteorVersion || 0; }
    const E = game.ext("meteors"), w = CM.meteorWarning(game);   // the warning: the birds go up (the night goes quiet)
    if (w > 0 && E.next !== warnedFor && (fl.number === 0 || fl.number === -1)) { warnedFor = E.next; const night = CM.isNight(game); birdsUp(r0.eye || [fl.pos[0] + 0.5, 1, fl.pos[1] + 0.5], night); game.say(night ? "The night goes quiet all at once: not a cricket, not an owl. The dogs in the town begin to howl." : "The birds go up from every tree at once, crying, and wheel away."); }
    if (fall) { const F = fall, A = parts(); F.t += dt; const k = Math.min(1, F.t / F.dur), e = k * k, x = F.from[0] + (F.to[0] - F.from[0]) * e, y = F.from[1] * (1 - e), z = F.from[2] + (F.to[1] - F.from[2]) * e;
      if (A) { if (!F.head) { F.head = { kind: "meteor", age: 1, seed: 0, sway: 0, swayAmp: 0, windy: 0, vx: 0, vy: 0, vz: 0, life: 99, size: 2.0, glow: 2, alpha: 1, x, y, z, far: true, top: 80, layer: "life:meteor" }; A.push(F.head); } F.head.x = x; F.head.y = y; F.head.z = z;
        for (let i = 0; i < 10; i++) A.push({ kind: "meteor", age: 0.4, seed: r() * 10, sway: 0, swayAmp: 0, windy: 0, vx: (r() - 0.5) * 0.4, vy: 0.1, vz: (r() - 0.5) * 0.4, life: 1.0 + r() * 0.8, size: 0.7 + r() * 0.9 * (1 - k * 0.5), glow: 2, alpha: 0.9, x: x + (r() - 0.5) * 0.3, y: y + (r() - 0.5) * 0.3, z: z + (r() - 0.5) * 0.3, far: true, top: 80, layer: "life:meteor" }); }
      if (k >= 1) impact(game, F); }
    if (flash > 0) { if (r0.skyx) r0.skyx.flash = Math.max(r0.skyx.flash || 0, flash * flash); flash = Math.max(0, flash - dt * 2.2); }
    if (felt > 0) { r0.roomFlash = Math.max(r0.roomFlash || 0, felt * 0.25); felt = Math.max(0, felt - dt * 1.5); } };
  // the burst's parts fly out and fall (a step after the air's own: a drag and a gravity the air's kinds don't have)
  { const st0 = CM.Air.prototype.step; CM.Air.prototype.step = function (dt, env) { const out = st0.call(this, dt, env); for (const p of this.parts) { if (p.drag) { const k = Math.max(0, 1 - p.drag * dt); p.vx *= k; p.vz *= k; } if (p.grav) p.vy -= p.grav * dt; } return out; }; }
  // the crater's glow in the minutes after
  { const xl0 = CM.extraLights; CM.extraLights = (game, fl, out, renderer) => { if (xl0) xl0(game, fl, out, renderer); if (!fl || !(fl.number === 0 || fl.number === -1) || !game.ext || !renderer || !renderer.eye) return; const t = CM.clockOf(game), E = game.ext("meteors");
      for (const s of E.strikes || []) { if (s.floor !== fl.number) continue; const m = t - s.at; if (m < 0 || m > 12) continue; const k = 1 - m / 12; out.push({ x: s.x + 0.5, y: 0.4, z: s.y + 0.5, reach: 1.5 + 1.7 * k, colour: [0.75 * k + 0.25 * (1 - k), 0.32 * k, 0.07 * k], flicker: true, d: Math.abs(s.x - fl.pos[0]) + Math.abs(s.y - fl.pos[1]) }); } }; }
}
