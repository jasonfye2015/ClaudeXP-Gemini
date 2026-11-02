# Upgrade plan 21: performance and tech (v26.0 - v26.4)

Asked for 2026-11-01: items 41-45 of the list ("8. Performance and tech"). Measured first, in the browser the
Timeline uses (QtWebEngine, Chromium 140), on this machine (v25.3):
- the page loaded 3.8 s, the art ready 4.2 s; a fresh town set built in 241 ms (Pixel), 618 ms (Stone), 112 ms (Drawn)
- the town set's textures: Pixel 165 MB, Stone 348 MB, Drawn 178 MB (162 of the town's own layers at the look's size)
- a floor's mesh made again: the town 84 ms, the Wood 118 ms, a dungeon floor 6 ms - whenever a door opens, a mark is
  left, the windows light or the trees turn
- frames: 60 a second settled everywhere; a few of 60-90 ms in the first seconds after a new game

## v26.0 - smaller textures (41)
- Right-sized: the Pixel look's pictures (pixel art) at 128; Stone's photographs at 512 and only they; the outdoors'
  drawn pictures in an array of their own at 256; the small sprites (motes, sparks, signs, moons, keys) four to a layer.

## v26.1 - partial rebuilds (43)
- The floor's mesh in chunks: a door, a mark, a trace, a lit window or a turned tree makes again only the chunk it is in.

## v26.2 - instanced drawing (44)
- The standing props, the crops and the grass's billboards drawn as instances of one quad, not rebuilt as triangles
  every frame.

## v26.3 - painting off the main thread (42)
- The drawn sets' pictures painted in a worker (OffscreenCanvas) where the browser has it, so building a set never
  stops the screen; the old way where it hasn't.

## v26.4 - faster loading (45)
- The built sets kept between visits (the pixels, by look and season, in the browser's own store), so a second start
  only uploads them; thrown away when the game's version changes.
