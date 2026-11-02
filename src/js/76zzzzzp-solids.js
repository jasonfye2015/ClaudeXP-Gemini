"use strict";
// 3-D items (v31.7, UPGRADE_PLAN_26.md): a thing's picture given depth - the icon laid layer on layer, the outer ones
// lit and the inner ones darker, so it stands as a small solid thing - turning when it is looked at: hover an icon in
// the pack, a shop, a chest or the stash and it turns where it lies; its tooltip card carries a larger one turning
// slowly. With Reduce motion it stands still, turned a little so its depth shows. CM.solidOf(canvas, size, ms).
{ const urls = new WeakMap(), url = (cv) => { let u = urls.get(cv); if (!u) { try { u = cv.toDataURL(); } catch (er) { u = ""; } urls.set(cv, u); } return u; };
  let styled = false; const style = () => { if (styled || !document.head) return; styled = true; const s = document.createElement("style");
    s.textContent = "@keyframes cm-solidspin { from { transform: rotateX(-14deg) rotateY(0deg); } to { transform: rotateX(-14deg) rotateY(360deg); } } .cm-solid { display: inline-block; pointer-events: none; } .cm-solid .spin { position: relative; width: 100%; height: 100%; transform-style: preserve-3d; } .cm-solid .ly { position: absolute; inset: 0; background-position: center; background-size: contain; background-repeat: no-repeat; image-rendering: pixelated; backface-visibility: visible; } .itemtip .tt-solid { float: right; margin: 0 0 4px 10px; }";
    document.head.appendChild(s); };
  CM.solidOf = (cv, size, ms) => { style(); const u = url(cv), box = document.createElement("div"); box.className = "cm-solid"; box.style.width = box.style.height = `${size}px`; box.style.perspective = `${size * 5}px`;
    const spin = document.createElement("div"); spin.className = "spin"; spin.style.animation = CM.reducedMotion ? "none" : `cm-solidspin ${ms}ms linear infinite`; if (CM.reducedMotion) spin.style.transform = "rotateX(-14deg) rotateY(28deg)";
    const N = Math.max(5, Math.min(12, Math.round(size / 6))), depth = size * 0.14;
    for (let i = 0; i < N; i++) { const l = document.createElement("div"); l.className = "ly"; l.style.backgroundImage = `url(${u})`; l.style.transform = `translateZ(${((i / (N - 1)) - 0.5) * depth}px)`;
      if (i !== 0 && i !== N - 1) l.style.filter = "brightness(0.5)"; spin.appendChild(l); }
    box.appendChild(spin); return box; };
  // hover: the icon turns where it lies
  let over = null;
  const drop = () => { if (!over) return; over.solid.remove(); over.icon.style.opacity = ""; over = null; };
  typeof document !== "undefined" && document.addEventListener && document.addEventListener("mouseover", (e) => { const t = e.target; if (!t || !t.matches) return;
    if (over && t === over.icon) return; drop();
    if (!t.matches("canvas.icon") || !t.closest("#bag, .dialog, #belt, .shop, .stash, .chest") || t.width < 12) return;
    const r = t.getBoundingClientRect(), s = CM.solidOf(t, Math.round(r.width), 2600); s.style.position = "fixed"; s.style.left = `${r.left}px`; s.style.top = `${r.top}px`; s.style.zIndex = 9000;
    document.body.appendChild(s); t.style.opacity = "0"; over = { icon: t, solid: s }; }, true);
  typeof document !== "undefined" && document.addEventListener && document.addEventListener("scroll", drop, true);
  // the tooltip's card: a larger one, turning slowly
  typeof document !== "undefined" && document.addEventListener && document.addEventListener("mouseover", (e) => { setTimeout(() => { const tip = document.querySelector(".itemtip.on"); if (!tip || tip.querySelector(".tt-solid")) return;
      const host = e.target && e.target.closest && e.target.closest("[title], [data-tip-title]"); if (!host) return;
      const icon = host.matches("canvas.icon") ? host : host.querySelector("canvas.icon") || (host.parentElement && host.parentElement.querySelector("canvas.icon")); if (!icon) return;
      const s = CM.solidOf(icon, 64, 6000); s.classList.add("tt-solid"); tip.insertBefore(s, tip.firstChild); }, 0); });
}
