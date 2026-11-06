"use strict";
// Curiosities, part three - the window's side (UPGRADE_PLAN_73.md). Kept quiet on purpose. Rules: 69zzzy-curios3.js.
{ const egg = (id) => { const g = CM.game; if (g && g.curio) g.curio(id); };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look), c = document.createElement("canvas"); c.width = c.height = 128; const p = c.getContext("2d");
      const g = p.createRadialGradient(64, 90, 1, 64, 90, 34); g.addColorStop(0, "rgba(200,230,255,0.9)"); g.addColorStop(1, "rgba(140,180,255,0)"); p.fillStyle = g; p.fillRect(26, 52, 76, 76); p.fillStyle = "#5A5048"; p.beginPath(); p.ellipse(64, 112, 20, 7, 0, 0, Math.PI * 2); p.fill();
      set.index["curio:odd2"] = set.layers.length; set.layers.push(c); return set; }; }
  CM.thingSprites = Object.assign(CM.thingSprites || {}, { oddity2: (t, x, y, now) => [{ x, y, layer: "curio:odd2", w: 0.32, h: 0.32, glow: 0.2 + 0.12 * Math.sin(now / 520 + y) }] });
  const css = () => { if (document.getElementById("curio2-css")) return; const st = document.createElement("style"); st.id = "curio2-css";
    st.textContent = "@keyframes curioSpin { to { transform: rotate(720deg); } } .curio-spin { animation: curioSpin 1.6s ease-in-out; display: inline-block; } .curio-flip { transform: rotate(180deg); transition: transform 0.8s; } .curio-spark { position: fixed; pointer-events: none; z-index: 99; font-size: 18px; color: #FFE6A0; text-shadow: 0 0 8px #FFB040; transition: transform 1.6s ease-out, opacity 1.6s; }"; document.head.appendChild(st); };
  const onTitle = () => { const sp = document.getElementById("splash"), ti = document.getElementById("title"); return (sp && !sp.classList.contains("gone") && sp.offsetParent !== null) || (ti && ti.offsetParent !== null && CM.game && CM.game.mode === "title"); };
  let typed = "", arrows = [];
  window.addEventListener("keydown", (e) => { if (!onTitle()) return; const t = e.target; if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA")) return; css();
    if (e.key && e.key.length === 1) typed = (typed + e.key.toLowerCase()).slice(-8);
    arrows = arrows.concat(e.key).slice(-8);
    if (typed.endsWith("magic")) { typed = ""; for (let i = 0; i < 24; i++) { const s = document.createElement("div"); s.className = "curio-spark"; s.textContent = "✦"; s.style.left = `${40 + Math.random() * 20}%`; s.style.top = "30%"; document.body.appendChild(s); requestAnimationFrame(() => { s.style.transform = `translate(${(Math.random() - 0.5) * 600}px, ${(Math.random() - 0.3) * 400}px)`; s.style.opacity = "0"; }); setTimeout(() => s.remove(), 1800); } egg("t:magic"); }
    if (typed.endsWith("mordeth")) { typed = ""; const h = document.querySelector("#splash h1") || document.querySelector("#title h1"); if (h && !h.dataset.mord) { h.dataset.mord = "1"; const was = h.innerHTML; h.innerHTML = "Mordeth <span>and Magic</span>"; h.style.filter = "hue-rotate(180deg)"; setTimeout(() => { h.innerHTML = was; h.style.filter = ""; delete h.dataset.mord; }, 3000); } egg("t:mordeth"); }
    if (typed.endsWith("aelith")) { typed = ""; const tg = document.querySelector("#splash .tag") || document.querySelector("#title .tagline"); if (tg && !tg.dataset.ael) { tg.dataset.ael = "1"; const was = tg.textContent; tg.textContent = "She used to sing. Not well. He loved it."; setTimeout(() => { tg.textContent = was; delete tg.dataset.ael; }, 5000); } egg("t:aelith"); }
    if (arrows.join(",") === "ArrowUp,ArrowUp,ArrowDown,ArrowDown,ArrowLeft,ArrowRight,ArrowLeft,ArrowRight") { arrows = []; const root = document.getElementById("app") || document.body; root.classList.add("curio-flip"); setTimeout(() => root.classList.remove("curio-flip"), 2200); egg("t:arrows"); } }, true);
  let clicks = 0, last = 0;
  document.addEventListener("click", (e) => { const em = e.target && e.target.closest && e.target.closest(".emblem-slot"); if (!em || !onTitle()) return; const now = Date.now(); clicks = now - last < 1500 ? clicks + 1 : 1; last = now;
    if (clicks === 7) { clicks = 0; css(); em.classList.remove("curio-spin"); void em.offsetWidth; em.classList.add("curio-spin"); egg("t:emblem"); } }, true);
}
