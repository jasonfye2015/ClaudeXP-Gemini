"use strict";
// The Gilded Joker, the window's side (the fifteenth update): Claudeatro's table in a dialog - the lobby (the wager,
// the deck, the house's book of unlocks), the blinds, the round (the Jokers, the hand, the chips and the mult as a
// hand is scored, step by step, each with its sound), the cash-out, the shop, the packs, and the end. The rules are
// 64k-claudeatro.js; the house's payouts and unlocks at its foot.
Object.assign(CM.UI.prototype, {
  openCasino() { this.caSel = []; this.caJ = null; this.caNote = ""; this.caBusy = false; this.renderCasino(); this.openDialog("#dlg-casino"); },
  caSfx(name, vol = 0.4, rate = 1) { try { CM.audio.play(name, vol, 0, rate); } catch (e) { /* quiet */ } },
  caCard(c, o = {}) {
    const CA = CM.CA, stone = c.enh === "stone", tip = [stone ? "Stone Card" : `${CA.rankLabel(c.r)} of ${CA.NAME[c.s]}`, c.enh && !stone ? CA.ENHANCEMENTS[c.enh][0] + ": " + CA.ENHANCEMENTS[c.enh][1] : stone ? CA.ENHANCEMENTS.stone[1] : "", c.ed ? CA.EDITIONS[c.ed][0] + ": " + CA.EDITIONS[c.ed][1] : "", c.bonus ? `+${c.bonus} Chips` : ""].filter(Boolean).join("\n");
    const sym = CA.SYMBOL[c.s], court = { 11: "J", 12: "Q", 13: "K" }[c.r], mid = stone ? `<span class="pstone"></span>` : court ? `<span class="pcourt"><i>${court === "K" ? "♚" : court === "Q" ? "♛" : "⚔"}</i><b>${sym}</b></span>` : c.r === 14 ? `<span class="ps ace">${sym}</span>` : `<span class="pips n${Math.min(10, c.r)}">${`<i>${sym}</i>`.repeat(Math.min(10, c.r))}</span>`;
    const enh = c.enh && !stone ? `<span class="ptag">${CA.ENHANCEMENTS[c.enh][0].replace(" Card", "")}</span>` : "";
    return `<div class="pc s${c.s}${c.enh ? " e-" + c.enh : ""}${c.ed ? " d-" + c.ed : ""}${o.cls ? " " + o.cls : ""}" data-cid="${c.id}"${o.data ? " " + o.data : ""} title="${this.esc(tip)}">${stone ? mid : `<span class="pr">${CA.rankLabel(c.r)}<small>${sym}</small></span>${mid}<span class="pr2">${CA.rankLabel(c.r)}<small>${sym}</small></span>`}${enh}${c.bonus ? `<span class="pbonus">+${c.bonus}</span>` : ""}</div>`;
  },
  caJoker(run, j, i, o = {}) {
    const J = CM.CA.JOKERS[j.k], st = run.jokerStatus(j), off = run.rnd && run.rnd.disabled === j.id;
    return `<div class="jk${j.ed ? " d-" + j.ed : ""}${this.caJ === i && !o.shop ? " sel" : ""}${off ? " off" : ""} r${J[1]}" data-jid="${j.id}"${o.data ? " " + o.data : ` data-jk="${i}"`} title="${this.esc(`${j.k}${j.ed ? " (" + CM.CA.EDITIONS[j.ed][0] + ")" : ""}\n${J[3]}${st ? "\n" + st : ""}${off ? "\nDisabled by the Crimson Heart" : ""}`)}"><span class="je">${J[0]}</span><small>${this.esc(j.k)}</small>${o.price !== undefined ? `<em>$${o.price}</em>` : `<em>sell $${j.sell}</em>`}</div>`;
  },
  caCons(c, i, o = {}) {
    const CA = CM.CA, T = c.type === "planet" ? ["🪐", 0, 0, `Levels up ${CA.PLANETS[c.k]}`] : CA.TAROTS[c.k];
    return `<div class="cs ${c.type}"${o.data ? " " + o.data : ` data-cs="${i}"`} title="${this.esc(`${c.k}\n${T[3]}`)}"><span class="je">${T[0]}</span><small>${this.esc(c.k)}</small>${o.price !== undefined ? `<em>$${o.price}</em>` : ""}</div>`;
  },
  // ---- the dialog: whatever the run is doing ----
  renderCasino() {
    const g = this.game, K = g.casino(), run = g.casinoRun(), box = this.$("#casino-body"), CA = CM.CA;
    const head = run ? `<div class="cahead"><b>${CM.CASINO.name}</b><span>Ante ${run.ante}${run.endless ? " (endless)" : ""} - round ${run.roundNo}</span><span class="money">$${run.money}</span><span class="wager">${run.wager ? `Wager ${run.wager} gold, paid back ${run.paid || 0}` : "Playing for nothing"}</span><span class="gold">The party: ${g.gold} gold</span></div>` : "";
    const jokers = run ? `<div class="carow jokers"><span class="lbl">Jokers ${run.jokers.length}/${run.jokerSlots}</span>${run.jokers.map((j, i) => this.caJoker(run, j, i)).join("") || "<small>None yet: the shop sells them.</small>"}${this.caJ !== null && run.jokers[this.caJ] ? `<button data-sell="${this.caJ}">Sell ${this.esc(run.jokers[this.caJ].k)} for $${run.jokers[this.caJ].sell}</button>` : ""}</div>
      <div class="carow cons"><span class="lbl">Consumables ${run.consumables.length}/${run.consSlots}</span>${run.consumables.map((c, i) => this.caCons(c, i)).join("") || "<small>-</small>"}</div>` : "";
    const note = `<div class="canote">${this.esc(this.caNote || "")}</div>`;
    if (!run) { this.renderCasinoLobby(box); return; }
    const st = run.stage;
    if (st === "blind") {
      const B = run.blinds();
      box.innerHTML = `${head}${jokers}<div class="blinds">${B.map((b, i) => `<div class="blind${i === run.blind ? " now" : ""} ${run.blindState[i]}" style="--bc:${b.colour}"><b>${this.esc(b.name)}</b>${b.text ? `<small>${this.esc(b.text)}</small>` : ""}<div>Score at least <b>${CA.fmt(b.target)}</b></div><div>Reward $${b.reward}${run.wager ? ` - the house pays ${CM.casinoPayout(run.wager, run.ante, i)} gold` : ""}</div>${run.blindState[i] ? `<em>${run.blindState[i]}</em>` : i === run.blind ? `<button class="primary" data-pick>Play this blind</button>${i < 2 ? `<button data-skip title="${this.esc(CA.TAGS[run.skipTags[i]][1])}">Skip: ${CA.TAGS[run.skipTags[i]][0]} ${this.esc(run.skipTags[i])}</button>` : ""}` : ""}</div>`).join("")}</div>${note}${this.caFoot(run)}`;
      box.querySelector("[data-pick]").addEventListener("click", () => { run.selectBlind(); this.caSel = []; this.caNote = ""; this.caSfx("card", 0.5); g.casinoKeep(run); this.renderCasino(); });
      const sk = box.querySelector("[data-skip]"); if (sk) sk.addEventListener("click", () => { this.caNote = run.skipBlind() || ""; this.caSfx("cardplace", 0.4); g.casinoKeep(run); this.renderCasino(); });
    } else if (st === "round") {
      const r = run.rnd, sel = this.caSel.filter((i) => i < r.hand.length), cards = sel.map((i) => r.hand[i]), pv = run.preview(cards);
      box.innerHTML = `${head}${jokers}<div class="caround"><div class="cablind" style="--bc:${(run.bossInfo(r.boss) || ["#2E6DA4"])[0]}"><b>${this.esc(r.name)}</b>${r.boss ? `<small>${this.esc(run.bossInfo(r.boss)[3])}</small>` : ""}<div>Score at least <b>${CA.fmt(r.target)}</b></div><div class="score">Round score <b>${CA.fmt(r.score)}</b></div><div>Hands <b>${r.hands}</b> - Discards <b>${r.discards}</b></div><div class="small">Deck ${r.draw.length}/${run.deck.length}</div></div>
        <div class="catable"><div class="hname">${pv ? `${this.esc(pv[0])} <small>lvl ${pv[1]}</small>` : "Choose up to five cards"}</div><div class="cxm"><span class="ch">${pv ? pv[2] : 0}</span> X <span class="mu">${pv ? pv[3] : 0}</span></div><div class="carow played"></div></div></div>
        <div class="cahandrow"><div class="capile cadiscard" title="Discarded this round: ${r.discard.length}">${r.discard.length ? `<span class="cback"></span><span class="cback"></span>` : ""}<em>${r.discard.length}</em></div><div class="carow hand">${r.hand.map((c, i) => this.caCard(c, { data: `data-h="${i}"`, cls: `${sel.includes(i) ? "sel" : ""}${run.debuffed(c) ? " deb" : ""}` })).join("")}</div><div class="capile cadeck" title="Left in the deck: ${r.draw.length}">${r.draw.length ? `<span class="cback"></span><span class="cback"></span><span class="cback"></span>` : ""}<em>${r.draw.length}</em></div></div>
        ${note}<div class="row cabar"><button class="primary" data-play ${sel.length && r.hands ? "" : "disabled"}>Play hand</button><button data-discard ${sel.length && r.discards ? "" : "disabled"}>Discard (${r.discards})</button><button data-sort="rank">Sort by rank</button><button data-sort="suit">Sort by suit</button>${this.caFoot(run, true)}</div>`;
      box.querySelectorAll("[data-h]").forEach((b) => b.addEventListener("click", () => { if (this.caBusy) return; const i = Number(b.dataset.h); if (this.caSel.includes(i)) this.caSel = this.caSel.filter((k) => k !== i); else if (this.caSel.length < 5) this.caSel.push(i); this.caSfx("card", 0.25, 1.2); this.renderCasino(); }));
      box.querySelector("[data-play]").addEventListener("click", () => this.caPlay(run));
      box.querySelector("[data-discard]").addEventListener("click", () => {   // (the chosen fly to the discard pile; then the new ones are dealt)
        if (this.caBusy || !this.caSel.length || r.discards <= 0) return; this.caBusy = true; const pile = box.querySelector(".cadiscard").getBoundingClientRect(), chosen = this.caSel.map((i) => box.querySelector(`[data-h="${i}"]`)).filter(Boolean), t = CM.reducedMotion ? 60 : 380;
        chosen.forEach((el, k) => { const b = el.getBoundingClientRect(); el.animate([{ transform: "translateY(-14px)", opacity: 1 }, { transform: `translate(${pile.left - b.left}px, ${pile.top - b.top + 6}px) rotate(${-25 - k * 9}deg) scale(0.62)`, opacity: 0.15 }], { duration: t, delay: k * 55, easing: "cubic-bezier(.5,0,.7,.4)", fill: "forwards" }); setTimeout(() => this.caSfx("card", 0.3, 0.8 + k * 0.08), k * 55); });
        setTimeout(() => { this.caBusy = false; if (run.discard(this.caSel)) { this.caSel = []; this.caSfx("cardplace", 0.3, 0.8); const out = g.casinoAfterHand(run, null); this.renderCasino(); this.caNews(out); } }, t + chosen.length * 55);
      });
      box.querySelectorAll("[data-sort]").forEach((b) => b.addEventListener("click", () => { run.sortHand(b.dataset.sort); this.caSel = []; this.renderCasino(); }));
    } else if (st === "cashout") {
      box.innerHTML = `${head}${jokers}<div class="cashout"><h3>${this.esc(run.cash[0][0])} beaten</h3>${run.cash.map(([l, v]) => `<div class="line"><span>${this.esc(l)}</span><b>$${v}</b></div>`).join("")}${run.notes.map((n) => `<div class="small">${this.esc(n)}</div>`).join("")}
        <button class="primary" data-collect>Cash out: $${run.cashTotal()}</button>${run.won ? `<p class="lore">Ante 8 is beaten: the run is won.</p><div class="row"><button data-endless>Play on, endless</button><button data-done>Leave the table, the run won</button></div>` : ""}</div>${note}${this.caFoot(run)}`;
      box.querySelector("[data-collect]").addEventListener("click", () => { run.collect(); if (run.won) run.endless = true; this.caSfx("coin", 0.5); g.casinoKeep(run); this.renderCasino(); });
      const en = box.querySelector("[data-endless]"); if (en) en.addEventListener("click", () => { run.won = false; run.endless = true; run.collect(); g.casinoKeep(run); this.renderCasino(); });
      const dn = box.querySelector("[data-done]"); if (dn) dn.addEventListener("click", () => { g.casinoQuit(); this.caNote = "The run is won. The house tips its hat."; this.renderCasino(); });
    } else if (st === "shop") {
      const S = run.shop;
      box.innerHTML = `${head}${jokers}<div class="shop"><div class="carow"><span class="lbl">For sale</span>${S.cards.map((it, i) => (it ? (it.type === "joker" ? this.caJoker(run, it.item, i, { shop: true, price: it.price, data: `data-buy="cards:${i}"` }) : this.caCons({ k: it.item, type: it.type }, i, { price: it.price, data: `data-buy="cards:${i}"` })) : `<div class="sold">sold</div>`)).join("")}</div>
        <div class="carow"><span class="lbl">Packs</span>${S.packs.map((it, i) => (it ? `<div class="pack" style="--pc:${CA.PACKS[it.kind][1]}" data-buy="packs:${i}" title="${this.esc(CA.PACKS[it.kind][2])}"><span class="je">${CA.PACKS[it.kind][0]}</span><small>${CA.packName(it.kind, it.size)}</small><em>$${it.price}</em></div>` : `<div class="sold">sold</div>`)).join("")}
        ${S.voucher ? `<div class="voucher" data-buy="voucher:0" title="${this.esc(CA.VOUCHERS[S.voucher.item][1])}"><span class="je">${CA.VOUCHERS[S.voucher.item][0]}</span><small>${this.esc(S.voucher.item)}</small><em>$${S.voucher.price}</em></div>` : ""}</div>
        <div class="row"><button data-reroll>Reroll ${S.free > 0 ? "(free)" : `$${S.reroll}`}</button><button class="primary" data-next>Next round</button></div></div>${note}${this.caFoot(run)}`;
      box.querySelectorAll("[data-buy]").forEach((b) => b.addEventListener("click", () => { const [w, i] = b.dataset.buy.split(":"); const why = run.buy(w, Number(i)); this.caNote = why || ""; this.caSfx(why ? "miss" : w === "packs" ? "chest" : "coin", 0.45); g.casinoKeep(run); this.renderCasino(); }));
      box.querySelector("[data-reroll]").addEventListener("click", () => { this.caNote = run.reroll() || ""; this.caSfx("card", 0.4); g.casinoKeep(run); this.renderCasino(); });
      box.querySelector("[data-next]").addEventListener("click", () => { run.nextRound(); this.caNote = ""; g.casinoKeep(run); this.renderCasino(); });
    } else if (st === "pack") {
      const P = run.pack, hand = run.packHand(), sel = this.caSel.filter((i) => i < hand.length);
      box.innerHTML = `${head}${jokers}<div class="packopen"><h3>${CA.PACKS[P.kind][0]} ${this.esc(CA.packName(P.kind, P.size))} - choose ${P.picks}</h3><div class="carow">${P.choices.map((ch, i) => ch.type === "joker" ? this.caJoker(run, ch.item, i, { shop: true, price: undefined, data: `data-take="${i}"` }) : ch.type === "card" ? this.caCard(ch.item, { data: `data-take="${i}"` }) : this.caCons({ k: ch.item, type: ch.type }, i, { data: `data-take="${i}"` })).join("")}</div>
        ${hand.length ? `<div class="small">Select cards for a Tarot that needs them:</div><div class="carow hand">${hand.map((c, i) => this.caCard(c, { data: `data-ph="${i}"`, cls: sel.includes(i) ? "sel" : "" })).join("")}</div>` : ""}<div class="row"><button data-skippack>Skip</button></div></div>${note}`;
      box.querySelectorAll("[data-ph]").forEach((b) => b.addEventListener("click", () => { const i = Number(b.dataset.ph); this.caSel = this.caSel.includes(i) ? this.caSel.filter((k) => k !== i) : this.caSel.concat(i).slice(-3); this.renderCasino(); }));
      box.querySelectorAll("[data-take]").forEach((b) => b.addEventListener("click", () => { const [ok, msg] = run.packPick(Number(b.dataset.take), this.caSel.map((i) => hand[i]).filter(Boolean)); this.caNote = msg || ""; if (ok) { this.caSel = []; this.caSfx("cardplace", 0.5); } else this.caSfx("miss", 0.3); g.casinoKeep(run); this.renderCasino(); }));
      box.querySelector("[data-skippack]").addEventListener("click", () => { run.closePack(); this.caSel = []; g.casinoKeep(run); this.renderCasino(); });
    } else this.renderCasinoLobby(box);
    // the Jokers and the consumables, wherever they are shown
    box.querySelectorAll("[data-jk]").forEach((b) => b.addEventListener("click", () => { const i = Number(b.dataset.jk); this.caJ = this.caJ === i ? null : i; this.renderCasino(); }));
    const sell = box.querySelector("[data-sell]"); if (sell) sell.addEventListener("click", () => { const j = run.sellJoker(Number(sell.dataset.sell)); this.caJ = null; this.caNote = `Sold ${j.k} for $${j.sell}.`; this.caSfx("coin", 0.4); g.casinoKeep(run); this.renderCasino(); });
    box.querySelectorAll("[data-cs]").forEach((b) => b.addEventListener("click", () => {
      if (this.caBusy) return; const i = Number(b.dataset.cs), c = run.consumables[i], sel = run.rnd ? this.caSel.map((k) => run.rnd.hand[k]).filter(Boolean) : [];
      this.caFlipIds = new Set(sel.map((cd) => cd.id)); const [ok, msg] = run.useConsumable(i, sel); this.caNote = msg || (ok ? `${c.k} used.` : ""); if (ok) { this.caSel = []; this.caSfx(c.type === "planet" ? "spell" : "teleport", 0.45); if (run.rnd) run.sortHand(); } else this.caSfx("miss", 0.3);
      g.casinoKeep(run); this.renderCasino();
    }));
    box.querySelectorAll("[data-leave]").forEach((b) => b.addEventListener("click", () => this.closeDialogs()));
    this.caMotion(box, run);
    const fold = box.querySelector("[data-fold]"); if (fold) fold.addEventListener("click", () => { g.casinoQuit(); this.caNote = "You fold. The cards go back in the box."; this.renderCasino(); this.refresh(); });
  },
  caFoot(run, inline) { return `${inline ? "" : `<div class="row cafoot">`}<button data-leave title="The game stays on the table until you come back">Leave the table</button><button data-fold title="${run.wager ? "What the house has paid back is yours; the rest of the wager is lost" : "End this run"}">Fold</button>${inline ? "" : "</div>"}`; },
  // a hand played: the cards laid out, every step of the score shown and heard, then the round goes on
  caPlay(run) {
    if (this.caBusy) return; const g = this.game, from = {}; for (const i of this.caSel) { const el = this.$(`#casino-body [data-h="${i}"]`); if (el) from[el.dataset.cid] = el.getBoundingClientRect(); }
    const res = run.play(this.caSel); if (!res) return;
    this.caSel = []; this.caBusy = true; this.renderCasino();
    const box = this.$("#casino-body"), played = box.querySelector(".played"), ch = box.querySelector(".ch"), mu = box.querySelector(".mu"), hn = box.querySelector(".hname"), scoringIds = new Set(res.scoring);
    played.innerHTML = run.rnd.played.map((c, i) => this.caCard(c, { cls: scoringIds.has(c.id) ? "scoring" : "dud", data: `data-p="${i}"` })).join("");
    played.querySelectorAll(".pc").forEach((el, i) => { const a = from[el.dataset.cid], b = el.getBoundingClientRect(); if (a) el.animate([{ transform: `translate(${a.left - b.left}px, ${a.top - b.top}px) rotate(${(i - 2) * 4}deg)` }, { transform: "translateY(-10px) scale(1.06)", offset: 0.7 }, { transform: "none" }], { duration: CM.reducedMotion ? 60 : 420, delay: i * 45, easing: "cubic-bezier(.2,.8,.3,1)", fill: "backwards" }); });   // (from the hand, up to the table)
    setTimeout(() => played.querySelectorAll(".pc.dud").forEach((el) => el.animate([{ filter: "none" }, { filter: "grayscale(0.8) brightness(0.7)", transform: "translateY(8px)" }], { duration: 300, fill: "forwards" })), CM.reducedMotion ? 60 : 520);   // (the cards that do not score sink back)
    hn.innerHTML = `${this.esc(res.hand)} <small>lvl ${res.level}</small>`; ch.textContent = res.base[0]; mu.textContent = res.base[1];
    this.caSfx("cardplace", 0.5);
    const evs = res.events, gap = CM.reducedMotion ? 30 : evs.length > 40 ? 70 : 150;
    const where = (at) => (at[0] === "played" ? played.querySelector(`[data-p="${at[1]}"]`) : at[0] === "joker" ? box.querySelector(`[data-jk="${at[1]}"]`) : at[0] === "held" ? box.querySelector(`[data-h="${at[1]}"]`) : hn);
    let k = 0;
    const step = () => {
      if (k >= evs.length) {
        const tot = document.createElement("div"); tot.className = "catotal"; tot.textContent = CM.CA.fmt(res.total); box.querySelector(".catable").appendChild(tot); this.caSfx(res.total >= run.rnd.target - (run.rnd.score - res.total) ? "cardwin" : "scale", 0.5);
        setTimeout(() => { run.afterPlay(); const out = g.casinoAfterHand(run, res); this.caBusy = false; this.renderCasino(); this.caNews(out); if (run.stage === "over") this.caSfx("cardlose", 0.6); }, CM.reducedMotion ? 150 : 900);
        return;
      }
      const ev = evs[k++], el = where(ev.at);
      if (el) { el.classList.remove("pulse"); void el.offsetWidth; el.classList.add("pulse"); const p = document.createElement("div"); p.className = `capop ${ev.kind}`; p.textContent = ev.text; el.appendChild(p); setTimeout(() => p.remove(), 900); }
      ch.textContent = CM.CA.fmt(ev.chips); mu.textContent = ev.mult % 1 ? ev.mult.toFixed(1) : ev.mult;
      this.caSfx(ev.kind === "chips" ? "card" : ev.kind === "mult" ? "cardhit" : ev.kind === "xmult" ? "elite" : ev.kind === "money" ? "coin" : "card", ev.kind === "xmult" ? 0.3 : 0.25, ev.kind === "chips" ? 1 + Math.min(1, k / 20) : 1);
      setTimeout(step, gap);
    };
    setTimeout(step, 450);
  },
  // the cards' motion between one drawing of the table and the next, each card (and each Joker) by its id: a card new
  // to the hand is dealt from the deck pile, one that moved slides to its new place, one a Tarot changed turns over
  // with a flash, a Joker new to the row springs in
  caMotion(box, run) {
    const last = this.caLast || new Map(), now = new Map(), quick = CM.reducedMotion, roundKey = run && run.rnd ? `${run.ante}:${run.roundNo}` : run && run.stage === "pack" ? "pack" : "";
    if (roundKey !== this.caLastKey) last.clear(); this.caLastKey = roundKey;
    const deck = box.querySelector(".cadeck"), dr = deck ? deck.getBoundingClientRect() : null, flips = this.caFlipIds || new Set(); this.caFlipIds = null;
    let dealt = 0;
    box.querySelectorAll(".hand .pc[data-cid]").forEach((el) => {
      const id = el.dataset.cid, b = el.getBoundingClientRect(), was = last.get(id), sig = el.className.replace(/\b(sel|deb)\b/g, "") + el.textContent;
      now.set(id, { left: b.left, top: b.top, sig });
      if (!was) { const k = dealt++; if (dr) el.animate([{ transform: `translate(${dr.left - b.left}px, ${dr.top - b.top}px) rotateY(180deg) scale(0.8)`, opacity: 0.4 }, { transform: "translateY(-18px) rotateY(0deg)", opacity: 1, offset: 0.75 }, { transform: "none", opacity: 1 }], { duration: quick ? 60 : 460, delay: quick ? 0 : 120 + k * 70, easing: "cubic-bezier(.2,.75,.3,1)", fill: "backwards" }); if (dr) setTimeout(() => this.caSfx("card", 0.22, 1 + k * 0.05), quick ? 0 : 120 + k * 70); }
      else if (flips.has(Number(id)) || was.sig !== sig) { el.animate([{ transform: "rotateY(0deg) scale(1)" }, { transform: "rotateY(90deg) scale(1.15)", filter: "brightness(2.2)" }, { transform: "rotateY(0deg) scale(1.08)", filter: "brightness(1.5)" }, { transform: "none", filter: "none" }], { duration: quick ? 60 : 650, easing: "ease-in-out" }); const burst = document.createElement("div"); burst.className = "caburst"; el.appendChild(burst); setTimeout(() => burst.remove(), 800); }
      else if (Math.abs(was.left - b.left) > 2 || Math.abs(was.top - b.top) > 2) el.animate([{ transform: `translate(${was.left - b.left}px, ${was.top - b.top}px)` }, { transform: "none" }], { duration: quick ? 40 : 260, easing: "cubic-bezier(.3,.7,.4,1)" });
    });
    this.caLast = now;
    const jl = this.caLastJ || new Set(), jn = new Set();
    box.querySelectorAll(".jokers .jk[data-jid]").forEach((el, k) => { jn.add(el.dataset.jid); if (this.caLastJ && !jl.has(el.dataset.jid)) el.animate([{ transform: "translateY(60px) scale(0.3) rotate(-20deg)", opacity: 0 }, { transform: "translateY(-8px) scale(1.15) rotate(4deg)", opacity: 1, offset: 0.7 }, { transform: "none" }], { duration: quick ? 60 : 520, delay: k * 30, easing: "cubic-bezier(.2,.8,.3,1.3)", fill: "backwards" }); });
    this.caLastJ = jn;
  },
  // the house's news after a round: what it paid, what is unlocked
  caNews(out) {
    if (!out) return; const bits = [];
    if (out.paid) bits.push(`The house pays you ${out.paid} gold.`);
    if (out.over) bits.push(`Game over at Ante ${out.over.ante}.${out.over.wager ? ` Of your ${out.over.wager} gold the house paid back ${out.over.paid}.` : ""} Deal again whenever you like.`);
    if (out.jokers.length) bits.push(`Unlocked: ${out.jokers.map((k) => CM.CA.JOKERS[k][0] + " " + k).join(", ")}.`);
    if (out.decks.length) bits.push(`New deck: ${out.decks.join(", ")}!`);
    if (!bits.length) return;
    this.caNote = bits.join(" "); this.renderCasino(); this.refresh();
    if (out.paid) this.caSfx("coin", 0.6); if (out.jokers.length || out.decks.length) this.caSfx("level", 0.5);
    for (const b of bits) this.game.say(`The Gilded Joker: ${b}`);
  },
  // ---- the lobby: the wager, the deck, the house's book ----
  renderCasinoLobby(box) {
    const g = this.game, K = g.casino(), CA = CM.CA, decks = g.casinoDecks(), pool = g.casinoJokers(), next = CM.CA_JOKER_ORDER[pool.length];
    this.caWager = this.caWager === undefined ? Math.min(K.wager || 0, g.gold) : this.caWager; this.caDeck = decks.includes(this.caDeck) ? this.caDeck : decks.includes(K.deck) ? K.deck : "Red Deck";
    box.innerHTML = `<div class="lobby"><h2>${CM.CASINO.name}</h2><p class="lore">Velvet and lamplight, a long green table, and at the end of it a dealer in a gold waistcoat shuffling a deck that hums. "Claudeatro," she says. "Play for gold, or play for nothing. The house keeps a book of what you've earned the right to play with."</p>
      <div class="list-title">The wager (the party has ${g.gold} gold)</div><div class="row wagers">${CM.CASINO.wagers.map((w) => `<button data-w="${w}" class="${this.caWager === w ? "primary" : ""}" ${w > g.gold ? "disabled" : ""}>${w ? `${w} gold` : "For nothing"}</button>`).join("")}</div>
      <div class="small">Each blind you beat, the house pays back ${CM.CASINO.share.map((s) => s * 100 + "%").join(", ")} of the wager (small, big, boss), a quarter more for every ante past the first; beating Ante 8 pays ${CM.CASINO.winBonus} wagers besides.</div>
      <div class="list-title">The deck</div><div class="decks">${Object.keys(CA.DECKS).map((d) => { const ok = decks.includes(d); return `<div class="deck${ok ? "" : " locked"}${this.caDeck === d ? " sel" : ""}" ${ok ? `data-deck="${this.esc(d)}"` : ""} style="--dc:${CA.DECKS[d][0]}"><b>${this.esc(d)}</b><small>${ok ? this.esc(CA.DECKS[d][1]) : "Locked: " + this.esc(CM.CA_DECK_UNLOCKS[d].why)}</small></div>`; }).join("")}</div>
      <div class="list-title">The house's book: Jokers unlocked ${pool.length} of ${CM.CA_JOKER_ORDER.length}${next ? ` - the next, after one more blind beaten` : ""}</div><div class="jbook">${CM.CA_JOKER_ORDER.map((k) => (pool.includes(k) ? `<span title="${this.esc(k + "\n" + CA.JOKERS[k][3])}">${CA.JOKERS[k][0]}</span>` : `<span class="lockd" title="Locked">?</span>`)).join("")}</div>
      <div class="small">Blinds beaten ${K.blinds}, bosses ${K.bosses}, highest ante ${K.maxAnte}, runs won ${K.wins} of ${K.runs}, best hand ${CA.fmt(K.bestHand)}. Wagered ${K.wagered} gold; the house has paid ${K.paid}.</div>
      <div class="canote">${this.esc(this.caNote || "")}</div>
      <div class="row"><button class="primary" data-deal>Deal${this.caWager ? ` (${this.caWager} gold)` : ""}</button><button data-leave>Leave</button></div></div>`;
    box.querySelectorAll("[data-w]").forEach((b) => b.addEventListener("click", () => { this.caWager = Number(b.dataset.w); this.renderCasino(); }));
    box.querySelectorAll("[data-deck]").forEach((b) => b.addEventListener("click", () => { this.caDeck = b.dataset.deck; this.caSfx("card", 0.3); this.renderCasino(); }));
    box.querySelector("[data-deal]").addEventListener("click", () => { const why = g.casinoDeal(this.caDeck, this.caWager); this.caNote = why || ""; if (!why) { this.caSfx("tablebell", 0.5); this.caSfx("card", 0.5); this.refresh(); } this.renderCasino(); });
    box.querySelectorAll("[data-leave]").forEach((b) => b.addEventListener("click", () => this.closeDialogs()));
  },
});
