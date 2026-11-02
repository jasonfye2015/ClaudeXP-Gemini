"use strict";
// The deeper, the older (v30.7, UPGRADE_PLAN_25.md): the dungeon's walls age as the floors go down - the first floors
// clean dressed stone; then cracks (from the sixth floor, most by the twelfth); roots hanging from the ceiling (the
// eighth to the thirtieth, thickest about the twentieth); fungus that glows low on the walls (from the eighteenth);
// strange stone veined in colours that shift as the eye moves (from the thirtieth). Endless's floors keep getting
// older. renderer.age = [cracks, roots, fungus, strange] (40-render.js).
{ const ramp = (f, a, b) => Math.max(0, Math.min(1, (f - a) / (b - a)));
  CM.ageOf = (number) => { if (!(number >= 1) || (CM.isTowerFloor && CM.isTowerFloor(number))) return [0, 0, 0, 0]; const f = number;
    return [ramp(f, 5, 12) * 0.9, ramp(f, 8, 18) * (1 - ramp(f, 26, 34)) * 0.9 + ramp(f, 44, 50) * 0.5, ramp(f, 18, 26) * (f > 40 ? 0.6 : 1), ramp(f, 30, 40) * 0.9]; };
  const bf0 = CM.beforeFrame; CM.beforeFrame = (game, r, dt, now) => { if (bf0) bf0(game, r, dt, now); r.age = game.floor && !r.sky ? CM.ageOf(game.floor.number) : null; };
}
