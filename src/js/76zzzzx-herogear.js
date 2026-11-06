"use strict";
// The heroes' gear seen (v29.3, UPGRADE_PLAN_24.md): a hero's portrait - on the party's cards (and so the level-up
// card's), the sheet, the camp's and the end's lists - shows what they carry: the weapon in hand at its lower right,
// the helm at its upper left, the armour at its lower left, each drawn in the look of the day, with a dark rim to lift
// it off the face. A portrait given a class's name (the title, the new party's choices) is the class's, as before.
{ const P = CM.UI.prototype, base = P.portrait, cache = new Map();
  const sig = (h) => ["weapon", "helm", "armor"].map((k) => (h[k] ? `${h[k].name}|${h[k].unknown ? 1 : 0}` : "-")).join("/");
  P.portrait = function (who, size) {
    if (typeof who === "string" || !who || !who.cls) return base.call(this, who, size);
    const look = this.game.settings.look, key = `${look}:${CM.art.hasDolls && CM.art.hasDolls() ? "dolls" : "drawn"}:${who.cls}:${size}:${sig(who)}`;   /* (the sprites' arrival makes a new key: a portrait drawn before the dolls were decoded is not kept) */
    let src = cache.get(key);
    if (!src) { const b = base.call(this, who.cls, size), c = document.createElement("canvas"); c.width = c.height = size; const p = c.getContext("2d"); p.drawImage(b, 0, 0);
      const put = (it, s, x, y, rot) => { if (!it || (it.props && it.props.fists)) return; let ic; try { ic = CM.art.itemIcon(it, Math.round(s), look); } catch (e) { return; }
        p.save(); p.translate(x, y); p.rotate(rot); p.shadowColor = "rgba(0,0,0,0.85)"; p.shadowBlur = Math.max(2, size / 20); p.drawImage(ic, -s / 2, -s / 2, s, s); p.restore(); };
      put(who.armor, size * 0.36, size * 0.2, size * 0.8, 0); put(who.helm, size * 0.34, size * 0.19, size * 0.19, -0.15); put(who.weapon, size * 0.5, size * 0.76, size * 0.72, -0.35);
      src = c; cache.set(key, c); if (cache.size > 200) cache.delete(cache.keys().next().value); }
    const out = document.createElement("canvas"); out.width = out.height = size; out.getContext("2d").drawImage(src, 0, 0); return out;
  };
}
