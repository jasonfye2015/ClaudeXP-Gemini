"use strict";
// Painting off the main thread (v26.3, UPGRADE_PLAN_21.md): the sets of pictures are painted in a worker, where the
// browser has one that can paint (an OffscreenCanvas), so that making a set never stops the screen. The worker is the
// game's own code - everything before 80-main.js, as the page has it - with a few stand-ins for the page; it is given
// the looks' packs as bitmaps once they are decoded. While the party plays, the sets it will want next are painted
// there ahead of time - the next band's down the shaft, the town's and the Wood's from below - and come back as
// bitmaps that go straight to the graphics card. Asked for a set it hasn't got, the page paints it the old way.
// the theme of a floor, as the page's useTheme chooses it (the worker has the same)
CM.themeOfFloor = (number, dream) => { const jk = CM.isJokerFloor && CM.isJokerFloor(number), ins = CM.isInterior && CM.isInterior(number), uc = CM.isUndercroft(number) || CM.isTowerFloor(number) || jk || ins;
  const special = number === 0 ? CM.TOWN_THEME : number === -1 ? CM.WOOD_THEME : CM.isTowerFloor(number) ? CM.TOWER_THEME : jk ? CM.JOKER_THEME : ins ? CM.themeFor(number) : uc ? CM.UNDERCROFT_THEME : null;
  return special || (dream ? CM.dreamTheme(CM.THEMES[CM.themeIndex(number)]) : CM.THEMES[CM.themeIndex(number)]); };
{ if (typeof self !== "undefined" && self.CM_WORKER) { /* (inside the worker: nothing of this here) */ } else {
  const AW = CM.ARTWORKER = { on: false, ready: {}, asked: new Set(), worker: null, made: 0, ms: 0 };

  const WORKER_SIDE = `
    self.CM_WORKER = true;
    onmessage = async (e) => { const m = e.data;
      if (m.init) { CM.art.packs.atlas = m.atlas || null; for (const [k, b] of m.stone || []) CM.art.packs.stone[k] = b; CM.art.packs.ready = true; if (CM.art.crops && m.crops) { CM.art.crops.atlas = m.crops; CM.art.crops.ready = true; } postMessage({ inited: true }); return; }
      if (m.build) { try { const t = performance.now(); const was = CM.art.season; CM.art.season = m.season;
          let set; try { set = CM.art.build(CM.themeOfFloor(m.number, m.dream), m.look); } finally { CM.art.season = was; }
          // each picture as the page will send it up: the small ones as bitmaps (they are packed four to a layer there),
          // the rest as raw pixels at the size their texture takes (the quickest way up), the shared ones left out when the
          // page holds them already, the outdoors' below ground not at all
          const look = String(set.sharedKey || "drawn:drawn").split(":")[1] || "drawn", Z = CM.art.LAYER_SIZES[look] || CM.art.LAYER_SIZES.drawn, own = Math.min(set.size || 256, Z.own), names = [], transfer = [];
          for (const [n, i] of Object.entries(set.index)) names[i] = n;
          const layers = await Promise.all(set.layers.map(async (c, i) => { const n = names[i]; if (!n || !c) return null;
            const theme = CM.art.isThemeLayer(n, set.theme), sfc = CM.art.isSurfaceLayer(n), small = CM.art.isPackable(n);
            if (sfc && !theme) return null; if (!theme && !small && m.skipShared) return null;
            if (small) { const b = await createImageBitmap(c); transfer.push(b); return b; }
            const size = theme && sfc && !CM.art.isPhotoLayer(n) ? Z.surf : theme ? own : Z.shared, o = new OffscreenCanvas(size, size), p = o.getContext("2d");
            p.imageSmoothingEnabled = !set.crisp; p.drawImage(c, 0, 0, size, size); const d = p.getImageData(0, 0, size, size); transfer.push(d.data.buffer); return { w: size, h: size, px: d.data.buffer }; }));
          postMessage({ key: m.key, number: m.number, index: set.index, sub: set.sub || {}, size: set.size, crisp: Boolean(set.crisp), sharedKey: set.sharedKey, layers, partial: Boolean(m.skipShared), ms: performance.now() - t }, transfer);
        } catch (err) { postMessage({ key: m.key, err: String(err && err.stack || err).slice(0, 400) }); } } };`;
  const SHIM = [
    "self.window = self; const noop = () => {};",
    "const el = () => ({ style: {}, dataset: {}, classList: { add: noop, remove: noop, toggle: noop, contains: () => false }, appendChild: noop, removeChild: noop, addEventListener: noop, removeEventListener: noop, setAttribute: noop, querySelector: () => null, querySelectorAll: () => [], insertAdjacentElement: noop, getContext: () => null, getBoundingClientRect: () => ({ left: 0, top: 0, width: 0, height: 0 }) });",
    "self.document = { createElement: (t) => t === 'canvas' ? new OffscreenCanvas(1, 1) : el(), body: el(), documentElement: el(), head: el(), addEventListener: noop, removeEventListener: noop, querySelector: () => null, querySelectorAll: () => [], getElementById: () => null, fonts: { ready: Promise.resolve() } };",
    "self.localStorage = { getItem: () => null, setItem: noop, removeItem: noop, key: () => null, length: 0 }; self.matchMedia = () => ({ matches: false, addEventListener: noop }); self.requestAnimationFrame = (f) => setTimeout(() => f(performance.now()), 16); self.cancelAnimationFrame = noop; self.Image = class { set src(v) {} };",
    "self.CM_WORKER = true;",
    "{ const gc0 = OffscreenCanvas.prototype.getContext; OffscreenCanvas.prototype.getContext = function (kind, o) { return gc0.call(this, kind, kind === '2d' ? Object.assign({ willReadFrequently: true }, o || {}) : o); }; }",   /* (painted in software: the graphics card is the page's) */
  ].join("\n");
  AW.start = () => {
    if (AW.worker || CM.artWorkerOff || typeof Worker === "undefined" || typeof OffscreenCanvas === "undefined" || typeof createImageBitmap === "undefined") return;
    let src = null; try { src = [...document.scripts].map((s) => s.textContent).find((t) => t.includes("// ---- " + "00-util.js ----")); } catch (e) { /* (no script to read) */ }
    if (!src) return; const cut = src.indexOf("// ---- " + "80-main.js ----")   /* (in two pieces: this file holds the words too) */; if (cut < 0) return;
    CM.startLog.push([Math.round(performance.now()), "worker starting"]);
    let w; try { w = new Worker(URL.createObjectURL(new Blob([SHIM + "\n" + src.slice(0, cut) + "\n;" + WORKER_SIDE], { type: "text/javascript" }))); } catch (e) { return; }
    AW.worker = w;
    w.onerror = () => { AW.on = false; AW.worker = null; };                  // (a worker that fails: the old way, quietly)
    w.onmessage = (e) => { const m = e.data; if (m.inited) { AW.on = true; CM.startLog.push([Math.round(performance.now()), "worker ready"]); return; }
      CM.startLog.push([Math.round(performance.now()), `worker painted ${m.key} (${Math.round(m.ms || 0)} ms there)`]);
      if (m.err || !m.key) { AW.asked.delete(m.key); return; }
      const layers = m.layers.map((l) => (l && l.px ? new ImageData(new Uint8ClampedArray(l.px), l.w, l.h) : l));
      AW.ready[m.key] = { index: m.index, sub: m.sub, size: m.size, crisp: m.crisp, sharedKey: m.sharedKey, layers, partial: m.partial, theme: AW.themes[m.key], fromWorker: true }; AW.made++; AW.ms += m.ms; };
    const bmp = (im) => (im ? createImageBitmap(im) : Promise.resolve(null));
    Promise.all([bmp(CM.art.packs.atlas), Promise.all(Object.entries(CM.art.packs.stone).map(([k, im]) => bmp(im).then((b) => [k, b]))), bmp(CM.art.crops && CM.art.crops.ready ? CM.art.crops.atlas : null)])
      .then(([atlas, stone, crops]) => { const list = [atlas, crops, ...stone.map((s) => s[1])].filter(Boolean); w.postMessage({ init: true, atlas, stone, crops }, list); }).catch(() => { AW.worker = null; });
  };
  AW.themes = {};
  // ask for a set ahead (the page's own key for it); taken when the page wants it
  CM.artAhead = (key, number, look, season, dream) => { if (!AW.on || AW.ready[key] || AW.asked.has(key)) return; AW.asked.add(key); AW.themes[key] = CM.themeOfFloor(number, dream); AW.worker.postMessage({ build: true, key, number, look, season, dream: Boolean(dream), skipShared: Boolean(CM.renderer && CM.renderer.sharedKey && CM.renderer.sharedKey.startsWith(`${look}:`)) }); };
  CM.artTake = (key) => { const s = AW.ready[key]; if (!s) return null; delete AW.ready[key]; AW.asked.delete(key); return s; };
  CM.artForget = (key) => { AW.asked.delete(key); };
  // once the packs are decoded (and the crops'), the worker is started
  const load0 = CM.art.load; CM.art.load = function (...a) { const p = load0.apply(this, a); Promise.resolve(p).then(() => { const t0 = performance.now(), wait = () => { if ((CM.art.crops && CM.art.crops.ready) || performance.now() - t0 > 8000) setTimeout(AW.start, 1200); else setTimeout(wait, 250); }; wait(); }); return p; };
} }
