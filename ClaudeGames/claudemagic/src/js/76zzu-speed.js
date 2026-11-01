"use strict";
// Fast mode and auto-play (v17.1). Fast: at the tables where the waiting is only watching - reels, wheels, cards
// dealt, chips falling, balls drawn - a "Fast" switch on the bar runs the window's clock two and a half times quicker
// (its animations, its pauses), and nothing else changes: the same results, the same pays. It's not offered where
// timing is the game (the cabinets, the fairground's aim, the pond's strike, the claw). The choice is remembered.
// Auto-play: at the tables where a play is one press - the reels, roulette and the Joker's Wheel (the bets on the
// board stay), the Drop Board, the slips - "Auto" plays 10, 25, 50 or 100 in a row, and stops early on a big win (if
// asked), when the purse runs short, on any key or click, or on leaving the table.
{ const SP = CM.SPEED = { rate: 2.5, FAST: ["slots", "roulette", "blackjack", "poker", "craps", "bigwheel", "scratch", "prizewheel", "pachinko", "plinko", "lottery", "bingo", "holdem", "hexwand", "pit", "claudeatro", "cascade"],
    AUTO: ["slots", "roulette", "bigwheel", "plinko", "scratch"], RUNS: [10, 25, 50, 100], big: 10 };
  // the window's clock: performance.now, the frames' time, the timers and the animations, all at one rate
  const realNow = performance.now.bind(performance); let vBase = realNow(), rBase = vBase, cur = 1;
  const vnow = () => vBase + (realNow() - rBase) * cur;
  SP.setRate = (k) => { if (k === cur) return; vBase = vnow(); rBase = realNow(); cur = k; for (const a of document.getAnimations ? document.getAnimations() : []) if (a.effect && a.effect.target && a.effect.target.closest && a.effect.target.closest("#dlg-casino")) a.playbackRate = k; };
  SP.rateNow = () => cur;
  performance.now = vnow;
  { const raf0 = window.requestAnimationFrame.bind(window); window.requestAnimationFrame = (cb) => raf0(() => cb(vnow())); }
  { const st0 = window.setTimeout.bind(window); window.setTimeout = (f, d, ...a) => st0(f, cur > 1 && typeof d === "number" ? d / cur : d, ...a); }
  if (window.Element && Element.prototype.animate) { const an0 = Element.prototype.animate; Element.prototype.animate = function (...a) { const x = an0.apply(this, a); if (cur > 1 && this.closest && this.closest("#dlg-casino")) x.playbackRate = cur; return x; }; }
  const r14 = CM.UI.prototype.renderCasino, nav14 = CM.UI.prototype.cgNav, close14 = CM.UI.prototype.closeDialogs;
  Object.assign(CM.UI.prototype, {
    cgFastOn() { const L = this.game.lbStore ? this.game.lbStore() : {}; return !!L.fast; },
    cgSpeedSync() { const dlg = this.$("#dlg-casino"), on = dlg && dlg.classList.contains("on") && SP.FAST.includes(this.cgView) && this.cgFastOn(); SP.setRate(on ? SP.rate : 1); },
    renderCasino() { if (this.cgAuto && this.cgAuto.id !== this.cgView) this.cgAutoStop("You left the table."); const out = r14.call(this); this.cgSpeedSync(); if (this.cgAuto) this.cgAutoBar(); return out; },
    closeDialogs() { const out = close14.call(this); const dlg = this.$("#dlg-casino"); if (!dlg || !dlg.classList.contains("on")) { if (this.cgAuto) this.cgAutoStop(); SP.setRate(1); } return out; },
    cgNav(box) { nav14.call(this, box); const v = this.cgView, nav = box.querySelector(".cgnav"), tools = nav && (nav.querySelector(".cghowtools") || nav.querySelector(".cgname")); if (!tools) return; const s = document.createElement("span"); s.className = "cgspeed";
      s.innerHTML = `${SP.FAST.includes(v) ? `<button class="cgfast${this.cgFastOn() ? " on" : ""}" data-fast title="Run this table's animations ${SP.rate} times faster">⏩ Fast</button>` : ""}${SP.AUTO.includes(v) ? `<button class="cgautob${this.cgAuto ? " on" : ""}" data-auto>${this.cgAuto ? `Stop auto (${this.cgAuto.done}/${this.cgAuto.n})` : "Auto ▾"}</button>` : ""}`; if (!s.innerHTML) return; tools.after(s);
      const f = s.querySelector("[data-fast]"); if (f) f.addEventListener("click", () => { const L = this.game.lbStore(); L.fast = !L.fast; this.game.saveCasino && this.game.saveCasino(); f.classList.toggle("on", L.fast); this.cgSpeedSync(); this.caSfx("cardplace", 0.3, L.fast ? 1.6 : 1); });
      const a = s.querySelector("[data-auto]"); if (a) a.addEventListener("click", (e) => { e.stopPropagation(); if (this.cgAuto) { this.cgAutoStop("Auto-play stopped."); return; } this.cgAutoMenu(a); }); },
    // ---- auto-play ----
    cgAutoMenu(anchor) { const old = document.querySelector(".cgautomenu"); if (old) { old.remove(); return; } const m = document.createElement("div"); m.className = "cgautomenu"; const big = this.cgAutoBig !== false;
      m.innerHTML = `<b>Play in a row</b><div class="row">${SP.RUNS.map((n) => `<button data-autorun="${n}">${n}</button>`).join("")}</div><label><input type="checkbox" data-autobig ${big ? "checked" : ""}> Stop on a big win (${SP.big}× the stake)</label><span class="small">Any key or click stops it.</span>`;
      const r = anchor.getBoundingClientRect(); m.style.left = `${Math.max(8, r.left)}px`; m.style.top = `${r.bottom + 6}px`; document.body.appendChild(m);
      m.querySelector("[data-autobig]").addEventListener("change", (e) => { this.cgAutoBig = e.target.checked; });
      m.querySelectorAll("[data-autorun]").forEach((b) => b.addEventListener("click", () => { m.remove(); this.cgAutoStart(Number(b.dataset.autorun)); }));
      setTimeout(() => { const off = (e) => { if (!m.contains(e.target)) { m.remove(); document.removeEventListener("mousedown", off, true); } }; document.addEventListener("mousedown", off, true); }, 0); },
    cgAutoButton() { const box = this.$("#casino-body"), skip = /^(leave|clear|cash out|get up|sell all|let it go)/i; return [...box.querySelectorAll("button.primary")].find((x) => !x.disabled && x.offsetParent && !x.closest(".cgnav") && !x.closest(".cgcats") && !skip.test(x.textContent.trim())) || null; },
    cgAutoStart(n) { const g = this.game, id = this.cgView; this.cgAuto = { id, n, done: 0, wait: false, stake: this.cgBet === undefined ? 5 : this.cgBet, start: g.gold };
      const stopper = (e) => { if (e.target && e.target.closest && (e.target.closest("[data-auto]") || e.target.closest(".cgautomenu"))) return; this.cgAutoStop("Auto-play stopped."); };
      this.cgAuto.stopper = stopper; setTimeout(() => { window.addEventListener("keydown", stopper, true); window.addEventListener("mousedown", stopper, true); }, 50);
      const step = () => { const A = this.cgAuto; if (!A || A !== this.cgAutoNow) return; if (this.cgBusy || (this.pkFly || []).length) { A.t = setTimeout(step, 120); return; }
        if (A.wait) { A.wait = false; A.done += 1; const net = g.gold - A.before; if (this.cgAutoBig !== false && net >= SP.big * Math.max(1, A.stake)) { this.cgAutoStop(`A big win - auto-play stopped after ${A.done}.`); return; } if (A.done >= A.n) { this.cgAutoStop("Auto-play done."); return; } this.cgAutoBar(); }
        if (g.gold < Math.max(1, A.stake)) { this.cgAutoStop("The purse is running short - auto-play stopped."); return; }
        const b = this.cgAutoButton(); if (!b) { this.cgAutoStop("Nothing to press - auto-play stopped."); return; } A.before = g.gold; A.wait = true; b.click(); A.t = setTimeout(step, 260); };
      this.cgAutoNow = this.cgAuto; this.cgAutoBar(); step(); },
    cgAutoStop(note) { const A = this.cgAuto; if (!A) return; clearTimeout(A.t); window.removeEventListener("keydown", A.stopper, true); window.removeEventListener("mousedown", A.stopper, true); this.cgAuto = null; this.cgAutoNow = null; if (note) { this.cgNote = `${note} (${A.done} played, ${g0(this.game.gold - A.start)} gold)`; } const b = this.$("#casino-body [data-auto]"); if (b) { b.textContent = "Auto ▾"; b.classList.remove("on"); } const n = this.$("#casino-body .cgnote"); if (n && note) n.textContent = this.cgNote; },
    cgAutoBar() { const A = this.cgAuto, b = this.$("#casino-body [data-auto]"); if (A && b) { b.textContent = `Stop auto (${A.done}/${A.n})`; b.classList.add("on"); } },
  });
  const g0 = (n) => `${n >= 0 ? "+" : "-"}${Math.abs(Math.round(n)).toLocaleString("en")}`;
}
