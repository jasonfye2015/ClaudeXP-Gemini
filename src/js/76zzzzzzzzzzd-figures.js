"use strict";
// The figures, loaded (v65.0, UPGRADE_PLAN_60.md phase 0): at start the baked figures (35c-figures.js) are inflated
// with the browser's DecompressionStream and parsed (37-figures.js) off the main path, and kept as CM.figures - the
// models, their clips and textures - for the renderer to draw from (phase 1). Nothing is drawn from them yet. Where
// the browser has no DecompressionStream, or anything fails, CM.figures stays null and the painted figures stand.
//   CM.figures -> { models, clips } | null;  CM.figuresReady -> Promise<boolean>
{ CM.figures = null;
  const b64 = (s) => { const bin = atob(s), out = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i); return out; };
  CM.figuresReady = (async () => { try { const P = CM.figuresPack; if (!P || !P.data || typeof DecompressionStream === "undefined") return false;
      const t0 = performance.now(), ds = new DecompressionStream("deflate-raw"), stream = new Blob([b64(P.data)]).stream().pipeThrough(ds), bytes = new Uint8Array(await new Response(stream).arrayBuffer());
      CM.figures = CM.Figures.parse(bytes, P.manifest); CM.figures.loadedMs = Math.round(performance.now() - t0);
      return true; } catch (e) { console.warn("figures: not loaded -", e && e.message); CM.figures = null; return false; } })();
}
