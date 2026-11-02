"use strict";
// Band landmarks (v40.0, UPGRADE_PLAN_35.md): on the third floor of each of the ten bands, the largest plain room (not a puzzle's) is the
// band's set-piece - the Candle Crypt, the Flooded Nave, the Forge-Hall, the Empty Throne, the Bell Square, the Fairy
// Ring, the Crystal Hall, the Great Crucible, the Skull Wall, the Heart-Root - said once when the party first steps in,
// and drawn by 76zzzzzzzb-landmarks.js. Nothing in the floor moves: the room is only chosen and named.
//   CM.LANDMARKS; floor.landmark = {band, x0, y0, x1, y1, at: [x, y]}; ext("landmarks")[floor] = true once seen
{ const L = CM.LANDMARKS = [
    { name: "the Candle Crypt", enter: "A crypt where someone still keeps the candles: a stone altar banked with them, and stubs burning in every corner. Nobody is here to light them." },
    { name: "the Flooded Nave", enter: "The floor gives way to black water: a nave, flooded to the knee, and a saint's statue standing up out of it with her hands out, as if to say it is all right." },
    { name: "the Forge-Hall", enter: "The Forge-Hall: an anvil the size of a cart, and a hammer still rising and falling on it with no hand on the haft. Sparks every time." },
    { name: "the Empty Throne", enter: "A throne-room, banners still on the walls, and the throne itself empty. The cushion keeps the shape of someone who sat there a very long time." },
    { name: "the Bell Square", enter: "A drowned town's square: the market bell still in its frame, swinging a little in a current you cannot feel, and never quite ringing." },
    { name: "the Fairy Ring", enter: "A ring of pale caps glowing round the room's edge, and in the middle a mushroom taller than a man. Do not step in the ring, says every grandmother. You are already in it." },
    { name: "the Crystal Hall", enter: "The Crystal Hall: crystals the height of a hero standing up out of the floor, each lit from inside, humming a note just under hearing." },
    { name: "the Great Crucible", enter: "The Great Crucible, still pouring: a stream of molten iron falling into a mould no one will ever open. The heat comes at you like a wall." },
    { name: "the Skull Wall", enter: "Skulls stacked shoulder-high in a careful heap, every one turned to face the door. Someone counted them. There is a tally scratched on the floor." },
    { name: "the Heart-Root", enter: "The Heart-Root: a knot of red root as big as a house, beating slow, like something asleep. The whole floor moves with it." },
  ];
  CM.isLandmarkFloor = (n) => n >= 1 && n <= 50 && n % 1 === 0 && n % 5 === 3;
  const key = (x, y) => `${x},${y}`;
  const mf0 = CM.makeFloor; CM.makeFloor = function (number, seed, gen) { const fl = mf0.call(this, number, seed, gen); if (!fl || (fl.special && !["dark", "wading"].includes(fl.special)) || fl.number !== number || !CM.isLandmarkFloor(number) || !fl.rooms) return fl;
    const PZ = ["altar", "mirror", "statue", "sunplate", "sunshaft"], busy = (r) => { for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) { const t = fl.things[key(x, y)]; if (t && (PZ.includes(t.type) || (fl.puzzle && fl.puzzle.chestAt === key(x, y)))) return true; } return false; };
    const rooms = fl.rooms.filter((r) => !r.name && !busy(r) && (r.x1 - r.x0 + 1) >= 3 && (r.y1 - r.y0 + 1) >= 3).sort((a, b) => (b.x1 - b.x0 + 1) * (b.y1 - b.y0 + 1) - (a.x1 - a.x0 + 1) * (a.y1 - a.y0 + 1)); const r = rooms[0]; if (!r) return fl;
    const cx = Math.floor((r.x0 + r.x1) / 2), cy = Math.floor((r.y0 + r.y1) / 2); let at = null, best = 99;
    for (let y = r.y0; y <= r.y1; y++) for (let x = r.x0; x <= r.x1; x++) { if (fl.grid[y][x] !== 0 || fl.things[key(x, y)] || (fl.features || {})[key(x, y)] || (fl.pos[0] === x && fl.pos[1] === y)) continue; const d = Math.abs(x - cx) + Math.abs(y - cy); if (d < best) { best = d; at = [x, y]; } }
    if (at) fl.landmark = { band: CM.themeIndex(number), x0: r.x0, y0: r.y0, x1: r.x1, y1: r.y1, at }; return fl; };
  CM.inLandmark = (fl, x, y) => { const M = fl && fl.landmark; return Boolean(M && x >= M.x0 && x <= M.x1 && y >= M.y0 && y <= M.y1); };
  const G = CM.Game.prototype;
  const look0 = G.look; G.look = function (...a) { const out = look0.apply(this, a), fl = this.floor; if (this.mode === "explore" && fl && fl.landmark && CM.inLandmark(fl, fl.pos[0], fl.pos[1]) && !this.ext("landmarks")[fl.number]) { this.ext("landmarks")[fl.number] = true; const M = L[fl.landmark.band] || L[0]; this.say(M.enter);
      this.tally.landmarks = (this.tally.landmarks || 0) + 1; } return out; };
}
