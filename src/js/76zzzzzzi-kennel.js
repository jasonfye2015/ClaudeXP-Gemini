"use strict";
// The kennel and the stable - the window's side (v35.4): the kennel drawn by the Keep-yard (a hut, a rail fence), and the
// party's animals in it while the party is in town (they don't follow it about the streets); Space at the gate opens
// it: feed them, name them again, teach the hound and fit the pony. Rules: 69zq-kennel.js.
{ const S = 256, cv = () => { const c = document.createElement("canvas"); c.width = c.height = S; return c; };
  const paint = (p) => { p.fillStyle = "rgba(0,0,0,0.3)"; p.beginPath(); p.ellipse(128, 246, 110, 10, 0, 0, Math.PI * 2); p.fill();
    p.fillStyle = "#7A5230"; p.fillRect(40, 120, 176, 120); p.fillStyle = "#5A3A1E"; p.beginPath(); p.moveTo(24, 128); p.lineTo(128, 48); p.lineTo(232, 128); p.closePath(); p.fill();
    p.fillStyle = "#1A0E06"; p.beginPath(); p.moveTo(98, 240); p.lineTo(98, 180); p.quadraticCurveTo(128, 150, 158, 180); p.lineTo(158, 240); p.fill();
    p.strokeStyle = "#4A2E16"; p.lineWidth = 3; for (let y = 140; y < 240; y += 16) { p.beginPath(); p.moveTo(40, y); p.lineTo(216, y); p.stroke(); }
    p.fillStyle = "#E8D8B0"; p.font = "bold 22px Georgia"; p.textAlign = "center"; p.fillText("KENNEL", 128, 116); };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look), c = cv(); paint(c.getContext("2d")); set.index["kennel:hut"] = set.layers.length; set.layers.push(c); return set; }; }
  CM.thingSprites = Object.assign(CM.thingSprites || {}, { kennel: (t, x, y, now) => { const g = CM.game, out = [{ x, y, layer: "kennel:hut", w: 0.95, h: 0.9, dz: -0.2 }];
    if (g && g.petName("dog")) out.push({ id: "kennel:dog", x, y, layer: "pet:dog", w: 0.42, h: 0.36, dx: -0.3, dz: 0.25, lift: Math.abs(Math.sin((now || 0) / 300)) * 0.01 });
    if (g && g.petName("pony")) out.push({ id: "kennel:pony", x: x - 1, y, layer: "pet:pony", w: 0.85, h: 0.78, dz: 0.1 }); return out; } });
  const fs0 = CM.followersSeen; if (fs0) CM.followersSeen = (game, fl) => { const out = fs0(game, fl); return fl && fl.number === 0 ? out.filter(([id]) => id !== "hound" && id !== "pony") : out; };   // (in town they're at the kennel)
  const make = (ui) => { if (ui.$("#dlg-kennel")) return; const d = document.createElement("div"); d.className = "dialog"; d.id = "dlg-kennel";
    d.innerHTML = `<div class="box journalbox"><h2>The kennel and the stable</h2><p class="lore">A low hut with straw in it, a rail fence, a trough. Whoever is home comes to the gate to see if you've brought anything.</p><div class="kbody"></div><div class="note" id="kennel-note"></div><div class="end"><button class="close">Close</button></div></div>`;
    ui.$("#dlg-magetower").parentNode.appendChild(d); d.querySelector(".close").addEventListener("click", () => ui.closeDialogs()); };
  CM.UI.prototype.openKennel = function (note) { make(this); const g = this.game, box = this.$("#dlg-kennel .kbody"); let h = "";
    const pets = [["dog", "the hound"], ["pony", "the pony"]].filter(([k]) => g.petName(k));
    if (!pets.length) h = `<p class="small">Nobody home: a hound and a pony are bought at the farm, in the Wood.</p>`;
    else { const why = g.feedWhy(); h += `<p><button data-feed ${why ? `disabled title="${this.esc(why)}"` : ""}>Feed them (${CM.KENNEL_FEED} gold: the party's heart lifts)</button></p>`;
      for (const [k, what] of pets) h += `<div class="recruit" style="grid-template-columns:1fr auto auto"><div><b>${this.esc(g.petName(k))}</b> <small>${what}</small></div><input data-name="${k}" maxlength="16" placeholder="a new name" style="width:9em"><button data-rename="${k}">Name</button></div>`;
      if (g.tricks && g.petName("dog")) h += `<div class="list-title">Tricks</div>` + Object.entries(CM.TRICKS).map(([id, T]) => { const w = g.teachTrickWhy(id), knows = g.tricks()[id]; return `<button data-trick="${id}" ${w ? `disabled title="${this.esc(w)}"` : ""}>${knows ? `${this.esc(T.name)}: known` : `Teach ${this.esc(T.name)} (${T.gold} gold)`}</button>`; }).join(" ");
      if (g.ponyGear && g.petName("pony")) h += `<div class="list-title">The pony's gear</div>` + Object.entries(CM.PONY_GEAR).map(([id, T]) => { const w = g.buyPonyGearWhy(id), has = g.ponyGear()[id]; return `<button data-gear="${id}" ${w ? `disabled title="${this.esc(w)}"` : ""}>${has ? `${this.esc(T.name)}: fitted` : `${this.esc(T.name)} (${T.gold} gold)`}</button>`; }).join(" "); }
    box.innerHTML = h; this.$("#kennel-note").textContent = note || "";
    const again = (e) => { this.openKennel(e || ""); this.refresh(); };
    const fb = box.querySelector("[data-feed]"); if (fb) fb.addEventListener("click", () => again(g.feedPets()));
    for (const b of box.querySelectorAll("[data-rename]")) b.addEventListener("click", () => { const inp = box.querySelector(`[data-name="${b.dataset.rename}"]`); again(g.renamePet(b.dataset.rename, inp.value)); });
    for (const b of box.querySelectorAll("[data-trick]")) b.addEventListener("click", () => again(g.teachTrick(b.dataset.trick)));
    for (const b of box.querySelectorAll("[data-gear]")) b.addEventListener("click", () => again(g.buyPonyGear(b.dataset.gear)));
    this.openDialog("#dlg-kennel"); };
  const rf0 = CM.UI.prototype.refresh; let bound = false;
  CM.UI.prototype.refresh = function (...a) { if (!bound && this.game && this.game.on) { bound = true; this.game.on("kennel", () => this.openKennel()); } const out = rf0.apply(this, a), g = this.game, el = this.$ && this.$("#side .pets");
    if (el && g && g.floor && g.floor.number === 0 && g.mode !== "title") { const n = [g.petName("dog"), g.petName("pony")].filter(Boolean); if (n.length) el.textContent = `${n.join(" and ")} at the kennel`; } return out; };   /* (in town: the side panel says where they are) */
}
