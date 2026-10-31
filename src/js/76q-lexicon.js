"use strict";
// The Lexicon Engine, the window's side (the twenty-sixth big update): a green-glass screen in a brass case - the glow,
// the scanlines, a slow roll and a flicker, the curve of the glass at its corners; the header typed out a letter at a
// time; the memory in two columns with their addresses; a word (or a bracket pair) lit as the pointer passes over it;
// the engine's answers typed into the log at the right; keys that tick. The rules are 64za-lexicon.js.
CM.CG_TABLES.push(["lexicon", "The Lexicon Engine"]);
{ const floor0 = CM.UI.prototype.renderFloor;
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "lexicon") return this.cgLexicon(box); return floor0.call(this, box); },
    cgLexicon(box) {
      const g = this.game, LX = CM.LX, S = g.lxStore(), P = g.lxLive, levels = LX.LEVELS.map(([len, n], i) => { const k = i + 1, done = k <= S.best, open = k <= S.best + 1, tier = CM.cardTierFor(k); return `<button data-lxl="${k}" class="${P && P.level === k ? "primary" : ""}" ${open ? "" : "disabled"} title="${len} letters, ${n} words; first crack: ${LX.gold(k)} gold and a ${tier === "better" ? "stronger common" : tier} card">${done ? "✓ " : open ? "" : "🔒 "}${k}</button>`; }).join("");
      box.innerHTML = `<div class="cgtable lexicon"><h3>The Lexicon Engine</h3><p class="lore">In the corner, a brass case with a green glass screen, humming. The artificer who left it here owes the house money; the house lets anyone who can get into it keep what it pays out. "It wants a word," says the attendant. "It will tell you how near you came."</p>
        <div class="lxlevels"><span class="lbl">Level:</span>${levels}</div>
        <div class="crt"><div class="crtglass"><div class="crtscreen" data-lxscreen></div></div><div class="crtscan"></div><div class="crtroll"></div></div>
        <div class="cgnote">${this.cgNote || ""}</div>${this.lxPrize && this.lxPrize.card ? this.cgCardWon(this.lxPrize.card) : ""}
        <div class="row">${P && P.stage !== "play" ? `<button class="primary" data-lxagain>${P.stage === "won" ? (P.level < LX.LEVELS.length ? `On to level ${P.level + 1}` : "Again") : "Try again"}</button>` : ""}<button data-leave>Leave</button></div>
        <div class="small">Choose a word in the memory: the engine answers with its likeness - how many letters stand in the same places as the password's. A pair of brackets with only symbols between them, on one row, takes out a dud or gives your tries back. Each level pays gold and a Claudescryption card the first time it is cracked (common to 4, a stronger common to 9, rare at 10); it costs nothing to sit down. Cracked ${S.best} of ${LX.LEVELS.length}.</div></div>`;
      const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => this.closeDialogs());
      box.querySelectorAll("[data-lxl]").forEach((b) => b.addEventListener("click", () => { const r = g.lxStart(Number(b.dataset.lxl)); this.cgNote = r.error || ""; this.lxPrize = null; this.lxBoot = performance.now(); this.cgSfx("hinge", 0.3, 1.6); this.renderCasino(); }));
      if (q("[data-lxagain]")) q("[data-lxagain]").addEventListener("click", () => { const lv = P.stage === "won" ? Math.min(LX.LEVELS.length, P.level + 1) : P.level; g.lxStart(lv); this.cgNote = ""; this.lxPrize = null; this.lxBoot = performance.now(); this.renderCasino(); });
      this.lxDraw(q("[data-lxscreen]"));
    },
    lxDraw(scr) {
      const g = this.game, LX = CM.LX, P = g.lxLive;
      if (!P) { scr.innerHTML = `<div class="lxhead">ARTIFICER'S LEXICON ENGINE - MODEL IX<br>(c) THE GUILD OF ARTIFICERS<br><br>&gt; CHOOSE A LEVEL TO BEGIN_<span class="cur"></span></div>`; return; }
      const W = LX.width, addr = (r) => `0x${(0xF4A0 + r * W).toString(16).toUpperCase()}`, boxes = "▮".repeat(P.tries) + "▯".repeat(P.maxTries - P.tries);
      const head = `ARTIFICER'S LEXICON ENGINE - MODEL IX<br>${P.stage === "locked" ? "!!! ENGINE LOCKED !!!" : P.stage === "won" ? "&gt; ACCESS GRANTED" : P.tries === 1 ? "!!! WARNING: LOCKOUT IMMINENT !!!" : "ENTER PASSWORD NOW"}<br><br>${P.tries} ATTEMPT(S) LEFT: <span class="tries">${boxes}</span>`;
      let mem = ""; for (let c = 0; c < LX.cols; c++) { mem += `<div class="lxcol">`; for (let r = 0; r < LX.rows; r++) { const row = c * LX.rows + r; mem += `<div class="lxrow"><span class="ad">${addr(row)}</span> `; for (let k = 0; k < W; k++) { const i = row * W + k, ch = P.chars[i]; mem += `<span data-i="${i}">${ch === "<" ? "&lt;" : ch === ">" ? "&gt;" : ch === "&" ? "&amp;" : ch}</span>`; } mem += "</div>"; } mem += "</div>"; }
      const log = P.log.slice(-16).map((l) => `<div>${l.replace(/</g, "&lt;").replace(/>/g, "&gt;")}</div>`).join("");
      scr.innerHTML = `<div class="lxhead" data-lxhead></div><div class="lxbody"><div class="lxmem">${mem}</div><div class="lxlog">${log}<div class="lxin">&gt;<span data-lxin></span><span class="cur"></span></div></div></div>`;
      // the header typed out a letter at a time when the engine wakes
      const hd = scr.querySelector("[data-lxhead]"), t0 = this.lxBoot || 0, full = head;
      if (performance.now() - t0 < 1500) { const plain = full.replace(/<br>/g, "\n").replace(/<[^>]+>/g, "").replace(/&gt;/g, ">"); let n = 0; hd.style.whiteSpace = "pre-line"; const tick = () => { if (!hd.isConnected) return; n = Math.min(plain.length, n + 3); hd.textContent = plain.slice(0, n); if (n % 6 === 0) this.cgSfx("step", 0.05, 2.2); if (n < plain.length) setTimeout(tick, 16); else { hd.style.whiteSpace = ""; hd.innerHTML = full; } }; tick(); } else hd.innerHTML = full;
      const spans = scr.querySelectorAll("[data-i]"), inp = scr.querySelector("[data-lxin]"), lit = (set, on) => { for (const i of set) spans[i] && spans[i].classList.toggle("lit", on); };
      let cur = [];
      const target = (i) => { const w = P.wordAt(i); if (w && !P.removed.has(w.w)) return { kind: "word", w, cells: Array.from({ length: w.w.length }, (_, k) => w.at + k) }; const b = P.bracketAt(i); if (b) return { kind: "bracket", b, cells: Array.from({ length: b.b - b.a + 1 }, (_, k) => b.a + k) }; return { kind: "char", cells: [i] }; };
      spans.forEach((sp) => {
        sp.addEventListener("mouseenter", () => { if (P.stage !== "play") return; lit(cur, false); const T = target(Number(sp.dataset.i)); cur = T.cells; lit(cur, true); inp.textContent = T.kind === "word" ? T.w.w : T.cells.map((i) => P.chars[i]).join(""); this.cgSfx("card", 0.05, 2.4); });
        sp.addEventListener("click", () => {
          if (P.stage !== "play") return; const T = target(Number(sp.dataset.i)); if (T.kind === "char") { P.log.push(`>${P.chars[T.cells[0]]}`, ">Error"); this.cgSfx("miss", 0.15, 1.6); this.lxDraw(scr); return; }
          if (T.kind === "bracket") { const r = P.bracket(T.b); if (r) this.cgSfx(r.reset ? "heal" : "zap", 0.35); this.lxDraw(scr); return; }
          const r = P.choose(T.w.w); if (!r) return; this.cgSfx("cardplace", 0.4, 1.4);
          if (r.won) { const pr = g.lxCracked(); this.lxPrize = pr; this.cgSfx("victory", 0.6); this.cgNote = pr && !pr.again ? `Level ${pr.level} cracked: ${pr.gold} gold${pr.card ? `, and a card - ${pr.card}` : ""}.` : `Level ${P.level} cracked again (its prize was paid the first time).`; if (pr && pr.card) setTimeout(() => this.cgSfx("cardwin", 0.5), 300); this.renderCasino(); if (pr && pr.gold) this.cgCoins(this.$("#casino-body"), 12); return; }
          if (P.stage === "locked") { this.cgSfx("slam", 0.5); this.cgNote = `Locked out. The password was ${P.answer}.`; this.renderCasino(); return; }
          this.cgSfx("miss", 0.3, 0.9); this.lxDraw(scr);
        });
      });
    },
  });
}
