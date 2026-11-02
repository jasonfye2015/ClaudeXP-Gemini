"use strict";
// A page of the Journal for the later updates (v32.0): CM.journalPage(id, label, title, render) adds a board button
// to the Journal's head and, when it is chosen, hands render(ui, box) the page to fill. Each page is its own; the
// Journal's own pages are as they were.
{ const pages = [];
  CM.journalPage = (id, label, title, render) => pages.push({ id, label, title, render });
  const oj0 = CM.UI.prototype.openJournal;
  CM.UI.prototype.openJournal = function (...a) {
    const j = this.$("#dlg-journal"), boards = j && j.querySelector(".boards");
    if (boards) for (const P of pages) if (!boards.querySelector(`[data-page="${P.id}"]`)) { const b = document.createElement("button"); b.dataset.page = P.id; b.textContent = P.label; b.title = P.title || "";
      boards.appendChild(b); b.addEventListener("click", () => { this.journalPage = P.id; this.openJournal(); }); }
    const P = pages.find((p) => p.id === this.journalPage);
    if (!P) { const out = oj0.apply(this, a); if (boards) for (const p of pages) { const b = boards.querySelector(`[data-page="${p.id}"]`); if (b) b.classList.remove("on"); } return out; }
    if (!j.classList.contains("on")) this.openDialog("#dlg-journal");
    for (const b of this.root.querySelectorAll("#dlg-journal .boards button")) b.classList.toggle("on", b.dataset.page === P.id);
    const box = this.$("#journal-list"); box.innerHTML = ""; try { P.render(this, box); } catch (er) { box.textContent = String(er); }
  };
}
