"use strict";
// Scene transitions (v31.6, UPGRADE_PLAN_26.md): the way from one place to the next shows how it was made - down or up
// the shaft the view goes to black and comes back; through a portal or a waystone it swirls; after a night's camp the
// dawn brightens slowly out of a warm dark; any other new floor fades in. A veil over the view (DOM) and the screen
// pass's swirl (40-render.js: renderer.screen.swirl).
{ let veil = null, prevFloor = null, portalAt = 0, swirlAt = 0, prevMode = null;
  const make = () => { const view = document.querySelector("#view"); if (!view) return null; const v = document.createElement("div"); v.className = "transit";
    v.style.cssText = "position:absolute;inset:0;pointer-events:none;opacity:0;z-index:3"; const c = view.querySelector(".compass"); view.insertBefore(v, c || null); return v; };
  const play = (bg, frames, ms) => { if (!veil) veil = make(); if (!veil || !veil.animate) return; veil.style.background = bg; veil.getAnimations().forEach((a) => a.cancel()); veil.animate(frames, { duration: ms, easing: "ease-in-out" }); };
  CM.transit = {
    shaft: () => play("#000", [{ opacity: 1 }, { opacity: 1, offset: 0.25 }, { opacity: 0 }], 1300),
    floor: () => play("#000", [{ opacity: 0.85 }, { opacity: 0 }], 520),
    dawn: () => play("radial-gradient(ellipse at 50% 90%, rgba(255,150,70,0.9), rgba(30,14,8,1) 70%)", [{ opacity: 1 }, { opacity: 0.85, offset: 0.3 }, { opacity: 0 }], 2800),
    portal: () => { swirlAt = performance.now(); play("radial-gradient(circle, rgba(200,160,255,0.0), rgba(60,20,110,0.75))", [{ opacity: 0 }, { opacity: 1, offset: 0.45 }, { opacity: 0 }], 1100); },
  };
  { const em0 = CM.Game.prototype.emit; CM.Game.prototype.emit = function (ev, ...a) {
      try { if (ev === "portalfx") { portalAt = performance.now(); CM.transit.portal(); }
        else if (ev === "floor" && this.floor && this.mode !== "title") { const n = this.floor.number;
          if (prevFloor !== null && n !== prevFloor && performance.now() - portalAt > 900) { const deep = (x) => x >= 1 && !(CM.isTowerFloor && CM.isTowerFloor(x));
            if ((prevFloor === 0 && deep(n)) || (deep(prevFloor) && n === 0) || (CM.isUndercroft && (CM.isUndercroft(n) !== CM.isUndercroft(prevFloor)) && (n === 0 || prevFloor === 0))) CM.transit.shaft(); else CM.transit.floor(); }
          prevFloor = n; }
        else if (ev === "mode") { const m = a[0]; if (prevMode === "camp" && m === "explore" && CM.hourOf && CM.daylightOf) { const h = CM.hourOf(this), dawn = CM.daylightOf(this)[0]; if (h >= dawn - 1.5 && h <= dawn + 2.5) CM.transit.dawn(); } prevMode = m; } } catch (er) { /* only the picture */ }
      return em0.call(this, ev, ...a); }; }
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); const S = r.screen || (r.screen = {}), e = (performance.now() - swirlAt) / 1100;
    S.swirl = e >= 0 && e < 1 && !CM.reducedMotion ? Math.sin(e * Math.PI) : 0; };
}
