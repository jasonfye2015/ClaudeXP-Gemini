"use strict";
// Followers seen (v29.5, UPGRADE_PLAN_24.md): who comes along walks behind the party, where a look back finds them -
// the porter under a great pack, the torchbearer with the torch held high (its light with him), the hedge-wizard, the
// adventurer cut loose, the farm's dog Grip, and the party's own hound at heel and pony on the lead (the pony only
// above ground). They keep to the party's trail, a step or two behind, and close up as it walks.
{ const S = 256, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const shadow = (p, w) => { p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, 246, w, 10, 0, 0, Math.PI * 2); p.fill(); };
  const person = (p, coat, skin) => { const R = (x, y, w, h, c) => { p.fillStyle = c; p.fillRect(x, y, w, h); };
    R(100, 184, 20, 58, "#3A2E24"); R(136, 184, 20, 58, "#3A2E24"); R(96, 238, 28, 8, "#1E1610"); R(132, 238, 28, 8, "#1E1610");
    R(88, 108, 80, 84, coat); R(68, 112, 20, 60, coat); R(168, 112, 20, 60, coat); R(68, 168, 20, 12, skin); R(168, 168, 20, 12, skin);
    p.fillStyle = skin; p.beginPath(); p.arc(128, 84, 26, 0, Math.PI * 2); p.fill(); R(116, 80, 6, 6, "#2A1A10"); R(134, 80, 6, 6, "#2A1A10"); };
  const PAINT = {
    "npc:porter": (p) => { shadow(p, 60); p.fillStyle = "#8A6A40"; p.fillRect(62, 34, 132, 120); p.strokeStyle = "#5A4020"; p.lineWidth = 6; p.strokeRect(62, 34, 132, 120); p.fillStyle = "#A0784A"; p.fillRect(80, 14, 96, 26); p.fillStyle = "#6A5030"; p.fillRect(150, 20, 40, 18);
      person(p, "#6A5A3A", "#D8A880"); p.fillStyle = "#4A3018"; p.fillRect(98, 108, 10, 84); p.fillRect(148, 108, 10, 84); },
    "npc:torchbearer": (p) => { shadow(p, 50); person(p, "#4A3A5A", "#A87850"); p.fillStyle = "#6A4A28"; p.fillRect(176, 60, 10, 120);
      const g = p.createRadialGradient(181, 50, 2, 181, 50, 34); g.addColorStop(0, "#FFF2A0"); g.addColorStop(0.4, "#FFA030"); g.addColorStop(1, "rgba(220,70,20,0)"); p.fillStyle = g; p.beginPath(); p.moveTo(160, 64); p.quadraticCurveTo(168, 20, 181, 8); p.quadraticCurveTo(196, 22, 202, 64); p.closePath(); p.fill(); },
    "pet:dog": (p) => { shadow(p, 60); p.fillStyle = "#7A5A3A"; p.beginPath(); p.ellipse(128, 176, 62, 30, 0, 0, Math.PI * 2); p.fill(); for (const x of [84, 104, 150, 170]) p.fillRect(x, 190, 12, 52);
      p.beginPath(); p.ellipse(190, 140, 28, 24, -0.3, 0, Math.PI * 2); p.fill(); p.beginPath(); p.ellipse(214, 150, 16, 10, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#5A3A22"; p.beginPath(); p.moveTo(176, 118); p.lineTo(188, 98); p.lineTo(194, 124); p.fill();
      p.fillStyle = "#1A1008"; p.fillRect(196, 134, 6, 6); p.fillRect(222, 146, 6, 5); p.strokeStyle = "#7A5A3A"; p.lineWidth = 10; p.beginPath(); p.moveTo(68, 166); p.quadraticCurveTo(46, 140, 54, 120); p.stroke(); },
    "pet:pony": (p) => { shadow(p, 80); p.fillStyle = "#8A6A4A"; p.beginPath(); p.ellipse(120, 150, 74, 40, 0, 0, Math.PI * 2); p.fill(); for (const x of [64, 88, 148, 172]) p.fillRect(x, 170, 16, 74);
      p.save(); p.translate(186, 112); p.rotate(-0.6); p.fillRect(-14, -50, 30, 70); p.restore(); p.beginPath(); p.ellipse(216, 70, 26, 16, -0.4, 0, Math.PI * 2); p.fill(); p.fillStyle = "#4A3020"; for (let i = 0; i < 6; i++) p.fillRect(170 + i * 6, 52 + i * 8, 10, 16);
      p.fillStyle = "#1A1008"; p.fillRect(220, 62, 6, 6); p.fillStyle = "#6A4A2A"; p.fillRect(40, 130, 10, 60); p.fillStyle = "#A0302A"; p.fillRect(96, 116, 50, 22); },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  const LAYER = { porter: "npc:porter", torchbearer: "npc:torchbearer", dog: "pet:dog", wizard: "npc:hermit", adventurer: "npc:adventurer" };
  // the party's trail on this floor: where it was, a step and two behind
  const trail = []; let trailFloor = null;
  const behind = (fl, k) => { const T = trailFloor === fl ? trail : []; return T.length > k ? T[T.length - 1 - k] : null; };
  const smooth = new Map();
  const at = (id, target, now) => { let S0 = smooth.get(id); if (!S0 || Math.hypot(S0.x - target[0], S0.y - target[1]) > 3) { S0 = { x: target[0], y: target[1] }; smooth.set(id, S0); }
    const k = Math.min(1, 0.12 * (CM.renderer && CM.renderer.lastDt ? CM.renderer.lastDt * 60 : 1)); S0.x += (target[0] - S0.x) * k; S0.y += (target[1] - S0.y) * k; return [S0.x, S0.y]; };
  CM.followersSeen = (game, fl) => { const out = [], f = game.follower; if (f && !f.away && LAYER[f.id]) out.push([f.id, LAYER[f.id], 1, f.id === "torchbearer"]);
    const dog = game.petName && game.petName("dog"); if (dog) out.push(["hound", "pet:dog", f ? 2 : 1, false]);
    const pony = game.petName && game.petName("pony"); if (pony && fl && (fl.number === 0 || fl.number === -1)) out.push(["pony", "pet:pony", out.length + 1, false]);
    return out; };
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (!fl || !CM.renderer || game.mode === "title") return out;
      for (const [id, layer, back] of CM.followersSeen(game, fl)) { const spot = behind(fl, back); if (!spot || CM.renderer.index[layer] === undefined) continue;
        const R = CM.DIRS[(fl.facing + 1) % 4], side = id === "hound" ? 0.34 : id === "pony" ? -0.36 : 0;
        const [x, y] = at(id, [spot[0] + R[0] * side, spot[1] + R[1] * side], now), cx = Math.floor(x + 0.5), cy = Math.floor(y + 0.5);
        if (cx === fl.pos[0] && cy === fl.pos[1]) continue;
        const moving = Math.hypot(x - spot[0] - R[0] * side, y - spot[1] - R[1] * side) > 0.05;
        out.push({ x: cx, y: cy, dx: x - cx, dz: y - cy, layer, w: id === "pony" ? 0.85 : id === "hound" ? 0.5 : 0.62, h: id === "pony" ? 0.78 : id === "hound" ? 0.42 : 0.82, lift: moving ? Math.abs(Math.sin(now / 150)) * 0.02 : 0,
          bend: CM.monsterBend ? CM.monsterBend(moving ? "walk" : "idle", now, cx * 2 + cy, null) : null }); }
      return out; }; }
  // the torchbearer's torch lights about him
  { const xl0 = CM.extraLights; CM.extraLights = (game, fl, out, renderer) => { if (xl0) xl0(game, fl, out, renderer); const f = game.follower; if (!fl || !f || f.away || f.id !== "torchbearer") return; const s = smooth.get("torchbearer"); if (!s) return;
      const R = CM.DIRS[(fl.facing + 1) % 4]; out.push({ x: s.x + 0.5 - R[0] * 0.3, y: 1.05, z: s.y + 0.5 - R[1] * 0.3, reach: 2.6, colour: [1.0, 0.62, 0.3], flicker: true, d: Math.abs(s.x - fl.pos[0]) + Math.abs(s.y - fl.pos[1]) }); }; }
  // the trail: the party's last squares on this floor (on arriving, the squares behind it, so the followers come in at its back)
  { const em0 = CM.Game.prototype.emit; CM.Game.prototype.emit = function (ev, ...a) { const g = this;
      if (ev === "moved") { if (trailFloor !== g.floor) { trail.length = 0; trailFloor = g.floor; smooth.clear(); } const L = trail[trail.length - 1]; if (!L || L[0] !== a[0] || L[1] !== a[1]) trail.push([a[0], a[1]]); if (trail.length > 6) trail.shift(); }
      else if (ev === "floor" && g.floor) { trail.length = 0; trailFloor = g.floor; smooth.clear(); const [x, y] = g.floor.pos, fd = CM.DIRS[(g.floor.facing + 2) % 4];
        const back = []; for (let k = 1; k <= 3; k++) { const bx = x + fd[0] * k, by = y + fd[1] * k; if (!CM.passable(g.floor, bx, by)) break; back.unshift([bx, by]); } trail.push(...back, [x, y]); }
      return em0.call(this, ev, ...a); }; }
}
