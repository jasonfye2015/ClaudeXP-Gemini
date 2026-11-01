"use strict";
// The Glyph Deep, the screen (v20.0): the cabinet's dialog (who plays, from which level, what's been paid), and the game
// drawn as letters on a black screen laid over the view - two lines of messages at the top, the level's 80x21, two lines
// of the hero's numbers at the bottom; the pack as a list over the map (i), prompts for what to drink, read, wield, wear,
// eat or drop, and for the stairs. Keys: arrows, the number pad or hjklyubn to move and fight, g or , to pick up, q r w W
// e d, . or 5 to wait, > and < at the stairs, i the pack, Esc to cancel. A click on the map steps toward it; a click in
// the pack offers that thing. The game is 64zzzc-glyph.js, the cabinet's rules 69o-glyphdeep.js.
{ const GD = CM.GLYPH, COLS = 80, ROWS = 25, TOP = 2;
  const MOVES = { ArrowUp: [0, -1], ArrowDown: [0, 1], ArrowLeft: [-1, 0], ArrowRight: [1, 0], Numpad8: [0, -1], Numpad2: [0, 1], Numpad4: [-1, 0], Numpad6: [1, 0], Numpad7: [-1, -1], Numpad9: [1, -1], Numpad1: [-1, 1], Numpad3: [1, 1],
    k: [0, -1], j: [0, 1], h: [-1, 0], l: [1, 0], y: [-1, -1], u: [1, -1], b: [-1, 1], n: [1, 1] };
  const ASK = { q: ["quaff", "drink", (it) => it.kind === "heal" || it.kind === "mana"], r: ["read", "read", (it) => it.kind === "gscroll"], w: ["wield", "wield", (it) => it.kind === "weapon"],
    W: ["wear", "wear", (it) => ["armor", "shield", "helm"].includes(it.kind)], e: ["eat", "eat", (it) => it.kind === "ration"], d: ["drop", "drop", () => true] };
  const TILE_COL = { "-": "#8A8A9A", "|": "#8A8A9A", ".": "#5A5A64", "#": "#7A7A7A", "+": "#B08040", "<": "#F0F0F0", ">": "#F0F0F0" };
  // the cabinet as the Wood shows it: a tall cabinet of dark wood, its marquee, the screen green with letters
  CM.art.glyphCabinet = function (size) { const c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"), u = size / 64;
    p.fillStyle = "#3A2418"; p.fillRect(16 * u, 6 * u, 32 * u, 58 * u); p.fillStyle = "#5A3A24"; p.fillRect(18 * u, 8 * u, 28 * u, 54 * u);
    p.fillStyle = "#1A1A2A"; p.fillRect(18 * u, 8 * u, 28 * u, 8 * u); p.fillStyle = "#60F080"; p.font = `bold ${5 * u}px monospace`; p.textAlign = "center"; p.fillText("GLYPH DEEP", 32 * u, 14 * u);
    p.fillStyle = "#061206"; p.fillRect(20 * u, 19 * u, 24 * u, 18 * u); p.fillStyle = "#50E070"; p.font = `${3.6 * u}px monospace`; p.textAlign = "left";
    ["|....@.|", "|.g..$.|", "--+-----"].forEach((t, i) => p.fillText(t, 21 * u, (24 + i * 5) * u));
    p.fillStyle = "#2A1A10"; p.fillRect(16 * u, 38 * u, 32 * u, 8 * u); p.fillStyle = "#C03030"; p.beginPath(); p.arc(26 * u, 42 * u, 2 * u, 0, Math.PI * 2); p.fill(); p.fillStyle = "#3060C0"; p.beginPath(); p.arc(36 * u, 42 * u, 2 * u, 0, Math.PI * 2); p.fill();
    p.fillStyle = "#C0A040"; p.fillRect(30 * u, 50 * u, 4 * u, 6 * u); p.fillStyle = "#6A4A2A"; p.fillRect(8 * u, 2 * u, 48 * u, 4 * u); return c; };
  { const b0 = CM.art.build; CM.art.build = function (theme, look) { const set = b0.call(this, theme, look); set.index.glyphcab = set.layers.length; set.layers.push(CM.art.glyphCabinet(set.size)); return set; }; }
  const ensure = (ui) => { if (ui.$("#dlg-glyph")) return; const d = document.createElement("div"); d.className = "dialog"; d.id = "dlg-glyph";
    d.innerHTML = `<div class="box glyphbox"><h2 class="gdtitle">THE GLYPH DEEP</h2><div id="gd-body"></div><div class="note" id="gd-note"></div><div class="row"><button data-gdclose>Walk away</button></div></div>`;
    (ui.root || document.body).appendChild(d); d.querySelector("[data-gdclose]").addEventListener("click", () => ui.closeDialogs()); };
  Object.assign(CM.UI.prototype, {
    openGlyphCab() { ensure(this); const g = this.game, S = g.glyphStore(), box = this.$("#gd-body"), top = g.glyphLevels(); this.gdStart = Math.min(this.gdStart || top, top);
      box.innerHTML = `<pre class="gdattract">  ----------        @ - you          $ gold     ! potion    ? scroll
  |..@...>.|        a-z - monsters   ) weapon   [ armour    = ring
  ----+-----        &  - the Unwritten  , seed  ~ card   * tickets</pre>
        <p class="small">One of the party plays, alone, with their own health, arms and skills. Reach the stairs down (&gt;) to go deeper, or to come home with everything. The first time each level's stairs are reached, tickets, gold and a thing go to the party. Die, and they come back with a tenth of their health and without what that level gave. At level 20, the Unwritten.</p>
        <p>Start on level <select data-gdlevel>${Array.from({ length: top }, (_, i) => i + 1).map((L) => `<option value="${L}" ${L === this.gdStart ? "selected" : ""}>${L}${S.paid[L] ? " (paid)" : ""}</option>`).join("")}</select> <span class="small">(any level reached so far)</span></p>
        <div class="list-title">Who plays</div>${g.glyphChoices().map((c) => `<div class="recruit" style="grid-template-columns: 1fr auto"><div><b>${this.esc(c.name)}</b> <small>${this.esc(c.cls)}, level ${c.level}${c.why ? ` - ${this.esc(c.why)}` : ""}</small></div><button data-gdhero="${c.i}" ${c.why ? "disabled" : ""}>Play</button></div>`).join("")}
        <p class="small">Levels paid: ${Object.keys(S.paid).length} of ${GD.levels}${S.boss ? " - the Unwritten is beaten" : ""}. Deaths: ${S.deaths}.</p>`;
      box.querySelector("[data-gdlevel]").addEventListener("change", (e) => { this.gdStart = Number(e.target.value); });
      box.querySelectorAll("[data-gdhero]").forEach((b) => b.addEventListener("click", () => { const why = g.enterGlyph(Number(b.dataset.gdhero), this.gdStart || 1); this.$("#gd-note").textContent = why || ""; if (!why) { this.closeDialogs(); this.gdLog = []; this.gdAsk = null; this.gdInv = false; this.refresh(); this.drawGlyph(); } }));
      this.$("#gd-note").textContent = ""; this.openDialog("#dlg-glyph"); },
    glyphCanvas() { let c = this.$("#glyphcanvas"); if (!c) { c = document.createElement("canvas"); c.id = "glyphcanvas"; this.$("#view").appendChild(c); c.addEventListener("mousedown", (e) => this.glyphClick(e)); }
      const r = c.getBoundingClientRect(), dpr = Math.min(2, window.devicePixelRatio || 1), w = Math.max(320, Math.round(r.width * dpr)), h = Math.max(200, Math.round(r.height * dpr)); if (c.width !== w || c.height !== h) { c.width = w; c.height = h; } return c; },
    // one turn, and what it said
    glyphDo(cmd, arg) { const g = this.game, r = g.glyphRun; if (!r) return; const before = { hp: r.hp, gold: r.gold }, msgs = g.glyphAct(cmd, arg) || [];
      this.gdLog = (this.gdLog || []).concat(msgs).slice(-60); this.gdNow = msgs;
      try { if (msgs.some((m) => /^You (hit|smite|kill)/.test(m))) CM.audio.play("hit", 0.35); if (r.hp < before.hp) CM.audio.play("hurt", 0.4); if (r.gold > before.gold) CM.audio.play("coin", 0.35); if (msgs.some((m) => /^You die/.test(m))) CM.audio.play("death", 0.5); } catch (e) { /* quiet */ }
      this.drawGlyph(); this.refresh(); },
    glyphKey(e) { const g = this.game, r = g.glyphRun; if (!r) return false; const k = e.key;
      if (this.gdAsk) { e.preventDefault(); if (k === "Escape") { this.gdAsk = null; this.gdNow = ["Never mind."]; this.drawGlyph(); return true; } const A = this.gdAsk;
        if (A.kind === "stairs") { if (/^[dD]$/.test(k) && r.L < GD.levels) { this.gdAsk = null; const why = g.glyphStairs(true); this.gdNow = [why || `Level ${g.glyphRun ? g.glyphRun.L : ""}.`]; this.gdLog.push(...this.gdNow); this.drawGlyph(); this.refresh(); } else if (/^[hH]$/.test(k) || (r.L >= GD.levels && /^[yY]$/.test(k))) { this.gdAsk = null; g.glyphStairs(false); this.refresh(); } return true; }
        if (A.kind === "up") { if (/^[yY]$/.test(k)) { this.gdAsk = null; g.glyphUp(); this.refresh(); } else { this.gdAsk = null; this.drawGlyph(); } return true; }
        const i = k.length === 1 ? k.charCodeAt(0) - 97 : -1; if (i >= 0 && i < r.pack.length) { this.gdAsk = null; this.glyphDo(A.cmd, i); } return true; }
      if (this.gdInv && k === "Escape") { e.preventDefault(); this.gdInv = false; this.drawGlyph(); return true; }
      const mv = MOVES[e.code] || (k.length === 1 && !e.shiftKey ? MOVES[k] : null); if (mv) { e.preventDefault(); this.gdInv = false; this.glyphDo("move", mv); return true; }
      if (k === "." || e.code === "Numpad5") { e.preventDefault(); this.glyphDo("wait"); return true; }
      if (k === "g" || k === ",") { e.preventDefault(); this.glyphDo("pick"); return true; }
      if (k === "i") { e.preventDefault(); this.gdInv = !this.gdInv; this.drawGlyph(); return true; }
      if (k === ">") { e.preventDefault(); this.glyphStairsAsk(); return true; }
      if (k === "<") { e.preventDefault(); if (r.atUp()) { this.gdAsk = { kind: "up" }; this.gdNow = ["Climb out and walk away? What this level gave stays here. [y/n]"]; } else this.gdNow = ["You can't go up here."]; this.drawGlyph(); return true; }
      if (ASK[k]) { e.preventDefault(); const [cmd, verb, ok] = ASK[k], can = r.pack.map((it, i) => [it, i]).filter(([it]) => ok(it)); if (!can.length) { this.gdNow = [`You don't have anything to ${verb}.`]; this.drawGlyph(); return true; }
        this.gdAsk = { cmd, ok }; this.gdInv = true; this.gdNow = [`What do you want to ${verb}? [${can.map(([, i]) => String.fromCharCode(97 + i)).join("")} or Esc]`]; this.drawGlyph(); return true; }
      return false; },
    glyphStairsAsk() { const r = this.game.glyphRun; if (!r.atDown()) { this.gdNow = ["You can't go down here."]; this.drawGlyph(); return; } if (r.L === GD.levels && !r.bossDown()) { this.gdNow = ["The way down is sealed while the Unwritten stands."]; this.drawGlyph(); return; }
      const paid = this.game.glyphStore().paid[r.L]; this.gdAsk = { kind: "stairs" }; this.gdNow = [r.L >= GD.levels ? "The last stairs. Climb out into the light? [y]" : `[D]own to level ${r.L + 1}, or [H]ome with everything?${paid ? "" : " (this level pays the party the first time)"}`]; this.drawGlyph(); },
    glyphClick(e) { const r = this.game.glyphRun, V = this.gdView; if (!r || !V) return; const c = this.$("#glyphcanvas"), b = c.getBoundingClientRect(), x = (e.clientX - b.left) * (c.width / b.width), y = (e.clientY - b.top) * (c.height / b.height);
      if (this.gdInv && V.inv) { const row = Math.floor((y - V.inv.y) / V.ch); if (x >= V.inv.x && row >= 0 && row < r.pack.length) { const it = r.pack[row], A = this.gdAsk; if (A && A.cmd && A.ok(it)) { this.gdAsk = null; this.glyphDo(A.cmd, row); return; }
        const uses = Object.entries(ASK).filter(([, [, , ok]]) => ok(it)); if (uses.length === 1 || (uses.length && uses[0][0] !== "d")) { const [cmd] = uses[0][1]; if (cmd !== "drop") { this.glyphDo(cmd, row); return; } } } return; }
      const gx = Math.floor(x / V.cw), gy = Math.floor(y / V.ch) - TOP; if (gy < 0 || gy >= GD.H) return; const dx = Math.sign(gx - r.x), dy = Math.sign(gy - r.y); if (dx || dy) this.glyphDo("move", [dx, dy]); else if (r.thingAt(r.x, r.y)) this.glyphDo("pick"); else if (r.atDown()) this.glyphStairsAsk(); },
    // the screen
    drawGlyph() { const r = this.game.glyphRun, c = this.glyphCanvas(), p = c.getContext("2d"); p.fillStyle = "#000"; p.fillRect(0, 0, c.width, c.height); if (!r) return;
      const cw = c.width / COLS, ch = c.height / ROWS, fs = Math.floor(Math.min(cw * 1.62, ch * 0.92)); this.gdView = { cw, ch };
      p.font = `${fs}px Consolas, "Courier New", monospace`; p.textBaseline = "middle"; p.textAlign = "center";
      const put = (x, y, t, col, bg) => { if (bg) { p.fillStyle = bg; p.fillRect(x * cw, (y + TOP) * ch, cw, ch); } p.fillStyle = col; p.fillText(t, x * cw + cw / 2, (y + TOP) * ch + ch / 2 + 1); };
      for (let y = 0; y < GD.H; y++) for (let x = 0; x < GD.W; x++) { const k = `${x},${y}`; if (!r.seen.has(k)) continue; const t = r.tile(x, y); if (t === " ") continue; const vis = r.visible(x, y); put(x, y, t, vis ? TILE_COL[t] || "#AAA" : "#33333C"); }
      for (const [k, list] of r.things) { if (!list.length || !r.seen.has(k)) continue; const [x, y] = k.split(",").map(Number); if (!r.visible(x, y) && !r.seen.has(k)) continue; const it = list[list.length - 1]; put(x, y, GD.glyphOf(it), r.visible(x, y) ? GD.colourOf(it) : "#44444C"); }
      for (const m of r.mons) if (m.hp > 0 && r.visible(m.x, m.y)) put(m.x, m.y, m.hidden ? "$" : m.ch, m.hidden ? "#F0D040" : m.col, m.boss ? "#2A002A" : null);
      put(r.x, r.y, "@", "#FFFFFF", "#203040");
      // the messages
      p.textAlign = "left"; p.font = `${Math.floor(ch * 0.78)}px Consolas, "Courier New", monospace`; const now = this.gdNow || []; p.fillStyle = "#E8E8E8";
      now.slice(-2).forEach((m, i) => p.fillText(m.slice(0, 110), 6, ch * (i + 0.5) + 1));
      // the hero's numbers
      const h = r.hero, at = r.heroAtk(), y1 = (ROWS - 2) * ch + ch / 2, y2 = (ROWS - 1) * ch + ch / 2, frac = r.hp / r.max;
      p.fillStyle = "#C0C0C0"; p.fillText(`${h.name} the ${h.cls}    Dlvl:${r.L}  $:${r.gold}  HP:`, 6, y1); const w0 = p.measureText(`${h.name} the ${h.cls}    Dlvl:${r.L}  $:${r.gold}  HP:`).width;
      p.fillStyle = frac > 0.5 ? "#60E060" : frac > 0.25 ? "#F0D040" : "#F05050"; p.fillText(`${r.hp}(${r.max})`, 6 + w0, y1); const w1 = p.measureText(`${r.hp}(${r.max})`).width;
      p.fillStyle = "#C0C0C0"; p.fillText(`  Atk:${at.atk}+${at.power}  Def:${r.heroDf()}  T:${r.turn}  Kills:${r.kills}`, 6 + w0 + w1, y1);
      p.fillText(`Wielding: ${r.wield ? r.wield.name : (h.weapon ? h.weapon.name : "bare hands")}   Wearing: ${r.wear ? r.wear.name : (h.armor ? h.armor.name : "nothing extra")}   Pack: ${r.pack.length}/26`, 6, y2);
      // the pack, over the map
      if (this.gdInv) { const lines = r.pack.length ? r.pack.map((it, i) => `${String.fromCharCode(97 + i)} - ${it.kind === "gtickets" ? `${it.n} prize tickets` : it.name}${it === r.wield ? " (wielded)" : it === r.wear ? " (worn)" : ""}${it.gsecure ? "" : " *"}`) : ["Your pack is empty."];
        const head = this.gdAsk && this.gdAsk.cmd ? "Choose:" : "Your pack (* found on this level):", wpx = Math.min(c.width * 0.6, Math.max(p.measureText(head).width, ...lines.map((l) => p.measureText(l).width)) + 30), x0 = c.width - wpx - 8, y0 = TOP * ch;
        p.fillStyle = "rgba(0,0,0,0.92)"; p.fillRect(x0, y0, wpx, (lines.length + 2) * ch); p.strokeStyle = "#5A5A6A"; p.strokeRect(x0, y0, wpx, (lines.length + 2) * ch);
        p.fillStyle = "#F0F0C0"; p.fillText(head, x0 + 10, y0 + ch / 2 + 1);
        lines.forEach((l, i) => { const it = r.pack[i]; p.fillStyle = it ? (this.gdAsk && this.gdAsk.ok && !this.gdAsk.ok(it) ? "#555" : GD.colourOf(it)) : "#AAA"; p.fillText(l, x0 + 10, y0 + (i + 1.5) * ch + 1); });
        this.gdView.inv = { x: x0, y: y0 + ch }; } else this.gdView.inv = null; },
  });
  // the action bar under the view while playing
  { const ra0 = CM.UI.prototype.renderActions; CM.UI.prototype.renderActions = function () { const g = this.game, box = this.$("#actions") || this.$(".actions"); if (g.mode !== "glyph") { if (box && box.dataset.mode && box.dataset.mode.startsWith("glyph")) box.dataset.mode = ""; return ra0.call(this); }
      const r = g.glyphRun; if (!r || !box) return; const k = `glyph:${r.L}:${r.atDown()}:${r.atUp()}`; if (box.dataset.mode === k) return; box.dataset.mode = k; box.innerHTML = "";
      const add = (text, fn, cls) => { const b = document.createElement("button"); b.textContent = text; if (cls) b.className = cls; b.addEventListener("click", () => { fn(); this.drawGlyph(); }); box.appendChild(b); };
      if (r.atDown()) add(r.L >= GD.levels ? "Climb out into the light (>)" : `Down to level ${r.L + 1} (> then D)`, () => { if (r.L >= GD.levels) g.glyphStairs(false); else { const why = g.glyphStairs(true); this.gdNow = [why || `Level ${g.glyphRun ? g.glyphRun.L : ""}.`]; } this.refresh(); }, "primary");
      if (r.atDown() && r.L < GD.levels) add("Home with everything (> then H)", () => { g.glyphStairs(false); this.refresh(); });
      add("Pack (i)", () => { this.gdInv = !this.gdInv; }); add("Pick up (g)", () => this.glyphDo("pick")); add("Wait (.)", () => this.glyphDo("wait"));
      add(r.atUp() ? "Climb out (this level's finds stay)" : "Walk away (this level's finds stay)", () => { g.leaveGlyph("fled"); this.refresh(); }); }; }
  { const rf0 = CM.UI.prototype.refresh; CM.UI.prototype.refresh = function (...a) { const out = rf0.apply(this, a); const on = this.game && this.game.mode === "glyph"; document.body.classList.toggle("inglyph", on); if (on) this.drawGlyph(); return out; }; }
  // the keys, before the game's own
  if (typeof window !== "undefined") window.addEventListener("keydown", (e) => { const ui = CM.ui, g = ui && ui.game; if (!g || g.mode !== "glyph" || !g.glyphRun || (ui.dialogOpen && ui.dialogOpen())) return; if (ui.glyphKey(e)) e.stopImmediatePropagation(); }, true);
  if (typeof window !== "undefined") window.addEventListener("resize", () => { const ui = CM.ui; if (ui && ui.game && ui.game.mode === "glyph") ui.drawGlyph(); });
}
