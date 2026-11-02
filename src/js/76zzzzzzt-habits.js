"use strict";
// Monster habits - the window's side (v38.2): the bestiary writes a kind's habit once it is known, and how many more must
// fall before it is. Rules: 69zzd-habits.js.
{ const bh0 = CM.UI.prototype.bestiaryHtml;
  CM.UI.prototype.bestiaryHtml = function (...a) { const html = bh0.apply(this, a), g = this.game, b = g.bestiary || {}; if (!html) return html;
    return html.replace(/<p><b>([^<]+)<\/b>/g, (all, name) => { const real = name.replace(/&amp;/g, "&").replace(/&#39;/g, "'"); const e = b[real]; if (!e || !CM.monsterKind(real)) return all;
      const known = g.habitRead(real) || g.habitKnown(real); return `${all}${known ? ` <i>Its way: ${this.esc(CM.habitOf(real))}.</i>` : ` <small>(its way is read by slaying ${CM.HABIT_AT} in one expedition)</small>`}`; }); };
}
