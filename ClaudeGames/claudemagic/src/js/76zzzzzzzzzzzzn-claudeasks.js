"use strict";
// Claude's account on the ending's own screen (UPGRADE_PLAN_72.md, release 1): the moment the run ends, under the
// ending's words, his short true account of it in his ink - the same that the Hall of Fame keeps. Rules:
// 69zzzo-twoclaudes.js (the account), 69zzzu-claudeasks.js (what he remembers in it).
{ const css = () => { if (document.getElementById("overclaude-css")) return; const st = document.createElement("style"); st.id = "overclaude-css";
    st.textContent = "#over-claude { margin: 10px auto 4px; max-width: 640px; padding: 8px 14px; border-left: 3px solid #B08A48; background: rgba(60,40,20,0.35); color: #D8C49A; font: italic 14px Georgia, serif; text-align: left; } #over-claude b { font-style: normal; color: #E8B860; }"; document.head.appendChild(st); };
  const se0 = CM.UI.prototype.showEnding; CM.UI.prototype.showEnding = function (won, entry, ...a) { const out = se0.call(this, won, entry, ...a), at = this.$("#over-text"); if (!at) return out; css();
    let box = this.$("#over-claude"); if (!entry || !entry.claudeNote) { if (box) box.remove(); return out; }
    if (!box) { box = document.createElement("div"); box.id = "over-claude"; at.after(box); }
    box.innerHTML = `<b>Claude's account:</b> ${this.esc(entry.claudeNote)}`; return out; };
}
