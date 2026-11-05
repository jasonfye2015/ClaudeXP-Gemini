"use strict";
// The dial's predictor (v72.0, UPGRADE_PLAN_61.md part 2): under the clock's text a bar of the next six game hours -
// the event in force to its end, then the one coming, each in its colour, with what it is and when it changes
// ("rain, 1 h 10 left - then clear" / "clear - mist in 40 min") - and the exact date and time with it. The sun and
// the moon on the dial are drawn larger (70-ui.js's markup), and the stars thicker on a clear night. 73b-clock.js
// draws the dial; this adds to it on each refresh.
{ const COL = { clear: "#4F8FD0", cloud: "#8A96A8", rain: "#5A7FB8", storm: "#3A3F6E", mist: "#B8BCC8", wind: "#9AB8A0", snow: "#E8F0FA", heat: "#E8A040", aurora: "#4ED0A0" };
  const NAME = { clear: "clear", cloud: "cloud", rain: "rain", storm: "a storm", mist: "mist", wind: "wind", snow: "snow", heat: "heat", aurora: "an aurora" };
  const span = (m) => (m >= 60 ? `${Math.floor(m / 60)} h${m % 60 ? ` ${Math.round(m % 60)}` : ""}` : `${Math.max(1, Math.round(m))} min`);
  const ds0 = CM.UI.prototype.drawSky; CM.UI.prototype.drawSky = function (...a) { const out = ds0.apply(this, a); try { const g = this.game, el = this.$("#view .sky"), bar = el && el.querySelector(".wxbar"); if (!bar || !g.ext || !CM.weatherNow) return out;
      const W = CM.weatherNow(g), N = CM.nextWeather(g), t = CM.clockOf(g), H = 6 * 60, segs = bar.querySelector(".segs"); let html = "", at = t, left = H;
      const seg = (kind, mins, k) => { const w = Math.max(0, Math.min(left, mins)); if (w <= 0) return; html += `<i style="width:${(w / H * 100).toFixed(1)}%;background:${COL[kind] || "#888"};opacity:${(0.45 + 0.55 * (kind === "clear" ? 1 : k || 1)).toFixed(2)}" title="${NAME[kind]}"></i>`; left -= w; at += w; };
      seg(W.kind, W.until - t, W.strength || 0.7); if (N) { seg(N.kind, N.until - N.from, N.strength); if (left > 0) seg(N.kind === "clear" ? "cloud" : "clear", left, 0.5); }
      segs.innerHTML = html;
      const now = W.kind === "clear" ? "clear" : `${NAME[W.kind]}${W.strength < 0.35 ? " (light)" : W.strength > 0.85 ? " (heavy)" : ""}`, then = N ? ` - ${N.kind === "clear" ? "clearing" : NAME[N.kind]} in ${span(W.until - t)}` : "";
      bar.querySelector(".wxtext").textContent = `${now}${then}`; const cal = CM.dateOf ? CM.dateOf(g) : null; bar.title = `${cal ? cal.text + ", " : ""}${CM.timeFigures(g)} - the next six hours`;
      const stars = el.querySelector(".dial .stars"); if (stars && this.game.floor) { const S = CM.sky(g); stars.style.opacity = S.night ? (W.kind === "clear" || W.kind === "aurora" ? 1 : 0.25) : S.light < 0.6 ? 0.35 : 0; } } catch (e) { /* the bar is a nicety */ } return out; };
}
