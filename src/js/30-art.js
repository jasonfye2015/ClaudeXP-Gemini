"use strict";
// Everything the game shows is painted here in code - the stone of each depth, the chests and hatches, every
// monster, the heroes' portraits - so the one file carries no pictures. Textures and sprites are 256 x 256 and go to
// the renderer as the layers of one texture array; CM.art.build(theme) returns {layers: [canvas...], index: {name: n}}.
CM.art = {};
const ART_SIZE = 256;

function artCanvas(size = ART_SIZE) {
  const c = document.createElement("canvas");
  c.width = c.height = size;
  return c;
}

function rgb([r, g, b], k = 1, a = 1) {
  return `rgba(${Math.round(CM.clamp(r * k, 0, 255))},${Math.round(CM.clamp(g * k, 0, 255))},${Math.round(CM.clamp(b * k, 0, 255))},${a})`;
}

function speckle(p, rnd, w, h, n, colour, alpha, size = 2) {           // grain on stone
  p.fillStyle = colour;
  p.globalAlpha = alpha;
  for (let i = 0; i < n; i++) p.fillRect(rnd.next() * w, rnd.next() * h, size * (0.5 + rnd.next()), size * (0.5 + rnd.next()));
  p.globalAlpha = 1;
}

function crack(p, rnd, x, y, length, colour) {
  p.strokeStyle = colour;
  p.lineWidth = 1.5;
  p.beginPath();
  p.moveTo(x, y);
  let a = rnd.next() * Math.PI * 2;
  for (let i = 0; i < length; i += 6) {
    a += (rnd.next() - 0.5) * 1.2;
    x += Math.cos(a) * 6;
    y += Math.sin(a) * 6;
    p.lineTo(x, y);
  }
  p.stroke();
}

function bone(p, rnd, x, y, k) {                                      // a bone, or a skull, set into the wall
  p.save();
  p.translate(x, y);
  p.rotate((rnd.next() - 0.5) * 1.2);
  p.fillStyle = "#D8D0B8";
  p.strokeStyle = "#5A5040";
  p.lineWidth = 1.5;
  if (k < 0.5) {
    p.fillRect(-14, -3, 28, 6);
    p.strokeRect(-14, -3, 28, 6);
    for (const sx of [-14, 14]) { p.beginPath(); p.arc(sx, -3, 4, 0, Math.PI * 2); p.arc(sx, 3, 4, 0, Math.PI * 2); p.fill(); p.stroke(); }
  } else {
    p.beginPath(); p.arc(0, -2, 11, 0, Math.PI * 2); p.fill(); p.stroke();
    p.fillRect(-7, 5, 14, 7); p.strokeRect(-7, 5, 14, 7);
    p.fillStyle = "#201810";
    p.beginPath(); p.arc(-4, -3, 3, 0, Math.PI * 2); p.arc(4, -3, 3, 0, Math.PI * 2); p.fill();
  }
  p.restore();
}

// ---- the stone ---------------------------------------------------------------------------------------------------
CM.art.wall = function (theme, seed, bones) {
  const c = artCanvas(), p = c.getContext("2d"), rnd = new CM.Random(seed), S = ART_SIZE;
  p.fillStyle = rgb(theme.mortar);
  p.fillRect(0, 0, S, S);
  const rows = 4, rowH = S / rows, cols = 3, mortar = 5;
  for (let r = 0; r < rows; r++) {
    const offset = r % 2 ? S / cols / 2 : 0;
    for (let col = -1; col <= cols; col++) {
      const x = col * (S / cols) + offset, y = r * rowH;
      const k = 0.82 + rnd.next() * 0.36;
      const g = p.createLinearGradient(x, y, x, y + rowH);
      g.addColorStop(0, rgb(theme.stone, k * 1.08));
      g.addColorStop(1, rgb(theme.stone, k * 0.86));
      p.fillStyle = g;
      p.fillRect(x + mortar / 2, y + mortar / 2, S / cols - mortar, rowH - mortar);
      p.strokeStyle = rgb(theme.stone, k * 1.25, 0.5);                 // a lit top edge
      p.lineWidth = 1.5;
      p.beginPath(); p.moveTo(x + mortar / 2, y + mortar / 2 + 1); p.lineTo(x + S / cols - mortar / 2, y + mortar / 2 + 1); p.stroke();
      p.strokeStyle = rgb(theme.mortar, 0.7, 0.6);                      // a shadowed bottom edge
      p.beginPath(); p.moveTo(x + mortar / 2, y + rowH - mortar / 2 - 1); p.lineTo(x + S / cols - mortar / 2, y + rowH - mortar / 2 - 1); p.stroke();
    }
  }
  speckle(p, rnd, S, S, 900, rgb(theme.stone, 0.55), 0.35);
  speckle(p, rnd, S, S, 500, rgb(theme.stone, 1.5), 0.2);
  for (let i = 0; i < 3; i++) crack(p, rnd, rnd.next() * S, rnd.next() * S, 30 + rnd.next() * 50, rgb(theme.mortar, 0.6, 0.8));
  p.globalAlpha = 0.45;                                                 // moss creeping in from the corners
  for (let i = 0; i < 5; i++) {
    const x = rnd.pick([0, S]) + (rnd.next() - 0.5) * 60, y = rnd.next() * S;
    const g = p.createRadialGradient(x, y, 0, x, y, 26 + rnd.next() * 30);
    g.addColorStop(0, rgb(theme.moss, 1, 0.8)); g.addColorStop(1, rgb(theme.moss, 1, 0));
    p.fillStyle = g; p.fillRect(0, 0, S, S);
  }
  p.globalAlpha = 1;
  if (bones) for (let i = 0; i < 2 + rnd.int(0, 2); i++) bone(p, rnd, 30 + rnd.next() * (S - 60), 30 + rnd.next() * (S - 60), rnd.next());
  return c;
};

CM.art.floor = function (theme, seed) {
  const c = artCanvas(), p = c.getContext("2d"), rnd = new CM.Random(seed), S = ART_SIZE;
  p.fillStyle = rgb(theme.mortar, 0.9);
  p.fillRect(0, 0, S, S);
  const n = 4, cell = S / n;
  for (let r = 0; r < n; r++) for (let col = 0; col < n; col++) {
    const k = 0.8 + rnd.next() * 0.4, gap = 4 + rnd.next() * 3;
    p.fillStyle = rgb(theme.floor, k);
    const x = col * cell + gap / 2, y = r * cell + gap / 2, w = cell - gap, h = cell - gap;
    p.beginPath();                                                      // a flagstone, a little irregular
    p.moveTo(x + rnd.next() * 6, y + rnd.next() * 6);
    p.lineTo(x + w - rnd.next() * 6, y + rnd.next() * 6);
    p.lineTo(x + w - rnd.next() * 6, y + h - rnd.next() * 6);
    p.lineTo(x + rnd.next() * 6, y + h - rnd.next() * 6);
    p.closePath(); p.fill();
  }
  speckle(p, rnd, S, S, 1200, rgb(theme.floor, 0.5), 0.3);
  speckle(p, rnd, S, S, 400, rgb(theme.floor, 1.4), 0.2);
  if (theme.name.includes("Flooded")) {                                 // standing water
    for (let i = 0; i < 3; i++) {
      const x = rnd.next() * S, y = rnd.next() * S, rad = 30 + rnd.next() * 40;
      const g = p.createRadialGradient(x, y, 0, x, y, rad);
      g.addColorStop(0, "rgba(60,110,140,0.75)"); g.addColorStop(1, "rgba(60,110,140,0)");
      p.fillStyle = g; p.fillRect(0, 0, S, S);
    }
  }
  return c;
};

CM.art.ceiling = function (theme, seed) {
  const c = artCanvas(), p = c.getContext("2d"), rnd = new CM.Random(seed), S = ART_SIZE;
  p.fillStyle = rgb(theme.ceiling);
  p.fillRect(0, 0, S, S);
  speckle(p, rnd, S, S, 1500, rgb(theme.ceiling, 0.6), 0.4, 3);
  speckle(p, rnd, S, S, 500, rgb(theme.ceiling, 1.4), 0.25, 2);
  for (let i = 0; i < 4; i++) crack(p, rnd, rnd.next() * S, rnd.next() * S, 40 + rnd.next() * 60, rgb(theme.ceiling, 0.4, 0.9));
  return c;
};

// ---- things ------------------------------------------------------------------------------------------------------
CM.art.chest = function () {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE;
  const w = 150, h = 70, x = (S - w) / 2, y = S - 20 - h;
  p.fillStyle = "rgba(0,0,0,0.35)";                                      // its shadow on the floor
  p.beginPath(); p.ellipse(S / 2, S - 18, w / 2 + 6, 10, 0, 0, Math.PI * 2); p.fill();
  p.fillStyle = "#6E4420"; p.fillRect(x, y, w, h);                     // the box
  p.fillStyle = "#8A5A2A"; p.fillRect(x, y - 30, w, 34);               // the lid
  p.fillStyle = "#5A3618";
  for (const bx of [x + 14, x + w / 2 - 5, x + w - 24]) p.fillRect(bx, y - 30, 10, h + 34);   // the planks' bands
  p.fillStyle = "#3A2410";
  for (let i = 1; i < 4; i++) p.fillRect(x, y + i * (h / 4), w, 2);
  p.strokeStyle = "#2A1A08"; p.lineWidth = 3; p.strokeRect(x, y - 30, w, h + 34);
  p.fillStyle = "#D8B040"; p.fillRect(S / 2 - 12, y - 6, 24, 26);       // the lock
  p.fillStyle = "#2A1A08"; p.fillRect(S / 2 - 3, y + 4, 6, 10);
  p.strokeStyle = "#D8B040"; p.lineWidth = 3;                           // the hinges' glint
  p.beginPath(); p.moveTo(x + 4, y - 26); p.lineTo(x + w - 4, y - 26); p.stroke();
  return c;
};

CM.art.hatch = function (theme) {                                       // a ladder down: a hole in the floor, seen from above
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE;
  p.fillStyle = rgb(theme.floor, 0.9); p.fillRect(0, 0, S, S);
  p.fillStyle = rgb(theme.floor, 1.2); p.fillRect(28, 28, S - 56, S - 56);   // a stone rim
  p.fillStyle = "#050403"; p.fillRect(40, 40, S - 80, S - 80);              // the dark
  const g = p.createLinearGradient(40, 40, S - 40, S - 40);
  g.addColorStop(0, "rgba(90,70,40,0.35)"); g.addColorStop(1, "rgba(0,0,0,0)");
  p.fillStyle = g; p.fillRect(40, 40, S - 80, S - 80);
  p.strokeStyle = "#A07840"; p.lineWidth = 9;                               // the ladder's rails and rungs
  p.beginPath(); p.moveTo(84, 40); p.lineTo(84, S - 40); p.moveTo(S - 84, 40); p.lineTo(S - 84, S - 40); p.stroke();
  p.lineWidth = 7;
  for (let y = 62; y < S - 44; y += 30) { p.beginPath(); p.moveTo(84, y); p.lineTo(S - 84, y); p.stroke(); }
  p.strokeStyle = "#1A1208"; p.lineWidth = 4; p.strokeRect(40, 40, S - 80, S - 80);
  return c;
};

// ---- monsters: one painter, many creatures ----------------------------------------------------------------------
function outlined(p, draw, fill, line = "#1A1410", width = 3) {
  p.fillStyle = fill; p.strokeStyle = line; p.lineWidth = width; p.lineJoin = "round";
  p.beginPath(); draw(); p.closePath(); p.fill(); p.stroke();
}

function shaded(p, hex, k) {                                            // a colour lighter (k > 1) or darker
  const v = parseInt(hex.slice(1), 16);
  return rgb([(v >> 16) & 255, (v >> 8) & 255, v & 255], k);
}

CM.art.monster = function (m, big = false) {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, cx = S / 2, ground = S - 14;
  const col = m.colour, dark = shaded(p, col, 0.65), light = shaded(p, col, 1.3);
  const bodies = { beast: [150, 70], small: [66, 76], biped: [84, 100], thin: [58, 100], wide: [130, 112], tall: [78, 140], ghost: [90, 140] };
  const [bw, bh] = bodies[m.body] || bodies.biped;
  const scale = big ? 1.12 : 1;
  p.translate(cx, ground); p.scale(scale, scale); p.translate(-cx, -ground);
  const bodyTop = ground - (m.body === "beast" ? 24 : 36) - bh, bodyBottom = bodyTop + bh;
  const headR = m.body === "small" ? 30 : m.body === "wide" ? 28 : m.body === "beast" ? 26 : 24;
  const headY = m.body === "beast" ? bodyTop + 4 : bodyTop - headR + 8;
  const ex = m.extras || [];
  p.fillStyle = "rgba(0,0,0,0.35)";                                     // the shadow on the floor
  p.beginPath(); p.ellipse(cx, ground - 2, bw / 2 + 10, 9, 0, 0, Math.PI * 2); p.fill();
  if (ex.includes("wings")) {
    for (const side of [-1, 1]) {
      outlined(p, () => {
        p.moveTo(cx + side * bw * 0.3, bodyTop + 20); p.lineTo(cx + side * (bw * 0.5 + 70), bodyTop - 40);
        p.lineTo(cx + side * (bw * 0.5 + 76), bodyTop + 10); p.lineTo(cx + side * (bw * 0.5 + 44), bodyTop + 2);
        p.lineTo(cx + side * (bw * 0.5 + 56), bodyTop + 50); p.lineTo(cx + side * (bw * 0.5 + 20), bodyTop + 36);
      }, dark);
    }
  }
  if (ex.includes("cape")) outlined(p, () => { p.moveTo(cx - bw * 0.6, bodyTop + 10); p.lineTo(cx + bw * 0.6, bodyTop + 10); p.lineTo(cx + bw * 0.75, ground); p.lineTo(cx - bw * 0.75, ground); }, "#2A1018");
  // legs (not for ghosts: they float)
  if (m.body !== "ghost") {
    const legW = m.body === "beast" ? 16 : Math.max(14, bw * 0.2), legs = m.body === "beast" ? [-0.4, -0.15, 0.15, 0.4] : [-0.25, 0.25];
    for (const f of legs) outlined(p, () => { p.rect(cx + f * bw - legW / 2, bodyBottom - 10, legW, ground - bodyBottom + 10); }, dark);
  }
  // the body
  if (m.body === "ghost") {
    const g = p.createLinearGradient(0, bodyTop, 0, ground);
    g.addColorStop(0, col); g.addColorStop(0.7, dark); g.addColorStop(1, "rgba(0,0,0,0)");
    p.fillStyle = g; p.beginPath();
    p.moveTo(cx - bw / 2, bodyTop + 30); p.quadraticCurveTo(cx, bodyTop - 20, cx + bw / 2, bodyTop + 30); p.lineTo(cx + bw / 2 + 10, ground - 30);
    for (let i = 4; i >= -4; i--) p.lineTo(cx + i * (bw / 8), ground - (i % 2 ? 10 : 34));
    p.lineTo(cx - bw / 2 - 10, ground - 30); p.closePath(); p.fill();
  } else if (m.body === "beast") {
    outlined(p, () => { p.ellipse(cx, bodyTop + bh / 2, bw / 2, bh / 2, 0, 0, Math.PI * 2); }, col);
  } else {
    const g = p.createLinearGradient(cx - bw / 2, 0, cx + bw / 2, 0);
    g.addColorStop(0, light); g.addColorStop(0.5, col); g.addColorStop(1, dark);
    outlined(p, () => {
      if (ex.includes("robe") || m.body === "tall") { p.moveTo(cx - bw / 2, bodyTop + 10); p.lineTo(cx + bw / 2, bodyTop + 10); p.lineTo(cx + bw / 2 + 12, ground); p.lineTo(cx - bw / 2 - 12, ground); }
      else p.roundRect(cx - bw / 2, bodyTop, bw, bh, 18);
    }, g);
    if (m.head === "skull" || ex.includes("torn")) {                     // ribs, or rags
      p.strokeStyle = m.head === "skull" ? "#1A1410" : dark; p.lineWidth = 3;
      for (let i = 1; i <= 4; i++) { const y = bodyTop + 14 + i * 16; p.beginPath(); p.moveTo(cx - bw * 0.35, y); p.quadraticCurveTo(cx, y + 8, cx + bw * 0.35, y); p.stroke(); }
    }
  }
  // arms and what they hold
  if (m.body !== "beast" && m.body !== "ghost") {
    const armW = Math.max(14, bw * 0.17), armLen = ex.includes("claws") ? bh * 0.8 : bh * 0.6;
    for (const side of [-1, 1]) {
      outlined(p, () => { p.roundRect(cx + side * (bw / 2 + 2) - (side < 0 ? armW : 0), bodyTop + 16, armW, armLen, 8); }, dark);
      if (ex.includes("claws")) {
        p.strokeStyle = "#E8E8E0"; p.lineWidth = 3;
        for (let i = -1; i <= 1; i++) { const x = cx + side * (bw / 2 + armW / 2 + 2) + i * 6; p.beginPath(); p.moveTo(x, bodyTop + 16 + armLen); p.lineTo(x + i * 2, bodyTop + 16 + armLen + 18); p.stroke(); }
      }
    }
    const hx = cx + bw / 2 + armW / 2 + 2, hy = bodyTop + 16 + armLen;
    p.lineCap = "round";
    if (ex.includes("sword") || ex.includes("dagger")) {
      const len = ex.includes("sword") ? 80 : 44;
      p.strokeStyle = "#1A1410"; p.lineWidth = 9; p.beginPath(); p.moveTo(hx, hy); p.lineTo(hx + 10, hy - len); p.stroke();
      p.strokeStyle = "#E8ECF4"; p.lineWidth = 5; p.beginPath(); p.moveTo(hx, hy); p.lineTo(hx + 10, hy - len); p.stroke();
      p.strokeStyle = "#8A6A20"; p.lineWidth = 5; p.beginPath(); p.moveTo(hx - 8, hy - 8); p.lineTo(hx + 10, hy - 2); p.stroke();
    } else if (ex.includes("club")) {
      p.strokeStyle = "#1A1410"; p.lineWidth = 12; p.beginPath(); p.moveTo(hx, hy); p.lineTo(hx + 14, hy - 70); p.stroke();
      p.strokeStyle = "#7A5A30"; p.lineWidth = 8; p.beginPath(); p.moveTo(hx, hy); p.lineTo(hx + 14, hy - 70); p.stroke();
      outlined(p, () => { p.ellipse(hx + 16, hy - 76, 14, 20, 0.2, 0, Math.PI * 2); }, "#6A4A28");
    } else if (ex.includes("axe")) {
      p.strokeStyle = "#1A1410"; p.lineWidth = 9; p.beginPath(); p.moveTo(hx, hy); p.lineTo(hx + 8, hy - 86); p.stroke();
      p.strokeStyle = "#6A4A28"; p.lineWidth = 5; p.beginPath(); p.moveTo(hx, hy); p.lineTo(hx + 8, hy - 86); p.stroke();
      outlined(p, () => { p.moveTo(hx + 6, hy - 84); p.lineTo(hx + 40, hy - 96); p.lineTo(hx + 40, hy - 50); p.lineTo(hx + 8, hy - 58); }, "#C8CCD4");
    } else if (ex.includes("bow")) {
      p.strokeStyle = "#1A1410"; p.lineWidth = 8; p.beginPath(); p.arc(hx + 6, hy - 30, 46, -1.2, 1.2); p.stroke();
      p.strokeStyle = "#8A6A30"; p.lineWidth = 4; p.beginPath(); p.arc(hx + 6, hy - 30, 46, -1.2, 1.2); p.stroke();
      p.strokeStyle = "#E8E8E0"; p.lineWidth = 1.5; p.beginPath(); p.moveTo(hx + 6 + 46 * Math.cos(-1.2), hy - 30 + 46 * Math.sin(-1.2)); p.lineTo(hx + 6 + 46 * Math.cos(1.2), hy - 30 + 46 * Math.sin(1.2)); p.stroke();
    } else if (ex.includes("staff")) {
      p.strokeStyle = "#1A1410"; p.lineWidth = 10; p.beginPath(); p.moveTo(hx, ground); p.lineTo(hx + 4, bodyTop - 50); p.stroke();
      p.strokeStyle = "#4A3A5A"; p.lineWidth = 6; p.beginPath(); p.moveTo(hx, ground); p.lineTo(hx + 4, bodyTop - 50); p.stroke();
      const g = p.createRadialGradient(hx + 4, bodyTop - 58, 0, hx + 4, bodyTop - 58, 22);
      g.addColorStop(0, m.eyes); g.addColorStop(0.5, shaded(p, m.eyes, 0.6)); g.addColorStop(1, "rgba(0,0,0,0)");
      p.fillStyle = g; p.beginPath(); p.arc(hx + 4, bodyTop - 58, 22, 0, Math.PI * 2); p.fill();
    }
  }
  if (ex.includes("tail")) {
    p.strokeStyle = "#1A1410"; p.lineWidth = 9; p.lineCap = "round";
    p.beginPath(); p.moveTo(cx + bw / 2 - 10, bodyBottom - 20); p.quadraticCurveTo(cx + bw / 2 + 50, bodyBottom - 10, cx + bw / 2 + 56, bodyTop); p.stroke();
    p.strokeStyle = dark; p.lineWidth = 5; p.stroke();
  }
  // the head
  const hy2 = headY, hx2 = cx;
  const faceCol = m.head === "skull" ? "#E8E4D8" : m.head === "pale" ? "#E8D8D0" : m.head === "hood" ? "#1A1420" : col;
  if (m.head === "hood") {
    outlined(p, () => { p.moveTo(hx2, hy2 - headR - 26); p.lineTo(hx2 + headR + 14, hy2 + headR); p.lineTo(hx2 - headR - 14, hy2 + headR); }, dark);
    outlined(p, () => { p.ellipse(hx2, hy2 + 4, headR * 0.8, headR * 0.9, 0, 0, Math.PI * 2); }, faceCol, "#0A080C", 2);
  } else {
    if (m.head === "horns") for (const side of [-1, 1]) outlined(p, () => { p.moveTo(hx2 + side * headR * 0.5, hy2 - headR * 0.6); p.quadraticCurveTo(hx2 + side * headR * 1.6, hy2 - headR * 1.2, hx2 + side * headR * 1.1, hy2 - headR * 2.0); p.lineTo(hx2 + side * headR * 0.9, hy2 - headR * 0.9); }, "#E8E0C8");
    if (m.head === "ears") for (const side of [-1, 1]) outlined(p, () => { p.moveTo(hx2 + side * headR * 0.6, hy2 - headR * 0.3); p.lineTo(hx2 + side * headR * 1.9, hy2 - headR * 1.0); p.lineTo(hx2 + side * headR * 0.8, hy2 + headR * 0.3); }, col);
    if (m.head === "pale") outlined(p, () => { p.ellipse(hx2, hy2 - 6, headR + 4, headR, 0, Math.PI, Math.PI * 2); }, "#1A1014");
    outlined(p, () => { p.ellipse(hx2, hy2, headR, headR * (m.head === "skull" ? 1.05 : 0.95), 0, 0, Math.PI * 2); }, faceCol);
    if (m.head === "snout") outlined(p, () => { p.ellipse(hx2, hy2 + headR * 0.55, headR * 0.7, headR * 0.45, 0, 0, Math.PI * 2); }, light);
    if (m.head === "tusks") for (const side of [-1, 1]) outlined(p, () => { p.moveTo(hx2 + side * headR * 0.5, hy2 + headR * 0.5); p.lineTo(hx2 + side * headR * 0.7, hy2 + headR * 1.05); p.lineTo(hx2 + side * headR * 0.25, hy2 + headR * 0.6); }, "#F0ECE0", "#1A1410", 2);
    if (m.head === "skull") {
      p.fillStyle = "#1A1410";
      for (const side of [-1, 1]) { p.beginPath(); p.ellipse(hx2 + side * headR * 0.42, hy2 - 2, headR * 0.3, headR * 0.34, 0, 0, Math.PI * 2); p.fill(); }
      p.beginPath(); p.moveTo(hx2, hy2 + 6); p.lineTo(hx2 - 5, hy2 + 16); p.lineTo(hx2 + 5, hy2 + 16); p.fill();
      p.fillRect(hx2 - headR * 0.5, hy2 + headR * 0.55, headR, 5);
      p.fillStyle = "#E8E4D8";
      for (let i = -3; i <= 3; i++) p.fillRect(hx2 + i * 6 - 2, hy2 + headR * 0.55, 4, 6);
    }
  }
  // the eyes: they glow
  const eyeY = m.head === "hood" ? hy2 + 2 : hy2 - (m.head === "snout" ? 6 : 2), eyeDX = headR * 0.42, eyeR = headR * (m.head === "skull" ? 0.18 : 0.14);
  p.save();
  p.shadowColor = m.eyes; p.shadowBlur = 14;
  p.fillStyle = m.eyes;
  for (const side of [-1, 1]) { p.beginPath(); p.arc(hx2 + side * eyeDX, eyeY, eyeR, 0, Math.PI * 2); p.fill(); }
  p.restore();
  if (ex.includes("crown")) {
    outlined(p, () => {
      const top = hy2 - headR - 2;
      p.moveTo(hx2 - headR * 0.9, top + 10);
      for (let i = 0; i <= 4; i++) { p.lineTo(hx2 - headR * 0.9 + i * headR * 0.45, top - (i % 2 ? 14 : 26)); }
      p.lineTo(hx2 + headR * 0.9, top + 10);
    }, "#F0C030", "#6A4A08", 2);
  }
  return c;
};

// ---- the dungeon's furniture ------------------------------------------------------------------------------------------
function planks(p, x, y, w, h, rnd, base = "#6E4A26", dark = "#4A2E14") {
  const n = Math.max(2, Math.round(w / 34));
  for (let i = 0; i < n; i++) {
    const px = x + i * (w / n), k = 0.9 + rnd.next() * 0.2;
    p.fillStyle = shaded(p, base, k);
    p.fillRect(px, y, w / n, h);
    p.fillStyle = dark; p.fillRect(px, y, 2, h);
    p.strokeStyle = shaded(p, dark, 0.8); p.lineWidth = 1;
    for (let g = 0; g < 3; g++) { const gx = px + 4 + rnd.next() * (w / n - 8); p.beginPath(); p.moveTo(gx, y + 4); p.lineTo(gx + (rnd.next() - 0.5) * 6, y + h - 4); p.stroke(); }
  }
}

CM.art.door = function (kind) {                                          // closed, locked, or open (the frame, the leaf swung in)
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(21);
  p.fillStyle = "#2A2420"; p.fillRect(0, 0, S, S);                       // the frame's stone
  p.fillStyle = "#4A4038"; p.fillRect(0, 0, S, 22); p.fillRect(0, 0, 22, S); p.fillRect(S - 22, 0, 22, S);
  p.fillStyle = "#1A1612"; p.fillRect(22, 22, S - 44, S - 22);
  if (kind === "open") {
    p.clearRect(30, 26, S - 60, S - 26);                                 // see through to the corridor beyond
    p.save(); p.translate(30, 26); p.transform(0.28, 0.09, 0, 1, 0, 0);  // the leaf, swung inward
    planks(p, 0, 0, S - 60, S - 26, rnd);
    p.restore();
    return c;
  }
  planks(p, 22, 22, S - 44, S - 22, rnd);
  p.fillStyle = "#2E2E34";                                               // iron bands
  for (const y of [50, S - 60]) { p.fillRect(22, y, S - 44, 14); for (let x = 30; x < S - 30; x += 24) { p.fillStyle = "#56565E"; p.beginPath(); p.arc(x, y + 7, 3, 0, Math.PI * 2); p.fill(); p.fillStyle = "#2E2E34"; } }
  p.strokeStyle = "#101010"; p.lineWidth = 3; p.strokeRect(22, 22, S - 44, S - 22);
  if (kind === "locked") {
    p.fillStyle = "#C8A040"; p.fillRect(S / 2 - 18, S / 2 - 6, 36, 40);
    p.strokeStyle = "#C8A040"; p.lineWidth = 7; p.beginPath(); p.arc(S / 2, S / 2 - 8, 14, Math.PI, 0); p.stroke();
    p.fillStyle = "#1A1410"; p.fillRect(S / 2 - 4, S / 2 + 6, 8, 16);
  } else {
    p.fillStyle = "#56565E"; p.beginPath(); p.arc(S - 50, S / 2 + 10, 8, 0, Math.PI * 2); p.fill();   // a ring handle
    p.strokeStyle = "#8A8A92"; p.lineWidth = 4; p.beginPath(); p.arc(S - 50, S / 2 + 24, 12, 0, Math.PI * 2); p.stroke();
  }
  return c;
};

CM.art.gate = function (open) {                                           // a portcullis, down or raised
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE;
  p.fillStyle = "#4A4038"; p.fillRect(0, 0, S, 20); p.fillRect(0, 0, 16, S); p.fillRect(S - 16, 0, 16, S);
  const top = open ? -S + 60 : 0;
  p.fillStyle = "#3A3A42"; p.strokeStyle = "#16161A"; p.lineWidth = 2;
  for (let x = 30; x < S - 20; x += 32) { p.fillRect(x, top + 20, 12, S - 20); p.strokeRect(x, top + 20, 12, S - 20);
    p.beginPath(); p.moveTo(x, top + S); p.lineTo(x + 6, top + S + 16); p.lineTo(x + 12, top + S); p.fill(); }
  for (let y = top + 50; y < top + S; y += 46) { p.fillRect(16, y, S - 32, 10); p.strokeRect(16, y, S - 32, 10); }
  return c;
};

CM.art.pit = function (theme, known) {                                     // a hole in the floor; a trapdoor, once it has given way
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(5);
  p.fillStyle = rgb(theme.floor, 0.9); p.fillRect(0, 0, S, S);
  if (known === "trapdoor") {
    planks(p, 30, 30, S - 60, S - 60, rnd, "#5A3E22", "#2A1A0A");
    p.strokeStyle = "#0A0806"; p.lineWidth = 4; p.beginPath(); p.moveTo(30, S / 2); p.lineTo(S - 30, S / 2); p.stroke();
    p.fillStyle = "#050403"; p.beginPath(); p.moveTo(30, S / 2 - 2); p.lineTo(S - 30, S / 2 - 2); p.lineTo(S - 40, S / 2 + 30); p.lineTo(40, S / 2 + 30); p.fill();
    return c;
  }
  p.fillStyle = "#050403"; p.beginPath();
  for (let i = 0; i < 16; i++) { const a = i / 16 * Math.PI * 2, r = 92 + rnd.next() * 18; p.lineTo(S / 2 + Math.cos(a) * r, S / 2 + Math.sin(a) * r); }
  p.closePath(); p.fill();
  p.strokeStyle = rgb(theme.floor, 0.5); p.lineWidth = 3; p.stroke();
  const g = p.createRadialGradient(S / 2, S / 2, 40, S / 2, S / 2, 100);
  g.addColorStop(0, "rgba(0,0,0,0)"); g.addColorStop(1, rgb(theme.floor, 0.35, 0.6));
  p.fillStyle = g; p.fill();
  return c;
};

CM.art.teleporter = function () {                                         // a ring of runes that glows
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE;
  p.clearRect(0, 0, S, S);
  const g = p.createRadialGradient(S / 2, S / 2, 20, S / 2, S / 2, 110);
  g.addColorStop(0, "rgba(140,80,255,0.85)"); g.addColorStop(0.6, "rgba(120,60,220,0.35)"); g.addColorStop(1, "rgba(80,40,160,0)");
  p.fillStyle = g; p.beginPath(); p.arc(S / 2, S / 2, 112, 0, Math.PI * 2); p.fill();
  p.strokeStyle = "#E0C8FF"; p.lineWidth = 5; p.beginPath(); p.arc(S / 2, S / 2, 88, 0, Math.PI * 2); p.stroke();
  p.lineWidth = 3; p.beginPath(); p.arc(S / 2, S / 2, 60, 0, Math.PI * 2); p.stroke();
  p.fillStyle = "#F0E8FF"; p.font = "bold 22px Georgia"; p.textAlign = "center"; p.textBaseline = "middle";
  for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2; p.save(); p.translate(S / 2 + Math.cos(a) * 74, S / 2 + Math.sin(a) * 74); p.rotate(a + Math.PI / 2); p.fillText("ᚠᚱᛇᛖᛟᚦᚷᛋᛒᛠᚫᚾ"[i], 0, 0); p.restore(); }
  return c;
};

CM.art.fountain = function (dry) {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, cx = S / 2, ground = S - 14;
  p.fillStyle = "rgba(0,0,0,0.35)"; p.beginPath(); p.ellipse(cx, ground - 2, 100, 10, 0, 0, Math.PI * 2); p.fill();
  outlined(p, () => { p.ellipse(cx, ground - 40, 96, 30, 0, 0, Math.PI * 2); }, "#6A6258");                  // the basin
  outlined(p, () => { p.rect(cx - 96, ground - 100, 192, 60); }, "#7A7268");
  outlined(p, () => { p.ellipse(cx, ground - 100, 96, 30, 0, 0, Math.PI * 2); }, "#8A8278");
  if (!dry) {
    const w = p.createRadialGradient(cx, ground - 100, 10, cx, ground - 100, 90);
    w.addColorStop(0, "#9AD0E8"); w.addColorStop(1, "#3A7A9A");
    p.fillStyle = w; p.beginPath(); p.ellipse(cx, ground - 100, 84, 22, 0, 0, Math.PI * 2); p.fill();
  } else {
    p.fillStyle = "#4A4640"; p.beginPath(); p.ellipse(cx, ground - 100, 84, 22, 0, 0, Math.PI * 2); p.fill();
  }
  outlined(p, () => { p.rect(cx - 12, ground - 200, 24, 100); }, "#7A7268");                                    // the column
  outlined(p, () => { p.ellipse(cx, ground - 204, 30, 10, 0, 0, Math.PI * 2); }, "#8A8278");
  if (!dry) {
    p.strokeStyle = "rgba(170,220,240,0.9)"; p.lineWidth = 4; p.lineCap = "round";
    for (const side of [-1, 1]) { p.beginPath(); p.moveTo(cx + side * 20, ground - 200); p.quadraticCurveTo(cx + side * 60, ground - 170, cx + side * 56, ground - 104); p.stroke(); }
  }
  return c;
};

CM.art.altar = function () {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, cx = S / 2, ground = S - 14;
  p.fillStyle = "rgba(0,0,0,0.35)"; p.beginPath(); p.ellipse(cx, ground - 2, 90, 10, 0, 0, Math.PI * 2); p.fill();
  outlined(p, () => { p.rect(cx - 70, ground - 70, 140, 70); }, "#5A5650");
  outlined(p, () => { p.rect(cx - 86, ground - 86, 172, 20); }, "#7A7670");
  p.fillStyle = "#E8E0C8";                                                // a cloth
  p.beginPath(); p.moveTo(cx - 60, ground - 86); p.lineTo(cx + 60, ground - 86); p.lineTo(cx + 54, ground - 40); p.lineTo(cx - 54, ground - 40); p.fill();
  for (const dx of [-44, 44]) {                                           // candles
    outlined(p, () => { p.rect(cx + dx - 6, ground - 130, 12, 44); }, "#F0E8D0", "#5A5040", 2);
    const g = p.createRadialGradient(cx + dx, ground - 140, 2, cx + dx, ground - 140, 20);
    g.addColorStop(0, "#FFF0A0"); g.addColorStop(0.4, "rgba(255,180,60,0.8)"); g.addColorStop(1, "rgba(255,140,40,0)");
    p.fillStyle = g; p.beginPath(); p.arc(cx + dx, ground - 140, 20, 0, Math.PI * 2); p.fill();
  }
  outlined(p, () => { p.rect(cx - 5, ground - 160, 10, 70); p.rect(cx - 26, ground - 140, 52, 10); }, "#E8C040", "#6A4A08", 2);   // a symbol
  return c;
};

CM.art.lever = function (pulled) {                                         // on a wall: a bracket and a handle
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE;
  p.clearRect(0, 0, S, S);
  outlined(p, () => { p.roundRect(70, 90, 116, 90, 10); }, "#4A4A52", "#16161A", 4);
  for (const [x, y] of [[84, 104], [172, 104], [84, 166], [172, 166]]) { p.fillStyle = "#8A8A92"; p.beginPath(); p.arc(x, y, 5, 0, Math.PI * 2); p.fill(); }
  p.fillStyle = "#101014"; p.fillRect(118, 112, 20, 46);
  p.save(); p.translate(128, 135); p.rotate(pulled ? 0.9 : -0.9);
  p.strokeStyle = "#16161A"; p.lineWidth = 16; p.lineCap = "round"; p.beginPath(); p.moveTo(0, 0); p.lineTo(0, -70); p.stroke();
  p.strokeStyle = "#8A6A30"; p.lineWidth = 10; p.beginPath(); p.moveTo(0, 0); p.lineTo(0, -70); p.stroke();
  p.fillStyle = "#C83030"; p.beginPath(); p.arc(0, -74, 13, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#16161A"; p.lineWidth = 3; p.stroke();
  p.restore();
  return c;
};

CM.art.carving = function () {                                            // a plaque of runes set into the wall
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(31);
  p.clearRect(0, 0, S, S);
  outlined(p, () => { p.roundRect(40, 60, S - 80, S - 120, 8); }, "#5E5650", "#1A1612", 4);
  p.fillStyle = "#2A2420";
  p.font = "bold 18px Georgia"; p.textAlign = "left"; p.textBaseline = "top";
  const runes = "ᚠᚢᚦᚨᚱᚷᚹᚾᛁᛇᛋᛏᛒᛖᛚᛟᛠᛦ";
  for (let row = 0; row < 5; row++) {
    let line = "";
    const n = 8 + rnd.int(0, 3);
    for (let i = 0; i < n; i++) line += runes[rnd.int(0, runes.length - 1)] + (rnd.chance(0.2) ? " " : "");
    p.fillText(line, 54, 74 + row * 24);
  }
  return c;
};

CM.art.stairsUp = function (theme) {                                       // a ladder up into a hole in the ceiling
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, cx = S / 2;
  p.clearRect(0, 0, S, S);
  p.fillStyle = "#050403"; p.beginPath(); p.ellipse(cx, 26, 70, 22, 0, 0, Math.PI * 2); p.fill();
  p.strokeStyle = rgb(theme.ceiling, 1.3); p.lineWidth = 6; p.stroke();
  p.strokeStyle = "#A07840"; p.lineWidth = 11; p.lineCap = "round";
  p.beginPath(); p.moveTo(cx - 34, S - 10); p.lineTo(cx - 34, 20); p.moveTo(cx + 34, S - 10); p.lineTo(cx + 34, 20); p.stroke();
  p.lineWidth = 8;
  for (let y = 40; y < S - 10; y += 30) { p.beginPath(); p.moveTo(cx - 34, y); p.lineTo(cx + 34, y); p.stroke(); }
  return c;
};

CM.art.key = function () {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, cx = S / 2, ground = S - 14;
  p.clearRect(0, 0, S, S);
  p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(cx, ground - 4, 60, 8, 0, 0, Math.PI * 2); p.fill();
  p.save(); p.translate(cx, ground - 30); p.rotate(-0.5);
  p.strokeStyle = "#1A1410"; p.lineWidth = 22; p.lineCap = "round"; p.beginPath(); p.moveTo(-60, 0); p.lineTo(50, 0); p.stroke();
  p.strokeStyle = "#D8B040"; p.lineWidth = 14; p.beginPath(); p.moveTo(-60, 0); p.lineTo(50, 0); p.stroke();
  p.lineWidth = 14; p.beginPath(); p.moveTo(30, 0); p.lineTo(30, 22); p.moveTo(50, 0); p.lineTo(50, 18); p.stroke();
  p.strokeStyle = "#1A1410"; p.lineWidth = 22; p.beginPath(); p.arc(-78, 0, 22, 0, Math.PI * 2); p.stroke();
  p.strokeStyle = "#D8B040"; p.lineWidth = 12; p.beginPath(); p.arc(-78, 0, 22, 0, Math.PI * 2); p.stroke();
  p.restore();
  return c;
};

CM.art.secretWall = function (theme, seed) {                               // a wall like the others, with a hairline round a door's shape
  const c = CM.art.wall(theme, seed, false), p = c.getContext("2d"), S = ART_SIZE;
  p.strokeStyle = rgb(theme.mortar, 0.45, 0.55); p.lineWidth = 2;
  p.beginPath(); p.moveTo(52, S); p.lineTo(52, 30); p.lineTo(S - 52, 30); p.lineTo(S - 52, S); p.stroke();
  return c;
};

// ---- the heroes' portraits ----------------------------------------------------------------------------------------
CM.art.portrait = function (cls, size = 56) {
  const c = artCanvas(size), p = c.getContext("2d"), s = size / 56;
  p.scale(s, s);
  p.fillStyle = { Knight: "#3A3E4A", Rogue: "#2E3A2A", Cleric: "#4A3E2A", Mage: "#2E2A4A", Paladin: "#4A3A2A", Ranger: "#2A3A2E",
    Druid: "#3A4A2A", Bard: "#4A2A3A" }[cls] || "#333";
  p.fillRect(0, 0, 56, 56);
  const skin = "#E0B890";
  p.fillStyle = { Knight: "#8A9098", Rogue: "#3A4A30", Cleric: "#E8E0D0", Mage: "#4A3A8A", Paladin: "#C8C0A0", Ranger: "#4A6A3A",
    Druid: "#6A7A3A", Bard: "#8A3A5A" }[cls] || "#555";
  p.fillRect(8, 36, 40, 24);                                            // shoulders
  if (cls === "Paladin") {
    outlined(p, () => { p.roundRect(14, 8, 28, 32, 6); }, "#D8D0B8", "#5A5040", 2);   // a helm with a gold cross
    p.fillStyle = "#1A1C22"; p.fillRect(16, 22, 24, 5);
    p.fillStyle = "#E8C040"; p.fillRect(26, 6, 4, 16); p.fillRect(21, 11, 14, 3);
  } else if (cls === "Ranger") {
    outlined(p, () => { p.moveTo(28, 6); p.lineTo(44, 28); p.lineTo(44, 40); p.lineTo(12, 40); p.lineTo(12, 28); }, "#3A5A2A", "#1A2A14", 2);   // a hood
    p.fillStyle = skin; p.fillRect(20, 24, 16, 12);
    p.fillStyle = "#3A2A1A"; p.fillRect(22, 28, 3, 3); p.fillRect(31, 28, 3, 3);
    p.strokeStyle = "#8A6A30"; p.lineWidth = 2; p.beginPath(); p.arc(44, 30, 16, -1.3, 1.3); p.stroke();   // a bow over the shoulder
  } else if (cls === "Druid") {
    outlined(p, () => { p.arc(28, 24, 14, 0, Math.PI * 2); }, skin, "#5A3A20", 2);
    p.fillStyle = "#7A5A3A"; p.fillRect(16, 34, 24, 12);                  // a beard
    p.fillStyle = "#4A8A3A";                                              // a crown of leaves
    for (let i = 0; i < 7; i++) { p.beginPath(); p.ellipse(14 + i * 5, 12, 4, 2.5, (i - 3) * 0.3, 0, Math.PI * 2); p.fill(); }
    p.fillStyle = "#3A2A1A"; p.fillRect(22, 22, 3, 3); p.fillRect(31, 22, 3, 3);
  } else if (cls === "Bard") {
    outlined(p, () => { p.arc(28, 26, 13, 0, Math.PI * 2); }, skin, "#5A3A20", 2);
    outlined(p, () => { p.moveTo(10, 16); p.lineTo(46, 14); p.lineTo(40, 8); p.lineTo(16, 10); }, "#8A2A4A", "#3A1020", 2);   // a feathered cap
    p.strokeStyle = "#E8E0A0"; p.lineWidth = 2; p.beginPath(); p.moveTo(40, 10); p.quadraticCurveTo(50, 2, 52, 10); p.stroke();
    p.fillStyle = "#3A2A1A"; p.fillRect(22, 24, 3, 3); p.fillRect(31, 24, 3, 3);
    p.fillStyle = "#E8C040"; p.fillRect(36, 40, 10, 12); p.fillStyle = "#6A4A20"; p.fillRect(38, 34, 2, 10);   // a lute
  } else if (cls === "Knight") {
    outlined(p, () => { p.roundRect(14, 8, 28, 32, 8); }, "#B8BEC8", "#2A2E36", 2);
    p.fillStyle = "#1A1C22"; p.fillRect(16, 22, 24, 5);                 // the visor's slit
    p.fillStyle = "#C83030"; p.fillRect(26, 2, 4, 10);                  // a plume
  } else if (cls === "Rogue") {
    outlined(p, () => { p.moveTo(28, 4); p.lineTo(46, 30); p.lineTo(46, 42); p.lineTo(10, 42); p.lineTo(10, 30); }, "#2A3A22", "#101810", 2);
    p.fillStyle = skin; p.fillRect(20, 24, 16, 10);
    p.fillStyle = "#FFE040"; p.fillRect(22, 27, 4, 3); p.fillRect(30, 27, 4, 3);
    p.fillStyle = "#4A2A1A"; p.fillRect(18, 34, 20, 8);                 // a scarf
  } else if (cls === "Cleric") {
    outlined(p, () => { p.arc(28, 24, 14, 0, Math.PI * 2); }, skin, "#5A3A20", 2);
    p.fillStyle = "#E8C040"; p.fillRect(14, 12, 28, 3);                 // a circlet
    p.fillStyle = "#3A2A1A"; p.fillRect(22, 21, 3, 3); p.fillRect(31, 21, 3, 3);
    p.fillStyle = "#E8C040"; p.fillRect(26, 40, 4, 14); p.fillRect(21, 44, 14, 4);   // a holy symbol
  } else {
    outlined(p, () => { p.moveTo(28, 0); p.lineTo(44, 26); p.lineTo(12, 26); }, "#4A3A9A", "#201848", 2);
    p.fillStyle = "#5A4AB0"; p.fillRect(8, 24, 40, 4);                  // the brim
    outlined(p, () => { p.arc(28, 34, 10, 0, Math.PI * 2); }, skin, "#5A3A20", 2);
    p.fillStyle = "#D0D0D8"; p.fillRect(20, 40, 16, 12);                // a beard
    p.fillStyle = "#3A2A1A"; p.fillRect(23, 32, 3, 3); p.fillRect(30, 32, 3, 3);
  }
  return c;
};

// the window's icon, for the browser tab
CM.art.icon = function () {
  const c = artCanvas(32), p = c.getContext("2d");
  p.fillStyle = "#1A1410"; p.fillRect(1, 1, 30, 30);
  p.fillStyle = "#6A5A48";
  p.beginPath(); p.moveTo(1, 1); p.lineTo(10, 8); p.lineTo(10, 24); p.lineTo(1, 31); p.fill();
  p.beginPath(); p.moveTo(31, 1); p.lineTo(22, 8); p.lineTo(22, 24); p.lineTo(31, 31); p.fill();
  p.fillStyle = "#4A3E32"; p.fillRect(10, 8, 12, 16);
  p.strokeStyle = "#E8E8F0"; p.lineWidth = 2; p.beginPath(); p.moveTo(9, 26); p.lineTo(23, 6); p.stroke();
  p.strokeStyle = "#F0C040"; p.beginPath(); p.moveTo(10, 20); p.lineTo(16, 24); p.stroke();
  return c.toDataURL();
};

// ---- the whole set for a depth, as texture-array layers -------------------------------------------------------------
CM.art.build = function (theme) {
  const layers = [], index = {};
  const add = (name, canvas) => { index[name] = layers.length; layers.push(canvas); };
  const seed = CM.hashSeed(theme.name);
  add("wall", CM.art.wall(theme, seed + 1, false));
  add("wall2", CM.art.wall(theme, seed + 2, false));
  add("wallbones", CM.art.wall(theme, seed + 3, true));
  add("floor", CM.art.floor(theme, seed + 4));
  add("ceiling", CM.art.ceiling(theme, seed + 5));
  add("wallsecret", CM.art.secretWall(theme, seed + 6));
  add("chest", CM.art.chest());
  add("hatch", CM.art.hatch(theme));
  add("door", CM.art.door("closed"));
  add("door_locked", CM.art.door("locked"));
  add("door_open", CM.art.door("open"));
  add("gate", CM.art.gate(false));
  add("gate_open", CM.art.gate(true));
  add("pit", CM.art.pit(theme));
  add("trapdoor", CM.art.pit(theme, "trapdoor"));
  add("teleporter", CM.art.teleporter());
  add("fountain", CM.art.fountain(false));
  add("fountain_dry", CM.art.fountain(true));
  add("altar", CM.art.altar());
  add("lever", CM.art.lever(false));
  add("lever_pulled", CM.art.lever(true));
  add("carving", CM.art.carving());
  add("stairs_up", CM.art.stairsUp(theme));
  add("key", CM.art.key());
  for (const m of CM.MONSTERS) add(`monster:${m.name}`, CM.art.monster(m));
  add(`monster:${CM.BOSS.name}`, CM.art.monster(CM.BOSS, true));
  return { layers, index, size: ART_SIZE };
};
