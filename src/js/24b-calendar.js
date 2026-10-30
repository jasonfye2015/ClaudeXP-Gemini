"use strict";
// The calendar (the eighth big update, phase 7): four seasons by the real date (or one pinned in Settings), written
// into the run at its start; weather by the season and the day of the run; twelve festivals, one a month, in the
// week around the fifteenth, keyed to the calendar the way the weekly seed is. What they do is read by the rules
// through CM.season(game), CM.weather(game) and CM.festival(game); the lines are the lore bible's (LORE.md).
//
//   CM.seasonOfDate(d)               -> "spring" | "summer" | "autumn" | "winter"   (set in 69c-farm.js; the day length below)
//   CM.festivalOfDate(d)             -> a festival id in its week, else null
//   CM.weatherOf(seed, day, season)  -> "clear" | "rain" | "mist" | "wind" | "snow"
//   CM.dateWords(game)               -> "spring, day 3 of the run - the Sowing; rain"
CM.SEASON_WORDS = { spring: "spring", summer: "summer", autumn: "autumn", winter: "winter" };
CM.DAYLIGHT = { spring: [5, 21], summer: [4, 22], autumn: [6, 20], winter: [7, 18] };   // night falls at the second hour, dawn is the first
CM.FESTIVAL_DAYS = [12, 18];                                              // the week around the fifteenth
CM.FESTIVALS = {
  midwinter: { month: 0, name: "Midwinter", what: "the home's hearth gives two rests, and the Lich King's court sits a floor higher (his floor's undead a tenth tougher)", line: "The longest night. The king's court sat late, they say, and sits later." },
  sexton: { month: 1, name: "the Sexton's Day", what: "a candle at the memorial costs no renown", line: "The sexton buried the city's dead for forty years and asked no coin of the poor. One day a year the town asks none either." },
  sowing: { month: 2, name: "the Sowing", what: "seed at the Merchant's House is half its price", line: "What goes into the ground in the Sowing comes up. The hill has always believed it, and the hill is mostly right." },
  letter: { month: 3, name: "the Dwarves' Letter", what: "the forge whets picks for nothing, and sells its picks at half", line: "The letter came up the shaft in a sealed tube: 'We are well. Do not come.' The town keeps the day it came." },
  greening: { month: 4, name: "the Greening", what: "the Wood's nodes give one more", line: "The hill's own: the first week the Wood is green to the top, the town goes out to it with baskets." },
  midsummer: { month: 5, name: "Midsummer", what: "the tavern's round is free, and the townsfolk are out in the square at night", line: "The shortest night, and nobody sleeps through it. There is dancing in the square, badly." },
  forgefire: { month: 6, name: "the Forge Fire", what: "the smith's gold (an enchantment, a grade, a tempering) is half", line: "The hill's own: the week the forge is never let go out, in memory of the one that made the first bell." },
  reaping: { month: 7, name: "the Reaping", what: "the farm's rows grow two stages a dawn", line: "The hill's own: everyone cuts, even the chronicler, who is no use at it." },
  harvest: { month: 8, name: "the Harvest Fair", what: "market day all week (a peddler's cloth in the square), and the farm's rows yield double", line: "The fair came up from the lower town once a year, and stayed when the lower town went under." },
  dead: { month: 9, name: "the Feast of the Dead", what: "the memorial's names are read at the well, a candle costs nothing, and the Ossuary's priests are gentle (a tenth weaker)", line: "The names are read at the well, oldest first. It takes most of the evening now." },
  bells: { month: 10, name: "the Night of Bells", what: "the bell-founder's boy hears one; the regular's gossip is on the house, and a lock is a tenth easier", line: "No bell has rung in the city since the king. One night a year the whole town listens anyway." },
  wassail: { month: 11, name: "the Wassail", what: "the tavern's round sets the heart to full, and comes with beer", line: "The hill's own: the year goes out singing. The tavern's cellar is open, and the smith sings worst." },
};
CM.festivalOfDate = (d) => { d = d || new Date(); const day = d.getDate(); if (day < CM.FESTIVAL_DAYS[0] || day > CM.FESTIVAL_DAYS[1]) return null; return Object.keys(CM.FESTIVALS).find((id) => CM.FESTIVALS[id].month === d.getMonth()) || null; };
CM.festival = (game) => (game && game.festival && CM.FESTIVALS[game.festival] ? game.festival : null);
CM.festivalIs = (game, id) => CM.festival(game) === id;
// the weather: by the seed, the day and the season; it holds a day
CM.WEATHERS = { clear: "clear", rain: "rain", mist: "mist", wind: "wind", snow: "snow" };
CM.WEATHER_ODDS = { spring: ["clear", "rain", "rain", "mist", "wind"], summer: ["clear", "clear", "clear", "wind", "rain"], autumn: ["clear", "mist", "mist", "rain", "wind"], winter: ["clear", "snow", "snow", "mist", "wind"] };
CM.weatherOf = (seed, day, season) => { const odds = CM.WEATHER_ODDS[season] || CM.WEATHER_ODDS.spring; return odds[CM.hashSeed(`${seed}:weather:${day}`) % odds.length]; };
CM.weather = (game) => (game && game.seed !== undefined ? CM.weatherOf(game.seed, CM.dayOf(game), CM.season(game)) : "clear");
CM.WEATHER_WORDS = { clear: "clear", rain: "rain (the river is up: the ford is deep, and the farm drinks)", mist: "mist (the beasts and the party find each other late)", wind: "wind (the beasts do not smell the party coming)", snow: "snow (tracks in the Wood, the river frozen and crossed anywhere, the well frozen)" };
CM.dateWords = (game) => { const f = CM.festival(game); return `${CM.season(game)}, day ${CM.dayOf(game) + 1} of the run${f ? ` - ${CM.FESTIVALS[f].name}` : ""}; ${CM.weather(game)}`; };
// the day's length by the season: the hour the rules read as night
{ const was = CM.isNight; CM.isNight = (game) => { if (!game || !game.season || !CM.DAYLIGHT[game.season]) return was(game); const h = CM.hourOf(game), [dawn, dusk] = CM.DAYLIGHT[game.season]; return h >= dusk || h < dawn; }; }
// a daily's mutators take the season's colour: winter dailies carry Gloom more often, summer dailies Swift
{ const was = CM.mutatorsFor; if (was) CM.mutatorsFor = function (seed) { const out = was(seed), s = String(seed), m = /^daily-(\d{4})-(\d{2})-(\d{2})$/.exec(s); if (!m) return out; const season = CM.seasonOfDate(new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))), want = season === "winter" ? "gloom" : season === "summer" ? "swift" : null; if (want && CM.MUTATORS[want] && !out.includes(want) && CM.hashSeed(`${seed}:season`) % 2 === 0) out[0] = want; return out; }; }
// the chronicler's calendar: the year's months, their festivals, and the runs that fell in each (the Hall of Fame's dates)
CM.MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
CM.calendarOf = (fame) => CM.MONTH_NAMES.map((name, month) => { const id = Object.keys(CM.FESTIVALS).find((k) => CM.FESTIVALS[k].month === month); const runs = (fame || []).filter((e) => e.date && Number(String(e.date).split("/")[0]) - 1 === month); return { month, name, season: CM.seasonOfDate(new Date(2000, month, 15)), festival: id, festivalName: CM.FESTIVALS[id].name, runs: runs.length, crowns: runs.filter((e) => e.won).length }; });
