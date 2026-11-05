"use strict";
// The figures, drawn (v66.0, UPGRADE_PLAN_60.md phase 1): a townsperson, a pet or a monster with a body in
// src/models/figures.json is drawn as that body - skinned by the renderer (40-render.js: uSkin, uJoints, uModel) in
// its idle clip, stood its billboard's height, turned to face the party, tinted as the mapping says - in place of its
// painted picture, within fourteen squares; farther off, and at Low detail, and under Settings > Figures: Painted,
// the picture stands as before. The pictures: a model's own texture, or for an untextured one a palette of its
// colours, go up as the figures' texture array (layers 3000 and up). The shadows, marks and statuses are untouched.
{ const REACH = 14, TEX = 256, b64png = (bytes) => { let s = ""; for (let i = 0; i < bytes.length; i += 8192) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 8192)); return "data:image/png;base64," + btoa(s); };
  const on = (game) => Boolean(CM.figures && game && !(game.settings && (game.settings.figures === "painted" || game.settings.detail === "low")));
  // the figures' pictures: made once the figures are parsed (the PNGs decoded, the palettes painted), then uploaded
  const pictures = async (F) => { const list = [], names = Object.keys(F.models); for (const name of names) { const m = F.models[name]; const c = document.createElement("canvas"); c.width = c.height = TEX; const p = c.getContext("2d");
      if (m.texture) { try { const img = new Image(); img.src = b64png(m.texture); await img.decode(); p.imageSmoothingEnabled = true; p.drawImage(img, 0, 0, TEX, TEX); } catch (e) { p.fillStyle = "#A08870"; p.fillRect(0, 0, TEX, TEX); } m.uvf = new Float32Array(m.verts * 2); for (let i = 0; i < m.verts * 2; i++) m.uvf[i] = m.uv[i] / 65535; }
      else { const P = CM.Figures.palette(m), cell = TEX / P.n; P.colours.forEach(([r, g, b], i) => { p.fillStyle = `rgb(${r},${g},${b})`; p.fillRect((i % P.n) * cell, Math.floor(i / P.n) * cell, cell + 1, cell + 1); }); m.uvf = P.uv; }
      m.layer = 3000 + list.length; list.push(c); } return list; };
  const R = CM.Renderer.prototype;
  R.figuresUp = async function (F) { const gl = this.gl; if (!gl || this.figTex) return; const pics = await pictures(F); if (!gl.isContextLost || !gl.isContextLost()) { this.figTex = gl.createTexture(); this._upload(this.figTex, pics, TEX, false, false); this.figLayers = pics.length; } };
  // a model's GL buffers: the renderer's ten floats a vertex (position, uv + layer, shade, fx) and the four joints and weights after them
  const buffersOf = (r, m) => { if (m.gl) return m.gl; const gl = r.gl, n = m.verts, data = new Float32Array(n * 18), lo = m.box[0], hi = m.box[1];
    for (let i = 0; i < n; i++) { const o = i * 18; for (let k = 0; k < 3; k++) data[o + k] = lo[k] + (m.pos[i * 3 + k] + 32767) / 65534 * (hi[k] - lo[k]); data[o + 3] = m.uvf[i * 2]; data[o + 4] = m.uvf[i * 2 + 1]; data[o + 5] = m.layer; data[o + 6] = 1; data[o + 7] = 0; data[o + 8] = 1; data[o + 9] = 0;
      for (let k = 0; k < 4; k++) { data[o + 10 + k] = m.joints[i * 4 + k]; data[o + 14 + k] = m.weights[i * 4 + k] / 255; } }
    const vb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, vb); gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW); const ib = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, m.index, gl.STATIC_DRAW);
    const jt = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, jt); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32F, 4, m.skeleton.n, 0, gl.RGBA, gl.FLOAT, null); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    return (m.gl = { vb, ib, jt, count: m.index.length, big: m.index instanceof Uint32Array, pose: new Float32Array(m.skeleton.n * 16) }); };
  // which sprites become figures: taken out of the sprite list, kept for drawFigures
  { const ss0 = R.setSprites; R.setSprites = function (list) { const g = CM.game, F = CM.figures; this.figList = [];
      if (!on(g) || !this.figTex || !F) return ss0.call(this, list);
      const fl = g.floor, px = fl ? fl.pos[0] : 0, py = fl ? fl.pos[1] : 0, keep = [];
      for (const s of list) { const key = CM.Figures.keyOf(s.layer), fig = key && CM.Figures.figureOf(key); const m = fig && fig !== "painted" && F.models[fig.model];
        if (!m || s.flat || s.hang !== undefined || s.axis || Math.abs(s.x - px) + Math.abs(s.y - py) > REACH) { keep.push(s); continue; }
        const parts = s.layer.split(":"), pose = parts[2] || "", clip = pose === "attack" ? "attack" : (s.walking ? "walk" : "idle");
        const scale = CM.Figures.fit(fig, m, s.h, s.w), ms = CM.Figures.measure(m);   // (the feet at the floor and the body centred on its square, whatever the model's own origin)
        this.figList.push({ s, fig, m, key, clip, x: s.x + 0.5 + (s.dx || 0), z: s.y + 0.5 + (s.dz || 0), y: (s.base || 0) + (s.lift || 0) - ms.foot * scale, scale, centre: ms.centre, phase: (CM.hashSeed(`${key}:${s.x},${s.y}`) % 1000) / 1000 }); }
      return ss0.call(this, keep); }; }
  const M16 = new Float32Array(16);
  R.drawFigures = function (sky, eye) { const L = this.figList; if (!L || !L.length || !this.figTex) return; const gl = this.gl, t = this.time || 0;
    gl.activeTexture(gl.TEXTURE4); gl.bindTexture(gl.TEXTURE_2D_ARRAY, this.figTex); gl.uniform1i(this.loc.uFig, 4); gl.activeTexture(gl.TEXTURE5); gl.uniform1i(this.loc.uJoints, 5);
    gl.uniform1f(this.loc.uSkin, 1); gl.uniform1f(this.loc.uBump, 0);
    for (const f of L) { const B = buffersOf(this, f.m), clip = f.m.clips[f.clip] || f.m.clips.idle || null, T = clip ? clip.frames / clip.fps : 1;
      CM.Figures.pose(f.m, clip, (t + f.phase * T) * (f.s.ghost ? 0.6 : 1), B.pose); gl.bindTexture(gl.TEXTURE_2D, B.jt); gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 4, f.m.skeleton.n, gl.RGBA, gl.FLOAT, B.pose);
      const yaw = Math.atan2(eye[0] - f.x, eye[2] - f.z) + (f.fig.yaw || 0);   // (faces the party; phase 2 gives them their own way)
      const c = Math.cos(yaw) * f.scale, sn = Math.sin(yaw) * f.scale, cx = f.centre[0], cz = f.centre[1];   // (the body's centre on the square: the model's own centre taken out, turned and scaled as it will be)
      gl.uniformMatrix4fv(this.loc.uModel, false, CM.Figures.modelMatrix(M16, f.x - (c * cx + sn * cz), f.y, f.z - (-sn * cx + c * cz), yaw, f.scale));
      const tint = f.fig.tint; gl.uniform3fv(this.loc.uTint, tint ? [tint[0] / 255, tint[1] / 255, tint[2] / 255] : [1, 1, 1]);
      gl.uniform3fv(this.loc.uFigFx, [f.s.flash || 0, f.s.alpha === undefined ? 1 : f.s.alpha, 0]);
      gl.bindBuffer(gl.ARRAY_BUFFER, B.vb); const bytes = 18 * 4; gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, bytes, 0); gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1, 3, gl.FLOAT, false, bytes, 12);
      gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2, 1, gl.FLOAT, false, bytes, 24); gl.enableVertexAttribArray(3); gl.vertexAttribPointer(3, 3, gl.FLOAT, false, bytes, 28);
      for (let i = 4; i < 8; i++) { gl.disableVertexAttribArray(i); gl.vertexAttrib4f(i, 0, 0, 0, 0); } gl.enableVertexAttribArray(8); gl.vertexAttribPointer(8, 4, gl.FLOAT, false, bytes, 40); gl.enableVertexAttribArray(9); gl.vertexAttribPointer(9, 4, gl.FLOAT, false, bytes, 56);
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, B.ib); gl.drawElements(gl.TRIANGLES, B.count, B.big ? gl.UNSIGNED_INT : gl.UNSIGNED_SHORT, 0); }
    gl.uniform1f(this.loc.uSkin, 0); gl.activeTexture(gl.TEXTURE0); this.figuresDrawn = L.length; };
  // once the figures are parsed, their pictures go up; the setting
  CM.figuresReady.then((ok) => { if (ok && CM.renderer && CM.renderer.gl) CM.renderer.figuresUp(CM.figures).catch((e) => console.warn("figures: pictures -", e && e.message)); });
  if (CM.settingLater) CM.settingLater((ui) => CM.addSetting("set-figures", "Figures - the townsfolk, the pets and the monsters as modelled bodies, or as the painted pictures", [["modelled", "Modelled"], ["painted", "Painted"]], "figures", "modelled", ui));
}
