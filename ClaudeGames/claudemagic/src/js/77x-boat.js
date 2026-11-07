"use strict";
// The boat, seen (UPGRADE_PLAN_80.md, v133.0; the rules 69zzzzk-boat.js): the Wren at her berth on the dock's south
// face, riding the swell, a gangplank down to her deck; the captain's sea chart when the party goes aboard - this
// island, the islands round it and the mainland, each a place to point at and choose; and the voyage itself, seen
// from her deck - out past the lighthouse and along the coast and round - which any key cuts short.
{ const S = CM.SHIP, H = CM.HARBOUR;
  // the ship: one moving static, drawn after the plants each frame (76zzzzzzzzzzq-plants.js has the pipeline)
  let voyage = null;
  const berthOf = (fl) => { if (!fl) return null; if (fl.number === -1 && fl.grid.length > H.head[3] + 1) return { x: S.at[0], z: S.at[1], yaw: -Math.PI / 2 }; const o = CM.isleOf && CM.isleOf(fl.number); return o && !o.depth ? { x: o.isle.ship[0], z: o.isle.ship[1], yaw: o.isle.shipYaw } : null; };   // (v134.0: at home, or at an island's jetty)
  CM.berthOf = berthOf;
  CM.movingStatics = (game) => { const fl = game && game.floor, B = berthOf(fl); if (!B || !CM.plants || !CM.plants.models.ship || game.mode === "title") return [];
    const t = CM.reducedMotion ? 0 : performance.now() / 1000, M = CM.plantsPack.manifest.models.ship, lo = M.box[0], hi = M.box[1], sc = S.scale;
    let x = B.x, z = B.z, yaw = B.yaw; if (voyage) { const v = voyagePos(performance.now()); x = v.x; z = v.z; yaw = v.yaw; }
    const bob = Math.sin(t * 1.1) * 0.05 + (voyage ? Math.sin(t * 2.3) * 0.04 : 0), c = Math.cos(yaw), s = Math.sin(yaw), ox = (lo[0] + hi[0]) / 2 * sc, oz = (lo[2] + hi[2]) / 2 * sc;
    return [{ model: "ship", x: x - (ox * c - oz * s), y: -0.42 + bob - lo[1] * sc, z: z - (ox * s + oz * c), yaw: yaw + Math.sin(t * 0.7) * 0.015, scale: sc, height: (hi[1] - lo[1]) * sc, shade: 0.74 }]; };
  { const R = CM.Renderer.prototype, ds0 = R.drawStatics; R.drawStatics = function (sky, eye) { ds0.call(this, sky, eye); const g = CM.game, list = CM.movingStatics(g); if (!list.length || !this.index || this.index["pal:plants"] === undefined) return; const gl = this.gl;
      gl.uniform1f(this.loc.uStatic, 1); gl.uniform1f(this.loc.uBump, 0); this._movBuf = this._movBuf || gl.createBuffer();
      for (const p of list) { const B = this.plantBuffers(p.model); if (!B) continue; gl.bindBuffer(gl.ARRAY_BUFFER, B.vb); this._attributes(); gl.bindBuffer(gl.ARRAY_BUFFER, this._movBuf);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([p.x, p.y, p.z, p.yaw, p.scale, 0, 400, p.height, 0, 0, 0, 0, p.shade, 1, 0, 0]), gl.DYNAMIC_DRAW);
        for (let i = 0; i < 4; i++) { gl.enableVertexAttribArray(4 + i); gl.vertexAttribPointer(4 + i, 4, gl.FLOAT, false, 64, i * 16); gl.vertexAttribDivisor(4 + i, 1); }
        gl.uniform3fv(this.loc.uTint, [1, 1, 1]); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, B.ib); gl.drawElementsInstanced(gl.TRIANGLES, B.count, B.big ? gl.UNSIGNED_INT : gl.UNSIGNED_SHORT, 0, 1); }
      for (let i = 4; i < 8; i++) { gl.vertexAttribDivisor(i, 0); gl.disableVertexAttribArray(i); gl.vertexAttrib4f(i, 0, 0, 0, 0); } gl.uniform1f(this.loc.uStatic, 0); gl.uniform3fv(this.loc.uTint, [1, 1, 1]); }; }
  // the gangplank, from the dock's edge down to her deck
  { const ls0 = CM.lifeSprites; CM.lifeSprites = (game, fl, now) => { const out = ls0 ? ls0(game, fl, now) : []; if (voyage || !fl || fl.number !== -1 || !fl.levels || game.mode === "title" || fl.grid.length <= H.head[3] + 1 || Math.abs(fl.pos[1] - H.head[3]) > 30) return out;
      const x0 = H.pier[0] + 0.25, x1 = H.pier[0] + 0.75, z0 = H.head[3] + 1, z1 = S.at[1] - 0.6, y0 = H.deck + 0.02, y1 = 0.22;
      out.push({ x: H.pier[0], y: H.head[3], quad: [[x0, y1, z1], [x1, y1, z1], [x1, y0, z0], [x0, y0, z0]], layer: "solid:timber", shade: 0.9 });
      return out; }; }
  // the voyage: a path at sea, a camera on the deck
  const arrival = (g) => { const B = berthOf(g.floor) || { x: S.at[0], z: S.at[1] }; return [[B.x + 4, B.z + 46], [B.x + 7, B.z + 24], [B.x + 2, B.z + 9], [B.x, B.z + 1]]; };   // (v134.0: in from the open sea to wherever she ties up)
  const ROUTES = { round: [[S.at[0], S.at[1]], [S.at[0] - 6, S.at[1] + 4], [20, 106], [-4, 104], [-8, 80], [-8, 40], [-8, 6], [-4, -6], [10, -8], [30, -9], [50, -8], [57, -9]] };
  const lenOf = (pts) => { let L = 0; for (let i = 1; i < pts.length; i++) L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); return L; };
  const voyagePos = (now) => { const pts = voyage.pts, k = Math.min(1, (now - voyage.t0) / voyage.ms), want = k * voyage.len; let d = 0;
    for (let i = 1; i < pts.length; i++) { const a = pts[i - 1], b = pts[i], seg = Math.hypot(b[0] - a[0], b[1] - a[1]); if (d + seg >= want || i === pts.length - 1) { const f = seg ? Math.min(1, (want - d) / seg) : 1, x = a[0] + (b[0] - a[0]) * f, z = a[1] + (b[1] - a[1]) * f;
        return { x, z, yaw: Math.atan2(b[0] - a[0], -(b[1] - a[1])) + Math.PI / 2, look: Math.atan2(b[0] - a[0], -(b[1] - a[1])), k }; } d += seg; }   // (the model's bow is its -z)
    return { x: pts[0][0], z: pts[0][1], yaw: 0, look: 0, k }; };
  const endVoyage = (g) => { if (!voyage) return; const v = voyage; voyage = null; g.perch = null; if (CM.renderer && g.floor) { CM.renderer.perch = null; CM.renderer.yaw = g.floor.facing * Math.PI / 2; } if (CM.fade) CM.fade(); document.removeEventListener("keydown", v.skip, true); if (v.done) v.done(); g.emit("change"); };
  { const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); if (!voyage || !game) return; const v = voyagePos(now);
      game.perch = { tower: [v.x - 0.5 - Math.sin(v.look) * 2.3, v.z - 0.5 + Math.cos(v.look) * 2.3], h: 1.75, voyage: true }; r.perch = { x: game.perch.tower[0], y: game.perch.tower[1], h: 1.75 };   // (on the afterdeck, over the waist)
      r.yaw = v.look + 0.6; r.turn = null; if (v.k >= 1) endVoyage(game); }; }   // (the island off the starboard bow)
  { const cd0 = CM.Game.prototype.climbDown; CM.Game.prototype.climbDown = function () { if (this.perch && this.perch.voyage) return false; return cd0.call(this); }; }   // (no stepping off a ship at sea)
  CM.startVoyage = (g, id, done) => { const pts = id === "round" ? ROUTES.round : arrival(g), len = lenOf(pts); if (CM.reducedMotion) { if (done) done(); return; }
    voyage = { pts, len, ms: len / 6.5 * 1000, t0: performance.now(), done, skip: (e) => { e.preventDefault(); e.stopPropagation(); endVoyage(g); } };
    setTimeout(() => { if (voyage) document.addEventListener("keydown", voyage.skip, true); }, 400); };
  CM.inVoyage = () => Boolean(voyage);
  // the sea chart
  const W = 860, Hh = 480;
  const paint = (p, g, now) => { const t = now / 1000;
    p.fillStyle = "#D9C9A0"; p.fillRect(0, 0, W, Hh); p.fillStyle = "rgba(90,130,150,0.35)"; p.fillRect(0, 0, W, Hh);
    p.strokeStyle = "rgba(60,90,110,0.25)"; for (let x = 40; x < W; x += 80) { p.beginPath(); p.moveTo(x, 0); p.lineTo(x, Hh); p.stroke(); } for (let y = 40; y < Hh; y += 80) { p.beginPath(); p.moveTo(0, y); p.lineTo(W, y); p.stroke(); }
    p.strokeStyle = "rgba(240,248,250,0.45)"; for (let k = 0; k < 70; k++) { const x = (k * 137) % W, y = (k * 71) % Hh; p.beginPath(); p.moveTo(x, y); p.quadraticCurveTo(x + 6, y - 4 + Math.sin(t + k) * 1.5, x + 12, y); p.stroke(); }
    const land = (pts, fill = "#CDB98A") => { p.fillStyle = fill; p.strokeStyle = "#6A5A3A"; p.lineWidth = 2; p.beginPath(); pts.forEach(([x, y], i) => (i ? p.lineTo(x, y) : p.moveTo(x, y))); p.closePath(); p.fill(); p.stroke(); p.lineWidth = 1; };
    land([[560, 0], [860, 0], [860, 210], [800, 190], [760, 150], [700, 140], [640, 120], [600, 70]], "#C8B482");   // the mainland's coast
    p.fillStyle = "#6A8A4A"; for (let i = 0; i < 14; i++) { const x = 620 + (i * 53) % 230, y = 20 + (i * 37) % 110; p.beginPath(); p.moveTo(x, y - 7); p.lineTo(x + 5, y + 4); p.lineTo(x - 5, y + 4); p.fill(); }
    p.fillStyle = "#8A7A6A"; for (let i = 0; i < 6; i++) { const x = 760 + (i * 29) % 90, y = 40 + (i * 23) % 70; p.beginPath(); p.moveTo(x, y - 12); p.lineTo(x + 9, y + 5); p.lineTo(x - 9, y + 5); p.fill(); }
    land([[360, 190], [470, 182], [500, 230], [488, 300], [430, 318], [372, 300], [350, 250]]);   // home
    p.fillStyle = "#4E7A38"; p.beginPath(); p.ellipse(410, 250, 42, 44, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#B8A070"; p.beginPath(); p.arc(470, 238, 18, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#5A8AC0"; p.lineWidth = 3; p.beginPath(); p.moveTo(400, 196); p.quadraticCurveTo(390, 250, 405, 312); p.stroke(); p.lineWidth = 1;
    land([[180, 96], [200, 92], [206, 118], [186, 126]], "#9A9080"); land([[130, 380], [170, 370], [190, 392], [160, 410], [128, 400]], "#9AB07A"); land([[140, 420], [158, 416], [162, 432], [144, 436]], "#9AB07A");
    land([[630, 390], [690, 382], [700, 420], [650, 430]], "#5A4A44"); p.fillStyle = `rgba(160,150,140,${0.5 + 0.2 * Math.sin(t)})`; p.beginPath(); p.arc(665, 372 - (t % 3) * 4, 6, 0, Math.PI * 2); p.fill();
    p.fillStyle = "#3A3020"; p.font = "italic 15px Georgia"; p.fillText("The Mainland", 700, 180); p.font = "italic 12px Georgia"; p.fillText("The Grey Sea", 250, 230);
    p.save(); p.translate(800, 420); p.strokeStyle = "#5A4A30"; p.beginPath(); p.arc(0, 0, 22, 0, Math.PI * 2); p.stroke(); p.fillStyle = "#5A4A30"; p.beginPath(); p.moveTo(0, -22); p.lineTo(5, 0); p.lineTo(0, 22); p.lineTo(-5, 0); p.fill(); p.font = "bold 11px Georgia"; p.textAlign = "center"; p.fillText("N", 0, -26); p.restore(); };
  Object.assign(CM.UI.prototype, {
    openSeaChart() { if (!this.$("#dlg-seachart")) { const d = document.createElement("div"); d.className = "dialog"; d.id = "dlg-seachart";
        d.innerHTML = `<div class="box wmbox"><h2>${this.esc(S.captain)}'s chart</h2><div class="wmwrap"><canvas width="${W}" height="${Hh}"></canvas><div class="wmmarks"></div><div class="wmtip" hidden></div></div><div class="note" id="sc-note"></div><div class="row"><button data-scclose>Stay ashore</button></div></div>`;
        (this.root || document.body).appendChild(d); d.querySelector("[data-scclose]").addEventListener("click", () => this.closeDialogs()); }
      const g = this.game, d = this.$("#dlg-seachart"), marks = d.querySelector(".wmmarks"), tip = d.querySelector(".wmtip"), note = d.querySelector("#sc-note");
      note.textContent = "Point at a place to hear what the captain knows of it; click to sail.";
      const places = CM.SEA_PLACES.filter((p) => !p.trip).concat(CM.SEA_PLACES.filter((p) => p.trip).map((p) => Object.assign({}, p, { chart: [p.chart[0] + 70, p.chart[1] + 70] })));
      marks.innerHTML = places.map((p) => { const why = g.seaWhyNot(p.id), open = CM.seaOpen(g, p.id); return `<button class="wmpin${open && !why ? " has" : ""}" data-sc="${p.id}" style="left:${(100 * p.chart[0]) / W}%;top:${(100 * p.chart[1]) / Hh}%;${open ? "" : "opacity:0.55"}" aria-label="${this.esc(p.name)}"><i></i></button>`; }).join("");
      marks.querySelectorAll("[data-sc]").forEach((b) => { const p = CM.seaPlace(b.dataset.sc);
        b.addEventListener("mouseenter", () => { const why = g.seaWhyNot(p.id); tip.hidden = false; tip.innerHTML = `<b>${this.esc(p.name)}</b><span>${this.esc(p.what)}</span>${p.fare ? `<em>${p.fare} gold, ${p.hours} hours</em>` : ""}${why ? `<em>${this.esc(why)}</em>` : ""}`; tip.style.left = b.style.left; tip.style.top = b.style.top; });
        b.addEventListener("mouseleave", () => { tip.hidden = true; });
        b.addEventListener("click", () => { const why = g.seaWhyNot(p.id); if (why) { note.textContent = why; return; } this.closeDialogs(); const r = g.sail(p.id); if (r) CM.startVoyage(g, p.id, () => this.refresh && this.refresh()); this.refresh && this.refresh(); }); });
      const cv = d.querySelector("canvas"), loop = (now) => { if (!d.classList.contains("on") && this.scDrawn) return; this.scDrawn = true; paint(cv.getContext("2d"), g, now); requestAnimationFrame(loop); }; this.scDrawn = false; this.openDialog("#dlg-seachart"); requestAnimationFrame(loop); } });
  { const em0 = CM.Game.prototype.emit; CM.Game.prototype.emit = function (ev, ...a) { const out = em0.call(this, ev, ...a); if (ev === "seachart" && CM.ui && CM.ui.openSeaChart && this === CM.game) CM.ui.openSeaChart(); return out; }; }
}
