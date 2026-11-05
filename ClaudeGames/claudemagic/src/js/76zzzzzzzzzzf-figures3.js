"use strict";
// The figures, finished (v70.0, UPGRADE_PLAN_60.md phase 5): impostors. Once the figures' pictures are up, each model
// is drawn once at load, flat-lit, from the front, into a layer of the figures' texture array (the renderer does it
// at the start of a frame, into a framebuffer of its own) and kept as a canvas too. Beyond the fourteen squares the
// bodies are drawn in, a mapped sprite wears its impostor in place of the painted picture, so a kind looks the same
// near and far; the bestiary's plates and the painted monster pictures are the impostors too, where a kind has a
// body. At most forty bodies are drawn a frame, the nearest; the rest wear impostors. The figures' credit joins the
// game's. (The impostor is the idle's first frame facing the viewer; it is what the far billboard shows anyway.)
{ const CAP = 40, FAR = 60, R = CM.Renderer.prototype, impostors = {};
  CM.figureImpostor = (model) => impostors[model] || null;
  // the pass: at the start of a frame, before the renderer sets its own state, each model into the framebuffer and out again
  R.figureImpostorPass = function () { const gl = this.gl, F = CM.figures, S = this.figTexSize || 256; if (!gl || !F || !this.figTex || this.figImpostorsDone || !this.program || !this.loc) return; this.figImpostorsDone = true;
    try { const fb = gl.createFramebuffer(), tex = gl.createTexture(), rb = gl.createRenderbuffer();
      gl.bindTexture(gl.TEXTURE_2D, tex); gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, S, S, 0, gl.RGBA, gl.UNSIGNED_BYTE, null); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
      gl.bindRenderbuffer(gl.RENDERBUFFER, rb); gl.renderbufferStorage(gl.RENDERBUFFER, gl.DEPTH_COMPONENT16, S, S);
      gl.bindFramebuffer(gl.FRAMEBUFFER, fb); gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0); gl.framebufferRenderbuffer(gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT, gl.RENDERBUFFER, rb);
      if (gl.checkFramebufferStatus(gl.FRAMEBUFFER) !== gl.FRAMEBUFFER_COMPLETE) throw new Error("no framebuffer for the impostors");
      gl.useProgram(this.program); gl.viewport(0, 0, S, S); gl.enable(gl.DEPTH_TEST); gl.disable(gl.BLEND);
      const L = this.loc, set1 = (n, v) => L[n] && gl.uniform1f(L[n], v), set3 = (n, v) => L[n] && gl.uniform3fv(L[n], v);   // flat, even light: no torch, no sun, no lamps, no fog, no grade
      set1("uReach", 500); set1("uAmbient", 1.0); set3("uTorch", [1, 1, 1]); set1("uFlicker", 0); set1("uSunK", 0); set3("uSun", [0, 1, 0]); if (L.uLights) gl.uniform1i(L.uLights, 0); set1("uHaze", 0); set1("uFlash", 0); set3("uGrade", [1, 1, 1]); set3("uLift", [0, 0, 0]); set3("uLook", [1, 1, 0]);
      set1("uCeil", 0); set1("uMapN", 0); set1("uWaterMist", 0); set1("uGroundFrost", 0); set1("uBump", 0); set1("uWet", 0); set1("uSnow", 0); set1("uMist", 0); set1("uLowFog", 0); set1("uMoss", 0); set1("uDapple", 0); set1("uAO", 0); set1("uShaft", 0); set3("uFog", [0, 0, 0]); set3("uBounce", [0, 0, 0]); if (L.uAge) gl.uniform4fv(L.uAge, [0, 0, 0, 0]); if (L.uCloud) gl.uniform4fv(L.uCloud, [0, 0, 0, 0]);
      gl.activeTexture(gl.TEXTURE4); gl.bindTexture(gl.TEXTURE_2D_ARRAY, this.figTex); gl.uniform1i(L.uFig, 4); gl.activeTexture(gl.TEXTURE5); gl.uniform1i(L.uJoints, 5);
      const px = new Uint8Array(S * S * 4), flipped = new Uint8Array(S * S * 4), M16 = new Float32Array(16), names = this.figImpostorNames || Object.keys(F.models);
      names.forEach((name, k) => { const m = F.models[name]; if (!m || name.startsWith("gear:")) return; const B = this.figureBuffers(m), ms = CM.Figures.measure(m), h = ms.height, w = ms.width;
        const clip = m.clips.idle || null; CM.Figures.pose(m, clip, 0, B.pose); gl.bindTexture(gl.TEXTURE_2D, B.jt); gl.texSubImage2D(gl.TEXTURE_2D, 0, 0, 0, 4, m.skeleton.n, gl.RGBA, gl.FLOAT, B.pose);
        const span = Math.max(h, w) * 1.1, eye = [ms.centre[0], ms.foot + h / 2, ms.centre[1] + span * 2.6], at = [ms.centre[0], ms.foot + h / 2, ms.centre[1]];   // from the front (the models face +z), the whole body in the square
        const view = mat4LookAt(eye, at, [0, 1, 0]), proj = mat4Perspective(2 * Math.atan(span / 2 / (span * 2.6)), 1, 0.05, span * 6); gl.uniformMatrix4fv(L.uViewProj, false, mat4Mul(proj, view)); gl.uniform3fv(L.uEye, eye);
        gl.uniform1f(L.uSkin, 1); gl.uniformMatrix4fv(L.uModel, false, CM.Figures.modelMatrix(M16, 0, 0, 0, 0, 1)); gl.uniform3fv(L.uTint, [1, 1, 1]); gl.uniform3fv(L.uFigFx, [0, 1, 0]);
        gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT); this.figureDrawModel(B);
        gl.readPixels(0, 0, S, S, gl.RGBA, gl.UNSIGNED_BYTE, px); for (let y = 0; y < S; y++) flipped.set(px.subarray(y * S * 4, (y + 1) * S * 4), (S - 1 - y) * S * 4);   // (the framebuffer reads from the bottom; a picture's rows run from the top)
        gl.activeTexture(gl.TEXTURE4); gl.bindTexture(gl.TEXTURE_2D_ARRAY, this.figTex); gl.texSubImage3D(gl.TEXTURE_2D_ARRAY, 0, 0, 0, this.figImpostorBase - 3000 + k, S, S, 1, gl.RGBA, gl.UNSIGNED_BYTE, flipped); gl.activeTexture(gl.TEXTURE5);
        const c = document.createElement("canvas"); c.width = c.height = S; const id = c.getContext("2d").createImageData(S, S); id.data.set(flipped); c.getContext("2d").putImageData(id, 0, 0); impostors[name] = c;
        this.index[`fig:${name}`] = this.figImpostorBase + k; });
      gl.activeTexture(gl.TEXTURE4); gl.bindTexture(gl.TEXTURE_2D_ARRAY, this.figTex); gl.generateMipmap(gl.TEXTURE_2D_ARRAY); gl.texParameteri(gl.TEXTURE_2D_ARRAY, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
      gl.uniform1f(L.uSkin, 0); gl.uniform3fv(L.uTint, [1, 1, 1]); gl.activeTexture(gl.TEXTURE0); gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.viewport(0, 0, this.canvas.width, this.canvas.height); gl.enable(gl.BLEND);
      gl.deleteFramebuffer(fb); gl.deleteTexture(tex); gl.deleteRenderbuffer(rb); this.figImpostors = Object.keys(impostors).length;
    } catch (e) { console.warn("figures: impostors -", e && e.message); gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.viewport(0, 0, this.canvas.width, this.canvas.height); } };
  { const d0 = R.frame; R.frame = function (...a) { if (this.figTex && !this.figImpostorsDone && CM.figures) this.figureImpostorPass(); return d0.apply(this, a); }; }
  // beyond the bodies' reach a mapped sprite wears its impostor; and no more than the cap of bodies, the nearest first
  { const ss0 = R.setSprites; R.setSprites = function (list) { const out = ss0.call(this, list); const L = this.figList; if (L && L.length > CAP) { const g = CM.game, fl = g && g.floor, px = fl ? fl.pos[0] + 0.5 : 0, pz = fl ? fl.pos[1] + 0.5 : 0;
        L.sort((a, b) => Math.hypot(a.x - px, a.z - pz) - Math.hypot(b.x - px, b.z - pz)); const spare = L.splice(CAP); for (const f of spare) this.sprites.push(f.s); }
      if (this.figImpostorsDone && CM.figures) { const g = CM.game, fl = g && g.floor, px = fl ? fl.pos[0] : 0, py = fl ? fl.pos[1] : 0;
        for (const s of this.sprites) { if (!s || s.flat || s.hang !== undefined || s.axis) continue; const key = CM.Figures.keyOf(s.layer), fig = key && CM.Figures.figureOf(key); if (!fig || fig === "painted") continue; const d = Math.abs(s.x - px) + Math.abs(s.y - py); if (d > FAR) continue;
          const name = `fig:${fig.model}`; if (this.index[name] === undefined) continue; s.layer = name; if (fig.tint) s.shade = (s.shade || 1) * (0.3 + 0.7 * (fig.tint[0] * 0.3 + fig.tint[1] * 0.59 + fig.tint[2] * 0.11) / 255); } }
      return out; }; }
  // the bestiary's plates and the painted monster pictures: the impostor, where a kind has a body
  { const mon0 = CM.art.monster; CM.art.monster = function (m, big, pose) { const fig = m && CM.Figures && CM.Figures.figureOf(`monster:${m.name}`), c = fig && fig !== "painted" && impostors[fig.model];
      if (!c || (pose && pose !== "idle")) return mon0.call(this, m, big, pose);
      const out = document.createElement("canvas"); out.width = out.height = c.width; const p = out.getContext("2d"); if (fig.tint) { p.drawImage(c, 0, 0); p.globalCompositeOperation = "multiply"; p.fillStyle = `rgb(${fig.tint.join(",")})`; p.fillRect(0, 0, out.width, out.height); p.globalCompositeOperation = "destination-in"; p.drawImage(c, 0, 0); } else p.drawImage(c, 0, 0);
      return out; }; }
  { const cr0 = CM.art.credits; CM.art.credits = function (...a) { const out = cr0.apply(this, a); if (CM.figuresPack && CM.figuresPack.credits) out.push(["The figures", CM.figuresPack.credits]); return out; }; }
}
