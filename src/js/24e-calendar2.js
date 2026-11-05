"use strict";
// The calendar named, and the clock that runs (v71.0, UPGRADE_PLAN_61.md part 1): the run's days are counted into a
// year of twelve months of thirty days, each month named for what the land does in it, the number kept beside the
// name so the time can be read two ways. A run begins in Year 500 on the first day of its season's first month. And
// the clock runs on the wall's time too: standing still, a game minute passes every CLOCK_RUN.secondsPerMinute real
// seconds (a day an hour), by CM.tickClock from the frame loop (76zzzzzzzzzzg-clockrun.js); a step still costs its
// minute. The films and replays are gone (v71.0): nothing need play back the same, so the weather may roll its own dice.
//   CM.MONTHS                    the twelve, from the spring's first: { name, season, note }
//   CM.dateOf(game)          -> { year, month (1-12), day (1-30), name, season, text, short }
//   CM.CLOCK_RUN                 { secondsPerMinute: 2.5 }  (24 game hours in 60 real minutes)
//   CM.tickClock(game, minutes)  the clock forward by the wall: the Wood's day turns as a step would turn it
{ CM.MONTHS = [
    { name: "Thawlight", season: "spring", note: "the ice goes off the river" },
    { name: "Sowmoon", season: "spring", note: "the fields are sown" },
    { name: "Greening", season: "spring", note: "the Wood comes into leaf" },
    { name: "Highsun", season: "summer", note: "the longest days" },
    { name: "Hayfall", season: "summer", note: "the hay is cut" },
    { name: "Emberwane", season: "summer", note: "the heat goes out of the year" },
    { name: "Harvestmoon", season: "autumn", note: "the harvest comes in" },
    { name: "Claudetober", season: "autumn", note: "the leaves turn, and the lamps are lit early" },
    { name: "Lanternfall", season: "autumn", note: "the lamplighter's long evenings" },
    { name: "Frostbell", season: "winter", note: "the first frost rings the bell" },
    { name: "Deepsnow", season: "winter", note: "the snow lies" },
    { name: "Longnight", season: "winter", note: "the year's end, the nights longest" },
  ];
  CM.YEAR_START = 500; CM.MONTH_DAYS = 30;
  CM.CLOCK_RUN = { secondsPerMinute: 2.5 };
  const firstMonth = (season) => Math.max(0, CM.MONTHS.findIndex((m) => m.season === season));
  CM.dateOf = (game) => { const d = Math.max(0, CM.dayOf ? CM.dayOf(game) : 0), start = firstMonth(CM.season ? CM.season(game) : "spring"), total = start * CM.MONTH_DAYS + d;
    const year = CM.YEAR_START + Math.floor(total / (12 * CM.MONTH_DAYS)), mi = Math.floor(total / CM.MONTH_DAYS) % 12, day = (total % CM.MONTH_DAYS) + 1, M = CM.MONTHS[mi];
    return { year, month: mi + 1, day, name: M.name, season: M.season, note: M.note, text: `Year ${year}, ${mi + 1} - ${M.name}, Day ${day}`, short: `Y${year} · ${mi + 1} ${M.name} ${day}` }; };
  CM.tickClock = (game, minutes = 1) => { if (!game || !(minutes > 0)) return; const before = CM.dayOf(game); game.clock = (game.clock || 0) + minutes;
    if (game.emit) { game.emit("clock", game.clock); if (CM.dayOf(game) !== before) game.emit("newday", CM.dayOf(game)); } };   // (the day's turning: what listens, listens; the Wood turns on its next step as it did)
}
