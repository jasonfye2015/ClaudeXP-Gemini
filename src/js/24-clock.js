"use strict";
// The clock is the game's, not the wall's: a step is a minute, a stair an hour, a round of a fight a minute, and a
// rest (the camp's, the hearth's) sleeps until the next dawn. A run begins at six in the morning. The hour is saved
// with the run and plays back the same in a film. The moon turns on a twenty-nine day month from the run's first day.
// What the hour does happens above ground (the town's lanterns, the townsfolk indoors) and on the first floors (a full
// moon: the undead a tenth tougher on floors 1 to 5; a new moon: a lock a tenth easier, a night ambush a little likelier).
CM.CLOCK = { start: 6 * 60, day: 24 * 60, stair: 60, moon: 29 };
CM.clockOf = (game) => (game && game.clock) || 0;
CM.minuteOf = (game) => (CM.CLOCK.start + CM.clockOf(game)) % CM.CLOCK.day;
CM.hourOf = (game) => CM.minuteOf(game) / 60;
CM.dayOf = (game) => Math.floor((CM.CLOCK.start + CM.clockOf(game)) / CM.CLOCK.day);   // (the run's day, from 0)
CM.isNight = (game) => { const h = CM.hourOf(game); return h >= 21 || h < 5; };
CM.hourWord = (h) => (h >= 21 || h < 1 ? "night" : h < 5 ? "the small hours" : h < 7 ? "dawn" : h < 11 ? "morning" : h < 13 ? "noon" : h < 17 ? "afternoon" : h < 19 ? "dusk" : "evening");
CM.MOON_WORDS = ["a new moon", "a waxing crescent", "the first quarter", "a waxing gibbous", "a full moon", "a waning gibbous", "the last quarter", "a waning crescent"];
CM.moonPhase = (game) => Math.round(((CM.dayOf(game) % CM.CLOCK.moon) / CM.CLOCK.moon) * 8) % 8;   // 0 new .. 4 full (the fifteenth day)
CM.moonWord = (game) => CM.MOON_WORDS[CM.moonPhase(game)];
CM.fullMoon = (game) => CM.moonPhase(game) === 4;
CM.newMoon = (game) => CM.moonPhase(game) === 0;
CM.clockWords = (game) => { const m = CM.minuteOf(game), h = Math.floor(m / 60), mm = m % 60; return `${CM.hourWord(CM.hourOf(game))} (${h}:${mm < 10 ? "0" : ""}${mm}), day ${CM.dayOf(game) + 1} of the run, ${CM.moonWord(game)}`; };
// the sun's and the moon's places on the sky bar's arc: 0 is the left horizon, 1 the right; below the horizon is null
CM.skyPlaces = (game) => { const h = CM.hourOf(game), sun = (h - 6) / 12, moon = ((h + 12) % 24 - 6) / 12; return { sun: sun >= 0 && sun <= 1 ? sun : null, moon: moon >= 0 && moon <= 1 ? moon : null, phase: CM.moonPhase(game) }; };
CM.townNight = (hour) => (hour === undefined ? false : hour >= 21 || hour < 5);   // (kept for the title screen's lanterns: the wall clock)
