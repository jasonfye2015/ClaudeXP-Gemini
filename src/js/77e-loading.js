"use strict";
// Loading, shown (a small upgrade after v102): the boot screen in the page itself (src/index.html: an ember, the name
// and a moving bar, drawn by the browser before the game's script is read) fades the moment the game is up; then a slim
// line under the title card and on the title screen tells the real progress of what the dungeon still needs - the
// heroes' sprites, the stone's textures, the trees and the figures - and fades when all is there; and a party that
// goes down before the textures are up sees "Lighting the torches..." over the view, with the same progress, till they
// are.
//   CM.loadSteps() -> [{ id, name, done }];  CM.loadReady() -> boolean (what the first view needs: the textures)
{ const STEPS = [["sprites", "the heroes", () => Boolean(CM.art && CM.art.hasDolls && CM.art.hasDolls())], ["textures", "the stone", () => Object.keys(CM.texAt || {}).length > 0],
    ["trees", "the trees", () => Boolean(CM.plants && CM.plants.models)], ["figures", "the figures", () => Boolean(CM.figures && CM.figures.models)]];
  CM.loadSteps = () => STEPS.map(([id, name, f]) => { let done = false; try { done = f(); } catch (e) { done = false; } return { id, name, done }; });
  CM.loadReady = () => CM.loadSteps().find((s) => s.id === "textures").done;
  const CSS = `.load-line { position: absolute; left: 50%; transform: translateX(-50%); display: flex; align-items: center; gap: 10px; font: italic 12px Georgia, serif; color: #A8987E; pointer-events: none; transition: opacity 0.6s; white-space: nowrap; z-index: 3; }
.load-line.done { opacity: 0; }
.load-line .bar { width: 140px; height: 3px; background: rgba(60,44,28,0.9); border-radius: 2px; overflow: hidden; }
.load-line .bar i { display: block; height: 100%; width: 0; background: #D9A441; transition: width 0.4s; }
#splash .load-line { bottom: 14px; }
#title .load-line { position: static; transform: none; justify-content: center; margin: 0 auto; flex: 0 0 auto; }
#view .load-veil { position: absolute; inset: 0; z-index: 8; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 14px; background: rgba(14,10,6,0.92); color: #D9A441; font: 600 20px Georgia, serif; transition: opacity 0.5s; }
#view .load-veil.done { opacity: 0; pointer-events: none; }
#view .load-veil .ember { width: 16px; height: 24px; border-radius: 50% 50% 45% 45% / 60% 60% 40% 40%; background: radial-gradient(circle at 50% 70%, #FFE6A0 0%, #FFB040 35%, #D0541A 70%, rgba(160,40,10,0) 100%); box-shadow: 0 0 20px 6px rgba(255,140,40,0.45); animation: bootFlicker 0.9s ease-in-out infinite alternate; }
#view .load-veil .load-line { position: static; transform: none; }`;
  const css = () => { if (document.getElementById("load-css")) return; const st = document.createElement("style"); st.id = "load-css"; st.textContent = CSS; document.head.appendChild(st); };
  const words = (steps) => { const left = steps.filter((s) => !s.done).map((s) => s.name); return left.length ? `Preparing the dungeon: ${left.join(", ")}` : "Ready"; };
  const fill = (line) => { const steps = CM.loadSteps(), n = steps.filter((s) => s.done).length; line.querySelector("span").textContent = words(steps); line.querySelector(".bar i").style.width = `${Math.round(n / steps.length * 100)}%`; return n === steps.length; };
  const makeLine = () => { const d = document.createElement("div"); d.className = "load-line"; d.innerHTML = `<span></span><div class="bar"><i></i></div>`; return d; };
  // the boot screen goes as the game comes up
  const boot = () => { const b = document.getElementById("boot"); if (!b) return; b.classList.add("gone"); setTimeout(() => b.remove(), 600); };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else setTimeout(boot, 0);
  // the line, on the card and on the title screen, till everything is there
  let watching = false;
  const watch = () => { if (watching) return; watching = true; css();
    const tick = () => { const places = [document.getElementById("splash"), document.querySelector("#title .sheet")].filter(Boolean); let all = true;
      for (const host of places) { let line = host.querySelector(":scope > .load-line"); if (!line) { line = makeLine(); if (host.id === "splash") host.appendChild(line); else { const foot = host.querySelector(":scope > .foot"); if (foot) foot.before(line); else host.appendChild(line); } } all = fill(line) && all; if (all) line.classList.add("done"); }
      if (!places.length) all = CM.loadSteps().every((s) => s.done);
      if (all) { watching = false; setTimeout(() => { for (const l of document.querySelectorAll("#splash > .load-line, #title .sheet > .load-line")) l.remove(); }, 900); return; }
      setTimeout(tick, 250); };
    tick(); };
  { const ss0 = CM.UI.prototype.showSplash; CM.UI.prototype.showSplash = function (...a) { const out = ss0.apply(this, a); watch(); return out; }; }
  { const rt0 = CM.UI.prototype.refreshTitle; CM.UI.prototype.refreshTitle = function (...a) { const out = rt0.apply(this, a); watch(); return out; }; }
  // gone down too soon: the veil over the view till the stone is up
  const veil = () => { if (CM.loadReady()) return; const view = document.getElementById("view"); if (!view || view.querySelector(".load-veil")) return; css();
    const v = document.createElement("div"); v.className = "load-veil"; v.innerHTML = `<div class="ember"></div><div>Lighting the torches...</div>`; const line = makeLine(); v.appendChild(line); view.appendChild(v);
    const tick = () => { fill(line); if (CM.loadReady()) { v.classList.add("done"); setTimeout(() => v.remove(), 600); return; } setTimeout(tick, 200); }; tick(); };
  CM.loadVeil = veil;
  const bind = () => { const g = CM.game; if (!g || !g.on) return false; g.on("mode", (m) => { if (m === "explore" || m === "camp" || m === "combat") veil(); }); return true; };
  if (!bind()) { const t = setInterval(() => { if (bind()) clearInterval(t); }, 300); }
}
