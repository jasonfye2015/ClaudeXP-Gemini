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
- Planned: the built sets kept between visits in the browser's store, so a second start only uploads them. Built and
  measured, and taken out again: reading two sets back from IndexedDB took 3.1 s in this browser, painting them 0.25 s
  (and the Pixel packs decode in about 1.3 s, so the title never waited long for them). Instead, what the start
  measured as slow was made quick: the 56 sounds made when first wanted (and the rest in idle moments), not all at the
  start (272 ms); the shaders compiled beside the start (KHR_parallel_shader_compile); the worker painting in software
  and only after a floor has settled (v26.3's paintings had stalled the frame 270-400 ms when they came back); and the
  side map drawn again only when something on it changes (a tenth of the work).
