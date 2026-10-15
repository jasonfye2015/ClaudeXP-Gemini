Furcadia art overrides
======================

Furcadia draws all of its own art. Put a PNG here and it's used instead (restart Furcadia to see it).
Anything missing stays hand-drawn, so you can replace one picture at a time.

splash.png                      The picture shown while connecting (about 640 x 340).

tiles\<name>.png                Floor tiles: 64 x 32 diamonds, transparent outside the diamond.
                                grass, flowers, darkgrass, dirt, cobble, flagstone, wood, boardwalk, sand, rug,
                                water, deepwater

objects\<name>.png              Objects: any size, transparent. The object's base point is centred left-to-right
                                and 16 px above the bottom edge of the picture.
                                tree, bigtree, pine, palm, bush, rock, bench, lamp, fountain, fence, sign, portal,
                                campfire, log, mushroom, table, chair, stool, cushion, umbrella, bookshelf,
                                fireplace, wall, woodwall, barrel, crate, counter, lantern, plant, shell

furres\<type>\<pose>_<facing>.png
                                Furre sprites: 48 x 64, transparent, feet at pixel (24, 58).
                                pose: stand, sit, lie     facing: 0 down-right, 1 down-left, 2 up-right, 3 up-left
                                type: canine, feline, lapine, rodent, mustelid, ursine, avian, dragon, equine,
                                      bovine, cervine, reptile, aquatic, insect, other
                                Paint the recolourable parts in these key colours (darker shades keep their
                                shading):  fur #FF00FF   markings #00FFFF   eyes #FFFF00   clothes #00FF00

reference\                      Screenshots of the real client, for matching the look. Not loaded by the program.

Per-buddy settings: add a "furcadia" section to a buddy's AIM contact file, for example
  "furcadia": {"species": "arctic fox", "desc": "A fluffy white fox in a blue scarf.",
               "look": {"kind": "canine", "fur": "#F2F0EA", "markings": "#B8B8B8", "eyes": "#3A7AD8",
                        "clothes": "#3050B0", "wings": false},
               "dreams": ["commons", "glade", "seaside", "inn"]}
