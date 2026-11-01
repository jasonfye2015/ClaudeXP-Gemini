"use strict";
// The Gilded Joker's floor, the window's side (the twentieth big update): a row of tables across the top of the
// casino's dialog - Claudeatro (76e-casino.js) and four of the floor's own games (64s-casinogames.js) - each drawn
// and moved: the reels spin and stop one by one, the wheel turns against its ball, the cards are dealt across the
// felt and the hole card turns over, held cards stay while the rest flip; chips clink, coins fall, and a jackpot rings.
CM.CG_TABLES = [["claudeatro", "Claudeatro"], ["slots", "The Gilded Reels"], ["roulette", "Roulette"], ["blackjack", "Blackjack"], ["poker", "Jacks or Better"]];
{ const r0 = CM.UI.prototype.renderCasino, open0 = CM.UI.prototype.openCasino;
  Object.assign(CM.UI.prototype, {
    openCasino() { this.cgView = this.cgView || "claudeatro"; open0.call(this); },
    renderCasino() {
      const box = this.$("#casino-body");
      if (this.cgView && this.cgView !== "claudeatro") this.renderFloor(box); else r0.call(this);
      this.cgNav(box);
    },
    cgNav(box) {
      const nav = document.createElement("div"); nav.className = "cgnav";
      nav.innerHTML = CM.CG_TABLES.map(([id, name]) => `<button data-cgv="${id}" class="${(this.cgView || "claudeatro") === id ? "primary" : ""}">${name}</button>`).join("") + `<span class="cggold">${this.game.gold} gold</span>`;
      box.prepend(nav);
      nav.querySelectorAll("[data-cgv]").forEach((b) => b.addEventListener("click", () => { if (this.cgBusy) return; this.cgView = b.dataset.cgv; this.cgNote = ""; this.caSfx("cardplace", 0.3); this.renderCasino(); }));
    },
    cgSfx(name, vol = 0.4, rate = 1) { try { CM.audio.play(name, vol, 0, rate); } catch (e) { /* quiet */ } },
    // the bet: chips added up, cleared, within the purse and the house's limit
    cgBetRow(label = "The bet") {
      const b = this.cgBet === undefined ? 5 : this.cgBet;
      return `<div class="cgbet"><span class="lbl">${label}: <b>${b}</b> gold</span>${CM.CG.chips.map((c) => `<button class="chip c${c}" data-chip="${c}" ${c > this.game.gold ? "disabled" : ""}>${c}</button>`).join("")}<button data-chipclear>Clear</button></div>`;
    },
    cgWireBet(box) {
      box.querySelectorAll("[data-chip]").forEach((el) => el.addEventListener("click", () => { if (this.cgBusy) return; this.cgBet = Math.min(CM.CG.max, this.game.gold, (this.cgBet === undefined ? 0 : this.cgBet) + Number(el.dataset.chip)); this.cgSfx("coin", 0.18, 1.4); this.renderCasino(); }));
      const c = box.querySelector("[data-chipclear]"); if (c) c.addEventListener("click", () => { if (this.cgBusy) return; this.cgBet = 0; this.renderCasino(); });
    },
    cgStats(game) { const F = this.game.cgStore(), w = F.wagered[game] || 0, p = F.paid[game] || 0; return `<div class="small cgstats">Played ${F.played[game] || 0}; wagered ${w} gold, paid back ${p}${w ? ` (${Math.round((100 * p) / w)}%)` : ""}.${F.cards.length ? ` Cards won on the floor: ${F.cards.length}.` : ""}</div>`; },
    // coins tumbling down the felt for a win; a ring of light and the card for a jackpot
    cgCoins(box, n) { const host = box.querySelector(".cgtable") || box; for (let i = 0; i < Math.min(40, n); i++) { const c = document.createElement("span"); c.className = "cgcoin"; c.style.left = `${10 + Math.random() * 80}%`; c.style.animationDelay = `${Math.random() * 0.5}s`; host.appendChild(c); setTimeout(() => c.remove(), 1800); } },
    cgCardWon(name) { if (!name || !CM.CARDS[name]) return ""; const C = CM.CARDS[name]; return `<div class="cgprize"><span class="em">${C[0]}</span><div><b>${this.esc(name)}</b><small>A Claudescryption card - off to the box in Leshy's cabin</small></div></div>`; },
    renderFloor(box) {
      const v = this.cgView; if (v === "slots") this.cgSlots(box); else if (v === "roulette") this.cgRoulette(box); else if (v === "blackjack") this.cgBlackjack(box); else this.cgPoker(box);
    },
    // ---- the Gilded Reels ----
    cgSlots(box) {
      const CG = CM.CG, P = CG.SLOT_PAY, A = CG.SLOT_ART, last = this.cgSlotLast, stops = last ? last.stops : [0, 9, 17], N = CG.REEL.length;
      const art = (s) => (s === "joker" ? `<span class="jokr">J<i>★</i></span>` : A[s]), strip = [].concat(...Array(6).fill(CG.REEL)).map((s) => `<div class="sym s-${s}">${art(s)}</div>`).join("");
      const row = (k, txt) => `<tr><td>${txt}</td><td>${P[k]} x</td></tr>`;
      box.innerHTML = `<div class="cgtable slots"><h3>The Gilded Reels</h3><p class="lore">A tall brass machine with a gilded Joker on its crown, humming faintly. "One line, three reels," says the attendant. "Fair as a coin."</p>
        <div class="slotwrap"><div class="slotcab"><div class="marquee"><span>THE GILDED REELS</span></div><div class="bulbs">${Array.from({ length: 18 }, (_, k) => `<i style="--k:${k}"></i>`).join("")}</div><div class="reels">${[0, 1, 2].map((i) => `<div class="reel"><div class="strip" data-reel="${i}" style="transform: translateY(${-(N + stops[i] - 1) * 64}px)">${strip}</div></div>`).join("")}<div class="payline"></div></div><div class="lever"><div class="arm"><i></i></div></div></div>
        <table class="paytable">${row("joker", `${art("joker")}${art("joker")}${art("joker")} + a rare card`)}${row("seven", "7 7 7")}${row("bar", "▬ ▬ ▬")}${row("cherry", "🍒🍒🍒")}${row("bell", "🔔🔔🔔")}${row("lemon", "🍋🍋🍋")}${row("mix", "any three of ▬ 🔔 7")}${row("twoCherry", "any two 🍒")}${row("oneCherry", "🍒 on the first reel")}<tr><td colspan="2" class="small">The machine returns 97.1% of what is put in it.</td></tr></table></div>
        ${this.cgBetRow()}<div class="cgnote">${this.cgNote || ""}</div>${last && last.card ? this.cgCardWon(last.card) : ""}
        <div class="row"><button class="primary" data-spin>Pull the lever</button><button data-leave>Leave</button></div>${this.cgStats("slots")}</div>`;
      this.cgWireBet(box); box.querySelector("[data-leave]").addEventListener("click", () => this.closeDialogs());
      box.querySelector("[data-spin]").addEventListener("click", () => {
        if (this.cgBusy) return; const r = this.game.slotSpin(this.cgBet === undefined ? 5 : this.cgBet); if (r.error) { this.cgNote = r.error; this.cgSfx("miss", 0.3); this.renderCasino(); return; }
        this.cgBusy = true; this.cgSfx("hinge", 0.5); const strips = [...box.querySelectorAll("[data-reel]")]; let ticks = 0; box.querySelector(".lever").classList.add("pull"); box.querySelector(".reels").classList.add("spinning"); box.querySelector(".slotcab").classList.add("busy");
        const tick = setInterval(() => { this.cgSfx("card", 0.1, 1.6 + Math.random() * 0.4); if (++ticks > 40) clearInterval(tick); }, 60);
        strips.forEach((el, i) => {
          const from = -(N + stops[i] - 1) * 64, to = -((2 + i) * N + r.stops[i] - 1) * 64;   // (round two to four times, on to the stop; the strip repeats, so the rest is the same picture)
          el.animate([{ transform: `translateY(${from}px)` }, { transform: `translateY(${to}px)` }], { duration: 1000 + i * 500, easing: "cubic-bezier(.15,.55,.25,1)" }).onfinish = () => {
            el.style.transform = `translateY(${-(N + r.stops[i] - 1) * 64}px)`; el.classList.add("stopped"); this.cgSfx("cardplace", 0.45, 0.8);
            if (i === 2) { clearInterval(tick); this.cgBusy = false; this.cgSlotLast = r; this.cgNote = r.won ? `${r.what}: ${r.won} gold!` : "Nothing on the line."; this.renderCasino(); const b2 = this.$("#casino-body"); if (!b2.querySelector(".slotwrap")) return;   // (the party went elsewhere while the reels turned)
              if (r.jackpot) { this.cgSfx("victory", 0.7); this.cgSfx("cardwin", 0.6); b2.querySelector(".slotwrap").classList.add("jackpot"); this.cgCoins(b2, 40); }
              else if (r.won >= (this.cgBet || 5) * 9) { this.cgSfx("victory", 0.45); this.cgCoins(b2, 18); }
              else if (r.won) { this.cgSfx("coin", 0.5); this.cgCoins(b2, 5); }
              if (r.won) { b2.querySelector(".slotwrap").classList.add("win"); b2.querySelectorAll("[data-reel]").forEach((el2, j) => { const sym = el2.children[N + r.stops[j]]; if (sym && (!/cherr/i.test(r.what) || CG.REEL[r.stops[j]] === "cherry")) sym.classList.add("hit"); }); } }
          };
        });
      });
    },
    // ---- Roulette ----
    cgRoulette(box) {
      const CG = CM.CG, bets = this.cgRBets = this.cgRBets || {}, last = this.cgRLast, staked = Object.values(bets).reduce((t, b) => t + b.amount, 0);
      const key = (type, n) => `${type}:${n || 0}`, chipOn = (type, n) => { const b = bets[key(type, n)]; return b ? `<i class="bchip">${b.amount}</i>` : ""; };
      const cell = (n) => `<div class="rc ${n === 0 ? "g" : CG.RED.has(n) ? "r" : "b"}${last && last.n === n ? " hit" : ""}" data-rb="straight:${n}">${n}${chipOn("straight", n)}</div>`;
      let grid = ""; for (let row = 3; row >= 1; row--) { for (let col = 0; col < 12; col++) grid += cell(col * 3 + row); grid += `<div class="rc o" data-rb="column:${row}">2:1${chipOn("column", row)}</div>`; }
      const out = [["dozen:1", "1st 12"], ["dozen:2", "2nd 12"], ["dozen:3", "3rd 12"]].map(([k, t]) => `<div class="rc o w4" data-rb="${k}">${t}${chipOn(...k.split(":").map((x, i) => (i ? Number(x) : x)))}</div>`).join("")
        + [["low", "1-18"], ["even", "Even"], ["red", "Red"], ["black", "Black"], ["odd", "Odd"], ["high", "19-36"]].map(([k, t]) => `<div class="rc o w2 ${k === "red" ? "r" : k === "black" ? "b" : ""}" data-rb="${k}:0">${t}${chipOn(k, 0)}</div>`).join("");
      box.innerHTML = `<div class="cgtable roulette"><h3>Roulette</h3><p class="lore">A wheel of polished walnut with a single green zero. The croupier spins it with two fingers. "Place your bets."</p>
        <div class="rwrap"><canvas class="rwheel" width="300" height="300"></canvas><div class="rboard"><div class="rzero">${cell(0)}</div><div class="rgrid">${grid}</div><div class="routs">${out}</div></div></div>
        ${this.cgBetRow("The chip")}<div class="cgnote">${this.cgNote || ""}${last ? ` <span class="rlast ${last.colour}">${last.n}</span>` : ""}</div>${last && last.card ? this.cgCardWon(last.card) : ""}
        <div class="row"><button class="primary" data-rspin ${staked ? "" : "disabled"}>Spin (${staked} gold on the board)</button><button data-rclear>Clear the board</button><button data-leave>Leave</button></div>
        <div class="small">A number pays 35 to 1, a dozen or a column 2 to 1, red, black, odd, even, 1-18 and 19-36 even money; the zero takes the outside bets. The wheel returns 97.3%; a straight bet of five or more that wins on the zero brings a Claudescryption card besides.</div>${this.cgStats("roulette")}</div>`;
      this.cgWireBet(box); box.querySelector("[data-leave]").addEventListener("click", () => this.closeDialogs());
      this.cgDrawWheel(box.querySelector(".rwheel"), this.cgWheelA || 0, this.cgBallA === undefined ? null : this.cgBallA);
      box.querySelectorAll("[data-rb]").forEach((el) => el.addEventListener("click", () => {
        if (this.cgBusy) return; const [type, n] = el.dataset.rb.split(":"), k = key(type, Number(n)), chip = this.cgBet || 0, total = staked + chip;
        if (!chip) { this.cgNote = "Choose a chip first."; this.renderCasino(); return; } if (total > this.game.gold || total > CG.max * 4) { this.cgNote = "That is more than the party has, or the house takes."; this.renderCasino(); return; }
        bets[k] = { type, n: Number(n), amount: (bets[k] ? bets[k].amount : 0) + chip }; this.cgSfx("coin", 0.22, 1.3); this.cgNote = ""; this.renderCasino();
      }));
      box.querySelector("[data-rclear]").addEventListener("click", () => { if (this.cgBusy) return; this.cgRBets = {}; this.renderCasino(); });
      box.querySelector("[data-rspin]").addEventListener("click", () => {
        if (this.cgBusy) return; const r = this.game.rouletteSpin(Object.values(bets)); if (r.error) { this.cgNote = r.error; this.renderCasino(); return; }
        this.cgBusy = true; const cv = box.querySelector(".rwheel"), a0 = this.cgWheelA || 0, idx = CG.WHEEL.indexOf(r.n), slot = (Math.PI * 2) / 37, t0 = performance.now(), dur = 4800;
        const wheelEnd = a0 + Math.PI * 2 * 3 + 0.7, pocketA = wheelEnd + idx * slot + slot / 2, ball0 = -Math.PI / 2, ballEnd = pocketA - Math.PI * 2 * (Math.ceil((pocketA - ball0) / (Math.PI * 2)) + 5); let lastPocket = -1;
        this.cgSfx("hinge", 0.4, 1.4);
        const step = (now) => {
          const k = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - k, 3), wa = a0 + (wheelEnd - a0) * e, ba = ball0 + (ballEnd - ball0) * e;
          const rad = 118 - Math.min(1, Math.max(0, (k - 0.55) / 0.4)) * 16;   
          this.cgDrawWheel(cv, wa, ba, rad); const pocket = Math.floor((((ba - wa) % (Math.PI * 2)) + Math.PI * 4) % (Math.PI * 2) / slot); if (pocket !== lastPocket && k > 0.15) { lastPocket = pocket; this.cgSfx("card", 0.06 + 0.1 * k, 2.2 - k); }
          this.cgBallTrail = (this.cgBallTrail || []).concat([[ba, rad]]).slice(-7); if (k < 1) { requestAnimationFrame(step); return; } this.cgBallTrail = [];
          this.cgWheelA = wa % (Math.PI * 2); this.cgBallA = this.cgWheelA + idx * slot + slot / 2; this.cgBallR = rad; this.cgBusy = false; this.cgRLast = r; this.cgSfx("cardplace", 0.6, 0.7);
          this.cgNote = `${r.n} ${r.colour}. ${r.back ? `The board pays ${r.back} gold.` : "The house takes the board."}`; if (!r.back) this.cgRBets = {};
          this.renderCasino(); const b2 = this.$("#casino-body"); if (r.back) { this.cgSfx(r.back >= r.staked * 5 ? "victory" : "coin", 0.55); this.cgCoins(b2, Math.min(30, 4 + Math.round(r.back / Math.max(1, r.staked)) * 2)); } if (r.card) this.cgSfx("cardwin", 0.6);
        };
        requestAnimationFrame(step);
      });
    },
    cgDrawWheel(cv, wa, ba, rad) {
      if (!cv) return; const p = cv.getContext("2d"), CG = CM.CG, c = 150, slot = (Math.PI * 2) / 37; p.clearRect(0, 0, 300, 300);
      p.fillStyle = "#4A2A14"; p.beginPath(); p.arc(c, c, 146, 0, Math.PI * 2); p.fill(); p.fillStyle = "#C8A040"; p.beginPath(); p.arc(c, c, 138, 0, Math.PI * 2); p.fill();
      CG.WHEEL.forEach((n, i) => { const a = wa + i * slot; p.fillStyle = n === 0 ? "#1E8A3A" : CG.RED.has(n) ? "#B02020" : "#1A1A1A"; p.beginPath(); p.moveTo(c, c); p.arc(c, c, 132, a, a + slot); p.closePath(); p.fill();
        p.save(); p.translate(c, c); p.rotate(a + slot / 2 + Math.PI / 2); p.fillStyle = "#F0E8D0"; p.font = "bold 10px Georgia, serif"; p.textAlign = "center"; p.fillText(String(n), 0, -118); p.restore(); });
      p.strokeStyle = "rgba(240,220,160,0.55)"; p.lineWidth = 1; CG.WHEEL.forEach((n, i) => { const a = wa + i * slot; p.beginPath(); p.moveTo(c + Math.cos(a) * 94, c + Math.sin(a) * 94); p.lineTo(c + Math.cos(a) * 132, c + Math.sin(a) * 132); p.stroke(); });
      const sh = p.createRadialGradient(c - 30, c - 40, 20, c, c, 146); sh.addColorStop(0, "rgba(255,255,255,0.12)"); sh.addColorStop(0.7, "rgba(0,0,0,0)"); sh.addColorStop(1, "rgba(0,0,0,0.35)"); p.fillStyle = sh; p.beginPath(); p.arc(c, c, 146, 0, Math.PI * 2); p.fill();
      p.fillStyle = "#3A2210"; p.beginPath(); p.arc(c, c, 92, 0, Math.PI * 2); p.fill(); p.strokeStyle = "#C8A040"; p.lineWidth = 3; p.beginPath(); p.arc(c, c, 92, 0, Math.PI * 2); p.stroke();
      const cone = p.createRadialGradient(c - 10, c - 14, 4, c, c, 92); cone.addColorStop(0, "#7A5028"); cone.addColorStop(1, "#2A1808"); p.fillStyle = cone; p.beginPath(); p.arc(c, c, 89, 0, Math.PI * 2); p.fill();
      p.fillStyle = "#F0D070"; for (let k = 0; k < 8; k++) { const a = (k * Math.PI) / 4 + Math.PI / 8; p.save(); p.translate(c + Math.cos(a) * 141, c + Math.sin(a) * 141); p.rotate(a); p.beginPath(); p.moveTo(-5, 0); p.lineTo(0, -2.5); p.lineTo(5, 0); p.lineTo(0, 2.5); p.closePath(); p.fill(); p.restore(); }
      p.save(); p.translate(c, c); p.rotate(wa); p.fillStyle = "#E0C060"; for (let k = 0; k < 4; k++) { p.rotate(Math.PI / 2); p.fillRect(-4, -60, 8, 56); } p.beginPath(); p.arc(0, 0, 14, 0, Math.PI * 2); p.fill(); p.restore();
      (this.cgBallTrail || []).forEach(([ta, tr], k, arr) => { p.fillStyle = `rgba(255,255,255,${(0.25 * (k + 1)) / arr.length})`; p.beginPath(); p.arc(c + Math.cos(ta) * tr, c + Math.sin(ta) * tr, 5, 0, Math.PI * 2); p.fill(); });
      if (ba !== null && ba !== undefined) { const r = rad || this.cgBallR || 106; p.fillStyle = "rgba(0,0,0,0.35)"; p.beginPath(); p.arc(c + Math.cos(ba) * r + 2, c + Math.sin(ba) * r + 3, 6, 0, Math.PI * 2); p.fill(); const bgr = p.createRadialGradient(c + Math.cos(ba) * r - 2, c + Math.sin(ba) * r - 2, 1, c + Math.cos(ba) * r, c + Math.sin(ba) * r, 6); bgr.addColorStop(0, "#FFFFFF"); bgr.addColorStop(1, "#B8B8C0"); p.fillStyle = bgr; p.beginPath(); p.arc(c + Math.cos(ba) * r, c + Math.sin(ba) * r, 6, 0, Math.PI * 2); p.fill(); p.strokeStyle = "rgba(0,0,0,0.35)"; p.lineWidth = 1; p.stroke(); }
    },
    // ---- Blackjack ----
    cgBlackjack(box) {
      const g = this.game, B = g.bjState(), CG = CM.CG, play = B && B.stage === "play", seen = this.cgSeen = this.cgSeen || new Set();
      const card = (c) => { const fresh = !seen.has(`${c.id}:${c.down ? 1 : 0}`); seen.add(`${c.id}:${c.down ? 1 : 0}`); return c.down ? `<div class="pc cgback${fresh ? " deal" : ""}"></div>` : this.caCard(c, { cls: fresh ? (seen.has(`${c.id}:1`) ? "flip" : "deal") : "" }); };
      const dv = B ? CG.bjValue(B.dealer).total : 0;
      const hands = B ? B.hands.map((H, i) => { const v = CG.bjValue(H.cards), res = B.results ? B.results[i] : null; return `<div class="bjhand${play && B.active === i ? " now" : ""}"><div class="cards">${H.cards.map(card).join("")}</div><div class="bjv">${v.total}${v.soft && v.total < 21 ? " (soft)" : ""} - ${H.bet} gold${H.doubled ? " (doubled)" : ""}${res ? ` <b class="res ${res.r}">${{ blackjack: "Blackjack!", win: "Win", push: "Push", lose: "Lose", bust: "Bust" }[res.r]}${res.pay ? ` +${res.pay}` : ""}</b>` : ""}</div></div>`; }).join("") : "";
      box.innerHTML = `<div class="cgtable blackjack"><h3>Blackjack</h3><p class="lore">Six decks in a brass shoe. The dealer smiles without showing her teeth. "Blackjack pays three to two. I stand on all seventeens."</p>
        <div class="bjtable"><svg class="bjprint" viewBox="0 0 600 200" preserveAspectRatio="none"><path id="bjarc" d="M 90 150 Q 300 60 510 150" fill="none"/><text><textPath href="#bjarc" startOffset="50%" text-anchor="middle">BLACKJACK PAYS 3 TO 2</textPath></text></svg><div class="bjrule">Dealer must stand on all 17s</div><div class="shoe" title="The shoe"><i></i></div>${B ? `<div class="bjbet"><div class="stack">${Array.from({ length: Math.min(8, 1 + Math.floor(Math.log2(Math.max(1, B.hands.reduce((t, H) => t + H.bet, 0))))) }, (_, k) => `<i style="--k:${k}"></i>`).join("")}</div><span>${B.hands.reduce((t, H) => t + H.bet, 0)}</span></div>` : `<div class="bjbet empty"><span>BET</span></div>`}<div class="bjdealer"><div class="lbl">The dealer${B ? ` - ${B.stage === "done" ? dv : CG.bjValue([B.dealer[0]]).total}` : ""}</div><div class="cards">${B ? B.dealer.map(card).join("") : ""}</div></div><div class="bjplayer">${hands || `<div class="small">Place a bet and deal.</div>`}</div>${B && B.stage === "done" && B.results ? (() => { const rs = B.results.map((x) => x.r), t = rs.includes("blackjack") ? ["BLACKJACK!", "bj"] : rs.some((x) => x === "win") ? ["YOU WIN", "win"] : rs.every((x) => x === "push") ? ["PUSH", "push"] : rs.every((x) => x === "lose" || x === "bust") ? [rs.includes("bust") ? "BUST" : "DEALER WINS", "lose"] : ["SETTLED", "push"]; return `<div class="bjbanner ${t[1]}">${t[0]}</div>`; })() : ""}</div>
        ${play ? "" : this.cgBetRow()}<div class="cgnote">${this.cgNote || ""}</div>${B && B.card ? this.cgCardWon(B.card) : ""}
        <div class="row">${play ? `<button class="primary" data-bj="hit">Hit</button><button data-bj="stand">Stand</button><button data-bj="double" ${g.bjCanDouble() ? "" : "disabled"}>Double</button><button data-bj="split" ${g.bjCanSplit() ? "" : "disabled"}>Split</button>` : `<button class="primary" data-bjdeal>Deal</button>`}<button data-leave>Leave</button></div>
        <div class="small">Six decks, shuffled when a quarter is left; the dealer peeks for blackjack and stands on soft 17; double on any two cards, split a pair once (split aces take one card each). About 99.5% back with good play. A blackjack of the Ace and Jack of Spades brings a Claudescryption card besides.</div>${this.cgStats("blackjack")}</div>`;
      this.cgWireBet(box); box.querySelector("[data-leave]").addEventListener("click", () => this.closeDialogs());
      box.querySelectorAll(".pc.deal").forEach((el, i) => { el.style.animationDelay = `${i * 0.18}s`; setTimeout(() => this.cgSfx("card", 0.4, 0.9 + Math.random() * 0.3), i * 180); });
      box.querySelectorAll(".pc.flip").forEach(() => this.cgSfx("cardplace", 0.5));
      const after = (r) => { if (r && r.error) { this.cgNote = r.error; this.renderCasino(); return; } const S = g.bjState(); this.cgNote = S.stage === "done" ? (S.back ? `${S.back} gold back.` : "The house takes it.") : ""; this.renderCasino();
        if (S.stage === "done") { const b2 = this.$("#casino-body"), best = (S.results || []).map((x) => x.r); setTimeout(() => { if (best.includes("blackjack")) { this.cgSfx("cardwin", 0.6); this.cgCoins(b2, 16); } else if (best.includes("win")) { this.cgSfx("coin", 0.55); this.cgCoins(b2, 6); } else if (best.every((x) => x === "bust" || x === "lose")) this.cgSfx("miss", 0.35); if (S.card) this.cgSfx("victory", 0.5); }, 500); } };
      const dl = box.querySelector("[data-bjdeal]"); if (dl) dl.addEventListener("click", () => { const r = g.bjDeal(this.cgBet === undefined ? 5 : this.cgBet); if (r && r.shuffled) this.cgSfx("chain", 0.3); after(r); });
      box.querySelectorAll("[data-bj]").forEach((b) => b.addEventListener("click", () => { const a = b.dataset.bj; after(a === "hit" ? g.bjHit() : a === "stand" ? g.bjStand() : a === "double" ? g.bjDouble() : g.bjSplit()); }));
    },
    // ---- Jacks or Better ----
    cgPoker(box) {
      const g = this.game, V = g.vpState(), CG = CM.CG, hold = V && V.stage === "hold", bet = V ? V.bet : (this.cgBet === undefined ? 5 : this.cgBet), seen = this.cgSeen = this.cgSeen || new Set();
      const cards = V ? V.cards.map((c, i) => { const fresh = !seen.has(`vp${c.id}:${V.stage}`) && (V.stage === "hold" || (V.drawn || []).includes(i)); seen.add(`vp${c.id}:${V.stage}`); return `<div class="vpslot${V.held[i] ? " held" : ""}" data-vh="${i}">${this.caCard(c, { cls: fresh ? (V.stage === "hold" ? "deal" : "flip") : "" })}<span class="tag">${V.held[i] ? "HELD" : hold ? "hold?" : ""}</span></div>`; }).join("") : [0, 1, 2, 3, 4].map(() => `<div class="vpslot"><div class="pc cgback"></div></div>`).join("");
      box.innerHTML = `<div class="cgtable poker"><h3>Jacks or Better</h3><p class="lore">A cabinet of brass and green glass that deals itself. Five cards; keep what you like; draw once.</p>
        <table class="paytable vp">${CG.VP_PAY.map(([n, m], i) => `<tr class="${V && V.stage === "done" && V.rank === i ? "won" : hold && CG.vpRank(V.cards) === i ? "now" : ""}"><td>${n}${i === 0 ? " <small>+ a rare card</small>" : ""}</td><td>${m * bet}</td></tr>`).join("")}<tr><td colspan="2" class="small">The full 9/6 table: 99.5% back with good play.</td></tr></table>
        <div class="vpcab"><div class="vphand">${cards}</div><div class="vpled"><span>BET <b>${bet}</b></span><span>${hold ? (CG.vpRank(V.cards) >= 0 ? `DEALT: <b>${CG.VP_PAY[CG.vpRank(V.cards)][0].toUpperCase()}</b>` : "HOLD AND DRAW") : V && V.stage === "done" ? (V.back ? `WIN <b>${V.back}</b>` : "GAME OVER") : "PRESS DEAL"}</span></div></div>${hold ? "" : this.cgBetRow()}<div class="cgnote">${this.cgNote || ""}</div>${V && V.card ? this.cgCardWon(V.card) : ""}
        <div class="row">${hold ? `<button class="primary" data-vpdraw>Draw</button>` : `<button class="primary" data-vpdeal>Deal</button>`}<button data-leave>Leave</button></div>${this.cgStats("poker")}</div>`;
      this.cgWireBet(box); box.querySelector("[data-leave]").addEventListener("click", () => this.closeDialogs());
      box.querySelectorAll(".pc.deal, .pc.flip").forEach((el, i) => { el.style.animationDelay = `${i * 0.12}s`; setTimeout(() => this.cgSfx("card", 0.35, 1 + Math.random() * 0.3), i * 120); });
      box.querySelectorAll("[data-vh]").forEach((el) => el.addEventListener("click", () => { if (!hold) return; g.vpHold(Number(el.dataset.vh)); this.cgSfx("cardplace", 0.3, 1.3); this.renderCasino(); }));
      const dl = box.querySelector("[data-vpdeal]"); if (dl) dl.addEventListener("click", () => { const r = g.vpDeal(bet); this.cgNote = r.error || "Click the cards to keep, then draw."; this.renderCasino(); });
      const dr = box.querySelector("[data-vpdraw]"); if (dr) dr.addEventListener("click", () => { const r = g.vpDraw(); this.cgNote = r.error || (r.back ? `${r.what}: ${r.back} gold!` : "Nothing this time."); this.renderCasino(); const b2 = this.$("#casino-body");
        setTimeout(() => { if (r.card) { this.cgSfx("victory", 0.7); this.cgSfx("cardwin", 0.6); this.cgCoins(b2, 40); } else if (r.back >= r.bet * 9) { this.cgSfx("cardwin", 0.55); this.cgCoins(b2, 18); } else if (r.back) { this.cgSfx("coin", 0.5); this.cgCoins(b2, 5); } }, 450); });
    },
  });
}
