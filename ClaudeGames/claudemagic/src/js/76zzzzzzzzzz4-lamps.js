"use strict";
// Lamp posts, painted (v56.3, UPGRADE_PLAN_51.md): the lantern's glass (warm when lit, dark when not - its glow is set
// per lamp in 80-main.js) and the soft pool of light a lit lamp throws on the ground beneath it.
{ const P = 64;
  const PAINT = {
    lampglass: (p) => { const g = p.createLinearGradient(0, 0, 0, P); g.addColorStop(0, "#FFE7A8"); g.addColorStop(0.6, "#F5B85A"); g.addColorStop(1, "#D88A30"); p.fillStyle = g; p.fillRect(4, 2, P - 8, P - 4);
      p.fillStyle = "rgba(60,40,20,0.85)"; p.fillRect(P / 2 - 2, 2, 4, P - 4); p.fillRect(4, P / 2 - 2, P - 8, 4); p.fillStyle = "rgba(255,255,240,0.6)"; p.fillRect(10, 8, 6, 14); },
    lamppool: (p) => { const g = p.createRadialGradient(P / 2, P / 2, 0, P / 2, P / 2, P / 2); g.addColorStop(0, "rgba(255,200,120,0.55)"); g.addColorStop(0.45, "rgba(255,180,100,0.25)"); g.addColorStop(1, "rgba(255,170,90,0)"); p.fillStyle = g; p.fillRect(0, 0, P, P); },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [k, f] of Object.entries(PAINT)) { if (set.index[k] !== undefined) continue; const c = document.createElement("canvas"); c.width = c.height = P; f(c.getContext("2d")); set.index[k] = set.layers.length; set.layers.push(c); } return set; }; }
}
