"use strict";
// The look of the dungeon: three themes the player chooses between, on the title and in Settings, at any time.
//   drawn  everything painted in code (30-art.js) - the game's own art
//   pixel  Dungeon Crawl Stone Soup's 32-pixel tiles (CC0), crisp and chunky: the stone of each depth, the furniture,
//          the monsters, the things in the pack, the spells, and the heroes as paper dolls
//   stone  photographed stone (ambientCG, CC0) on the walls, floors and ceilings, with the drawn furniture and monsters
// The packs ride inside the one file (35-packs.js, written by pack.py from src/art/) and are decoded once, by
// CM.art.load(); until then, and wherever a pack has no tile for something, the drawn art stands in.
CM.LOOKS = {
  drawn: { name: "Drawn", what: "painted in code: the game's own art" },
  pixel: { name: "Pixel tiles", what: "Dungeon Crawl Stone Soup's pixel tiles, crisp and chunky" },
  stone: { name: "Stone", what: "photographed stone on the walls and floors, with the drawn monsters" },
};
CM.art.packs = { ready: false, atlas: null, stone: {}, loading: null };

// decode the packs (a promise; it resolves at once when the file carries none)
CM.art.load = function () {
  const packs = CM.art.packs;
  if (packs.loading) return packs.loading;
  const P = CM.packs;
  if (!P) { packs.ready = true; return (packs.loading = Promise.resolve()); }
  const decode = (src) => new Promise((done) => { const im = new Image(); im.onload = () => done(im); im.onerror = () => done(null); im.src = src; });
  packs.loading = Promise.all([decode(P.pixel.atlas), ...Object.entries(P.stone.textures || {}).map(([k, src]) => decode(src).then((im) => [k, im]))])
    .then(([atlas, ...stones]) => {
      packs.atlas = atlas;
      for (const [k, im] of stones) if (im) packs.stone[k] = im;
      packs.ready = true;
    });
  return packs.loading;
};
CM.art.hasLook = (look) => look === "drawn" || (look === "pixel" && Boolean(CM.art.packs.atlas)) || (look === "stone" && Object.keys(CM.art.packs.stone).length > 0);

// a tile of the atlas, drawn crisp (no smoothing) into a rectangle; false when there's no such tile
CM.art.tileOnto = function (p, key, x, y, w, h, opts = {}) {
  const P = CM.packs && CM.packs.pixel, at = P && P.index[key], atlas = CM.art.packs.atlas;
  if (!at || !atlas) return false;
  p.save();
  p.imageSmoothingEnabled = false;
  if (opts.alpha !== undefined) p.globalAlpha = opts.alpha;
  p.drawImage(atlas, at[0], at[1], P.size, P.size, x, y, w, h);
  p.restore();
  return true;
};
CM.art.tile = function (key, size = ART_SIZE, opts = {}) {
  const c = artCanvas(size);
  CM.art.tileOnto(c.getContext("2d"), key, 0, 0, size, size, opts);
  return c;
};
// the drawn art, made of so many pixels a side - for what the tile set has no tile for
CM.art.pixelate = function (canvas, cells = 32) {
  const small = artCanvas(cells), sp = small.getContext("2d");
  sp.drawImage(canvas, 0, 0, cells, cells);
  const c = artCanvas(canvas.width), p = c.getContext("2d");
  p.imageSmoothingEnabled = false;
  p.drawImage(small, 0, 0, canvas.width, canvas.height);
  return c;
};

// ---- the Pixel theme: a depth's whole set from the atlas -------------------------------------------------------------
CM.art.buildPixel = function (theme) {
  const t = `t${Math.max(0, CM.THEMES.indexOf(theme))}`, S = ART_SIZE, layers = [], index = {};
  const add = (name, canvas) => { index[name] = layers.length; layers.push(canvas); };
  const tiled = (key, n = 2, darken = 0) => {                                 // the stone: a tile repeated n x n across the face
    const c = artCanvas(S), p = c.getContext("2d");
    for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) CM.art.tileOnto(p, key, x * S / n, y * S / n, S / n, S / n);
    if (darken) { p.fillStyle = `rgba(0,0,0,${darken})`; p.fillRect(0, 0, S, S); }
    return c;
  };
  add("wall", tiled(`${t}.wall`));
  add("wall2", tiled(`${t}.wall2`));
  add("wallbones", tiled(`${t}.wallbones`));
  add("floor", tiled(`${t}.floor`));
  add("ceiling", tiled(`${t}.ceiling`, 2, 0.12));
  const secret = tiled(`${t}.wall`);
  CM.art.tileOnto(secret.getContext("2d"), "secret", 0, 0, S, S, { alpha: 0.3 });     // (the door's shape, faint)
  add("wallsecret", secret);
  const sprite = (key) => CM.art.tile(key, S);
  for (const name of ["chest", "hatch", "door", "door_locked", "door_open", "gate", "gate_open", "pit", "trapdoor", "teleporter", "fountain", "fountain_dry",
    "altar", "carving", "stairs_up", "key"]) add(name, sprite(name));
  add("lever", CM.art.pixelate(CM.art.lever(false)));
  add("lever_pulled", CM.art.pixelate(CM.art.lever(true)));
  const phy = artCanvas(S), pp = phy.getContext("2d");                      // the box from the east, lit from within
  const glow = pp.createRadialGradient(S / 2, S * 0.55, 10, S / 2, S * 0.55, S * 0.45);
  glow.addColorStop(0, "rgba(96,208,255,0.55)"); glow.addColorStop(1, "rgba(96,208,255,0)");
  pp.fillStyle = glow; pp.fillRect(0, 0, S, S);
  CM.art.tileOnto(pp, "phylactery", S * 0.15, S * 0.15, S * 0.7, S * 0.7);
  add("phylactery", phy);
  const tileOr = (key, drawn) => (CM.packs.pixel.index[key] ? sprite(key) : CM.art.pixelate(drawn()));   // (the set's tile, or the drawn one made of pixels)
  for (const m of CM.MONSTERS) add(`monster:${m.name}`, tileOr(`m.${m.name}`, () => CM.art.monster(m)));
  add(`monster:${CM.BOSS.name}`, sprite(`m.${CM.BOSS.name}`));
  for (const G of Object.values(CM.GUARDIANS)) add(`monster:${G.name}`, tileOr(`m.${G.name}`, () => CM.art.monster(G, 1.12)));
  add("nest", CM.art.pixelate(CM.art.nest())); add("throne", CM.art.pixelate(CM.art.throne())); add("anvil", CM.art.pixelate(CM.art.anvil()));
  add("ember", tileOr("ember", CM.art.ember));
  for (const [who, row] of Object.entries(CM.art.PEOPLE)) add(`npc:${who}`, tileOr(`npc.${who}`, () => CM.art.monster(row)));
  add("bones", CM.art.pixelate(CM.art.bones())); add("rope", CM.art.pixelate(CM.art.rope()));
  add("plate", tileOr("plate", () => CM.art.plate(false)));
  const pressed = CM.packs.pixel.index.plate ? sprite("plate") : CM.art.pixelate(CM.art.plate(true));   // (the plate, sunk: the same tile, darkened)
  if (CM.packs.pixel.index.plate) { const q = pressed.getContext("2d"); q.globalCompositeOperation = "source-atop"; q.fillStyle = "rgba(0,0,0,0.45)"; q.fillRect(0, 0, S, S); }
  add("plate_pressed", pressed);
  add("door_riddle", tileOr("door_riddle", () => CM.art.door("riddle")));
  add("fungus", CM.art.pixelate(CM.art.fungus())); add("crystal", CM.art.pixelate(CM.art.crystal())); add("root", CM.art.pixelate(CM.art.root()));
  add("fx:spark", tileOr("fx.spark", CM.art.fxSpark)); add("fx:shard", tileOr("fx.shard", CM.art.fxShard)); add("fx:fire", tileOr("fx.fire", CM.art.fxFire));
  add("fx:frost", tileOr("fx.frost", CM.art.fxFrost)); add("fx:bolt", tileOr("fx.bolt", CM.art.fxBolt)); add("fx:force", tileOr("fx.force", CM.art.fxForce));
  add("fx:holy", tileOr("fx.holy", CM.art.fxHoly)); add("fx:arrow", tileOr("fx.arrow", CM.art.fxArrow)); add("fx:leaf", tileOr("fx.leaf", CM.art.fxLeaf));
  add("fx:ring", tileOr("fx.ring", CM.art.fxRing));
  for (let f = 0; f < 3; f++) { add(`torch${f}`, tileOr(`torch${f}`, () => CM.art.torch(f))); add(`water${f}`, tileOr(`water${f}`, () => CM.art.water(f))); }
  return { layers, index, size: S, crisp: true };
};

// ---- the Stone theme: photographs on the stone, the drawn art on everything else ---------------------------------------
CM.art.buildStone = function (theme) {
  const t = theme.photos || `t${Math.max(0, CM.THEMES.indexOf(theme))}`, S = (CM.packs && CM.packs.stone.size) || 512, layers = [], index = {};
  const add = (name, canvas) => { index[name] = layers.length; layers.push(canvas); };
  const photo = (key, flip = false, darken = 0) => {
    const c = artCanvas(S), p = c.getContext("2d"), im = CM.art.packs.stone[key];
    if (im) {
      if (flip) { p.translate(S, 0); p.scale(-1, 1); }
      p.drawImage(im, 0, 0, S, S);
      p.setTransform(1, 0, 0, 1, 0, 0);
    } else { p.fillStyle = rgb(theme.stone); p.fillRect(0, 0, S, S); }
    p.globalCompositeOperation = "overlay";                                 // a breath of the depth's own colour
    p.globalAlpha = 0.3;
    p.fillStyle = rgb(theme.stone, 1.5);
    p.fillRect(0, 0, S, S);
    p.globalCompositeOperation = "source-over";
    p.globalAlpha = 1;
    if (darken) { p.fillStyle = `rgba(0,0,0,${darken})`; p.fillRect(0, 0, S, S); }
    return c;
  };
  add("wall", photo(`${t}.wall`));
  add("wall2", photo(`${t}.wall`, true));
  const bones = photo(`${t}.wall`), bp = bones.getContext("2d"), rnd = new CM.Random(CM.hashSeed(theme.name + ":stone"));
  bp.scale(S / ART_SIZE, S / ART_SIZE);
  for (let k = 0; k < 2 + rnd.int(0, 2); k++) bone(bp, rnd, 30 + rnd.next() * (ART_SIZE - 60), 30 + rnd.next() * (ART_SIZE - 60), rnd.next());
  add("wallbones", bones);
  add("floor", photo(`${t}.floor`));
  add("ceiling", photo(`${t}.ceiling`, false, 0.3));
  const secret = photo(`${t}.wall`), sp = secret.getContext("2d");          // the hairline round a door's shape
  sp.strokeStyle = "rgba(0,0,0,0.4)"; sp.lineWidth = S / 128;
  sp.beginPath(); sp.moveTo(S * 0.2, S); sp.lineTo(S * 0.2, S * 0.12); sp.lineTo(S * 0.8, S * 0.12); sp.lineTo(S * 0.8, S); sp.stroke();
  add("wallsecret", secret);
  const drawn = CM.art.buildDrawn(theme);                                   // the rest, as drawn, at the stone's size
  for (const [name, i] of Object.entries(drawn.index)) {
    if (name in index) continue;
    const c = artCanvas(S);
    c.getContext("2d").drawImage(drawn.layers[i], 0, 0, S, S);
    add(name, c);
  }
  return { layers, index, size: S, crisp: false };
};

// the whole set for a depth, in the look asked for (the drawn one when a pack isn't there)
CM.art.build = function (theme, look = "drawn") {
  if (look === "pixel" && CM.art.hasLook("pixel")) return CM.art.buildPixel(theme);
  if (look === "stone" && CM.art.hasLook("stone")) return CM.art.buildStone(theme);
  return CM.art.buildDrawn(theme);
};

// ---- the heroes, in the Pixel theme: paper dolls, part laid on part ------------------------------------------------------
CM.art.DOLLS = {
  Knight: ["human_male", "boots.gray", "legs.armor", "body.plate", "head.helm_plume", "left.shield_knight", "right.long_sword"],
  Paladin: ["human_female", "boots.gray", "legs.armor", "body.plate_cloth", "cloak.white", "head.full_gold", "left.shield_holy", "right.blessed_blade"],
  Rogue: ["human_male", "boots.short", "legs.black", "body.leather", "cloak.black", "head.hood_black", "right.dagger"],
  Ranger: ["human_female", "boots.brown", "legs.green", "body.leather_green", "cloak.green", "head.hood_green", "right.bow"],
  Cleric: ["human_male", "boots.brown", "body.robe_white_red", "hair.short_black", "head.healer", "left.shield_round", "right.mace"],
  Mage: ["human_male", "boots.short", "body.robe_blue", "beard.long_white", "head.wizard_blue", "left.book", "right.staff_mage"],
  Druid: ["human_female", "boots.brown", "body.robe_green", "hair.long_red", "head.hood_green_2", "right.staff_organic"],
  Bard: ["human_male", "boots.short", "legs.blue", "body.vest", "cloak.red", "hair.short_black", "head.feather_red", "right.horn"],
};
CM.art.PORTRAIT_BG = { Knight: "#3A3E4A", Rogue: "#2E3A2A", Cleric: "#4A3E2A", Mage: "#2E2A4A", Paladin: "#4A3A2A", Ranger: "#2A3A2E", Druid: "#3A4A2A", Bard: "#4A2A3A" };
CM.art.portrait = function (cls, size = 56, look = "drawn") {
  if (look !== "pixel" || !CM.art.hasLook("pixel")) return CM.art.portraitDrawn(cls, size);
  const c = artCanvas(size), p = c.getContext("2d");
  p.fillStyle = CM.art.PORTRAIT_BG[cls] || "#333";
  p.fillRect(0, 0, size, size);
  for (const part of CM.art.DOLLS[cls] || CM.art.DOLLS.Knight) CM.art.tileOnto(p, `d.${part}`, 0, 0, size, size);
  return c;
};

// ---- the things in the pack, as icons: a tile in the Pixel theme, a glyph painted in code otherwise ------------------------
CM.art.itemKey = function (item) {
  const n = item.name || "", has = (...words) => words.some((w) => n.includes(w));
  switch (item.kind) {
    case "heal": case "mana": case "revive": case "antidote": return `i.${item.kind}`;
    case "scroll": return "i.scroll";
    case "wand": return "i.wand";
    case "torch": return "i.torch";
    case "lantern": return "i.lantern";
    case "key": return "i.key";
    case "rope": return "i.rope";
    case "bones": return "i.bones";
    case "tome": return "i.tome";
    case "gem": return `i.gem_${item.gem}`;
    case "greaterheal": return "i.greaterheal";
    case "oil": return "i.oil";
    case "bomb": return "i.bomb";
    case "ingredient": return "i.ingredient";
    case "scrap": return "i.scrap";
    case "weapon":
      if (item.props && item.props.bow) return has("Short Bow", "Hunting Bow") ? "i.bow" : "i.longbow";
      if (has("Dagger")) return "i.dagger";
      if (has("Knife")) return "i.knife";
      if (has("Short Sword")) return "i.short_sword";
      if (has("Mace")) return "i.mace";
      if (has("Axe")) return "i.axe";
      if (has("Hammer")) return "i.hammer";
      if (has("Flamberge", "Dragonslayer")) return "i.great_sword";
      if (has("Club")) return "i.club";
      if (has("Staff")) return "i.staff";
      if (has("Spear")) return "i.spear";
      return "i.long_sword";
    case "armor":
      if (has("Vest", "Robe", "Tunic")) return "i.robe";
      if (has("Leather")) return "i.leather";
      if (has("Ring Mail")) return "i.ring_mail";
      if (has("Scale")) return "i.scale";
      if (has("Chain", "Elven", "Banded")) return "i.chain";
      return "i.plate";
    case "shield": return has("Buckler") ? "i.buckler" : has("Tower") ? "i.tower" : "i.shield";
    case "helm": return has("Cap", "Coif") ? "i.cap" : has("Great") ? "i.great_helm" : "i.helm";
    case "ring": return "i.ring";
    case "amulet": return "i.amulet";
    default: return "i.unknown";
  }
};
// a small painted glyph for a thing, in a 24-unit square scaled to `size`
CM.art.glyph = function (item, size = 24) {
  const c = artCanvas(size), p = c.getContext("2d"), s = size / 24, key = CM.art.itemKey(item).slice(2);
  p.scale(s, s);
  p.lineJoin = "round"; p.lineCap = "round";
  const line = (col, w) => { p.strokeStyle = col; p.lineWidth = w; };
  const potion = (col) => {
    outlined(p, () => { p.moveTo(9, 3); p.lineTo(15, 3); p.lineTo(15, 8); p.lineTo(19, 14); p.lineTo(19, 20); p.lineTo(5, 20); p.lineTo(5, 14); p.lineTo(9, 8); }, "#D8E8F0", "#1A1410", 1.5);
    p.fillStyle = col; p.beginPath(); p.moveTo(6.5, 14.5); p.lineTo(17.5, 14.5); p.lineTo(17.5, 19); p.lineTo(6.5, 19); p.fill();
    p.fillStyle = "#6A4A28"; p.fillRect(9, 1, 6, 3);
  };
  const blade = (len, col) => { line("#1A1410", 5); p.beginPath(); p.moveTo(5, 19); p.lineTo(5 + len, 19 - len); p.stroke(); line(col, 3); p.beginPath(); p.moveTo(5, 19); p.lineTo(5 + len, 19 - len); p.stroke(); line("#8A6A20", 3); p.beginPath(); p.moveTo(3, 15); p.lineTo(9, 21); p.stroke(); };
  switch (key) {
    case "heal": potion("#D83030"); break;
    case "mana": potion("#3060E0"); break;
    case "revive": potion("#F0C040"); break;
    case "antidote": potion("#40B050"); break;
    case "greaterheal": potion("#FF6060"); p.fillStyle = "#FFF0F0"; p.fillRect(10, 11, 4, 1.5); p.fillRect(11.2, 9.8, 1.6, 4); break;
    case "oil": potion("#E0A030"); break;
    case "bomb": outlined(p, () => { p.arc(12, 14, 7, 0, Math.PI * 2); }, "#3A3430", "#1A1410", 1.5); line("#C8A040", 1.5); p.beginPath(); p.moveTo(12, 7); p.lineTo(15, 3); p.stroke(); p.fillStyle = "#FF9030"; p.beginPath(); p.arc(15, 3, 1.6, 0, Math.PI * 2); p.fill(); break;
    case "ingredient": line("#1A1410", 4); p.beginPath(); p.moveTo(6, 20); p.quadraticCurveTo(12, 4, 19, 6); p.stroke(); line("#6A9A40", 2); p.beginPath(); p.moveTo(6, 20); p.quadraticCurveTo(12, 4, 19, 6); p.stroke(); outlined(p, () => { p.ellipse(13, 12, 4, 7, -0.7, 0, Math.PI * 2); }, "#80B050", "#1A1410", 1.2); break;
    case "scrap": outlined(p, () => { p.moveTo(5, 16); p.lineTo(10, 7); p.lineTo(14, 12); p.lineTo(19, 9); p.lineTo(18, 19); p.lineTo(7, 20); }, "#8A8A90", "#1A1410", 1.5); break;
    case "scroll": outlined(p, () => { p.rect(5, 4, 14, 16); }, "#E8DCC0", "#5A4A2A", 1.5); line("#8A6A3A", 1); for (let y = 8; y <= 16; y += 3) { p.beginPath(); p.moveTo(8, y); p.lineTo(16, y); p.stroke(); } p.fillStyle = "#B03030"; p.fillRect(5, 17, 14, 2); break;
    case "wand": line("#1A1410", 5); p.beginPath(); p.moveTo(5, 19); p.lineTo(17, 7); p.stroke(); line("#8A6A30", 3); p.beginPath(); p.moveTo(5, 19); p.lineTo(17, 7); p.stroke(); p.fillStyle = "#F0E060"; p.beginPath(); p.arc(18, 6, 3, 0, Math.PI * 2); p.fill(); break;
    case "torch": line("#1A1410", 5); p.beginPath(); p.moveTo(10, 21); p.lineTo(13, 11); p.stroke(); line("#7A5A30", 3); p.beginPath(); p.moveTo(10, 21); p.lineTo(13, 11); p.stroke(); outlined(p, () => { p.moveTo(13, 2); p.lineTo(18, 9); p.lineTo(13, 12); p.lineTo(8, 9); }, "#F0A030", "#A04010", 1.5); break;
    case "lantern": outlined(p, () => { p.rect(7, 7, 10, 12); }, "#F0D070", "#4A3A1A", 1.5); p.fillStyle = "#4A3A1A"; p.fillRect(6, 5, 12, 3); p.fillRect(11, 2, 2, 3); break;
    case "tome": outlined(p, () => { p.rect(5, 3, 14, 18); }, "#4A3A8A", "#1A1410", 1.5); p.fillStyle = "#2A2050"; p.fillRect(5, 3, 3, 18); p.fillStyle = "#E8C870"; p.fillRect(10, 8, 7, 1.6); p.fillRect(10, 11, 7, 1.6); p.fillRect(10, 14, 5, 1.6); break;
    case "gem_diamond": case "gem_ruby": case "gem_sapphire": case "gem_sunstone": {
      const col = { gem_diamond: "#E8F4FF", gem_ruby: "#E03040", gem_sapphire: "#3060E0", gem_sunstone: "#F0B030" }[key];
      outlined(p, () => { p.moveTo(12, 3); p.lineTo(20, 10); p.lineTo(12, 21); p.lineTo(4, 10); }, col, "#1A1410", 1.5);
      p.strokeStyle = "rgba(255,255,255,0.7)"; p.lineWidth = 1; p.beginPath(); p.moveTo(4, 10); p.lineTo(20, 10); p.moveTo(12, 3); p.lineTo(8, 10); p.lineTo(12, 21); p.moveTo(12, 3); p.lineTo(16, 10); p.lineTo(12, 21); p.stroke();
      break;
    }
    case "rope": line("#1A1410", 6); for (let i = 0; i < 3; i++) { p.beginPath(); p.ellipse(12, 10 + i * 4, 8 - i, 3, 0, 0, Math.PI * 2); p.stroke(); } line("#A07840", 3); for (let i = 0; i < 3; i++) { p.beginPath(); p.ellipse(12, 10 + i * 4, 8 - i, 3, 0, 0, Math.PI * 2); p.stroke(); } break;
    case "bones": line("#1A1410", 6); p.beginPath(); p.moveTo(5, 18); p.lineTo(19, 6); p.stroke(); line("#E8E0C8", 3.5); p.beginPath(); p.moveTo(5, 18); p.lineTo(19, 6); p.stroke(); p.fillStyle = "#E8E0C8"; for (const [x, y] of [[4, 16], [7, 20], [17, 4], [21, 8]]) { p.beginPath(); p.arc(x, y, 2.4, 0, Math.PI * 2); p.fill(); } break;
    case "key": line("#1A1410", 5); p.beginPath(); p.moveTo(8, 12); p.lineTo(20, 12); p.stroke(); line("#E0B840", 3); p.beginPath(); p.moveTo(8, 12); p.lineTo(20, 12); p.moveTo(17, 12); p.lineTo(17, 16); p.moveTo(20, 12); p.lineTo(20, 15); p.stroke(); outlined(p, () => { p.arc(7, 12, 4, 0, Math.PI * 2); }, "#E0B840", "#1A1410", 1.5); break;
    case "dagger": case "knife": blade(8, "#D8DCE8"); break;
    case "short_sword": blade(11, "#D8DCE8"); break;
    case "long_sword": case "great_sword": blade(14, "#E8ECF4"); break;
    case "axe": line("#1A1410", 5); p.beginPath(); p.moveTo(6, 20); p.lineTo(16, 8); p.stroke(); line("#7A5A30", 3); p.beginPath(); p.moveTo(6, 20); p.lineTo(16, 8); p.stroke(); outlined(p, () => { p.moveTo(14, 9); p.lineTo(21, 5); p.lineTo(21, 13); p.lineTo(15, 12); }, "#C8CCD4", "#1A1410", 1.5); break;
    case "mace": case "hammer": case "club": line("#1A1410", 5); p.beginPath(); p.moveTo(6, 20); p.lineTo(15, 9); p.stroke(); line("#7A5A30", 3); p.beginPath(); p.moveTo(6, 20); p.lineTo(15, 9); p.stroke(); outlined(p, () => { if (key === "club") p.ellipse(16, 7, 4, 5, 0.8, 0, Math.PI * 2); else p.rect(13, 3, 8, 8); }, key === "club" ? "#7A5A30" : "#A8ACB4", "#1A1410", 1.5); break;
    case "staff": line("#1A1410", 5); p.beginPath(); p.moveTo(7, 21); p.lineTo(16, 4); p.stroke(); line("#6A4A5A", 3); p.beginPath(); p.moveTo(7, 21); p.lineTo(16, 4); p.stroke(); p.fillStyle = "#80E0FF"; p.beginPath(); p.arc(16, 4, 2.5, 0, Math.PI * 2); p.fill(); break;
    case "spear": line("#1A1410", 4); p.beginPath(); p.moveTo(5, 20); p.lineTo(18, 7); p.stroke(); line("#7A5A30", 2); p.beginPath(); p.moveTo(5, 20); p.lineTo(18, 7); p.stroke(); outlined(p, () => { p.moveTo(16, 9); p.lineTo(21, 3); p.lineTo(19, 10); }, "#D8DCE8", "#1A1410", 1.5); break;
    case "bow": case "longbow": line("#1A1410", 4); p.beginPath(); p.arc(10, 12, 9, -1.1, 1.1); p.stroke(); line("#8A6A30", 2); p.beginPath(); p.arc(10, 12, 9, -1.1, 1.1); p.stroke(); line("#E8E8E0", 1); p.beginPath(); p.moveTo(14, 4); p.lineTo(14, 20); p.stroke(); break;
    case "robe": outlined(p, () => { p.moveTo(8, 4); p.lineTo(16, 4); p.lineTo(20, 9); p.lineTo(17, 10); p.lineTo(18, 21); p.lineTo(6, 21); p.lineTo(7, 10); p.lineTo(4, 9); }, "#6A5A9A", "#1A1410", 1.5); break;
    case "leather": case "ring_mail": case "scale": case "chain": case "plate": {
      const col = { leather: "#8A5A2A", ring_mail: "#8A8A90", scale: "#7A9A80", chain: "#A0A4AC", plate: "#C0C4CC" }[key];
      outlined(p, () => { p.moveTo(7, 4); p.lineTo(17, 4); p.lineTo(21, 8); p.lineTo(18, 11); p.lineTo(18, 20); p.lineTo(6, 20); p.lineTo(6, 11); p.lineTo(3, 8); }, col, "#1A1410", 1.5);
      if (key === "chain" || key === "ring_mail") { p.fillStyle = "rgba(0,0,0,0.25)"; for (let y = 7; y < 19; y += 3) for (let x = 7; x < 18; x += 3) p.fillRect(x, y, 1.5, 1.5); }
      if (key === "scale") { line("#1A1410", 1); for (let y = 8; y < 19; y += 3) { p.beginPath(); p.moveTo(7, y); p.lineTo(17, y); p.stroke(); } }
      break;
    }
    case "buckler": case "shield": case "tower": outlined(p, () => { p.moveTo(12, 3); p.lineTo(20, 6); p.lineTo(19, 14); p.lineTo(12, 21); p.lineTo(5, 14); p.lineTo(4, 6); }, key === "buckler" ? "#8A6A3A" : key === "tower" ? "#5A6A8A" : "#A03030", "#1A1410", 1.5); line("#E8C040", 2); p.beginPath(); p.moveTo(12, 7); p.lineTo(12, 17); p.moveTo(8, 11); p.lineTo(16, 11); p.stroke(); break;
    case "cap": case "helm": case "great_helm": outlined(p, () => { p.arc(12, 13, 8, Math.PI, 0); p.lineTo(20, 17); p.lineTo(4, 17); }, key === "cap" ? "#8A5A2A" : "#B8BEC8", "#1A1410", 1.5); if (key !== "cap") { p.fillStyle = "#1A1410"; p.fillRect(6, 12, 12, 2.5); } if (key === "great_helm") { p.fillStyle = "#C83030"; p.fillRect(11, 2, 2, 5); } break;
    case "ring": line("#1A1410", 4.5); p.beginPath(); p.arc(12, 14, 6, 0, Math.PI * 2); p.stroke(); line("#E8C040", 2.5); p.beginPath(); p.arc(12, 14, 6, 0, Math.PI * 2); p.stroke(); outlined(p, () => { p.moveTo(12, 3); p.lineTo(15, 7); p.lineTo(12, 10); p.lineTo(9, 7); }, "#E03030", "#1A1410", 1); break;
    case "amulet": line("#1A1410", 2.5); p.beginPath(); p.arc(12, 8, 7, 0.3, Math.PI - 0.3, true); p.stroke(); line("#E8C040", 1.2); p.beginPath(); p.arc(12, 8, 7, 0.3, Math.PI - 0.3, true); p.stroke(); outlined(p, () => { p.arc(12, 16, 4.5, 0, Math.PI * 2); }, "#3060E0", "#1A1410", 1.5); p.fillStyle = "#C0E0FF"; p.beginPath(); p.arc(11, 15, 1.5, 0, Math.PI * 2); p.fill(); break;
    default: p.fillStyle = "#A09070"; p.font = "bold 16px Georgia"; p.textAlign = "center"; p.fillText("?", 12, 18);
  }
  return c;
};
CM.art.itemIcon = function (item, size = 24, look = "drawn") {
  if (look === "pixel" && CM.art.hasLook("pixel") && CM.packs.pixel.index[CM.art.itemKey(item)]) return CM.art.tile(CM.art.itemKey(item), size);
  return CM.art.glyph(item, size);
};
// a spell's or skill's icon (the Pixel theme has them; the others go without)
CM.art.spellIcon = function (id, size = 18, look = "drawn") {
  if (look !== "pixel" || !CM.art.hasLook("pixel") || !(CM.packs.pixel.index[`s.${id}`])) return null;
  return CM.art.tile(`s.${id}`, size);
};
// who made the art, for the Credits dialog
CM.art.credits = function () {
  const lines = [["The drawn theme, the music and the sounds", "painted and composed in code, in this file."]];
  if (CM.packs && CM.packs.credits) {
    lines.push(["The Pixel theme", CM.packs.credits.pixel]);
    lines.push(["The Stone theme", CM.packs.credits.stone]);
  }
  return lines;
};
