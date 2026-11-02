"use strict";
// Camp scenes - the window's side (v34.0): coming into a camp, the four round the fire - a night scene painted on a
// canvas, the fire alive, each hero's portrait in the firelight, the fallen's place left empty - and their talk beneath,
// a line at a time. It comes up once a camp (not under Automatic or a film); the camp's "Round the fire" brings it
// back. And CM.addAction(modes, label, fn), a button for the window files' own in the actions row. Rules: 69zh-fireside.js.
{ const extra = []; CM.addAction = (modes, label, fn) => extra.push({ modes, label, fn });
  const ra0 = CM.UI.prototype.renderActions;
  CM.UI.prototype.renderActions = function (...a) { const out = ra0.apply(this, a), g = this.game, box = this.$("#actions"); if (!box || this.xmenu) return out;
    for (const X of extra) { if (!X.modes.includes(g.mode)) continue; const id = `xa-${X.label.replace(/\W+/g, "")}`; if (box.querySelector(`[data-xa="${id}"]`)) continue;
      const b = document.createElement("button"); b.dataset.xa = id; b.innerHTML = X.label; b.addEventListener("click", () => X.fn(this)); const menu = [...box.children].find((c) => /Menu/.test(c.textContent)); box.insertBefore(b, menu || null); }
    return out; };
  let anim = 0, lines = [], shown = 0, t0 = 0;
  const make = (ui) => { if (ui.$("#dlg-fireside")) return; const d = document.createElement("div"); d.className = "dialog"; d.id = "dlg-fireside";
    d.innerHTML = `<div class="box" style="max-width:680px"><h2>Round the fire</h2><canvas width="640" height="260" style="width:100%;border-radius:6px;background:#0A0806"></canvas><div class="firetalk" style="min-height:120px;margin-top:8px"></div><div class="end"><button class="close">Go on</button></div></div>`;
    ui.$("#dlg-magetower").parentNode.appendChild(d); d.querySelector(".close").addEventListener("click", () => { cancelAnimationFrame(anim); anim = 0; ui.closeDialogs(); }); };
  const paint = (ui, cv, t) => { const p = cv.getContext("2d"), W = cv.width, H = cv.height, g = ui.game, fx = W / 2, fy = H * 0.72;
    const sky = p.createLinearGradient(0, 0, 0, H); sky.addColorStop(0, "#05060C"); sky.addColorStop(1, "#1A120A"); p.fillStyle = sky; p.fillRect(0, 0, W, H);
    p.fillStyle = "rgba(255,255,255,0.7)"; for (let i = 0; i < 40; i++) { const x = (i * 97) % W, y = (i * 53) % (H * 0.45), tw = 0.5 + 0.5 * Math.sin(t * 2 + i); p.globalAlpha = 0.3 + 0.5 * tw; p.fillRect(x, y, 1.5, 1.5); } p.globalAlpha = 1;
    const fl = 0.85 + 0.15 * Math.sin(t * 9) * Math.sin(t * 3.3), glow = p.createRadialGradient(fx, fy, 4, fx, fy, 230 * fl); glow.addColorStop(0, "rgba(255,170,70,0.55)"); glow.addColorStop(1, "rgba(255,120,40,0)"); p.fillStyle = glow; p.fillRect(0, 0, W, H);
    p.fillStyle = "#2A1C10"; p.beginPath(); p.ellipse(fx, fy + 18, 220, 34, 0, 0, Math.PI * 2); p.fill();
    const seats = [[-190, -6], [-90, -34], [90, -34], [190, -6]];
    g.party.forEach((h, i) => { const [dx, dy] = seats[i] || [0, 0], x = fx + dx, y = fy + dy - 40; if (h.hp <= 0) { p.fillStyle = "rgba(60,40,24,0.8)"; p.fillRect(x - 22, y + 30, 44, 10); return; }
      const c = ui.portrait(h, 56); p.save(); p.globalAlpha = 0.95; p.drawImage(c, x - 28, y - 28 + Math.sin(t * 1.3 + i) * 1.2, 56, 56); p.globalCompositeOperation = "source-atop"; p.restore();
      const lit = p.createRadialGradient(fx, fy, 10, fx, fy, 260); lit.addColorStop(0, "rgba(255,150,60,0.25)"); lit.addColorStop(1, "rgba(0,0,0,0.35)"); p.fillStyle = lit; p.fillRect(x - 28, y - 28, 56, 56);
      p.fillStyle = "#E8D8B0"; p.font = "12px Georgia"; p.textAlign = "center"; p.fillText(h.name, x, y + 44); });
    p.fillStyle = "#3A2614"; for (const a of [-0.5, 0.5, 0]) { p.save(); p.translate(fx, fy + 8); p.rotate(a); p.fillRect(-34, -4, 68, 8); p.restore(); }
    for (let k = 0; k < 3; k++) { const h = (46 - k * 12) * fl * (0.9 + 0.1 * Math.sin(t * 13 + k)), w = 22 - k * 6, c = ["rgba(255,80,20,0.9)", "rgba(255,170,50,0.95)", "rgba(255,245,200,1)"][k];
      p.fillStyle = c; p.beginPath(); p.moveTo(fx - w, fy + 4); p.quadraticCurveTo(fx - w * 0.6, fy - h * 0.5, fx + Math.sin(t * 7 + k) * 5, fy - h); p.quadraticCurveTo(fx + w * 0.6, fy - h * 0.5, fx + w, fy + 4); p.fill(); }
    p.fillStyle = "rgba(255,200,120,0.9)"; for (let i = 0; i < 8; i++) { const e = (t * 0.6 + i / 8) % 1; p.globalAlpha = 1 - e; p.fillRect(fx + Math.sin(i * 7 + t) * 18 * e, fy - 40 - e * 120, 2, 2); } p.globalAlpha = 1; };
  CM.UI.prototype.openFireside = function () { make(this); const g = this.game, d = this.$("#dlg-fireside"), cv = d.querySelector("canvas"), talk = d.querySelector(".firetalk");
    lines = g.campTalk(); shown = 0; t0 = performance.now(); talk.innerHTML = ""; this.openDialog("#dlg-fireside");
    const step = () => { if (!d.classList.contains("on")) { anim = 0; return; } const t = (performance.now() - t0) / 1000; paint(this, cv, CM.reducedMotion ? 0 : t);
      const want = Math.min(lines.length, 1 + Math.floor(t / 1.6)); while (shown < want) { const L = lines[shown++], el = document.createElement("p"); el.className = "small"; el.style.margin = "4px 0"; el.innerHTML = this.esc(L.line); talk.appendChild(el); }
      anim = requestAnimationFrame(step); };
    cancelAnimationFrame(anim); anim = requestAnimationFrame(step); };
  CM.addAction(["camp"], "Round the fire", (ui) => ui.openFireside());
  let seen = null; const rf0 = CM.UI.prototype.refresh;
  CM.UI.prototype.refresh = function (...a) { const out = rf0.apply(this, a), g = this.game;
    if (g && g.mode === "camp" && this.screen === "play" && !(g.autoOn && g.autoOn()) && !g.film && !this.dialogOpen()) { const key = `${g.seed}:${g.floor ? g.floor.number : 0}:${(g.camps || []).length}`; if (seen !== key) { seen = key; setTimeout(() => { if (g.mode === "camp" && !this.dialogOpen()) this.openFireside(); }, 400); } }
    return out; };
}
