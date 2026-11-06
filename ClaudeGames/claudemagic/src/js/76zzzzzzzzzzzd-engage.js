"use strict";
// Being engaged - the window's side (UPGRADE_PLAN_67.md): when a fight begins the view turns to the attacker (quick,
// eased; at once under reduced motion), its border glows by how the fight began - red for an ambush with a short
// shake, amber when they come in plain sight, gold when the party has the drop on them - a stinger sounds under the
// battle music, and a word says where they came from ("FROM BEHIND") so the turn reads as the party's, not the
// camera's. A movement key pressed in a fight says, once a fight, how to get out of it.
{ const CSS = `
#view .engage-glow { position: absolute; inset: 0; pointer-events: none; z-index: 6; opacity: 0; border-radius: 2px; }
#view .engage-glow.on { animation: engageGlow 1.4s ease-out forwards; }
#view .engage-glow.ambush { box-shadow: inset 0 0 0 3px rgba(255,60,40,0.95), inset 0 0 70px 18px rgba(200,20,10,0.75); }
#view .engage-glow.met { box-shadow: inset 0 0 0 3px rgba(255,170,50,0.9), inset 0 0 60px 14px rgba(210,120,20,0.55); }
#view .engage-glow.drop { box-shadow: inset 0 0 0 3px rgba(255,225,120,0.95), inset 0 0 60px 14px rgba(230,190,60,0.55); }
@keyframes engageGlow { 0% { opacity: 0; } 12% { opacity: 1; } 55% { opacity: 0.85; } 100% { opacity: 0.32; } }
#view .engage-word { position: absolute; left: 0; right: 0; top: 18%; text-align: center; pointer-events: none; z-index: 7; font: 700 22px Georgia, serif; letter-spacing: 0.18em; color: #fff; text-shadow: 0 0 8px rgba(0,0,0,0.9), 0 0 2px #000; opacity: 0; }
#view .engage-word.on { animation: engageWord 1.5s ease-out forwards; }
#view .engage-word.ambush { color: #FFB0A0; } #view .engage-word.drop { color: #FFE8A0; }
@keyframes engageWord { 0% { opacity: 0; transform: scale(1.25); } 15% { opacity: 1; transform: scale(1); } 70% { opacity: 1; } 100% { opacity: 0; } }
#party.engaged-ambush { animation: engageParty 0.6s ease-out 1; }
@keyframes engageParty { 0% { box-shadow: 0 0 0 0 rgba(255,60,40,0); } 30% { box-shadow: 0 0 18px 4px rgba(255,60,40,0.8); } 100% { box-shadow: 0 0 0 0 rgba(255,60,40,0); } }
@media (prefers-reduced-motion: reduce) { #view .engage-glow.on, #view .engage-word.on { animation-duration: 0.01s; opacity: 0.4; } }`;
  const WORDS = { right: "FROM THE RIGHT", behind: "FROM BEHIND", left: "FROM THE LEFT" }, HOW = { ambush: "AMBUSH!", drop: "THE DROP ON THEM" };
  const setup = () => { if (document.getElementById("engage-css")) return; const st = document.createElement("style"); st.id = "engage-css"; st.textContent = CSS; document.head.appendChild(st); };
  const restart = (el, cls) => { el.className = cls; void el.offsetWidth; el.className = `${cls} on`; };
  const flourish = (ev) => { const view = document.getElementById("view"); if (!view) return; setup();
    let glow = view.querySelector(".engage-glow"); if (!glow) { glow = document.createElement("div"); view.appendChild(glow); } restart(glow, `engage-glow ${ev.how}`);
    const text = ev.turned ? WORDS[ev.from] : HOW[ev.how]; let word = view.querySelector(".engage-word"); if (!word) { word = document.createElement("div"); view.appendChild(word); } if (text) { word.textContent = ev.turned && ev.how === "ambush" ? `AMBUSH - ${text}` : text; restart(word, `engage-word ${ev.how}`); } else word.className = "engage-word";
    clearTimeout(flourish.t); flourish.t = setTimeout(() => { const g = CM.game; if (!g || g.mode !== "combat") glow.className = "engage-glow"; }, 1500);
    const party = document.getElementById("party"); if (party && ev.how === "ambush") { party.classList.remove("engaged-ambush"); void party.offsetWidth; party.classList.add("engaged-ambush"); } };
  const bind = () => { const g = CM.game; if (!g || !g.on || g._engageBound) return Boolean(g && g._engageBound); g._engageBound = true;
    g.on("engaged", (ev) => { const R = CM.renderer, smooth = g.settings && g.settings.smooth && !CM.reducedMotion;
      if (ev.turned && R && R.turnTo) R.turnTo(ev.facing, smooth ? 240 : 0);
      if (R && R.shake && ev.how === "ambush") R.shake(0.45); else if (R && R.punch && ev.how === "drop") R.punch();
      if (CM.audio && CM.audio.play) CM.audio.play(`stinger_${ev.how}`, 0.85, ev.from === "left" ? -0.5 : ev.from === "right" ? 0.5 : 0);
      g.engageHinted = false; flourish(ev); });
    g.on("mode", (m) => { if (m !== "combat") { const glow = document.querySelector("#view .engage-glow"); if (glow) glow.className = "engage-glow"; } });
    // a movement key in a fight: say once how to get out
    window.addEventListener("keydown", (e) => { if (g.mode !== "combat" || g.engageHinted || (CM.ui && CM.ui.dialogOpen && CM.ui.dialogOpen())) return; const K = (g.settings && g.settings.keys) || CM.DEFAULT_KEYS || {}, moves = ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", K.forward, K.back, K.left, K.right, K.strafeLeft, K.strafeRight].filter(Boolean); if (!moves.includes(e.code)) return;
      g.engageHinted = true; const run = String(K.run || "KeyR").replace(/^Key|^Digit/, ""); g.say(`You're in a fight: no walking off. Fight it out, or Flee (${run}) - back, away from them.`); g.emit("change"); });
    return true; };
  if (!bind()) { const i0 = setInterval(() => { if (bind()) clearInterval(i0); }, 400); }
}
