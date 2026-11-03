"use strict";
// Photo mode (v52.3, UPGRADE_PLAN_47.md): from the pause menu (or Shift+P on the floor) the interface goes away and the
// camera is freed a little - the arrow keys turn it and lean it about the party's square (half a square each way), Q
// and E raise and lower it - and Space or Enter saves the picture (a .png, "Claude and Magic - <place>.png"). Escape
// puts everything back as it was. The game stands still meanwhile.
{ if (typeof document !== "undefined" && !(typeof self !== "undefined" && self.CM_WORKER)) {
  let on = null;
  const HIDE = ["#side", "#party", "#log", "#controls", "#actions", ".hud", "#hud", "#view .fps", "#view .compass", "#view .sky", "#view .hand", "#view .hint", "#view .titlecard", "#floats", "#towerhud", ".tray"];
  const help = () => { let h = document.getElementById("cm-photo-help"); if (!h) { h = document.createElement("div"); h.id = "cm-photo-help"; h.style.cssText = "position:fixed;left:50%;bottom:14px;transform:translateX(-50%);background:rgba(0,0,0,0.6);color:#E8DCC0;font:13px Georgia,serif;padding:6px 14px;border-radius:4px;z-index:50;pointer-events:none";
      h.textContent = "Photo mode - arrows: turn and lean - Q/E: up and down - Space: save the picture - Esc: back"; document.body.appendChild(h); } return h; };
  const start = () => { const r = CM.renderer, g = CM.game; if (on || !r || !g || g.mode === "title") return; if (CM.ui && CM.ui.closeDialogs) CM.ui.closeDialogs();
    on = { eye: r.eye.slice(), yaw: r.yaw, dx: 0, dz: 0, dy: 0, hidden: [] }; for (const sel of HIDE) for (const el of document.querySelectorAll(sel)) { on.hidden.push([el, el.style.visibility]); el.style.visibility = "hidden"; }
    help().style.display = ""; setTimeout(() => { if (on) help().style.display = "none"; }, 4000); };
  const stop = () => { const r = CM.renderer; if (!on) return; for (const [el, v] of on.hidden) el.style.visibility = v; if (r) { r.eye = on.eye.slice(); r.yaw = on.yaw; } on = null; help().style.display = "none"; };
  const save = () => { const r = CM.renderer, c = document.querySelector("#view canvas"); if (!r || !c) return; try { r.frame(0); const url = c.toDataURL("image/png"), fl = CM.game && CM.game.floor, place = fl ? (fl.number === 0 ? "Caer Duin" : fl.number === -1 ? "the Deep Wood" : `floor ${fl.number}`) : "the view";
      const a = document.createElement("a"); a.href = url; a.download = `Claude and Magic - ${place}.png`; document.body.appendChild(a); a.click(); a.remove(); if (CM.uiSound) CM.uiSound("page"); } catch (e) { /* (no picture) */ } };
  CM.photoMode = { start, stop, save, active: () => Boolean(on) };
  // the frame: the free camera over the party's own
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); if (!on) return; const f = [Math.sin(r.yaw), -Math.cos(r.yaw)], rt = [Math.cos(r.yaw), Math.sin(r.yaw)];
    r.eye = [on.eye[0] + on.dx, on.eye[1] + on.dy, on.eye[2] + on.dz]; void f; void rt; r.move = r.turn = null; };
  window.addEventListener("keydown", (e) => { if (!on) { if (e.key === "P" && e.shiftKey && CM.game && CM.game.mode === "explore" && !(CM.ui && CM.ui.dialogOpen && CM.ui.dialogOpen())) { e.preventDefault(); e.stopPropagation(); start(); } return; }
    const r = CM.renderer, step = 0.08, k = e.key, f = [Math.sin(r.yaw), -Math.cos(r.yaw)], rt = [Math.cos(r.yaw), Math.sin(r.yaw)], clampD = () => { const d = Math.hypot(on.dx, on.dz); if (d > 0.45) { on.dx *= 0.45 / d; on.dz *= 0.45 / d; } };
    if (k === "Escape") stop(); else if (k === " " || k === "Enter") save(); else if (k === "ArrowLeft") r.yaw -= 0.06; else if (k === "ArrowRight") r.yaw += 0.06;
    else if (k === "ArrowUp") { on.dx += f[0] * step; on.dz += f[1] * step; clampD(); } else if (k === "ArrowDown") { on.dx -= f[0] * step; on.dz -= f[1] * step; clampD(); }
    else if (k === "q" || k === "Q") on.dy = Math.min(0.35, on.dy + 0.04); else if (k === "e" || k === "E") on.dy = Math.max(-0.35, on.dy - 0.04); else if (k === "a" || k === "A") { on.dx -= rt[0] * step; on.dz -= rt[1] * step; clampD(); } else if (k === "d" || k === "D") { on.dx += rt[0] * step; on.dz += rt[1] * step; clampD(); }
    else return; e.preventDefault(); e.stopPropagation(); }, true);
  // the pause menu's button
  const wire = () => { const end = document.querySelector("#dlg-pause .end"); if (!end) return false; if (!document.getElementById("btn-pause-photo")) { const b = document.createElement("button"); b.id = "btn-pause-photo"; b.textContent = "Photo mode"; b.title = "Hide the interface, move the camera a little, save a picture (Shift+P)"; b.addEventListener("click", start); end.insertBefore(b, end.firstChild); } return true; };
  const t = setInterval(() => { if (wire()) clearInterval(t); }, 300); } }
