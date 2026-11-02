"use strict";
// Letters home - the window's side (v34.3): the Journal's Letters page - every letter kept, newest first, each on its
// own sheet of paper with who wrote it and when. Rules: 69zk-letters.js.
CM.journalPage("letters", "Letters", "The letters the heroes wrote home after each trip down", (ui, box) => {
  const L = ui.game.letters().slice().reverse();
  box.innerHTML = `<div class="list-title">Letters home (${L.length})</div><p class="small">Every hero standing writes one when the party comes up into the town after a trip down. The last eighty are kept.</p>`
    + (L.length ? L.map((l) => `<div class="entry" style="background:linear-gradient(170deg,#EADBB8,#D8C49A);color:#2A1C10;border-radius:4px;padding:10px 12px;margin:8px 0;font-family:Georgia,serif;font-style:italic;box-shadow:0 2px 4px rgba(0,0,0,0.5)"><div style="font-style:normal;font-size:11px;opacity:0.7">${ui.esc(l.hero)} the ${ui.esc(l.cls)} - ${ui.esc(l.date)}, day ${l.day + 1} of the run</div>${ui.esc(l.text)}</div>`).join("") : `<p class="small">None yet: they come with the first trip home.</p>`);
});
