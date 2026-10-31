"use strict";
// Leshy's table in the cabin (the thirteenth update): the window's side of Claudescryption. Four views in one dialog -
// the table (which game to play, the deck, the box), the deck (cards in and out), the battle (the board, the hand,
// the scale, the bell) and the winnings (a card to choose). The rules are 64h-cards.js; the collection and the
// rewards 61f-cabin.js.
//
// The board moves (v11.2): every card on it has an identity, and each time the board is drawn it is compared with the
// last - a card new to a lane is dealt in (from your hand below, from Leshy's waiting row above), one that changed
// lanes slides there, one that is gone falls away; a card new to the hand slides in from the pile. The bell's steps
// come a beat apart, and each is shown: the attacker lunges at its lane, the one struck shakes and a number rises off
// it, a blow to the player rises off the scale, whose beam tips toward whoever is winning. And each has its sound.
Object.assign(CM.UI.prototype, {
  openCabin() { this.cabinView = this.game.cardGame && !this.game.cardGame.done ? "battle" : "table"; this.cardPrev = null; this.renderCabin(); this.openDialog("#dlg-cabin"); },
  cardSfx(name, vol = 0.45) { try { CM.audio.play(name, vol); } catch (e) { /* quiet */ } },
  cardHtml(s, o = {}) {
    const I = CM.cardInfo(s), c = o.creature, power = c ? o.power : I.power, health = c ? c.health : I.health, hurt = c && c.health < c.maxHealth;
    const cost = I.blood ? "🩸".repeat(I.blood) : I.bones ? `🦴${I.bones}` : "";
    const tip = [s.name, ...I.sigils.map((g) => `${g}: ${(CM.SIGILS[g] || ["", ""])[1]}`)].join("\n");
    const rare = CM.CARDS[s.name] && CM.CARDS[s.name][6] === "r";
    return `<div class="ccard${rare ? " rare" : ""}${o.cls ? " " + o.cls : ""}"${o.data ? ` ${o.data}` : ""}${o.style ? ` style="${o.style}"` : ""} title="${this.esc(tip)}"><div class="cname">${this.esc(s.name)}</div><div class="ccost">${cost}</div><div class="cemo">${I.emoji}</div><div class="csig">${I.sigils.map((g) => (CM.SIGILS[g] || ["?"])[0]).join("")}</div><div class="cstat"><b>${power}</b><i class="${hurt ? "hurt" : ""}">${health}</i></div></div>`;
  },
  renderCabin() {
    const g = this.game, K = g.cards(), box = this.$("#cabin-body"), v = this.cabinView || "table";
    if (v === "table") {
      const rows = CM.CARD_TABLES.map((T) => { const open = g.cardTableOpen(T), won = K.beaten[T.id] || 0;
        return `<div class="ctable${open ? "" : " locked"}"><div><b>${this.esc(T.name)}</b><br><small>${open ? `${T.boss ? "a boss game: " : ""}${T.gold} gold${won ? "" : " (doubled the first time)"}, a ${T.pick} card to choose${T.item ? ", and a thing" : ""}${won ? ` - won ${won}` : ""}` : `first win ${T.needs.map((id) => CM.CARD_TABLES.find((t) => t.id === id).name.replace(/^A game (in|on) the /, "the ").replace("Leshy wears the ", "the ").replace("'s mask", "")).join(", ")}`}</small></div><button data-sit="${T.id}" ${open ? "" : "disabled"}>Sit down</button></div>`; }).join("");
      const owned = Object.values(K.owned).reduce((s, n) => s + n, 0);
      box.innerHTML = `${this.leshyHead("Leshy's cabin")}<p class="lore">${this.esc(CM.LESHY_LINES.greet)}</p><div class="ctables">${rows}</div>
        <p class="small">Your deck: ${K.deck.length} cards (${CM.CARD_DECK_MIN} to ${CM.CARD_DECK_MAX}). In the box: ${owned} cards of ${Object.keys(K.owned).length} kinds. Games won: ${K.wins} of ${K.games}. Cards turn up now and then in chests below, and good ones from the guardians and the tower's bosses. A lost game costs nothing.</p>
        <div class="row"><button data-cabin="deck">Change the deck</button><button class="close">Leave the table</button></div><div class="small" id="cabin-note"></div>`;
      for (const b of box.querySelectorAll("[data-sit]")) b.addEventListener("click", () => { const why = g.startCardGame(b.dataset.sit); if (why) this.$("#cabin-note").textContent = why; else { this.cabinSel = { hand: null, sac: [] }; this.cardPrev = null; this.cabinView = "battle"; this.cardSfx("card", 0.5); this.renderCabin(); this.cardBanner(g.cardGame.table.boss ? `${g.cardGame.table.boss === "Leshy" ? "Leshy" : g.cardGame.table.boss}` : "Leshy deals", "his"); } });
    } else if (v === "deck") {
      const inDeck = {}; for (const n of K.deck) inDeck[n] = (inDeck[n] || 0) + 1;
      const names = Object.keys(K.owned).sort((a, b) => (CM.CARDS[a][6] === "r") - (CM.CARDS[b][6] === "r") || a.localeCompare(b));
      const deck = K.deck.slice().sort().map((n) => this.cardHtml(CM.cardSpec(n), { data: `data-out="${this.esc(n)}"`, cls: "small" })).join("");
      const boxed = names.filter((n) => K.owned[n] - (inDeck[n] || 0) > 0).map((n) => `<div class="cwrap">${this.cardHtml(CM.cardSpec(n), { data: `data-in="${this.esc(n)}"`, cls: "small" })}<span>x${K.owned[n] - (inDeck[n] || 0)}</span></div>`).join("");
      box.innerHTML = `<h2>The deck</h2><p class="small">Click a card in the deck to put it back in the box; click one in the box to add it. A deck holds ${CM.CARD_DECK_MIN} to ${CM.CARD_DECK_MAX} cards, and squirrels are always to hand besides.</p>
        <div class="list-title">The deck (${K.deck.length})</div><div class="crow wrap">${deck}</div><div class="list-title">The box</div><div class="crow wrap">${boxed || "<small>Every card you own is in the deck.</small>"}</div>
        <div class="small" id="cabin-note"></div><div class="row"><button data-cabin="table">Back to the table</button></div>`;
      for (const b of box.querySelectorAll("[data-out]")) b.addEventListener("click", () => { const why = g.deckRemove(b.dataset.out); this.cardSfx(why ? "miss" : "card", 0.4); this.renderCabin(); if (why) this.$("#cabin-note").textContent = why; });
      for (const b of box.querySelectorAll("[data-in]")) b.addEventListener("click", () => { const why = g.deckAdd(b.dataset.in); this.cardSfx(why ? "miss" : "cardplace", 0.4); this.renderCabin(); if (why) this.$("#cabin-note").textContent = why; });
    } else if (v === "battle") this.renderCardBattle();
    else if (v === "reward") {
      const R = g.cardGame && g.cardGame.reward;
      box.innerHTML = `${this.leshyHead(R ? "You win" : "Leshy wins")}${R ? `<p class="lore">${R.gold} gold${R.item ? `, and ${this.esc(R.item.name)} (${this.esc(CM.itemLabel(R.item))})` : ""}. Leshy fans three cards on the table: take one.</p>
        <div class="crow fan">${R.choices.map((n, i) => this.cardHtml(CM.cardSpec(n), { data: `data-take="${this.esc(n)}"`, cls: (R.taken === n ? "sel" : R.taken ? "dim" : "") + " fanned", style: `--i:${i - 1}; animation-delay:${i * 0.12}s` })).join("")}</div>` : `<p class="lore">The scale tips his way. Nothing is lost: sit down again whenever you like.</p>`}
        <div class="row"><button data-cabin="table" ${R && !R.taken ? "disabled" : ""}>Back to the table</button></div>`;
      for (const b of box.querySelectorAll("[data-take]")) b.addEventListener("click", () => { if (g.takeCardReward(b.dataset.take)) { this.cardSfx("cardplace", 0.6); this.renderCabin(); } this.refresh(); });
    }
    for (const b of box.querySelectorAll("[data-cabin]")) b.addEventListener("click", () => { if (b.dataset.cabin === "table") g.leaveCardTable(); this.cabinView = b.dataset.cabin; this.renderCabin(); });
    for (const b of box.querySelectorAll("button.close")) b.addEventListener("click", () => this.closeDialogs());
  },
  // Leshy across the table: two eyes in the dark between the candles
  leshyHead(title) { return `<div class="cleshy"><span class="candle">🕯️</span><div class="ceyes${this.cardGlint ? " glint" : ""}"><i></i><i></i></div><span class="candle">🕯️</span></div><h2 class="ctitle">${this.esc(title)}</h2>`; },
  // a word across the board for a moment: whose turn, a mask, the end
  cardBanner(text, who) {
    const box = this.$("#cabin-body"); if (!box) return;
    const b = document.createElement("div"); b.className = `cbanner ${who || ""}`; b.textContent = text; box.appendChild(b); setTimeout(() => b.remove(), 1300);
  },
  // ---- the board ----
  renderCardBattle() {
    const g = this.game, G = g.cardGame, B = G.battle, box = this.$("#cabin-body"), sel = this.cabinSel || (this.cabinSel = { hand: null, sac: [] }), busy = Boolean(this.cabinBusy);
    // the cards' identities, and where each was the last time the board was drawn
    const ids = this.cardIds || (this.cardIds = new WeakMap()), idOf = (o) => { if (!o) return 0; if (!ids.has(o)) ids.set(o, (this.cardNext = (this.cardNext || 0) + 1)); return ids.get(o); };
    const prev = this.cardPrev || { slots: {}, hand: new Set(), scale: B.scale }, now = { slots: {}, hand: new Set(), scale: B.scale }, ROWS = { queue: 0, leshy: 1, you: 2 }, W = 90, H = 122;
    const slot = (c, side, i) => {
      const key = `${side}:${i}`;
      if (!c) return `<div class="cslot" data-slot="${key}"><div class="ccard empty${side === "you" && !busy && sel.hand !== null ? " target" : ""}" data-lane="${key}"></div></div>`;
      const id = idOf(c), was = prev.slots[id]; let anim = "", style = "";
      if (!was) anim = side === "you" ? " dealt" : side === "leshy" ? " placed" : " queued";
      else if (was.row !== side || was.lane !== i) { anim = " moved"; style = `--dx:${(was.lane - i) * W}px; --dy:${(ROWS[was.row] - ROWS[side]) * H}px`; }
      now.slots[id] = { row: side, lane: i, html: null };
      const html = this.cardHtml(c.spec, { creature: c, power: side === "queue" ? c.basePower : B.powerOf(side, i), cls: `${anim}${side === "you" && sel.sac.includes(i) ? " sac" : ""}`, data: `data-lane="${key}" data-cid="${id}"`, style });
      now.slots[id].html = html;
      return `<div class="cslot" data-slot="${key}">${html}</div>`;
    };
    const rowHtml = (row, side) => row.map((c, i) => slot(c, side, i)).join("");
    const hand = B.hand.map((s, i) => { const id = idOf(s); now.hand.add(id); return this.cardHtml(s, { data: `data-hand="${i}"`, cls: `${sel.hand === i ? "sel" : ""}${B.canAfford(s) ? "" : " dim"}${prev.hand.has(id) || !this.cardPrev ? "" : " drawn"}`, style: `animation-delay:${Math.min(4, [...now.hand].length - 1) * 0.04}s` }); }).join("");
    const need = sel.hand !== null && B.hand[sel.hand] ? CM.cardInfo(B.hand[sel.hand]).blood : 0, have = B.bloodOf(sel.sac);
    const tip = B.over ? "" : busy ? "The bell rings..." : B.canDraw() ? "Draw: a card from your deck, or a squirrel." : sel.hand === null ? "Play a card from your hand, or ring the bell." : need > have ? `Sacrifice ${need - have} more blood: click your creatures.` : "Now click an empty lane of yours.";
    const tilt = (v) => `${Math.max(-5, Math.min(5, v)) * 4}deg`;   // (the heavier pan sinks: his on the left, yours on the right)
    box.innerHTML = `<div class="cbattle">${this.leshyHead(G.table.name + (B.boss && B.phase === 2 ? " - the second phase" : ""))}
      <div class="ctop"><div class="cscalebox" title="The scale: five teeth your way wins"><div class="cscalebeam" style="--from:${tilt(prev.scale)}; --to:${tilt(B.scale)}"><span class="pan his">${B.scale < 0 ? "🦷".repeat(-B.scale) : ""}</span><span class="pan yours">${B.scale > 0 ? "🦷".repeat(B.scale) : ""}</span></div><div class="cscalepost"></div><div class="cscaleword">${B.scale === 0 ? "even" : B.scale > 0 ? `${B.scale} your way` : `${-B.scale} his way`}</div></div>
      <div class="clog">${B.log.slice(-2).map((l) => `<div>${this.esc(l)}</div>`).join("") || "<div>Leshy waits for you to play.</div>"}</div></div>
      <div class="cboard"><div class="crow queue">${rowHtml(B.queue, "queue")}</div><div class="crow his">${rowHtml(B.leshy, "leshy")}</div><div class="crow mine">${rowHtml(B.you, "you")}</div></div>
      <div class="cbar"><button class="cpile" data-draw="deck" ${B.canDraw() && B.deck.length && !busy ? "" : "disabled"}><span class="cback"></span>Deck (${B.deck.length})</button><button class="cpile" data-draw="squirrel" ${B.canDraw() && B.squirrels && !busy ? "" : "disabled"}><span class="cback sq">🐿️</span>Squirrels (${B.squirrels})</button><span class="cbones">🦴 ${B.bones}</span><span class="ctip">${this.esc(tip)}</span><button class="primary cbell" data-bell ${!B.canDraw() && !busy && !B.over ? "" : "disabled"}>🔔 Ring the bell</button></div>
      <div class="crow hand">${hand}</div>
      <div class="row"><button data-forfeit>${B.over ? "Back to the table" : "Leave the game (it is lost)"}</button></div></div>`;
    // the fallen: where they stood, falling away
    for (const [id, was] of Object.entries(prev.slots)) {
      if (now.slots[id] || !was.html) continue;
      const cell = box.querySelector(`.cslot[data-slot="${was.row}:${was.lane}"]`); if (!cell) continue;
      const ghost = document.createElement("div"); ghost.className = "cghost"; ghost.innerHTML = was.html; const card = ghost.firstElementChild; if (card) { card.className = card.className.replace(/ (dealt|placed|queued|moved)/g, "") + " dying"; card.removeAttribute("data-lane"); }
      cell.appendChild(ghost); setTimeout(() => ghost.remove(), 700);
      if (!this.cardMuteDeath) this.cardSfx("carddeath", 0.4);
    }
    this.cardPrev = now; this.cardGlint = false;
    // the hands on the table
    box.querySelectorAll("[data-draw]").forEach((b) => b.addEventListener("click", () => { if (B.draw(b.dataset.draw)) this.cardSfx("card", 0.55); this.renderCabin(); }));
    box.querySelectorAll("[data-hand]").forEach((b) => b.addEventListener("click", () => { if (busy || B.canDraw()) return; const i = Number(b.dataset.hand); sel.hand = sel.hand === i ? null : i; sel.sac = []; this.cardSfx("card", 0.25); this.renderCabin(); }));
    box.querySelectorAll("[data-lane^='you:']").forEach((b) => b.addEventListener("click", () => {
      if (busy || sel.hand === null) return; const lane = Number(b.dataset.lane.split(":")[1]), card = B.hand[sel.hand]; if (!card) return;
      const I = CM.cardInfo(card), haveNow = B.bloodOf(sel.sac);
      if (B.you[lane] && I.blood && haveNow < I.blood && !sel.sac.includes(lane)) { sel.sac.push(lane); this.cardSfx("sacrifice", 0.35); this.renderCabin(); return; }
      if (B.you[lane] && sel.sac.includes(lane) && haveNow < I.blood) { sel.sac = sel.sac.filter((k) => k !== lane); this.renderCabin(); return; }
      const bones = B.bones, sacs = sel.sac.length;
      if (B.play(sel.hand, lane, sel.sac)) {
        sel.hand = null; sel.sac = []; this.cardMuteDeath = sacs > 0;
        if (sacs) this.cardSfx("sacrifice", 0.5); setTimeout(() => this.cardSfx("cardplace", 0.6), sacs ? 140 : 0); if (B.bones > bones) setTimeout(() => this.cardSfx("bones", 0.4), 260);
      } else this.cardSfx("miss", 0.3);
      this.renderCabin(); this.cardMuteDeath = false;
    }));
    const bell = box.querySelector("[data-bell]"); if (bell) bell.addEventListener("click", () => this.ringCardBell());
    box.querySelector("[data-forfeit]").addEventListener("click", () => { if (!B.over) { B.over = "lost"; g.finishCardGame(); } g.leaveCardTable(); this.cabinView = "table"; this.renderCabin(); this.refresh(); });
  },
  // a step of the bell, shown: the attacker lunges toward the lane it strikes; what is struck shakes, a number rises
  showCardStep(ev) {
    const box = this.$("#cabin-body"), card = (side, lane) => box.querySelector(`.cslot[data-slot="${side}:${lane}"] .ccard:not(.empty)`), cell = (side, lane) => box.querySelector(`.cslot[data-slot="${side}:${lane}"]`);
    const pop = (host, text, cls) => { if (!host) return; const p = document.createElement("div"); p.className = `cpop ${cls || ""}`; p.textContent = text; host.appendChild(p); setTimeout(() => p.remove(), 900); };
    if (ev.kind === "hit" || ev.kind === "face") {
      const a = card(ev.side, ev.lane), up = ev.side === "you";
      if (a) { a.style.setProperty("--lx", `${(ev.t - ev.lane) * 90}px`); a.classList.add(up ? "lunge-up" : "lunge-down"); }
      if (ev.kind === "hit") { const other = up ? "leshy" : "you", t = card(other, ev.t); setTimeout(() => { if (t) t.classList.add("struck"); pop(cell(other, ev.t), `-${ev.power}`, "dmg"); this.cardSfx("cardhit", 0.5); }, 150); }
      else setTimeout(() => { pop(box.querySelector(".cscalebox"), `${up ? "+" : "-"}${ev.power} 🦷`, up ? "good" : "dmg"); this.cardSfx("cardhit", 0.4); setTimeout(() => this.cardSfx("scale", 0.5), 120); }, 150);
    } else if (ev.kind === "advance") { this.cardSfx("cardplace", 0.4); }
    else if (ev.kind === "leshy_turn") { this.cardGlint = true; this.cardBanner("Leshy's turn", "his"); this.cardSfx("card", 0.4); }
    else if (ev.kind === "trick") { this.cardBanner(ev.boss === "Leshy" ? "Leshy wears a mask" : `${ev.boss}!`, "his trick"); this.cardSfx("elite", 0.5); }
    else if (ev.kind === "your_turn") this.cardBanner("Your turn", "yours");
  },
  // the bell: the battle's steps, a beat apart, the board redrawn and the step shown at each
  ringCardBell() {
    const g = this.game, B = g.cardGame.battle, it = B.ringBell(); this.cabinBusy = true; this.cabinSel = { hand: null, sac: [] }; this.cardSfx("tablebell", 0.7);
    const beat = CM.reducedMotion ? 120 : 520;
    const step = () => {
      const r = it.next();
      if (r.done || r.value.kind === "your_turn" || B.over) {
        this.cabinBusy = false;
        if (B.over === "phase") { B.nextPhase(); this.renderCabin(); this.cardBanner(B.boss === "Leshy" ? "Behold - the Moon" : "The second phase", "his trick"); this.cardSfx("elite", 0.6); return; }
        if (B.over) { const won = B.over === "won"; g.finishCardGame(); this.cabinView = "reward"; this.refresh(); this.renderCabin(); this.cardSfx(won ? "cardwin" : "cardlose", 0.7); return; }
        this.renderCabin(); this.showCardStep({ kind: "your_turn" }); return;
      }
      this.renderCabin(); this.showCardStep(r.value); setTimeout(step, r.value.kind === "advance" ? beat * 0.6 : beat);
    };
    this.renderCabin(); setTimeout(step, 300);
  },
});
