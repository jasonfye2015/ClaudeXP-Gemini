"use strict";
// Return to Claude, and Claude keeps the house - the window's side (UPGRADE_PLAN_71.md, release 1): the "Return to
// Claude..." button in the actions row once he has been met (H, too), and the panel each thing in his cabin keeps -
// Export / Import for the desk, Settings opened at the right row for the lamp, the clock and the kettle, Keys, the
// Statistics for the shelf, the Credits for the back door. Rules: 69zzzp-claudehouse.js.
{ const met = (g) => Boolean(g && g.village && g.village.ext && g.village.ext.claude && g.village.ext.claude.met);
  const go = (ui) => { const g = ui.game; g.returnToClaude(); ui.refresh && ui.refresh(); };
  if (CM.addAction) CM.addAction(["explore"], "Return to Claude... (H)", go, (ui) => met(ui.game) && !(ui.game.floor && ui.game.floor.interior === "claude"));
  window.addEventListener("keydown", (e) => { const ui = CM.ui, g = CM.game; if (e.code !== "KeyH" || e.ctrlKey || e.altKey || e.metaKey || !ui || !g || g.mode !== "explore") return;
    const t = e.target; if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT" || t.isContentEditable)) return; if (ui.dialogOpen && ui.dialogOpen()) return;
    if (!met(g)) return; e.preventDefault(); go(ui); });
  const ROW = { look: "#set-look", pace: "#set-speed", sound: "#set-sound" };
  const css = () => { if (document.getElementById("claudehouse-css")) return; const st = document.createElement("style"); st.id = "claudehouse-css";
    st.textContent = ".claude-mark { outline: 2px solid #D9A441; outline-offset: 3px; border-radius: 4px; transition: outline-color 1.6s; } .claude-mark.fade { outline-color: rgba(217,164,65,0); } .claude-note { color: #C8B48A; margin-top: 4px; }"; document.head.appendChild(st); };
  const open = (ui, id) => { css(); const click = (sel) => { const b = document.querySelector(sel); if (b) b.click(); };
    if (id === "transfer") return click("#btn-transfer");
    if (id === "keys") return click("#btn-keys");
    if (id === "credits") return click("#btn-credits");
    if (id === "stats") return ui.openStats ? ui.openStats() : click("#btn-stats");
    if (ROW[id]) { ui.openDialog("#dlg-settings"); const el = document.querySelector(ROW[id]); const row = el && (el.closest(".row") || el.parentNode); if (row) { row.scrollIntoView({ block: "center" }); row.classList.add("claude-mark"); setTimeout(() => row.classList.add("fade"), 1400); setTimeout(() => row.classList.remove("claude-mark", "fade"), 3200); } } };
  const bind = () => { const g = CM.game, ui = CM.ui; if (!g || !g.on || !ui) return false; g.on("claudePanel", (id) => setTimeout(() => open(ui, id), 350)); return true; };
  if (!bind()) { const t = setInterval(() => { if (bind()) clearInterval(t); }, 300); }
}
