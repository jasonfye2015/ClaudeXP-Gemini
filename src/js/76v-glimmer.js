"use strict";
// The Glimmer Maze, the window's side (the twenty-ninth big update): the hedge maze on a canvas - dark hedges with a
// lit edge, gold motes, the Hex Runes pulsing, the lantern-house and its door; the glimmerslime (its mouth toward where
// it goes, melting when caught), the four Lantern Haunts (a lantern's body with its flame's colour, a ragged hem, eyes
// that look the way they go; pale and wobbling when the runes scare them, blinking white as that wears off, only eyes on
// the way home), the lucky chip, the points; the score, the lives and the level at the top. Arrows or W A S D to steer
// (a turn can be given early), P to pause. The rules are 64zf-glimmer.js.
CM.CG_TABLES.push(["glimmer", "The Glimmer Maze"]);
{ const floor0 = CM.UI.prototype.renderFloor, C = 24, TOP = 28;
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "glimmer") return this.cgGlimmer(box); return floor0.call(this, box); },
    cgGlimmer(box) {
      const g = this.game, GZ = CM.GZ, S = g.gzState(), L = g.gzLevel(), live = !!L, bet = live ? S.bet : (this.cgBet === undefined ? 5 : this.cgBet), Cl = g.gzClaimed(), last = S && S.stage === "done" ? S.last : null;
      const top = Math.max(12, (S && live ? S.n : 1) + 4), rows = []; for (let n = 1; n <= top; n++) { const tier = CM.cardTierFor(n); rows.push(`<div class="rung${live && S.n === n ? " now" : ""}${live && S.n > n ? " done" : ""}"><span>Level ${n}</span><b>${Math.round(bet * GZ.pay(n))}</b><i class="${Cl[n] ? "got" : tier}" title="${Cl[n] ? "card already won" : `a ${tier === "better" ? "stronger common" : tier} card, the first time`}">${Cl[n] ? "✓" : tier === "rare" ? "★" : tier === "better" ? "◆" : "♦"}</i></div>`); }
      box.innerHTML = `<div class="cgtable glimmer runestack dash"><h3>The Glimmer Maze</h3><div class="rswrap"><canvas class="gzcanvas" width="${GZ.W * C}" height="${GZ.H * C + TOP}" tabindex="0"></canvas>
        <div class="dashside"><p class="lore">A hedge maze grown in the Joker's back garden, strung with glimmer motes. "Eat them all," says the attendant, handing you the reins of a hungry glimmerslime. "The lanterns don't like that. The runes in the corners - the lanterns like those even less."</p>
        <div class="ladder rsladder">${rows.reverse().join("")}</div>
        ${live ? "" : this.cgBetRow("The stake")}<div class="cgnote">${this.cgNote || ""}</div>${last && last.cards && last.cards.length ? last.cards.map((c) => this.cgCardWon(c)).join("") : ""}
        <div class="row">${live ? `<button data-gzpause>${this.gzPaused ? "Go on" : "Pause"}</button>` : `<button class="primary" data-gzstart>Into the maze (${bet} gold)</button>`}<button data-leave>Leave</button></div>
        <div class="small">Arrows or W A S D to steer - press a turn early and the slime takes it at the next corner; P to pause. Ember hunts you straight, Bramble heads where you are going, Frost comes from the far side, Moth closes in and then shies off; now and then they all drift to their corners. A Hex Rune makes them pale and slow - eat them then (200, 400, 800, 1600). The tunnels at the sides wrap round. A lucky chip shows under the lantern-house twice a level. Three lives, one more at 10,000. Each level cleared pays gold, more each, every play; its card comes the first time ever (♦ common 1-4, ◆ a stronger common 5-9, ★ rare from 10). Best score ${g.cgStore().gzBest || 0}.</div>${this.cgStats("glimmer")}</div></div></div>`;
      this.cgWireBet(box); const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      if (q("[data-gzstart]")) q("[data-gzstart]").addEventListener("click", () => { const r = g.gzStart(bet); this.cgNote = r.error || "Level 1. Eat!"; this.gzFx = { pts: [] }; this.gzPaused = false; this.cgSfx(r.error ? "miss" : "door", 0.45); this.renderCasino(); const cv = this.$("#casino-body .gzcanvas"); if (cv) cv.focus(); });
      if (q("[data-gzpause]")) q("[data-gzpause]").addEventListener("click", () => { this.gzPaused = !this.gzPaused; this.renderCasino(); });
      this.gzCanvas = q(".gzcanvas");
      if (!this.gzKeys) { const map = { ArrowUp: "up", KeyW: "up", ArrowDown: "down", KeyS: "down", ArrowLeft: "left", KeyA: "left", ArrowRight: "right", KeyD: "right" };
        this.gzKeys = (e) => { if (this.cgView !== "glimmer" || !this.dialogOpen() || !this.game.gzLevel()) return; if (e.code === "KeyP") { e.preventDefault(); this.gzPaused = !this.gzPaused; this.renderCasino(); return; } const d = map[e.code]; if (d) { e.preventDefault(); e.stopPropagation(); if (!this.gzPaused) this.game.gzLevel().input(d); } };
        window.addEventListener("keydown", this.gzKeys, true); }
      if (!this.gzLoop) { let prev = performance.now(); const loop = (now) => { if (!this.gzCanvas || !this.gzCanvas.isConnected || this.cgView !== "glimmer") { this.gzLoop = null; return; } const dt = Math.min(0.05, (now - prev) / 1000); prev = now; this.gzFrame(dt, now); this.gzLoop = requestAnimationFrame(loop); }; this.gzLoop = requestAnimationFrame(loop); }
    },
    gzFrame(dt, now) {
      const g = this.game, GZ = CM.GZ, L = g.gzLevel(), cv = this.gzCanvas, p = cv.getContext("2d"), fx = this.gzFx = this.gzFx || { pts: [] };
      if (L && !this.gzPaused) { L.update(dt); for (const e of L.events.splice(0)) this.gzEvent(e, now); const out = g.gzCheck();
        if (out && out.cleared) { fx.banner = { at: now, level: out.cleared, pay: out.pay, card: out.card }; this.cgSfx("victory", 0.55); if (out.card) setTimeout(() => this.cgSfx("cardwin", 0.5), 300); this.cgNote = `Level ${out.cleared} cleared: ${out.pay} gold${out.card ? `, and a card - ${out.card}` : ""}.`; this.renderCasino(); return; }
        if (out && out.over) { const S = g.gzState(); this.cgNote = `The last glimmer fades on level ${S.last.level}. ${S.won} gold back${S.last.cards.length ? `, and ${S.last.cards.length} card${S.last.cards.length > 1 ? "s" : ""}` : ""}.`; this.cgSfx("cardlose", 0.5); this.renderCasino(); if (S.won) this.cgCoins(this.$("#casino-body"), 12); return; } }
      const Lv = L || this.gzLastDrawn; if (L) this.gzLastDrawn = L;
      p.fillStyle = "#08100C"; p.fillRect(0, 0, cv.width, cv.height);
      p.fillStyle = "#FFE070"; p.font = "bold 14px monospace"; p.fillText(Lv ? `SCORE ${Lv.score}` : "THE GLIMMER MAZE", 8, 19); if (Lv) { p.fillText(`LEVEL ${Lv.n}`, cv.width / 2 - 30, 19); for (let k = 0; k < Lv.lives; k++) this.gzSlime(p, cv.width - 16 - k * 22, 14, "left", 0.42, 0.6, 0); }
      p.save(); p.translate(0, TOP);
      // the hedges: a dark body, a lit edge where it meets a path
      for (let y = 0; y < GZ.H; y++) for (let x = 0; x < GZ.W; x++) { const c = GZ.MAP[y][x], X = x * C, Y = y * C;
        if (c === "#") { p.fillStyle = "#1C4A2A"; p.fillRect(X, Y, C, C); p.fillStyle = "#3A8A4A"; const open = (dx, dy) => { const ch = (GZ.MAP[y + dy] || "")[x + dx]; return ch !== undefined && ch !== "#" && ch !== "X"; };
          if (open(0, -1)) p.fillRect(X, Y, C, 3); if (open(0, 1)) p.fillRect(X, Y + C - 3, C, 3); if (open(-1, 0)) p.fillRect(X, Y, 3, C); if (open(1, 0)) p.fillRect(X + C - 3, Y, 3, C);
          p.fillStyle = "rgba(120,200,120,0.18)"; if ((x * 7 + y * 13) % 5 === 0) p.fillRect(X + 8, Y + 9, 3, 3); }
        else if (c === "-") { p.fillStyle = "#F0A0C0"; p.fillRect(X, Y + C / 2 - 2, C, 4); }
        if (Lv && Lv.motes[y][x] === 1) { p.fillStyle = "#FFE48A"; p.fillRect(X + C / 2 - 2, Y + C / 2 - 2, 4, 4); }
        else if (Lv && Lv.motes[y][x] === 2) { const k = 0.6 + 0.4 * Math.sin(now / 160); p.save(); p.shadowColor = "#C080FF"; p.shadowBlur = 10 * k; p.fillStyle = `rgba(200,140,255,${0.6 + 0.4 * k})`; p.beginPath(); p.moveTo(X + C / 2, Y + 3); p.lineTo(X + C - 4, Y + C / 2); p.lineTo(X + C / 2, Y + C - 3); p.lineTo(X + 4, Y + C / 2); p.closePath(); p.fill(); p.fillStyle = "#FFF"; p.fillRect(X + C / 2 - 1, Y + C / 2 - 4, 2, 8); p.restore(); } }
      if (!Lv) { p.restore(); p.fillStyle = "rgba(255,240,200,0.9)"; p.font = "bold 24px Georgia, serif"; p.textAlign = "center"; p.fillText("The Glimmer Maze", cv.width / 2, cv.height / 2); p.textAlign = "left"; return; }
      if (Lv.chip) { const X = GZ.CHIP[0] * C + C / 2, Y = GZ.CHIP[1] * C + C / 2; p.fillStyle = "#C02030"; p.beginPath(); p.arc(X, Y, 9, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#FFF"; p.lineWidth = 2; p.setLineDash([3, 3]); p.beginPath(); p.arc(X, Y, 7, now / 400, now / 400 + Math.PI * 2); p.stroke(); p.setLineDash([]); p.fillStyle = "#FFE070"; p.beginPath(); p.arc(X, Y, 3, 0, Math.PI * 2); p.fill(); p.lineWidth = 1; }
      const P = Lv.p; this.gzSlime(p, P.fx * C + C / 2, P.fy * C + C / 2, P.dir, 1, Math.abs(Math.sin(P.mouth)) * 0.9, P.dead ? 1 - P.dead / 1.8 : 0);
      for (const h of Lv.haunts) this.gzHaunt(p, h, Lv, now);
      fx.pts = (fx.pts || []).filter((q) => now - q.at < 900); for (const q of fx.pts) { p.globalAlpha = 1 - (now - q.at) / 900; p.fillStyle = "#A0F0FF"; p.font = "bold 12px monospace"; p.fillText(String(q.n), q.x, q.y - (now - q.at) / 40); } p.globalAlpha = 1;
      p.restore();
      if (fx.banner && now - fx.banner.at < 2400) { const B = fx.banner, t = (now - B.at) / 2400; p.globalAlpha = t > 0.8 ? (1 - t) / 0.2 : 1; p.fillStyle = "rgba(0,0,0,0.7)"; p.fillRect(0, cv.height / 2 - 50, cv.width, 100); p.fillStyle = "#FFE070"; p.font = "bold 28px Georgia, serif"; p.textAlign = "center"; p.fillText(`Level ${B.level} cleared!`, cv.width / 2, cv.height / 2 - 10); p.font = "15px Georgia, serif"; p.fillStyle = "#F0E0B0"; p.fillText(`+${B.pay} gold${B.card ? ` - ${B.card}` : ""}`, cv.width / 2, cv.height / 2 + 20); p.textAlign = "left"; p.globalAlpha = 1; }
      if (this.gzPaused) { p.fillStyle = "rgba(0,0,0,0.6)"; p.fillRect(0, 0, cv.width, cv.height); p.fillStyle = "#FFF"; p.font = "bold 26px Georgia, serif"; p.textAlign = "center"; p.fillText("Paused", cv.width / 2, cv.height / 2); p.textAlign = "left"; }
    },
    gzEvent(e, now) {
      const fx = this.gzFx;
      if (e.kind === "mote") { this.gzTick = (this.gzTick || 0) + 1; if (this.gzTick % 2) this.cgSfx("coin", 0.1, 1.6 + (this.gzTick % 4) * 0.08); }
      else if (e.kind === "rune") this.cgSfx("spell", 0.5);
      else if (e.kind === "eat") { this.cgSfx("shatter", 0.45, 1.3); fx.pts.push({ x: e.h.fx * C, y: e.h.fy * C + C / 2, n: e.pts, at: now }); }
      else if (e.kind === "chip") this.cgSfx("tablebell", 0.35); else if (e.kind === "chipeat") { this.cgSfx("coin", 0.6); fx.pts.push({ x: CM.GZ.CHIP[0] * C - 6, y: CM.GZ.CHIP[1] * C + C / 2, n: e.pts, at: now }); }
      else if (e.kind === "die") this.cgSfx("hurt", 0.6); else if (e.kind === "extra") this.cgSfx("cardwin", 0.4); else if (e.kind === "clear") this.cgSfx("tablebell", 0.5);
    },
    // the glimmerslime: a teal blob with a shine, two eyes, a mouth that opens toward where it goes; melts when caught
    gzSlime(p, X, Y, dir, s, open, melt) {
      const ang = { right: 0, down: Math.PI / 2, left: Math.PI, up: -Math.PI / 2 }[dir] || 0, r = 10 * s, m = open * 0.6;
      p.save(); p.translate(X, Y); p.scale(1 + melt * 0.6, 1 - melt * 0.8); p.translate(0, melt * 8 * s);
      const gr = p.createRadialGradient(-3 * s, -3 * s, 1, 0, 0, r); gr.addColorStop(0, "#C0FFF0"); gr.addColorStop(1, "#30B8A0"); p.fillStyle = gr;
      p.beginPath(); p.moveTo(0, 0); p.arc(0, 0, r, ang + m, ang + Math.PI * 2 - m); p.closePath(); p.fill();
      if (!melt) { const ex = Math.cos(ang - 1.2) * r * 0.45, ey = Math.sin(ang - 1.2) * r * 0.45; p.fillStyle = "#103028"; p.fillRect(ex - 1.5 * s, ey - 1.5 * s, 3 * s, 3 * s); }
      p.restore();
    },
    // a Lantern Haunt: a lantern's glow for a body with a ragged hem; pale when scared, only eyes on the way home
    gzHaunt(p, h, Lv, now) {
      const GZ = CM.GZ, X = h.fx * C + C / 2, Y = h.fy * C + C / 2, look = GZ.DIRS[h.dir] || [0, 0];
      const eyes = () => { for (const ex of [-4, 4]) { p.fillStyle = "#FFF"; p.beginPath(); p.ellipse(X + ex, Y - 2, 3.2, 4, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#2030A0"; p.beginPath(); p.arc(X + ex + look[0] * 1.6, Y - 2 + look[1] * 2, 1.8, 0, Math.PI * 2); p.fill(); } };
      if (h.state === "eyes" || h.state === "entering") return eyes();
      const scared = h.scared && Lv.fright > 0, blink = scared && Lv.fright < 2 && Math.floor(now / 180) % 2, col = scared ? (blink ? "#F0F0FF" : "#5060E0") : GZ.HAUNTS[h.i].color;
      p.save(); p.shadowColor = col; p.shadowBlur = scared ? 4 : 12; p.fillStyle = col;
      p.beginPath(); p.moveTo(X - 10, Y + 10); p.lineTo(X - 10, Y - 2); p.quadraticCurveTo(X - 10, Y - 11, X, Y - 11); p.quadraticCurveTo(X + 10, Y - 11, X + 10, Y - 2); p.lineTo(X + 10, Y + 10);
      const w = Math.floor(now / 120) % 2; for (let k = 0; k < 4; k++) { p.lineTo(X + 10 - k * 5 - 2.5, (k + w) % 2 ? Y + 6 : Y + 10); p.lineTo(X + 10 - (k + 1) * 5, Y + 10); }
      p.closePath(); p.fill(); p.restore();
      if (!scared) { p.fillStyle = "rgba(255,255,220,0.45)"; p.fillRect(X - 6, Y + 3, 12, 2); p.fillStyle = "#3A2A10"; p.fillRect(X - 3, Y - 14, 6, 3); eyes(); }
      else { p.fillStyle = blink ? "#E04040" : "#FFE0C0"; p.fillRect(X - 4, Y - 4, 3, 3); p.fillRect(X + 1, Y - 4, 3, 3); p.strokeStyle = p.fillStyle; p.beginPath(); for (let k = 0; k <= 4; k++) p.lineTo(X - 6 + k * 3, Y + 3 + (k % 2 ? -2 : 0)); p.stroke(); }
    },
  });
}
