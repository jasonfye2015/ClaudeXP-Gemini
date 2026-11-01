"use strict";
// The town's asking, the window's side: the request board (from the town's "Requests" button) - a cork board with the
// day's three notes pinned to it, each from someone in the village, naming the place it calls on, what's wanted, how
// far along it is, and what it pays; Done when it's done. The buildings' needs are written on their build buttons
// (70-ui.js asks CM.matsNote). The rules are 69e-requests.js.
{ const RQ = CM.TOWNREQ, init0 = CM.UI.prototype.init;
  const ensure = (ui) => { if (ui.$("#dlg-requests")) return; const d = document.createElement("div"); d.className = "dialog"; d.id = "dlg-requests"; d.innerHTML = `<div class="box journalbox rqbox"><h2>The request board</h2><div id="rq-body"></div><div class="row"><button data-rqclose>Close</button></div></div>`;
    (ui.root || document.body).appendChild(d); d.querySelector("[data-rqclose]").addEventListener("click", () => ui.closeDialogs()); };
  Object.assign(CM.UI.prototype, {
    openRequests() { ensure(this); this.renderRequests(); this.openDialog("#dlg-requests"); },
    renderRequests() { const g = this.game, L = g.rqList(), S = g.rqStore(), box = this.$("#rq-body");
      box.innerHTML = `<p class="lore">By the well, a board of old oak with the village's needs pinned to it, a fresh three every morning. "Whatever you can do," says the note at the top, in the chronicler's hand. "Wherever you can do it."</p>
        <div class="rqgrid">${L.map((q, i) => { const p = g.rqProgress(q), ok = p >= q.n && !q.done, K = RQ.byId[q.kind]; return `<div class="rqnote${q.done ? " done" : ok ? " ready" : ""}" style="--r:${(i - 1) * 2}deg"><i class="pin"></i><span class="rqgiver">From ${q.giver}${q.carried ? " (still wanted)" : ""}</span><b>${this.esc(g.rqWords(q))}</b><span class="rqplace">${K.deed ? "Do it" : "Bring it"}: ${K.place}</span>
          <div class="flbar"><i style="width:${Math.round((100 * Math.min(p, q.n)) / q.n)}%"></i></div><span class="small">${q.done ? "Done - thank you!" : `${Math.min(p, q.n)} of ${q.n}`}</span><span class="rqpay">${q.renown} renown, ${q.gold} gold</span>
          <button class="${ok ? "primary" : ""}" data-rqdone="${i}" ${ok ? "" : "disabled"}>${q.done ? "Done" : K.deed ? "Report it" : "Hand it over"}</button></div>`; }).join("")}</div>
        <div class="note" id="rq-note">${this.rqNote || ""}</div><p class="small">Requests answered: ${S.done}. The village has ${g.renown()} renown to build with.</p>`;
      box.querySelectorAll("[data-rqdone]").forEach((b) => b.addEventListener("click", () => { const r = g.rqDone(Number(b.dataset.rqdone)); this.rqNote = r.error || `${r.giver.charAt(0).toUpperCase() + r.giver.slice(1)} thanks you: ${r.renown} renown and ${r.gold} gold.`; this.renderRequests(); this.refresh && this.refresh(); })); },
  });
}
