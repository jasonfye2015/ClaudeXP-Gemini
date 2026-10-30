"use strict";
// Monsters that move (the eleventh update, phase 0): a monster's pose as a pure function of what happened to it and
// when, so the Node tests can drive it and the frame loop only reads it. Times are milliseconds on one clock (the
// page's performance.now()). Nothing here touches the rules.
//
//   CM.motion({ now, phase, lungeAt, hitAt, fellAt, fledAt, roseAt, ghost, sleeping, sway, reduced })
//     -> { forward, back, lift, tilt, scaleY, scale, flash, alpha, skew, done }
//
// forward: toward the party (a lunge), back: away (a flinch, a flight) - both in squares; lift in squares; tilt in
// radians about its foot (a fall: it topples to one side); scaleY a breath; scale the whole picture (a flight
// shrinks down the corridor); flash a white flash, 0 to 1; alpha; skew a sway of its top (the Lich King's robe);
// done: the pose has finished (a fall faded, a flight gone) and the sprite can be dropped.
CM.MOTION = {
  breath: 0.02, breathMs: 820,
  lungeIn: 120, lungeOut: 200, lungeReach: 0.24,
  flinchMs: 220, flinchBack: 0.17, flashMs: 90,
  fallMs: 400, fadeMs: 300, fallTilt: (80 * Math.PI) / 180,
  fleeMs: 650, fleeBack: 1.4,
  riseMs: 1000,
};
CM.motion = function (s) {
  const M = CM.MOTION, now = s.now, out = { forward: 0, back: 0, lift: 0, tilt: 0, scaleY: 1, scale: 1, flash: 0, alpha: 1, skew: 0, done: false };
  const since = (t) => (t === undefined || t === null ? Infinity : now - t);
  const phase = s.phase || 0;
  if (s.sleeping) {                                                       // lying where it sleeps: no breath to see but a slow rise of its side
    out.tilt = M.fallTilt * 0.95;
    if (!s.reduced) out.scaleY = 1 + Math.sin(now / 1700 + phase) * 0.012;
    return out;
  }
  const fell = since(s.fellAt);
  if (fell !== Infinity) {                                                // falling: it topples, then fades
    if (s.reduced) { out.alpha = Math.max(0, 1 - fell / (M.fallMs + M.fadeMs)); out.done = fell >= M.fallMs + M.fadeMs; return out; }
    const k = Math.min(1, fell / M.fallMs);
    out.tilt = M.fallTilt * (1 - Math.pow(1 - k, 2)) * (s.ghost ? 0 : 1);
    if (s.ghost) out.lift = (fell / (M.fallMs + M.fadeMs)) * 0.6;        // (a ghost rises away instead)
    out.alpha = fell <= M.fallMs ? 1 : Math.max(0, 1 - (fell - M.fallMs) / M.fadeMs);
    out.done = fell >= M.fallMs + M.fadeMs;
    return out;
  }
  const fled = since(s.fledAt);
  if (fled !== Infinity) {                                                // running: away down the corridor, smaller, then gone
    const k = Math.min(1, fled / M.fleeMs);
    if (s.reduced) { out.alpha = 1 - k; out.done = k >= 1; return out; }
    out.back = M.fleeBack * k * k; out.scale = 1 - 0.45 * k; out.alpha = 1 - k * k; out.lift = Math.abs(Math.sin(fled / 70)) * 0.03 * (1 - k);
    out.done = k >= 1;
    return out;
  }
  if (!s.reduced) {
    out.scaleY = 1 + Math.sin(now / M.breathMs + phase) * M.breath;     // breathing, each in its own time
    const rose = since(s.roseAt);
    if (rose < M.riseMs) { const k = rose / M.riseMs; out.lift = -(1 - k) * (1 - k) * 1.0; }   // (a guardian rises from the floor into its title)
    const lunge = since(s.lungeAt), hit = since(s.hitAt);
    const lunging = lunge < M.lungeIn + M.lungeOut && !(hit < lunge);     // (struck mid-lunge: the lunge is broken off)
    if (lunging) out.forward = lunge < M.lungeIn ? M.lungeReach * (lunge / M.lungeIn) : M.lungeReach * (1 - (lunge - M.lungeIn) / M.lungeOut);
    if (hit < M.flinchMs) out.back = M.flinchBack * Math.sin((Math.PI * hit) / M.flinchMs);
    if (s.sway) out.skew = Math.sin(now / 900 + phase) * 0.045 + Math.sin(now / 370 + phase * 2) * 0.012;
  }
  const hit = since(s.hitAt);
  if (hit < M.flashMs) out.flash = 1 - hit / M.flashMs;                    // (the flash, even with motion reduced)
  return out;
};
// which way a monster's picture faces: toward the party's line of sight. side > 0: it stands to the right of the
// line, so it is mirrored to look left, at the party
CM.facesMirror = (side) => side > 0.04;
