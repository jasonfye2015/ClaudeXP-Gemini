"use strict";
// Mana Shelter, the window's side (the twenty-seventh big update): the warren in cross-section on a canvas - packed earth
// and rock, a stair down the left with its lanterns, each floor's rooms with their own furnishings (the well's blue
// glow, the kitchen's hearth, the spring's pool, beds in the quarters, crates, the beacon's lamp, the hall's dummies),
// the residents walking about their work, a bar for each room's work, a bubble bobbing over a room whose work waits to
// be gathered, floating counts as it is, hearts at a birth; beside it the stores, the marks, who lives there, and what
// can be built. Click a room to gather or choose it; choose a room to build and click an empty place. Rules: 64zd-shelter.js.
CM.CG_TABLES.push(["shelter", "Mana Shelter"]);
{ const floor0 = CM.UI.prototype.renderFloor, SHAFT = 70, SW = 150, FH = 92;
  const tint = (id) => ["#C83A3A", "#3A7AC8", "#3AA05A", "#C8A03A", "#8A4AC8", "#C86A3A", "#3AA0A0", "#A03A7A"][id % 8];
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "shelter") return this.cgShelter(box); return floor0.call(this, box); },
    cgShelter(box) {
      const g = this.game, SHL = CM.SHL, W = g.shLive();
      if (!this.shOpened) { this.shOpened = true; const secs = g.shAway(Date.now()); if (secs > 60) this.cgNote = `While you were away (${Math.round(secs / 60)} minutes) the warren carried on without you.`; }
      const r = this.shSel ? W.room(this.shSel) : null, bar = (k) => `<div class="shbar"><span class="${k}" style="width:${Math.min(100, (100 * W.stock[k]) / W.storeCap())}%"></span><em>${{ mana: "Mana", bread: "Bread", water: "Water" }[k]} ${Math.floor(W.stock[k])} / ${W.storeCap()}</em></div>`;
      const idle = W.folk.filter((p) => !p.room), stat = (p) => `M${p.st.might} G${p.st.grace} W${p.st.wit}`;
      let panel = "";
      if (r) { const R = SHL.ROOMS[r.k], st = W.staff(r); panel = `<div class="shroom"><b>${R.name}</b> <small>level ${r.lvl}${R.stat ? ` - wants ${R.stat}` : ""}</small>
        ${R.noStaff ? `<div class="small">Holds ${R.store * r.lvl} more of each store.</div>` : `<div class="small">${r.k === "quarters" ? `Room for ${R.cap * r.lvl}. Two who share it raise a child.` : r.k === "beacon" ? "Draws a wanderer in now and then." : r.k === "hall" ? "Trains each one's weakest strength." : `Makes ${R.amount * r.lvl} ${R.res} a time.`}</div>
        <div class="shstaff">${st.map((p) => `<span>${this.esc(p.name)} <small>${stat(p)}</small><button data-shout="${p.id}" title="Send out">×</button></span>`).join("") || "<small>No one works here.</small>"}</div>
        ${st.length < SHL.staffMax(r.lvl) ? `<button data-shadd ${W.bestIdle(r) ? "" : "disabled"}>Add the best idle hand</button>` : ""}`}
        ${r.lvl < 3 ? `<button data-shup>Improve (${SHL.upCost(r.lvl)} marks)</button>` : ""}</div>`; }
      box.innerHTML = `<div class="cgtable shelter"><h3>Mana Shelter</h3><div class="shwrap"><div class="shview"><canvas class="shcanvas" width="${SHAFT + SW * SHL.SLOTS}" height="${FH * Math.max(SHL.FLOORS, W.floors) + 30}"></canvas></div>
        <div class="shside"><p class="lore">Below the Joker's cellars the house has let you dig. "Keep them fed and watered and the mana flowing," says the attendant, "and they'll keep you."</p>
          ${bar("mana")}${bar("bread")}${bar("water")}<div class="shnums">Marks <b data-sh="marks">${Math.floor(W.marks)}</b> - residents <b>${W.pop()}</b> / ${W.cap()}${W.weary() ? ` - <em>hungry or thirsty: work is slow</em>` : ""}</div>
          ${panel}
          <div class="list-title">Build${this.shBuild ? ` - click an empty place (<a href="#" data-shcancel>cancel</a>)` : ""}</div><div class="shbuild">${Object.entries(SHL.ROOMS).map(([k, R]) => `<button data-shb="${k}" class="${this.shBuild === k ? "primary" : ""}" ${W.marks >= W.cost(k) ? "" : "disabled"}>${R.name} <small>${W.cost(k)}</small></button>`).join("")}<button data-shdig ${W.floors < SHL.FLOORS && W.marks >= SHL.digCost(W.floors) ? "" : "disabled"}>Dig deeper <small>${W.floors < SHL.FLOORS ? SHL.digCost(W.floors) : "-"}</small></button></div>
          <div class="list-title">Idle (${idle.length})</div><div class="shidle">${idle.map((p) => `<button data-shpick="${p.id}" class="${this.shPick === p.id ? "primary" : ""}" ${p.age < SHL.grow ? "disabled title=\"still a child\"" : ""}>${this.esc(p.name)} <small>${p.age < SHL.grow ? "child" : stat(p)}</small></button>`).join("") || "<small>Everyone is at work.</small>"}</div>
          <div class="cgnote">${this.cgNote || ""}</div>${(this.shWins || []).slice(-2).map((w) => this.cgCardWon(w.card)).join("")}
          <div class="list-title">The house's rewards (first time the warren holds...)</div><div class="mnmarks">${SHL.MARKS.map((m, i) => `<span class="${W.paid > i ? "got" : ""}" title="${SHL.gold(i)} gold and a ${i >= 6 ? "rare" : i >= 3 ? "stronger common" : "common"} card">${W.paid > i ? "✓" : "○"} ${m}</span>`).join("")}</div>
          <div class="row"><button data-leave>Leave</button></div></div></div>
        <div class="small">Click a room to gather what waits in it, or to choose it; pick an idle resident and click a room to set them to work. Might suits the well, grace the kitchen, wit the spring and the beacon. It runs on while you are away (four hours at most). Free to play.</div></div>`;
      const q = (s) => box.querySelector(s), keep = () => g.shKeep(Date.now()); q("[data-leave]").addEventListener("click", () => { keep(); this.closeDialogs(); });
      box.querySelectorAll("[data-shb]").forEach((b) => b.addEventListener("click", () => { this.shBuild = this.shBuild === b.dataset.shb ? null : b.dataset.shb; this.shPick = null; this.renderCasino(); }));
      if (q("[data-shcancel]")) q("[data-shcancel]").addEventListener("click", (e) => { e.preventDefault(); this.shBuild = null; this.renderCasino(); });
      if (q("[data-shdig]")) q("[data-shdig]").addEventListener("click", () => { const why = W.dig(); this.cgNote = why || "The diggers break through to a new floor."; if (!why) this.cgSfx("grind", 0.6, 0.7); keep(); this.renderCasino(); });
      box.querySelectorAll("[data-shpick]").forEach((b) => b.addEventListener("click", () => { const id = Number(b.dataset.shpick); this.shPick = this.shPick === id ? null : id; this.shBuild = null; this.renderCasino(); }));
      box.querySelectorAll("[data-shout]").forEach((b) => b.addEventListener("click", () => { W.assign(Number(b.dataset.shout), null); keep(); this.renderCasino(); }));
      if (q("[data-shadd]")) q("[data-shadd]").addEventListener("click", () => { const p = W.bestIdle(r); if (p) W.assign(p.id, r.id); this.cgSfx("step", 0.3); keep(); this.renderCasino(); });
      if (q("[data-shup]")) q("[data-shup]").addEventListener("click", () => { const why = W.upgrade(r.id); this.cgNote = why || `The ${SHL.ROOMS[r.k].name} is improved.`; if (!why) this.cgSfx("level", 0.5); keep(); this.renderCasino(); });
      const cv = q(".shcanvas"); this.shCanvas = cv;
      cv.addEventListener("click", (e) => { const rc = cv.getBoundingClientRect(), x = ((e.clientX - rc.left) * cv.width) / rc.width, y = ((e.clientY - rc.top) * cv.height) / rc.height - 30, f = Math.floor(y / FH), s = Math.floor((x - SHAFT) / SW); this.shClick(f, s); });
      if (!this.shLoop) { let prev = performance.now(), keepT = 0, reT = 0; const loop = (now) => { if (!this.shCanvas || !this.shCanvas.isConnected || this.cgView !== "shelter") { this.shLoop = null; this.shOpened = false; g.shKeep(Date.now()); return; } const dt = Math.min(1, (now - prev) / 1000); prev = now; this.shFrame(dt, now); if ((keepT += dt) > 5) { keepT = 0; g.shKeep(Date.now()); } if ((reT += dt) > 2) { reT = 0; this.shSide(); } this.shLoop = requestAnimationFrame(loop); }; this.shLoop = requestAnimationFrame(loop); }
    },
    shClick(f, s) {
      const g = this.game, SHL = CM.SHL, W = g.shLive(); if (f < 0 || s < 0 || s >= SHL.SLOTS) return; const r = W.at(f, s);
      if (this.shBuild) { const why = W.build(this.shBuild, f, s); this.cgNote = why || `A ${SHL.ROOMS[this.shBuild].name} is built.`; if (!why) { this.cgSfx("grind", 0.5); this.shSel = W.at(f, s).id; this.shBuild = null; } else this.cgSfx("miss", 0.3); g.shKeep(Date.now()); this.renderCasino(); return; }
      if (!r) { this.shSel = null; this.renderCasino(); return; }
      if (this.shPick) { const ok = W.assign(this.shPick, r.id); this.cgNote = ok ? "" : "No room there for another hand."; this.cgSfx(ok ? "step" : "miss", 0.3); if (ok) this.shPick = null; g.shKeep(Date.now()); this.renderCasino(); return; }
      if (r.ready) { const n = W.collect(r.id); (this.shFloats = this.shFloats || []).push({ x: SHAFT + r.s * SW + SW / 2, y: 30 + r.f * FH + 20, text: `+${n} ${SHL.ROOMS[r.k].res}`, at: performance.now() }); this.cgSfx("coin", 0.4, 1.1); g.shKeep(Date.now()); }
      this.shSel = r.id; this.renderCasino();
    },
    // the side's numbers, kept fresh (a fuller redraw only when something there changes)
    shSide() { const W = this.game.shLive(), key = `${W.pop()}:${W.folk.filter((p) => !p.room).length}:${Math.floor(W.marks / 20)}:${W.weary()}:${W.rooms.map((r) => r.ready ? 1 : 0).join("")}:${W.folk.filter((p) => p.age < CM.SHL.grow).length}`; if (key !== this.shKey) { this.shKey = key; const sc = this.shCanvas && this.shCanvas.parentElement.scrollTop; this.renderCasino(); const v = this.$("#casino-body .shview"); if (v && sc) v.scrollTop = sc; } },
    shFrame(dt, now) {
      const g = this.game, SHL = CM.SHL, W = g.shLive(), cv = this.shCanvas, p = cv.getContext("2d");
      W.update(dt);
      for (const e of W.events.splice(0)) {
        if (e.kind === "ready") this.cgSfx("card", 0.15, 2);
        else if (e.kind === "born") { this.cgSfx("heal", 0.5); this.cgNote = `A child is born in the quarters: ${e.p.name}.`; const r = W.rooms.find((x) => x.k === "quarters" && W.staff(x).length >= 2); if (r) (this.shFloats = this.shFloats || []).push({ x: SHAFT + r.s * SW + SW / 2, y: 30 + r.f * FH + 30, text: "♥", at: now, heart: true }); }
        else if (e.kind === "wanderer") { this.cgSfx("door", 0.5); this.cgNote = `A wanderer follows the beacon down: ${e.p.name}.`; }
        else if (e.kind === "grown") this.cgNote = `${e.p.name} is grown, and ready to work.`;
        else if (e.kind === "trained") this.cgSfx("level", 0.25, 1.4);
      }
      const won = g.shMarks(); if (won.length) { this.shWins = (this.shWins || []).concat(won); this.cgSfx("victory", 0.55); this.cgSfx("cardwin", 0.5); this.cgNote = won.map((w) => `The warren houses ${w.mark}: ${w.gold} gold and a card - ${w.card}.`).join(" "); this.renderCasino(); this.cgCoins(this.$("#casino-body"), 14); return; }
      // the earth and the stair
      const H = cv.height; p.fillStyle = "#3A2A1C"; p.fillRect(0, 0, cv.width, H); p.fillStyle = "#6A8A3A"; p.fillRect(0, 0, cv.width, 8); p.fillStyle = "#4A3424"; p.fillRect(0, 8, cv.width, 22);
      for (let k = 0; k < 160; k++) { const x = (k * 97) % cv.width, y = 30 + ((k * 53) % (H - 30)); p.fillStyle = k % 3 ? "rgba(0,0,0,0.18)" : "rgba(255,240,200,0.06)"; p.fillRect(x, y, 4 + (k % 5), 3); }
      const dark = W.stock.mana <= 0 ? 0.35 + 0.15 * Math.sin(now / 90) : 0;
      for (let f = 0; f < W.floors; f++) { const y = 30 + f * FH; p.fillStyle = "#2A2420"; p.fillRect(0, y + 4, SHAFT, FH - 8); p.strokeStyle = "#6A5A3A"; for (let k = 0; k < 6; k++) { p.beginPath(); p.moveTo(10 + k * 9, y + FH - 6 - k * 13); p.lineTo(60, y + FH - 6 - k * 13); p.stroke(); } p.fillStyle = "#FFD070"; p.beginPath(); p.arc(SHAFT - 10, y + 16, 3, 0, Math.PI * 2); p.fill();
        for (let s = 0; s < SHL.SLOTS; s++) { const X = SHAFT + s * SW; if (!W.at(f, s)) { p.fillStyle = this.shBuild ? `rgba(240,208,112,${0.18 + 0.1 * Math.sin(now / 200)})` : "rgba(0,0,0,0.15)"; p.fillRect(X + 3, y + 4, SW - 6, FH - 8); if (this.shBuild) { p.strokeStyle = "#F0D070"; p.setLineDash([5, 4]); p.strokeRect(X + 3.5, y + 4.5, SW - 7, FH - 9); p.setLineDash([]); } } } }
      for (let f = W.floors; f < SHL.FLOORS; f++) { p.fillStyle = "rgba(0,0,0,0.25)"; p.fillRect(0, 30 + f * FH, cv.width, FH); }
      for (const r of W.rooms) this.shRoom(p, r, now, W);
      p.fillStyle = `rgba(0,0,30,${dark})`; p.fillRect(0, 30, cv.width, H - 30);
      // the folk: the staff about their rooms, the idle on the stairs
      for (const pp of W.folk) { let x, y; const r = pp.room ? W.room(pp.room) : null, ph = (pp.id * 1.7 + now / (1400 + (pp.id % 5) * 300)) % (Math.PI * 2);
        if (r) { x = SHAFT + r.s * SW + 22 + (SW - 44) * (0.5 + 0.5 * Math.sin(ph)); y = 30 + r.f * FH + FH - 10; } else { const fi = pp.id % W.floors; x = 14 + 42 * (0.5 + 0.5 * Math.sin(ph)); y = 30 + fi * FH + FH - 10; }
        this.shPerson(p, x, y, pp, Math.cos(ph) > 0 ? 1 : -1, now); }
      // floats
      this.shFloats = (this.shFloats || []).filter((fl) => now - fl.at < 1200); for (const fl of this.shFloats) { const t = (now - fl.at) / 1200; p.globalAlpha = 1 - t; p.fillStyle = fl.heart ? "#FF7090" : "#FFE070"; p.font = `bold ${fl.heart ? 26 : 16}px Georgia, serif`; p.textAlign = "center"; p.fillText(fl.text, fl.x, fl.y - t * 40); p.textAlign = "left"; p.globalAlpha = 1; }
      const mk = this.$("#casino-body [data-sh=marks]"); if (mk) mk.textContent = Math.floor(W.marks);
    },
    shRoom(p, r, now, W) {
      const SHL = CM.SHL, R = SHL.ROOMS[r.k], X = SHAFT + r.s * SW, Y = 30 + r.f * FH, w = SW - 6, h = FH - 8, x = X + 3, y = Y + 4;
      const bg = p.createLinearGradient(0, y, 0, y + h); bg.addColorStop(0, R.colour); bg.addColorStop(1, "#1A1410"); p.fillStyle = bg; p.fillRect(x, y, w, h); p.fillStyle = "#5A4A3A"; p.fillRect(x, y + h - 6, w, 6);
      p.strokeStyle = this.shSel === r.id ? "#FFE070" : "#8A7050"; p.lineWidth = this.shSel === r.id ? 3 : 1.5; p.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1); p.lineWidth = 1;
      // furnishings
      const cx = x + w / 2, fy = y + h - 6;
      if (r.k === "well") { p.save(); p.shadowColor = "#60A0FF"; p.shadowBlur = 14 + 4 * Math.sin(now / 300); p.fillStyle = "#70B0FF"; p.beginPath(); p.ellipse(cx, fy - 8, 22, 7, 0, 0, Math.PI * 2); p.fill(); p.restore(); p.fillStyle = "#6A6A72"; p.fillRect(cx - 26, fy - 8, 52, 8); }
      else if (r.k === "kitchen") { p.fillStyle = "#3A3030"; p.fillRect(x + 12, fy - 30, 34, 30); p.fillStyle = `rgba(255,${120 + 60 * Math.sin(now / 140)},40,0.9)`; p.fillRect(x + 18, fy - 14, 22, 10); p.fillStyle = "#8A6A40"; p.fillRect(x + w - 50, fy - 16, 40, 4); }
      else if (r.k === "spring") { p.fillStyle = "#3A70A0"; p.beginPath(); p.ellipse(cx, fy - 4, 34, 6, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "rgba(200,240,255,0.6)"; p.beginPath(); p.ellipse(cx + Math.sin(now / 400) * 6, fy - 4, 10 + 6 * ((now / 600) % 1), 2, 0, 0, Math.PI * 2); p.stroke(); }
      else if (r.k === "quarters") { for (let k = 0; k < r.lvl + 1; k++) { p.fillStyle = "#6A4A30"; p.fillRect(x + 8 + k * 34, fy - 10, 28, 10); p.fillStyle = "#D8D0C0"; p.fillRect(x + 9 + k * 34, fy - 13, 10, 4); p.fillStyle = "#8A3A4A"; p.fillRect(x + 18 + k * 34, fy - 12, 17, 5); } }
      else if (r.k === "store") { for (let k = 0; k < 2 + r.lvl * 2; k++) { p.fillStyle = k % 2 ? "#8A6A3A" : "#7A5A2A"; p.fillRect(x + 10 + (k % 4) * 30, fy - 16 - Math.floor(k / 4) * 16, 26, 16); p.strokeStyle = "#4A3418"; p.strokeRect(x + 10.5 + (k % 4) * 30, fy - 15.5 - Math.floor(k / 4) * 16, 25, 15); } }
      else if (r.k === "beacon") { p.fillStyle = "#4A3A2A"; p.fillRect(cx - 3, y + 14, 6, fy - y - 14); p.save(); p.shadowColor = "#FFE080"; p.shadowBlur = 20 + 10 * Math.sin(now / 250); p.fillStyle = "#FFE080"; p.beginPath(); p.arc(cx, y + 16, 7, 0, Math.PI * 2); p.fill(); p.restore(); }
      else if (r.k === "hall") { for (const k of [0.25, 0.75]) { p.fillStyle = "#8A6A40"; p.fillRect(x + w * k - 2, fy - 30, 4, 30); p.fillStyle = "#C8A870"; p.beginPath(); p.arc(x + w * k, fy - 32, 7, 0, Math.PI * 2); p.fill(); p.fillRect(x + w * k - 10, fy - 24, 20, 4); } }
      p.fillStyle = "rgba(255,240,200,0.85)"; p.font = "bold 10px Georgia, serif"; p.fillText(`${R.name}${r.lvl > 1 ? ` ${"I".repeat(r.lvl)}` : ""}`, x + 5, y + 12);
      // the work's bar and a bubble over finished work
      if (R.res) { p.fillStyle = "#1A1410"; p.fillRect(x + 5, y + 16, w - 10, 4); p.fillStyle = "#C8E070"; p.fillRect(x + 5, y + 16, (w - 10) * (r.ready ? 1 : r.prog), 4); }
      else if (r.k === "quarters" || r.k === "beacon") { const T = r.k === "quarters" ? SHL.child : SHL.wander; if (r.timer) { p.fillStyle = "#1A1410"; p.fillRect(x + 5, y + 16, w - 10, 4); p.fillStyle = r.k === "quarters" ? "#FF90B0" : "#FFE080"; p.fillRect(x + 5, y + 16, (w - 10) * Math.min(1, r.timer / T), 4); } }
      if (r.ready) { const by = y + 34 + Math.sin(now / 250 + r.id) * 4; p.fillStyle = "rgba(255,255,255,0.92)"; p.beginPath(); p.arc(cx, by, 15, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#C8A040"; p.lineWidth = 2; p.stroke(); p.lineWidth = 1; this.shIcon(p, R.res, cx, by); }
    },
    // the stores' marks, drawn: a blue crystal, a loaf, a drop
    shIcon(p, res, x, y) {
      if (res === "mana") { p.fillStyle = "#4A7AD0"; p.beginPath(); p.moveTo(x, y - 9); p.lineTo(x + 7, y); p.lineTo(x, y + 9); p.lineTo(x - 7, y); p.closePath(); p.fill(); p.fillStyle = "#B0D0FF"; p.beginPath(); p.moveTo(x, y - 9); p.lineTo(x + 3, y - 1); p.lineTo(x - 3, y - 1); p.closePath(); p.fill(); }
      else if (res === "bread") { p.fillStyle = "#C88A3A"; p.beginPath(); p.ellipse(x, y + 1, 10, 6, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#7A4A18"; p.lineWidth = 1.5; for (const k of [-4, 0, 4]) { p.beginPath(); p.moveTo(x + k - 2, y - 3); p.lineTo(x + k + 2, y + 2); p.stroke(); } p.lineWidth = 1; }
      else { p.fillStyle = "#3AA0D8"; p.beginPath(); p.moveTo(x, y - 9); p.quadraticCurveTo(x + 8, y + 2, x, y + 8); p.quadraticCurveTo(x - 8, y + 2, x, y - 9); p.fill(); p.fillStyle = "rgba(255,255,255,0.6)"; p.fillRect(x - 3, y, 2, 3); }
    },
    shPerson(p, x, y, pp, dir, now) {
      const child = pp.age < CM.SHL.grow, s = child ? 0.65 : 1, step = Math.sin(now / 120 + pp.id) * 2;
      p.save(); p.translate(x, y); p.scale(dir * s, s); p.fillStyle = "#2A2420"; p.fillRect(-4, -8, 3, 8 + (step > 0 ? 0 : -1)); p.fillRect(1, -8, 3, 8 + (step > 0 ? -1 : 0));
      p.fillStyle = tint(pp.id); p.fillRect(-6, -24, 12, 16); p.fillStyle = "#E8C8A0"; p.beginPath(); p.arc(0, -29, 5, 0, Math.PI * 2); p.fill(); p.fillStyle = ["#3A2A1A", "#8A6A3A", "#C8A060", "#1A1A1A"][pp.id % 4]; p.fillRect(-5, -35, 10, 4); p.restore();
    },
  });
}
