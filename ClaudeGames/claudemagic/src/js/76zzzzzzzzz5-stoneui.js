"use strict";
// A Stone interface (v52.0, UPGRADE_PLAN_47.md): the windows, the buttons and the panels are dressed to match the
// look - dark carved stone, a texture painted once here, framed in iron with a rivet at each corner of a window, the
// buttons set into it like stone blocks that take a warm edge of torchlight when the pointer is on them. The colours of
// the words are as they were, so nothing is harder to read.
{ if (typeof document !== "undefined" && !(typeof self !== "undefined" && self.CM_WORKER)) {
  const paint = () => { const S = 256, c = document.createElement("canvas"); c.width = c.height = S; const p = c.getContext("2d"), r = new CM.Random(4242);
    p.fillStyle = "#2A2420"; p.fillRect(0, 0, S, S);
    for (let y = 0; y < S; y += 32) for (let x = ((y / 32) % 2) * -24; x < S; x += 48) { const k = 34 + Math.floor(r.next() * 14); p.fillStyle = `rgb(${k + 4},${k},${k - 6})`; p.fillRect(x + 2, y + 2, 44, 28);
      for (let i = 0; i < 40; i++) { const g = Math.floor(r.next() * 18) - 9; p.fillStyle = `rgba(${128 + g},${120 + g},${110 + g},0.06)`; p.fillRect(x + 2 + r.next() * 42, y + 2 + r.next() * 26, 1 + r.next() * 3, 1 + r.next() * 2); }
      p.fillStyle = "rgba(255,240,210,0.05)"; p.fillRect(x + 2, y + 2, 44, 2); p.fillStyle = "rgba(0,0,0,0.25)"; p.fillRect(x + 2, y + 28, 44, 2); }
    return c.toDataURL("image/png"); };
  const install = () => { if (document.getElementById("cm-stone-ui")) return; const url = paint(), s = document.createElement("style"); s.id = "cm-stone-ui";
    const rivet = "radial-gradient(circle at 50% 40%, #9A9AA4 0 2px, #4A4A52 3px, transparent 4px)";
    s.textContent = `
.dialog .box { background: url(${url}) repeat, #241E1A; background-size: 256px 256px; border: 3px solid #3A3A40; border-radius: 3px; box-shadow: inset 0 0 0 1px #6A6A74, inset 0 0 24px rgba(0,0,0,0.6), 0 6px 22px rgba(0,0,0,0.75); position: relative; }
.dialog .box::before { content: ""; position: absolute; inset: 3px; pointer-events: none; background: ${rivet} top left / 12px 12px no-repeat, ${rivet} top right / 12px 12px no-repeat, ${rivet} bottom left / 12px 12px no-repeat, ${rivet} bottom right / 12px 12px no-repeat; }
button { background: linear-gradient(#3E3630, #2C2622); border: 1px solid #1A1612; border-top-color: #6A5E52; border-left-color: #5A4E44; box-shadow: inset 0 -2px 0 rgba(0,0,0,0.35); text-shadow: 0 1px 0 #000; }
button:hover:not(:disabled) { background: linear-gradient(#4E4236, #362C24); border-top-color: #C8A060; box-shadow: inset 0 -2px 0 rgba(0,0,0,0.35), 0 0 6px rgba(232,180,90,0.35); }
button:active:not(:disabled) { background: linear-gradient(#2A2420, #3A322A); box-shadow: inset 0 2px 3px rgba(0,0,0,0.6); }
button.primary { background: linear-gradient(#5A4428, #3C2C1A); border-color: #1A1208; border-top-color: #E8C870; }
#log, #party .hero, #side > div { background-image: url(${url}); background-size: 256px 256px; }`;
    document.head.appendChild(s); };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install); else install(); } }
