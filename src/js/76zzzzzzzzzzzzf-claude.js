"use strict";
// Claude, at the end of the green path - the window's side (UPGRADE_PLAN_70.md): Claude himself, a figure like the
// town's own (the scholar's frame, ink-brown, a book under his arm), and asleep a heap of blankets with a lamp beside;
// the cat who belongs to nobody; the post at the path's mouth with its quill; the door back out. Rules: 69zzzm-claude.js.
{ const S = 256;
  if (CM.figuresPack && CM.figuresPack.figures) CM.figuresPack.figures["npc:claude"] = { model: "mage", scale: 0.96, tint: [196, 176, 150], wear: ["book"], attack: "cast" };
  const shadow = (p, w) => { p.fillStyle = "rgba(0,0,0,0.32)"; p.beginPath(); p.ellipse(128, 244, w, 10, 0, 0, Math.PI * 2); p.fill(); };
  const PAINT = {
    // the cat: grey, curled, one eye open
    cat: (p) => { shadow(p, 56); p.fillStyle = "#6E6A66"; p.beginPath(); p.ellipse(124, 210, 62, 32, 0, 0, Math.PI * 2); p.fill(); p.beginPath(); p.ellipse(170, 196, 28, 24, 0, 0, Math.PI * 2); p.fill();
      p.beginPath(); p.moveTo(152, 180); p.lineTo(158, 152); p.lineTo(170, 176); p.fill(); p.beginPath(); p.moveTo(176, 176); p.lineTo(188, 150); p.lineTo(194, 180); p.fill();
      p.strokeStyle = "#6E6A66"; p.lineWidth = 14; p.lineCap = "round"; p.beginPath(); p.moveTo(66, 214); p.quadraticCurveTo(60, 244, 120, 240); p.stroke();
      p.fillStyle = "#8A8580"; p.beginPath(); p.ellipse(118, 200, 30, 12, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#D8C040"; p.beginPath(); p.ellipse(180, 194, 5, 3, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#3A3632"; p.fillRect(160, 194, 10, 2); },
    // the post at the path's mouth: weathered wood, a quill cut into it, a small board under
    post: (p) => { shadow(p, 30); p.fillStyle = "#6A4E32"; p.fillRect(116, 40, 26, 206); p.fillStyle = "#58402A"; p.fillRect(116, 40, 6, 206); p.fillStyle = "#7A5C3C"; p.beginPath(); p.moveTo(112, 44); p.lineTo(129, 26); p.lineTo(146, 44); p.fill();
      p.strokeStyle = "#E8DCC0"; p.lineWidth = 3; p.beginPath(); p.moveTo(121, 118); p.quadraticCurveTo(136, 84, 140, 58); p.stroke(); p.lineWidth = 2; for (let i = 0; i < 7; i++) { const t = i / 7, x = 124 + t * 14, y = 112 - t * 50; p.beginPath(); p.moveTo(x, y); p.lineTo(x - 8, y - 4); p.stroke(); }
      p.fillStyle = "#8A6A44"; p.fillRect(92, 140, 74, 34); p.fillStyle = "#3A2818"; p.fillRect(102, 150, 54, 3); p.fillRect(102, 160, 40, 3); },
    // asleep: blankets, and the lamp still lit
    asleep: (p) => { shadow(p, 90); p.fillStyle = "#6A3A30"; p.beginPath(); p.ellipse(120, 206, 92, 34, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#8A5A3A"; p.beginPath(); p.ellipse(106, 196, 70, 22, -0.08, 0, Math.PI * 2); p.fill();
      p.fillStyle = "#3A5A6A"; for (let i = 0; i < 5; i++) p.fillRect(48 + i * 30, 186 + (i % 2) * 6, 16, 26); p.fillStyle = "#D8B890"; p.beginPath(); p.arc(206, 188, 16, 0, Math.PI * 2); p.fill(); p.fillStyle = "#2A2018"; p.beginPath(); p.arc(210, 182, 16, Math.PI * 1.1, Math.PI * 1.9); p.fill();
      p.fillStyle = "#E8E0CC"; p.font = "italic 30px Georgia"; p.fillText("z", 222, 150); p.font = "italic 22px Georgia"; p.fillText("z", 238, 126); },
  };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look);
      for (const [k, f] of Object.entries(PAINT)) { const cv = document.createElement("canvas"); cv.width = cv.height = S; f(cv.getContext("2d")); set.index[`claude:${k}`] = set.layers.length; set.layers.push(cv); }
      if (set.index["npc:claude"] === undefined && set.index["npc:res_library"] !== undefined) set.index["npc:claude"] = set.index["npc:res_library"];   // (the painted stand-in, till the figures are read)
      return set; }; }
  CM.thingSprites = Object.assign(CM.thingSprites || {}, {
    claude: (t, x, y, now) => { const g = CM.game; if (g && CM.claudeSpot && CM.claudeSpot(g) === "bed") return [{ x, y, layer: "claude:asleep", w: 0.9, h: 0.5, dz: -0.75, lift: 0.36 }];
      return [{ x, y, layer: "npc:claude", w: 0.7, h: 0.85, lift: Math.sin(now / 1200 + x) * 0.006 }]; },
    cabincat: (t, x, y, now) => [{ x, y, layer: "claude:cat", w: 0.42, h: 0.32, lift: Math.abs(Math.sin(now / 1700)) * 0.004 }],
    quillpost: (t, x, y) => [{ x, y, layer: "claude:post", w: 0.42, h: 0.95 }],
    claudeexit: (t, x, y) => [{ x, y, layer: "door_open", face: 2, w: 0.7, h: 0.92, lift: 0.04, glow: 0.2 }],
    claudecabin: () => [],   /* (the door is the cabin's own, in the mesh) */
  });
}
