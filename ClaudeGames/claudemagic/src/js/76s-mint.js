"use strict";
// The Gilded Mint, the window's side (the twenty-seventh big update): the great coin press to strike (it thumps down,
// and dust puffs up with the count floating off it), the dust and the rate, the workshop list of those who mint for you
// (lit when you can afford the next), their upgrades and the hammers, the marks and what they paid, the lucky coin that
// glints across the counter now and then, and the melt. The rules are 64zc-mint.js.
CM.CG_TABLES.push(["mint", "The Gilded Mint"]);
{ const floor0 = CM.UI.prototype.renderFloor;
  Object.assign(CM.UI.prototype, {
    renderFloor(box) { if (this.cgView === "mint") return this.cgMint(box); return floor0.call(this, box); },
    cgMint(box) {
      const g = this.game, MN = CM.MN, M = g.mnLive(), f = MN.fmt;
      if (!this.mnOpened) { this.mnOpened = true; const away = g.mnAway(Date.now()); if (away > 1) this.cgNote = `While you were away the mint made ${f(away)} dust.`; }
      const marks = MN.MARKS.map((m, i) => `<span class="${M.marks > i ? "got" : ""}" title="${f(m)} dust minted in all: ${MN.gold(i)} gold and a ${i >= 9 ? "rare" : i >= 4 ? "stronger common" : "common"} card">${M.marks > i ? "✓" : "○"} ${f(m)}</span>`).join("");
      box.innerHTML = `<div class="cgtable mint"><h3>The Gilded Mint</h3><div class="mnwrap">
        <div class="mnleft"><div class="mndust"><b data-mn="dust">${f(M.dust)}</b> gold dust<small><span data-mn="rate">${f(M.rate())}</span> a second${M.t < M.luckyUntil ? " - <em>lucky!</em>" : ""}</small></div>
          <button class="mnpress" data-mnpress title="Strike the press"><span class="die"></span><span class="anvil"></span></button><div class="mnclick">A strike: <b data-mn="click">${f(M.perClick())}</b></div>
          <div class="mnseal">${M.seals ? `Gilded Seals: <b>${M.seals}</b> (+${Math.round(M.seals * MN.sealBonus * 100)}%)` : ""}${M.sealsIfMelted() ? `<button data-mnmelt title="Start again from nothing, for good seals">Melt the mint for ${M.sealsIfMelted()} seal${M.sealsIfMelted() > 1 ? "s" : ""}</button>` : `<small>At ${f(MN.sealAt)} dust this run, the mint can be melted down for Gilded Seals.</small>`}</div></div>
        <div class="mnshop"><div class="list-title">The workshop</div>${MN.KINDS.map((K, k) => `<button class="mnkind" data-mnbuy="${k}"><b>${K[1]}</b><small>${M.owned[k]} owned - ${f(K[3] * M.mult(k))} each a second</small><em>${f(MN.cost(k, M.owned[k]))}</em></button>`).join("")}
          <div class="list-title">Upgrades</div><div class="mnups">${M.hammerOpen() ? `<button data-mnhammer>A better hammer: strikes ×${MN.HAMMERS[M.hammer][1]} <em>${f(MN.HAMMERS[M.hammer][0])}</em></button>` : ""}${MN.KINDS.map((K, k) => (M.upOpen(k) ? `<button data-mnup="${k}">${K[1]}s ×2 <em>${f(MN.upCost(k, M.ups[k]))}</em></button>` : "")).join("")}</div></div></div>
        <div class="cgnote">${this.cgNote || ""}</div>${(this.mnWins || []).slice(-2).map((w) => this.cgCardWon(w.card)).join("")}
        <div class="list-title">The marks (dust minted in all, ${f(M.allTime)}) - gold and a card the first time each is passed</div><div class="mnmarks">${marks}</div>
        <div class="row"><button data-leave>Leave</button></div>
        <div class="small">Strike the press for dust; buy those who mint it for you. The mint keeps going while you are away (half as fast, up to eight hours). Catch the lucky coin when it glints. It costs nothing to play.</div></div>`;
      const q = (s) => box.querySelector(s); q("[data-leave]").addEventListener("click", () => { g.mnKeep(Date.now()); this.closeDialogs(); });
      const press = q("[data-mnpress]");
      press.addEventListener("mousedown", (e) => { const n = M.strike(); press.classList.remove("hit"); void press.offsetWidth; press.classList.add("hit"); this.cgSfx("bump", 0.25, 1.4 + Math.random() * 0.3); const fl = document.createElement("span"); fl.className = "mnfloat"; fl.textContent = `+${f(n)}`; const r = press.getBoundingClientRect(), pr = press.parentElement.getBoundingClientRect(); fl.style.left = `${e.clientX - pr.left}px`; fl.style.top = `${e.clientY - pr.top - 10}px`; press.parentElement.appendChild(fl); setTimeout(() => fl.remove(), 900); void r; });
      box.querySelectorAll("[data-mnbuy]").forEach((b) => b.addEventListener("click", () => { if (M.buy(Number(b.dataset.mnbuy))) { this.cgSfx("coin", 0.4, 0.9); this.renderCasino(); } else this.cgSfx("miss", 0.2); }));
      box.querySelectorAll("[data-mnup]").forEach((b) => b.addEventListener("click", () => { if (M.upgrade(Number(b.dataset.mnup))) { this.cgSfx("level", 0.4); this.renderCasino(); } }));
      if (q("[data-mnhammer]")) q("[data-mnhammer]").addEventListener("click", () => { if (M.buyHammer()) { this.cgSfx("grind", 0.5); this.renderCasino(); } });
      if (q("[data-mnmelt]")) q("[data-mnmelt]").addEventListener("click", () => { if (!this.mnAsk || performance.now() - this.mnAsk > 4000) { this.mnAsk = performance.now(); this.cgNote = "Melt the mint down? Everything goes but the seals (and the marks already passed). Click again."; this.renderCasino(); return; } const s = M.melt(); this.cgNote = `The mint is melted down: ${s} Gilded Seal${s > 1 ? "s" : ""}. Every dust from now on comes ${Math.round(M.seals * MN.sealBonus * 100)}% faster.`; this.cgSfx("victory", 0.5); g.mnKeep(Date.now()); this.renderCasino(); });
      this.mnBox = box;
      if (!this.mnLoop) { let prev = performance.now(), keepT = 0, reT = 0; const loop = (now) => { if (!this.mnBox || !this.mnBox.isConnected || this.cgView !== "mint") { this.mnLoop = null; this.mnOpened = false; g.mnKeep(Date.now()); return; } const dt = Math.min(1, (now - prev) / 1000); prev = now; this.mnFrame(dt); if ((keepT += dt) > 5) { keepT = 0; g.mnKeep(Date.now()); } if ((reT += dt) > 1) { reT = 0; this.mnRefresh(); } this.mnLoop = requestAnimationFrame(loop); }; this.mnLoop = requestAnimationFrame(loop); }
    },
    mnFrame(dt) {
      const g = this.game, M = g.mnLive(), f = CM.MN.fmt, b = this.mnBox, ev = M.update(dt, g.mnRnd);
      const set = (k, v) => { const e = b.querySelector(`[data-mn="${k}"]`); if (e) e.textContent = v; }; set("dust", f(M.dust)); set("rate", f(M.rate())); set("click", f(M.perClick()));
      if (ev === "lucky") { this.cgSfx("spell", 0.3, 1.6); const c = document.createElement("button"); c.className = "mnlucky"; c.title = "A lucky coin!"; c.style.left = `${M.lucky.x * 100}%`; c.style.top = `${M.lucky.y * 100}%`; b.querySelector(".mnwrap").appendChild(c);
        c.addEventListener("click", () => { const r = M.catchLucky(g.mnRnd); c.remove(); if (!r) return; this.cgSfx("victory", 0.5); this.cgNote = r.kind === "frenzy" ? "A lucky coin! Everything mints seven times over for half a minute." : `A lucky coin! ${f(r.n)} dust at once.`; this.renderCasino(); }); setTimeout(() => c.remove(), 12000); }
      const won = g.mnMarks(); if (won.length) { this.mnWins = (this.mnWins || []).concat(won); this.cgSfx("cardwin", 0.5); this.cgNote = won.map((w) => `${f(w.mark)} dust minted: ${w.gold} gold and a card - ${w.card}.`).join(" "); this.renderCasino(); this.cgCoins(this.$("#casino-body"), 12); }
    },
    // the buttons lit as they come within reach
    mnRefresh() { const M = this.game.mnLive(), MN = CM.MN, b = this.mnBox; b.querySelectorAll("[data-mnbuy]").forEach((e) => { const k = Number(e.dataset.mnbuy); e.classList.toggle("can", M.dust >= MN.cost(k, M.owned[k])); });
      b.querySelectorAll("[data-mnup]").forEach((e) => { const k = Number(e.dataset.mnup); e.classList.toggle("can", M.dust >= MN.upCost(k, M.ups[k])); }); const h = b.querySelector("[data-mnhammer]"); if (h) h.classList.toggle("can", M.hammerOpen() && M.dust >= MN.HAMMERS[M.hammer][0]);
      const newUp = MN.KINDS.some((K, k) => M.upOpen(k) && !b.querySelector(`[data-mnup="${k}"]`)) || (M.sealsIfMelted() && !b.querySelector("[data-mnmelt]")); if (newUp) this.renderCasino(); },
  });
}
