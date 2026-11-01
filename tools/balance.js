"use strict";
// The house's books (v16.9): plays the Gilded Joker's tables many thousands of times in Node (tools/headless.js) with a
// plain, sensible way of playing each, and measures what each pays back of what is laid, the tickets and the JXP it
// gives for every hundred gold, and its biggest single win. Games of skill (the arcade cabinets, the fairground, the
// pond) are read from their pay tables instead - the level or score that wins the stake back - with a steady hand's
// figures where one can be played. Flags anything that pays back more than it takes, or gives far more tickets than
// the floor's run. Writes BALANCE.md (the report) and src/js/64zzo-odds.js (the figures for the House odds page).
//
//   node tools/balance.js            (about a minute)
//   node tools/balance.js --quick    (fewer rounds)
const fs = require("fs"), path = require("path");
const { load, fixedParty } = require("./headless");
const ROOT = path.join(__dirname, ".."), QUICK = process.argv.includes("--quick"), N = (n) => (QUICK ? Math.ceil(n / 8) : n);
const CM = load(), CG = CM.CG;
const fresh = (seed) => { const g = new CM.Game(); g.newGame(seed, fixedParty(CM), "pauper", "fair", [], "dungeon", { town: true }); g.gold = 1e9; g.saveCasino = null; return g; };
const book = (g) => { const F = g.cgStore(), T = g.tkStore(), J = g.jkStore ? g.jkStore() : { jxp: 0 }; return { w: Object.values(F.wagered).reduce((a, b) => a + b, 0), p: Object.values(F.paid).reduce((a, b) => a + b, 0), t: T.earned || 0, j: J.jxp || 0 }; };
const rows = [];
// a game of chance, played n times by `play`, measured
const measure = (id, how, n, play, opts = {}) => { const g = fresh(`books:${id}:${how}`), b0 = book(g), t0 = Date.now(); let best = 0, plays = 0, s1 = 0, s2 = 0;
  for (let k = 0; k < n; k++) { const g0 = g.gold, a = book(g); play(g, k); const z = book(g), wk = z.w - a.w; plays++; best = Math.max(best, g.gold - g0); if (wk > 0) { const r = (z.p - a.p) / wk; s1 += r; s2 += r * r; } }
  const b1 = book(g), w = b1.w - b0.w, p = b1.p - b0.p; const row = { id, how, kind: "chance", plays, ret: w ? p / w : 0, tk100: w ? (100 * (b1.t - b0.t)) / w : 0, jxp100: w ? (100 * (b1.j - b0.j)) / w : 0, best, se: plays > 1 ? Math.sqrt(Math.max(0, s2 / plays - (s1 / plays) ** 2) / plays) : 0, ...opts };
  rows.push(row); process.stdout.write(`  ${id.padEnd(10)} ${how.padEnd(28)} ${(row.ret * 100).toFixed(1).padStart(6)}%  ${row.tk100.toFixed(1).padStart(5)} tickets/100g  (${((Date.now() - t0) / 1000).toFixed(1)} s)\n`); return row; };
const skill = (id, how, note, extra = {}) => rows.push({ id, how, kind: "skill", note, ...extra });
console.log("The house's books:");
// ---- the tables ----
measure("slots", "10 gold a pull", N(40000), (g) => g.slotSpin(10));
measure("roulette", "10 gold on red", N(40000), (g) => g.rouletteSpin([{ type: "red", n: 0, amount: 10 }]));
measure("roulette", "10 gold on one number", N(40000), (g) => g.rouletteSpin([{ type: "straight", n: 17, amount: 10 }]), { alt: true });
measure("blackjack", "draw to 17, never double", N(20000), (g) => { g.bjDeal(10); let guard = 0; while (g.bjHand() && guard++ < 20) { if (CG.bjValue(g.bjHand().cards).total < 17) g.bjHit(); else g.bjStand(); } });
measure("poker", "hold pairs and better", N(20000), (g) => { g.vpDeal(10); const V = g.vpState(), cnt = {}; V.cards.forEach((c) => (cnt[c.r] = (cnt[c.r] || 0) + 1)); V.cards.forEach((c, i) => { if (cnt[c.r] >= 2) g.vpHold(i); }); g.vpDraw(); });
measure("craps", "10 gold on the pass line", N(20000), (g) => { const why = g.crapsBet("pass", 10); if (why) return; let guard = 0; while (g.crapsState().bets.pass && guard++ < 200) g.crapsRoll(); });
measure("bigwheel", "10 gold on the 1", N(30000), (g) => g.bwSpin({ 1: 10 }));
measure("bigwheel", "10 gold on the Joker", N(30000), (g) => g.bwSpin({ joker: 10 }), { alt: true });
for (const k of ["copper", "silver", "gold"]) measure("scratch", `${k} slips`, N(20000), (g) => { g.scBuy(k); g.scClaim(); }, { alt: k !== "silver" });
for (const r of ["low", "med", "high"]) measure("plinko", `${r} board, 10 gold`, N(30000), (g) => g.pkDrop(10, r), { alt: r !== "med" });
{ let bestP = 0, bestR = 0; for (let pw = 0; pw <= 1.0001; pw += 0.1) { const g = fresh(`books:pc:${pw}`), b0 = book(g); g.pcBuy(400); for (let k = 0; k < 400 && g.pcState().balls > 0; k++) g.pcShoot(pw); g.pcExchange(); const b1 = book(g), r = (b1.p - b0.p) / (b1.w - b0.w); if (r > bestR) { bestR = r; bestP = pw; } }
  measure("pachinko", `the handle at ${Math.round(bestP * 100)}`, N(60), (g) => { g.pcBuy(200); for (let k = 0; k < 200 && g.pcState().balls > 0; k++) g.pcShoot(bestP); g.pcExchange(); }); }   // (each ball bought shot once; what's left is exchanged)
measure("bingo", "four cards, Copper Room", N(3000), (g) => { const r = g.bgBuy("copper", 4, true); if (r && r.error) return; let guard = 0; while (g.bgGame() && g.bgGame().stage === "play" && guard++ < 200) { g.bgDraw(); const G = g.bgGame(); if (G && G.stage === "play" && g.bgDone(G).some(Boolean)) g.bgCall(); } });
{ const LOT = CM.LOT, R = new CM.Random(7); let won = 0, n = N(300000); for (let k = 0; k < n; k++) { const a = LOT.quick(R), b = LOT.quick(R), m = a.filter((x) => b.includes(x)).length; won += m === 6 ? LOT.pot0 : (LOT.PAYS[m] || [0])[0]; }
  rows.push({ id: "lottery", how: "quick picks (jackpot at its start)", kind: "chance", plays: n, ret: won / (n * LOT.price), tk100: 0, jxp100: 0, best: LOT.pot0, note: "more when the jackpot has grown" }); }
{ const P = CM.POND; for (const bait of ["worms", "spinners"]) for (const [hour, when] of [[14, "by day"], [22, "at night"]]) { let gold = 0, tk = 0; const n = N(20000), R = new CM.Random(11);
    for (let k = 0; k < n; k++) { const c = P.pick(0.75, bait, hour, R), f = P.byId[c.id], land = 0.95 - c.fight * 0.3; gold += land * Math.floor(c.kg * f[5]); tk += land * f[6]; }
    const cost = (n * P.BAIT[bait].price) / P.BAIT[bait].casts; rows.push({ id: "pond", how: `${bait} ${when}, cast well out`, kind: "chance", plays: n, ret: gold / cost, tk100: (100 * tk) / cost, jxp100: 0, best: 0, alt: !(bait === "worms" && hour === 14), note: "landing most fish" }); } }
// ---- the fairground: a steady hand ----
{ const FA = CM.FAIR, red = FA.BOTTLES ? FA.BOTTLES.slice().sort((a, b) => b.pts - a.pts)[0] : null, aims = { darts: [0, -0.605], skee: [0, 0.464], rings: red ? [red.x, Math.max(0, Math.min(1, red.y - 0.05))] : [0, 0.5] };
  for (const kind of ["darts", "skee", "rings"]) { const K = FA[kind], even = (K.PAY.find(([, m]) => m >= 1) || [null])[0];
    const row = measure(kind, "a steady hand, aiming high", N(3000), (g) => { g.faStart(kind, 10); let guard = 0; while (g.faState(kind).stage === "play" && guard++ < 40) g.faThrow(kind, aims[kind][0], aims[kind][1]); });
    Object.assign(row, { kind: "fair", even, note: even ? `pays the stake back from ${even} points` : `never quite pays the stake back (${Math.round(K.PAY[K.PAY.length - 1][1] * 100)}% at ${K.PAY[K.PAY.length - 1][0]} points) - the tickets are the prize` }); } }
// ---- the arcade cabinets: by the level reached ----
for (const [id, def] of Object.entries(CM.ARC.reg)) { let sum = 0, L = 0; while (sum < 1 && L < 60) { L += 1; sum += def.pay(L); } const tk = (L * (L + 1)) / 2;
  skill(id, "by the level reached", `the stake comes back once level ${L} is cleared`, { even: L, tkEven: tk, payL1: def.pay(1), name: def.name }); }
// ---- what can't be measured this way ----
const NOTE = { holdem: "against the residents: the house only deals and takes nothing", claudeatro: "a run of poker hands against blinds - skill and jokers", pit: "a hero sent down the pit - pays by how deep", hexwand: "a duel of charges against the dealer - skill",
  cascade: "a coin pusher - prizes over the edge", claw: "a claw machine - skill, with real prizes", mint: "idle - free to play", shelter: "idle - free to play", gemtray: "match-three - pays by the score", mahjong: "free to play", lexicon: "free to play", conduit: "free to play",
  patience: "free to play", traps: "free to play", vault: "free to play - tickets every vault", prizewheel: "free - a spin a day", range: "skill - pays by the round reached", pond: "", runestack: "pays by the level reached", pinball: "pays by the marks made" };
for (const [id, note] of Object.entries(NOTE)) if (note && !rows.some((r) => r.id === id)) skill(id, "", note);
// ---- where the sums are exact, the exact figure (the measured one is still kept) ----
{ const C = (n, k) => { let c = 1; for (let i = 0; i < k; i++) c = (c * (n - i)) / (i + 1); return c; }, set = (id, how, x) => { const r = rows.find((q) => q.id === id && q.how === how); if (r) r.exact = x; };
  set("roulette", "10 gold on red", 36 / 37); set("roulette", "10 gold on one number", 36 / 37); set("craps", "10 gold on the pass line", 244 / 495 * 2);
  const S = CM.LUCK.BW.SLOTS, P = CM.LUCK.BW.PAYS; set("bigwheel", "10 gold on the 1", (S.filter((x) => x === 1).length / S.length) * (P[1] + 1)); set("bigwheel", "10 gold on the Joker", (1 / S.length) * (P.joker + 1));
  for (const r of ["low", "med", "high"]) set("plinko", `${r} board, 10 gold`, CM.PK.RISK[r].reduce((a, m, b) => a + (m * C(CM.PK.rows, b)) / 2 ** CM.PK.rows, 0)); }
// ---- the run of the floor, and the flags ----
const main = rows.filter((r) => r.kind !== "skill" && !r.alt), tkMed = main.map((r) => r.tk100).sort((a, b) => a - b)[Math.floor(main.length / 2)];
for (const r of rows) { r.flags = []; if (r.kind !== "skill" && (r.exact !== undefined ? r.exact > 1 : r.ret > 1 + 2.5 * (r.se || 0)) && r.id !== "pond") r.flags.push(r.kind === "fair" ? "a steady hand wins more than it lays" : "pays back more than it takes"); if (r.kind === "chance" && r.id !== "pond" && r.tk100 > tkMed * 4 && r.tk100 > 8) r.flags.push(`tickets ${(r.tk100 / tkMed).toFixed(1)}x the floor's run`); }
const name = (id) => (CM.ARC.reg[id] ? CM.ARC.reg[id].name : { slots: "The Gilded Reels", roulette: "Roulette", blackjack: "Blackjack", poker: "Jacks or Better", craps: "Bones", bigwheel: "The Joker's Wheel", scratch: "Fortune Slips", plinko: "The Drop Board", pachinko: "The Pin Garden", bingo: "The Bell Hall", lottery: "The Town Lottery", pond: "The Fishing Pond", darts: "The Tavern Board", skee: "Rune-Roll", rings: "Hoop-la" }[id] || id);
const pc = (x) => `${(x * 100).toFixed(1)}%`;
let md = `# The house's books\n\nMade by \`node tools/balance.js\` on ${new Date().toISOString().slice(0, 10)} (v${(fs.readFileSync(path.join(ROOT, "build.py"), "utf8").match(/VERSION = "([^"]+)"/) || [])[1]}).\nEach game of chance was played many thousands of times with a plain, sensible way of playing; the figures are what came back of every 100 gold laid. Games of skill are read from their pay tables.\n\n`;
md += `## Games of chance\n\n| Game | Played as | Rounds | Pays back (±2 s.e.) | Tickets per 100 gold | JXP per 100 gold | Flags |\n|---|---|---:|---:|---:|---:|---|\n`;
for (const r of rows.filter((x) => x.kind === "chance" || x.kind === "fair")) md += `| ${name(r.id)} | ${r.how}${r.note ? ` (${r.note})` : ""} | ${r.plays.toLocaleString("en")} | ${pc(r.ret)}${r.se ? ` ±${(r.se * 200).toFixed(1)}` : ""}${r.exact !== undefined ? ` (exactly ${pc(r.exact)})` : ""} | ${r.tk100.toFixed(1)} | ${r.jxp100.toFixed(1)} | ${r.flags.join("; ") || "-"} |\n`;
md += `\nThe floor's run of tickets: about ${tkMed.toFixed(1)} for every 100 gold laid.\n\n## Games of skill\n\n| Game | Terms |\n|---|---|\n`;
for (const r of rows.filter((x) => x.kind === "skill")) md += `| ${name(r.id)} | ${r.note} |\n`;
const flagged = rows.filter((r) => r.flags && r.flags.length); md += `\n## Flags\n\n${flagged.length ? flagged.map((r) => `- ${name(r.id)} (${r.how}): ${r.flags.join("; ")}`).join("\n") : "None: no game pays back more than it takes, and none gives tickets far out of the floor's run."}\n`;
fs.writeFileSync(path.join(ROOT, "BALANCE.md"), md);
const odds = { made: new Date().toISOString().slice(0, 10), tkRun: Math.round(tkMed * 10) / 10, rows: rows.map((r) => ({ id: r.id, how: r.how, kind: r.kind, ret: r.ret !== undefined ? Math.round((r.exact !== undefined ? r.exact : r.ret) * 1000) / 1000 : null, exact: r.exact !== undefined, tk: r.tk100 !== undefined ? Math.round(r.tk100 * 10) / 10 : null, jxp: r.jxp100 !== undefined ? Math.round(r.jxp100 * 10) / 10 : null, even: r.even || null, note: r.note || "", alt: !!r.alt })) };
fs.writeFileSync(path.join(ROOT, "src", "js", "64zzo-odds.js"), `"use strict";\n// The house's books, as last measured by tools/balance.js (${odds.made}) - read by the House odds page (76zzs-odds.js). Made, not written: run the tool again after changing a table.\nCM.ODDS = ${JSON.stringify(odds)};\n`);
console.log(`\n${rows.length} rows; flags: ${flagged.length}. Wrote BALANCE.md and src/js/64zzo-odds.js.`);
