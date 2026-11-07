"use strict";
// The world, on one page - the window's side. The world map (the "World map" button in the
// menu, from anywhere): a painted map of Caer Duin's hill with its walls and doors, the Keep-yard with its portals and the shaft,
// the Deep Wood to the west with the farm, the river, the cabin, the Mage Tower's clearing, the Fortress to the north and
// Claudeita's crag to the south, and beyond the portals the places they open on (Haven, the island, the pipe's
// world). Every place is a marker - pointed at, it says what's there; clicked, the party goes there - and a gold mark
// with a count where something waits. And a "Goals" page in the Journal: every part of the game, and what's next in
// it, each with the way there. The rules are 69f-worldmap.js.
{ const WM = CM.WORLDMAP, W = 860, H = 480;
  // where each place sits on the painted map
  const AT = { home: [600, 300], well: [640, 262], tavern: [624, 236], merchant: [668, 236], smith: [620, 330], temple: [648, 168], library: [630, 196], guildhall: [672, 318], casino: [700, 214],
    pipe: [678, 290], shaft: [752, 262], haven: [748, 220], gate: [782, 254], yard: [762, 300], farm: [330, 330], cabin: [210, 210], fortress: [330, 70], crag: [340, 430], woodgate: [470, 268], fields: [650, 338], glyph: [405, 252] };
  const TZ = 1.25, CX = 670, CY = 255;   // (the town, drawn larger than the Wood so its doors don't crowd)
  for (const id of ["home", "well", "tavern", "merchant", "smith", "temple", "library", "guildhall", "casino", "pipe", "shaft", "haven", "gate", "yard", "fields"]) { const [x, y] = AT[id]; AT[id] = [CX + (x - 670) * TZ, CY + (y - 255) * TZ]; }
  const paint = (p, now) => { const t = now / 1000;
    const sky = p.createLinearGradient(0, 0, 0, H); sky.addColorStop(0, "#D8C8A0"); sky.addColorStop(1, "#C8B488"); p.fillStyle = sky; p.fillRect(0, 0, W, H);
    p.strokeStyle = "rgba(90,60,20,0.15)"; for (let k = 0; k < 40; k++) { p.beginPath(); p.moveTo(0, k * 12); p.lineTo(W, k * 12 + 4); p.stroke(); }
    if (CM.islandKnown && CM.islandKnown(CM.game)) {   // (v129.0) once the island is known: the sea round it, the land its own shape
      p.fillStyle = "#86A8B8"; p.fillRect(0, 0, W, H); p.strokeStyle = "rgba(240,248,250,0.35)"; p.lineWidth = 1.2; for (let k = 0; k < 60; k++) { const x = (k * 137) % W, y = (k * 71) % H; p.beginPath(); p.moveTo(x, y); p.quadraticCurveTo(x + 6, y - 4 + Math.sin(t + k) * 1.5, x + 12, y); p.stroke(); } p.lineWidth = 1;
      const land = () => { p.beginPath(); p.moveTo(6, 30); p.bezierCurveTo(200, -4, 432, 6, 534, 46); p.lineTo(556, 454); p.bezierCurveTo(380, 486, 140, 486, 6, 454); p.closePath(); p.moveTo(CX + 199, CY); p.ellipse(CX, CY, 199, 168, 0, 0, Math.PI * 2); };
      p.fillStyle = "#D2C096"; land(); p.fill(); p.fillRect(500, 120, 120, 300); p.strokeStyle = "rgba(60,90,110,0.55)"; p.lineWidth = 2.5; land(); p.stroke(); p.lineWidth = 1;
      p.fillStyle = "rgba(40,70,90,0.75)"; p.font = "italic 15px Georgia"; p.fillText("the Sea", 26, 476); p.fillText("the Sea", 590, 24); p.font = "italic 11px Georgia"; p.fillText("(all the way round)", 86, 476); }
    // the Wood
    p.fillStyle = "#6A8A4A"; p.beginPath(); p.moveTo(20, 40); p.bezierCurveTo(200, 10, 420, 20, 520, 60); p.lineTo(540, 440); p.bezierCurveTo(380, 470, 140, 470, 20, 440); p.closePath(); p.fill();
    const R = new CM.Random(31); for (let k = 0; k < 170; k++) { const x = 30 + R.next() * 490, y = 50 + R.next() * 390; if (Math.hypot(x - 330, y - 330) < 60 || Math.hypot(x - 260, y - 140) < 40) continue; p.fillStyle = R.chance(0.5) ? "#3E6A30" : "#4E7A38"; p.beginPath(); p.moveTo(x, y - 10); p.lineTo(x + 7, y + 5); p.lineTo(x - 7, y + 5); p.fill(); }
    p.strokeStyle = "#5A8AC0"; p.lineWidth = 6; p.beginPath(); p.moveTo(120, 30); p.bezierCurveTo(180, 160, 90, 280, 150, 460); p.stroke(); p.lineWidth = 1;   // (the river)
    p.fillStyle = "#C8B060"; for (let r = 0; r < 4; r++) p.fillRect(290, 300 + r * 14, 80, 9);   // (the fields)
    p.fillStyle = "#8A8070"; p.beginPath(); p.arc(260, 140, 16, 0, Math.PI * 2); p.fill(); p.fillStyle = "#5A4A80"; p.fillRect(254, 104, 12, 36); p.beginPath(); p.moveTo(250, 104); p.lineTo(260, 84); p.lineTo(270, 104); p.fill();   // (the Mage Tower)
    p.fillStyle = "#6A6A70"; p.fillRect(300, 46, 60, 22); for (let k = 0; k < 6; k++) p.fillRect(300 + k * 11, 40, 6, 6);   // (the Fortress)
    p.fillStyle = "#7A6A5A"; p.beginPath(); p.moveTo(300, 450); p.lineTo(340, 405); p.lineTo(380, 450); p.fill(); p.fillStyle = "#1A1410"; p.beginPath(); p.arc(340, 440, 7, Math.PI, 0); p.fill();   // (the crag)
    p.fillStyle = "#6A4A28"; p.fillRect(200, 200, 22, 14); p.fillStyle = "#4A2A18"; p.beginPath(); p.moveTo(196, 200); p.lineTo(211, 188); p.lineTo(226, 200); p.fill(); p.fillStyle = `rgba(160,160,170,${0.4 + 0.2 * Math.sin(t)})`; p.beginPath(); p.arc(218, 182 - (t % 2) * 6, 4, 0, Math.PI * 2); p.fill();   // (the cabin's smoke)
    // the road up the hill to the town
    p.strokeStyle = "#A08A60"; p.lineWidth = 5; p.beginPath(); p.moveTo(470, 268); p.bezierCurveTo(500, 270, 510, 268, 528, 262); p.stroke(); p.lineWidth = 1;
    p.save(); p.translate(CX, CY); p.scale(TZ, TZ); p.translate(-670, -255);
    // the town on its hill, inside its wall
    p.fillStyle = "#B8A070"; p.beginPath(); p.ellipse(670, 255, 150, 125, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#E0D4B4"; p.beginPath(); p.ellipse(670, 255, 118, 100, 0, 0, Math.PI * 2); p.fill();
    p.strokeStyle = "#7A6A50"; p.lineWidth = 5; p.beginPath(); p.ellipse(670, 255, 118, 100, 0, 0, Math.PI * 2); p.stroke(); p.lineWidth = 1;
    p.fillStyle = "#8A6A4A"; for (const [x, y] of [[600, 220], [610, 280], [690, 200], [640, 300], [700, 300], [660, 190], [600, 250]]) { p.fillRect(x - 10, y - 8, 20, 14); p.fillStyle = "#A04030"; p.beginPath(); p.moveTo(x - 12, y - 8); p.lineTo(x, y - 18); p.lineTo(x + 12, y - 8); p.fill(); p.fillStyle = "#8A6A4A"; }
    p.fillStyle = "#7A1A28"; p.fillRect(690, 200, 24, 18); p.fillStyle = "#F0C040"; p.fillRect(690, 196, 24, 4);   // (the Joker, red and gold)
    p.strokeStyle = "#6A5A40"; p.lineWidth = 3; p.strokeRect(732, 230, 64, 82); p.lineWidth = 1;   // (the Keep-yard)
    p.fillStyle = "#1A1410"; p.beginPath(); p.arc(752, 262, 8, 0, Math.PI * 2); p.fill();   // (the shaft)
    for (const [x, y, c] of [[748, 220, "#E03030"], [782, 254, "#8060D0"], [762, 300, "#60A0F0"]]) { p.fillStyle = c; p.globalAlpha = 0.6 + 0.3 * Math.sin(t * 2 + x); p.beginPath(); p.ellipse(x, y, 7, 11, 0, 0, Math.PI * 2); p.fill(); p.globalAlpha = 1; }
    p.fillStyle = "#3A5A3A"; p.fillRect(674, 284, 8, 12);   // (the pipe)
    p.fillStyle = "#5A4A30"; p.font = "italic 15px Georgia"; p.fillText("The Deep Wood", 160, 260); p.font = "italic 17px Georgia"; p.fillText("Caer Duin", 632, 125 + 8); p.font = "italic 12px Georgia"; p.fillText("the Keep-yard", 730, 326); p.restore();
    // the compass
    p.save(); p.translate(60, 410); p.strokeStyle = "#5A4A30"; p.beginPath(); p.arc(0, 0, 22, 0, Math.PI * 2); p.stroke(); p.fillStyle = "#5A4A30"; p.beginPath(); p.moveTo(0, -22); p.lineTo(5, 0); p.lineTo(0, 22); p.lineTo(-5, 0); p.fill(); p.font = "bold 11px Georgia"; p.textAlign = "center"; p.fillText("N", 0, -26); p.textAlign = "left"; p.restore(); };
  const init0 = CM.UI.prototype.openJournal;
  Object.assign(CM.UI.prototype, {
    openWorldMap() { if (!this.$("#dlg-worldmap")) { const d = document.createElement("div"); d.className = "dialog"; d.id = "dlg-worldmap"; d.innerHTML = `<div class="box wmbox"><h2>The world</h2><div class="wmwrap"><canvas width="${W}" height="${H}"></canvas><div class="wmmarks"></div><div class="wmtip" hidden></div></div><div class="note" id="wm-note"></div><div class="row"><button data-wmgoals>Goals</button><button data-wmclose>Close</button></div></div>`;
        (this.root || document.body).appendChild(d); d.querySelector("[data-wmclose]").addEventListener("click", () => this.closeDialogs()); d.querySelector("[data-wmgoals]").addEventListener("click", () => { this.journalPage = "goals"; this.closeDialogs(); this.openJournal(); }); }
      const g = this.game, d = this.$("#dlg-worldmap"), marks = d.querySelector(".wmmarks"), tip = d.querySelector(".wmtip"), M = g.wmMarks(), why = g.wmCanTravel(), here = g.floor ? g.floor.number : null;
      d.querySelector("#wm-note").textContent = why ? `${why} (the map still shows what's waiting where)` : "Click a place to go there.";
      marks.innerHTML = WM.PLACES.map(([id, name, , , what]) => { const [x, y] = AT[id], m = M[id]; return `<button class="wmpin${m ? " has" : ""}" data-wm="${id}" style="left:${(100 * x) / W}%;top:${(100 * y) / H}%" aria-label="${this.esc(name)}"><i></i>${m ? `<b>${m.length}</b>` : ""}</button>`; }).join("");
      marks.querySelectorAll("[data-wm]").forEach((b) => { const P = WM.byId[b.dataset.wm], m = M[P[0]];
        b.addEventListener("mouseenter", () => { tip.hidden = false; tip.innerHTML = `<b>${this.esc(P[1])}</b><span>${this.esc(P[4])}</span>${m ? m.map((x) => `<em>${this.esc(x)}</em>`).join("") : ""}`; tip.style.left = b.style.left; tip.style.top = b.style.top; });
        b.addEventListener("mouseleave", () => { tip.hidden = true; });
        b.addEventListener("click", () => { const r = g.wmCanTravel(); if (r) { d.querySelector("#wm-note").textContent = r; return; } this.closeDialogs(); const e = g.wmTravel(P[0]); if (e) g.say(e); if (P[0] === "well" && this.openRequests) this.openRequests(); this.refresh && this.refresh(); }); });
      const cv = d.querySelector("canvas"), loop = (now) => { if (!d.classList.contains("on") && this.wmDrawn) return; this.wmDrawn = true; paint(cv.getContext("2d"), now); requestAnimationFrame(loop); }; this.wmDrawn = false; this.openDialog("#dlg-worldmap"); requestAnimationFrame(loop); },
    // the Journal's Goals page
    openJournal() { const j = this.$("#dlg-journal"), boards = j && j.querySelector(".boards"); if (boards && !boards.querySelector('[data-page="goals"]')) { const b = document.createElement("button"); b.dataset.page = "goals"; b.textContent = "Goals"; boards.prepend(b); b.addEventListener("click", () => { this.journalPage = "goals"; this.openJournal(); }); }
      if (this.journalPage !== "goals") { if (boards) { const gb = boards.querySelector('[data-page="goals"]'); if (gb) gb.classList.remove("on"); } return init0.call(this); }
      const g = this.game, box = this.$("#journal-list"), goals = g.wmGoals(), areas = [...new Set(goals.map((x) => x.area))], can = !g.wmCanTravel();
      for (const b of this.root.querySelectorAll("#dlg-journal .boards button")) b.classList.toggle("on", b.dataset.page === "goals");
      box.innerHTML = `<div class="small">Every part of the world, and what's next in it.${can ? " Go takes you straight there." : " (Go works from the town or the Wood.)"} <button data-wmopen>The world map</button></div>` + areas.map((a) => `<div class="list-title">${this.esc(a)}</div>${goals.filter((x) => x.area === a).map((x) => `<div class="entry goal"><p>${this.esc(x.text)}</p>${x.go ? `<button data-goto="${x.go}" ${can ? "" : "disabled"}>Go</button>` : ""}</div>`).join("")}`).join("");
      box.querySelector("[data-wmopen]").addEventListener("click", () => { this.closeDialogs(); this.openWorldMap(); });
      box.querySelectorAll("[data-goto]").forEach((b) => b.addEventListener("click", () => { this.closeDialogs(); const e = g.wmTravel(b.dataset.goto); if (e) g.say(e); if (b.dataset.goto === "well" && this.openRequests) this.openRequests(); this.refresh && this.refresh(); }));
      this.openDialog("#dlg-journal"); },
  });
}
