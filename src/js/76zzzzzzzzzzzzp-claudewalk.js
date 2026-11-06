"use strict";
// Claude, seen walking (UPGRADE_PLAN_72.md, release 3): when he comes down with the party for the last of it (plan 71's
// walk), he is drawn behind the back row the way the porter and the hound are - a step behind the last of them, the
// scholar's figure with a book under his arm, keeping to the party's trail and closing up as it walks. He stands back
// from a fight. Rules: 69zzzt-lastpage.js (the walk), 76zzzzz-followers.js (the trail).
{ const fs0 = CM.followersSeen; if (fs0) CM.followersSeen = (game, fl) => { const out = fs0(game, fl);
    if (game && game.claudeWalking && game.claudeWalking() && fl && fl.number >= 1 && game.mode !== "combat") out.push(["claude", "npc:claude", out.length + 1, false]);
    return out; }; }
