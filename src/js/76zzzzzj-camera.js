"use strict";
// Camera feel (v31.1, UPGRADE_PLAN_26.md): Settings > Camera motion - Full: the walk bobs and sways from foot to foot,
// the view leans into a turn, a hard blow on a hero makes it stumble, a guardian's or a giant's arrival shakes it;
// Gentle (the default): the same, softer; Off: a steady camera (no bob at all). Reduce motion is Off, always.
// renderer.camOff {x (to the right), y, roll} (40-render.js). And CM.addSetting, a row of the Settings for the window
// files: a select bound to game.settings[key].
{ CM.addSetting = (id, label, options, key, def, ui0) => {
    const ui = ui0 || CM.ui, box = document.querySelector("#dlg-settings .box"), before = document.querySelector("#set-storage"); if (!ui || !box || document.getElementById(id)) return;
    const row = document.createElement("div"); row.className = "row";
    row.innerHTML = `<label for="${id}">${label}</label><select id="${id}">${options.map(([v, n]) => `<option value="${v}">${n}</option>`).join("")}</select>`;
    box.insertBefore(row, before); const sel = row.querySelector("select"), g = ui.game, sync = () => { sel.value = g.settings[key] || def; };
    sync(); sel.addEventListener("change", () => { g.settings[key] = sel.value; g.saveSettings(); g.emit("settings", g.settings); });
    const od = ui.openDialog; ui.openDialog = function (sel2) { const out = od.call(this, sel2); if (sel2 === "#dlg-settings") sync(); return out; };
  };
  const later = []; CM.settingLater = (f) => later.push(f);
  { const rf0 = CM.UI.prototype.refresh; CM.UI.prototype.refresh = function (...a) { if (!this.setRows && document.querySelector && document.querySelector("#dlg-settings")) { this.setRows = true; try { for (const f of later) f(this); } catch (er) { /* */ } } return rf0.apply(this, a); }; }
  CM.settingLater((ui) => CM.addSetting("set-camera", "Camera motion - the walk's bob and sway, a lean into turns, a stumble at a hard blow", [["gentle", "Gentle"], ["full", "Full"], ["off", "Off (a steady camera)"]], "camera", "gentle", ui));
  let stumble = 0, side = 1, thud = 0, stepSide = 1, lastMove = null;
  const modeOf = (game) => (CM.reducedMotion ? "off" : (game.settings && game.settings.camera) || "gentle");
  { const em0 = CM.Game.prototype.emit; CM.Game.prototype.emit = function (ev, ...a) {
      if (ev === "fx" && a[0] && a[0].kind === "hurt") { const fx = a[0], frac = fx.hero && fx.hero.max ? fx.amount / fx.hero.max : 0; if (frac >= 0.25) { stumble = Math.min(1, frac * 1.6); side = Math.random() < 0.5 ? -1 : 1; } }
      else if (ev === "mode" && a[0] === "combat" && this.foes && this.foes.some((m) => m.guardian || m.boss || (CM.monsterKind && (CM.monsterKind(m.kind || m.name) || {}).big))) thud = 1;
      return em0.call(this, ev, ...a); }; }
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now);
    const M = modeOf(game), k = M === "full" ? 1 : M === "gentle" ? 0.5 : 0, co = r.camOff || (r.camOff = { x: 0, y: 0, roll: 0 });
    if (r.move && r.move !== lastMove) { lastMove = r.move; stepSide = -stepSide; }
    const m = r.move ? Math.sin(r.move.t * Math.PI) : 0;
    co.x = k * m * 0.014 * stepSide; co.y = M === "off" ? -m * 0.018 : k * m * 0.016;          // (off: the renderer's own small bob taken back out)
    let roll = 0; if (r.turn && k) { const dir = Math.sign(r.turn.to - r.turn.from); roll = Math.sin(r.turn.t * Math.PI) * 0.032 * k * dir; }
    if (stumble > 0) { const s = Math.sin(Math.min(1, stumble) * Math.PI); co.y -= 0.07 * s * k; roll += 0.05 * s * side * k; stumble = Math.max(0, stumble - dt * 1.8); }
    if (thud > 0) { if (k) r.shake(0.55 * k); co.y -= 0.03 * k; thud = 0; }
    co.roll = roll; };
}
