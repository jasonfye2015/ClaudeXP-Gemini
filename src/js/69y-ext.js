"use strict";
// The run's own extra keeping (v32.0): the later updates' run-long state - what a run has done that the rules want to
// remember until it ends - kept in the tally, which is saved with the run and made new with each one. game.ext()
// returns it (an object), game.ext(name) the named part of it (made empty the first time).
Object.assign(CM.Game.prototype, {
  ext(name) { this.tally = this.tally || (this.freshTally ? this.freshTally() : {}); const E = this.tally.ext = this.tally.ext || {}; if (!name) return E; return (E[name] = E[name] || {}); },
  vext(name) { this.village = this.village || {}; const E = this.village.ext = this.village.ext || {}; return (E[name] = E[name] || {}); },   // (the village's: kept between runs)
});
