"use strict";
// Going down (v52.1, UPGRADE_PLAN_47.md): a change of floor is no longer a cut - going down, the view sinks and dims to
// black and the new floor rises up into it out of the dark; going up, the other way, rising into it from below; through
// a door into the town or a house, a short fade. The floor's name comes up as before. With reduced motion, only a fade.
{ if (typeof document !== "undefined" && !(typeof self !== "undefined" && self.CM_WORKER)) {
  let el = null, last = null;
  const veil = () => { if (el) return el; el = document.createElement("div"); el.id = "cm-descent"; el.style.cssText = "position:absolute;inset:0;pointer-events:none;background:#000;opacity:0;z-index:5"; const v = document.querySelector("#view"); (v || document.body).appendChild(el); return el; };
  const canvas = () => document.querySelector("#view canvas");
  const play = (dir) => { const v = veil(), c = canvas(), still = CM.reducedMotion, ms = dir ? 650 : 380;
    v.animate([{ opacity: 1 }, { opacity: 0.85, offset: 0.35 }, { opacity: 0 }], { duration: ms, easing: "ease-out" });
    if (c && !still && dir) c.animate([{ transform: `translateY(${dir > 0 ? -8 : 8}%) scale(1.06)`, filter: "brightness(0.3)" }, { transform: "none", filter: "none" }], { duration: ms, easing: "cubic-bezier(.2,.7,.2,1)" }); };
  const bind = () => { const g = CM.game; if (!g || !g.on) return false;
    g.on("floor", (fl) => { if (!fl || g.mode === "title") { last = fl ? fl.number : null; return; } const n = fl.number, was = last; last = n; if (was === null || was === n) return;
      const dir = n >= 1 && was >= 1 ? Math.sign(n - was) : n >= 1 && was < 1 ? 1 : was >= 1 && n < 1 ? -1 : 0; play(dir); }); return true; };
  const t = setInterval(() => { if (bind()) clearInterval(t); }, 300); } }
