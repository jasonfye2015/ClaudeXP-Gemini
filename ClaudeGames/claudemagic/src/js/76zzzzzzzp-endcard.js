"use strict";
// Ending scenes (v42.4, UPGRADE_PLAN_37.md): a run's end opens on a painted card of how it ended - the place, in its
// band's own stone and floor, seen down a corridor; the party along the front, those who stand standing and the fallen
// laid down and greyed; and what ended it looming at the back - the foe that was still standing, or for a won run the
// crown in a gold light. A line under it says where and by what. The rest of the window is as it was.
{ const W = 520, H = 210, rgb = (c, k = 1) => `rgb(${c.map((v) => Math.max(0, Math.min(255, Math.round(v * k)))).join(",")})`;
  const paint = (ui, won, entry) => { const g = ui.game, c = document.createElement("canvas"); c.width = W; c.height = H; const p = c.getContext("2d"), T = CM.themeFor(entry.floor > 0 ? entry.floor : 1) || CM.THEMES[0];
    const st = T.stone || [110, 100, 90], fl = T.floor || [80, 70, 60], ce = T.ceiling || [50, 44, 40], bx0 = W * 0.38, bx1 = W * 0.62, by0 = H * 0.3, by1 = H * 0.62;
    p.fillStyle = rgb(ce, 0.7); p.fillRect(0, 0, W, H); p.fillStyle = rgb(fl, 0.8); p.beginPath(); p.moveTo(0, H); p.lineTo(bx0, by1); p.lineTo(bx1, by1); p.lineTo(W, H); p.fill();
    p.fillStyle = rgb(st, 0.75); p.beginPath(); p.moveTo(0, 0); p.lineTo(bx0, by0); p.lineTo(bx0, by1); p.lineTo(0, H); p.fill(); p.beginPath(); p.moveTo(W, 0); p.lineTo(bx1, by0); p.lineTo(bx1, by1); p.lineTo(W, H); p.fill();
    p.fillStyle = rgb(st, 0.5); p.fillRect(bx0, by0, bx1 - bx0, by1 - by0); p.strokeStyle = rgb(st, 0.45); p.lineWidth = 1; for (let i = 1; i < 6; i++) { const y = (H / 6) * i; p.beginPath(); p.moveTo(0, y); p.lineTo(bx0, by0 + (by1 - by0) * i / 6); p.moveTo(W, y); p.lineTo(bx1, by0 + (by1 - by0) * i / 6); p.stroke(); }
    const light = (x, y, r, col) => { const gr = p.createRadialGradient(x, y, 4, x, y, r); gr.addColorStop(0, col); gr.addColorStop(1, "rgba(0,0,0,0)"); p.fillStyle = gr; p.fillRect(0, 0, W, H); };
    const foe = !won ? (g.foes || []).find((m) => m.hp > 0) : null;
    if (won) { light(W / 2, by1 - 30, 160, "rgba(255,210,100,0.55)"); p.fillStyle = "#E8B830"; p.beginPath(); p.moveTo(W / 2 - 34, by1 - 10); p.lineTo(W / 2 - 34, by1 - 46); p.lineTo(W / 2 - 18, by1 - 30); p.lineTo(W / 2, by1 - 56); p.lineTo(W / 2 + 18, by1 - 30); p.lineTo(W / 2 + 34, by1 - 46); p.lineTo(W / 2 + 34, by1 - 10); p.closePath(); p.fill(); p.fillStyle = "#C83040"; p.beginPath(); p.arc(W / 2, by1 - 24, 5, 0, Math.PI * 2); p.fill(); }
    else { light(W * 0.22, H * 0.55, 150, "rgba(255,150,60,0.32)"); if (foe) { try { const kind = CM.monsterKind(foe.kind || foe.name) || foe, pic = CM.art.monster(kind, Boolean(foe.boss || foe.guardian)); const s = 150; p.globalAlpha = 0.92; p.drawImage(pic, W / 2 - s / 2 + 40, by1 - s + 22, s, s); p.globalAlpha = 1; } catch (e) { /* (no picture: the dark alone) */ } } }
    const v = p.createRadialGradient(W / 2, H / 2, H * 0.3, W / 2, H / 2, W * 0.6); v.addColorStop(0, "rgba(0,0,0,0)"); v.addColorStop(1, "rgba(0,0,0,0.7)"); p.fillStyle = v; p.fillRect(0, 0, W, H);
    const party = g.party.filter(Boolean), sz = 58; party.forEach((h, i) => { let pic; try { pic = CM.art.portrait(h.cls, sz, g.settings.look); } catch (e) { return; } const x = 24 + i * (sz + 10), y = H - sz - 34;
      p.save(); if (h.hp > 0) p.drawImage(pic, x, y, sz, sz); else { p.filter = "grayscale(1) brightness(0.7)"; p.translate(x + sz / 2, y + sz * 0.78); p.rotate(-Math.PI / 2); p.drawImage(pic, -sz * 0.28, -sz / 2, sz * 0.56, sz); } p.restore();
      p.fillStyle = h.hp > 0 ? "#F0E0C0" : "#8A8070"; p.font = "11px Georgia"; p.textAlign = "center"; p.fillText(h.name, x + sz / 2, H - 22); });
    const where = won ? "the crown taken" : foe ? `brought down by ${/^[AEIOU]/.test(foe.name) ? "an" : "a"} ${foe.name}` : "taken by the dark", line = `${entry.floor > 0 ? `Floor ${entry.floor}, ${CM.themeFor(entry.floor).name}` : "Caer Duin"} - ${where}`;
    p.fillStyle = "rgba(0,0,0,0.55)"; p.fillRect(0, H - 18, W, 18); p.fillStyle = "#E8D8B0"; p.font = "italic 13px Georgia"; p.textAlign = "center"; p.fillText(line, W / 2, H - 5);
    p.strokeStyle = "#8A6A40"; p.lineWidth = 3; p.strokeRect(1.5, 1.5, W - 3, H - 3); return c; };
  const se0 = CM.UI.prototype.showEnding; CM.UI.prototype.showEnding = function (won, entry, ...a) { const out = se0.call(this, won, entry, ...a);
    try { const box = this.$("#dlg-over .box"); if (box) { const old = box.querySelector(".cm-endcard"); if (old) old.remove(); const c = paint(this, won, entry); c.className = "cm-endcard"; c.style.cssText = "display:block;width:100%;max-width:520px;height:auto;margin:6px auto 8px;border-radius:3px;box-shadow:0 3px 10px rgba(0,0,0,0.6)";
        const h2 = box.querySelector("#over-title"); box.insertBefore(c, h2 || box.firstChild); } } catch (e) { /* (the window as it was) */ }
    return out; };
}
