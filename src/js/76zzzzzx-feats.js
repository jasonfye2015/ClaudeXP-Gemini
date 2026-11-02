"use strict";
// The hall of feats - the window's side (v33.0): a room at the Mage Tower's foot, a plaque on its walls for every feat
// there is - brass and bright for those earned, with who and when; dark stone with the feat's words for the rest - and
// the title the player wears. From the Tower's doors (a button), and from the title screen's honours. Rules:
// the achievements (10-data.js) and 69zd-feats.js.
{ const css = `#dlg-feats .plaques { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 8px; }
  #dlg-feats .plaque { border-radius: 6px; padding: 8px 10px; font-size: 12px; line-height: 1.3; min-height: 64px; }
  #dlg-feats .plaque.got { background: linear-gradient(160deg, #E8C878, #B88A38 55%, #8A6420); color: #2A1A08; box-shadow: inset 0 1px 0 rgba(255,255,255,0.5), inset 0 -2px 3px rgba(0,0,0,0.35), 0 2px 4px rgba(0,0,0,0.5); }
  #dlg-feats .plaque.got b { display: block; font-size: 13px; text-shadow: 0 1px 0 rgba(255,240,200,0.6); }
  #dlg-feats .plaque.not { background: linear-gradient(160deg, #3A3530, #26221E); color: #8A8070; box-shadow: inset 0 0 6px rgba(0,0,0,0.6); }
  #dlg-feats .plaque.not b { display: block; color: #A89880; }
  #dlg-feats .plaque small { display: block; opacity: 0.85; margin-top: 3px; }`;
  const make = (ui) => { if (ui.$("#dlg-feats")) return; const st = document.createElement("style"); st.textContent = css; document.head.appendChild(st);
    const d = document.createElement("div"); d.className = "dialog"; d.id = "dlg-feats"; d.innerHTML = `<div class="box journalbox"><h2>The hall of feats</h2><p class="lore">A long room at the Tower's foot, cold and quiet. Brass plaques line its walls, one for every deed the Tower thinks worth remembering. Some are polished; most wait.</p><p class="small" id="feats-sum"></p><div class="plaques"></div><div class="end"><button class="close">Close</button></div></div>`;
    const host = ui.$("#dlg-magetower"); host.parentNode.appendChild(d); d.querySelector(".close").addEventListener("click", () => ui.closeDialogs()); };
  CM.UI.prototype.openFeats = function () { make(this); const g = this.game, A = g.achievements || {}, ids = Object.keys(CM.ACHIEVEMENTS), got = ids.filter((id) => A[id]);
    this.$("#feats-sum").textContent = `${got.length} of ${ids.length} earned.${got.length ? ` The title worn: ${CM.playerName || "Adventurer"} ${CM.titleFor(A)}.` : ""}`;
    this.$("#dlg-feats .plaques").innerHTML = ids.filter((id) => A[id]).concat(ids.filter((id) => !A[id])).map((id) => { const a = CM.ACHIEVEMENTS[id], t = A[id];
      return t ? `<div class="plaque got"><b>${this.esc(a.name)}</b>${this.esc(a.what)}<small>"${this.esc(a.title)}" - ${this.esc(t.name || "")}, ${this.esc(t.date || "")}</small></div>` : `<div class="plaque not"><b>${this.esc(a.name)}</b>${this.esc(a.what)}</div>`; }).join("");
    this.openDialog("#dlg-feats"); };
  const om0 = CM.UI.prototype.openMageTower;
  CM.UI.prototype.openMageTower = function (...a) { const out = om0.apply(this, a), box = this.$("#dlg-magetower .box"); if (!box) return out;
    let b = box.querySelector(".hallbtn"); if (!b) { b = document.createElement("button"); b.className = "hallbtn"; b.textContent = "The hall of feats, at the Tower's foot"; const lore = box.querySelector(".lore"); if (lore) lore.after(b); else box.prepend(b); b.addEventListener("click", () => this.openFeats()); }
    return out; };
}
