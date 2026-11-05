"use strict";
// The plants' reader (UPGRADE_PLAN_62.md phase 0): parses the binary tools/plants.py bakes into 35d-plants.js
// (CM.plantsPack: manifest, data as deflated base64) into typed arrays. No DOM, no WebGL here: the Node tests read
// it as the game does. Inflating is the caller's (the window inflates with DecompressionStream in
// 76zzzzzzzzzzq-plants.js; Node with zlib.inflateRawSync).
//   CM.Plants.parse(bytes, manifest) -> { models: { name: model } }
//     model: { name, verts, tris, box [lo, hi], pos Int16Array(3n), ci Uint8Array(n), index Uint16Array|Uint32Array,
//              palette [[r, g, b]], tags }
//   CM.Plants.measure(model) -> { height, width, foot, centre [x, z] }   in the pack's metres
//   CM.Plants.vertex(model, i, out?) -> [x, y, z]                        a vertex in metres
//   CM.Plants.atlas(models) -> { n, cells: { name: [cellIndex...] } }    the palette atlas: every model's colours in
//     one square grid of n x n cells (the window paints it as the "pal:plants" layer; a vertex's uv is its cell's centre)
{ const parseModel = (bytes, dv, off, m) => { let o = off; const verts = dv.getUint32(o, true), nidx = dv.getUint32(o + 4, true); o += 8;
    const pos = new Int16Array(verts * 3); for (let i = 0; i < verts * 3; i++) { pos[i] = dv.getInt16(o, true); o += 2; }
    const ci = bytes.slice(o, o + verts); o += verts;
    let index; if (m.big) { index = new Uint32Array(nidx); for (let i = 0; i < nidx; i++) { index[i] = dv.getUint32(o, true); o += 4; } } else { index = new Uint16Array(nidx); for (let i = 0; i < nidx; i++) { index[i] = dv.getUint16(o, true); o += 2; } }
    if (o !== off + m.length) throw new Error(`plants: ${verts} verts, ${nidx} indices: ${o - off} of ${m.length}`);
    return { verts, tris: nidx / 3, box: m.box, pos, ci, index, palette: m.palette, tags: m.tags || [] }; };
  CM.Plants = {
    parse(bytes, manifest) { const dv = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength), models = {}; for (const [name, m] of Object.entries(manifest.models)) { models[name] = parseModel(bytes, dv, m.offset, m); models[name].name = name; } return { models }; },
    vertex(model, i, out = [0, 0, 0]) { const lo = model.box[0], hi = model.box[1]; for (let k = 0; k < 3; k++) out[k] = lo[k] + (model.pos[i * 3 + k] + 32767) / 65534 * (hi[k] - lo[k]); return out; },
    measure(model) { if (model.measured) return model.measured; const lo = model.box[0], hi = model.box[1]; return (model.measured = { height: Math.max(1e-3, hi[1] - lo[1]), width: Math.max(1e-3, hi[0] - lo[0], hi[2] - lo[2]), foot: lo[1], centre: [(lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2] }); },
    atlas(models) { const cells = {}; let n = 0; for (const [name, m] of Object.entries(models)) { cells[name] = m.palette.map(() => n++); } const side = Math.max(1, Math.ceil(Math.sqrt(n))); return { n: side, count: n, cells }; },
  };
}
