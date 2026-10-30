"use strict";
// Everything the game shows in its Drawn theme is painted here in code - the stone of each depth, the chests and
// hatches, every monster, the heroes' portraits. Textures and sprites are 256 x 256 and go to the renderer as the
// layers of one texture array; CM.art.buildDrawn(theme) returns {layers: [canvas...], index: {name: n}}. The other
// themes (pixel tiles, photographed stone) are in 36-looks.js, which also defines CM.art.build(theme, look).
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

// a monster, from its row in CM.MONSTERS: a body shape, a head, what it holds, its colour and eyes - and the finish:
// a sheen where the torch catches it, fur or scales or a hide and belt, its skin (stone cracks, warts, rot), brows
// drawn down and a grim mouth with teeth or fangs
// pose: "idle" (as drawn), "idle2" (the weight on the other foot: a breath, a shift), "attack" (leaning in, the
// weapon arm up) - the Drawn theme's frames, the same picture under a different hand (36-looks.js keeps the layers)
CM.art.monster = function (m, big = false, pose = "idle") {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, cx = S / 2, ground = S - 14, rndm = new CM.Random(CM.hashSeed(m.name));
  const col = m.colour, dark = shaded(p, col, 0.65), light = shaded(p, col, 1.3);
  const bodies = { beast: [150, 70], small: [66, 76], biped: [84, 100], thin: [58, 100], wide: [130, 112], tall: [78, 140], ghost: [90, 140] };
  const [bw, bh] = bodies[m.body] || bodies.biped;
  const scale = big === true ? 1.12 : typeof big === "number" ? big : 1;
  p.translate(cx, ground); p.scale(scale, scale); p.translate(-cx, -ground);
  if (pose === "idle2") { p.translate(cx, ground); p.transform(1, 0, -0.04, 0.97, 0, 0); p.translate(-cx, -ground); }      // (a shift of the weight, a breath out)
  else if (pose === "attack") { p.translate(cx, ground); p.transform(1.06, 0, 0.18, 1.0, 0, 6); p.translate(-cx, -ground); }   // (leaning in)
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
  if (m.body !== "ghost") {
    // the finish: a sheen where the torch catches; fur on a beast, scales on a wyvern; a belt and the hide's seams on
    // whatever carries a weapon; and the skin, where the kind has one
    const sheen = p.createRadialGradient(cx - bw * 0.22, bodyTop + bh * 0.22, 2, cx - bw * 0.22, bodyTop + bh * 0.22, bw * 0.55);
    sheen.addColorStop(0, "rgba(255,255,255,0.26)"); sheen.addColorStop(1, "rgba(255,255,255,0)");
    p.fillStyle = sheen; p.fillRect(cx - bw / 2 - 12, bodyTop - 4, bw + 24, bh + 8);
    p.lineCap = "round";
    if (m.body === "beast") {
      p.strokeStyle = dark; p.lineWidth = 2;
      if (ex.includes("wings")) {                                         // scales, in rows
        for (let r = 0; r < 4; r++) for (let i = -3; i <= 3; i++) { p.beginPath(); p.arc(cx + i * 18 + (r % 2) * 9, bodyTop + 14 + r * 13, 8, Math.PI * 0.15, Math.PI * 0.85); p.stroke(); }
      } else {                                                            // fur, along the back and the flanks
        for (let i = 0; i < 30; i++) {
          const a = -Math.PI * 0.95 + i * (Math.PI * 0.9 / 29), x = cx + Math.cos(a) * bw / 2, y = bodyTop + bh / 2 + Math.sin(a) * bh / 2;
          p.beginPath(); p.moveTo(x, y); p.lineTo(x + Math.cos(a) * 7 + (rndm.next() - 0.5) * 4, y + Math.sin(a) * 7 - 3); p.stroke();
        }
      }
    } else if (ex.some((e) => ["sword", "dagger", "club", "axe", "bow"].includes(e)) && m.head !== "skull" && m.body !== "tall") {
      p.fillStyle = "#2A1C10"; p.fillRect(cx - bw / 2 + 4, bodyTop + bh * 0.62, bw - 8, 9);                 // a belt
      p.fillStyle = "#C8A040"; p.fillRect(cx - 6, bodyTop + bh * 0.62 - 1, 12, 11);
      p.strokeStyle = dark; p.lineWidth = 2;
      p.beginPath(); p.moveTo(cx, bodyTop + 12); p.lineTo(cx, bodyTop + bh * 0.58); p.stroke();              // the seam down the chest
      for (const side of [-1, 1]) { p.beginPath(); p.moveTo(cx + side * bw * 0.18, bodyTop + 22); p.quadraticCurveTo(cx + side * bw * 0.3, bodyTop + bh * 0.35, cx + side * bw * 0.16, bodyTop + bh * 0.52); p.stroke(); }
    }
    if (m.skin === "stone") { for (let i = 0; i < 6; i++) crack(p, rndm, cx + (rndm.next() - 0.5) * bw * 0.8, bodyTop + 6 + rndm.next() * (bh - 12), 24, "#2A2A30"); }
    else if (m.skin === "warts") { p.fillStyle = dark; for (let i = 0; i < 14; i++) { p.beginPath(); p.arc(cx + (rndm.next() - 0.5) * bw * 0.85, bodyTop + 10 + rndm.next() * (bh - 20), 3 + rndm.next() * 3, 0, Math.PI * 2); p.fill(); } }
    else if (m.skin === "rot") { p.fillStyle = "rgba(70,120,50,0.55)"; for (let i = 0; i < 6; i++) { p.beginPath(); p.ellipse(cx + (rndm.next() - 0.5) * bw * 0.8, bodyTop + 12 + rndm.next() * (bh - 24), 8 + rndm.next() * 8, 5 + rndm.next() * 5, rndm.next() * 3, 0, Math.PI * 2); p.fill(); } }
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
    } else if (ex.includes("hammer")) {                                   // a maul: a long haft and a block of iron
      p.strokeStyle = "#1A1410"; p.lineWidth = 11; p.beginPath(); p.moveTo(hx, hy); p.lineTo(hx + 10, hy - 96); p.stroke();
      p.strokeStyle = "#4A3A2A"; p.lineWidth = 7; p.beginPath(); p.moveTo(hx, hy); p.lineTo(hx + 10, hy - 96); p.stroke();
      outlined(p, () => { p.roundRect(hx - 16, hy - 112, 54, 30, 4); }, "#6A6E78", "#1A1410", 3);
      p.fillStyle = "#9AA0AA"; p.fillRect(hx - 12, hy - 108, 46, 6);
    }
    if (ex.includes("shield")) {                                          // a kite shield on the other arm
      const sx = cx - bw / 2 - armW / 2 - 2, sy = bodyTop + 30;
      outlined(p, () => { p.moveTo(sx - 30, sy); p.lineTo(sx + 30, sy); p.lineTo(sx + 30, sy + 40); p.quadraticCurveTo(sx + 30, sy + 80, sx, sy + 96); p.quadraticCurveTo(sx - 30, sy + 80, sx - 30, sy + 40); }, "#4A5A64", "#1A1410", 4);
      p.strokeStyle = "#8A9AA4"; p.lineWidth = 5; p.beginPath(); p.moveTo(sx, sy + 8); p.lineTo(sx, sy + 84); p.moveTo(sx - 24, sy + 30); p.lineTo(sx + 24, sy + 30); p.stroke();
    }
    if (ex.includes("glow")) {                                            // the forge in its chest, behind a grate
      const fg = p.createRadialGradient(cx, bodyTop + bh * 0.45, 2, cx, bodyTop + bh * 0.45, bw * 0.34);
      fg.addColorStop(0, "rgba(255,240,170,1)"); fg.addColorStop(0.35, "rgba(255,150,40,0.9)"); fg.addColorStop(1, "rgba(255,80,0,0)");
      p.fillStyle = fg; p.fillRect(cx - bw / 2, bodyTop, bw, bh);
      p.strokeStyle = "#1A1410"; p.lineWidth = 3;
      for (let i = -2; i <= 2; i++) { p.beginPath(); p.moveTo(cx - bw * 0.3, bodyTop + bh * 0.3 + i * 10); p.lineTo(cx + bw * 0.3, bodyTop + bh * 0.3 + i * 10); p.stroke(); }
    }
  }
  if (ex.includes("weed")) {                                              // weed down the shoulders, and water running off
    p.strokeStyle = "#3A6A3A"; p.lineWidth = 5; p.lineCap = "round";
    for (let i = 0; i < 7; i++) { const x = cx - bw / 2 + 6 + i * (bw - 12) / 6; p.beginPath(); p.moveTo(x, bodyTop + 2); p.quadraticCurveTo(x + (i % 2 ? 8 : -8), bodyTop + 30, x + (i % 2 ? -4 : 6), bodyTop + 40 + (i % 3) * 14); p.stroke(); }
    p.fillStyle = "rgba(150,210,230,0.8)";
    for (let i = 0; i < 6; i++) { p.beginPath(); p.ellipse(cx - bw / 2 + 10 + i * (bw - 20) / 5, bodyBottom + 10 + (i % 2) * 16, 3, 6, 0, 0, Math.PI * 2); p.fill(); }
  }
  if (ex.includes("swarm")) {                                             // small rats about its feet
    for (let i = 0; i < 5; i++) {
      const rx = cx - 90 + i * 45 + (i % 2) * 10, ry = ground - 8 - (i % 2) * 6;
      outlined(p, () => { p.ellipse(rx, ry, 18, 9, 0, 0, Math.PI * 2); }, dark, "#1A1410", 2);
      outlined(p, () => { p.ellipse(rx + 16, ry - 3, 8, 6, 0, 0, Math.PI * 2); }, dark, "#1A1410", 2);
      p.fillStyle = m.eyes; p.beginPath(); p.arc(rx + 19, ry - 4, 1.6, 0, Math.PI * 2); p.fill();
      p.strokeStyle = dark; p.lineWidth = 2; p.beginPath(); p.moveTo(rx - 16, ry); p.quadraticCurveTo(rx - 30, ry - 10, rx - 34, ry + 4); p.stroke();
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
    if (m.head === "helm") {                                            // a great helm: steel, a visor slit, the eyes behind it
      outlined(p, () => { p.moveTo(hx2 - headR - 4, hy2 + headR * 0.95); p.lineTo(hx2 - headR - 4, hy2 - headR * 0.2); p.arc(hx2, hy2 - headR * 0.2, headR + 4, Math.PI, 0); p.lineTo(hx2 + headR + 4, hy2 + headR * 0.95); }, "#8A94A0", "#1A1410", 3);
      p.fillStyle = "#1A1410"; p.fillRect(hx2 - headR * 0.8, hy2 - headR * 0.14, headR * 1.6, headR * 0.3);
      p.fillStyle = "#6A7480"; p.fillRect(hx2 - 3, hy2 - headR * 0.9, 6, headR * 1.75);
    }
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
  const eyeY = m.head === "hood" ? hy2 + 2 : m.head === "helm" ? hy2 + 1 : hy2 - (m.head === "snout" ? 6 : 2), eyeDX = headR * 0.42, eyeR = headR * (m.head === "skull" ? 0.18 : 0.14);
  p.save();
  p.shadowColor = m.eyes; p.shadowBlur = 14;
  p.fillStyle = m.eyes;
  for (const side of [-1, 1]) { p.beginPath(); p.arc(hx2 + side * eyeDX, eyeY, eyeR, 0, Math.PI * 2); p.fill(); }
  p.restore();
  if (m.head !== "skull" && m.head !== "hood" && m.head !== "helm" && !m.calm) {   // brows drawn down, and a grim mouth (not on the dungeon's people)
    p.strokeStyle = "#1A1410"; p.lineWidth = 3; p.lineCap = "round";
    for (const side of [-1, 1]) { p.beginPath(); p.moveTo(hx2 + side * headR * 0.66, eyeY - headR * 0.36); p.lineTo(hx2 + side * headR * 0.2, eyeY - headR * 0.2); p.stroke(); }
    const my = m.head === "snout" ? hy2 + headR * 0.74 : hy2 + headR * 0.46, fangs = m.head === "pale";
    p.lineWidth = 2.5; p.beginPath(); p.moveTo(hx2 - headR * 0.34, my + 3); p.quadraticCurveTo(hx2, my - 5, hx2 + headR * 0.34, my + 3); p.stroke();
    if (m.head === "snout" || m.head === "tusks" || fangs) {             // teeth, or fangs
      p.fillStyle = "#F0ECE0";
      for (const t of fangs ? [-0.18, 0.18] : [-0.26, -0.09, 0.09, 0.26]) {
        p.beginPath(); p.moveTo(hx2 + t * headR - 3, my + 1); p.lineTo(hx2 + t * headR + 3, my + 1); p.lineTo(hx2 + t * headR, my + (fangs ? 12 : 7)); p.fill();
      }
    }
  }
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
  } else if (kind === "riddle") {                                       // written over with runes that glow
    p.save(); p.shadowColor = "#80E0FF"; p.shadowBlur = 14; p.strokeStyle = "#B0F0FF"; p.lineWidth = 4; p.lineCap = "round"; p.lineJoin = "round";
    const r2 = new CM.Random(44);
    for (let i = 0; i < 9; i++) {
      const x = 44 + (i % 3) * 58, y = 78 + Math.floor(i / 3) * 44;
      p.beginPath(); p.moveTo(x, y); p.lineTo(x + 12 + r2.next() * 18, y + 4 + r2.next() * 8); p.lineTo(x + 4 + r2.next() * 8, y + 24);
      if (r2.chance(0.5)) p.lineTo(x + 26, y + 26 - r2.next() * 10);
      p.stroke();
    }
    p.restore();
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

// the town's things: a house front with a door and a sign, a foundation of low stones, the square's well
CM.art.treeWall = function (theme, seed) {                               // the Wood's wall: a trunk and its crown against the dark of the trees behind
  const c = artCanvas(), p = c.getContext("2d"), rnd = new CM.Random(seed), S = ART_SIZE;
  p.fillStyle = rgb(theme.mortar); p.fillRect(0, 0, S, S);
  for (let i = 0; i < 60; i++) { p.fillStyle = `rgba(${theme.stone[0] + rnd.int(-20, 20)},${theme.stone[1] + rnd.int(-20, 20)},${theme.stone[2] + rnd.int(-10, 10)},0.7)`; p.beginPath(); p.arc(rnd.int(0, S), rnd.int(0, S * 0.7), rnd.int(14, 30), 0, Math.PI * 2); p.fill(); }
  const tx = S / 2 + rnd.int(-20, 20), tw = 34 + rnd.int(0, 12);
  p.fillStyle = "#4A3220"; p.fillRect(tx - tw / 2, S * 0.3, tw, S * 0.7);
  p.fillStyle = "#3A2614"; for (let y = S * 0.3; y < S; y += 14) p.fillRect(tx - tw / 2 + rnd.int(0, 6), y, tw - rnd.int(4, 12), 3);
  p.fillStyle = `rgba(${theme.moss[0]},${theme.moss[1]},${theme.moss[2]},0.85)`; for (let i = 0; i < 14; i++) { p.beginPath(); p.arc(tx + rnd.int(-60, 60), S * 0.18 + rnd.int(-30, 30), rnd.int(20, 40), 0, Math.PI * 2); p.fill(); }
  return c;
};
CM.art.vein = function (colour) {                                        // ore in the rock: a lump of stone with the metal's flecks
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(CM.hashSeed(colour));
  p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(S / 2, S - 14, 70, 9, 0, 0, Math.PI * 2); p.fill();
  p.fillStyle = "#6A625A"; p.beginPath(); p.moveTo(60, 236); p.lineTo(70, 150); p.lineTo(128, 120); p.lineTo(190, 150); p.lineTo(200, 236); p.closePath(); p.fill();
  p.fillStyle = "#4A443E"; p.beginPath(); p.moveTo(60, 236); p.lineTo(70, 150); p.lineTo(110, 236); p.closePath(); p.fill();
  p.fillStyle = colour; for (let i = 0; i < 26; i++) { p.beginPath(); p.arc(80 + rnd.int(0, 100), 140 + rnd.int(0, 86), rnd.int(3, 7), 0, Math.PI * 2); p.fill(); }
  return c;
};
CM.art.house = function (stage = 4) {                                   // 1 a frame; 2 a roofed house; 3 with its sign; 4 with a lit window
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE;
  p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(S / 2, S - 14, 100, 9, 0, 0, Math.PI * 2); p.fill();
  if (stage >= 2) p.fillStyle = "#B89C78", p.fillRect(38, 96, 180, 146);   // the wall, limewashed
  p.fillStyle = "#6E4A2A"; for (const x of [38, 124, 212]) p.fillRect(x, 96, 6, 146); p.fillRect(38, 150, 180, 6); p.fillRect(38, 96, 180, 6);   // the timbers (a frame alone, at the first stage)
  if (stage >= 2) { p.fillStyle = "#7A4A2A"; p.beginPath(); p.moveTo(22, 100); p.lineTo(128, 30); p.lineTo(234, 100); p.closePath(); p.fill(); p.fillStyle = "#5A3418"; for (let y = 40; y < 100; y += 12) p.fillRect(22 + (100 - y) * 0.9, y, 212 - (100 - y) * 1.8, 3); }   // the roof
  else { p.strokeStyle = "#6E4A2A"; p.lineWidth = 6; p.beginPath(); p.moveTo(40, 98); p.lineTo(128, 36); p.lineTo(216, 98); p.stroke(); }   // the roof's beams, bare
  p.fillStyle = "#4A2E16"; p.fillRect(108, 166, 40, 76);                 // the door
  p.fillStyle = "#D8B040"; p.beginPath(); p.arc(140, 206, 3, 0, Math.PI * 2); p.fill();
  if (stage >= 2) { p.fillStyle = stage >= 4 ? "#F0D080" : "#A8C8E0"; p.fillRect(58, 166, 30, 30); p.fillRect(168, 166, 30, 30); p.strokeStyle = "#4A2E16"; p.lineWidth = 3; p.strokeRect(58, 166, 30, 30); p.strokeRect(168, 166, 30, 30); p.beginPath(); p.moveTo(73, 166); p.lineTo(73, 196); p.moveTo(183, 166); p.lineTo(183, 196); p.stroke(); }   // the windows (lit, at the last stage)
  if (stage >= 3) { p.fillStyle = "#8A6A3A"; p.fillRect(92, 108, 72, 26); p.strokeStyle = "#3A2410"; p.lineWidth = 2; p.strokeRect(92, 108, 72, 26); }   // the sign
  return c;
};
CM.art.foundation = function () {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE;
  p.fillStyle = "rgba(0,0,0,0.25)"; p.beginPath(); p.ellipse(S / 2, S - 14, 100, 9, 0, 0, Math.PI * 2); p.fill();
  p.fillStyle = "#9A8A74"; p.fillRect(40, 196, 176, 46);
  p.fillStyle = "#7A6A56"; for (let i = 0; i < 6; i++) p.fillRect(44 + i * 29, 200 + (i % 2) * 20, 24, 18);
  p.strokeStyle = "#5A4A3A"; p.lineWidth = 2; p.strokeRect(40, 196, 176, 46);
  p.fillStyle = "#6E4A2A"; p.fillRect(60, 150, 6, 50); p.fillRect(190, 150, 6, 50);   // two posts, waiting for a roof
  return c;
};
CM.art.well = function () {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE;
  p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(S / 2, S - 14, 70, 9, 0, 0, Math.PI * 2); p.fill();
  p.fillStyle = "#8A8070"; p.fillRect(72, 176, 112, 60);                  // the ring
  p.fillStyle = "#6A6054"; for (let i = 0; i < 4; i++) p.fillRect(76 + i * 28, 182 + (i % 2) * 24, 22, 18);
  p.fillStyle = "#1A2030"; p.beginPath(); p.ellipse(S / 2, 176, 54, 12, 0, 0, Math.PI * 2); p.fill();
  p.fillStyle = "#6E4A2A"; p.fillRect(80, 90, 8, 90); p.fillRect(168, 90, 8, 90); p.fillRect(74, 84, 108, 8);   // the posts and the beam
  p.fillStyle = "#7A4A2A"; p.beginPath(); p.moveTo(64, 92); p.lineTo(128, 50); p.lineTo(192, 92); p.closePath(); p.fill();   // the little roof
  p.fillStyle = "#4A2E16"; p.fillRect(124, 92, 6, 60); p.fillStyle = "#8A7A5A"; p.fillRect(112, 150, 30, 22);   // the rope and the bucket
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

CM.art.phylactery = function () {                                          // the box from the east, on a plinth, lit from within
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, cx = S / 2, ground = S - 14;
  p.clearRect(0, 0, S, S);
  p.fillStyle = "rgba(0,0,0,0.35)"; p.beginPath(); p.ellipse(cx, ground - 2, 70, 9, 0, 0, Math.PI * 2); p.fill();
  outlined(p, () => { p.rect(cx - 50, ground - 60, 100, 60); }, "#4A4A52");
  outlined(p, () => { p.rect(cx - 60, ground - 70, 120, 14); }, "#5E5E68");
  const g = p.createRadialGradient(cx, ground - 110, 4, cx, ground - 110, 70);
  g.addColorStop(0, "rgba(120,220,255,0.9)"); g.addColorStop(0.5, "rgba(60,140,200,0.35)"); g.addColorStop(1, "rgba(40,80,140,0)");
  p.fillStyle = g; p.beginPath(); p.arc(cx, ground - 110, 70, 0, Math.PI * 2); p.fill();
  outlined(p, () => { p.rect(cx - 34, ground - 130, 68, 56); }, "#1E2A3A", "#0A0E14", 4);
  p.strokeStyle = "#8AC8F0"; p.lineWidth = 3;
  p.strokeRect(cx - 28, ground - 124, 56, 44);
  p.beginPath(); p.moveTo(cx - 34, ground - 102); p.lineTo(cx + 34, ground - 102); p.stroke();
  p.fillStyle = "#C8ECFF"; p.beginPath(); p.arc(cx, ground - 102, 7, 0, Math.PI * 2); p.fill();   // the clasp, glowing
  return c;
};

CM.art.secretWall = function (theme, seed) {                               // a wall like the others, with a hairline round a door's shape
  const c = CM.art.wall(theme, seed, false), p = c.getContext("2d"), S = ART_SIZE;
  p.strokeStyle = rgb(theme.mortar, 0.45, 0.55); p.lineWidth = 2;
  p.beginPath(); p.moveTo(52, S); p.lineTo(52, 30); p.lineTo(S - 52, 30); p.lineTo(S - 52, S); p.stroke();
  return c;
};

// ---- the heroes' portraits (the drawn ones; 36-looks.js picks by theme) ---------------------------------------------
CM.art.portraitDrawn = function (cls, size = 56) {
  const c = artCanvas(size), p = c.getContext("2d"), s = size / 56;
  p.scale(s, s);
  p.fillStyle = { Knight: "#3A3E4A", Rogue: "#2E3A2A", Cleric: "#4A3E2A", Mage: "#2E2A4A", Paladin: "#4A3A2A", Ranger: "#2A3A2E",
    Druid: "#3A4A2A", Bard: "#4A2A3A", Monk: "#4A3A20", Necromancer: "#2A1A3A", Artificer: "#3A3A2A" }[cls] || "#333";
  p.fillRect(0, 0, 56, 56);
  const skin = "#E0B890";
  p.fillStyle = { Knight: "#8A9098", Rogue: "#3A4A30", Cleric: "#E8E0D0", Mage: "#4A3A8A", Paladin: "#C8C0A0", Ranger: "#4A6A3A",
    Druid: "#6A7A3A", Bard: "#8A3A5A", Monk: "#C08040", Necromancer: "#3A2A5A", Artificer: "#7A5A30" }[cls] || "#555";
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
  } else if (cls === "Monk") {
    outlined(p, () => { p.arc(28, 24, 14, 0, Math.PI * 2); }, skin, "#5A3A20", 2);     // a shaven head, a red headband
    p.fillStyle = "#C03030"; p.fillRect(14, 16, 28, 5);
    p.fillStyle = "#3A2A1A"; p.fillRect(22, 24, 3, 3); p.fillRect(31, 24, 3, 3);
    p.fillStyle = "#E0B890"; p.fillRect(10, 40, 10, 10); p.fillRect(36, 40, 10, 10);   // the fists, wrapped
    p.fillStyle = "#D8D0B8"; p.fillRect(10, 44, 10, 2); p.fillRect(36, 44, 10, 2);
  } else if (cls === "Necromancer") {
    outlined(p, () => { p.moveTo(28, 2); p.lineTo(46, 30); p.lineTo(46, 42); p.lineTo(10, 42); p.lineTo(10, 30); }, "#2A1A3A", "#100818", 2);   // a deep hood
    p.fillStyle = "#E8E0D0"; p.fillRect(20, 22, 16, 14);                 // a face gone pale
    p.fillStyle = "#8040E0"; p.fillRect(22, 26, 4, 4); p.fillRect(30, 26, 4, 4);   // eyes that glow
    p.fillStyle = "#1A1020"; p.fillRect(26, 32, 4, 3);
    p.fillStyle = "#A080E0"; p.fillRect(40, 36, 3, 18);                  // a bone staff
  } else if (cls === "Artificer") {
    outlined(p, () => { p.arc(28, 26, 13, 0, Math.PI * 2); }, skin, "#5A3A20", 2);
    outlined(p, () => { p.moveTo(12, 16); p.lineTo(44, 16); p.lineTo(40, 8); p.lineTo(16, 8); }, "#5A4A30", "#2A2010", 2);   // a leather cap
    p.fillStyle = "#C8A040"; p.beginPath(); p.arc(22, 20, 5, 0, Math.PI * 2); p.arc(34, 20, 5, 0, Math.PI * 2); p.fill();   // goggles
    p.fillStyle = "#4A7A8A"; p.beginPath(); p.arc(22, 20, 3, 0, Math.PI * 2); p.arc(34, 20, 3, 0, Math.PI * 2); p.fill();
    p.fillStyle = "#3A2A1A"; p.fillRect(22, 30, 3, 3); p.fillRect(31, 30, 3, 3);
    p.fillStyle = "#B8A040"; p.fillRect(38, 40, 10, 6); p.fillRect(41, 46, 4, 8);   // a wrench
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

// ---- what flies and bursts (the effects' sprites), and the torches and water of a living dungeon -------------------
function softDot(p, cx, cy, r, inner, outer) {
  const g = p.createRadialGradient(cx, cy, 0, cx, cy, r);
  g.addColorStop(0, inner); g.addColorStop(0.45, inner); g.addColorStop(1, outer);
  p.fillStyle = g; p.beginPath(); p.arc(cx, cy, r, 0, Math.PI * 2); p.fill();
}
CM.art.fxSpark = function () { const c = artCanvas(), p = c.getContext("2d"); softDot(p, 128, 128, 120, "rgba(255,250,220,1)", "rgba(255,200,80,0)"); return c; };
CM.art.fxShard = function () {                                             // a sliver of bone
  const c = artCanvas(), p = c.getContext("2d");
  p.translate(128, 128); p.rotate(-0.6);
  outlined(p, () => { p.roundRect(-70, -18, 140, 36, 16); }, "#E8E0C8", "#6A6050", 6);
  p.fillStyle = "#B8B0A0"; p.fillRect(-60, -4, 120, 8);
  return c;
};
CM.art.fxFire = function () { const c = artCanvas(), p = c.getContext("2d"); softDot(p, 128, 140, 118, "rgba(255,120,30,0.95)", "rgba(255,60,0,0)"); softDot(p, 128, 124, 66, "rgba(255,240,160,1)", "rgba(255,180,60,0)"); return c; };
CM.art.fxFrost = function () {                                             // a six-armed crystal
  const c = artCanvas(), p = c.getContext("2d");
  softDot(p, 128, 128, 110, "rgba(200,240,255,0.6)", "rgba(120,200,255,0)");
  p.strokeStyle = "#E8FAFF"; p.lineWidth = 10; p.lineCap = "round";
  for (let i = 0; i < 6; i++) {
    const a = i * Math.PI / 3;
    p.beginPath(); p.moveTo(128, 128); p.lineTo(128 + Math.cos(a) * 95, 128 + Math.sin(a) * 95); p.stroke();
    for (const s of [-1, 1]) { p.beginPath(); p.moveTo(128 + Math.cos(a) * 60, 128 + Math.sin(a) * 60); p.lineTo(128 + Math.cos(a) * 60 + Math.cos(a + s * 0.9) * 28, 128 + Math.sin(a) * 60 + Math.sin(a + s * 0.9) * 28); p.stroke(); }
  }
  return c;
};
CM.art.fxBolt = function () {                                              // lightning, top to bottom
  const c = artCanvas(), p = c.getContext("2d"), pts = [[128, 6], [100, 90], [146, 110], [112, 180], [150, 200], [120, 250]];
  softDot(p, 128, 128, 120, "rgba(200,220,255,0.35)", "rgba(120,160,255,0)");
  p.lineCap = "round"; p.lineJoin = "round";
  for (const [w, col] of [[26, "rgba(120,170,255,0.6)"], [12, "#E8F4FF"], [5, "#FFFFFF"]]) { p.strokeStyle = col; p.lineWidth = w; p.beginPath(); pts.forEach(([x, y], i) => (i ? p.lineTo(x, y) : p.moveTo(x, y))); p.stroke(); }
  return c;
};
CM.art.fxForce = function () { const c = artCanvas(), p = c.getContext("2d"); softDot(p, 128, 128, 118, "rgba(200,120,255,0.95)", "rgba(120,40,200,0)"); softDot(p, 128, 128, 60, "rgba(255,230,255,1)", "rgba(220,160,255,0)"); return c; };
CM.art.fxHoly = function () {                                              // an eight-pointed light
  const c = artCanvas(), p = c.getContext("2d");
  softDot(p, 128, 128, 120, "rgba(255,240,180,0.7)", "rgba(255,220,120,0)");
  p.fillStyle = "#FFF8D0"; p.beginPath();
  for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4, r = i % 2 ? 34 : 112; p.lineTo(128 + Math.cos(a) * r, 128 + Math.sin(a) * r); }
  p.closePath(); p.fill();
  return c;
};
CM.art.fxArrow = function () {
  const c = artCanvas(), p = c.getContext("2d");
  p.translate(128, 128); p.rotate(-Math.PI / 4); p.lineCap = "round";
  p.strokeStyle = "#1A1410"; p.lineWidth = 14; p.beginPath(); p.moveTo(-100, 0); p.lineTo(100, 0); p.stroke();
  p.strokeStyle = "#8A6A30"; p.lineWidth = 8; p.beginPath(); p.moveTo(-100, 0); p.lineTo(80, 0); p.stroke();
  outlined(p, () => { p.moveTo(110, 0); p.lineTo(70, -18); p.lineTo(78, 0); p.lineTo(70, 18); }, "#D8DCE8", "#1A1410", 3);
  outlined(p, () => { p.moveTo(-100, 0); p.lineTo(-70, -22); p.lineTo(-50, -4); p.lineTo(-50, 4); p.lineTo(-70, 22); }, "#E8E0C0", "#1A1410", 3);
  return c;
};
CM.art.fxLeaf = function () {
  const c = artCanvas(), p = c.getContext("2d");
  p.translate(128, 128); p.rotate(0.5);
  outlined(p, () => { p.moveTo(0, -110); p.quadraticCurveTo(90, -40, 0, 110); p.quadraticCurveTo(-90, -40, 0, -110); }, "#4A9A3A", "#1A3A14", 6);
  p.strokeStyle = "#1A3A14"; p.lineWidth = 5; p.beginPath(); p.moveTo(0, -100); p.lineTo(0, 100); p.stroke();
  return c;
};
CM.art.fxRing = function () {                                              // a ring of cold light, spreading on the floor
  const c = artCanvas(), p = c.getContext("2d"), g = p.createRadialGradient(128, 128, 60, 128, 128, 124);
  g.addColorStop(0, "rgba(120,240,255,0)"); g.addColorStop(0.55, "rgba(120,240,255,0)"); g.addColorStop(0.8, "rgba(180,250,255,0.95)"); g.addColorStop(1, "rgba(120,240,255,0)");
  p.fillStyle = g; p.fillRect(0, 0, 256, 256);
  return c;
};
// a wall torch: an iron bracket and a flame that leans one way, then the other (three frames)
CM.art.torch = function (frame) {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, lean = [-1, 0, 1][frame % 3] * 18;
  p.fillStyle = "#1A1410"; p.fillRect(118, 150, 20, 90); p.fillRect(96, 230, 64, 16);
  p.fillStyle = "#3A3A42"; p.fillRect(122, 154, 12, 82);
  p.fillStyle = "#6A4A28"; p.fillRect(114, 120, 28, 40);
  const g = p.createRadialGradient(128 + lean, 100, 4, 128 + lean, 100, 90);
  g.addColorStop(0, "rgba(255,240,180,0.9)"); g.addColorStop(0.4, "rgba(255,160,40,0.55)"); g.addColorStop(1, "rgba(255,100,0,0)");
  p.fillStyle = g; p.fillRect(0, 0, S, S);
  outlined(p, () => { p.moveTo(128, 130); p.quadraticCurveTo(170 + lean, 100, 128 + lean, 30); p.quadraticCurveTo(86 + lean, 100, 128, 130); }, "#FFA030", "#C04010", 4);
  outlined(p, () => { p.moveTo(128, 126); p.quadraticCurveTo(146 + lean * 0.5, 100, 128 + lean * 0.6, 66); p.quadraticCurveTo(110 + lean * 0.5, 100, 128, 126); }, "#FFF0A0", "#FFC040", 2);
  return c;
};
// water on the floor of the flooded vaults: a dark sheet with rings of light that move from frame to frame
CM.art.water = function (frame) {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(77);
  p.fillStyle = "rgba(40,80,90,0.55)"; p.fillRect(0, 0, S, S);
  p.strokeStyle = "rgba(180,230,240,0.5)"; p.lineWidth = 3;
  for (let i = 0; i < 7; i++) { const x = rnd.next() * S, y = rnd.next() * S, r = 14 + ((rnd.next() * 40 + frame * 13) % 40); p.beginPath(); p.ellipse(x, y, r, r * 0.45, 0, 0, Math.PI * 2); p.stroke(); }
  speckle(p, rnd, S, S, 60, "rgba(220,245,255,0.8)", 0.6, 3);
  return c;
};

// ---- the guardians' lairs: a heap of bones and rags, a sunken throne, an anvil, embers in the forge-floor ---------------
CM.art.nest = function () {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(505);
  p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, S - 14, 110, 12, 0, 0, Math.PI * 2); p.fill();
  outlined(p, () => { p.moveTo(18, S - 16); p.quadraticCurveTo(60, S - 112, 128, S - 120); p.quadraticCurveTo(196, S - 112, 238, S - 16); }, "#5A4A38", "#1A1410", 4);
  p.lineCap = "round";
  for (let i = 0; i < 12; i++) {                                           // straw and rags
    p.strokeStyle = i % 3 ? "#8A6A48" : "#3A2A1C"; p.lineWidth = 4;
    const x = 40 + rnd.next() * 176, y = S - 30 - rnd.next() * 66;
    p.beginPath(); p.moveTo(x - 14, y + 4); p.lineTo(x + 14, y - 4); p.stroke();
  }
  for (let i = 0; i < 7; i++) bone(p, rnd, 50 + rnd.next() * 156, S - 44 - rnd.next() * 60, rnd.next());
  p.fillStyle = "#FF5040";
  for (let i = 0; i < 3; i++) { const x = 60 + i * 70, y = S - 60 - (i % 2) * 20; p.beginPath(); p.arc(x, y, 2.5, 0, Math.PI * 2); p.arc(x + 9, y, 2.5, 0, Math.PI * 2); p.fill(); }   // eyes in the heap
  return c;
};
CM.art.throne = function () {                                              // a stone seat, weeded, standing in water
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE;
  p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, S - 12, 90, 10, 0, 0, Math.PI * 2); p.fill();
  outlined(p, () => { p.roundRect(60, 30, 136, 190, 10); }, "#5A6A70", "#1A1410", 4);                            // the back
  outlined(p, () => { p.roundRect(44, 130, 168, 60, 8); }, "#6A7A80", "#1A1410", 4);                             // the seat
  for (const x of [44, 190]) outlined(p, () => { p.roundRect(x, 110, 22, 110, 6); }, "#4A5A60", "#1A1410", 3);     // the arms
  p.fillStyle = "#7A8A90"; p.fillRect(74, 44, 108, 70);
  p.strokeStyle = "#2A3A40"; p.lineWidth = 3;
  for (let i = 0; i < 4; i++) { p.beginPath(); p.moveTo(80, 60 + i * 14); p.lineTo(176, 60 + i * 14); p.stroke(); }   // the carving on the back
  p.strokeStyle = "#3A6A3A"; p.lineWidth = 5; p.lineCap = "round";
  for (let i = 0; i < 6; i++) { const x = 70 + i * 24; p.beginPath(); p.moveTo(x, 34); p.quadraticCurveTo(x + 6, 70, x - 4, 90 + (i % 3) * 16); p.stroke(); }   // weed
  p.fillStyle = "rgba(40,80,90,0.5)"; p.fillRect(0, S - 60, S, 60);                                               // the water it stands in
  return c;
};
CM.art.anvil = function () {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE;
  p.fillStyle = "rgba(0,0,0,0.35)"; p.beginPath(); p.ellipse(128, S - 12, 86, 10, 0, 0, Math.PI * 2); p.fill();
  outlined(p, () => { p.rect(84, S - 60, 88, 48); }, "#4A3A2A", "#1A1410", 4);                                    // the stump
  outlined(p, () => { p.moveTo(104, S - 60); p.lineTo(96, S - 100); p.lineTo(160, S - 100); p.lineTo(152, S - 60); }, "#5A5E66", "#1A1410", 4);   // the waist
  outlined(p, () => { p.moveTo(40, S - 128); p.lineTo(200, S - 128); p.lineTo(236, S - 118); p.lineTo(206, S - 100); p.lineTo(60, S - 100); p.lineTo(60, S - 112); p.lineTo(40, S - 118); }, "#7A8088", "#1A1410", 4);   // the face and the horn
  p.fillStyle = "#B0B6BE"; p.fillRect(66, S - 126, 134, 5);                                                        // the shine on the face
  softDot(p, 150, S - 140, 22, "rgba(255,200,80,0.9)", "rgba(255,120,0,0)");                                       // a spark of the forge
  return c;
};
CM.art.ember = function () {                                               // the forge-floor: fire in the cracks of dark stone
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(909);
  p.fillStyle = "rgba(20,10,8,0.45)"; p.fillRect(0, 0, S, S);
  for (let i = 0; i < 12; i++) { const x = rnd.next() * S, y = rnd.next() * S; softDot(p, x, y, 36 + rnd.next() * 34, "rgba(255,170,50,1)", "rgba(255,60,0,0)"); }
  p.strokeStyle = "rgba(255,235,150,0.95)"; p.lineWidth = 5; p.lineCap = "round";
  for (let i = 0; i < 9; i++) {
    const x = rnd.next() * S, y = rnd.next() * S;
    p.beginPath(); p.moveTo(x, y); p.lineTo(x + (rnd.next() - 0.5) * 70, y + (rnd.next() - 0.5) * 70); p.lineTo(x + (rnd.next() - 0.5) * 90, y + (rnd.next() - 0.5) * 90); p.stroke();
  }
  return c;
};

// ---- the dungeon's people and puzzles: who stands in the halls, a heap of bones, a rope, a plate in the floor ----------
CM.art.PEOPLE = {
  ghost: { name: "Ghost", colour: "#C0D4E4", body: "ghost", head: "pale", eyes: "#F0FAFF", extras: [], calm: true },
  hermit: { name: "Hermit", colour: "#8A7A5A", body: "small", head: "hood", eyes: "#E8D8A0", extras: ["staff"] },
  adventurer: { name: "Adventurer", colour: "#9A6A48", body: "biped", head: "round", eyes: "#F0E8D0", extras: ["torn"], calm: true },
};
CM.art.bones = function () {                                               // someone's, gnawed and scattered
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(313);
  p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, S - 14, 80, 10, 0, 0, Math.PI * 2); p.fill();
  for (let i = 0; i < 9; i++) bone(p, rnd, 60 + rnd.next() * 136, S - 26 - rnd.next() * 44, i === 4 ? 0.9 : 0.2);
  return c;
};
CM.art.rope = function () {                                                // a coil of rope, hanging from above and heaped on the floor
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE;
  p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, S - 14, 70, 9, 0, 0, Math.PI * 2); p.fill();
  p.strokeStyle = "#1A1410"; p.lineWidth = 16; p.lineCap = "round"; p.beginPath(); p.moveTo(136, 0); p.lineTo(132, S - 70); p.stroke();
  p.strokeStyle = "#A07840"; p.lineWidth = 10; p.beginPath(); p.moveTo(136, 0); p.lineTo(132, S - 70); p.stroke();
  for (let i = 0; i < 4; i++) {
    const y = S - 64 + i * 13, w = 58 - i * 6;
    outlined(p, () => { p.ellipse(128, y, w, 12, 0, 0, Math.PI * 2); }, "#A07840", "#1A1410", 4);
    p.strokeStyle = "#6A4A24"; p.lineWidth = 2;
    for (let a = 0; a < Math.PI * 2; a += 0.4) { p.beginPath(); p.moveTo(128 + Math.cos(a) * w, y + Math.sin(a) * 12); p.lineTo(128 + Math.cos(a + 0.12) * (w - 4), y + Math.sin(a + 0.12) * 9); p.stroke(); }
  }
  return c;
};
CM.art.plate = function (pressed) {                                        // a slab in the floor, proud of it - or sunk
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE;
  p.fillStyle = pressed ? "rgba(0,0,0,0.45)" : "rgba(0,0,0,0.25)"; p.fillRect(40, 40, S - 80, S - 80);
  outlined(p, () => { p.rect(52, 52, S - 104, S - 104); }, pressed ? "#4A4038" : "#6A5E52", "#1A1410", 5);
  p.fillStyle = pressed ? "rgba(0,0,0,0.2)" : "rgba(255,240,200,0.14)"; p.fillRect(56, 56, S - 112, 12);
  p.strokeStyle = pressed ? "#2A2420" : "#8A7E70"; p.lineWidth = 3;
  p.beginPath(); p.moveTo(76, 128); p.lineTo(S - 76, 128); p.moveTo(128, 76); p.lineTo(128, S - 76); p.stroke();   // a cross cut into it
  return c;
};

// ---- the Deep's lairs: fungus that glows, crystal that grows, the roots of the world --------------------------------------
CM.art.fungus = function () {                                              // a ring of pale caps on the floor, lit from within
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(606);
  softDot(p, 128, 128, 120, "rgba(150,230,120,0.35)", "rgba(80,160,60,0)");
  for (let i = 0; i < 9; i++) {
    const a = rnd.next() * Math.PI * 2, d = 30 + rnd.next() * 70, x = 128 + Math.cos(a) * d, y = 128 + Math.sin(a) * d, r = 10 + rnd.next() * 14;
    outlined(p, () => { p.ellipse(x, y, r, r * 0.6, 0, 0, Math.PI * 2); }, "#C8E8A0", "#3A5A2A", 2);
    p.fillStyle = "rgba(255,255,220,0.8)"; p.beginPath(); p.arc(x - r * 0.3, y - r * 0.2, r * 0.25, 0, Math.PI * 2); p.fill();
  }
  return c;
};
CM.art.crystal = function () {                                             // a cluster of violet shards, standing
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, g = S - 14;
  p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, g - 2, 70, 9, 0, 0, Math.PI * 2); p.fill();
  softDot(p, 128, 130, 110, "rgba(220,190,255,0.35)", "rgba(160,120,220,0)");
  for (const [x, h, w, lean] of [[90, 120, 26, -0.15], [128, 190, 34, 0.02], [166, 140, 28, 0.18], [112, 90, 18, -0.3], [150, 100, 20, 0.32]]) {
    outlined(p, () => { p.moveTo(x - w, g); p.lineTo(x - w * 0.6 + lean * h, g - h * 0.75); p.lineTo(x + lean * h * 1.2, g - h); p.lineTo(x + w * 0.6 + lean * h, g - h * 0.75); p.lineTo(x + w, g); }, "#C8A8F0", "#4A2A7A", 3);
    p.fillStyle = "rgba(255,255,255,0.55)"; p.beginPath(); p.moveTo(x - w * 0.5 + lean * h * 0.3, g - h * 0.3); p.lineTo(x - w * 0.3 + lean * h * 0.7, g - h * 0.72); p.lineTo(x - w * 0.15 + lean * h * 0.7, g - h * 0.7); p.lineTo(x - w * 0.3 + lean * h * 0.3, g - h * 0.3); p.fill();
  }
  return c;
};
CM.art.root = function () {                                                // roots of the world, breaking through the wall and the floor
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, g = S - 14, rnd = new CM.Random(707);
  p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, g - 2, 90, 10, 0, 0, Math.PI * 2); p.fill();
  p.lineCap = "round";
  for (let i = 0; i < 7; i++) {
    const x0 = 40 + i * 30 + rnd.next() * 10, w = 10 + rnd.next() * 14;
    p.strokeStyle = "#1A1410"; p.lineWidth = w + 6; p.beginPath(); p.moveTo(x0, 10); p.bezierCurveTo(x0 + 40 * (rnd.next() - 0.5), 90, x0 - 50 * (rnd.next() - 0.5), 170, 128 + (rnd.next() - 0.5) * 120, g); p.stroke();
    p.strokeStyle = i % 2 ? "#5A2A26" : "#6E3A30"; p.lineWidth = w; p.stroke();
    p.strokeStyle = "rgba(255,90,60,0.55)"; p.lineWidth = 2; p.stroke();
  }
  return c;
};

// the run's summary as a card to keep: the emblem, the lines, old gold on dark leather
CM.art.summaryCard = function (e, title) {
  const W = 600, H = 340, c = document.createElement("canvas"), p = c.getContext("2d");
  c.width = W; c.height = H;
  const g = p.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, "#2A2016"); g.addColorStop(1, "#15100A");
  p.fillStyle = g; p.fillRect(0, 0, W, H);
  p.strokeStyle = "#8A6A30"; p.lineWidth = 3; p.strokeRect(8, 8, W - 16, H - 16);
  p.strokeStyle = "#4A3A1A"; p.lineWidth = 1; p.strokeRect(14, 14, W - 28, H - 28);
  p.drawImage(CM.art.emblem(110), 24, 24, 110, 110);
  p.fillStyle = "#E8C870"; p.font = "bold 26px Georgia, serif"; p.textBaseline = "top";
  p.fillText("Claude and Magic", 150, 30);
  p.fillStyle = "#C8B088"; p.font = "italic 15px Georgia, serif";
  const d = CM.DIFFICULTIES[e.difficulty] ? CM.DIFFICULTIES[e.difficulty].name : "Fair";
  p.fillText(`${e.name}${title ? " " + title : ""}'s expedition - ${d}${e.daily ? ", today's dungeon" : ""}`, 150, 66);
  p.fillStyle = e.won ? "#F0D080" : "#E8DCC0"; p.font = "bold 17px Georgia, serif";
  const gold = `with ${(e.gold || 0).toLocaleString()} gold`;
  p.fillText(CM.endlessFall(e) ? `Floor ${e.floor} of the endless dark${e.won ? ", crowned" : ""}, ${gold}` : e.bottom ? `To the bottom of the world, ${gold}`
    : e.won ? `Slew the Lich King, ${gold}` : `Fell on floor ${e.floor}, ${CM.themeFor(e.floor).name}, ${gold}`, 150, 92);
  p.fillStyle = "#B0A080"; p.font = "13px Georgia, serif";
  p.fillText(`Seed ${e.seed || "?"} - ${e.date || ""}`, 150, 116);
  const t = e.tally || {}, lines = [];
  for (const who of (e.party || [])) lines.push("  " + who);
  const wrap = (text) => { const words = text.split(" "), out = []; let line = ""; for (const w of words) { if (p.measureText(line + " " + w).width > W - 60 && line) { out.push(line); line = w; } else line = line ? line + " " + w : w; } if (line) out.push(line); return out; };
  p.fillStyle = "#E8DCC0"; p.font = "14px Georgia, serif";
  let y = 150;
  if (lines.length) { p.fillStyle = "#C8B088"; p.fillText("The party", 28, y); y += 20; p.fillStyle = "#E8DCC0"; for (const l of lines) { p.fillText(l, 28, y); y += 19; } y += 6; }
  const facts = [`${CM.plural(t.kills || 0, "monster")} slain, ${CM.plural(t.chests || 0, "chest")} opened, ${CM.plural(t.steps || 0, "step")}, ${CM.plural(t.fights || 0, "fight")}${t.fled ? ` (${t.fled} fled)` : ""}`];
  if (t.guardians && t.guardians.length) facts.push(`Guardians slain: ${t.guardians.map((id) => (CM.GUARDIANS[id] || { name: id }).name.replace(/^The /, "the ")).join(", ")}`);
  if (e.mutators && e.mutators.length) facts.push(`Mutators: ${e.mutators.map((m) => (CM.MUTATORS[m] || { name: m }).name).join(" and ")}`);
  if (e.titles && e.titles.length) facts.push(`Earned: ${e.titles.map((id) => (CM.ACHIEVEMENTS[id] || { name: id }).name).join(", ")}`);
  for (const f of facts) for (const l of wrap(f)) { if (y > H - 34) break; p.fillText(l, 28, y); y += 19; }
  p.fillStyle = "#6A5A40"; p.font = "italic 11px Georgia, serif"; p.textAlign = "right";
  p.fillText("A Claude Timeline game", W - 24, H - 30);
  return c;
};

// the title's emblem: the Lich King's crown on his skull, over a crossed sword and staff, on a medallion of old gold
CM.art.emblem = function (size = 160) {
  const c = artCanvas(size), p = c.getContext("2d"), s = size / 160, cx = 80, cy = 82;
  p.scale(s, s);
  const rim = p.createRadialGradient(cx, cy, 60, cx, cy, 78);
  rim.addColorStop(0, "#5A4420"); rim.addColorStop(0.55, "#E8C870"); rim.addColorStop(1, "#7A5A20");
  p.fillStyle = rim; p.beginPath(); p.arc(cx, cy, 78, 0, Math.PI * 2); p.fill();
  const disc = p.createRadialGradient(cx - 20, cy - 24, 4, cx, cy, 68);
  disc.addColorStop(0, "#3A3040"); disc.addColorStop(1, "#120E14");
  p.fillStyle = disc; p.beginPath(); p.arc(cx, cy, 66, 0, Math.PI * 2); p.fill();
  p.fillStyle = "#F0D890";                                              // studs on the rim
  for (let i = 0; i < 12; i++) { const a = i * Math.PI / 6; p.beginPath(); p.arc(cx + Math.cos(a) * 72, cy + Math.sin(a) * 72, 2.5, 0, Math.PI * 2); p.fill(); }
  p.lineCap = "round";
  p.strokeStyle = "#1A1410"; p.lineWidth = 9; p.beginPath(); p.moveTo(cx - 46, cy + 50); p.lineTo(cx + 46, cy - 42); p.stroke();   // the sword
  p.strokeStyle = "#D8DCE8"; p.lineWidth = 5; p.beginPath(); p.moveTo(cx - 30, cy + 34); p.lineTo(cx + 46, cy - 42); p.stroke();
  p.strokeStyle = "#8A6A20"; p.lineWidth = 5; p.beginPath(); p.moveTo(cx - 46, cy + 50); p.lineTo(cx - 30, cy + 34); p.stroke();   // its hilt
  p.beginPath(); p.moveTo(cx - 40, cy + 24); p.lineTo(cx - 22, cy + 42); p.stroke();                                              // and guard
  p.strokeStyle = "#1A1410"; p.lineWidth = 9; p.beginPath(); p.moveTo(cx + 46, cy + 50); p.lineTo(cx - 42, cy - 38); p.stroke();   // the staff
  p.strokeStyle = "#4A3A5A"; p.lineWidth = 5; p.beginPath(); p.moveTo(cx + 46, cy + 50); p.lineTo(cx - 42, cy - 38); p.stroke();
  const orb = p.createRadialGradient(cx - 44, cy - 42, 0, cx - 44, cy - 42, 13);
  orb.addColorStop(0, "#C0FFFF"); orb.addColorStop(0.5, "#40F0FF"); orb.addColorStop(1, "rgba(64,240,255,0)");
  p.fillStyle = orb; p.beginPath(); p.arc(cx - 44, cy - 42, 13, 0, Math.PI * 2); p.fill();
  outlined(p, () => { p.ellipse(cx, cy - 4, 26, 28, 0, 0, Math.PI * 2); }, "#E8E4D8", "#1A1410", 3);                            // the skull
  outlined(p, () => { p.rect(cx - 14, cy + 16, 28, 14); }, "#E8E4D8", "#1A1410", 3);                                            // the jaw
  p.fillStyle = "#1A1410";
  for (let i = -2; i <= 2; i++) p.fillRect(cx + i * 6 - 1, cy + 16, 2, 14);
  for (const side of [-1, 1]) { p.beginPath(); p.ellipse(cx + side * 10, cy - 6, 8, 9, 0, 0, Math.PI * 2); p.fill(); }
  p.beginPath(); p.moveTo(cx, cy + 2); p.lineTo(cx - 4, cy + 10); p.lineTo(cx + 4, cy + 10); p.fill();
  p.save(); p.shadowColor = "#40F0FF"; p.shadowBlur = 10; p.fillStyle = "#40F0FF";
  for (const side of [-1, 1]) { p.beginPath(); p.arc(cx + side * 10, cy - 6, 3.5, 0, Math.PI * 2); p.fill(); }
  p.restore();
  outlined(p, () => {                                                   // the crown
    p.moveTo(cx - 26, cy - 24);
    for (let i = 0; i <= 4; i++) p.lineTo(cx - 26 + i * 13, cy - (i % 2 ? 36 : 50));
    p.lineTo(cx + 26, cy - 24);
  }, "#F0C030", "#6A4A08", 2.5);
  p.fillStyle = "#E03030"; p.beginPath(); p.arc(cx, cy - 32, 3.5, 0, Math.PI * 2); p.fill();
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


// ---- the surface: ground, the faces of houses and walls, trees, the canopy, the sky's gradient, the sun and the moon ----
CM.art.ground = function (kind, seed = 1) {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(CM.hashSeed(`ground:${kind}:${seed}`));
  if (kind === "grass" || kind === "moss") {
    const base = kind === "grass" ? [86, 124, 54] : [52, 78, 40];
    p.fillStyle = rgb(base); p.fillRect(0, 0, S, S);
    speckle(p, rnd, S, S, 2600, rgb(base, 1.25), 0.45, 3); speckle(p, rnd, S, S, 1400, rgb(base, 0.7), 0.4, 3);
    p.strokeStyle = rgb(base, 1.4, 0.7); p.lineWidth = 1.5;
    for (let i = 0; i < 260; i++) { const x = rnd.next() * S, y = rnd.next() * S, l = 5 + rnd.next() * 9; p.beginPath(); p.moveTo(x, y); p.lineTo(x + (rnd.next() - 0.5) * 6, y - l); p.stroke(); }
    if (kind === "grass") { p.fillStyle = "rgba(240,220,120,0.8)"; for (let i = 0; i < 6; i++) { p.beginPath(); p.arc(rnd.next() * S, rnd.next() * S, 2.5, 0, Math.PI * 2); p.fill(); } }
  } else if (kind === "dirt" || kind === "tilled") {
    const base = [126, 100, 70];
    p.fillStyle = rgb(base); p.fillRect(0, 0, S, S);
    speckle(p, rnd, S, S, 2200, rgb(base, 0.75), 0.4, 3); speckle(p, rnd, S, S, 900, rgb(base, 1.25), 0.35, 3);
    for (let i = 0; i < 18; i++) { p.fillStyle = rgb([150, 140, 125], 1, 0.7); p.beginPath(); p.ellipse(rnd.next() * S, rnd.next() * S, 3 + rnd.next() * 4, 2 + rnd.next() * 3, rnd.next() * 3, 0, Math.PI * 2); p.fill(); }
    if (kind === "tilled") { p.fillStyle = rgb(base, 0.6, 0.8); for (let y = 10; y < S; y += 32) p.fillRect(0, y, S, 9); p.fillStyle = rgb(base, 1.2, 0.5); for (let y = 24; y < S; y += 32) p.fillRect(0, y, S, 5); }
  } else if (kind === "cobbles" || kind === "flags") {
    const base = kind === "cobbles" ? [128, 118, 104] : [140, 134, 124];
    p.fillStyle = rgb(base, 0.55); p.fillRect(0, 0, S, S);
    const n = kind === "cobbles" ? 8 : 4, w = S / n;
    for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
      const x = i * w + (kind === "cobbles" && j % 2 ? w / 2 : 0), y = j * w, k = 0.85 + rnd.next() * 0.3;
      p.fillStyle = rgb(base, k);
      if (kind === "cobbles") { p.beginPath(); p.ellipse(((x + w / 2) % S), y + w / 2, w * 0.44, w * 0.38, 0, 0, Math.PI * 2); p.fill(); }
      else { p.fillRect(x + 2, y + 2, w - 4, w - 4); }
    }
    speckle(p, rnd, S, S, 900, rgb(base, 1.3), 0.3, 2);
  } else if (kind === "litter" || kind === "needles") {
    const base = kind === "litter" ? [96, 74, 44] : [92, 62, 40];
    p.fillStyle = rgb(base); p.fillRect(0, 0, S, S);
    if (kind === "litter") for (let i = 0; i < 320; i++) { const k = 0.7 + rnd.next() * 0.7; p.fillStyle = `rgba(${Math.round(150 * k)},${Math.round(100 * k)},${Math.round(40 * k)},0.85)`; p.beginPath(); p.ellipse(rnd.next() * S, rnd.next() * S, 4 + rnd.next() * 5, 2 + rnd.next() * 3, rnd.next() * 3, 0, Math.PI * 2); p.fill(); }
    else { p.strokeStyle = rgb(base, 1.4, 0.8); p.lineWidth = 1.5; for (let i = 0; i < 700; i++) { const x = rnd.next() * S, y = rnd.next() * S, a = rnd.next() * Math.PI; p.beginPath(); p.moveTo(x, y); p.lineTo(x + Math.cos(a) * 8, y + Math.sin(a) * 8); p.stroke(); } }
    CM.art.footShade(c);
  } else if (kind === "planks") {
    const base = [120, 88, 56];
    p.fillStyle = rgb(base, 0.6); p.fillRect(0, 0, S, S);
    for (let i = 0; i < 6; i++) { p.fillStyle = rgb(base, 0.85 + rnd.next() * 0.3); p.fillRect(i * S / 6 + 2, 0, S / 6 - 4, S); }
    p.strokeStyle = rgb(base, 0.6, 0.6); p.lineWidth = 1.5;
    for (let i = 0; i < 80; i++) { const x = rnd.next() * S, y = rnd.next() * S; p.beginPath(); p.moveTo(x, y); p.lineTo(x + (rnd.next() - 0.5) * 4, y + 20 + rnd.next() * 40); p.stroke(); }
  }
  return c;
};
// a plastered, half-timbered face; what is in it: nothing, a window, a door, a shop's door and board
CM.art.facade = function (what, seed = 1, base = null) {                  // base: a picture of the plaster to build on (the Stone look's photograph), else painted
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(CM.hashSeed(`facade:${what}:${seed}`));
  if (base) p.drawImage(base, 0, 0, S, S);
  else { p.fillStyle = "#D8CCB0"; p.fillRect(0, 0, S, S); speckle(p, rnd, S, S, 1600, "#B8A890", 0.35, 3); speckle(p, rnd, S, S, 500, "#F0E8D8", 0.3, 3); }
  p.fillStyle = "#5A4028";                                                                  // the timbers
  p.fillRect(0, 0, 12, S); p.fillRect(S - 12, 0, 12, S); p.fillRect(0, 0, S, 10); p.fillRect(0, S - 14, S, 14);
  if (what === "house" || what === "frame") { p.fillRect(S / 2 - 6, 0, 12, S); p.beginPath(); p.moveTo(12, S * 0.55); p.lineTo(S / 2 - 6, 10); p.lineTo(S / 2 - 6, 26); p.lineTo(26, S * 0.6); p.closePath(); p.fill(); }
  const window = (x, y, w, h) => {
    p.fillStyle = "#5A4028"; p.fillRect(x - 5, y - 5, w + 10, h + 10);
    p.fillStyle = "#2A3444"; p.fillRect(x, y, w, h);
    p.fillStyle = "rgba(200,220,240,0.35)"; p.fillRect(x + 3, y + 3, w / 2 - 5, h / 2 - 5);
    p.fillStyle = "#5A4028"; p.fillRect(x + w / 2 - 2, y, 4, h); p.fillRect(x, y + h / 2 - 2, w, 4);
  };
  if (what === "house") { window(S * 0.62, S * 0.3, S * 0.22, S * 0.26); }
  if (what === "door" || what === "shop") {
    p.fillStyle = "#5A4028"; p.fillRect(S * 0.3, S * 0.3, S * 0.4, S * 0.7);                   // the frame
    p.fillStyle = "#7A5230"; p.fillRect(S * 0.33, S * 0.34, S * 0.34, S * 0.66);                 // the door
    p.fillStyle = "#4A3220"; for (let i = 1; i < 5; i++) p.fillRect(S * 0.33 + i * S * 0.068, S * 0.34, 3, S * 0.66);
    p.fillStyle = "#D8C070"; p.beginPath(); p.arc(S * 0.62, S * 0.68, 4, 0, Math.PI * 2); p.fill();   // the latch
    if (what === "door") window(S * 0.74, S * 0.36, S * 0.16, S * 0.2);
    else { p.fillStyle = "#5A4028"; p.fillRect(S * 0.2, S * 0.12, S * 0.6, S * 0.14); p.fillStyle = "#8A6A3A"; p.fillRect(S * 0.22, S * 0.14, S * 0.56, S * 0.1); p.fillStyle = "#F0D080"; p.fillRect(S * 0.3, S * 0.175, S * 0.4, 3); }
  }
  if (what === "frame") {                                                                   // posts and beams, the plaster not yet on: see through
    const f = artCanvas(), q = f.getContext("2d");
    q.fillStyle = "#6A4A2A"; q.fillRect(0, 0, 14, S); q.fillRect(S - 14, 0, 14, S); q.fillRect(S / 2 - 7, 0, 14, S); q.fillRect(0, 0, S, 12); q.fillRect(0, S * 0.5, S, 10); q.fillRect(0, S - 12, S, 12);
    return f;
  }
  return c;
};
CM.art.townWall = function (top = false, seed = 1) {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(CM.hashSeed(`townwall:${top}:${seed}`)), base = top ? [120, 116, 108] : [104, 100, 94];
  p.fillStyle = rgb(base, 0.55); p.fillRect(0, 0, S, S);
  const rows = top ? 4 : 5, hgt = S / rows;
  for (let j = 0; j < rows; j++) { let x = j % 2 ? -S / 7 : 0; while (x < S) { const w = S / 4 + rnd.next() * S / 7; p.fillStyle = rgb(base, 0.85 + rnd.next() * 0.35); p.fillRect(x + 3, j * hgt + 3, w - 6, hgt - 6); x += w; } }
  speckle(p, rnd, S, S, 1500, rgb(base, 0.6), 0.3, 3); speckle(p, rnd, S, S, 500, rgb(base, 1.4), 0.25, 2);
  if (!top) { p.fillStyle = "rgba(90,120,60,0.35)"; for (let i = 0; i < 10; i++) { p.beginPath(); p.arc(rnd.next() * S, S * 0.7 + rnd.next() * S * 0.3, 8 + rnd.next() * 12, 0, Math.PI * 2); p.fill(); } }
  return c;
};
CM.art.hedge = function (seed = 1) {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(CM.hashSeed(`hedge:${seed}`));
  p.fillStyle = "#2E4A22"; p.fillRect(0, 0, S, S);
  for (let i = 0; i < 700; i++) { const k = 0.7 + rnd.next() * 0.8; p.fillStyle = `rgba(${Math.round(70 * k)},${Math.round(120 * k)},${Math.round(50 * k)},0.9)`; p.beginPath(); p.arc(rnd.next() * S, rnd.next() * S, 5 + rnd.next() * 9, 0, Math.PI * 2); p.fill(); }
  return c;
};
CM.art.fence = function (seed = 1) {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(CM.hashSeed(`fence:${seed}`));
  for (let i = 0; i < 6; i++) { p.fillStyle = rgb([130, 100, 66], 0.85 + rnd.next() * 0.3); const x = 8 + i * (S / 6); p.fillRect(x, S * 0.15, S / 6 - 22, S * 0.85); p.beginPath(); p.moveTo(x, S * 0.15); p.lineTo(x + (S / 6 - 22) / 2, S * 0.06); p.lineTo(x + S / 6 - 22, S * 0.15); p.fill(); }
  p.fillStyle = "#6E5236"; p.fillRect(0, S * 0.3, S, 14); p.fillRect(0, S * 0.68, S, 14);
  return c;
};
CM.art.cliff = function (seed = 1) {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(CM.hashSeed(`cliff:${seed}`)), base = [112, 100, 86];
  p.fillStyle = rgb(base, 0.7); p.fillRect(0, 0, S, S);
  let y = 0; while (y < S) { const h = 18 + rnd.next() * 30; p.fillStyle = rgb(base, 0.75 + rnd.next() * 0.5); p.fillRect(0, y, S, h - 3); y += h; }
  speckle(p, rnd, S, S, 1800, rgb(base, 0.55), 0.35, 3); for (let i = 0; i < 6; i++) crack(p, rnd, rnd.next() * S, rnd.next() * S, 60 + rnd.next() * 80, rgb(base, 0.4, 0.8));
  p.fillStyle = "rgba(90,130,60,0.5)"; for (let i = 0; i < 8; i++) { p.beginPath(); p.arc(rnd.next() * S, rnd.next() * S * 0.3, 8 + rnd.next() * 10, 0, Math.PI * 2); p.fill(); }
  return c;
};
CM.art.roof = function (seed = 1) {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(CM.hashSeed(`roof:${seed}`)), base = [138, 78, 52];
  p.fillStyle = rgb(base, 0.6); p.fillRect(0, 0, S, S);
  const rows = 8, h = S / rows, w = S / 6;
  for (let j = 0; j < rows; j++) for (let i = -1; i < 7; i++) { p.fillStyle = rgb(base, 0.8 + rnd.next() * 0.4); p.beginPath(); p.moveTo(i * w + (j % 2 ? w / 2 : 0) + 2, j * h); p.lineTo(i * w + (j % 2 ? w / 2 : 0) + w - 2, j * h); p.lineTo(i * w + (j % 2 ? w / 2 : 0) + w - 2, j * h + h - 3); p.arc(i * w + (j % 2 ? w / 2 : 0) + w / 2, j * h + h - 3, w / 2 - 2, 0, Math.PI); p.closePath(); p.fill(); }
  return c;
};
// a tree, trunk and crown, against nothing (three kinds: an oak, a tall fir, a birch in its autumn)
CM.art.tree = function (variant = 0, bark = null) {                       // bark: a picture for the trunk (the Stone look's photograph), else painted
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(CM.hashSeed(`tree:${variant}`));
  const trunk = variant === 2 ? "#D8D0C0" : "#4A3220", crown = variant === 0 ? [62, 110, 48] : variant === 1 ? [40, 84, 52] : [196, 150, 48];
  if (bark && variant !== 2) { p.save(); p.beginPath(); p.rect(S / 2 - 12, S * 0.45, 24, S * 0.55); p.clip(); p.drawImage(bark, 0, 0, S / 2, S, S / 2 - 12, S * 0.45, 24, S * 0.55); p.restore(); }
  else { p.fillStyle = trunk; p.fillRect(S / 2 - 12, S * 0.45, 24, S * 0.55); }
  if (variant === 2) { p.fillStyle = "#2A2420"; for (let i = 0; i < 9; i++) p.fillRect(S / 2 - 12 + rnd.next() * 14, S * 0.5 + rnd.next() * S * 0.45, 6 + rnd.next() * 8, 3); }
  if (variant === 1) { for (let i = 0; i < 5; i++) { const y = S * 0.08 + i * S * 0.14, w = S * 0.14 + i * S * 0.07; p.fillStyle = rgb(crown, 0.8 + i * 0.07); p.beginPath(); p.moveTo(S / 2, y); p.lineTo(S / 2 + w, y + S * 0.2); p.lineTo(S / 2 - w, y + S * 0.2); p.closePath(); p.fill(); } }
  else { for (let i = 0; i < 26; i++) { const a = rnd.next() * Math.PI * 2, r = rnd.next() * S * 0.26, x = S / 2 + Math.cos(a) * r, y = S * 0.32 + Math.sin(a) * r * 0.8; p.fillStyle = rgb(crown, 0.75 + rnd.next() * 0.5); p.beginPath(); p.arc(x, y, S * 0.1 + rnd.next() * S * 0.08, 0, Math.PI * 2); p.fill(); } }
  return c;
};
CM.art.canopy = function (seed = 1) {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(CM.hashSeed(`canopy:${seed}`));
  p.fillStyle = "#1E3418"; p.fillRect(0, 0, S, S);
  for (let i = 0; i < 500; i++) { const k = 0.6 + rnd.next() * 0.9; p.fillStyle = `rgba(${Math.round(50 * k)},${Math.round(96 * k)},${Math.round(40 * k)},0.95)`; p.beginPath(); p.arc(rnd.next() * S, rnd.next() * S, 7 + rnd.next() * 11, 0, Math.PI * 2); p.fill(); }
  p.globalCompositeOperation = "destination-out";                                            // holes for the sky
  for (let i = 0; i < 14; i++) { p.beginPath(); p.arc(rnd.next() * S, rnd.next() * S, 3 + rnd.next() * 6, 0, Math.PI * 2); p.fill(); }
  p.globalCompositeOperation = "source-over";
  return c;
};
CM.art.skyGradient = function () {                                                            // red: how high, for the shader to colour
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, g = p.createLinearGradient(0, 0, 0, S);
  g.addColorStop(0, "rgb(255,0,0)"); g.addColorStop(0.62, "rgb(90,0,0)"); g.addColorStop(1, "rgb(0,0,0)");
  p.fillStyle = g; p.fillRect(0, 0, S, S);
  return c;
};
CM.art.sun = function () {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, g = p.createRadialGradient(S / 2, S / 2, S * 0.16, S / 2, S / 2, S * 0.5);
  g.addColorStop(0, "rgba(255,246,200,1)"); g.addColorStop(0.3, "rgba(255,230,140,0.9)"); g.addColorStop(1, "rgba(255,210,120,0)");
  p.fillStyle = g; p.fillRect(0, 0, S, S);
  return c;
};
CM.art.moon = function (phase = 4) {                                                          // 0 new .. 4 full .. 7 waning crescent
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, r = S * 0.3, cx = S / 2, cy = S / 2;
  const glow = p.createRadialGradient(cx, cy, r, cx, cy, r * 1.6); glow.addColorStop(0, "rgba(220,228,255,0.35)"); glow.addColorStop(1, "rgba(220,228,255,0)");
  p.fillStyle = glow; p.fillRect(0, 0, S, S);
  p.fillStyle = "#E8ECF4"; p.beginPath(); p.arc(cx, cy, r, 0, Math.PI * 2); p.fill();
  p.fillStyle = "rgba(170,180,200,0.5)"; for (const [dx, dy, rr] of [[-0.3, -0.2, 0.18], [0.25, 0.1, 0.12], [-0.05, 0.35, 0.1]]) { p.beginPath(); p.arc(cx + dx * r, cy + dy * r, rr * r, 0, Math.PI * 2); p.fill(); }
  if (phase !== 4) {                                                                           // the shadow: a disc slid across, or the dark side
    p.fillStyle = "#0A0C18";
    const k = (phase - 4) / 4;                                                                 // -1 new .. 0 full .. 0.75 waning crescent
    p.beginPath(); p.arc(cx, cy, r + 1, 0, Math.PI * 2); p.clip();
    p.beginPath(); p.arc(cx + (phase < 4 ? -1 : 1) * r * 2 * (1 - Math.abs(k)) * -1 + (phase < 4 ? -r * 0 : 0), cy, r * (phase === 0 ? 1.1 : 1.2 + Math.abs(k)), 0, Math.PI * 2);
    if (phase === 0) { p.fillRect(0, 0, S, S); } else p.fill();
  }
  return c;
};


// the ground under a tree: needles or leaf litter, darker at the middle where the trunk's shade falls
CM.art.footShade = function (canvas) {
  const p = canvas.getContext("2d"), S = canvas.width, g = p.createRadialGradient(S / 2, S / 2, S * 0.05, S / 2, S / 2, S * 0.62);
  g.addColorStop(0, "rgba(0,0,0,0.55)"); g.addColorStop(0.55, "rgba(0,0,0,0.25)"); g.addColorStop(1, "rgba(0,0,0,0)");
  p.fillStyle = g; p.fillRect(0, 0, S, S);
  return canvas;
};
// the far ring: a tree-line against the sky, and the town's hill with its wall, roofs and the keep's stump
CM.art.farTrees = function () {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, rnd = new CM.Random(CM.hashSeed("far:trees"));
  p.fillStyle = "#2A4428";
  p.fillRect(0, S * 0.72, S, S * 0.28);
  for (let i = 0; i < 26; i++) {
    const x = rnd.next() * S, r = S * (0.05 + rnd.next() * 0.06), top = S * (0.32 + rnd.next() * 0.3);
    if (rnd.chance(0.35)) { p.beginPath(); p.moveTo(x, top - r); p.lineTo(x + r * 0.9, S * 0.8); p.lineTo(x - r * 0.9, S * 0.8); p.closePath(); p.fill(); }
    else { p.beginPath(); p.arc(x, top + r, r * 1.2, 0, Math.PI * 2); p.fill(); p.fillRect(x - r * 1.2, top + r, r * 2.4, S); }
  }
  return c;
};
CM.art.farHill = function () {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE;
  p.fillStyle = "#3A4A34";
  p.beginPath(); p.moveTo(0, S); p.lineTo(0, S * 0.7); p.quadraticCurveTo(S * 0.5, S * 0.32, S, S * 0.7); p.lineTo(S, S); p.closePath(); p.fill();
  p.fillStyle = "#6A665E"; p.fillRect(S * 0.18, S * 0.46, S * 0.64, S * 0.1);                          // the wall
  for (let x = S * 0.18; x < S * 0.82; x += S * 0.05) p.fillRect(x, S * 0.43, S * 0.025, S * 0.04);   // its crenels
  p.fillStyle = "#5A3A2A";
  for (const [x, w] of [[0.26, 0.09], [0.37, 0.07], [0.5, 0.1], [0.63, 0.08]]) { p.beginPath(); p.moveTo(S * x, S * 0.46); p.lineTo(S * (x + w / 2), S * 0.36); p.lineTo(S * (x + w), S * 0.46); p.closePath(); p.fill(); }
  p.fillStyle = "#6A665E"; p.fillRect(S * 0.72, S * 0.3, S * 0.06, S * 0.16);                         // the keep's stump
  return c;
};
// a signpost: a post with two boards; and the signs over the doors: a board with the house's mark
CM.art.signpost = function () {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE;
  p.fillStyle = "#5A4028"; p.fillRect(S / 2 - 9, S * 0.2, 18, S * 0.8);
  for (const [y, dir] of [[S * 0.24, 1], [S * 0.4, -1]]) {
    p.fillStyle = "#8A6A3A"; p.beginPath();
    if (dir > 0) { p.moveTo(S * 0.22, y); p.lineTo(S * 0.7, y); p.lineTo(S * 0.8, y + 16); p.lineTo(S * 0.7, y + 32); p.lineTo(S * 0.22, y + 32); }
    else { p.moveTo(S * 0.78, y); p.lineTo(S * 0.3, y); p.lineTo(S * 0.2, y + 16); p.lineTo(S * 0.3, y + 32); p.lineTo(S * 0.78, y + 32); }
    p.closePath(); p.fill();
    p.fillStyle = "#3A2A18"; for (let i = 0; i < 5; i++) p.fillRect(S * 0.3 + i * 22 + (dir > 0 ? 0 : 10), y + 12, 14, 7);   // (the words, too far to read)
  }
  return c;
};
CM.art.cross = function () {                                              // the market cross: steps, a shaft, and the cross on it
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE;
  p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(S / 2, S - 12, 80, 10, 0, 0, Math.PI * 2); p.fill();
  p.fillStyle = "#9A948A"; p.fillRect(S * 0.2, S * 0.86, S * 0.6, S * 0.1); p.fillStyle = "#B0AA9E"; p.fillRect(S * 0.3, S * 0.78, S * 0.4, S * 0.09);
  p.fillStyle = "#A8A298"; p.fillRect(S / 2 - 12, S * 0.22, 24, S * 0.58); p.fillStyle = "#C0BAB0"; p.fillRect(S / 2 - 12, S * 0.22, 8, S * 0.58);
  p.fillStyle = "#B8B2A8"; p.fillRect(S / 2 - 10, S * 0.06, 20, S * 0.2); p.fillRect(S / 2 - 36, S * 0.11, 72, 16);
  return c;
};
CM.SIGN_MARKS = { home: "key", tavern: "lantern", merchant: "bale", smith: "anvil", garden: "mortar", library: "book", temple: "sun", guildhall: "swords", chronicler: "quill" };
CM.art.sign = function (id) {
  const c = artCanvas(), p = c.getContext("2d"), S = ART_SIZE, mark = CM.SIGN_MARKS[id] || "key";
  p.fillStyle = "#3A2A18"; p.fillRect(S * 0.46, 0, S * 0.08, S * 0.14);                       // the bracket
  p.fillStyle = "#8A6A3A"; p.fillRect(S * 0.1, S * 0.14, S * 0.8, S * 0.72);                  // the board
  p.fillStyle = "#5A4028"; p.fillRect(S * 0.1, S * 0.14, S * 0.8, 8); p.fillRect(S * 0.1, S * 0.86 - 8, S * 0.8, 8); p.fillRect(S * 0.1, S * 0.14, 8, S * 0.72); p.fillRect(S * 0.9 - 8, S * 0.14, 8, S * 0.72);
  const cx = S / 2, cy = S * 0.5; p.lineWidth = 8; p.lineCap = "round"; p.strokeStyle = "#F0D080"; p.fillStyle = "#F0D080";
  if (mark === "lantern") { p.fillStyle = "#F0D080"; p.fillRect(cx - 26, cy - 36, 52, 70); p.fillStyle = "#8A6A3A"; p.fillRect(cx - 18, cy - 28, 36, 54); p.fillStyle = "#FFE890"; p.beginPath(); p.ellipse(cx, cy, 10, 18, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#F0D080"; p.beginPath(); p.arc(cx, cy - 44, 12, Math.PI, 0); p.stroke(); }
  else if (mark === "bale") { p.fillRect(cx - 40, cy - 30, 80, 60); p.strokeStyle = "#5A4028"; p.lineWidth = 6; p.beginPath(); p.moveTo(cx - 40, cy); p.lineTo(cx + 40, cy); p.moveTo(cx, cy - 30); p.lineTo(cx, cy + 30); p.stroke(); }
  else if (mark === "anvil") { p.beginPath(); p.moveTo(cx - 44, cy - 20); p.lineTo(cx + 44, cy - 20); p.lineTo(cx + 30, cy); p.lineTo(cx + 12, cy + 4); p.lineTo(cx + 20, cy + 30); p.lineTo(cx - 20, cy + 30); p.lineTo(cx - 12, cy + 4); p.lineTo(cx - 30, cy); p.closePath(); p.fill(); }
  else if (mark === "mortar") { p.beginPath(); p.moveTo(cx - 36, cy - 10); p.lineTo(cx + 36, cy - 10); p.lineTo(cx + 22, cy + 34); p.lineTo(cx - 22, cy + 34); p.closePath(); p.fill(); p.beginPath(); p.moveTo(cx + 10, cy - 14); p.lineTo(cx + 40, cy - 50); p.stroke(); }
  else if (mark === "book") { p.fillRect(cx - 40, cy - 28, 36, 56); p.fillRect(cx + 4, cy - 28, 36, 56); p.strokeStyle = "#5A4028"; p.lineWidth = 4; p.beginPath(); p.moveTo(cx - 30, cy - 12); p.lineTo(cx - 12, cy - 12); p.moveTo(cx - 30, cy); p.lineTo(cx - 12, cy); p.moveTo(cx + 12, cy - 12); p.lineTo(cx + 30, cy - 12); p.moveTo(cx + 12, cy); p.lineTo(cx + 30, cy); p.stroke(); }
  else if (mark === "sun") { p.beginPath(); p.arc(cx, cy, 22, 0, Math.PI * 2); p.fill(); for (let i = 0; i < 8; i++) { const a = i * Math.PI / 4; p.beginPath(); p.moveTo(cx + Math.cos(a) * 30, cy + Math.sin(a) * 30); p.lineTo(cx + Math.cos(a) * 46, cy + Math.sin(a) * 46); p.stroke(); } }
  else if (mark === "swords") { p.beginPath(); p.moveTo(cx - 40, cy + 36); p.lineTo(cx + 36, cy - 40); p.moveTo(cx + 40, cy + 36); p.lineTo(cx - 36, cy - 40); p.stroke(); p.lineWidth = 12; p.beginPath(); p.moveTo(cx - 34, cy + 18); p.lineTo(cx - 18, cy + 34); p.moveTo(cx + 34, cy + 18); p.lineTo(cx + 18, cy + 34); p.stroke(); }
  else if (mark === "quill") { p.beginPath(); p.moveTo(cx - 30, cy + 40); p.quadraticCurveTo(cx, cy - 10, cx + 36, cy - 44); p.quadraticCurveTo(cx + 10, cy - 10, cx - 30, cy + 40); p.fill(); p.beginPath(); p.moveTo(cx - 30, cy + 40); p.lineTo(cx - 40, cy + 50); p.stroke(); }
  else { p.beginPath(); p.arc(cx - 16, cy - 10, 18, 0, Math.PI * 2); p.stroke(); p.beginPath(); p.moveTo(cx, cy); p.lineTo(cx + 40, cy + 40); p.moveTo(cx + 24, cy + 24); p.lineTo(cx + 36, cy + 12); p.stroke(); }   // a key
  return c;
};
// every layer the surface wants, from the painters - `pick(key, drawn)` lets a look use its own tile for one
CM.art.surfaceLayers = function (pick) {
  const use = pick || ((key, drawn) => drawn());
  const out = {};
  for (const g of CM.GROUNDS) out[`ground:${g}`] = use(`ground.${g}`, () => CM.art.ground(g));
  out["solid:house"] = use("solid.house", () => CM.art.facade("house"));
  out["solid:door"] = use("solid.door", () => CM.art.facade("door"));
  out["solid:shop"] = use("solid.shop", () => CM.art.facade("shop"));
  out["solid:frame"] = use("solid.frame", () => CM.art.facade("frame"));
  out["solid:townwall"] = use("solid.townwall", () => CM.art.townWall(false));
  out["solid:townwall:top"] = use("solid.townwall.top", () => CM.art.townWall(true));
  out["solid:hedge"] = use("solid.hedge", () => CM.art.hedge());
  out["solid:fence"] = use("solid.fence", () => CM.art.fence());
  out["solid:cliff"] = use("solid.cliff", () => CM.art.cliff());
  out["solid:roof"] = use("solid.roof", () => CM.art.roof());
  for (let v = 0; v < 3; v++) out[`tree:${v}`] = use(`tree.${v}`, () => CM.art.tree(v));
  out.canopy = use("canopy", () => CM.art.canopy());
  out["far:trees"] = use("far.trees", () => CM.art.farTrees());
  out["far:hill"] = use("far.hill", () => CM.art.farHill());
  out.signpost = use("signpost", () => CM.art.signpost());
  out.cross = use("cross", () => CM.art.cross());
  for (const id of Object.keys(CM.TOWN_PLOTS || {})) out[`sign:${id}`] = use(`sign.${id}`, () => CM.art.sign(id));
  out.skygrad = CM.art.skyGradient();
  out.sun = CM.art.sun();
  for (let ph = 0; ph < 8; ph++) out[`moon:${ph}`] = CM.art.moon(ph);
  return out;
};



// the props a look may make from photographs: `kit` has pieces cut from the cut-out atlases (the Stone look), each
// { img, sx, sy, sw, sh } - blades of grass, green leaves, maple leaves; without a kit, everything is painted
CM.art.cutKit = function (packs) {
  const A = (key) => packs && packs[key];
  if (!A("cut.blades") || !A("cut.leaf") || !A("cut.maple")) return null;
  const cell = (img, i, cols, rows) => { const W = img.width, H = img.height; return { img, sx: (i % cols) * W / cols, sy: Math.floor(i / cols) * H / rows, sw: W / cols, sh: H / rows }; };
  const blades = []; { const img = A("cut.blades"), W = img.width; for (let i = 0; i < 9; i++) blades.push({ img, sx: W * (0.035 + i * 0.104), sy: W * 0.05, sw: W * 0.1, sh: W * 0.87 }); }
  if (A("cut.grass")) { const img = A("cut.grass"), W = img.width; for (let i = 0; i < 4; i++) blades.push({ img, sx: W * (0.05 + i * 0.155), sy: W * 0.02, sw: W * 0.12, sh: W * 0.45 }); }
  const leaves = [], maples = [];
  for (let i = 0; i < 9; i++) { leaves.push(cell(A("cut.leaf"), i, 3, 3)); maples.push(cell(A("cut.maple"), i, 3, 3)); }
  return { blades, leaves, maples };
};
const stamp = (p, piece, x, y, w, h, angle = 0) => { p.save(); p.translate(x, y); p.rotate(angle); p.drawImage(piece.img, piece.sx, piece.sy, piece.sw, piece.sh, -w / 2, -h, w, h); p.restore(); };
const tint = (c, colour, mode = "multiply") => { const p = c.getContext("2d"); p.save(); p.globalCompositeOperation = "source-atop"; p.globalAlpha = 1; p.fillStyle = colour; if (mode === "multiply") p.globalCompositeOperation = "source-atop"; p.fillRect(0, 0, c.width, c.height); p.restore(); return c; };
CM.art.surfaceProp = function (id, S, kit) {
  const c = artCanvas(S), p = c.getContext("2d"), rnd = new CM.Random(CM.hashSeed(`prop:${id}`));
  const blades = (n, hMin, hMax, colour, tipColour) => {
    for (let i = 0; i < n; i++) {
      const x = S * 0.12 + rnd.next() * S * 0.76, h = S * (hMin + rnd.next() * (hMax - hMin)), lean = (rnd.next() - 0.5) * 0.5;
      if (kit) stamp(p, kit.blades[rnd.int(0, kit.blades.length - 1)], x, S - 1, S * 0.09, h, lean * 0.6);
      else { const k = 0.7 + rnd.next() * 0.6; p.strokeStyle = colour(k); p.lineWidth = 3 + rnd.next() * 2; p.lineCap = "round"; p.beginPath(); p.moveTo(x, S - 2); p.quadraticCurveTo(x + lean * S * 0.1, S - h * 0.6, x + lean * S * 0.3, S - h); p.stroke(); if (tipColour) { p.strokeStyle = tipColour; p.beginPath(); p.moveTo(x + lean * S * 0.25, S - h * 0.85); p.lineTo(x + lean * S * 0.3, S - h); p.stroke(); } }
    }
  };
  const green = (k) => `rgb(${Math.round(70 * k)},${Math.round(120 * k)},${Math.round(44 * k)})`, gold = (k) => `rgb(${Math.round(176 * k)},${Math.round(150 * k)},${Math.round(70 * k)})`;
  if (id === "tuft") blades(kit ? 24 : 26, 0.35, 0.9, green);
  else if (id === "tuft_dry") { blades(kit ? 22 : 24, 0.3, 0.85, gold); if (kit) { p.save(); p.globalCompositeOperation = "source-atop"; p.fillStyle = "rgba(190,150,60,0.55)"; p.fillRect(0, 0, S, S); p.restore(); } }
  else if (id === "tuft_snow") { blades(kit ? 10 : 18, 0.3, 0.7, (k) => `rgb(${Math.round(90 * k)},${Math.round(110 * k)},${Math.round(80 * k)})`, "#F4F6FA"); p.fillStyle = "#EEF2F8"; p.beginPath(); p.ellipse(S / 2, S - 4, S * 0.45, S * 0.08, 0, 0, Math.PI * 2); p.fill(); }
  else if (id === "tallgrass") { blades(kit ? 22 : 34, 0.6, 1.0, (k) => `rgb(${Math.round(120 * k)},${Math.round(140 * k)},${Math.round(60 * k)})`); for (let i = 0; i < 8; i++) { const x = S * 0.15 + rnd.next() * S * 0.7, y = S * (0.04 + rnd.next() * 0.2); p.fillStyle = "#C8B060"; p.beginPath(); p.ellipse(x, y, 3, 9, (rnd.next() - 0.5) * 0.6, 0, Math.PI * 2); p.fill(); } }
  else if (id === "shrub") {
    p.fillStyle = "#24381C"; p.beginPath(); p.ellipse(S / 2, S * 0.62, S * 0.42, S * 0.34, 0, 0, Math.PI * 2); p.fill();
    for (let i = 0; i < (kit ? 70 : 140); i++) {
      const a = rnd.next() * Math.PI * 2, r = Math.sqrt(rnd.next()), x = S / 2 + Math.cos(a) * r * S * 0.42, y = S * 0.62 + Math.sin(a) * r * S * 0.33 - S * 0.04;
      if (kit) stamp(p, kit.leaves[rnd.int(0, 8)], x, y + S * 0.06, S * 0.13, S * 0.15, rnd.next() * Math.PI * 2);
      else { const k = 0.6 + rnd.next() * 0.7; p.fillStyle = `rgb(${Math.round(58 * k)},${Math.round(104 * k)},${Math.round(42 * k)})`; p.beginPath(); p.arc(x, y, S * (0.03 + rnd.next() * 0.03), 0, Math.PI * 2); p.fill(); }
    }
  } else if (id === "fern") {
    for (let f = 0; f < 7; f++) {
      const a = -Math.PI / 2 + (f - 3) * 0.32 + (rnd.next() - 0.5) * 0.15, len = S * (0.55 + rnd.next() * 0.35), x0 = S / 2, y0 = S - 2;
      p.strokeStyle = "#3E6A2C"; p.lineWidth = 3; p.beginPath(); p.moveTo(x0, y0); const xe = x0 + Math.cos(a) * len, ye = y0 + Math.sin(a) * len; p.quadraticCurveTo(x0 + Math.cos(a) * len * 0.5, y0 + Math.sin(a) * len * 0.3, xe, ye); p.stroke();
      for (let t = 0.15; t < 1; t += 0.08) { const x = x0 + (xe - x0) * t, y = y0 + (ye - y0) * t + Math.sin(t * Math.PI) * len * 0.08, w = (1 - t) * S * 0.09 + 3; p.strokeStyle = t % 0.16 < 0.08 ? "#4E8A38" : "#5A9A40"; p.lineWidth = 3; p.beginPath(); p.moveTo(x - w, y + w * 0.4); p.lineTo(x + w, y - w * 0.4); p.stroke(); }
    }
  } else if (id === "mushroom") {
    for (const [x, s] of [[0.32, 0.8], [0.6, 1], [0.78, 0.6]]) { p.fillStyle = "#E8DCC4"; p.fillRect(S * x - S * 0.04 * s, S * (1 - 0.45 * s), S * 0.08 * s, S * 0.45 * s); p.fillStyle = "#B0442C"; p.beginPath(); p.ellipse(S * x, S * (1 - 0.45 * s), S * 0.16 * s, S * 0.12 * s, 0, Math.PI, 0); p.fill(); p.fillStyle = "#F4ECDC"; for (let i = 0; i < 3; i++) { p.beginPath(); p.arc(S * x + (i - 1) * S * 0.06 * s, S * (1 - 0.5 * s), S * 0.018, 0, Math.PI * 2); p.fill(); } }
  } else if (id === "leaves") {
    for (let i = 0; i < (kit ? 14 : 22); i++) {
      const x = S * 0.1 + rnd.next() * S * 0.8, y = S * 0.18 + rnd.next() * S * 0.78;
      if (kit) stamp(p, kit.maples[rnd.int(0, 8)], x, y, S * 0.2, S * 0.2, rnd.next() * Math.PI * 2);
      else { p.fillStyle = ["#C86A28", "#D8A040", "#A8442C", "#B08838"][rnd.int(0, 3)]; p.beginPath(); p.ellipse(x, y - 8, 9, 6, rnd.next() * 3, 0, Math.PI * 2); p.fill(); }
    }
  } else if (id === "log") {
    p.fillStyle = "#5A3E26"; p.fillRect(S * 0.06, S * 0.42, S * 0.84, S * 0.5); p.fillStyle = "#4A3220"; for (let i = 0; i < 6; i++) p.fillRect(S * 0.06, S * (0.48 + i * 0.07), S * 0.84, 3);
    p.fillStyle = "#C8A878"; p.beginPath(); p.ellipse(S * 0.9, S * 0.67, S * 0.08, S * 0.25, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#8A6A44"; p.lineWidth = 2; for (const r of [0.15, 0.09]) { p.beginPath(); p.ellipse(S * 0.9, S * 0.67, S * 0.08 * r / 0.15 * 0.8, S * r, 0, 0, Math.PI * 2); p.stroke(); }
    p.fillStyle = "rgba(90,130,60,0.7)"; for (let i = 0; i < 6; i++) { p.beginPath(); p.arc(S * (0.15 + rnd.next() * 0.6), S * 0.44, 6 + rnd.next() * 6, 0, Math.PI * 2); p.fill(); }
  } else if (id === "stump") {
    p.fillStyle = "#5A3E26"; p.beginPath(); p.moveTo(S * 0.2, S); p.lineTo(S * 0.26, S * 0.3); p.lineTo(S * 0.74, S * 0.3); p.lineTo(S * 0.8, S); p.closePath(); p.fill();
    p.fillStyle = "#C8A878"; p.beginPath(); p.ellipse(S / 2, S * 0.3, S * 0.24, S * 0.08, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#8A6A44"; p.lineWidth = 2; p.beginPath(); p.ellipse(S / 2, S * 0.3, S * 0.14, S * 0.045, 0, 0, Math.PI * 2); p.stroke();
  } else if (id === "boulder") {
    p.fillStyle = "#6E6A62"; p.beginPath(); p.ellipse(S / 2, S * 0.62, S * 0.46, S * 0.38, 0, 0, Math.PI * 2); p.fill(); p.fillRect(S * 0.04, S * 0.62, S * 0.92, S * 0.38);
    p.fillStyle = "#8A867C"; p.beginPath(); p.ellipse(S * 0.42, S * 0.45, S * 0.26, S * 0.16, -0.3, 0, Math.PI * 2); p.fill();
    p.fillStyle = "rgba(80,120,50,0.6)"; p.beginPath(); p.ellipse(S * 0.6, S * 0.3, S * 0.18, S * 0.06, 0, 0, Math.PI * 2); p.fill();
  } else if (id === "reeds") {
    blades(kit ? 16 : 22, 0.6, 1.0, (k) => `rgb(${Math.round(90 * k)},${Math.round(116 * k)},${Math.round(56 * k)})`);
    for (let i = 0; i < 4; i++) { const x = S * 0.25 + rnd.next() * S * 0.5, y = S * (0.08 + rnd.next() * 0.2); p.fillStyle = "#5A3A22"; p.beginPath(); p.ellipse(x, y, 5, 16, 0, 0, Math.PI * 2); p.fill(); }
  } else if (id === "steps") {
    for (const [x, y] of [[0.3, 0.25], [0.62, 0.45], [0.36, 0.72]]) { p.fillStyle = "#7A766C"; p.beginPath(); p.ellipse(S * x, S * y, S * 0.15, S * 0.11, 0.3, 0, Math.PI * 2); p.fill(); p.fillStyle = "rgba(255,255,255,0.2)"; p.beginPath(); p.ellipse(S * x - 5, S * y - 4, S * 0.07, S * 0.04, 0.3, 0, Math.PI * 2); p.fill(); }
  } else if (id === "hay") {
    p.fillStyle = "#C8A850"; p.beginPath(); p.ellipse(S / 2, S * 0.6, S * 0.44, S * 0.38, 0, 0, Math.PI * 2); p.fill(); p.fillRect(S * 0.06, S * 0.6, S * 0.88, S * 0.4);
    p.strokeStyle = "#A8883A"; p.lineWidth = 2; for (let i = 0; i < 40; i++) { const x = S * 0.1 + rnd.next() * S * 0.8, y = S * 0.3 + rnd.next() * S * 0.66; p.beginPath(); p.moveTo(x, y); p.lineTo(x + (rnd.next() - 0.5) * 20, y + 6); p.stroke(); }
    p.strokeStyle = "#7A5A2A"; p.lineWidth = 4; p.beginPath(); p.moveTo(S * 0.06, S * 0.66); p.lineTo(S * 0.94, S * 0.66); p.stroke();
  } else if (id === "snow") {
    p.fillStyle = "#EEF2F8"; for (let i = 0; i < 7; i++) { p.beginPath(); p.ellipse(S * (0.25 + rnd.next() * 0.5), S * (0.25 + rnd.next() * 0.5), S * (0.12 + rnd.next() * 0.16), S * (0.08 + rnd.next() * 0.12), rnd.next() * 3, 0, Math.PI * 2); p.fill(); }
  } else if (id === "barrel") {
    p.fillStyle = "#7A5230"; p.beginPath(); p.moveTo(S * 0.18, S * 0.06); p.quadraticCurveTo(S * 0.06, S * 0.53, S * 0.18, S); p.lineTo(S * 0.82, S); p.quadraticCurveTo(S * 0.94, S * 0.53, S * 0.82, S * 0.06); p.closePath(); p.fill();
    p.fillStyle = "#5A3A20"; for (let i = 1; i < 6; i++) p.fillRect(S * (0.12 + i * 0.13), S * 0.06, 3, S * 0.94);
    p.fillStyle = "#3A3A3A"; for (const y of [0.18, 0.5, 0.84]) p.fillRect(S * 0.1, S * y, S * 0.8, 7);
  } else if (id === "crate") {
    p.fillStyle = "#9A7448"; p.fillRect(S * 0.08, S * 0.12, S * 0.84, S * 0.88); p.strokeStyle = "#6A4A28"; p.lineWidth = 8; p.strokeRect(S * 0.12, S * 0.16, S * 0.76, S * 0.8);
    p.beginPath(); p.moveTo(S * 0.12, S * 0.16); p.lineTo(S * 0.88, S * 0.96); p.stroke(); p.lineWidth = 3; for (let i = 1; i < 4; i++) { p.beginPath(); p.moveTo(S * 0.12, S * (0.16 + i * 0.2)); p.lineTo(S * 0.88, S * (0.16 + i * 0.2)); p.stroke(); }
  } else if (id === "lamp") {
    p.fillStyle = "#2E2E30"; p.fillRect(S * 0.42, S * 0.12, S * 0.16, S * 0.88); p.fillRect(S * 0.3, S * 0.96, S * 0.4, S * 0.04);
    p.fillStyle = "#2E2E30"; p.fillRect(S * 0.22, S * 0.02, S * 0.56, S * 0.025); p.fillRect(S * 0.24, S * 0.1, S * 0.52, S * 0.02);
    p.fillStyle = "#F0D070"; p.fillRect(S * 0.28, S * 0.045, S * 0.44, S * 0.055);
  } else if (id === "cart") {
    p.fillStyle = "#8A6438"; p.fillRect(S * 0.08, S * 0.3, S * 0.74, S * 0.32); p.fillStyle = "#6A4A28"; for (let i = 0; i < 4; i++) p.fillRect(S * 0.08, S * (0.34 + i * 0.07), S * 0.74, 3);
    p.strokeStyle = "#6A4A28"; p.lineWidth = 6; p.beginPath(); p.moveTo(S * 0.82, S * 0.5); p.lineTo(S * 0.98, S * 0.72); p.stroke();
    for (const x of [0.25, 0.65]) { p.strokeStyle = "#4A3220"; p.lineWidth = 8; p.beginPath(); p.arc(S * x, S * 0.74, S * 0.18, 0, Math.PI * 2); p.stroke(); p.lineWidth = 3; for (let a = 0; a < 6; a++) { p.beginPath(); p.moveTo(S * x, S * 0.74); p.lineTo(S * x + Math.cos(a) * S * 0.18, S * 0.74 + Math.sin(a) * S * 0.18); p.stroke(); } }
  } else if (id === "stall") {
    p.fillStyle = "#5A3E26"; p.fillRect(S * 0.08, S * 0.18, 8, S * 0.82); p.fillRect(S * 0.92 - 8, S * 0.18, 8, S * 0.82);
    for (let i = 0; i < 6; i++) { p.fillStyle = i % 2 ? "#E8DCC0" : "#B0442C"; p.beginPath(); p.moveTo(S * (0.04 + i * 0.153), S * 0.08); p.lineTo(S * (0.04 + (i + 1) * 0.153), S * 0.08); p.lineTo(S * (0.04 + (i + 1) * 0.153), S * 0.24); p.quadraticCurveTo(S * (0.04 + (i + 0.5) * 0.153), S * 0.3, S * (0.04 + i * 0.153), S * 0.24); p.closePath(); p.fill(); }
    p.fillStyle = "#8A6438"; p.fillRect(S * 0.06, S * 0.62, S * 0.88, S * 0.1); p.fillRect(S * 0.12, S * 0.72, S * 0.76, S * 0.28);
    for (let i = 0; i < 7; i++) { p.fillStyle = ["#D8A040", "#C84A30", "#70A040", "#E8DCC0"][rnd.int(0, 3)]; p.beginPath(); p.arc(S * (0.16 + i * 0.11), S * 0.58, S * 0.04, 0, Math.PI * 2); p.fill(); }
  }
  return c;
};


// the dungeon's debris: painted at the props' size, for every look
CM.art.DEBRIS_IDS = ["cobweb", "dust", "coffinlid", "candle", "puddle", "slime", "rotcrate", "rubble", "pick", "rails", "armour", "glass", "urn", "candelabra", "frost", "weed", "shells", "oar", "fungi", "shard", "slag", "chains", "cogs", "bonepile", "roots", "coins", "books", "scrolls", "straw"];
CM.art.debrisProp = function (id, S) {
  const c = artCanvas(S), p = c.getContext("2d"), rnd = new CM.Random(CM.hashSeed(`debris:${id}`));
  const blob = (x, y, rx, ry, colour) => { p.fillStyle = colour; p.beginPath(); p.ellipse(x, y, rx, ry, rnd.next() * 3, 0, Math.PI * 2); p.fill(); };
  const scatter = (n, f) => { for (let i = 0; i < n; i++) f(S * 0.12 + rnd.next() * S * 0.76, S * 0.12 + rnd.next() * S * 0.76, i); };
  const stone = (k) => `rgb(${Math.round(110 * k)},${Math.round(104 * k)},${Math.round(96 * k)})`;
  switch (id) {
    case "cobweb": {
      p.strokeStyle = "rgba(230,230,235,0.95)"; p.lineWidth = 2;
      const ax = 2, bx = S - 2, top = 2, cx = S / 2, cy = S * 0.85;
      for (let i = 0; i <= 6; i++) { const t = i / 6, x = ax + (bx - ax) * t; p.beginPath(); p.moveTo(x, top); p.lineTo(cx + (x - cx) * 0.1, cy); p.stroke(); }
      for (let r = 1; r <= 5; r++) { const k = r / 5.5; p.beginPath(); for (let i = 0; i <= 6; i++) { const t = i / 6, x = ax + (bx - ax) * t, px = x + (cx - x) * k, py = top + (cy - top) * k + Math.sin(t * Math.PI) * 6; if (i) p.lineTo(px, py); else p.moveTo(px, py); } p.stroke(); }
      break;
    }
    case "dust": scatter(60, (x, y) => blob(x, y, 4 + rnd.next() * 8, 3 + rnd.next() * 5, `rgba(${170 + rnd.int(0, 30)},${160 + rnd.int(0, 30)},${140 + rnd.int(0, 20)},1)`)); break;
    case "coffinlid": p.fillStyle = "#5A4030"; p.beginPath(); p.moveTo(S * 0.3, S * 0.05); p.lineTo(S * 0.7, S * 0.05); p.lineTo(S * 0.85, S * 0.3); p.lineTo(S * 0.72, S * 0.95); p.lineTo(S * 0.28, S * 0.95); p.lineTo(S * 0.15, S * 0.3); p.closePath(); p.fill(); p.fillStyle = "#3A2A20"; p.fillRect(S * 0.47, S * 0.2, S * 0.06, S * 0.5); p.fillRect(S * 0.35, S * 0.32, S * 0.3, S * 0.06); break;
    case "candle": for (const [x, h] of [[0.35, 0.55], [0.6, 0.75], [0.48, 0.4]]) { p.fillStyle = "#E8DCC0"; p.fillRect(S * x - S * 0.06, S * (1 - h * 0.7), S * 0.12, S * h * 0.7); p.fillStyle = "#F0C040"; p.beginPath(); p.ellipse(S * x, S * (1 - h * 0.7) - S * 0.07, S * 0.04, S * 0.08, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#FFF0B0"; p.beginPath(); p.ellipse(S * x, S * (1 - h * 0.7) - S * 0.05, S * 0.02, S * 0.04, 0, 0, Math.PI * 2); p.fill(); } break;
    case "puddle": blob(S / 2, S / 2, S * 0.4, S * 0.28, "rgba(40,60,80,1)"); blob(S * 0.42, S * 0.42, S * 0.16, S * 0.06, "rgba(150,180,210,1)"); break;
    case "slime": scatter(10, (x, y) => blob(x, y, 10 + rnd.next() * 14, 6 + rnd.next() * 8, `rgb(${60 + rnd.int(0, 30)},${110 + rnd.int(0, 40)},${40 + rnd.int(0, 20)})`)); break;
    case "rotcrate": p.fillStyle = "#5A4630"; p.fillRect(S * 0.08, S * 0.2, S * 0.84, S * 0.8); p.strokeStyle = "#3A2C1C"; p.lineWidth = 6; p.strokeRect(S * 0.12, S * 0.24, S * 0.76, S * 0.72); p.fillStyle = "#1A1410"; p.beginPath(); p.moveTo(S * 0.5, S * 0.2); p.lineTo(S * 0.7, S * 0.2); p.lineTo(S * 0.6, S * 0.45); p.closePath(); p.fill(); p.fillStyle = "rgba(70,110,60,0.8)"; p.fillRect(S * 0.08, S * 0.86, S * 0.84, S * 0.14); break;
    case "rubble": case "bonepile": case "slag": {
      const col = id === "rubble" ? stone : id === "bonepile" ? (k) => `rgb(${Math.round(216 * k)},${Math.round(206 * k)},${Math.round(180 * k)})` : (k) => `rgb(${Math.round(60 * k)},${Math.round(52 * k)},${Math.round(48 * k)})`;
      for (let i = 0; i < 18; i++) { const t = i / 18, x = S * (0.15 + rnd.next() * 0.7), y = S * (0.98 - Math.sin(rnd.next() * Math.PI) * 0.55 * (1 - Math.abs(x / S - 0.5))); blob(x, Math.min(S * 0.92, y), S * (0.06 + rnd.next() * 0.07), S * (0.05 + rnd.next() * 0.05), col(0.7 + rnd.next() * 0.5)); }
      p.fillStyle = col(0.6); p.fillRect(S * 0.08, S * 0.9, S * 0.84, S * 0.1);
      if (id === "bonepile") { blob(S * 0.5, S * 0.42, S * 0.11, S * 0.1, "#E4DCC4"); blob(S * 0.46, S * 0.43, S * 0.025, S * 0.03, "#2A2420"); blob(S * 0.55, S * 0.43, S * 0.025, S * 0.03, "#2A2420"); }
      if (id === "slag") scatter(8, (x, y) => blob(x, S * 0.6 + y * 0.35, 4, 3, "#F08030"));
      break;
    }
    case "pick": p.strokeStyle = "#6A4A28"; p.lineWidth = 8; p.beginPath(); p.moveTo(S * 0.15, S * 0.85); p.lineTo(S * 0.75, S * 0.25); p.stroke(); p.strokeStyle = "#7A7A80"; p.lineWidth = 10; p.beginPath(); p.moveTo(S * 0.5, S * 0.1); p.quadraticCurveTo(S * 0.82, S * 0.18, S * 0.9, S * 0.5); p.stroke(); break;
    case "rails": p.fillStyle = "#5A3E26"; for (let i = 0; i < 5; i++) p.fillRect(S * 0.1, S * (0.12 + i * 0.18), S * 0.8, S * 0.07); p.fillStyle = "#6A6A70"; p.fillRect(S * 0.25, S * 0.04, S * 0.06, S * 0.92); p.fillRect(S * 0.69, S * 0.04, S * 0.06, S * 0.92); break;
    case "armour": blob(S * 0.4, S * 0.45, S * 0.22, S * 0.28, "#7A5A3A"); blob(S * 0.4, S * 0.42, S * 0.16, S * 0.2, "#8A6A48"); blob(S * 0.72, S * 0.7, S * 0.14, S * 0.1, "#6A5038"); p.fillStyle = "#3A2A1A"; p.fillRect(S * 0.32, S * 0.4, S * 0.16, 4); break;
    case "glass": scatter(14, (x, y) => { p.fillStyle = `rgba(${170 + rnd.int(0, 60)},${200 + rnd.int(0, 40)},${220 + rnd.int(0, 30)},1)`; p.beginPath(); p.moveTo(x, y); p.lineTo(x + 6 + rnd.next() * 10, y + rnd.next() * 8); p.lineTo(x + rnd.next() * 6, y + 6 + rnd.next() * 10); p.closePath(); p.fill(); }); break;
    case "urn": p.fillStyle = "#7A5A44"; p.beginPath(); p.moveTo(S * 0.38, S * 0.08); p.lineTo(S * 0.62, S * 0.08); p.lineTo(S * 0.58, S * 0.2); p.quadraticCurveTo(S * 0.92, S * 0.45, S * 0.66, S * 0.94); p.lineTo(S * 0.34, S * 0.94); p.quadraticCurveTo(S * 0.08, S * 0.45, S * 0.42, S * 0.2); p.closePath(); p.fill(); p.fillStyle = "#A07A5A"; p.fillRect(S * 0.24, S * 0.5, S * 0.52, 5); break;
    case "candelabra": p.fillStyle = "#8A7440"; p.fillRect(S * 0.46, S * 0.3, S * 0.08, S * 0.66); p.fillRect(S * 0.3, S * 0.94, S * 0.4, S * 0.06); p.fillRect(S * 0.2, S * 0.3, S * 0.6, S * 0.04); for (const x of [0.22, 0.5, 0.78]) { p.fillStyle = "#E8DCC0"; p.fillRect(S * x - 5, S * 0.18, 10, S * 0.12); p.fillStyle = "#F0C040"; p.beginPath(); p.ellipse(S * x, S * 0.13, 5, 9, 0, 0, Math.PI * 2); p.fill(); } break;
    case "frost": scatter(30, (x, y) => blob(x, y, 6 + rnd.next() * 10, 4 + rnd.next() * 6, `rgb(${200 + rnd.int(0, 40)},${220 + rnd.int(0, 30)},255)`)); break;
    case "weed": p.lineWidth = 4; p.lineCap = "round"; for (let i = 0; i < 9; i++) { const x = S * (0.15 + rnd.next() * 0.7), y = S * (0.15 + rnd.next() * 0.7), a = rnd.next() * Math.PI * 2; p.strokeStyle = `rgb(${60 + rnd.int(0, 40)},${80 + rnd.int(0, 40)},${40 + rnd.int(0, 20)})`; p.beginPath(); p.moveTo(x, y); p.bezierCurveTo(x + Math.cos(a) * 30, y + Math.sin(a) * 10, x + Math.cos(a) * 10, y + Math.sin(a) * 40, x + Math.cos(a + 1) * 40, y + Math.sin(a + 1) * 40); p.stroke(); } break;
    case "shells": scatter(8, (x, y) => { blob(x, y, 7, 5, "#E8D8C0"); p.strokeStyle = "#B8A080"; p.lineWidth = 1; p.beginPath(); p.moveTo(x - 6, y); p.lineTo(x + 6, y); p.stroke(); }); break;
    case "oar": p.strokeStyle = "#6A5038"; p.lineWidth = 7; p.beginPath(); p.moveTo(S * 0.1, S * 0.85); p.lineTo(S * 0.68, S * 0.32); p.stroke(); blob(S * 0.78, S * 0.22, S * 0.16, S * 0.08, "#5A4430"); break;
    case "fungi": for (const [x, s] of [[0.3, 0.7], [0.55, 1], [0.75, 0.55]]) { p.fillStyle = "#C8D8B0"; p.fillRect(S * x - S * 0.035 * s, S * (1 - 0.5 * s), S * 0.07 * s, S * 0.5 * s); p.fillStyle = "#90E0B0"; p.beginPath(); p.ellipse(S * x, S * (1 - 0.5 * s), S * 0.17 * s, S * 0.1 * s, 0, Math.PI, 0); p.fill(); } break;
    case "shard": for (const [x, h, a] of [[0.4, 0.95, -0.2], [0.58, 0.7, 0.25], [0.28, 0.5, -0.4]]) { p.save(); p.translate(S * x, S); p.rotate(a); p.fillStyle = "#B0E0F8"; p.beginPath(); p.moveTo(-S * 0.07, 0); p.lineTo(0, -S * h); p.lineTo(S * 0.07, 0); p.closePath(); p.fill(); p.fillStyle = "#E8F8FF"; p.beginPath(); p.moveTo(0, 0); p.lineTo(0, -S * h); p.lineTo(S * 0.07, 0); p.closePath(); p.fill(); p.restore(); } break;
    case "chains": p.strokeStyle = "#5A5A60"; p.lineWidth = 5; for (let i = 0; i < 9; i++) { const x = S * (0.15 + i * 0.085), y = S * (0.3 + Math.sin(i * 0.8) * 0.2); p.beginPath(); p.ellipse(x, y, 9, 6, i % 2 ? 0 : Math.PI / 2, 0, Math.PI * 2); p.stroke(); } break;
    case "cogs": for (const [x, y, r] of [[0.4, 0.45, 0.22], [0.7, 0.68, 0.14]]) { p.fillStyle = "#6E6A64"; for (let t = 0; t < 10; t++) { const a = t * Math.PI / 5; p.fillRect(S * x + Math.cos(a) * S * r - 5, S * y + Math.sin(a) * S * r - 5, 10, 10); } blob(S * x, S * y, S * r * 0.9, S * r * 0.9, "#7E7A72"); blob(S * x, S * y, S * r * 0.3, S * r * 0.3, "#3A3834"); } break;
    case "roots": p.lineCap = "round"; for (let i = 0; i < 5; i++) { const y = S * (0.15 + rnd.next() * 0.7); p.strokeStyle = "#5A3424"; p.lineWidth = 8 - i; p.beginPath(); p.moveTo(0, y); p.bezierCurveTo(S * 0.3, y + (rnd.next() - 0.5) * 60, S * 0.6, y + (rnd.next() - 0.5) * 60, S, y + (rnd.next() - 0.5) * 40); p.stroke(); } break;
    case "coins": scatter(16, (x, y) => { blob(x, y, 7, 5, "#E8C050"); blob(x - 1, y - 1, 4, 2, "#FFE890"); }); break;
    case "books": for (let i = 0; i < 4; i++) { const x = S * (0.2 + rnd.next() * 0.6), y = S * (0.2 + rnd.next() * 0.6); p.save(); p.translate(x, y); p.rotate(rnd.next() * 3); p.fillStyle = ["#6A2A2A", "#2A4A6A", "#3A5A2A", "#5A3A1A"][i]; p.fillRect(-S * 0.13, -S * 0.09, S * 0.26, S * 0.18); p.fillStyle = "#E8DCC0"; p.fillRect(-S * 0.11, S * 0.07, S * 0.22, 4); p.restore(); } break;
    case "scrolls": for (let i = 0; i < 3; i++) { const x = S * (0.25 + rnd.next() * 0.5), y = S * (0.25 + rnd.next() * 0.5); p.save(); p.translate(x, y); p.rotate(rnd.next() * 3); p.fillStyle = "#E8DCB8"; p.fillRect(-S * 0.18, -S * 0.05, S * 0.36, S * 0.1); p.fillStyle = "#C8B890"; p.beginPath(); p.arc(-S * 0.18, 0, S * 0.05, 0, Math.PI * 2); p.fill(); p.beginPath(); p.arc(S * 0.18, 0, S * 0.05, 0, Math.PI * 2); p.fill(); p.restore(); } break;
    case "straw": p.lineWidth = 3; for (let i = 0; i < 90; i++) { const x = S * (0.1 + rnd.next() * 0.8), y = S * (0.1 + rnd.next() * 0.8), a = rnd.next() * Math.PI; p.strokeStyle = `rgb(${190 + rnd.int(0, 40)},${160 + rnd.int(0, 30)},${80 + rnd.int(0, 30)})`; p.beginPath(); p.moveTo(x, y); p.lineTo(x + Math.cos(a) * 16, y + Math.sin(a) * 16); p.stroke(); } break;
    default: break;
  }
  return c;
};

// ---- props: the small things on the floors, painted at half size and packed four to a layer --------------------------
CM.art.prop = function (id, kit = null) {
  const S = ART_SIZE / 2, c = artCanvas(S), p = c.getContext("2d"), rnd = new CM.Random(CM.hashSeed(`prop:${id}`));
  if (CM.art.DEBRIS_IDS.includes(id)) return CM.art.debrisProp(id, S);
  if (!["tuft", "flowers", "pebbles", "rock", "bones", "skull"].includes(id) || (kit && id === "tuft")) return CM.art.surfaceProp(id, kit ? S * 2 : S, kit);   // (the surface's own, and with a kit the photographed tuft, at full size for the blades' detail)
  if (id === "tuft" || id === "flowers") {
    for (let i = 0; i < (id === "tuft" ? 26 : 14); i++) {
      const x = S * 0.15 + rnd.next() * S * 0.7, h = S * (0.35 + rnd.next() * 0.55), lean = (rnd.next() - 0.5) * S * 0.3, k = 0.7 + rnd.next() * 0.6;
      p.strokeStyle = `rgb(${Math.round(70 * k)},${Math.round(120 * k)},${Math.round(44 * k)})`; p.lineWidth = 3 + rnd.next() * 2; p.lineCap = "round";
      p.beginPath(); p.moveTo(x, S - 2); p.quadraticCurveTo(x + lean * 0.3, S - h * 0.6, x + lean, S - h); p.stroke();
    }
    if (id === "flowers") for (let i = 0; i < 5; i++) { const x = S * 0.2 + rnd.next() * S * 0.6, y = S * (0.25 + rnd.next() * 0.3); p.fillStyle = ["#F0E060", "#E8E8F0", "#C080E0", "#E06070"][rnd.int(0, 3)]; for (let a = 0; a < 5; a++) { p.beginPath(); p.arc(x + Math.cos(a * 1.26) * 5, y + Math.sin(a * 1.26) * 5, 4, 0, Math.PI * 2); p.fill(); } p.fillStyle = "#E0A020"; p.beginPath(); p.arc(x, y, 3, 0, Math.PI * 2); p.fill(); }
  } else if (id === "pebbles") {
    for (let i = 0; i < 9; i++) { const x = S * 0.15 + rnd.next() * S * 0.7, y = S * 0.15 + rnd.next() * S * 0.7, r = S * (0.04 + rnd.next() * 0.06), k = 0.75 + rnd.next() * 0.5; p.fillStyle = `rgb(${Math.round(120 * k)},${Math.round(114 * k)},${Math.round(104 * k)})`; p.beginPath(); p.ellipse(x, y, r * 1.3, r, rnd.next() * 3, 0, Math.PI * 2); p.fill(); p.fillStyle = "rgba(255,255,255,0.18)"; p.beginPath(); p.ellipse(x - r * 0.3, y - r * 0.3, r * 0.5, r * 0.35, 0, 0, Math.PI * 2); p.fill(); }
  } else if (id === "rock") {
    p.fillStyle = "#6E6860"; p.beginPath(); p.moveTo(S * 0.08, S - 2); p.lineTo(S * 0.16, S * 0.45); p.lineTo(S * 0.42, S * 0.2); p.lineTo(S * 0.74, S * 0.3); p.lineTo(S * 0.92, S * 0.6); p.lineTo(S * 0.94, S - 2); p.closePath(); p.fill();
    p.fillStyle = "#8A847A"; p.beginPath(); p.moveTo(S * 0.16, S * 0.45); p.lineTo(S * 0.42, S * 0.2); p.lineTo(S * 0.74, S * 0.3); p.lineTo(S * 0.5, S * 0.5); p.closePath(); p.fill();
    p.fillStyle = "#4E4A44"; p.beginPath(); p.moveTo(S * 0.74, S * 0.3); p.lineTo(S * 0.92, S * 0.6); p.lineTo(S * 0.94, S - 2); p.lineTo(S * 0.6, S - 2); p.lineTo(S * 0.5, S * 0.5); p.closePath(); p.fill();
  } else if (id === "bones") {
    p.lineCap = "round";
    for (let i = 0; i < 4; i++) { const x = S * 0.2 + rnd.next() * S * 0.6, y = S * 0.2 + rnd.next() * S * 0.6, a = rnd.next() * Math.PI, l = S * (0.15 + rnd.next() * 0.18); p.strokeStyle = "#D8D0B8"; p.lineWidth = 6; p.beginPath(); p.moveTo(x - Math.cos(a) * l, y - Math.sin(a) * l); p.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l); p.stroke(); p.fillStyle = "#E4DCC4"; for (const s of [-1, 1]) { p.beginPath(); p.arc(x + s * Math.cos(a) * l, y + s * Math.sin(a) * l, 5, 0, Math.PI * 2); p.fill(); } }
  } else if (id === "skull") {
    p.fillStyle = "#E0D8C0"; p.beginPath(); p.arc(S / 2, S * 0.48, S * 0.34, Math.PI, 0); p.lineTo(S * 0.8, S * 0.7); p.lineTo(S * 0.66, S * 0.94); p.lineTo(S * 0.34, S * 0.94); p.lineTo(S * 0.2, S * 0.7); p.closePath(); p.fill();
    p.fillStyle = "#2A2420"; p.beginPath(); p.ellipse(S * 0.36, S * 0.56, S * 0.09, S * 0.11, 0, 0, Math.PI * 2); p.fill(); p.beginPath(); p.ellipse(S * 0.64, S * 0.56, S * 0.09, S * 0.11, 0, 0, Math.PI * 2); p.fill();
    p.beginPath(); p.moveTo(S / 2, S * 0.66); p.lineTo(S * 0.45, S * 0.76); p.lineTo(S * 0.55, S * 0.76); p.closePath(); p.fill();
    for (let i = 0; i < 4; i++) p.fillRect(S * (0.38 + i * 0.07), S * 0.84, 4, S * 0.08);
  }
  return c;
};
// the props, four to a layer: `add(name, canvas)` as the set builders have it; `make(id)` paints one at half the layer's
// size. Returns `sub`: { "prop:<id>": [layer name, u0, v0, u1, v1] } for the renderer to find each one's corner.
CM.art.packProps = function (add, size, make) {
  const sub = {}, ids = Object.keys(CM.PROPS || {}), half = size / 2;
  for (let i = 0; i < ids.length; i += 4) {
    const c = artCanvas(size), p = c.getContext("2d"), name = `props:${i / 4}`;
    ids.slice(i, i + 4).forEach((id, j) => {
      const qx = (j % 2) * half, qy = Math.floor(j / 2) * half, pad = Math.max(1, size / 128);
      p.drawImage(make(id), qx + pad, qy + pad, half - 2 * pad, half - 2 * pad);
      sub[`prop:${id}`] = [name, (qx + pad) / size, (qy + pad) / size, (qx + half - pad) / size, (qy + half - pad) / size];
    });
    add(name, c);
  }
  return sub;
};

// ---- the whole set for a depth, as texture-array layers (the Drawn theme) ----------------------------------------------
CM.art.buildDrawn = function (theme) {
  const layers = [], index = {};
  const add = (name, canvas) => { index[name] = layers.length; layers.push(canvas); };
  const seed = CM.hashSeed(theme.name);
  add("wall", theme.tree ? CM.art.treeWall(theme, seed + 1) : CM.art.wall(theme, seed + 1, false));
  add("wall2", theme.tree ? CM.art.treeWall(theme, seed + 2) : CM.art.wall(theme, seed + 2, false));
  add("wallbones", theme.tree ? CM.art.treeWall(theme, seed + 3) : CM.art.wall(theme, seed + 3, true));
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
  add("phylactery", CM.art.phylactery());
  for (const m of CM.MONSTERS) { add(`monster:${m.name}`, CM.art.monster(m)); add(`monster:${m.name}:idle2`, CM.art.monster(m, false, "idle2")); add(`monster:${m.name}:attack`, CM.art.monster(m, false, "attack")); }
  add(`monster:${CM.BOSS.name}`, CM.art.monster(CM.BOSS, true)); add(`monster:${CM.BOSS.name}:idle2`, CM.art.monster(CM.BOSS, true, "idle2")); add(`monster:${CM.BOSS.name}:attack`, CM.art.monster(CM.BOSS, true, "attack"));
  for (const G of Object.values(CM.GUARDIANS)) { const k = G.size >= 1 ? 1.12 : 1.04; add(`monster:${G.name}`, CM.art.monster(G, k)); add(`monster:${G.name}:idle2`, CM.art.monster(G, k, "idle2")); add(`monster:${G.name}:attack`, CM.art.monster(G, k, "attack")); }
  add("nest", CM.art.nest()); add("throne", CM.art.throne()); add("anvil", CM.art.anvil()); add("ember", CM.art.ember());
  for (const [who, row] of Object.entries(CM.art.PEOPLE)) add(`npc:${who}`, CM.art.monster(row));
  for (const [id, O] of Object.entries(CM.ORES)) add(`vein:${id}`, CM.art.vein(O.colour));
  add("house", CM.art.house(4)); for (let s = 1; s <= 4; s++) add(`house${s}`, CM.art.house(s)); add("foundation", CM.art.foundation()); add("well", CM.art.well());
  add("bones", CM.art.bones()); add("rope", CM.art.rope()); add("plate", CM.art.plate(false)); add("plate_pressed", CM.art.plate(true)); add("door_riddle", CM.art.door("riddle"));
  add("fungus", CM.art.fungus()); add("crystal", CM.art.crystal()); add("root", CM.art.root());
  add("fx:spark", CM.art.fxSpark()); add("fx:shard", CM.art.fxShard()); add("fx:fire", CM.art.fxFire()); add("fx:frost", CM.art.fxFrost());
  add("fx:bolt", CM.art.fxBolt()); add("fx:force", CM.art.fxForce()); add("fx:holy", CM.art.fxHoly()); add("fx:arrow", CM.art.fxArrow());
  add("fx:leaf", CM.art.fxLeaf()); add("fx:ring", CM.art.fxRing());
  for (let f = 0; f < 3; f++) { add(`torch${f}`, CM.art.torch(f)); add(`water${f}`, CM.art.water(f)); }
  for (const [name, c] of Object.entries(CM.art.surfaceLayers())) add(name, c);
  const sub = CM.art.packProps(add, ART_SIZE, (id) => CM.art.prop(id));
  return { layers, index, size: ART_SIZE, crisp: false, sub };
};
