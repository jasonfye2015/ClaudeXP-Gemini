"use strict";
// Boss phases - the window's side (v38.4): when a guardian or the Lich King changes, a card with its name and the words
// of the change, the entrance's sting, a shake, and the fight's music held at its height until the fight is done.
// Rules: 69zzf-phases.js.
{ let height = false;
  if (CM.music && CM.music.setDanger) { const sd0 = CM.music.setDanger.bind(CM.music); CM.music.setDanger = (k) => sd0(height ? 1 : k); }
  const rf0 = CM.UI.prototype.refresh; let bound = false;
  CM.UI.prototype.refresh = function (...a) { const g = this.game; if (!bound && g && g.on) { bound = true;
      g.on("fx", (fx) => { if (!fx || fx.kind !== "bossphase" || !fx.foe) return; height = true; try { this.titleCard(fx.foe.name, "changes"); } catch (e) { /* */ } try { CM.music && CM.music.motif && CM.music.motif("entrance"); } catch (e) { /* */ } if (CM.renderer && CM.renderer.shake) CM.renderer.shake(0.5); });
      g.on("mode", (m) => { if (m !== "combat") height = false; }); }
    return rf0.apply(this, a); };
}
