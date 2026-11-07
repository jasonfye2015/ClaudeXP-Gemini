"use strict";
// The picture, kept (v138.0): if the graphics card drops the 3D view's context - it can, on a long session, a driver
// hiccup, a change of window size - the view would stay black, as everything drawn into the old context is gone. So:
// the loss is caught, a word is put over the view, and when the card offers the context back the page loads again
// (the run saves as it goes, so it comes back where it was). If the card never offers it back, the word says to reload.
{ const t = typeof self !== "undefined" && self.CM_WORKER ? null : setInterval(() => { const r = CM.renderer, cv = r && r.canvas; if (!cv) return; clearInterval(t);
    let note = null;
    const say = (text) => { if (!note) { note = document.createElement("div"); note.className = "glnote"; Object.assign(note.style, { position: "absolute", left: "0", right: "0", top: "40%", textAlign: "center", color: "#E8D8B0", font: "16px Georgia, serif", textShadow: "0 1px 3px #000", pointerEvents: "none", zIndex: 5 }); (cv.parentElement || document.body).appendChild(note); } note.textContent = text; };
    cv.addEventListener("webglcontextlost", (e) => { e.preventDefault(); CM.glLost = (CM.glLost || 0) + 1; say("The picture was lost by the graphics card - getting it back..."); setTimeout(() => { if (note) say("The picture hasn't come back. Close the game and open it again: your run is saved where you were."); }, 8000); }, false);
    cv.addEventListener("webglcontextrestored", () => { say("The picture is back - reloading..."); setTimeout(() => location.reload(), 300); }, false); }, 300); }
