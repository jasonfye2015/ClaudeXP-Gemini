"use strict";
// The Gilded Joker's gallery (the thirty-eighth big update - v14.8): with twenty-seven tables the row of buttons had
// grown past use, so the floor opens on a gallery instead - a page of cards, each with a little painted picture of its
// table, its name and a line on what it is, filtered by kind (cards and tables, arcade, puzzles, idle and builders,
// prizes) and turned page by page (the arrows, or ← and →). Inside a table the long row gives way to a slim bar: back to
// the gallery, the table before and after, the table's name and the party's gold. Each table's own window is as it
// was; it simply has the room.
CM.CG_INFO = {
  claudeatro: { cat: "tables", line: "Poker hands against blinds, with jokers that bend the rules." },
  slots: { cat: "tables", line: "Three reels, a payline, a joker jackpot." },
  roulette: { cat: "tables", line: "Thirty-seven numbers, a wheel and a ball." },
  blackjack: { cat: "tables", line: "Twenty-one against the dealer." },
  poker: { cat: "tables", line: "Video poker: hold, draw, Jacks or Better." },
  hexwand: { cat: "tables", line: "A wand of live and dud charges against the dealer." },
  pit: { cat: "tables", line: "Send a hero into the 3-D pit to play for the house." },
  runefall: { cat: "arcade", line: "Aim a rune-ball down through the pegs." },
  dash: { cat: "arcade", line: "Hop the lantern across endless lanes." },
  runestack: { cat: "arcade", line: "Falling rune-blocks; clear the lines." },
  manamine: { cat: "arcade", line: "Dig, tether and pop the mine's creatures." },
  glimmer: { cat: "arcade", line: "Eat the motes; flee the Lantern Haunts." },
  swarm: { cat: "arcade", line: "A lantern-skiff against diving Gloomwings." },
  hexmarch: { cat: "arcade", line: "Hold the cellar range against marching hexlings." },
  shatterpane: { cat: "arcade", line: "Break the chapel's stained glass." },
  starstone: { cat: "arcade", line: "Split drifting starstones in a folded void." },
  moatleap: { cat: "arcade", line: "Hop a toad over road and moat." },
  runestep: { cat: "arcade", line: "Light the pyramid's cubes; mind the serpent." },
  pinball: { cat: "arcade", line: "Flippers, bumpers, and a dragon to slay." },
  gemtray: { cat: "puzzles", line: "Swap gems to match three and more." },
  mahjong: { cat: "puzzles", line: "Pair the free tiles until the table is bare." },
  lexicon: { cat: "puzzles", line: "Guess the password on a humming terminal." },
  conduit: { cat: "puzzles", line: "Lay pipes before the mana flows." },
  mint: { cat: "idle", line: "Strike the coin press; hire hands to mint for you." },
  shelter: { cat: "idle", line: "Dig a warren and keep its residents fed." },
  cascade: { cat: "prizes", line: "Drop coins on the pusher; prizes over the edge." },
  claw: { cat: "prizes", line: "Copper, silver and gold claws full of real prizes." },
  wyrm: { cat: "arcade", line: "Feed the wyrm berries; mind its tail." },
  crawler: { cat: "arcade", line: "Shoot the long crawler down through the toadstools." },
  belfry: { cat: "arcade", line: "Climb the bell tower past the troll's kegs." },
  lander: { cat: "arcade", line: "Set the sky-skiff down gently on a lit pad." },
  rampart: { cat: "arcade", line: "Burst the falling embers before they reach the town." },
  glimmerpop: { cat: "arcade", line: "Shoot coloured bubbles; three of a kind pop." },
  craps: { cat: "tables", line: "Dice at the true odds: the line, the field, the place bets." },
  darts: { cat: "fair", line: "Eight rounds of three darts at the tavern board." },
  skee: { cat: "fair", line: "Roll nine balls up the lane into the rings." },
  bard: { cat: "arcade", line: "Strike the notes on the beat; keep the crowd cheering." },
  patience: { cat: "puzzles", line: "Klondike and FreeCell, free to play." },
  traps: { cat: "puzzles", line: "Lift the safe stones; the numbers tell of traps." },
  pachinko: { cat: "luck", line: "Pachinko: balls through the brass pins, and the tulip's Fever." },
  bigwheel: { cat: "luck", line: "Pick a number; round goes the great wheel." },
  scratch: { cat: "luck", line: "Scratch the foil; three alike wins." },
  prizewheel: { cat: "luck", line: "A free spin every day." },
  rings: { cat: "fair", line: "Ten rings over the bottle necks." },
  range: { cat: "fair", line: "A crossbow at tin ducks, dragons and stars." },
};
CM.CG_CATS = [["all", "All"], ["tables", "Cards & tables"], ["arcade", "Arcade"], ["puzzles", "Puzzles"], ["idle", "Idle & builders"], ["luck", "Luck"], ["fair", "Fairground"], ["prizes", "Prizes"]];
// a little picture for each table, painted on a small canvas
CM.CG_THUMB = (() => {
  const bg = (p, w, h, a, b) => { const g = p.createLinearGradient(0, 0, 0, h); g.addColorStop(0, a); g.addColorStop(1, b); p.fillStyle = g; p.fillRect(0, 0, w, h); };
  const card = (p, x, y, s, c, txt, rot = 0) => { p.save(); p.translate(x, y); p.rotate(rot); p.fillStyle = "#F8F0E0"; p.fillRect(-12 * s, -17 * s, 24 * s, 34 * s); p.strokeStyle = "#3A2A10"; p.strokeRect(-12 * s, -17 * s, 24 * s, 34 * s); p.fillStyle = c; p.font = `bold ${14 * s}px Georgia`; p.textAlign = "center"; p.fillText(txt, 0, 5 * s); p.restore(); };
  const circ = (p, x, y, r, c) => { p.fillStyle = c; p.beginPath(); p.arc(x, y, r, 0, Math.PI * 2); p.fill(); };
  return {
    claudeatro: (p, w, h) => { bg(p, w, h, "#1A4A2A", "#0A2A14"); card(p, w / 2 - 34, h / 2 + 4, 1, "#C03030", "A♥", -0.3); card(p, w / 2, h / 2, 1, "#202020", "K♠"); card(p, w / 2 + 34, h / 2 + 4, 1, "#7030A0", "J★", 0.3); },
    slots: (p, w, h) => { bg(p, w, h, "#5A1A1A", "#2A0A0A"); for (let k = 0; k < 3; k++) { p.fillStyle = "#F8F0E0"; p.fillRect(w / 2 - 54 + k * 38, h / 2 - 22, 32, 44); p.fillStyle = "#C02020"; p.font = "bold 24px Georgia"; p.textAlign = "center"; p.fillText("7", w / 2 - 38 + k * 38, h / 2 + 9); } p.strokeStyle = "#F0C040"; p.lineWidth = 2; p.beginPath(); p.moveTo(w / 2 - 60, h / 2); p.lineTo(w / 2 + 60, h / 2); p.stroke(); },
    roulette: (p, w, h) => { bg(p, w, h, "#1A4A2A", "#0A2A14"); for (let k = 0; k < 18; k++) { p.fillStyle = k % 2 ? "#202020" : "#C02020"; p.beginPath(); p.moveTo(w / 2, h / 2); p.arc(w / 2, h / 2, 40, (k * Math.PI) / 9, ((k + 1) * Math.PI) / 9); p.fill(); } circ(p, w / 2, h / 2, 18, "#8A5A2A"); circ(p, w / 2 + 28, h / 2 - 22, 4, "#FFF"); },
    blackjack: (p, w, h) => { bg(p, w, h, "#1A4A2A", "#0A2A14"); card(p, w / 2 - 16, h / 2, 1, "#202020", "A♠", -0.15); card(p, w / 2 + 14, h / 2 + 2, 1, "#C03030", "K♦", 0.15); p.fillStyle = "#F0D070"; p.font = "bold 13px Georgia"; p.fillText("21", 10, 20); },
    poker: (p, w, h) => { bg(p, w, h, "#102050", "#081028"); ["10", "J", "Q", "K", "A"].forEach((t, k) => card(p, w / 2 - 52 + k * 26, h / 2, 0.8, "#C03030", t + "♥")); },
    hexwand: (p, w, h) => { bg(p, w, h, "#2A1A3A", "#140A20"); p.save(); p.translate(w / 2, h / 2); p.rotate(-0.4); p.fillStyle = "#6A3A1A"; p.fillRect(-50, -4, 90, 8); circ(p, 44, 0, 8, "#C080FF"); p.restore(); for (let k = 0; k < 5; k++) circ(p, 30 + k * 18, h - 16, 5, k % 2 ? "#F05040" : "#808080"); },
    pit: (p, w, h) => { bg(p, w, h, "#3A2A10", "#1A1008"); p.fillStyle = "#0A0604"; p.beginPath(); p.ellipse(w / 2, h / 2 + 10, 50, 20, 0, 0, Math.PI * 2); p.fill(); p.fillStyle = "#F0C040"; p.font = "bold 14px Georgia"; p.textAlign = "center"; p.fillText("THE PIT", w / 2, 24); circ(p, w / 2, h / 2 + 4, 6, "#F0C8A0"); },
    runefall: (p, w, h) => { bg(p, w, h, "#10203A", "#081020"); for (let y = 0; y < 4; y++) for (let x = 0; x < 8; x++) circ(p, 20 + x * 18 + (y % 2) * 9, 28 + y * 16, 3, (x + y) % 5 ? "#60A0F0" : "#F08040"); circ(p, w / 2, 12, 5, "#FFF"); },
    dash: (p, w, h) => { bg(p, w, h, "#3A6A30", "#2A4A20"); for (let k = 0; k < 3; k++) { p.fillStyle = "#3A3632"; p.fillRect(0, 22 + k * 26, w, 16); p.fillStyle = "#A04030"; p.fillRect(20 + k * 50, 24 + k * 26, 30, 12); } circ(p, w / 2, h - 10, 7, "#F0D060"); },
    runestack: (p, w, h) => { bg(p, w, h, "#141030", "#080618"); const cols = ["#E05050", "#50A0E0", "#E0C040", "#60C060", "#A060E0"]; for (let y = 0; y < 4; y++) for (let x = 0; x < 8; x++) if ((x * 7 + y * 3) % 5 || y > 2) { p.fillStyle = cols[(x + y) % 5]; p.fillRect(28 + x * 14, h - 18 - y * 14, 13, 13); } p.fillStyle = cols[4]; p.fillRect(56, 14, 13, 13); p.fillRect(70, 14, 13, 13); p.fillRect(70, 28, 13, 13); },
    manamine: (p, w, h) => { bg(p, w, h, "#B07A3A", "#6A3A1E"); p.fillStyle = "#4A7AC0"; p.fillRect(0, 0, w, 18); p.fillStyle = "#140C08"; p.fillRect(60, 18, 12, 60); p.fillRect(20, 60, 110, 12); circ(p, 100, 66, 9, "#A0583A"); circ(p, 66, 40, 6, "#3060B0"); },
    glimmer: (p, w, h) => { bg(p, w, h, "#08100C", "#08100C"); p.strokeStyle = "#3A8A4A"; p.lineWidth = 3; p.strokeRect(10, 10, w - 20, h - 20); p.strokeRect(40, 34, w - 80, h - 68); for (let x = 20; x < w - 10; x += 12) { circ(p, x, 22, 1.8, "#FFE48A"); circ(p, x, h - 22, 1.8, "#FFE48A"); } circ(p, 40, 22, 7, "#30B8A0"); circ(p, 100, h - 22, 7, "#F05030"); circ(p, 128, h - 22, 7, "#60C8F0"); },
    swarm: (p, w, h) => { bg(p, w, h, "#06061A", "#100C24"); for (let k = 0; k < 6; k++) circ(p, 30 + k * 22, 26, 5, k % 2 ? "#B070F0" : "#F09040"); circ(p, w / 2, 46, 7, "#40A050"); p.fillStyle = "#8A5A2A"; p.fillRect(w / 2 - 10, h - 16, 20, 6); circ(p, w / 2, h - 22, 3, "#FFE070"); p.fillStyle = "#80F0FF"; p.fillRect(w / 2 - 1, h - 50, 2, 10); },
    hexmarch: (p, w, h) => { bg(p, w, h, "#0C0A10", "#16121C"); const c = ["#F06080", "#60D0F0", "#A0E060"]; for (let y = 0; y < 3; y++) for (let x = 0; x < 7; x++) { p.fillStyle = c[y]; p.fillRect(24 + x * 18, 14 + y * 14, 12, 8); } p.fillStyle = "#8A8A9A"; for (let k = 0; k < 3; k++) p.fillRect(26 + k * 46, h - 30, 26, 8); p.fillStyle = "#C08A40"; p.fillRect(w / 2 - 6, h - 14, 12, 8); },
    shatterpane: (p, w, h) => { bg(p, w, h, "#120E0C", "#120E0C"); const t = ["#C83C46", "#3C6ED2", "#E6B43C", "#46AA64", "#9650BE"]; for (let y = 0; y < 4; y++) for (let x = 0; x < 8; x++) { p.fillStyle = t[(x * 3 + y) % 5]; p.fillRect(14 + x * 18, 12 + y * 10, 17, 9); } p.fillStyle = "#C0E0F0"; p.fillRect(w / 2 - 22, h - 12, 44, 5); circ(p, w / 2 + 10, h - 34, 4, "#E0FAFF"); },
    starstone: (p, w, h) => { bg(p, w, h, "#04040E", "#140A24"); for (const [x, y, r, c] of [[34, 30, 14, "#8A6AB0"], [120, 26, 10, "#6A7280"], [100, 70, 16, "#7A4A3A"], [40, 76, 6, "#8A6AB0"]]) circ(p, x, y, r, c); p.save(); p.translate(w / 2 - 6, h / 2 + 4); p.rotate(-0.6); p.fillStyle = "#8A5A2A"; p.fillRect(-10, -2, 16, 4); p.fillStyle = "#A0F0FF"; p.beginPath(); p.moveTo(6, -4); p.lineTo(13, 0); p.lineTo(6, 4); p.fill(); p.restore(); },
    moatleap: (p, w, h) => { bg(p, w, h, "#1E4A78", "#3A3632"); p.fillStyle = "#3A7A30"; p.fillRect(0, h / 2 - 6, w, 12); p.fillStyle = "#7A5230"; p.fillRect(20, 14, 60, 12); p.fillRect(90, 32, 50, 12); p.fillStyle = "#8A5A2A"; p.fillRect(30, h - 26, 26, 12); circ(p, w / 2 + 20, h / 2, 7, "#5AAA40"); },
    runestep: (p, w, h) => { bg(p, w, h, "#0C0818", "#1A1028"); for (let r = 0; r < 4; r++) for (let c = 0; c <= r; c++) { const x = w / 2 + (2 * c - r) * 14, y = 14 + r * 20; p.fillStyle = (r + c) % 2 ? "#60E080" : "#5A70C0"; p.beginPath(); p.moveTo(x, y - 7); p.lineTo(x + 14, y); p.lineTo(x, y + 7); p.lineTo(x - 14, y); p.fill(); p.fillStyle = "#2E2448"; p.fillRect(x - 14, y, 28, 10); } circ(p, w / 2 + 14, 26, 6, "#F0A030"); },
    pinball: (p, w, h) => { bg(p, w, h, "#2A1E30", "#1A1420"); circ(p, w / 2, 20, 10, "#3A8A3A"); for (const [x, y] of [[w / 2 - 26, 44], [w / 2 + 26, 44], [w / 2, 62]]) circ(p, x, y, 8, "#6040C0"); p.strokeStyle = "#F0E8E0"; p.lineWidth = 5; p.beginPath(); p.moveTo(w / 2 - 40, h - 14); p.lineTo(w / 2 - 12, h - 6); p.moveTo(w / 2 + 40, h - 14); p.lineTo(w / 2 + 12, h - 6); p.stroke(); circ(p, w / 2 + 6, h - 30, 4, "#D0D8E0"); },
    gemtray: (p, w, h) => { bg(p, w, h, "#2A1A10", "#140A08"); const c = ["#E04050", "#40B0E0", "#60D060", "#E0C040", "#B060E0"]; for (let y = 0; y < 4; y++) for (let x = 0; x < 7; x++) { p.save(); p.translate(28 + x * 18, 18 + y * 18); p.rotate(Math.PI / 4); p.fillStyle = c[(x * 2 + y * 3) % 5]; p.fillRect(-6, -6, 12, 12); p.restore(); } },
    mahjong: (p, w, h) => { bg(p, w, h, "#1A4A2A", "#0A2A14"); for (let k = 0; k < 9; k++) { const x = 24 + (k % 5) * 26, y = 18 + Math.floor(k / 5) * 34; p.fillStyle = "#F8F0E0"; p.fillRect(x, y, 22, 30); p.fillStyle = "#C8B890"; p.fillRect(x + 22, y + 3, 3, 30); p.fillStyle = ["#C03030", "#208040", "#2040A0"][k % 3]; p.font = "bold 14px Georgia"; p.textAlign = "center"; p.fillText("ᚠᚢᚦᚨᚱ"[k % 5], x + 11, y + 20); } },
    lexicon: (p, w, h) => { bg(p, w, h, "#0A140A", "#040A04"); p.fillStyle = "#40F070"; p.font = "10px monospace"; for (let k = 0; k < 6; k++) p.fillText(["0xF3A0 }{!#RUNE&*", "0xF3AC $%LORE@^(+", "0xF3B8 [=BANE;:'", "> LORE", "> 2/5 correct", "> _"][k], 10, 18 + k * 13); },
    conduit: (p, w, h) => { bg(p, w, h, "#1A1A24", "#0E0E16"); p.strokeStyle = "#5A6A80"; for (let x = 10; x < w; x += 20) for (let y = 10; y < h; y += 20) p.strokeRect(x, y, 20, 20); p.strokeStyle = "#60C0F0"; p.lineWidth = 6; p.beginPath(); p.moveTo(20, 20); p.lineTo(80, 20); p.lineTo(80, 60); p.lineTo(140, 60); p.stroke(); },
    mint: (p, w, h) => { bg(p, w, h, "#3A2A10", "#1A1008"); circ(p, w / 2, h / 2, 26, "#F0C040"); circ(p, w / 2, h / 2, 20, "#D0A020"); p.fillStyle = "#6A4A10"; p.font = "bold 20px Georgia"; p.textAlign = "center"; p.fillText("G", w / 2, h / 2 + 7); for (let k = 0; k < 5; k++) circ(p, 20 + k * 30, h - 10, 5, "#F0C040"); },
    shelter: (p, w, h) => { bg(p, w, h, "#4A3A2A", "#2A1E14"); for (let y = 0; y < 3; y++) for (let x = 0; x < 3; x++) { p.fillStyle = ["#3A5A8A", "#8A5A3A", "#5A8A3A"][(x + y) % 3]; p.fillRect(30 + x * 40, 12 + y * 26, 36, 22); circ(p, 40 + x * 40, 28 + y * 26, 3, "#F0C8A0"); } p.fillStyle = "#6A5A4A"; p.fillRect(10, 12, 14, 74); },
    cascade: (p, w, h) => { bg(p, w, h, "#3A1A40", "#1A0A20"); p.fillStyle = "#8A8A9A"; p.fillRect(20, 20, w - 40, 14); for (let k = 0; k < 18; k++) circ(p, 26 + (k * 37) % (w - 50), 46 + ((k * 13) % 30), 6, "#F0C040"); },
    wyrm: (p, w, h) => { bg(p, w, h, "#3A7A2E", "#2A5A20"); const pts = [[20, 60], [40, 60], [60, 50], [80, 40], [100, 40], [120, 50]]; pts.forEach(([x, y], i) => circ(p, x, y, 9 - i * 0.6, i === pts.length - 1 ? "#6AD070" : "#4AA050")); circ(p, 150, 30, 6, "#D02848"); },
    crawler: (p, w, h) => { bg(p, w, h, "#140C08", "#2A1C12"); for (let k = 0; k < 7; k++) circ(p, 30 + k * 14, 40, 7, k ? "#80B040" : "#E0B030"); for (const [x, y] of [[20, 20], [60, 18], [120, 26], [140, 60], [90, 62]]) { p.fillStyle = "#C83828"; p.beginPath(); p.arc(x, y, 6, Math.PI, 0); p.fill(); } p.fillStyle = "#3060C0"; p.beginPath(); p.moveTo(w / 2 - 5, h - 4); p.lineTo(w / 2, h - 16); p.lineTo(w / 2 + 5, h - 4); p.fill(); },
    belfry: (p, w, h) => { bg(p, w, h, "#2A2030", "#140E14"); p.fillStyle = "#7A4A22"; for (let k = 0; k < 4; k++) p.fillRect(k % 2 ? 10 : 30, 18 + k * 18, w - 40, 4); p.strokeStyle = "#8A6A3A"; p.strokeRect(w - 50, 22, 8, 14); circ(p, 60, 30 + 18, 5, "#8A5A28"); circ(p, 30, 12, 7, "#4A6A3A"); p.fillStyle = "#C8962A"; p.beginPath(); p.arc(w / 2, 14, 7, Math.PI, 0); p.fill(); },
    lander: (p, w, h) => { bg(p, w, h, "#2A1A4A", "#F0A050"); p.fillStyle = "#3A2E3A"; p.beginPath(); p.moveTo(0, h); p.lineTo(0, 60); p.lineTo(30, 50); p.lineTo(60, 64); p.lineTo(90, 64); p.lineTo(120, 44); p.lineTo(w, 58); p.lineTo(w, h); p.fill(); p.fillStyle = "#C8A060"; p.fillRect(60, 62, 30, 3); circ(p, 76, 24, 7, "#E0C080"); p.fillStyle = "#FFB040"; p.beginPath(); p.moveTo(73, 34); p.lineTo(76, 44); p.lineTo(79, 34); p.fill(); },
    rampart: (p, w, h) => { bg(p, w, h, "#060818", "#1A1A3A"); p.strokeStyle = "rgba(255,140,60,0.7)"; for (const [x0, x1] of [[20, 50], [90, 70], [150, 120]]) { p.beginPath(); p.moveTo(x0, 0); p.lineTo(x1, 50); p.stroke(); } const g = p.createRadialGradient(100, 40, 0, 100, 40, 16); g.addColorStop(0, "#FFF"); g.addColorStop(1, "rgba(120,180,255,0)"); p.fillStyle = g; p.fillRect(80, 20, 40, 40); p.fillStyle = "#3A3440"; p.fillRect(0, h - 12, w, 12); for (let k = 0; k < 6; k++) { p.fillStyle = "#8A3A2A"; p.fillRect(14 + k * 26, h - 20, 12, 8); } },
    glimmerpop: (p, w, h) => { bg(p, w, h, "#1A2830", "#0A1014"); const c = ["#E04050", "#40A0F0", "#50C060", "#F0C030", "#B060E0"]; for (let r = 0; r < 3; r++) for (let k = 0; k < 9; k++) circ(p, 14 + k * 18 + (r % 2) * 9, 12 + r * 15, 8, c[(k + r * 2) % 5]); circ(p, w / 2, h - 12, 8, "#40A0F0"); },
    craps: (p, w, h) => { bg(p, w, h, "#1E6A40", "#0E4A2A"); for (const [x, y, r, f] of [[60, 44, 0.3, 5], [104, 52, -0.2, 2]]) { p.save(); p.translate(x, y); p.rotate(r); p.fillStyle = "#D02030"; p.fillRect(-16, -16, 32, 32); p.fillStyle = "#FFF"; const pp = { 5: [[-8, -8], [8, -8], [0, 0], [-8, 8], [8, 8]], 2: [[-8, -8], [8, 8]] }[f]; for (const [a, b] of pp) { p.beginPath(); p.arc(a, b, 3, 0, Math.PI * 2); p.fill(); } p.restore(); } p.fillStyle = "#F0E0B0"; p.font = "bold 10px Georgia"; p.fillText("PASS LINE", 10, h - 8); },
    darts: (p, w, h) => { bg(p, w, h, "#3A2414", "#5A3A20"); const cx = w / 2, cy = h / 2; for (let i = 0; i < 20; i++) { const a = (i * Math.PI) / 10; p.fillStyle = i % 2 ? "#E8DCC0" : "#1A1A1A"; p.beginPath(); p.moveTo(cx, cy); p.arc(cx, cy, 34, a, a + Math.PI / 10); p.fill(); } p.strokeStyle = "#C02828"; p.lineWidth = 3; p.beginPath(); p.arc(cx, cy, 21, 0, Math.PI * 2); p.stroke(); p.beginPath(); p.arc(cx, cy, 33, 0, Math.PI * 2); p.stroke(); p.lineWidth = 1; circ(p, cx, cy, 4, "#C02828"); p.fillStyle = "#C03030"; p.fillRect(cx + 8, cy - 14, 18, 3); },
    skee: (p, w, h) => { bg(p, w, h, "#1A1210", "#3A2418"); for (const [r, c] of [[30, "#6A4A2A"], [21, "#7A3A2A"], [13, "#5A3A6A"], [6, "#101010"]]) { p.fillStyle = c; p.beginPath(); p.ellipse(w / 2, 30, r * 1.3, r * 0.8, 0, 0, Math.PI * 2); p.fill(); } p.fillStyle = "#6A4A28"; p.beginPath(); p.moveTo(w / 2 - 20, 56); p.lineTo(w / 2 + 20, 56); p.lineTo(w / 2 + 50, h); p.lineTo(w / 2 - 50, h); p.fill(); circ(p, w / 2 + 6, h - 12, 6, "#E0C090"); },
    bard: (p, w, h) => { bg(p, w, h, "#1A0A14", "#3A1A1A"); const c = ["#E05050", "#50B0F0", "#60D070", "#F0C040"]; for (let i = 0; i < 4; i++) { p.fillStyle = c[i] + "33"; p.fillRect(40 + i * 24, 0, 20, h - 16); circ(p, 50 + i * 24, h - 16, 8, c[i]); circ(p, 50 + i * 24, 14 + ((i * 23) % 40), 6, c[i]); } },
    patience: (p, w, h) => { bg(p, w, h, "#2A7A4A", "#0E3A20"); for (let i = 0; i < 6; i++) { const x = 12 + i * 26; for (let k = 0; k <= i % 4; k++) { p.fillStyle = k === i % 4 ? "#FBF6E8" : "#7A1A2A"; p.fillRect(x, 26 + k * 8, 22, 30); p.strokeStyle = "rgba(0,0,0,0.3)"; p.strokeRect(x, 26 + k * 8, 22, 30); } } p.fillStyle = "#C02030"; p.font = "bold 12px Georgia"; p.fillText("A♥", 120, 50); },
    traps: (p, w, h) => { bg(p, w, h, "#1A140E", "#1A140E"); const N = ["", "#4A80F0", "#40B050", "#E04040"]; for (let y = 0; y < 4; y++) for (let x = 0; x < 8; x++) { const X = 6 + x * 20, Y = 4 + y * 20, open = (x + y * 3) % 4 === 0 || (x > 3 && y > 1); p.fillStyle = open ? "#3A2E22" : "#8A7E70"; p.fillRect(X, Y, 18, 18); if (open && (x + y) % 3) { p.fillStyle = N[(x + y) % 3 + 1]; p.font = "bold 12px Georgia"; p.fillText(String((x + y) % 3), X + 5, Y + 14); } } p.fillStyle = "#C02830"; p.beginPath(); p.moveTo(30, 30); p.lineTo(40, 34); p.lineTo(30, 38); p.fill(); },
    pachinko: (p, w, h) => { bg(p, w, h, "#1A1440", "#5A2A3A"); for (let r = 0; r < 4; r++) for (let x = 14 + (r % 2) * 8; x < w - 10; x += 16) circ(p, x, 18 + r * 14, 2, "#F0D070"); circ(p, 60, 40, 3.5, "#D0D8E8"); circ(p, 110, 54, 3.5, "#D0D8E8"); p.fillStyle = "#E05090"; p.beginPath(); p.ellipse(w / 2 - 5, h - 14, 4, 8, -0.4, 0, Math.PI * 2); p.ellipse(w / 2 + 5, h - 14, 4, 8, 0.4, 0, Math.PI * 2); p.fill(); },
    bigwheel: (p, w, h) => { bg(p, w, h, "#3A1A30", "#1A0A14"); const c = ["#E8DCC0", "#60A0E0", "#60C070", "#E07040", "#B060E0", "#F0C040"]; for (let i = 0; i < 24; i++) { p.fillStyle = c[i % 6]; p.beginPath(); p.moveTo(w / 2, h / 2 + 4); p.arc(w / 2, h / 2 + 4, 36, (i * Math.PI) / 12, ((i + 1) * Math.PI) / 12); p.fill(); } circ(p, w / 2, h / 2 + 4, 10, "#5A2A6A"); p.fillStyle = "#6A3A1A"; p.beginPath(); p.moveTo(w / 2 - 5, 0); p.lineTo(w / 2 + 5, 0); p.lineTo(w / 2, 12); p.fill(); },
    scratch: (p, w, h) => { bg(p, w, h, "#F0C850", "#8A6010"); p.fillStyle = "#FBF4E0"; p.fillRect(30, 14, w - 60, h - 24); for (let i = 0; i < 9; i++) { const x = 34 + (i % 3) * ((w - 68) / 3), y = 18 + Math.floor(i / 3) * ((h - 32) / 3); p.fillStyle = i % 4 === 1 ? "#FBF4E0" : "#B8BCC8"; p.fillRect(x, y, (w - 74) / 3, (h - 38) / 3); if (i % 4 === 1) { p.fillStyle = "#3A2408"; p.font = "bold 12px Georgia"; p.fillText("50", x + 10, y + 16); } } },
    prizewheel: (p, w, h) => { bg(p, w, h, "#2A4A6A", "#1A2A40"); const c = ["#E05050", "#F0A030", "#F0D040", "#60C060", "#40A0E0", "#8060D0", "#E060B0", "#40C0B0"]; for (let i = 0; i < 8; i++) { p.fillStyle = c[i]; p.beginPath(); p.moveTo(w / 2, h / 2); p.arc(w / 2, h / 2, 34, (i * Math.PI) / 4, ((i + 1) * Math.PI) / 4); p.fill(); } circ(p, w / 2, h / 2, 6, "#F0C040"); p.fillStyle = "#FFE070"; p.font = "bold 10px Georgia"; p.fillText("FREE", 8, 14); },
    rings: (p, w, h) => { bg(p, w, h, "#C03040", "#5A1A20"); p.fillStyle = "#6A4A2A"; p.beginPath(); p.moveTo(20, h - 6); p.lineTo(w - 20, h - 6); p.lineTo(w - 40, 30); p.lineTo(40, 30); p.fill(); const c = ["#D0A020", "#3A70C0", "#3A9A50"]; for (let r = 0; r < 3; r++) for (let k = 0; k < 5; k++) { p.fillStyle = r === 0 && k === 2 ? "#C02830" : c[r]; p.fillRect(50 + k * 18 - r * 4 + r * 0, 32 + r * 14, 5, 12); } p.strokeStyle = "#E0B070"; p.lineWidth = 3; p.beginPath(); p.ellipse(w / 2 + 20, 20, 9, 4, 0, 0, Math.PI * 2); p.stroke(); p.lineWidth = 1; },
    range: (p, w, h) => { bg(p, w, h, "#1A2448", "#4A3050"); p.fillStyle = "#B08A40"; p.fillRect(0, 30, w, 3); p.fillRect(0, 56, w, 3); circ(p, 40, 22, 8, "#F0D040"); circ(p, 100, 48, 7, "#4AA050"); p.fillStyle = "#FFD840"; p.beginPath(); for (let k = 0; k < 10; k++) { const r = k % 2 ? 3 : 7, a = (k * Math.PI) / 5; p.lineTo(140 + Math.cos(a) * r, 22 + Math.sin(a) * r); } p.fill(); p.strokeStyle = "#F04030"; p.beginPath(); p.arc(100, 48, 10, 0, Math.PI * 2); p.stroke(); p.fillStyle = "#3A80C0"; p.fillRect(0, h - 10, w, 10); },
    claw: (p, w, h) => { bg(p, w, h, "#2A1A40", "#4A1A30"); p.strokeStyle = "#CCC"; p.beginPath(); p.moveTo(w / 2, 4); p.lineTo(w / 2, 30); p.stroke(); p.strokeStyle = "#B06A3A"; p.lineWidth = 3; p.beginPath(); p.moveTo(w / 2 - 8, 42); p.lineTo(w / 2, 30); p.lineTo(w / 2 + 8, 42); p.stroke(); for (const [x, c] of [[30, "#B08040"], [60, "#3A5AA0"], [100, "#D0D8E8"], [130, "#F0E8D0"]]) circ(p, x, h - 18, 10, c); },
  };
})();
{ const r1 = CM.UI.prototype.renderCasino, open1 = CM.UI.prototype.openCasino, PER = 12;
  Object.assign(CM.UI.prototype, {
    // the floor opens on the gallery (unless something asked for a table: ui.cgOpenTo)
    openCasino() { this.cgView = this.cgOpenTo || "gallery"; this.cgOpenTo = null; open1.call(this); },
    renderCasino() { if (this.cgView === "gallery") return this.cgGallery(this.$("#casino-body")); return r1.call(this); },
    // inside a table: a slim bar - the gallery, the tables either side, the name, the gold
    cgNav(box) {
      const list = CM.CG_TABLES, i = Math.max(0, list.findIndex(([id]) => id === (this.cgView || "claudeatro"))), [, name] = list[i], prev = list[(i - 1 + list.length) % list.length], next = list[(i + 1) % list.length];
      const nav = document.createElement("div"); nav.className = "cgnav cgbar";
      nav.innerHTML = `<button data-cggal>◀ All games</button><button data-cgv="${prev[0]}" title="${prev[1]}">‹</button><span class="cgname">${name}</span><button data-cgv="${next[0]}" title="${next[1]}">›</button><span class="cggold">${this.game.gold} gold</span>`;
      box.prepend(nav);
      nav.querySelector("[data-cggal]").addEventListener("click", () => { if (this.cgBusy) return; this.cgView = "gallery"; this.cgNote = ""; this.caSfx("cardplace", 0.3); this.renderCasino(); });
      nav.querySelectorAll("[data-cgv]").forEach((b) => b.addEventListener("click", () => { if (this.cgBusy) return; this.cgView = b.dataset.cgv; this.cgNote = ""; this.caSfx("cardplace", 0.3); this.renderCasino(); }));
    },
    cgGallery(box) {
      const cat = this.cgCat || "all", all = CM.CG_TABLES.filter(([id]) => cat === "all" || (CM.CG_INFO[id] || {}).cat === cat), pages = Math.max(1, Math.ceil(all.length / PER)), page = this.cgPage = Math.max(0, Math.min(pages - 1, this.cgPage || 0)), shown = all.slice(page * PER, page * PER + PER), F = this.game.cgStore();
      box.innerHTML = `<div class="cggallery"><div class="cghead"><h3>The Gilded Joker</h3><span class="cgsub">${CM.CG_TABLES.length} tables on the floor</span><span class="cggold">${this.game.gold} gold</span></div>
        <div class="cgcats">${CM.CG_CATS.map(([k, n]) => `<button data-cgcat="${k}" class="${k === cat ? "primary" : ""}">${n}</button>`).join("")}</div>
        <div class="cggrid">${shown.map(([id, name]) => { const info = CM.CG_INFO[id] || { line: "" }, played = (F.played || {})[id]; return `<button class="cgcard" data-cgopen="${id}"><canvas width="176" height="82" data-cgthumb="${id}"></canvas><b>${name}</b><span>${info.line}</span>${played ? `<i>played ${played}</i>` : ""}</button>`; }).join("")}</div>
        <div class="cgpager"><button data-cgpg="-1" ${page === 0 ? "disabled" : ""}>◀ Back</button><span>Page ${page + 1} of ${pages}</span><button data-cgpg="1" ${page >= pages - 1 ? "disabled" : ""}>Next ▶</button></div>
        <div class="row"><button data-leave>Leave the Joker</button></div></div>`;
      box.querySelectorAll("[data-cgthumb]").forEach((c) => { const f = CM.CG_THUMB[c.dataset.cgthumb], p = c.getContext("2d"); if (f) f(p, c.width, c.height); else { p.fillStyle = "#2A1A30"; p.fillRect(0, 0, c.width, c.height); p.fillStyle = "#F0C040"; p.font = "bold 28px Georgia"; p.textAlign = "center"; p.fillText("?", c.width / 2, c.height / 2 + 10); } });
      box.querySelectorAll("[data-cgopen]").forEach((b) => b.addEventListener("click", () => { this.cgView = b.dataset.cgopen; this.cgNote = ""; this.caSfx("cardplace", 0.35); this.renderCasino(); }));
      box.querySelectorAll("[data-cgcat]").forEach((b) => b.addEventListener("click", () => { this.cgCat = b.dataset.cgcat; this.cgPage = 0; this.caSfx("card", 0.25); this.renderCasino(); }));
      box.querySelectorAll("[data-cgpg]").forEach((b) => b.addEventListener("click", () => { this.cgPage = page + Number(b.dataset.cgpg); this.caSfx("card", 0.3, 1.2); this.renderCasino(); }));
      box.querySelector("[data-leave]").addEventListener("click", () => this.closeDialogs());
      if (!this.cgGalKeys) { this.cgGalKeys = (e) => { if (this.cgView !== "gallery" || !this.dialogOpen() || !this.$("#casino-body .cggallery")) return; const d = e.code === "ArrowRight" ? 1 : e.code === "ArrowLeft" ? -1 : 0; if (!d) return; e.preventDefault(); this.cgPage = (this.cgPage || 0) + d; this.renderCasino(); }; window.addEventListener("keydown", this.cgGalKeys); }
    },
  });
}
