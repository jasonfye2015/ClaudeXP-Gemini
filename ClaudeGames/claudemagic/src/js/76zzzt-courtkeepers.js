"use strict";
// The court's keepers, the window's side (v21.3): the noticeboard drawn (a board of dark planks on two posts, chalked
// notes pinned to it) and its dialog, a row for every place beyond the court in its own colour; the Portal-warden drawn
// (a keeper in a long grey-blue coat with a lantern on a staff); and the lift - at the shaft, Space offers the winch's
// floors (the first, and every camp reached) instead of the old straight drop to the deepest camp. The rules are
// 69s-courtkeepers.js.
{ const CK = CM.COURTKEEPERS;
  CM.art.courtBoard = function (size) { const c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"), u = size / 64;
    p.fillStyle = "#3A2A1A"; p.fillRect(12 * u, 34 * u, 3 * u, 30 * u); p.fillRect(49 * u, 34 * u, 3 * u, 30 * u); p.fillStyle = "#5A3E26"; p.fillRect(8 * u, 10 * u, 48 * u, 32 * u);
    p.strokeStyle = "#3A2814"; p.lineWidth = u; for (let y = 16; y < 42; y += 6) { p.beginPath(); p.moveTo(8 * u, y * u); p.lineTo(56 * u, y * u); p.stroke(); }
    p.fillStyle = "#4A3420"; p.beginPath(); p.moveTo(5 * u, 11 * u); p.lineTo(32 * u, 3 * u); p.lineTo(59 * u, 11 * u); p.closePath(); p.fill();
    const notes = [["#F0E8D0", 11, 14], ["#E8E0C0", 24, 13], ["#F4ECD8", 38, 15], ["#E8DCC0", 14, 27], ["#F0E4CC", 30, 26], ["#ECE0C8", 43, 28]];
    for (const [col, x, y] of notes) { p.fillStyle = col; p.fillRect(x * u, y * u, 10 * u, 11 * u); p.fillStyle = "#8A7A60"; for (let r = 0; r < 3; r++) p.fillRect((x + 1.5) * u, (y + 3 + r * 2.5) * u, 7 * u, 0.7 * u); p.fillStyle = "#C03030"; p.beginPath(); p.arc((x + 5) * u, (y + 1) * u, 0.9 * u, 0, Math.PI * 2); p.fill(); } return c; };
  CM.art.warden = function (size) { const c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"), u = size / 64, R = (x, y, w, h, col) => { p.fillStyle = col; p.fillRect(x * u, y * u, w * u, h * u); };
    R(45, 6, 2, 56, "#5A4A30"); p.fillStyle = "#FFD870"; p.beginPath(); p.arc(46 * u, 8 * u, 3.4 * u, 0, Math.PI * 2); p.fill(); R(43.5, 4, 5, 1.2, "#3A3A40"); R(43.5, 11, 5, 1.2, "#3A3A40");
    p.fillStyle = "#4A5A70"; p.beginPath(); p.moveTo(22 * u, 62 * u); p.lineTo(25 * u, 28 * u); p.lineTo(39 * u, 28 * u); p.lineTo(42 * u, 62 * u); p.closePath(); p.fill(); R(31, 28, 2, 34, "#3A4858"); R(24, 42, 16, 2.5, "#6A5030");
    R(20, 30, 5, 14, "#4A5A70"); R(39, 30, 6, 10, "#4A5A70"); R(43, 38, 3, 3, "#D8B098"); R(20, 44, 4, 3, "#D8B098");
    p.fillStyle = "#D8B098"; p.beginPath(); p.arc(32 * u, 22 * u, 6 * u, 0, Math.PI * 2); p.fill(); p.fillStyle = "#C8C8C8"; p.beginPath(); p.arc(32 * u, 27 * u, 4.5 * u, 0, Math.PI); p.fill();
    R(29, 20, 1.6, 1.6, "#2A1A10"); R(33.5, 20, 1.6, 1.6, "#2A1A10"); p.fillStyle = "#3A4858"; p.beginPath(); p.moveTo(24 * u, 20 * u); p.quadraticCurveTo(32 * u, 7 * u, 40 * u, 20 * u); p.lineTo(38 * u, 16 * u); p.quadraticCurveTo(32 * u, 12 * u, 26 * u, 16 * u); p.closePath(); p.fill(); return c; };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); set.index.courtboard = set.layers.length; set.layers.push(CM.art.courtBoard(set.size)); set.index["npc:warden"] = set.layers.length; set.layers.push(CM.art.warden(set.size)); return set; }; }
  const dlg = (ui, id, title) => { if (ui.$(`#${id}`)) return ui.$(`#${id}`); const d = document.createElement("div"); d.className = "dialog"; d.id = id; d.innerHTML = `<div class="box ckbox"><h2>${title}</h2><div class="ck-body"></div><div class="note ck-note"></div><div class="row"><button data-ckclose>Close</button></div></div>`;
    (ui.root || document.body).appendChild(d); d.querySelector("[data-ckclose]").addEventListener("click", () => ui.closeDialogs()); return d; };
  Object.assign(CM.UI.prototype, {
    openCourtBoard() { const d = dlg(this, "dlg-courtboard", "The court's noticeboard"), rows = CK.board(this.game);
      d.querySelector(".ck-body").innerHTML = `<div class="ckrows">${rows.map((r) => `<div class="ckrow" style="--c:${r.col}"><i></i><div><b>${this.esc(r.name)}</b> <span class="small">${{ wood: "the Wood", world: "another world", shaft: "the dungeon", stone: "the Wood, anywhere known" }[r.kind] || ""}</span><div>${this.esc(r.status)}</div><div class="small">${this.esc(r.who)}</div></div></div>`).join("")}</div>`;
      d.querySelector(".ck-note").textContent = ""; this.openDialog("#dlg-courtboard"); },
    openShaftLift() { const g = this.game, d = dlg(this, "dlg-shaftlift", "The winch"), camps = (g.camps || []).slice().sort((a, b) => a - b);
      d.querySelector(".ck-body").innerHTML = `<p class="lore">A winch of old oak over the shaft's mouth, a cage on its rope big enough for four. The keeper's chalk on the post: the camps you've reached.</p>
        <div class="ckrows"><button class="ckgo" data-lift="0"><b>The first floor</b><span class="small">down the ladder, the long way</span></button>${camps.map((n) => `<button class="ckgo" data-lift="${n}"><b>The camp beneath floor ${n}</b><span class="small">the merchant's lantern</span></button>`).join("")}</div>`;
      d.querySelectorAll("[data-lift]").forEach((b) => b.addEventListener("click", () => { const why = g.shaftLift(Number(b.dataset.lift)); d.querySelector(".ck-note").textContent = why || ""; if (!why) { this.closeDialogs(); this.refresh && this.refresh(); } }));
      d.querySelector(".ck-note").textContent = ""; this.openDialog("#dlg-shaftlift"); },
  });
  // Space at the shaft, with camps to choose from: the winch asks (the window's choice; the rules' own Space still drops
  // to the deepest camp, as it always has, for the films and the tests)
  { const G = CM.Game.prototype, use0 = G.use; G.use = function (...a) { const fl = this.floor, t = fl && this.mode === "explore" && fl.number === 0 && fl.things[`${fl.pos[0]},${fl.pos[1]}`];
      if (t && t.type === "ladder" && (this.camps || []).length && !this.replaying && CM.ui && CM.ui.game === this) { CM.ui.openShaftLift(); return; } return use0.apply(this, a); }; }
}
