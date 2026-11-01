"use strict";
// The South Fields' crops, drawn (v19.0): the crop pack (35b-croppack.js: [LPC] Crops and josehzz's crops, a 32x64 cell
// a frame) decoded with the other packs, and laid eight to a texture layer in every look's set - each frame a corner of
// its layer, as the props are - under the names "crop:<frame>". CM.plotSprites says what stands on a plot: two plants
// at the plot's stage, and the darker earth of a plot watered today. The rules are 69j-fields.js.
{ const CP = CM.cropPack;
  CM.art.crops = { ready: false, atlas: null };
  { const load0 = CM.art.load; CM.art.load = function () { const P = CM.art.packs; if (P.cropsWaited) return P.loading || load0.call(this); P.cropsWaited = true;   // (the crops first, then the packs: ready means both)
      if (!CP || typeof Image === "undefined") return load0.call(this);
      const crops = new Promise((done) => { const im = new Image(); im.onload = () => { CM.art.crops.atlas = im; CM.art.crops.ready = true; done(); }; im.onerror = () => done(); im.src = CP.atlas; });
      P.loading = crops.then(() => { P.loading = null; return load0.call(this); }); return P.loading; }; }
  // every frame, eight to a layer (four across, two down), each a corner of it for the renderer
  CM.art.packCrops = function (add, size, crisp) { const sub = {}, A = CM.art.crops.atlas; if (!A || !CP) return sub; const [cw, ch] = CP.cell, n = Math.ceil(A.width / cw) * Math.ceil(A.height / ch), sw = size / 4, sh = size / 2;
    for (let i = 0; i < n; i += 8) { const c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"); p.imageSmoothingEnabled = false; const name = `crops:${i / 8}`;
      for (let j = 0; j < 8 && i + j < n; j++) { const f = i + j, fx = (f % CP.cols) * cw, fy = Math.floor(f / CP.cols) * ch, qx = (j % 4) * sw, qy = Math.floor(j / 4) * sh, pad = crisp ? 0 : 1;
        p.drawImage(A, fx, fy, cw, ch, qx + pad, qy + pad, sw - 2 * pad, sh - 2 * pad); sub[`crop:${f}`] = [name, (qx + pad) / size, (qy + pad) / size, (qx + sw - pad) / size, (qy + sh - pad) / size]; }
      add(name, c); }
    return sub; };
  { const build0 = CM.art.build; CM.art.build = function (theme, look) { const set = build0.call(this, theme, look); if (!CM.art.crops.ready) return set;
      const add = (name, canvas) => { set.index[name] = set.layers.length; set.layers.push(canvas); }; set.sub = Object.assign({}, set.sub || {}, CM.art.packCrops(add, set.size, set.crisp)); add("scarecrow", CM.art.scarecrow(set.size)); return set; }; }
  // the scarecrow (v19.1): a post, a crossbar, a sacking head under a straw hat, a patched coat with straw at the cuffs
  CM.art.scarecrow = function (size) { const c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"), u = size / 64;
    p.fillStyle = "#6A4A28"; p.fillRect(30 * u, 16 * u, 4 * u, 48 * u); p.fillRect(12 * u, 26 * u, 40 * u, 4 * u);
    p.fillStyle = "#7A5A9A"; p.fillRect(20 * u, 24 * u, 24 * u, 22 * u); p.fillStyle = "#5A4A7A"; p.fillRect(14 * u, 25 * u, 8 * u, 7 * u); p.fillRect(42 * u, 25 * u, 8 * u, 7 * u); p.fillStyle = "#B07A3A"; p.fillRect(26 * u, 34 * u, 7 * u, 6 * u);
    p.fillStyle = "#E8C860"; for (const x of [11, 50]) { p.fillRect(x * u, 26 * u, 3 * u, 6 * u); } p.fillRect(23 * u, 46 * u, 18 * u, 3 * u);
    p.fillStyle = "#D8C090"; p.beginPath(); p.arc(32 * u, 17 * u, 7 * u, 0, Math.PI * 2); p.fill(); p.fillStyle = "#3A2A1A"; p.fillRect(28 * u, 15 * u, 2 * u, 2 * u); p.fillRect(34 * u, 15 * u, 2 * u, 2 * u); p.fillRect(29 * u, 20 * u, 6 * u, 1 * u);
    p.fillStyle = "#C8A040"; p.fillRect(20 * u, 10 * u, 24 * u, 3 * u); p.fillRect(25 * u, 4 * u, 14 * u, 7 * u); p.fillStyle = "#8A2A2A"; p.fillRect(25 * u, 9 * u, 14 * u, 2 * u); return c; };
  // what stands on a plot
  const SPOTS = [[-0.22, -0.14], [0.2, 0.16]];
  CM.plotFrame = (game, key) => { const st = game.plotStage(key), F = game.fields(), P = F.plots[key], fr = CP && CP.frames; if (!fr) return null;
    if (st === "bare" || st === "tilled") return null; if (st === "sown") return fr.sown; const C = fr[P.crop]; if (!C) return fr.sown;
    return st === "ripe" ? C.s[3] : st === "after" ? C.after : C.s[Math.max(0, Math.min(2, st - 1))]; };
  CM.plotSprites = (game, key, x, y) => { const out = [], P = game.fields().plots[key];
    if (P && P.t && (P.w || P.wetToday)) out.push({ x, y, layer: "shadow", flat: true, w: 0.92, alpha: 0.35 });   // (watered: the earth darker)
    const f = CM.plotFrame(game, key); if (f === null || f === undefined) return out;
    if (f === CP.frames.sown) { out.push({ x, y, layer: `crop:${f}`, w: 0.34, h: 0.68, shade: 0.95 }); return out; }   // (one mound of turned earth)
    for (const [dx, dz] of SPOTS) out.push({ x, y, dx, dz, layer: `crop:${f}`, w: 0.4, h: 0.8, shade: 0.95 });
    return out; };
}
