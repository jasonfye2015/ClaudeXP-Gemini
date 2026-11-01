"use strict";
// Bones (v15.7): the Gilded Joker's dice table - craps, at the true casino odds. The shooter throws two dice. On the
// come-out roll a 7 or 11 wins the pass line, 2, 3 or 12 loses it; any other number becomes the point, and the shooter
// throws on until the point comes again (the pass line wins) or a 7 (it loses - a seven-out). Don't Pass is the other
// side (12 on the come-out is a push). Behind a pass bet, once the point is on, the odds pay true - 2 to 1 on 4 and 10,
// 3 to 2 on 5 and 9, 6 to 5 on 6 and 8 - up to three times the pass bet. The Field pays on 2, 3, 4, 9, 10, 11 and 12
// (double on 2, triple on 12) for one roll; Place 6 and Place 8 pay 7 to 6 each time their number comes while the point
// is on, until a seven; Any Seven pays 4 to 1 for one roll. A shooter who makes four points before sevening out wins a
// Claudescryption card. Window: 76zp-craps.js.
CM.CRAPS = {
  BETS: { pass: "Pass Line", dont: "Don't Pass", odds: "Odds", field: "Field", place6: "Place 6", place8: "Place 8", seven: "Any Seven" },
  ODDS: { 4: [2, 1], 10: [2, 1], 5: [3, 2], 9: [3, 2], 6: [6, 5], 8: [6, 5] }, hotHand: 4,
};
{ const CR = CM.CRAPS;
  Object.assign(CM.Game.prototype, {
    crapsState() { const F = this.cgStore(); F.craps = F.craps || { point: 0, bets: {}, made: 0, rolls: 0, last: null }; return F.craps; },
    // a chip on a spot: what is allowed when
    crapsBet(type, amount) {
      const K = this.crapsState(), B = K.bets; amount = Math.floor(amount || 0); if (!CR.BETS[type] || amount < 1) return "Choose a chip first.";
      if ((type === "pass" || type === "dont") && K.point) return "The line takes bets on the come-out roll only.";
      if (type === "odds") { if (!K.point || !B.pass) return "Odds go behind a pass bet, once the point is on."; if ((B.odds || 0) + amount > B.pass * 3) return `The odds take up to three times the pass bet (${B.pass * 3}).`; }
      if ((type === "place6" || type === "place8") && amount % 6) return "Place bets go in sixes, to pay 7 to 6.";
      const why = this.cgStake("craps", amount); if (why) return why; B[type] = (B[type] || 0) + amount; this.saveCasino && this.saveCasino(); return "";
    },
    crapsTakeDown(type) { const K = this.crapsState(), B = K.bets; if (!(type === "place6" || type === "place8") || !B[type]) return 0; const v = B[type]; delete B[type]; this.gold += v; this.saveCasino && this.saveCasino(); return v; },
    crapsRoll() {
      const K = this.crapsState(), B = K.bets; if (!Object.values(B).some((v) => v > 0)) return { error: "Put a bet on the table first." };
      const R = this.cgRnd("craps"), d = [R.int(1, 6), R.int(1, 6)], s = d[0] + d[1], res = []; let back = 0, card = null; K.rolls += 1;
      const win = (type, mult) => { const v = B[type], w = Math.floor(v * mult); back += v + w; res.push({ type, won: v + w }); delete B[type]; }, lose = (type) => { res.push({ type, lost: B[type] }); delete B[type]; }, push = (type) => { back += B[type]; res.push({ type, push: B[type] }); delete B[type]; };
      // one-roll bets
      if (B.field) { if (s === 2) win("field", 2); else if (s === 12) win("field", 3); else if ([3, 4, 9, 10, 11].includes(s)) win("field", 1); else lose("field"); }
      if (B.seven) { if (s === 7) win("seven", 4); else lose("seven"); }
      const was = K.point;
      if (!K.point) {
        if (s === 7 || s === 11) { if (B.pass) win("pass", 1); if (B.dont) lose("dont"); }
        else if (s === 2 || s === 3) { if (B.pass) lose("pass"); if (B.dont) win("dont", 1); }
        else if (s === 12) { if (B.pass) lose("pass"); if (B.dont) push("dont"); }
        else K.point = s;
      } else {
        for (const t of ["place6", "place8"]) if (B[t] && s === Number(t.slice(5))) { const w = Math.floor(B[t] * 7 / 6); back += w; res.push({ type: t, won: w, stays: true }); }
        if (s === K.point) { if (B.pass) win("pass", 1); if (B.odds) { const [a, b] = CR.ODDS[s]; win("odds", a / b); } if (B.dont) lose("dont"); K.made += 1; K.point = 0; if (K.made === CR.hotHand) card = this.cgCard(false, "A hot shooter at Bones: four points made!", R); }
        else if (s === 7) { for (const t of ["pass", "odds", "place6", "place8"]) if (B[t]) lose(t); if (B.dont) win("dont", 1); K.point = 0; K.made = 0; }
      }
      if (back) this.cgPay("craps", back); K.last = { d, s, back, point: K.point, was };
      this.saveCasino && this.saveCasino(); this.emit("change"); return { dice: d, sum: s, res, back, point: K.point, was, sevenOut: was && s === 7, made: was && s === was, card };
    },
  });
}
