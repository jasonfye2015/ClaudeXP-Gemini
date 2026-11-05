"use strict";
// Market days - the window's side (v36.0): each trader drawn at their stall in the Square (a striped awning over them),
// and the side panel says who is in the Square today. Rules: 69zr-market.js.
{ const S = 256, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const COLS = { hrodna: ["#8A2A20", "#E8D8B0"], saffi: ["#C08020", "#5A2A6A"], mott: ["#2A5A3A", "#E8D8B0"], books: ["#2A3A6A", "#D8C8A0"] };
  const awning = (p, a, b) => { p.fillStyle = "#5A3A1E"; p.fillRect(30, 70, 10, 180); p.fillRect(216, 70, 10, 180); for (let i = 0; i < 8; i++) { p.fillStyle = i % 2 ? a : b; p.beginPath(); p.moveTo(18 + i * 28, 40); p.lineTo(46 + i * 28, 40); p.lineTo(46 + i * 28, 92); p.quadraticCurveTo(32 + i * 28, 104, 18 + i * 28, 92); p.closePath(); p.fill(); }
    p.fillStyle = "#6A4A2A"; p.fillRect(20, 196, 216, 18); p.fillStyle = "#8A6A40"; p.fillRect(20, 190, 216, 8); };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); for (const [id, [a, b]] of Object.entries(COLS)) { const c = cv(); awning(c.getContext("2d"), a, b); set.index[`stall:${id}`] = set.layers.length; set.layers.push(c); } return set; }; }
  const WHO = { hrodna: "npc:res_smith", saffi: "npc:res_farm", mott: "npc:hermit", books: "npc:res_library" };
  CM.thingSprites = Object.assign(CM.thingSprites || {}, { trader: (t, x, y) => { const out = [{ x, y, layer: `stall:${t.id}`, w: 1.0, h: 1.05, dz: -0.15 }]; const L = WHO[t.id]; if (L && CM.renderer && CM.renderer.index[L] !== undefined) out.push({ id: `trader:${t.id}`, act: "work", x, y, layer: L, w: 0.55, h: 0.75, dz: -0.05 }); return out; } });
  const rf0 = CM.UI.prototype.refresh;
  CM.UI.prototype.refresh = function (...a) { const out = rf0.apply(this, a), g = this.game, where = this.$ && this.$("#side .where"); if (where && g && g.floor && g.floor.number === 0 && g.mode !== "title" && CM.tradersOn) { const on = CM.tradersOn(g);
      let el = this.$("#side .market"); if (!el) { el = document.createElement("div"); el.className = "market small"; where.after(el); } el.textContent = on.length ? `${on.length > 1 ? "Market day" : "In the Square today"}: ${on.map((id) => CM.TRADERS[id].name).join(", ")}` : ""; }
    else { const el = this.$ && this.$("#side .market"); if (el) el.textContent = ""; } return out; };
}
