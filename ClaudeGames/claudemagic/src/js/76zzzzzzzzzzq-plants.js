"use strict";
// The plants, loaded and drawn (UPGRADE_PLAN_62.md phases 0-1): at start the baked plants (35d-plants.js) are inflated
// with the browser's DecompressionStream and parsed (37b-plants.js) into CM.plants. Their colours go into one picture,
// "pal:plants" (a shared layer, so below ground too): a vertex's uv is its colour's cell. Each model gets a vertex
// buffer in the floor's own layout, and each floor an instance buffer a model (CM.plantInstancesOf, 69zzs-plants.js),
// rebuilt when the floor's mesh is and when the party has walked four squares; the renderer draws them instanced
// (40-render.js: uStatic) after the figures. Where DecompressionStream is missing, or Detail is low, the pictures stand.
//   CM.plants -> { models } | null;  CM.plantsReady -> Promise<boolean>;  renderer.plantReach (the floor key reads it)
{ CM.plants = null; let atlas = null;
  const b64 = (s) => { const bin = atob(s), out = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i); return out; };
  CM.plantsReady = (async () => { try { const P = CM.plantsPack; if (!P || !P.data || typeof DecompressionStream === "undefined") return false;
      const t0 = performance.now(), ds = new DecompressionStream("deflate-raw"), stream = new Blob([b64(P.data)]).stream().pipeThrough(ds), bytes = new Uint8Array(await new Response(stream).arrayBuffer());
      CM.plants = CM.Plants.parse(bytes, P.manifest); CM.plants.loadedMs = Math.round(performance.now() - t0); atlas = CM.Plants.atlas(CM.plants.models); CM.plants.atlas = atlas;
      if (CM.renderer && CM.renderer.index && CM.renderer.index["pal:plants"] === undefined && CM.renderer.art && CM.renderer.setTextures) { try { CM.renderer.setTextures(CM.art.build(CM.renderer.art.theme, CM.renderer.art.look), false); } catch (e) { /* (the next floor's build has it) */ } }
      return true; } catch (e) { console.warn("plants: not loaded -", e && e.message); CM.plants = null; return false; } })();
  // the palette picture: every model's colours, a cell each
  const SIDE = 128;
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); if (!CM.plants || !atlas || set.index["pal:plants"] !== undefined) return set; const c = document.createElement("canvas"); c.width = c.height = SIDE; const p = c.getContext("2d"), n = atlas.n, cell = SIDE / n;
      for (const [name, cells] of Object.entries(atlas.cells)) { const m = CM.plants.models[name]; cells.forEach((ci, k) => { const [r, g, b] = m.palette[k]; p.fillStyle = `rgb(${r},${g},${b})`; p.fillRect(Math.floor((ci % n) * cell), Math.floor(Math.floor(ci / n) * cell), Math.ceil(cell), Math.ceil(cell)); }); }
      set.index["pal:plants"] = set.layers.length; set.layers.push(c); return set; }; }
  // the buffers: a model's vertices in the floor's layout (pos 3, uv 3, shade, fx 3), once a palette layer
  const R = CM.Renderer.prototype;
  R.plantBuffers = function (name) { const gl = this.gl, m = CM.plants.models[name], layer = this.index["pal:plants"]; if (!m || layer === undefined) return null; if (m.gl && m.gl.layer === layer && m.gl.ctx === gl) return m.gl;
    const n = atlas.n, cells = atlas.cells[name], data = new Float32Array(m.verts * 10), v = [0, 0, 0];
    for (let i = 0; i < m.verts; i++) { CM.Plants.vertex(m, i, v); const ci = cells[m.ci[i]], o = i * 10; data[o] = v[0]; data[o + 1] = v[1]; data[o + 2] = v[2]; data[o + 3] = ((ci % n) + 0.5) / n; data[o + 4] = (Math.floor(ci / n) + 0.5) / n; data[o + 5] = layer; data[o + 6] = 1; data[o + 7] = 0; data[o + 8] = 1; data[o + 9] = 0; }
    const vb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, vb); gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW); const ib = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, m.index, gl.STATIC_DRAW);
    return (m.gl = { vb, ib, count: m.index.length, big: m.index instanceof Uint32Array, layer, ctx: gl }); };
  // the instances: by model, for the floor about the party
  const groups = new Map(); let built = { key: null, at: null, version: -1 };
  R.plantInstances = function (game, fl) { const reach = this.plantReach || 0; if (!reach || !CM.plants) { groups.clear(); return; } const at = fl.pos, key = `${fl.number}|${this.floorKey}|${this.season}|${this.turnK}|${reach}`, v = (game.treesVersion || 0) + (game.plantsVersion || 0) * 1000;
    if (built.key === key && built.version === v && built.at && Math.abs(built.at[0] - at[0]) + Math.abs(built.at[1] - at[1]) < 4) return; built = { key, at: at.slice(), version: v };
    const by = new Map(); for (const p of CM.plantInstancesOf(game, fl, at, reach, this.density === undefined ? 1 : this.density)) { let a = by.get(p.model); if (!a) by.set(p.model, (a = [])); a.push(p.x, p.y, p.z, p.yaw, p.scale, p.sway || 0, p.small ? Math.min(reach, CM.PLANTS.smallReach) : reach, p.height, 0, 0, 0, 0, p.shade === undefined ? 1 : p.shade, 1, 0, 0); }
    groups.clear(); const gl = this.gl; for (const [model, arr] of by) { const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(arr), gl.STATIC_DRAW); groups.set(model, { buf, n: arr.length / 16, tint: CM.plantTintOf ? CM.plantTintOf(game, fl, model) : null }); } this.plantsDrawn = 0; };
  R.drawStatics = function (sky, eye) { const g = CM.game, fl = g && g.floor; if (!fl || !CM.plants || !this.index || this.index["pal:plants"] === undefined) return; this.plantInstances(g, fl); if (!groups.size) return; const gl = this.gl;
    gl.uniform1f(this.loc.uStatic, 1); gl.uniform1f(this.loc.uBump, 0); let drawn = 0;
    for (const [model, G] of groups) { const B = this.plantBuffers(model); if (!B) continue; gl.bindBuffer(gl.ARRAY_BUFFER, B.vb); this._attributes(); gl.bindBuffer(gl.ARRAY_BUFFER, G.buf);
      for (let i = 0; i < 4; i++) { gl.enableVertexAttribArray(4 + i); gl.vertexAttribPointer(4 + i, 4, gl.FLOAT, false, 64, i * 16); gl.vertexAttribDivisor(4 + i, 1); }
      gl.uniform3fv(this.loc.uTint, G.tint || [1, 1, 1]); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, B.ib); gl.drawElementsInstanced(gl.TRIANGLES, B.count, B.big ? gl.UNSIGNED_INT : gl.UNSIGNED_SHORT, 0, G.n); drawn += G.n; }
    for (let i = 4; i < 8; i++) { gl.vertexAttribDivisor(i, 0); gl.disableVertexAttribArray(i); gl.vertexAttrib4f(i, 0, 0, 0, 0); } gl.uniform1f(this.loc.uStatic, 0); gl.uniform3fv(this.loc.uTint, [1, 1, 1]); this.plantsDrawn = drawn; };
  // the reach, by the Detail setting and the pack's presence (the floor's mesh key reads it: the far pictures change with it)
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const want = CM.plants && !CM.plantsOff ? CM.PLANTS.reach(r.density === undefined ? 1 : r.density) : 0; if (r.plantReach !== want) r.plantReach = want; };
}
