"use strict";
// Interiors, the window's side (v24.6): the keepers as figures, the rooms' painted walls, floors and ceilings by style,
// and the furniture's pictures and shapes (76zzzzh-models.js's kit). The rules are 69t-interiors.js.
{ const IN = CM.INTERIORS;
  // the keepers, as figures
  CM.interiorLayer = (t) => { const R = IN[t.id]; return R && R.who ? `npc:${R.who}` : null; };
  // the painted surfaces of each style: plaster and timber over planks, the forge's stone, the library's panelling, the temple's pale stone; a beamed ceiling
  const S0 = 256, cv = () => { const c = document.createElement("canvas"); c.width = S0; c.height = S0; return c; };
  const noise = (p, n, cols, seed) => { const R = new CM.Random(seed); for (let k = 0; k < n; k++) { p.fillStyle = cols[k % cols.length]; p.fillRect(R.next() * S0, R.next() * S0, 2 + R.next() * 3, 2 + R.next() * 3); } };
  const SURF = {
    planks: (p) => { p.fillStyle = "#7A5634"; p.fillRect(0, 0, S0, S0); for (let i = 0; i < 4; i++) { p.fillStyle = i % 2 ? "#6E4C2C" : "#84603A"; p.fillRect(0, i * 64, S0, 62); p.fillStyle = "#3A2614"; p.fillRect(0, i * 64 + 62, S0, 2); p.fillRect(((i * 97) % 200) + 20, i * 64, 2, 62); } noise(p, 900, ["rgba(40,24,10,0.15)", "rgba(200,160,110,0.08)"], 3); },
    flags: (p) => { p.fillStyle = "#6E6862"; p.fillRect(0, 0, S0, S0); p.strokeStyle = "#3A3632"; p.lineWidth = 3; for (const [x, y, w, h] of [[0, 0, 128, 100], [128, 0, 128, 140], [0, 100, 90, 156], [90, 100, 166, 80], [128, 140, 128, 116], [90, 180, 38, 76]]) p.strokeRect(x, y, w, h); noise(p, 1400, ["rgba(0,0,0,0.12)", "rgba(255,255,255,0.06)"], 5); },
    plaster: (p) => { p.fillStyle = "#D8CCB4"; p.fillRect(0, 0, S0, S0); noise(p, 1200, ["rgba(120,100,70,0.08)", "rgba(255,255,255,0.1)"], 7); p.fillStyle = "#4A3220"; p.fillRect(0, 0, S0, 14); p.fillRect(0, S0 - 34, S0, 34); p.fillRect(0, 0, 14, S0);
      p.save(); p.translate(14, S0 - 34); p.rotate(-0.72); p.fillRect(0, -7, 300, 14); p.restore(); p.fillStyle = "#5A3E28"; p.fillRect(0, S0 - 34, S0, 4); },
    stone: (p) => { p.fillStyle = "#5E5A56"; p.fillRect(0, 0, S0, S0); p.fillStyle = "#3A3632"; for (let y = 0; y < S0; y += 42) { p.fillRect(0, y, S0, 3); for (let x = (y / 42) % 2 ? 0 : 40; x < S0; x += 80) p.fillRect(x, y, 3, 42); } noise(p, 1400, ["rgba(0,0,0,0.12)", "rgba(255,240,220,0.06)"], 9); },
    pale: (p) => { p.fillStyle = "#C8C2B6"; p.fillRect(0, 0, S0, S0); p.fillStyle = "#9A948A"; for (let y = 0; y < S0; y += 52) { p.fillRect(0, y, S0, 2); for (let x = (y / 52) % 2 ? 0 : 64; x < S0; x += 128) p.fillRect(x, y, 2, 52); } p.fillStyle = "#B8A070"; p.fillRect(0, S0 - 30, S0, 6); noise(p, 800, ["rgba(0,0,0,0.06)"], 11); },
    panel: (p) => { p.fillStyle = "#5A3A20"; p.fillRect(0, 0, S0, S0); for (let x = 8; x < S0; x += 64) { p.fillStyle = "#6A4626"; p.fillRect(x, 20, 48, S0 - 60); p.strokeStyle = "#3A2410"; p.lineWidth = 3; p.strokeRect(x, 20, 48, S0 - 60); } p.fillStyle = "#C89A40"; p.fillRect(0, 8, S0, 4); noise(p, 600, ["rgba(0,0,0,0.12)"], 13); },
    beams: (p) => { p.fillStyle = "#3A2A1E"; p.fillRect(0, 0, S0, S0); p.fillStyle = "#5A4028"; p.fillRect(0, 100, S0, 56); p.fillStyle = "#2A1C10"; p.fillRect(0, 154, S0, 4); noise(p, 600, ["rgba(0,0,0,0.15)", "rgba(200,170,120,0.05)"], 15); },
  };
  const STYLE = { inn: { floor: "planks", wall: "plaster", ceiling: "beams" }, forge: { floor: "flags", wall: "stone", ceiling: "beams" }, library: { floor: "planks", wall: "panel", ceiling: "beams" }, temple: { floor: "flags", wall: "pale", ceiling: "pale" }, hall: { floor: "planks", wall: "stone", ceiling: "beams" } };
  { const b0 = CM.art.build; CM.art.build = function (th, look) { const set = b0.call(this, th, look); if (!th || !th.interior) return set; const St = STYLE[th.interior] || STYLE.inn, Nn = set.size || S0;
      for (const [layer, kind] of [["floor", St.floor], ["wall", St.wall], ["wall2", St.wall], ["wallbones", St.wall], ["wallsecret", St.wall], ["ceiling", St.ceiling]]) { const i = set.index[layer]; if (i === undefined) continue; const c = cv(); SURF[kind](c.getContext("2d"));
        let out = c; if (Nn !== S0) { out = document.createElement("canvas"); out.width = Nn; out.height = Nn; out.getContext("2d").drawImage(c, 0, 0, Nn, Nn); } set.layers[i] = out; }
      return set; }; }
  // the furniture's own pictures: book spines, cloth, stone, the fire in a hearth
  const paint = (size, kind) => { const c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"), s = size / 64, R = new CM.Random(CM.hashSeed(`int:${kind}`));
    if (kind === "books") { p.fillStyle = "#3A2614"; p.fillRect(0, 0, size, size); for (let row = 0; row < 3; row++) { let x = 2; while (x < 62) { const w = 3 + Math.floor(R.next() * 4), h = 13 + Math.floor(R.next() * 6); p.fillStyle = ["#8A2A22", "#2A4A6A", "#3A6A3A", "#8A6A2A", "#5A2A5A", "#6A4A2A"][Math.floor(R.next() * 6)]; p.fillRect(x * s, (row * 21 + 20 - h) * s, w * s, h * s); x += w + 0.5; } p.fillStyle = "#5A3E24"; p.fillRect(0, (row * 21 + 20) * s, size, 2 * s); } }
    else if (kind === "cloth") { p.fillStyle = "#8A2A2A"; p.fillRect(0, 0, size, size); p.fillStyle = "#C8A048"; p.fillRect(0, 6 * s, size, 3 * s); p.fillRect(0, 55 * s, size, 3 * s); }
    else if (kind === "linen") { p.fillStyle = "#E8E0CC"; p.fillRect(0, 0, size, size); p.fillStyle = "#5A6A9A"; for (let y = 0; y < 64; y += 8) p.fillRect(0, y * s, size, 3 * s); }
    else if (kind === "stone") { p.fillStyle = "#7A746C"; p.fillRect(0, 0, size, size); p.fillStyle = "#4A4640"; for (let y = 0; y < 64; y += 16) { p.fillRect(0, y * s, size, s); for (let x = (y / 16) % 2 ? 0 : 12; x < 64; x += 24) p.fillRect(x * s, y * s, s, 16 * s); } }
    else if (kind === "fire") { const g = p.createRadialGradient(size / 2, size * 0.8, 2, size / 2, size * 0.7, size * 0.6); g.addColorStop(0, "#FFF2A0"); g.addColorStop(0.35, "#FF9A30"); g.addColorStop(0.7, "#A0300C"); g.addColorStop(1, "#200804"); p.fillStyle = g; p.fillRect(0, 0, size, size); }
    return c; };
  { const b1 = CM.art.build; CM.art.build = function (th, look) { const set = b1.call(this, th, look); for (const k of ["books", "cloth", "linen", "stone", "fire"]) { set.index[`model:${k}`] = set.layers.length; set.layers.push(paint(set.size, k)); } return set; }; }
  // the furniture's shapes (the kit: boxes and cylinders in the piece's own frame; its front faces +z)
  { const pm0 = CM.propModel; CM.propModel = (p, quad, index) => {
      if (!["counter", "shelf", "table", "stool", "pew", "hearth", "anvil", "altar", "bed"].includes(p.id)) return pm0(p, quad, index);
      const K = CM.modelKit(p, quad, index); if (!K) return false; const { box, at, L } = K, Q = (a, b, c, d, layer, sh) => quad(at(...a), at(...b), at(...c), at(...d), layer, sh);
      switch (p.id) {
        case "counter": box(-0.49, 0, -0.22, 0.49, 0.46, 0.22, L("wood"), L("dark")); box(-0.5, 0.46, -0.25, 0.5, 0.5, 0.25, L("dark"), L("wood")); return true;
        case "shelf": box(-0.46, 0, -0.16, 0.46, 0.88, 0.16, L("dark"), L("dark")); Q([-0.43, 0.03, 0.161], [0.43, 0.03, 0.161], [0.43, 0.85, 0.161], [-0.43, 0.85, 0.161], p.books ? L("books") : L("wood"), 0.95);
          if (!p.books) for (const y of [0.3, 0.58]) box(-0.43, y, 0.0, 0.43, y + 0.03, 0.2, L("dark"), L("wood")); return true;
        case "table": box(-0.4, 0.38, -0.3, 0.4, 0.43, 0.3, L("dark"), L("wood")); for (const [x, z] of [[-0.36, -0.26], [0.32, -0.26], [-0.36, 0.22], [0.32, 0.22]]) box(x, 0, z, x + 0.04, 0.38, z + 0.04, L("dark"), null); return true;
        case "stool": box(-0.13, 0.22, -0.13, 0.13, 0.26, 0.13, L("dark"), L("wood")); for (const [x, z] of [[-0.11, -0.11], [0.08, -0.11], [-0.11, 0.08], [0.08, 0.08]]) box(x, 0, z, x + 0.03, 0.22, z + 0.03, L("dark"), null); return true;
        case "pew": box(-0.46, 0.2, -0.14, 0.46, 0.25, 0.14, L("dark"), L("wood")); box(-0.46, 0.25, -0.16, 0.46, 0.55, -0.12, L("wood"), L("dark")); for (const x of [-0.44, 0.4]) box(x, 0, -0.14, x + 0.04, 0.2, 0.14, L("dark"), null); return true;
        case "hearth": box(-0.48, 0, -0.18, 0.48, 0.72, 0.2, L("stone"), L("stone")); box(-0.52, 0.72, -0.2, 0.52, 0.78, 0.26, L("stone"), L("stone"));
          Q([-0.3, 0.02, 0.202], [0.3, 0.02, 0.202], [0.3, p.forge ? 0.42 : 0.5, 0.202], [-0.3, p.forge ? 0.42 : 0.5, 0.202], L("fire"), 1.4); return true;
        case "anvil": box(-0.2, 0, -0.1, 0.2, 0.22, 0.1, L("dark"), L("dark")); box(-0.08, 0.22, -0.06, 0.08, 0.3, 0.06, L("iron"), L("iron")); box(-0.24, 0.3, -0.09, 0.22, 0.38, 0.09, L("iron"), L("iron")); return true;
        case "altar": box(-0.45, 0, -0.22, 0.45, 0.5, 0.22, L("stone"), L("stone")); box(-0.46, 0.5, -0.23, 0.46, 0.53, 0.23, L("cloth"), L("cloth")); return true;
        case "bed": box(-0.42, 0, -0.32, 0.42, 0.24, 0.42, L("dark"), L("linen")); box(-0.36, 0.24, 0.24, 0.36, 0.3, 0.4, L("linen"), L("linen")); box(-0.44, 0, 0.42, 0.44, 0.5, 0.46, L("dark"), L("dark")); return true;
        default: return false;
      } }; }
  // indoors, only a little dust in the lamplight
  { const k0 = CM.airKinds; CM.airKinds = function (env) { const g = CM.game; if (g && g.floor && g.floor.special === "interior") return [{ id: "mote", rate: 2 }]; return k0.call(this, env); }; }
  // the door, by hand: a house that stands is walked into (the rules still say "building"; Automatic and a film keep to the door's window)
  { const em0 = CM.Game.prototype.emit; CM.Game.prototype.emit = function (event, ...args) {
      if (event === "building" && CM.ui && this.floor && this.floor.number === 0 && CM.INTERIORS[args[0]] && !this.replaying && !(this.film && this.film.playing) && !(this.autoOn && this.autoOn()) && CM.interiorOpen(this, args[0]) && this.intEnter(args[0])) return;
      return em0.call(this, event, ...args); }; }
}
