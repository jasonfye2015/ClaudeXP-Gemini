"use strict";
// Windows that move (v25.0, UPGRADE_PLAN_20.md): a window rises and fades in when it opens and fades away when it
// closes; buttons press in; the purse counts up (or down) to the new gold, a flash of colour with it; and what the
// party picks up flies from the view to the Inventory button. Reduced motion keeps all of it still.
{ const still = () => CM.reducedMotion;
  const close0 = CM.UI.prototype.closeDialogs;
  CM.UI.prototype.closeDialogs = function (...a) {                        // the window that closes fades where it was (a picture of it, for a moment)
    if (!still() && this.root) for (const d of this.root.querySelectorAll(".dialog.on")) { const box = d.querySelector(".box"); if (!box) continue; const r = box.getBoundingClientRect(); if (!r.width) continue;
      const ghost = box.cloneNode(true); ghost.classList.add("dlg-ghost"); Object.assign(ghost.style, { left: `${r.left}px`, top: `${r.top}px`, width: `${r.width}px`, height: `${r.height}px` }); document.body.appendChild(ghost); setTimeout(() => ghost.remove(), 200); }
    return close0.apply(this, a);
  };
  // the purse: counted to the new gold
  const rf0 = CM.UI.prototype.refresh;
  CM.UI.prototype.refresh = function (...a) {
    const out = rf0.apply(this, a), g = this.game, el = this.$ && this.$("#side .purse"); if (!el || !g) return out;
    const to = g.gold; if (this.goldShown === undefined || still()) { this.goldShown = to; return out; }
    if (to !== (this.goldTo === undefined ? this.goldShown : this.goldTo)) {
      const from = this.goldShown, t0 = performance.now(), ms = Math.min(900, 300 + Math.abs(to - from) * 4); this.goldTo = to; el.classList.remove("up", "down"); void el.offsetWidth; el.classList.add(to > from ? "up" : "down");
      const step = () => { if (this.goldTo !== to) return; const k = Math.min(1, (performance.now() - t0) / ms), e = 1 - Math.pow(1 - k, 3); this.goldShown = Math.round(from + (to - from) * e);
        el.textContent = el.textContent.replace(/Gold: [\d,.\s]+?(?=\s{2,}|$)/, `Gold: ${this.goldShown.toLocaleString()}`); if (k < 1) requestAnimationFrame(step); else { this.goldShown = to; this.goldTo = undefined; } };
      requestAnimationFrame(step);
    }
    if (this.goldTo !== undefined) el.textContent = el.textContent.replace(/Gold: [\d,.\s]+?(?=\s{2,}|$)/, `Gold: ${this.goldShown.toLocaleString()}`);
    return out;
  };
  // what's picked up flies to the pack
  const fly = (ui, items) => {
    if (still() || !ui.root || !ui.icon) return; const view = ui.$("#view"), bag = [...ui.root.querySelectorAll("button")].find((b) => /^Inventory/.test(b.textContent.trim())); if (!view || !bag || !view.offsetParent) return;
    const v = view.getBoundingClientRect(), b = bag.getBoundingClientRect();
    items.slice(0, 4).forEach((it, i) => { let ic; try { ic = ui.icon(it, 28); } catch (e) { return; } const el = document.createElement("div"); el.className = "flyitem"; el.appendChild(ic);
      const x0 = v.left + v.width / 2 + (i - 1.5) * 26, y0 = v.top + v.height * 0.55, x1 = b.left + b.width / 2, y1 = b.top + b.height / 2;
      Object.assign(el.style, { left: `${x0}px`, top: `${y0}px` }); document.body.appendChild(el);
      const anim = el.animate([{ transform: "translate(-50%,-50%) scale(1.3)", opacity: 0 }, { transform: "translate(-50%,-50%) scale(1.2)", opacity: 1, offset: 0.15 },
        { transform: `translate(calc(-50% + ${(x1 - x0) * 0.5}px), calc(-50% + ${(y1 - y0) * 0.5 - 70}px)) scale(1)`, opacity: 1, offset: 0.55 }, { transform: `translate(calc(-50% + ${x1 - x0}px), calc(-50% + ${y1 - y0}px)) scale(0.5)`, opacity: 0.2 }],
        { duration: 750, delay: i * 90, easing: "ease-in-out", fill: "forwards" });
      anim.onfinish = () => { el.remove(); bag.classList.remove("bump"); void bag.offsetWidth; bag.classList.add("bump"); }; });
  };
  const gain0 = CM.Game.prototype.gain;
  CM.Game.prototype.gain = function (items, how) { const out = gain0.call(this, items, how); const ui = CM.ui; if (ui && ui.game === this && !this.replaying && (this.mode === "explore" || this.mode === "combat") && out && out.length && !(ui.dialogOpen && ui.dialogOpen())) fly(ui, out); return out; };
}
