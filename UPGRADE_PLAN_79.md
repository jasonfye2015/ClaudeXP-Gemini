# Upgrade plan 79: the Scarp, the falls, and the sea

Asked for: one side of the forest lifted into a plateau, with a waterfall off it into a river that runs to an ocean,
and the whole land found, in the end, to be an island in a wide sea.

## Where

In the south-east of the Deep Wood, against the hill's cliffs. Every seed leaves this corner as plain forest, so
nothing a seed placed has to move. The plateau sits as high as the cliff tops (2.2), so the heath runs into the hill
as one piece of ground.

## v128.0: the Scarp and the falls

- **The land** (`23e-scarp.js`, laid after everything the seed placed):
  - A high heath (x 45 to 57, y 57 to 79) of heather and bare rock, walled by its own layered stone, the "scarp" kind.
  - One stair cut into the west face from the South Meadow, a step a square, with rock on both sides.
  - Two tors standing on the heath.
  - A tarn, and the spring that fills it.
  - A stream that crosses the heath under a plank bridge and goes over the west edge in a fall, into a plunge pool
    among the trees.
  - From the pool the stream runs west through the forest to the river.
  - The Lookout, a cairn at the heath's south edge.
- **Heights:**
  - They are the floor's levels (`69zzi-levels.js`), made with the land and never saved.
  - The surface mesh now honours levels under the sky. A square's ground is drawn at its level, and where a neighbour
    is higher, a face of the scarp's stone rises to it.
  - Sprites, figures and the eye already follow the levels.
  - The rim and the stair walls are solid, so the only way up or down is the stair. The fall is never a way up, even
    when the Wood freezes.
- **Seen** (`77s-scarp.js`):
  - Ground: heath and rock.
  - Plants and stones on the heath sit on the heath.
  - Boulders lie at the scarp's foot, along its lip and around the tors.
  - The falls: a white rope of water down the face, a veil of spray, foam in the pool, mist rising off it, and a
    curtain of ice in snow.
- **Heard:** the falls roar, louder the nearer the party is (`76zzzzs-placeamb.js`).
- **Places:** the Scarp, the Scarp stair, the foot of the Scarp, the Falls and the Lookout are named. The stair, the
  falls, the Lookout and the spring join the Where-to list once seen.

## v129.0: the shore, the sea, the island

- **The land grows south** to the coast:
  - A fringe of trees, then the Strand: sand from the forest's edge to the water, where the river meets the sea.
  - A ford at the river's mouth.
  - Tracks down to the shore from both meadows, with stepping stones over the falls' stream.
- **The sea past the land's edge** on the north, the west and the south:
  - It ripples, carries the sky and glints, using the water's own shader.
  - The hill and the town stay on the east.
  - The far rings of hills stand only beyond the hill.
- **The discovery:**
  - The first sight of the sea from the Strand.
  - From the Lookout, the whole of it: water on every side.
  - It is remembered with the village, so later runs know it.
  - Claude has a word to say about it once he hears.
- **The map:** once the island is known, it shows the land as a land with sea around it.
