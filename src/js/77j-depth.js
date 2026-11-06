"use strict";
// Presentation, second pass (UPGRADE_PLAN_74.md, release 2): light with depth, and combat that hits.
//  Light: the engine already casts shadows from the sun, the lamps and the torch, sways them with the flame, darkens
//  the corners along the walls and stops a lamp at a wall - so this is tuning. Below ground the party's torch makes a
//  tighter pool (Settings > Lighting: Deep, the default, or Classic as before), so the near floor glows and the far
//  corridor falls away; and the small shadow under every foot is a little firmer.
//  Combat: a crit lands in Claude's red ink; a spell's hit washes the view's edge in its element's colour for a
//  moment; a crit gives the view a short, hard punch (not with Reduce motion).

{ const css = `
.float.crit { color: #E2483A; font: italic 700 32px Georgia, serif; text-shadow: 0 0 2px #2A0A04, 0 0 10px rgba(255,220,180,0.55), 0 2px 3px #000; letter-spacing: 0.01em; }
#view .edge-wash { position: absolute; inset: 0; pointer-events: none; z-index: 5; opacity: 0; transition: opacity 0.5s ease-out; }
#view .edge-wash.on { opacity: 1; transition: opacity 0.06s; }
@keyframes viewPunch { 0% { transform: scale(1); } 30% { transform: scale(1.012) translateY(1px); } 100% { transform: scale(1); } }
#view .canvas-slot.punch { animation: viewPunch 0.16s ease-out; }`;
  const style = () => { if (document.getElementById("depth-css")) return; const st = document.createElement("style"); st.id = "depth-css"; st.textContent = css; document.head.appendChild(st); };
  // light: the torch's pool
  const deep = () => { const g = CM.game; return Boolean(g && g.floor && g.floor.number >= 1 && ((g.settings || {}).lighting || "deep") === "deep"); };
  { const t = () => { const r = CM.renderer; if (r) r.fallK = deep() ? 3.2 : 1; requestAnimationFrame(t); }; requestAnimationFrame(t); }
  // the shadow under each foot, firmer
  { const sc0 = CM.shadowCaster; if (sc0) CM.shadowCaster = (game, renderer, fl) => { const c = sc0(game, renderer, fl); return (...a) => { const out = c(...a); if (out[0] && out[0].rot === undefined) { out[0].alpha = Math.min(0.92, (out[0].alpha || 0.75) * 1.18); out[0].w *= 1.06; } return out; }; }; }
  // combat: the element's wash, the punch
  const HUE = { fire: "255,120,40", flame: "255,120,40", firebolt: "255,120,40", fireball: "255,120,40", bomb: "255,120,40", frost: "150,210,255", ice: "150,210,255", blizzard: "150,210,255", lightning: "200,180,255", storm: "200,180,255", shock: "200,180,255", chain: "200,180,255",
    holy: "255,220,120", turn: "255,220,120", heal: "140,230,140", poison: "130,220,90", venom: "130,220,90", shadow: "170,110,230", drain: "170,110,230", missile: "190,170,255" };
  const elementOf = (id) => { if (!id) return null; const S = (CM.SPELLS || {})[id]; const e = (S && (S.element || S.elem)) || id; return HUE[e] ? e : Object.keys(HUE).find((k) => String(id).toLowerCase().includes(k)) || null; };
  const wash = (ui, rgb) => { const v = ui.$("#view"); if (!v) return; style(); let w = v.querySelector(".edge-wash"); if (!w) { w = document.createElement("div"); w.className = "edge-wash"; v.appendChild(w); }
    w.style.boxShadow = `inset 0 0 70px 18px rgba(${rgb},0.55)`; w.classList.add("on"); setTimeout(() => w.classList.remove("on"), 90); };
  const punch = (ui) => { if (CM.reducedMotion) return; const s = ui.$("#view .canvas-slot"); if (!s) return; s.classList.remove("punch"); void s.offsetWidth; s.classList.add("punch"); };
  const bind = () => { const g = CM.game, ui = CM.ui; if (!g || !g.on || !ui) return false; style();
    g.on("fx", (fx) => { if (!fx || g.replaying || g.film) return;
      if (fx.kind === "cast") { const e = elementOf(fx.id); if (e) wash(ui, HUE[e]); }
      if (fx.kind === "hit" && fx.crit) punch(ui); });
    return true; };
  if (!bind()) { const t = setInterval(() => { if (bind()) clearInterval(t); }, 300); }
  if (CM.settingLater && CM.addSetting) CM.settingLater((ui) => CM.addSetting("set-lighting", "Lighting below ground - Deep: the torch makes a tighter pool and the dark comes closer; Classic: as it always was", [["deep", "Deep"], ["classic", "Classic"]], "lighting", "deep", ui));
}
