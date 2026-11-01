"use strict";
// The floor's big nights, the window's side: over the gallery a marquee of bulbs with the progressive jackpot in lit
// digits (and what it must go by, and who had it last), the day's happy hour posted beneath - lit and flashing while
// it's on, with a "2x tickets" ribbon on that game's card - and the jackpot's figure on every table's bar. Two more
// doors on the club strip: the Ticket Exchange (a brass-railed counter with the day's rates chalked up, arrows against
// yesterday, a little chart of the fortnight, and buying and selling) and the High-Roller (today's challenger drawn at
// the table with the wager in chips on the felt, what they want to play, and accept or let it go; then the result).
// The rules are 64zzk-floor2.js.
{ const r7 = CM.UI.prototype.renderCasino, gal7 = CM.UI.prototype.cgGallery, nav7 = CM.UI.prototype.cgNav, JP = CM.JP, HR = CM.HR, TX = CM.TX;
  const ticket = (n) => `<span class="tkcount"><i class="tkt"></i>${n}</span>`, money = (n) => Math.floor(n).toLocaleString("en");
  const nameOf = (id) => ((CM.CG_TABLES.find(([k]) => k === id) || [])[1]) || id;
  const hour = (h) => `${((h + 11) % 12) + 1} ${h < 12 ? "am" : "pm"}`;
  const portrait = (p, w, h, id, now) => { const P = CM.HE.RES[id], cx = w / 2, cy = h * 0.46, bob = Math.sin(now / 700) * 1.5;
    const bg = p.createRadialGradient(cx, cy, 10, cx, cy, w * 0.7); bg.addColorStop(0, "#5A1A24"); bg.addColorStop(1, "#1A0408"); p.fillStyle = bg; p.fillRect(0, 0, w, h);
    p.fillStyle = "rgba(255,220,140,0.12)"; p.beginPath(); p.ellipse(cx, 18, 70, 14, 0, 0, Math.PI * 2); p.fill();
    p.fillStyle = P.col; p.beginPath(); p.moveTo(cx - 56, h); p.quadraticCurveTo(cx - 52, cy + 34, cx, cy + 30); p.quadraticCurveTo(cx + 52, cy + 34, cx + 56, h); p.fill();
    p.fillStyle = "#E8C8A0"; p.fillRect(cx - 8, cy + 14 + bob, 16, 18); p.beginPath(); p.ellipse(cx, cy + bob, 26, 30, 0, 0, Math.PI * 2); p.fill();
    p.fillStyle = P.hair; p.beginPath(); p.ellipse(cx, cy - 18 + bob, 28, 16, 0, Math.PI, Math.PI * 2); p.fill(); p.fillRect(cx - 28, cy - 18 + bob, 6, 18); p.fillRect(cx + 22, cy - 18 + bob, 6, 18);
    const blink = (now % 4200) < 140; p.fillStyle = "#1A1010"; for (const s of [-1, 1]) { if (blink) p.fillRect(cx + s * 10 - 4, cy - 2 + bob, 8, 1.5); else { p.beginPath(); p.arc(cx + s * 10, cy - 2 + bob, 2.6, 0, Math.PI * 2); p.fill(); } }
    p.strokeStyle = "#7A3A2A"; p.lineWidth = 2; p.beginPath(); p.arc(cx, cy + 10 + bob, 8, 0.2, Math.PI - 0.2); p.stroke(); p.lineWidth = 1;
    // the table's edge and the wager in chips on the felt
    p.fillStyle = "#1E5A32"; p.fillRect(0, h - 34, w, 34); p.fillStyle = "#3A2214"; p.fillRect(0, h - 38, w, 6);
    for (let s = 0; s < 4; s++) for (let k = 0; k < 6 - s; k++) { const x = 30 + s * 26, y = h - 14 - k * 4; p.fillStyle = ["#C02830", "#2A50C0", "#1A1A1A", "#F0C040"][s]; p.beginPath(); p.ellipse(x, y, 11, 4, 0, 0, Math.PI * 2); p.fill(); p.strokeStyle = "rgba(255,255,255,0.6)"; p.setLineDash([2, 3]); p.stroke(); p.setLineDash([]); } };
  Object.assign(CM.UI.prototype, {
    renderCasino() { const v = this.cgView, box = this.$("#casino-body");
      const J = this.game.jpJust; if (J && !this.cgBusy) { this.game.jpJust = null; this.cgNote = `${this.cgNote ? `${this.cgNote} ` : ""}And the bulbs go wild - the progressive jackpot, ${money(J.gold)} gold!`; }
      if (v === "exchange" || v === "highroller") { if (v === "exchange") this.cgExchange(box); else this.cgHighRoller(box); this.cgToasts && this.cgToasts(); this.cgFwFlush(); return; } return r7.call(this); },
    cgGallery(box) {
      gal7.call(this, box); const g = this.game, pot = g.jpPot(), J = g.jpStore(), H = g.hhToday(), live = g.hhOn(), C = g.hrToday(), head = box.querySelector(".cghead"); if (!head) return;
      const bar = document.createElement("div"); bar.className = "jpbar";
      bar.innerHTML = `<div class="jpmarq"><span class="jplabel">PROGRESSIVE JACKPOT</span><span class="jpdigits">${money(pot).split("").map((d) => `<i>${d}</i>`).join("")}</span><span class="jpsub">gold · must go by ${money(JP.must)}${J.wins[0] ? ` · last won: ${money(J.wins[0].gold)} at ${nameOf(J.wins[0].game)}` : ""}</span></div>
        <button class="hhline${live ? " live" : ""}" data-hhgo="${H.table}">${live ? `<b>HAPPY HOUR NOW</b> at ${nameOf(H.table)} - double tickets until ${hour((H.hour + 1) % 24)}!` : `Happy hour today: <b>${nameOf(H.table)}</b>, ${hour(H.hour)} to ${hour((H.hour + 1) % 24)} - double tickets`}</button>`;
      head.after(bar); bar.querySelector("[data-hhgo]").addEventListener("click", () => { this.cgView = H.table; this.cgNote = ""; this.caSfx("cardplace", 0.3); this.renderCasino(); });
      const card = box.querySelector(`[data-cgopen="${H.table}"]`); if (card) { card.classList.add("hhcard"); if (live) card.classList.add("live"); card.insertAdjacentHTML("beforeend", `<i class="hhbadge">${live ? "2× tickets now" : `happy hour ${hour(H.hour)}`}</i>`); }
      const strip = box.querySelector(".cgclub"); if (!strip) return; const add = (view, html, cls) => { const b = document.createElement("button"); b.className = cls; b.innerHTML = html; strip.appendChild(b); b.addEventListener("click", () => { this.cgView = view; this.caSfx("cardplace", 0.3); this.renderCasino(); }); };
      add("exchange", "Ticket exchange", "flbtn"); add("highroller", `High-roller${C.state === "offered" ? ` <b class="flready">!</b>` : C.state === "on" ? " ✦" : ""}`, "flbtn hrbtn");
    },
    cgNav(box) { nav7.call(this, box); const nav = box.querySelector(".cgnav"), gold = nav && nav.querySelector(".cggold"); if (!gold) return; const s = document.createElement("span"); s.className = "jptick"; s.innerHTML = `Jackpot <b>${money(this.game.jpPot())}</b>`; gold.before(s); },
    // ---- the ticket exchange ----
    cgExchange(box) {
      const g = this.game, T = g.tkStore(), X = g.txStore(), r = g.txRates(), hist = TX.history(g.seed, X.day), y = hist[hist.length - 2], arrow = (a, b) => (a > b ? `<i class="up">▲</i>` : a < b ? `<i class="down">▼</i>` : `<i>■</i>`), n = this.txN = this.txN || 100;
      box.innerHTML = `<div class="txroom"><p class="lore">By the cashier's cage a little brass-railed counter, with a clerk in sleeve-garters chalking the day's rates on a slate. "Tickets for gold, gold for tickets. The rates move with the floor, sir, madam - today's are today's."</p>
        <div class="txtop"><div class="txslate"><div><span>We buy tickets at</span><b>${r.sell.toFixed(3)}</b><span>gold each ${arrow(r.sell, y.sell)}</span></div><div><span>We sell tickets at</span><b>${r.buy.toFixed(3)}</b><span>gold each ${arrow(r.buy, y.buy)}</span></div></div>
        <div class="txchart"><canvas width="380" height="170" data-txchart></canvas><div class="txlegend"><span><i style="background:#F0A030"></i>We buy (what you get)</span><span><i style="background:#60A8F0"></i>We sell (what you pay)</span></div></div></div>
        <div class="txdesk"><div class="txamt">Tickets: ${[50, 100, 250, 500, 1000].map((k) => `<button data-txn="${k}" class="${k === n ? "primary" : ""}">${k}</button>`).join("")}</div>
        <div class="row"><button class="primary" data-txsell ${T.n >= n ? "" : "disabled"}>Sell ${n} tickets for ${Math.floor(n * r.sell)} gold</button><button class="primary" data-txbuy ${g.gold >= Math.ceil(n * r.buy) ? "" : "disabled"}>Buy ${n} tickets for ${Math.ceil(n * r.buy)} gold</button>${T.n ? `<button data-txall>Sell all ${T.n}</button>` : ""}</div>
        <div class="cgnote">${this.cgNote || ""}</div>
        <div class="small">You hold ${ticket(T.n)} and ${g.gold} gold. Today the exchange will buy ${TX.sellMax - X.sold} more tickets and sell ${TX.buyMax - X.bought} more. Buying always costs more than selling pays. Bought here, tickets don't count towards the prize counter's growth.</div></div></div>`;
      this.cgClubHead(box, "Ticket exchange"); const q = (s) => box.querySelector(s);
      box.querySelectorAll("[data-txn]").forEach((b) => b.addEventListener("click", () => { this.txN = Number(b.dataset.txn); this.cgSfx("card", 0.25); this.renderCasino(); }));
      const deal = (o, verb) => { if (o.error) { this.cgNote = o.error; this.cgSfx("miss", 0.3); } else { this.cgNote = `${verb} ${o.tickets} tickets for ${o.gold} gold.`; this.cgSfx("coin", 0.5); this.cgCoins(this.$("#casino-body"), Math.min(16, 2 + o.gold / 10)); } this.renderCasino(); };
      q("[data-txsell]").addEventListener("click", () => deal(g.txSell(n), "Sold")); q("[data-txbuy]").addEventListener("click", () => deal(g.txBuy(n), "Bought")); if (q("[data-txall]")) q("[data-txall]").addEventListener("click", () => deal(g.txSell(Math.min(T.n, TX.sellMax - X.sold)), "Sold"));
      // the fortnight's rates on one scale, today's points ringed, the last value labelled
      const c = q("[data-txchart]"), p = c.getContext("2d"), L = 40, R = 52, Tp = 12, B = 22, w = c.width - L - R, h = c.height - Tp - B, top = 0.55, X2 = (i) => L + (i / (hist.length - 1)) * w, Y = (v) => Tp + h - (v / top) * h;
      p.fillStyle = "#1A1410"; p.fillRect(0, 0, c.width, c.height); p.strokeStyle = "rgba(255,255,255,0.08)"; p.fillStyle = "rgba(240,230,210,0.6)"; p.font = "10px Georgia";
      for (const v of [0, 0.1, 0.2, 0.3, 0.4, 0.5]) { p.beginPath(); p.moveTo(L, Y(v)); p.lineTo(L + w, Y(v)); p.stroke(); p.fillText(v.toFixed(1), 8, Y(v) + 3); }
      p.fillText("14 days ago", L, c.height - 6); p.textAlign = "right"; p.fillText("today", L + w, c.height - 6); p.textAlign = "left";
      for (const [k, col] of [["sell", "#F0A030"], ["buy", "#60A8F0"]]) { p.strokeStyle = col; p.lineWidth = 2; p.beginPath(); hist.forEach((d, i) => (i ? p.lineTo(X2(i), Y(d[k])) : p.moveTo(X2(i), Y(d[k])))); p.stroke(); p.lineWidth = 1;
        const last = hist[hist.length - 1][k]; p.fillStyle = "#1A1410"; p.beginPath(); p.arc(X2(hist.length - 1), Y(last), 5, 0, Math.PI * 2); p.fill(); p.fillStyle = col; p.beginPath(); p.arc(X2(hist.length - 1), Y(last), 3.5, 0, Math.PI * 2); p.fill(); p.fillStyle = "#F0E8D8"; p.fillText(last.toFixed(3), L + w + 8, Y(last) + 3); }
    },
    // ---- the high-roller ----
    cgHighRoller(box) {
      const g = this.game, C = g.hrToday(), P = CM.HE.RES[C.who], S = g.hrStore(), Rz = C.result, game = C.kind === "holdem" ? "the Residents' Game" : nameOf(C.kind);
      const ask = C.kind === "holdem" ? `"Heads up, you and me, ${C.wager} gold each. Last one with chips takes the lot."` : `"I put ${C.target} on the board at ${game} last night. Beat it in one game and my ${C.wager} is yours with your own. Fall short and I keep yours."`;
      const state = C.state === "offered" ? `<div class="row"><button class="primary" data-hrok>Take the wager (${C.wager} gold)</button><button data-hrno>Let it go</button></div>`
        : C.state === "on" ? `<div class="row"><button class="primary" data-hrgo>${C.kind === "holdem" ? "Take your seat" : `Go to ${game}`}</button></div><div class="small">${C.kind === "holdem" ? "Win every chip, then cash out to collect. Walk away early and the wager's lost." : `Play one game of ${game}; the next one you finish is the one that counts. Your score must beat ${C.target}.`}</div>`
        : C.state === "declined" ? `<p class="small">You let the wager go. ${P.short} shrugs and orders a drink. There'll be someone else tomorrow.</p>`
        : `<div class="hrresult ${Rz && Rz.win ? "won" : "lost"}">${Rz && Rz.win ? `<b>You beat ${P.name}!</b> ${Rz.detail}.${Rz.gold ? ` ${Rz.gold} gold,` : ""} ${Rz.tickets} tickets.` : `<b>${P.short} takes the wager.</b> ${Rz ? Rz.detail : ""}. "${P.say.win.replace(/"/g, "")}"`}</div>${Rz && Rz.card ? this.cgCardWon(Rz.card) : ""}`;
      box.innerHTML = `<div class="hrroom"><div class="hrtop"><canvas width="240" height="220" data-hrart></canvas><div class="hrside"><p class="lore">A table is cleared by the fire and a velvet cloth thrown over it. ${P.name[0].toUpperCase() + P.name.slice(1)} is waiting with a stack of chips and a look you've seen across the poker table.</p>
        <div class="hrbubble">${ask}</div><div class="hrwager"><span>The wager</span><b>${money(C.wager)}</b><span>gold - win and it pays double, with ${HR.tickets + Math.floor(C.wager / 20)} tickets${S.beaten[C.who] ? "" : " and a card the first time you beat them"}</span></div>
        ${state}<div class="cgnote">${this.cgNote || ""}</div></div></div>
        <h4>The residents you've beaten</h4><div class="hrbeaten">${Object.entries(CM.HE.RES).map(([id, R]) => `<span class="${S.beaten[id] ? "on" : ""}">${S.beaten[id] ? "✓" : "·"} ${R.short}</span>`).join("")}</div>
        <div class="small">A new challenger comes each real day. Challenges won ${S.won}, lost ${S.lost}.</div></div>`;
      this.cgClubHead(box, "The High-Roller"); const q = (s) => box.querySelector(s), cv = q("[data-hrart]");
      if (q("[data-hrok]")) q("[data-hrok]").addEventListener("click", () => { const r = g.hrAccept(); this.cgNote = r.error || `${P.short} smiles and pushes the chips in. "Good."`; this.cgSfx(r.error ? "miss" : "coin", 0.5); this.renderCasino(); });
      if (q("[data-hrno]")) q("[data-hrno]").addEventListener("click", () => { g.hrDecline(); this.cgNote = ""; this.cgSfx("card", 0.3); this.renderCasino(); });
      if (q("[data-hrgo]")) q("[data-hrgo]").addEventListener("click", () => { this.cgView = C.kind; this.cgNote = C.kind === "holdem" ? `Heads up against ${P.name} - ${C.wager} gold a side.` : `The high-roller's challenge: beat ${C.target}.`; this.caSfx("cardplace", 0.3); this.renderCasino(); });
      const draw = (now) => { if (!cv.isConnected) return; portrait(cv.getContext("2d"), cv.width, cv.height, C.who, now); requestAnimationFrame(draw); }; requestAnimationFrame(draw);
    },
  });
}
