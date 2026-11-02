"use strict";
// Weather on the lens (v31.9, UPGRADE_PLAN_26.md): out in the rain, drops gather on the view - beads that sit and
// runners that slide down, bending what is behind them; in falling snow it gathers in the corners and along the
// edges; in mist, and in the damp bands below (the Flooded Vaults, the Drowned Town), fine beads of it cloud the
// view a little. Each comes and goes slowly with the weather; not under a roof or in a fight. Settings > Weather on
// the view: On or Off. renderer.screen.lens = [rain, snow, mist] (40-render.js's screen pass).
{ const DAMP = new Set(["The Flooded Vaults", "The Drowned Town"]), cur = [0, 0, 0];
  CM.settingLater((ui) => CM.addSetting("set-lens", "Weather on the view - raindrops running down it, snow at its edges, beads of mist", [["on", "On"], ["off", "Off"]], "lens", "on", ui));
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now);
    const on = !(game.settings && game.settings.lens === "off") && game.mode === "explore", fl = game.floor, th = fl ? CM.themeFor(fl.number) || {} : {}, w = r.sky ? CM.weather(game) : "";
    const roof = fl && fl.number <= -21 && fl.number >= -28;
    const want = on && !roof ? [w === "rain" ? 1 : 0, w === "snow" ? 0.8 : 0, w === "mist" || (!r.sky && DAMP.has(th.name)) ? 1 : 0] : [0, 0, 0];
    for (let i = 0; i < 3; i++) cur[i] += (want[i] - cur[i]) * Math.min(1, dt * (want[i] > cur[i] ? 0.25 : 0.6));
    const S = r.screen || (r.screen = {}); S.lens = cur.map((v) => (v < 0.01 ? 0 : v)); };
}
