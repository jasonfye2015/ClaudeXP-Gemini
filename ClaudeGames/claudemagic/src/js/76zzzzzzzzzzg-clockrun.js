"use strict";
// The clock that runs (v71.0, UPGRADE_PLAN_61.md part 1): on the floor, in a fight or at camp, with the page in view,
// a game minute passes every CM.CLOCK_RUN.secondsPerMinute real seconds whether the party moves or not - a day in an
// hour - by game.tickClock (24e-calendar2.js). Steps still cost their minute, so the day goes quicker on the walk. The
// title screen and a hidden page stop it. Settings > Clock: Runs (the default) or By steps only (as it was). The HUD's
// dial shows the calendar's date beside the day (73b-clock.js), and refreshes as the minutes pass.
{ let acc = 0, lastRefresh = 0;
  const running = (game) => game && game.floor && ["explore", "combat", "camp"].includes(game.mode) && !(game.settings && game.settings.clock === "steps") && (typeof document === "undefined" || document.visibilityState !== "hidden");
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now);
    if (!running(game)) { acc = 0; return; } acc += Math.min(dt || 0, 1); const per = (CM.CLOCK_RUN && CM.CLOCK_RUN.secondsPerMinute) || 2.5; let n = 0; while (acc >= per && n < 60) { acc -= per; n++; }
    if (n) { CM.tickClock(game, n); if (CM.ui && now - lastRefresh > 2000 && !CM.ui.dialogOpen()) { lastRefresh = now; try { CM.ui.refresh(); } catch (e) { /* the HUD will catch up */ } } } };
  if (CM.settingLater) CM.settingLater((ui) => CM.addSetting("set-clock", "Clock - runs on its own (a day an hour, standing or walking), or only by the party's steps", [["runs", "Runs"], ["steps", "By steps only"]], "clock", "runs", ui));
}
