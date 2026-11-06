"use strict";
// The lore-master - the window's side (UPGRADE_PLAN_71.md, release 2): Claude's shelves open the Journal at the codex,
// the compendium of things or the run's own pages (with the bestiary). Rules: 69zzzq-loremaster.js.
{ const PAGE = { codex: "codex", things: "things", journal: "journal" };
  const bind = () => { const g = CM.game, ui = CM.ui; if (!g || !g.on || !ui) return false;
    g.on("claudePanel", (id) => { if (!PAGE[id]) return; setTimeout(() => { ui.journalPage = PAGE[id]; if (ui.openJournal) ui.openJournal(); }, 350); }); return true; };
  if (!bind()) { const t = setInterval(() => { if (bind()) clearInterval(t); }, 300); }
}
