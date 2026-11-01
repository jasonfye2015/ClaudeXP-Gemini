"use strict";
// The Joker's story (v17.8): five chapters, told by the Joker himself in his alcove at the end of the foyer, each
// opened by the party's Joker level (3, 7, 12, 17, 22) - who he is, where the floor came from, and what he wants -
// and then, from level 25 with every chapter heard, the Final Night: the Joker plays the party at five of his own
// games, one after another. Win them all and the story ends, with his own charm (the Joker's Own), the golden crown
// for his card, 5,000 gold, 1,000 tickets and a rare card. A round lost can be tried again; nothing played in practice
// counts. The window is 76zzzb-story.js.
{ const ST = CM.STORY = {
    CHAPTERS: [
      { level: 3, title: "I. The card that floated", text: [
        "\"Sit, sit. You've been in often enough that I ought to introduce myself. I am the Joker. Not a joker - the Joker. The one from the deck.\"",
        "\"Before your town was on the hill it was down by the river, the lower town, with a bell-founder and a market and a gambling-house called the Gilded Lantern. Every deck in it had a Joker in it, and nobody ever played us. We were the spare card. The one you throw away.\"",
        "\"Then the water came up one night and took the lower town, and everyone in it who couldn't run. And in all that dark water, do you know what floated?\" He taps his painted chest. \"Pasteboard floats.\"" ] },
      { level: 7, title: "II. The one who picked me up", text: [
        "\"A girl found me on the bank in the morning. Nine years old, soaked through, everyone she knew gone under. She dried me on a stone and kept me in her sleeve.\"",
        "\"She played games with me. Not cards - you can't play cards with one card - but games all the same. Which hand is it in. Heads or tails. Guess the number. She laughed every time she won and every time she lost, and every laugh went into me like warmth into a stone.\"",
        "\"That is what I eat, you understand. Not gold. Not luck. The laugh when the wheel stops. The breath held when the ball drops. I grew fat on one small girl's laughing.\"" ] },
      { level: 12, title: "III. A house built on a laugh", text: [
        "\"She grew up, and she was clever, and she built a house on the hill for games. A small one. Two tables and a fire. She called it the Gilded Joker, after me, and she hung me in a frame over the door.\"",
        "\"People came, because people always come where there's laughing. And every night I ate, and every night I grew, and one night I found I could step down out of the frame.\"",
        "\"She was old by then. She saw me standing on her floor - a painted card, as tall as a man - and she wasn't frightened at all. She said: 'There you are. Look after them.' And then she was gone, the way people go, and the house was mine.\"" ] },
      { level: 17, title: "IV. Why the floor goes back so far", text: [
        "\"You've noticed the hall is bigger inside than the street allows. That's me. Every table I add, I make room for. Every game you love, I keep. The reels, the wheels, the little fish in the pond - all of it is the house remembering what made people laugh.\"",
        "\"And the residents - the tavern-keeper, the farmer's hand, the librarian with her patience - they come because they need it, the way the girl did. A town that lost half of itself in one night needs somewhere to hold its breath and let it go.\"",
        "\"Under the hill, something else is awake. You know the one. He eats quiet, and fear, and the ends of things. I eat the other part. Between us, we keep the town in balance.\"" ] },
      { level: 22, title: "V. What I want from you", text: [
        "\"So. Why tell you all this? Because you are the first in a long time to stand on my floor and laugh as much when you lose as when you win. She did that. Nobody else has, until you.\"",
        "\"A card wants to be played. All those years in the frame, in the sleeve, in the dark water - nobody has ever played me. Not properly. Not to win.\"",
        "\"When you're ready - when you've stood with me long enough - come back to this alcove, and we will have a Final Night, you and I. Five of my games. My hand against yours. And if you win, I'll give you something I've never given anyone.\"" ] },
    ],
    FINAL_LEVEL: 25,
    ROUNDS: [
      { id: "reels", game: "slots", name: "The Reels", goal: "Three alike on the line within 15 pulls.", n: 15 },
      { id: "cards", game: "blackjack", name: "Twenty-one", goal: "Win 3 hands of blackjack before losing 3.", n: 3 },
      { id: "darts", game: "darts", name: "The Board", goal: "Beat the Joker's 600 at the Tavern Board in one game.", target: 600 },
      { id: "drop", game: "plinko", name: "The Drop", goal: "Land 8 times the chip or better on the high Drop Board within 12 drops.", n: 12 },
      { id: "hand", game: "poker", name: "The Hand", goal: "Make two pair or better twice at Jacks or Better within 6 deals.", n: 6 },
    ],
    REWARD: { gold: 5000, tickets: 1000 },
    TAUNT: ["\"Ha! The house wins this one. Again?\"", "\"Not tonight, friend. Shuffle up.\"", "\"So close. I love it when it's close.\""],
    PRAISE: ["\"Well played! On to the next.\"", "\"Oh, that stings. Lovely.\"", "\"You're better than I thought. Next!\"", "\"Ha! One more. Just one more.\""],
  };
  const P = CM.Game.prototype, slot0 = P.slotSpin, bj0 = P.bjSettle, fa0 = P.faEnd, pk0 = P.pkDrop, vp0 = P.vpDraw;
  Object.assign(P, {
    stStore() { const F = this.cgStore(); F.story = F.story || { heard: [], final: null, done: false }; return F.story; },
    stOpen(i) { return (this.jkLevel ? this.jkLevel() : 1) >= ST.CHAPTERS[i].level; },
    stHear(i) { if (!this.stOpen(i)) return { error: `The Joker will tell you this at Joker level ${ST.CHAPTERS[i].level}.` }; const S = this.stStore(); if (!S.heard.includes(i)) { S.heard.push(i); this.saveCasino && this.saveCasino(); } return { chapter: ST.CHAPTERS[i] }; },
    stFinalReady() { const S = this.stStore(); return !S.done && (this.jkLevel ? this.jkLevel() : 1) >= ST.FINAL_LEVEL && ST.CHAPTERS.every((_, i) => S.heard.includes(i)); },
    stBegin() { if (!this.stFinalReady()) return { error: "Not yet." }; const S = this.stStore(); S.final = { round: 0, c: 0, l: 0, won: [], tries: 0 }; this.saveCasino && this.saveCasino(); return S.final; },
    stRound() { const S = this.stStore(); return S.final && !S.done ? ST.ROUNDS[S.final.round] : null; },
    // a round's play, counted: "win", "lose", or nothing yet
    stCount(game, f) { if (this.cgPractice) return; const S = this.stStore(), F = S.final, R = this.stRound(); if (!F || !R || R.game !== game) return; const r = f(F, R); if (!r) return;
      if (r === "lose") { F.c = 0; F.l = 0; F.tries += 1; this.stNote = { lost: true, round: R, line: ST.TAUNT[F.tries % ST.TAUNT.length] }; }
      else { F.won.push(R.id); F.round += 1; F.c = 0; F.l = 0; this.stNote = { won: true, round: R, line: ST.PRAISE[(F.round - 1) % ST.PRAISE.length] }; this.cgCelebrate && this.cgCelebrate(2, `The Final Night: ${R.name} - won!`); if (F.round >= ST.ROUNDS.length) this.stEnd(); }
      this.saveCasino && this.saveCasino(); },
    stEnd() { const S = this.stStore(); S.done = true; S.final.over = true; this.gold += ST.REWARD.gold; if (this.tkAdd) this.tkAdd(ST.REWARD.tickets, "story"); S.reward = { gold: ST.REWARD.gold, tickets: ST.REWARD.tickets, card: this.cgTierCard ? this.cgTierCard("rare", "The Joker's own card, given at the end of the Final Night.", new CM.Random(CM.hashSeed(`${this.seed}:story`))) : null };
      this.stNote = { finished: true }; this.cgCelebrate && this.cgCelebrate(3, "You beat the Joker!"); },
    slotSpin(bet) { const r = slot0.call(this, bet); if (r && !r.error) this.stCount("slots", (F, R) => { F.c += 1; const [a, b, c] = r.symbols; return a === b && b === c ? "win" : F.c >= R.n ? "lose" : null; }); return r; },
    bjSettle() { const B = bj0.call(this); if (B && B.results) this.stCount("blackjack", (F, R) => { for (const x of B.results) { if (x.r === "win" || x.r === "blackjack") F.c += 1; else if (x.r === "lose" || x.r === "bust") F.l += 1; } return F.c >= R.n ? "win" : F.l >= R.n ? "lose" : null; }); return B; },
    faEnd(kind) { const out = fa0.call(this, kind); if (kind === "darts") this.stCount("darts", (F, R) => (this.faState("darts").score > R.target ? "win" : "lose")); return out; },
    pkDrop(bet, risk) { const r = pk0.call(this, bet, risk); if (r && !r.error && risk === "high") this.stCount("plinko", (F, R) => { F.c += 1; return r.mult >= 8 ? "win" : F.c >= R.n ? "lose" : null; }); return r; },
    vpDraw() { const r = vp0.call(this), V = this.vpState(); if (V && V.stage === "done") this.stCount("poker", (F, R) => { F.c += 1; if (V.rank >= 0 && V.rank <= 7) F.l += 1; return F.l >= 2 ? "win" : F.c >= R.n ? "lose" : null; }); return r; },
  });
  // the Joker's Own: the story's charm, for the party that finished it
  if (CM.CHARMS) { CM.CHARMS.LIST.push({ id: "own", name: "The Joker's Own", icon: "🃏", what: "The Joker's own card: 3% to hit, 3% more criticals, 5% more gold and experience from fights.", earn: "Win the Final Night of the Joker's story." }); CM.CHARMS.byId.own = CM.CHARMS.LIST[CM.CHARMS.LIST.length - 1];
    const e0 = P.chEarned, h0 = P.hitChance, c0 = P.critChance, m0 = P.jkMul;
    Object.assign(P, { chEarned(id) { return id === "own" ? !!this.stStore().done : e0.call(this, id); },
      hitChance(h) { return Math.min(0.98, h0.call(this, h) + (this.chOn("own") ? 0.03 : 0)); }, critChance(h) { return Math.min(0.75, c0.call(this, h) + (this.chOn("own") ? 0.03 : 0)); },
      jkMul(kind) { return m0.call(this, kind) + ((kind === "gold" || kind === "xp") && this.chOn("own") ? 0.05 : 0); } }); }
  // the golden crown: the story's end opens it whatever the level
  { const w0 = P.wdOpen; P.wdOpen = function (kind, id) { return w0.call(this, kind, id) || (kind === "hat" && id === "goldcrown" && !!this.stStore().done); }; }
  // the Joker's alcove, at the foyer's end on his floor
  if (CM.makeJokerFloor) { const mk0 = CM.makeJokerFloor; CM.makeJokerFloor = function (...a) { const fl = mk0.apply(this, a); fl.things["20,24"] = { type: "cgservice", view: "story", name: "The Joker's alcove" }; return fl; }; }
}
