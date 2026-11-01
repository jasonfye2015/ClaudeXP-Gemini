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
      const add = (name, canvas) => { set.index[name] = set.layers.length; set.layers.push(canvas); }; set.sub = Object.assign({}, set.sub || {}, CM.art.packCrops(add, set.size, set.crisp)); return set; }; }
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
