"use strict";
// Hit reactions (v39.1, UPGRADE_PLAN_34.md): a struck monster flinches away from the blow, and a weak spot staggers it
// further back and tips it; what the blow knocks off it flies by what it is - sparks from plate, chips of shell and crystal,
// splinters of bone, tufts of hide, a spray of blood from flesh, cold motes from the bodiless. (The renderer's sprites for
// that monster carry the hit's flash; they are pushed back by it.)
{ const S = 128, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const PAINT = {
    "hit:chip": (p) => { p.fillStyle = "#C8D0D8"; p.beginPath(); p.moveTo(30, 20); p.lineTo(100, 50); p.lineTo(70, 110); p.lineTo(20, 80); p.closePath(); p.fill(); p.fillStyle = "rgba(255,255,255,0.7)"; p.fillRect(40, 40, 20, 10); },
    "hit:bone": (p) => { p.fillStyle = "#EDE3C8"; p.fillRect(20, 54, 88, 20); for (const x of [22, 106]) { p.beginPath(); p.arc(x, 56, 12, 0, Math.PI * 2); p.arc(x, 74, 12, 0, Math.PI * 2); p.fill(); } },
    "hit:tuft": (p) => { p.strokeStyle = "#6A5038"; p.lineWidth = 6; p.lineCap = "round"; for (let i = 0; i < 7; i++) { p.beginPath(); p.moveTo(64, 100); p.quadraticCurveTo(40 + i * 8, 60, 30 + i * 12, 20); p.stroke(); } },
    "hit:blood": (p) => { p.fillStyle = "#8A1010"; p.beginPath(); p.arc(64, 64, 34, 0, Math.PI * 2); p.fill(); p.fillStyle = "#B02020"; p.beginPath(); p.arc(54, 54, 14, 0, Math.PI * 2); p.fill(); },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [n, f] of Object.entries(PAINT)) { const c = cv(); f(c.getContext("2d")); set.index[n] = set.layers.length; set.layers.push(c); } return set; }; }
  const DEBRIS = { plate: ["fx:spark", 12, 0.05, 2.2], shell: ["hit:chip", 7, 0.07, 1.6], bone: ["hit:bone", 5, 0.09, 1.4], hide: ["hit:tuft", 6, 0.07, 1.0], flesh: ["hit:blood", 8, 0.05, 1.2], none: ["fx:frost", 8, 0.06, 0.8] };
  let crit = 0;
  const bind = () => { const g = CM.game, K = CM.fxKit; if (!g || !g.on || !K) return false;
    g.on("fx", (fx) => { if (!fx || fx.kind !== "hit" || !fx.foe || fx.spell || CM.reducedMotion) return; if (fx.crit) crit = performance.now(); const at = K.atFoe && K.atFoe(fx.foe, 0.5); if (!at) return;
      const D = DEBRIS[CM.hideOf(fx.foe)] || DEBRIS.flesh, big = fx.crit ? 1.6 : 1; setTimeout(() => K.fxs.burst({ at, layer: D[0], n: Math.round(D[1] * big), size: D[2], speed: D[3] * big, up: 1.4, gravity: 5, ms: 600, glow: D[0] === "fx:spark" ? 1 : 0 }), 60); }); return true; };
  const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (bind()) clearInterval(t); }, 300);
  // the flinch: a struck monster's sprite pushed back from the eye, more on a weak spot, and tipped
  const prep = (r) => { const ss0 = r.setSprites; r.setSprites = function (list) { if (!CM.reducedMotion) { const fwd = [Math.sin(this.yaw), -Math.cos(this.yaw)], hard = performance.now() - crit < 400 ? 2.2 : 1;
        for (const s of list) if (s.flash > 0.05 && typeof s.layer === "string" && s.layer.startsWith("monster:")) { const k = s.flash * 0.09 * hard; s.dx = (s.dx || 0) + fwd[0] * k; s.dz = (s.dz || 0) + fwd[1] * k; if (hard > 1 && !s.bend) s.tilt = (s.tilt || 0) - 0.12 * s.flash; } }
      return ss0.call(this, list); }; r.flinchWrapped = true; };
  const t2 = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { if (CM.renderer && !CM.renderer.flinchWrapped) { prep(CM.renderer); clearInterval(t2); } }, 200);
}
