"use strict";
// The teller of the tale - the window's side (UPGRADE_PLAN_71.md, release 3): Claude's lines in the log (they begin
// with his pen, CM.PEN) in his own ink, italic and warm; two rows in Settings - Narration, and whether he may step
// outside the story on his own; and the Journal titled as his account. Rules: 69zzzr-teller.js.
{ const css = () => { if (document.getElementById("teller-css")) return; const st = document.createElement("style"); st.id = "teller-css";
    st.textContent = "#log .claude-ink { color: #D8B878; font-style: italic; } #log .claude-ink::first-letter { color: #E8A040; font-style: normal; }"; document.head.appendChild(st); };
  { const rl0 = CM.UI.prototype.renderLog; CM.UI.prototype.renderLog = function (...a) { const out = rl0.apply(this, a), log = this.$("#log"); if (!log || !CM.PEN) return out; css();
      for (const d of log.children) if (d.textContent.startsWith(CM.PEN.trim())) d.classList.add("claude-ink"); return out; }; }
  if (CM.settingLater && CM.addSetting) CM.settingLater((ui) => {
    CM.addSetting("set-narrator", "Narration - Claude tells the story in the log: the opening, a chapter for each band, a line in the margin now and then", [["on", "On"], ["off", "Off"]], "narrator", "on", ui);
    CM.addSetting("set-fourthwall", "Claude may step outside the story on his own (asides about the making of the game)", [["asked", "Only when asked"], ["free", "Yes, now and then"]], "fourthWall", "asked", ui); });
  { const oj0 = CM.UI.prototype.openJournal; if (oj0) CM.UI.prototype.openJournal = function (...a) { const out = oj0.apply(this, a), h = this.$("#dlg-journal h2"); if (!h) return out;   /* (only the title's own words change: the tabs inside the heading stay) */
      const t = [...h.childNodes].find((n) => n.nodeType === 3 && /Journal/.test(n.textContent)); if (t) { const base = t.textContent.replace(" - Claude's account", ""); t.textContent = (this.game.settings || {}).narrator !== "off" ? base.replace("Journal", "Journal - Claude's account") : base; } return out; }; }
}
