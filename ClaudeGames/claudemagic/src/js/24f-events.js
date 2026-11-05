"use strict";
// The weather, live (v72.0, UPGRADE_PLAN_61.md part 2): the weather is events now, not one word a day. An event - rain,
// a storm, mist, wind, snow, cloud, heat, an aurora - lasts two to six game hours and comes in and goes out over
// twenty minutes; between events the sky is clear for one to six hours (longer at night, which leans clear). When an
// event ends the next is rolled on the spot (no script, no seed: the dice are thrown when the sky changes), by the
// season, the hour and the day's leaning - the day's old word, which doubles its kind's odds. The state lives in the
// run (game.ext("wx")) and is saved with it. CM.weather(game) answers the event's word (rain, mist, wind, snow or
// clear) so everything that read the day's word follows the live sky; CM.weatherNow gives the whole of it.
//   CM.weatherStep(game)      rolls what's due (idempotent; the frame loop and the clock's tick call it)
//   CM.weatherNow(game)       -> { kind, strength 0..1 (ramped), word, from, until, wind: { speed, dir } }
//   CM.nextWeather(game)      -> { kind, strength, from, until, inMinutes }
//   CM.weatherDayWord(game)   the day's leaning, the old word
{ const WX = CM.WX = { kinds: ["clear", "cloud", "rain", "storm", "mist", "wind", "snow", "heat", "aurora", "tornado"], tornadoMin: 60, tornadoMax: 120, tornadoSpeed: 0.5, afterRainMinutes: 90, clearMin: 60, clearMax: 360, eventMin: 120, eventMax: 360, ramp: 20, nightClear: 0.8,
    odds: { spring: { cloud: 3, rain: 4, storm: 1, mist: 2, wind: 2, snow: 0, heat: 0, tornado: 0.15 }, summer: { cloud: 2, rain: 2, storm: 2, mist: 1, wind: 2, snow: 0, heat: 3, tornado: 0.3 }, autumn: { cloud: 3, rain: 3, storm: 1, mist: 3, wind: 3, snow: 0, heat: 0, tornado: 0.4 }, winter: { cloud: 3, rain: 1, storm: 0, mist: 2, wind: 3, snow: 4, heat: 0, tornado: 0 } },
    word: { clear: "clear", cloud: "clear", rain: "rain", storm: "rain", mist: "mist", wind: "wind", snow: "snow", heat: "clear", aurora: "clear", tornado: "wind" },
    windSpeed: { clear: 0.15, cloud: 0.25, rain: 0.45, storm: 0.85, mist: 0.05, wind: 1.0, snow: 0.35, heat: 0.1, aurora: 0.1, tornado: 1.0 } };
  const rnd = () => (CM.wxRandom ? CM.wxRandom() : Math.random()), between = (a, b) => a + rnd() * (b - a);
  const hourAt = (clock) => ((CM.CLOCK.start + clock) % CM.CLOCK.day) / 60;
  const nightAt = (game, clock) => { const [dawn, dusk] = CM.daylightOf(game), h = hourAt(clock); return h >= dusk || h < dawn; };
  CM.weatherDayWord = (game) => (game && game.seed !== undefined ? CM.weatherOf(game.seed, CM.dayOf(game), CM.season(game)) : "clear");
  const pickKind = (game, at) => { const season = CM.season(game), odds = Object.assign({}, WX.odds[season] || WX.odds.spring), lean = CM.weatherDayWord(game), h = hourAt(at), night = nightAt(game, at);
    if (lean === "rain") { odds.rain *= 2; odds.storm = (odds.storm || 0.5) * 2; } else if (odds[lean] !== undefined) odds[lean] *= 2;
    if (!(h >= 12 && h < 17)) odds.heat = 0; if (night) { odds.heat = 0; odds.storm *= 0.5; odds.tornado = 0; }   // (a tornado by day, when it can be seen coming)
    if (night && season === "winter" && rnd() < 0.3) return "aurora";
    const total = Object.values(odds).reduce((a, b) => a + b, 0); let r = rnd() * total; for (const [k, w] of Object.entries(odds)) { r -= w; if (r < 0) return k; } return "cloud"; };
  const roll = (game, at, after) => { const night = nightAt(game, at);
    if (after !== "clear" || (night && rnd() < WX.nightClear)) { const len = Math.round(between(WX.clearMin, WX.clearMax) * (night ? 1.6 : 1)); return { kind: "clear", strength: 1, from: at, until: at + len }; }
    const kind = pickKind(game, at), len = Math.round(kind === "tornado" ? between(WX.tornadoMin, WX.tornadoMax) : between(WX.eventMin, WX.eventMax)), strength = kind === "aurora" ? between(0.5, 1) : Math.min(1, between(0.45, 1.05));
    const ev = { kind, strength, from: at, until: at + len }; if (kind === "tornado") { const a = rnd() * Math.PI * 2; ev.twister = { x: 0, y: 0, dx: Math.cos(a), dy: Math.sin(a), placed: false }; } return ev; };
  // (v73.0) the twister: a tornado has a place that crosses the floor along its way at WX.tornadoSpeed squares a minute, from an edge, placed when it first starts on a floor
  CM.twisterNow = (game) => { const W = game && game.tally && game.tally.ext && game.tally.ext.wx, c = W && W.cur; if (!c || c.kind !== "tornado" || !c.twister || !game.floor || !(game.floor.number === 0 || game.floor.number === -1)) return null;
    const T = c.twister, fl = game.floor, N = fl.grid.length, t = CM.clockOf(game) - c.from;
    if (!T.placed || T.floor !== fl.number) { const cx = N / 2, cy = N / 2, R = N * 0.55; T.x0 = cx - T.dx * R; T.y0 = cy - T.dy * R; T.placed = true; T.floor = fl.number; }   // (it comes in from the edge on the wind's side and crosses the middle)
    const d = Math.min(t * WX.tornadoSpeed, N * 1.1); T.x = T.x0 + T.dx * d; T.y = T.y0 + T.dy * d; return { x: T.x, y: T.y, dx: T.dx, dy: T.dy, minutes: t, strength: c.strength, inside: T.x >= 0 && T.y >= 0 && T.x < N && T.y < N }; };
  // (v73.0) the sky's glow after rain: 1 in the minutes after a rain or a storm ends, falling to 0 over WX.afterRainMinutes
  CM.afterRain = (game) => { const W = game && game.tally && game.tally.ext && game.tally.ext.wx; if (!W || !W.prev || !(W.prev.kind === "rain" || W.prev.kind === "storm") || !W.cur || W.cur.kind !== "clear") return 0; const m = CM.clockOf(game) - W.prev.until; return m < 0 ? 0 : Math.max(0, 1 - m / WX.afterRainMinutes); };
  // (v73.0) the mist's sight: one square in a dense mist, two in a light one, the usual four otherwise
  CM.mistSightNow = (game) => { const W = game && game.tally && game.tally.ext && game.tally.ext.wx, c = W && W.cur; if (!c || c.kind !== "mist") return null; const now = CM.weatherNow(game); return now.strength > 0.7 ? 1 : 2; };
  CM.weatherStep = (game) => { if (!game || !game.ext) return null; const W = game.ext("wx"), t = CM.clockOf(game);
    if (!W.cur) { W.cur = { kind: "clear", strength: 1, from: t, until: t + Math.round(between(30, 120)) }; W.next = roll(game, W.cur.until, "clear"); }
    let guard = 0; while (t >= W.cur.until && guard++ < 200) { W.prev = W.cur; W.cur = W.next && W.next.from === W.cur.until ? W.next : roll(game, W.cur.until, W.cur.kind); W.next = roll(game, W.cur.until, W.cur.kind); }
    return W; };
  CM.weatherNow = (game) => { const W = CM.weatherStep(game); if (!W) return { kind: "clear", strength: 0, word: "clear", from: 0, until: 0, wind: { speed: 0.15, dir: [1, 0] } };
    const c = W.cur, t = CM.clockOf(game), k = c.kind === "clear" ? 0 : Math.max(0, Math.min(1, (t - c.from) / WX.ramp, (c.until - t) / WX.ramp)) * c.strength;
    const dir = CM.windDir ? CM.windDir(game) : [1, 0]; return { kind: c.kind, strength: k, word: WX.word[c.kind] || "clear", from: c.from, until: c.until, wind: { speed: 0.12 + (WX.windSpeed[c.kind] - 0.12) * (c.kind === "clear" ? 1 : Math.max(0.2, k)), dir } }; };
  CM.nextWeather = (game) => { const W = CM.weatherStep(game); if (!W || !W.next) return null; const n = W.next; return Object.assign({ inMinutes: Math.max(0, n.from - CM.clockOf(game)) }, n); };
  CM.windDir = (game) => { const d = CM.dayOf ? CM.dayOf(game) : 0, a = (CM.hashSeed(`${game && game.seed}:wind:${d}`) % 360) * Math.PI / 180; return [Math.cos(a), Math.sin(a)]; };   // (the wind's way, a day's)
  // the day's word gives way to the live sky's, once the run has one
  { const w0 = CM.weather; CM.weather = (game) => { const W = game && game.ext && game.tally && game.tally.ext && game.tally.ext.wx; return W && W.cur ? WX.word[W.cur.kind] || "clear" : w0(game); }; }
  { const t0 = CM.tickClock; CM.tickClock = (game, minutes) => { t0(game, minutes); if (game && game.ext) CM.weatherStep(game); }; }
}
