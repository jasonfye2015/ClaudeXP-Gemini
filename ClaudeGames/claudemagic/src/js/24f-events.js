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
{ const WX = CM.WX = { kinds: ["clear", "cloud", "rain", "storm", "mist", "wind", "snow", "heat", "aurora"], clearMin: 60, clearMax: 360, eventMin: 120, eventMax: 360, ramp: 20, nightClear: 0.8,
    odds: { spring: { cloud: 3, rain: 4, storm: 1, mist: 2, wind: 2, snow: 0, heat: 0 }, summer: { cloud: 2, rain: 2, storm: 2, mist: 1, wind: 2, snow: 0, heat: 3 }, autumn: { cloud: 3, rain: 3, storm: 1, mist: 3, wind: 3, snow: 0, heat: 0 }, winter: { cloud: 3, rain: 1, storm: 0, mist: 2, wind: 3, snow: 4, heat: 0 } },
    word: { clear: "clear", cloud: "clear", rain: "rain", storm: "rain", mist: "mist", wind: "wind", snow: "snow", heat: "clear", aurora: "clear" },
    windSpeed: { clear: 0.15, cloud: 0.25, rain: 0.45, storm: 0.85, mist: 0.05, wind: 1.0, snow: 0.35, heat: 0.1, aurora: 0.1 } };
  const rnd = () => (CM.wxRandom ? CM.wxRandom() : Math.random()), between = (a, b) => a + rnd() * (b - a);
  const hourAt = (clock) => ((CM.CLOCK.start + clock) % CM.CLOCK.day) / 60;
  const nightAt = (game, clock) => { const [dawn, dusk] = CM.daylightOf(game), h = hourAt(clock); return h >= dusk || h < dawn; };
  CM.weatherDayWord = (game) => (game && game.seed !== undefined ? CM.weatherOf(game.seed, CM.dayOf(game), CM.season(game)) : "clear");
  const pickKind = (game, at) => { const season = CM.season(game), odds = Object.assign({}, WX.odds[season] || WX.odds.spring), lean = CM.weatherDayWord(game), h = hourAt(at), night = nightAt(game, at);
    if (lean === "rain") { odds.rain *= 2; odds.storm = (odds.storm || 0.5) * 2; } else if (odds[lean] !== undefined) odds[lean] *= 2;
    if (!(h >= 12 && h < 17)) odds.heat = 0; if (night) { odds.heat = 0; odds.storm *= 0.5; }
    if (night && season === "winter" && rnd() < 0.3) return "aurora";
    const total = Object.values(odds).reduce((a, b) => a + b, 0); let r = rnd() * total; for (const [k, w] of Object.entries(odds)) { r -= w; if (r < 0) return k; } return "cloud"; };
  const roll = (game, at, after) => { const night = nightAt(game, at);
    if (after !== "clear" || (night && rnd() < WX.nightClear)) { const len = Math.round(between(WX.clearMin, WX.clearMax) * (night ? 1.6 : 1)); return { kind: "clear", strength: 1, from: at, until: at + len }; }
    const kind = pickKind(game, at), len = Math.round(between(WX.eventMin, WX.eventMax)), strength = kind === "aurora" ? between(0.5, 1) : Math.min(1, between(0.45, 1.05));
    return { kind, strength, from: at, until: at + len }; };
  CM.weatherStep = (game) => { if (!game || !game.ext) return null; const W = game.ext("wx"), t = CM.clockOf(game);
    if (!W.cur) { W.cur = { kind: "clear", strength: 1, from: t, until: t + Math.round(between(30, 120)) }; W.next = roll(game, W.cur.until, "clear"); }
    let guard = 0; while (t >= W.cur.until && guard++ < 200) { W.cur = W.next && W.next.from === W.cur.until ? W.next : roll(game, W.cur.until, W.cur.kind); W.next = roll(game, W.cur.until, W.cur.kind); }
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
