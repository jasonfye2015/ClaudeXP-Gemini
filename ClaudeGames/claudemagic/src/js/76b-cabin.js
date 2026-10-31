"use strict";
// Leshy's table in the cabin (the thirteenth update): the window's side of Claudescryption. Four views in one dialog -
// the table (which game to play, the deck, the box), the deck (cards in and out), the battle (the board, the hand,
// the scale, the bell) and the winnings (a card to choose). The rules are 64h-cards.js; the collection and the
// rewards 61f-cabin.js.
Object.assign(CM.UI.prototype, {
  openCabin() { this.cabinView = this.game.cardGame && !this.game.cardGame.done ? "battle" : "table"; this.renderCabin(); this.openDialog("#dlg-cabin"); },
  cardHtml(s, o = {}) {
    const I = CM.cardInfo(s), c = o.creature, power = c ? o.power : I.power, health = c ? c.health : I.health;
    const cost = I.blood ? "🩸".repeat(I.blood) : I.bones ? `🦴${I.bones}` : "";
    const tip = [s.name, ...I.sigils.map((g) => `${g}: ${(CM.SIGILS[g] || ["", ""])[1]}`)].join("\n");
    return `<div class="ccard${o.cls ? " " + o.cls : ""}"${o.data ? ` ${o.data}` : ""} title="${this.esc(tip)}"><div class="cname">${this.esc(s.name)}</div><div class="ccost">${cost}</div><div class="cemo">${I.emoji}</div><div class="csig">${I.sigils.map((g) => (CM.SIGILS[g] || ["?"])[0]).join("")}</div><div class="cstat"><b>${power}</b><i>${health}</i></div></div>`;
  },
  renderCabin() {
    const g = this.game, K = g.cards(), box = this.$("#cabin-body"), v = this.cabinView || "table";
    if (v === "table") {
      const rows = CM.CARD_TABLES.map((T) => { const open = g.cardTableOpen(T), won = K.beaten[T.id] || 0;
        return `<div class="ctable${open ? "" : " locked"}"><div><b>${this.esc(T.name)}</b><br><small>${open ? `${T.boss ? "a boss game: " : ""}${T.gold} gold${won ? "" : " (doubled the first time)"}, a ${T.pick} card to choose${T.item ? ", and a thing" : ""}${won ? ` - won ${won}` : ""}` : `first win ${T.needs.map((id) => CM.CARD_TABLES.find((t) => t.id === id).name.replace(/^A game (in|on) the /, "the ").replace("Leshy wears the ", "the ").replace("'s mask", "")).join(", ")}`}</small></div><button data-sit="${T.id}" ${open ? "" : "disabled"}>Sit down</button></div>`; }).join("");
      const owned = Object.values(K.owned).reduce((s, n) => s + n, 0);
      box.innerHTML = `<h2>Leshy's cabin</h2><p class="lore">${this.esc(CM.LESHY_LINES.greet)}</p><div class="ctables">${rows}</div>
        <p class="small">Your deck: ${K.deck.length} cards (${CM.CARD_DECK_MIN} to ${CM.CARD_DECK_MAX}). In the box: ${owned} cards of ${Object.keys(K.owned).length} kinds. Games won: ${K.wins} of ${K.games}. Cards turn up now and then in chests below, and good ones from the guardians and the tower's bosses. A lost game costs nothing.</p>
        <div class="row"><button data-cabin="deck">Change the deck</button><button class="close">Leave the table</button></div><div class="small" id="cabin-note"></div>`;
      for (const b of box.querySelectorAll("[data-sit]")) b.addEventListener("click", () => { const why = g.startCardGame(b.dataset.sit); if (why) this.$("#cabin-note").textContent = why; else { this.cabinSel = { hand: null, sac: [] }; this.cabinView = "battle"; this.renderCabin(); } });
    } else if (v === "deck") {
      const inDeck = {}; for (const n of K.deck) inDeck[n] = (inDeck[n] || 0) + 1;
      const names = Object.keys(K.owned).sort((a, b) => (CM.CARDS[a][6] === "r") - (CM.CARDS[b][6] === "r") || a.localeCompare(b));
      const deck = K.deck.slice().sort().map((n) => this.cardHtml(CM.cardSpec(n), { data: `data-out="${this.esc(n)}"`, cls: "small" })).join("");
      const boxed = names.filter((n) => K.owned[n] - (inDeck[n] || 0) > 0).map((n) => `<div class="cwrap">${this.cardHtml(CM.cardSpec(n), { data: `data-in="${this.esc(n)}"`, cls: "small" + (CM.CARDS[n][6] === "r" ? " rare" : "") })}<span>x${K.owned[n] - (inDeck[n] || 0)}</span></div>`).join("");
      box.innerHTML = `<h2>The deck</h2><p class="small">Click a card in the deck to put it back in the box; click one in the box to add it. A deck holds ${CM.CARD_DECK_MIN} to ${CM.CARD_DECK_MAX} cards, and squirrels are always to hand besides.</p>
        <div class="list-title">The deck (${K.deck.length})</div><div class="crow wrap">${deck}</div><div class="list-title">The box</div><div class="crow wrap">${boxed || "<small>Every card you own is in the deck.</small>"}</div>
        <div class="small" id="cabin-note"></div><div class="row"><button data-cabin="table">Back to the table</button></div>`;
      for (const b of box.querySelectorAll("[data-out]")) b.addEventListener("click", () => { const why = g.deckRemove(b.dataset.out); this.renderCabin(); if (why) this.$("#cabin-note").textContent = why; });
      for (const b of box.querySelectorAll("[data-in]")) b.addEventListener("click", () => { const why = g.deckAdd(b.dataset.in); this.renderCabin(); if (why) this.$("#cabin-note").textContent = why; });
    } else if (v === "battle") this.renderCardBattle();
    else if (v === "reward") {
      const R = g.cardGame && g.cardGame.reward;
      box.innerHTML = `<h2>${R ? "You win" : "Leshy wins"}</h2>${R ? `<p class="lore">${R.gold} gold${R.item ? `, and ${this.esc(R.item.name)} (${this.esc(CM.itemLabel(R.item))})` : ""}. Leshy fans three cards on the table: take one.</p>
        <div class="crow">${R.choices.map((n) => this.cardHtml(CM.cardSpec(n), { data: `data-take="${this.esc(n)}"`, cls: (R.taken === n ? "sel" : "") + (CM.CARDS[n][6] === "r" ? " rare" : "") })).join("")}</div>` : `<p class="lore">The scale tips his way. Nothing is lost: sit down again whenever you like.</p>`}
        <div class="row"><button data-cabin="table" ${R && !R.taken ? "disabled" : ""}>Back to the table</button></div>`;
      for (const b of box.querySelectorAll("[data-take]")) b.addEventListener("click", () => { if (g.takeCardReward(b.dataset.take)) this.renderCabin(); this.refresh(); });
    }
    for (const b of box.querySelectorAll("[data-cabin]")) b.addEventListener("click", () => { if (b.dataset.cabin === "table") g.leaveCardTable(); this.cabinView = b.dataset.cabin; this.renderCabin(); });
    for (const b of box.querySelectorAll("button.close")) b.addEventListener("click", () => this.closeDialogs());
  },
  // the board: his queue, his row, yours; the hand; the piles, the bones, the scale and the bell
  renderCardBattle() {
    const g = this.game, G = g.cardGame, B = G.battle, box = this.$("#cabin-body"), sel = this.cabinSel || (this.cabinSel = { hand: null, sac: [] }), busy = Boolean(this.cabinBusy);
    const slot = (c, side, i, cls) => (c ? this.cardHtml(c.spec, { creature: c, power: side === "queue" ? c.basePower : B.powerOf(side, i), cls: `${cls || ""}${side === "you" && sel.sac.includes(i) ? " sac" : ""}${c.flash ? " flash" : ""}`, data: `data-lane="${side}:${i}"` }) : `<div class="ccard empty" data-lane="${side}:${i}"></div>`);
    const teeth = []; for (let k = -5; k <= 5; k++) teeth.push(`<i class="${k === 0 ? "mid" : (k < 0 && B.scale <= k) || (k > 0 && B.scale >= k) ? (k < 0 ? "his" : "yours") : ""}"></i>`);
    const hand = B.hand.map((s, i) => this.cardHtml(s, { data: `data-hand="${i}"`, cls: `${sel.hand === i ? "sel" : ""}${B.canAfford(s) ? "" : " dim"}` })).join("");
    const need = sel.hand !== null && B.hand[sel.hand] ? CM.cardInfo(B.hand[sel.hand]).blood : 0, have = B.bloodOf(sel.sac);
    const tip = B.over ? "" : busy ? "..." : B.canDraw() ? "Draw: a card from your deck, or a squirrel." : sel.hand === null ? "Play a card from your hand, or ring the bell." : need > have ? `Sacrifice ${need - have} more blood: click your creatures.` : "Now click an empty lane of yours.";
    box.innerHTML = `<div class="cbattle"><div class="chead"><b>${this.esc(G.table.name)}</b>${B.boss && B.phase === 2 ? " - the second phase" : ""}<span class="cscale" title="The scale: five teeth your way wins">${teeth.join("")}</span></div>
      <div class="clog">${B.log.slice(-3).map((l) => `<div>${this.esc(l)}</div>`).join("") || "<div>Leshy waits for you to play.</div>"}</div>
      <div class="crow queue">${B.queue.map((c, i) => slot(c, "queue", i, "q")).join("")}</div>
      <div class="crow">${B.leshy.map((c, i) => slot(c, "leshy", i)).join("")}</div>
      <div class="crow mine">${B.you.map((c, i) => slot(c, "you", i)).join("")}</div>
      <div class="cbar"><button data-draw="deck" ${B.canDraw() && B.deck.length && !busy ? "" : "disabled"}>Deck (${B.deck.length})</button><button data-draw="squirrel" ${B.canDraw() && B.squirrels && !busy ? "" : "disabled"}>🐿️ Squirrels (${B.squirrels})</button><span>🦴 ${B.bones}</span><span class="ctip">${this.esc(tip)}</span><button class="primary" data-bell ${!B.canDraw() && !busy && !B.over ? "" : "disabled"}>🔔 Ring the bell</button></div>
      <div class="crow hand">${hand}</div>
      <div class="row"><button data-forfeit>${B.over ? "Back to the table" : "Leave the game (it is lost)"}</button></div></div>`;
    box.querySelectorAll("[data-draw]").forEach((b) => b.addEventListener("click", () => { B.draw(b.dataset.draw); this.renderCabin(); }));
    box.querySelectorAll("[data-hand]").forEach((b) => b.addEventListener("click", () => { if (busy || B.canDraw()) return; const i = Number(b.dataset.hand); sel.hand = sel.hand === i ? null : i; sel.sac = []; this.renderCabin(); }));
    box.querySelectorAll("[data-lane^='you:']").forEach((b) => b.addEventListener("click", () => {
      if (busy || sel.hand === null) return; const lane = Number(b.dataset.lane.split(":")[1]), card = B.hand[sel.hand]; if (!card) return;
      const I = CM.cardInfo(card), haveNow = B.bloodOf(sel.sac);
      if (B.you[lane] && I.blood && haveNow < I.blood && !sel.sac.includes(lane)) { sel.sac.push(lane); this.renderCabin(); return; }
      if (B.you[lane] && sel.sac.includes(lane) && haveNow < I.blood) { sel.sac = sel.sac.filter((k) => k !== lane); this.renderCabin(); return; }
      if (B.play(sel.hand, lane, sel.sac)) { sel.hand = null; sel.sac = []; this.cardSound("play"); }
      this.renderCabin();
    }));
    const bell = box.querySelector("[data-bell]"); if (bell) bell.addEventListener("click", () => this.ringCardBell());
    box.querySelector("[data-forfeit]").addEventListener("click", () => { if (!B.over) { B.over = "lost"; g.finishCardGame(); } g.leaveCardTable(); this.cabinView = "table"; this.renderCabin(); this.refresh(); });
  },
  cardSound(what) { try { CM.audio.play(what === "bell" ? "toll" : what === "hit" ? "hit" : what === "face" ? "slam" : "step", what === "bell" ? 0.35 : 0.3); } catch (e) { /* quiet */ } },
  // the bell: the battle's steps, a beat apart, the board redrawn at each
  ringCardBell() {
    const g = this.game, B = g.cardGame.battle, it = B.ringBell(); this.cabinBusy = true; this.cabinSel = { hand: null, sac: [] }; this.cardSound("bell");
    const step = () => {
      const r = it.next();
      if (r.done || r.value.kind === "your_turn" || B.over) {
        this.cabinBusy = false;
        if (B.over === "phase") { B.nextPhase(); this.renderCabin(); return; }
        if (B.over) { g.finishCardGame(); this.cabinView = "reward"; this.refresh(); }
        this.renderCabin(); return;
      }
      if (r.value.kind === "hit" || r.value.kind === "face") this.cardSound(r.value.kind);
      this.renderCabin(); setTimeout(step, CM.reducedMotion ? 60 : 300);
    };
    this.renderCabin(); setTimeout(step, 250);
  },
});
