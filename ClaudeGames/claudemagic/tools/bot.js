"use strict";
// A party that plays by itself: the game's own Automatic (src/js/66-auto.js), driven to the end - with warping past
// a floor it is lost on (counted, so the simulator can say) and the waking of the Root allowed, so a run can be
// measured from the top to the bottom. The balance simulator runs it over many seeds; the tests use it to get a run
// a few floors deep.
function playRun(CM, game, opts = {}) {
  const auto = new CM.Autopilot(game, Object.assign({ warp: true, wake: true, sync: true }, opts));
  let guard = 0;
  while (auto.step() && guard++ < 1e6) { /* a step at a time, until it stops */ }
  return { log: auto.log, moves: auto.moves, stuck: auto.stuck, tools: auto.tools };
}

module.exports = { playRun };
