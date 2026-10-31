"use strict";
// The window around the dungeon: the title (what you set out with, the Hall of Fame and its details, settings), the
// party and the log under the view, the automap, the bag and the merchant, the little dialogs, and the end of a run.
// It listens to the Game and redraws; it never decides the rules.
CM.UI = class {
  constructor(game, root) {
    this.game = game;
    this.root = root;
    this.bagRow = -1; this.shopRow = -1;
    this.portraits = {};
    root.innerHTML = `
<div id="title" class="screen">
  <div class="backdrop-slot"></div><div class="shade"></div>
  <div class="sheet">
    <h1><span class="emblem-slot"></span>Claude and Magic</h1>
    <div class="tagline">Twenty floors down, the Lich King waits - and below him, the Deep. Four go in together.</div>
    <div class="note" id="title-note"></div>
    <div class="honours" id="honours"></div>
    <div class="card" id="expedition">
      <h2>Expedition</h2>
      <div class="row slots" id="slots-row"><span class="small">Expedition</span><button data-slot="1">1</button><button data-slot="2">2</button><button data-slot="3">3</button></div>
      <div class="row"><button id="btn-continue" class="primary">Continue</button><span id="continue-note" class="small"></span></div>
      <div class="row"><button id="btn-new" class="primary">New Expedition</button><label for="seed">Seed</label><input id="seed" type="text" maxlength="40" spellcheck="false"><button id="btn-dice" title="Another seed">&#x2684;</button><button id="btn-daily" title="Today's dungeon: the same one for everyone, today">Today's</button><button id="btn-weekly" title="This week's challenge: one seed, three mutators and a party the seed rolls, the same for everyone all week">This week's</button></div>
      <p class="small">A run code (CM1:...) from a summary card goes in the seed box too: New Expedition then sets out with that party, difficulty and kit.</p>
      <p>The same seed lays out the same fifty floors, so a dungeon can be tried again - or handed to a friend - and
      the dice of every fight are the seed's too: the same fight, fought the same way, goes the same way. The run saves
      as you go; when the whole party falls, it ends, and the deepest runs go in the Hall of Fame.</p>
      <h2>The callings</h2>
      <div id="classes"></div>
      <p id="start-with"></p>
    </div>
    <div class="card" id="fame"><h2>Hall of Fame <span class="boards"><button data-board="dungeon" class="on" title="Runs down the dungeon: to the Lich King, and to the bottom">The dungeon</button><button data-board="endless" title="Endless expeditions: how deep they went">Endless</button><button data-board="weekly" title="This week's challenge: the runs on this week's seed">This week</button></span></h2><table></table><h2 class="later">Unlocks</h2><div id="unlocks"></div><h2 class="later">Trophies</h2><div id="trophies"></div><h2 class="later">In memoriam</h2><div id="memorial"></div><h2 class="later">Achievements</h2><div id="achievements"></div></div>
    <div class="foot"><label for="look">Theme</label><select id="look" title="The look of the dungeon - change it any time, here or in Settings"></select><button id="btn-village">The Village</button><button id="btn-film">Films</button><button id="btn-settings">Settings</button><button id="btn-keys">Keys</button><button id="btn-transfer">Export / Import</button><button id="btn-stats">Statistics</button><button id="btn-credits">Credits</button><button id="btn-install" hidden title="Install the game as an app of its own: it opens from an icon, and works without the network">Install</button></div>
    <div class="version"></div>
  </div>
</div>
<div id="create" class="screen">
  <div class="sheet">
    <h1>Who goes down?</h1>
    <div class="tagline">Four of them. Name them, choose their callings, roll their stats, and set them in their rows. The advice is only advice.</div>
    <div id="slots"></div>
    <div class="card" id="advice"><h2>Advice</h2><ul></ul></div>
    <div class="foot"><button id="btn-suggest">Suggest a party</button><button id="btn-reroll-all">Reroll everyone</button>
      <label for="create-seed">Seed</label><input id="create-seed" type="text" maxlength="40" spellcheck="false">
      <label for="kit">Kit</label><select id="kit" title="What the deepest run so far has earned"></select>
      <label for="difficulty">Difficulty</label><select id="difficulty" title="How hard the dungeon is"></select>
      <label for="mode">Expedition</label><select id="mode" title="The dungeon has a bottom; an Endless expedition does not; an Awakened one is the same seed, mirrored and deeper, once the bottom has been reached"><option value="dungeon">The dungeon</option><option value="endless">Endless</option><option value="awakened" id="mode-awakened">Awakened</option><option value="otherdream" id="mode-otherdream">The Other Dream</option></select>
      <label for="ascension" id="ascension-label">Ascension</label><select id="ascension" title="A rule more for every rung climbed: win on Fair or above to open the next"></select>
      <label for="iron" id="iron-label"><input type="checkbox" id="iron"> Iron</label>
      <button id="btn-setout" class="primary">Set out</button><button id="btn-create-back">Back</button></div>
    <div class="small" id="create-note"></div>
  </div>
</div>
<div id="play" class="screen">
  <div class="top">
    <div id="view"><div class="canvas-slot"></div><canvas id="hud"></canvas><div class="vignette"></div><div class="compass"></div><div class="sky" title="The hour, the day and the moon. Click it, or K, for the calendar."><svg class="dial" viewBox="-40 -40 80 80" aria-hidden="true"><defs><clipPath id="cm-dialclip"><circle r="37"/></clipPath><linearGradient id="cm-dialsky" x1="0" y1="0" x2="0" y2="1"><stop class="skytop" offset="0"/><stop class="skylow" offset="0.55"/></linearGradient></defs><g clip-path="url(#cm-dialclip)"><rect x="-40" y="-40" width="80" height="80" fill="url(#cm-dialsky)"/><g class="stars"><circle cx="-22" cy="-18" r="0.9"/><circle cx="-8" cy="-30" r="0.7"/><circle cx="6" cy="-22" r="1"/><circle cx="18" cy="-28" r="0.7"/><circle cx="27" cy="-12" r="0.9"/><circle cx="-30" cy="-6" r="0.7"/><circle cx="12" cy="-9" r="0.6"/><circle cx="-14" cy="-10" r="0.6"/></g><path class="arc" d="M-25 2A25 25 0 0 1 25 2"/><g class="sun"><circle class="glow" r="10"/><circle class="disc" r="5.5"/></g><g class="moon"><circle class="dark" r="6"/><path class="lit"/></g><path class="ground" d="M-40 4C-26 -1 -14 6 0 3S24 -1 40 4L40 40L-40 40Z"/></g><circle class="rim" r="37"/></svg><div class="clocktext"><div class="row1"><b class="time"></b><span class="moonslot"></span></div><div class="hourword"></div><div class="date"></div><div class="wx"></div><div class="fest"></div></div></div><div class="fps"></div><div id="towerhud"><div class="cross"></div><div class="tname"></div><div class="tboss"><b></b><i></i></div><div class="tbars"><div class="thp"><i></i><span></span></div><div class="tmp"><i></i><span></span></div><div class="tarrows"></div></div><div class="thelp">W A S D move - mouse or arrows turn - click or Space shoots - right-click or R the great spell - E at the ladder - Esc the menu</div></div><div class="hurt"></div><div class="blink"></div><div class="fall"></div><div class="tint"></div><div id="floats"></div><div class="titlecard"><b></b><small></small></div><div class="hint"></div><div class="filmbar"><button data-film="toggle">Pause</button><button data-film="speed">1x</button><button data-film="fight">Next fight</button><button data-film="floor">Next floor</button><button data-film="stop">Stop (Esc)</button><span class="small"></span></div></div>
    <div id="side"><canvas id="automap" width="290" height="290"></canvas><div class="where"></div><div class="purse"></div><div class="light"></div><div class="temper"></div><div class="follower"></div><div class="belt" id="belt" title="The belt: four things to hand (keys 5 to 8). In a fight the first used in a round costs no turn."></div></div>
  </div>
  <div id="party"></div>
  <div id="log" role="log" aria-live="polite"></div>
  <div id="actions"></div>
</div>
<div id="bag" class="screen">
  <h2 id="bag-title"></h2>
  <div class="filters" id="bag-filters"></div>
  <div class="lists"><div class="list" id="bag-list"></div><div class="list" id="shop-list"></div></div>
  <div class="note" id="bag-note"></div>
  <div class="give" id="bag-give"></div><div class="give" id="bag-belt"></div>
  <div class="act"><button id="btn-buy">Buy</button><button id="btn-sell">Sell</button><button id="btn-sell-shown" title="Everything the filter shows (keys, relics and a Homecoming scroll that remembers a square are kept)">Sell all shown</button><button id="btn-sell-spare" title="Gear nobody wears, known and not cursed">Sell spare gear</button><button id="btn-sort" title="Weapons, then armour, shields, helms, rings, amulets, then the rest - the best first">Sort the pack</button><button id="btn-bag-done" class="primary">Done</button></div>
</div>
<div class="dialog" id="dlg-settings"><div class="box"><h2>Settings</h2>
  <div class="row"><label for="set-sound">Sound</label><input type="checkbox" id="set-sound"></div>
  <div class="row"><label for="set-volume">Volume</label><input type="range" id="set-volume" min="0" max="100"></div>
  <div class="row"><label for="set-music">Music (a tune for each depth, the fight, the camp)</label><input type="checkbox" id="set-music"></div>
  <div class="row"><label for="set-music-volume">Music volume</label><input type="range" id="set-music-volume" min="0" max="100"></div>
  <div class="row"><label for="set-look">Theme - the look of the dungeon</label><select id="set-look"></select></div>
  <div class="small" id="set-look-note"></div>
  <div class="row"><label for="set-detail">Detail - the grass, stones and bones on the floors (when frames come late it is lowered first)</label><select id="set-detail"><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></div>
  <div class="row"><label for="set-smooth">Smooth steps and turns (off: snap, the classic way)</label><input type="checkbox" id="set-smooth"></div>
  <div class="row"><label for="set-fps">Show frames per second (F3)</label><input type="checkbox" id="set-fps"></div>
  <div class="row"><label for="set-tap">Tap or click the view to move (the sides turn, the top walks, the bottom steps back)</label><input type="checkbox" id="set-tap"></div>
  <div class="row"><label for="set-skipwalk">Skip the walk: a new run begins at the shaft's mouth, not at the party's door</label><input type="checkbox" id="set-skipwalk"></div>
  <div class="row"><label for="set-season">The season: the real date's, or one pinned for every new run</label><select id="set-season"><option value="">By the date</option><option value="spring">Spring</option><option value="summer">Summer</option><option value="autumn">Autumn</option><option value="winter">Winter</option></select></div>
  <div class="row"><label for="set-autoland">Automatic takes a day in the land before the shaft: the Wood's nodes, the open cave with a pick, the farm</label><input type="checkbox" id="set-autoland"></div>
  <div class="row"><label for="set-render">Render scale - fewer pixels on a slow machine (Auto steps down when frames come late)</label><select id="set-render"><option value="auto">Auto</option><option value="full">Full</option><option value="three">Three quarters</option><option value="half">Half</option></select></div>
  <div class="row"><label for="set-speed">Combat speed - how long bolts fly and sparks hang</label><select id="set-speed"><option value="normal">Normal</option><option value="fast">Fast</option><option value="instant">As good as instant</option></select></div>
  <div class="row"><label for="set-text">Text size</label><select id="set-text"><option value="normal">Normal</option><option value="large">Large</option><option value="larger">Larger</option></select></div>
  <div class="row"><label for="set-motion">Reduce motion - no shaking, no flashes, no washes of colour over the view</label><input type="checkbox" id="set-motion"></div>
  <div class="row"><label for="set-contrast">High contrast - brighter text and sharper edges</label><input type="checkbox" id="set-contrast"></div>
  <div class="row"><label for="set-swapab">Gamepad: swap A and B (confirm with B, back with A)</label><input type="checkbox" id="set-swapab"></div>
  <div class="row"><label for="set-layout">Handheld layout - thumb-sized buttons and larger text, as on a Steam Deck</label><select id="set-layout"><option value="auto">Auto (by the screen's shape)</option><option value="on">On</option><option value="off">Off</option></select></div>
  <div class="small" id="set-storage"></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-keys"><div class="box"><h2>Keys</h2><p class="small">Change sets a key: press the one you want. Esc and the arrows stay as they are.</p><table class="keys kb"></table>
  <h2>Gamepad</h2><p class="small" id="pad-note"></p><table class="keys pad"></table><div class="end"><button id="btn-keys-reset">Reset</button><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-credits"><div class="box"><h2>Credits</h2><div id="credits"></div><div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-transfer"><div class="box"><h2>Export / Import</h2>
  <p class="small">Your run, the Hall of Fame and your settings, as text. Copy it to keep it or to carry it to another
  browser; paste a copy here and Import to bring it back. Download saves it as a file; drop a saved file on the box to read it in.</p>
  <textarea id="transfer-text" spellcheck="false"></textarea>
  <div class="small" id="transfer-note"></div>
  <div class="end"><button id="btn-copy">Copy</button><button id="btn-download">Download</button><button id="btn-link" title="The save as a link: it opens the game with the save in it, and is stored nowhere else">Link</button><button id="btn-import">Import</button><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-link"><div class="box"><h2 id="link-title"></h2><p class="small" id="link-text"></p><div class="small" id="link-note"></div>
  <div class="end"><button id="btn-link-yes" class="primary">Yes</button><button class="close">Not now</button></div></div></div>
<div class="dialog" id="dlg-stats"><div class="box statsbox"><h2>Statistics</h2><div id="stats"></div><div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-pause"><div class="box"><h2>Paused</h2>
  <p class="small">The run is saved as you go.</p>
  <div class="end"><button id="btn-pause-clip" title="Ten seconds of the view, saved as a .webm">Record a clip</button><button id="btn-pause-settings">Settings</button><button id="btn-pause-title">Back to the title</button><button class="close primary">Carry on</button></div></div></div>
<div class="dialog" id="dlg-sheet"><div class="box sheetbox">
  <h2 id="sheet-title"></h2>
  <div class="sheet-grid"><div id="sheet-left"></div><div id="sheet-right"></div></div>
  <div id="sheet-boon"></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-temple"><div class="box"><h2>The Temple</h2>
  <p class="small">An old priest keeps a shrine by the camp fire, and asks for the upkeep of his candles.</p>
  <div class="row"><label>Cure the small ailments - poison, sleep, paralysis, blindness - for everyone</label><button data-service="cure">30 gold</button></div>
  <div class="row"><label>Lift a curse</label><button data-service="uncurse">60 gold</button></div>
  <div class="row"><label>Stone to flesh</label><button data-service="unstone">150 gold</button></div>
  <div class="row"><label>Raise the fallen (100 gold a level)</label><button id="btn-temple-raise">Raise</button></div>
  <div class="row"><label>The priest's scribe names everything unknown you carry</label><button id="btn-scribe">25 gold</button></div>
  <div class="row"><label>Close the wounds of the fallen-and-risen (40 gold a hero)</label><button data-service="wounds">Wounds</button></div>
  <div class="row"><label>A tithe: a tenth of the purse, for a blessing on the band (+1 defence, blows land surer, five floors)</label><button id="btn-tithe">Tithe</button></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-tavern"><div class="box"><h2>The Tavern</h2>
  <p class="small">Three who'd come along, for a price - to take the place of a hero who has fallen or turned to stone. What the fallen wore besides weapon and armour stays with the party.</p>
  <div id="recruits"></div>
  <div id="fence"></div>
  <div class="small" id="tavern-note"></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-smith"><div class="box journalbox"><h2>The Smith</h2>
  <p class="small">A dwarf of the deep halls, who came up and stayed, works a forge by the camp. A diamond and his fee put +1 on a piece of gear (three times at most);
  a ruby, a sapphire or a sunstone goes into a weapon for fire, frost or holiness.</p>
  <div class="small" id="smith-gems"></div><div id="smith-list"></div><div class="small" id="smith-note"></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-vault"><div class="box journalbox"><h2>The Vault</h2>
  <p class="small">The merchant keeps one thing in an iron box for whoever comes after: leave an heirloom here, and the next party to reach a camp may take it up.</p>
  <div class="list-title">In the vault</div><div class="recruit" id="vault-held"></div>
  <div class="list-title">Leave something</div><div id="vault-list"></div><div class="small" id="vault-note"></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-film"><div class="box"><h2>Watch a film</h2>
  <p class="small">A run, watched in the real view - the walk, the fights, the choices - from its seed and its log. The Hall of Fame keeps the last six runs' films; a film code (CM2:...) from a summary card plays anyone's.</p>
  <div id="film-list"></div>
  <textarea id="film-text" spellcheck="false" placeholder="Paste a film code here, CM2:..."></textarea>
  <div class="small" id="film-note"></div>
  <div class="end"><button id="btn-film-play">Watch</button><button id="btn-film-link" title="The film code in the box, as a link anyone can open">Link</button><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-home"><div class="box journalbox"><h2>Your house</h2>
  <p class="small" id="home-what"></p><div id="home-rooms"></div><div class="small" id="home-note"></div>
  <div class="end"><button id="btn-home-build">Build</button><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-library"><div class="box journalbox"><h2>The Library</h2>
  <p class="small" id="library-what"></p><div id="library-rooms"></div><div class="small" id="library-note"></div>
  <div class="end"><button id="btn-library-build">Build</button><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-guild"><div class="box journalbox"><h2>The Guildhall</h2>
  <p class="small" id="guild-what"></p><div id="guild-rooms"></div><div class="small" id="guild-note"></div>
  <div class="end"><button id="btn-guild-build">Build</button><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-chronicler"><div class="box journalbox"><h2>The Chronicler's House</h2>
  <p class="small">Wren keeps the town's memory dry: the films of runs, the statistics, the ledger, the Hall of Fame and the memorial's book.</p>
  <div id="chronicler-rooms"></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-building"><div class="box"><h2 id="building-title">A door</h2>
  <p class="small" id="building-what"></p><div class="small" id="building-levels"></div><div class="small" id="building-note"></div>
  <div class="end"><button id="btn-building-build">Build</button><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-village"><div class="box journalbox"><h2>The Village</h2>
  <p class="small">The surface, between runs. Every run brings home renown - floors, guardians, the crown, titles earned, the week's seed - and the village grows with it. Renown never buys a blow in the dungeon.</p>
  <div class="small" id="village-renown"></div><div id="village-buildings"></div>
  <div class="list-title">The people</div><div id="village-people"></div>
  <div class="list-title">Contracts this week</div><div id="village-contracts"></div>
  <div class="list-title">The guildhall's trainers</div><div id="village-trainers"></div>
  <div class="list-title">The shrine: candles</div><div id="village-shrine"></div><div class="small" id="village-note"></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-alchemist"><div class="box journalbox"><h2>The Alchemist</h2>
  <p class="small">A woman with a copper still by the camp fire. The monsters of each depth drop something she wants - moss, weed, soot, dust, slag, salt, sap - and she makes potions, oils and worse of it, for gold.</p>
  <div class="small" id="alchemist-have"></div><div id="alchemist-list"></div><div class="small" id="alchemist-note"></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-choice"><div class="box"><h2 id="choice-title"></h2><p id="choice-text" class="lore"></p><div id="choice-options" class="answers"></div>
  <div class="end"><button class="close">Step back</button></div></div></div>
<div class="dialog" id="dlg-second"><div class="box"><h2>The Guild's Letter</h2>
  <p class="small">With a guildhall of the second level, a hero at twenty may take a second calling at a camp, for 200 renown: its first two spells or skills are theirs for good.</p>
  <div id="second-list"></div><div class="small" id="second-note"></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-waystone"><div class="box"><h2>The Waystones</h2>
  <p class="small">A mark chalked by every camp fire the party has reached. From one camp, the old road leads to another: the floors between stay as you left them.</p>
  <div id="waystone-list"></div><div class="small" id="waystone-note"></div>
  <div class="end"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-lore"><div class="box readbox"><h2>Carved into the stone</h2><p id="lore-text" class="lore hand"></p><div class="small" id="lore-hint">Space shows it all.</div>
  <div class="end"><button class="close primary">Walk on</button></div></div></div>
<div class="dialog" id="dlg-talk"><div class="box"><h2 id="talk-title"></h2><p id="talk-text" class="lore"></p>
  <div class="end"><button id="talk-more" hidden>More</button><button class="close primary">Walk on</button></div></div></div>
<div class="dialog" id="dlg-farm"><div class="box"><h2>The farm in the First Glade</h2><p id="farm-head" class="lore"></p><div id="farm-rows"></div><div id="farm-more"></div><p id="farm-note" class="small"></p>
  <div class="end"><button class="close primary">Back to the path</button></div></div></div>
<div class="dialog" id="dlg-hut"><div class="box"><h2>The hermit's hut</h2><p class="lore">"Hides I'll take, by daylight. Trouble I won't." The hermit tans and stitches for 20 gold a piece.</p><div id="hut-list"></div><p id="hut-note" class="small"></p>
  <div class="end"><button class="close primary">Walk on</button></div></div></div>
<div class="dialog" id="dlg-riddle"><div class="box"><h2>Runes on the door</h2><p id="riddle-q" class="lore"></p><div id="riddle-answers" class="answers"></div>
  <p class="small">The answer is carved somewhere above. A wrong one burns.</p><div class="end"><button class="close">Step back</button></div></div></div>
<div class="dialog" id="dlg-claudeita"><div class="box"><h2>Claudeita's cave</h2><p class="lore">The mouth breathes warm air that smells of wet stone and smoke. Whoever goes in goes alone, with a wand: a caster, who knows what a wand is for.</p><div id="claudeita-who"></div><div class="small" id="claudeita-note"></div><div class="row"><button class="close">Not now</button></div></div></div>
<div class="dialog" id="dlg-magetower"><div class="box"><h2>The Mage Tower</h2><p class="lore">The doors are taller than three men, and warm to the touch. Whoever goes in, goes in alone: a caster, or someone with a bow.</p><div id="magetower-who"></div><div class="small" id="magetower-note"></div><div class="row"><button class="close">Not now</button></div></div></div>
<div class="dialog" id="dlg-cabin"><div class="box cabinbox"><div id="cabin-body"></div></div></div>
<div class="dialog" id="dlg-calendar"><div class="box journalbox calbox"><h2>The Calendar</h2><div id="calendar-body"></div><div class="row"><button class="close">Close</button></div></div></div>
<div class="dialog" id="dlg-whereto"><div class="box journalbox"><h2>Where to?</h2><div class="small">The party walks there by what it knows, and stops for whatever it meets on the way. Any key stops it.</div><div id="whereto-list"></div><div class="row"><button class="close">Back</button></div></div></div>
<div class="dialog" id="dlg-journal"><div class="box journalbox"><h2>Journal <span class="boards"><button data-page="journal" class="on" title="Everything read and heard this run, in the order it came">Journal</button><button data-page="codex" title="The story of Caer Duin, chapter by chapter: what has been read, and the blanks">Codex</button><button data-page="things" title="Every kind of thing the dungeon holds, and which you have found">Things</button><button data-page="errands" title="What the townsfolk have asked of you, and what they ask now">Errands</button></span></h2><div id="journal-list"></div>
  <div class="end"><button class="close primary">Close</button></div></div></div>
<div class="dialog" id="dlg-over"><div class="box overbox"><div class="emblem-slot"></div><h2 id="over-title"></h2><p id="over-text" class="lore"></p>
  <div class="roll" id="over-party"></div><div class="small" id="over-retire"></div><div class="tally" id="over-tally"></div><div class="page ended" id="over-page"></div>
  <div class="end"><button id="btn-over-card" class="ended">Summary card</button><button id="btn-over-page" class="ended" title="The ending as an illuminated page: the chapters the party completed, and blank lines for the rest">Save the page (PNG)</button><button class="close primary ended">To the title</button>
    <button id="btn-over-daylight" class="crown">Into the daylight</button><button id="btn-over-deep" class="crown primary">Into the Deep</button></div></div></div>
<div class="dialog" id="dlg-card"><div class="box cardbox"><h2>The expedition, in a card</h2><div id="card-slot"></div>
  <textarea id="card-text" spellcheck="false" readonly></textarea><div class="small" id="card-note"></div>
  <div class="end"><button id="btn-card-copy">Copy the text</button><button id="btn-card-save">Save the card (PNG)</button><button class="close">Close</button></div></div></div>
<div class="dialog" id="bigmap"><canvas id="bigmap-canvas" width="600" height="600"></canvas></div>`;
    this.$ = (sel) => root.querySelector(sel);
    this.canvas = document.createElement("canvas");                        // the one WebGL canvas, moved between screens
    this.canvas.id = "gl";
    this.attachCanvas("title");
    for (const b of root.querySelectorAll(".dialog .close")) b.addEventListener("click", () => this.closeDialogs());
    for (const d of root.querySelectorAll(".dialog")) d.addEventListener("click", (e) => { if (e.target === d) this.closeDialogs(); });
    this._title();
    this._create();
    this._bag();
    this._settings();
    for (const b of root.querySelectorAll("#dlg-temple button[data-service]")) {
      b.addEventListener("click", () => { game.temple(b.dataset.service); this.refresh(); });
    }
    this.$("#btn-temple-raise").addEventListener("click", () => { game.raiseDead(); this.refresh(); });
    this.$("#btn-scribe").addEventListener("click", () => { game.scribe(); this.refresh(); });
    this.$("#btn-tithe").addEventListener("click", () => { const note = game.tithe(); if (note) game.say(note); this.refresh(); });
    this.$("#btn-daily").addEventListener("click", () => { this.$("#seed").value = CM.dailySeed(); this.refreshTitle(); });
    this.$("#btn-weekly").addEventListener("click", () => { this.$("#seed").value = CM.weeklySeed(); this.refreshTitle(); });
    this.$("#btn-download").addEventListener("click", () => {
      const blob = new Blob([g.exportText()], { type: "application/json" }), a = document.createElement("a");
      a.href = URL.createObjectURL(blob); a.download = `claude-and-magic-${CM.today().replace(/\//g, "-")}.json`;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(a.href), 2000);
      this.$("#transfer-note").textContent = "Downloaded, where the browser puts downloads.";
    });
    const drop = this.$("#transfer-text");
    drop.addEventListener("dragover", (e) => { e.preventDefault(); });
    drop.addEventListener("drop", (e) => {
      e.preventDefault();
      const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
      if (!f) return;
      f.text().then((t) => { drop.value = t; this.$("#transfer-note").textContent = `${f.name} read in. Import brings it back.`; });
    });
    this.$("#btn-pause-settings").addEventListener("click", () => { this.closeDialogs(); this.openDialog("#dlg-settings"); });
    this.$("#btn-film").addEventListener("click", () => this.openFilms());
    this.$("#btn-film-play").addEventListener("click", () => { const spec = CM.parseFilm(this.$("#film-text").value); if (!spec) { this.$("#film-note").textContent = "That isn't a film code (CM2:...)."; return; } this.closeDialogs(); this.watch(spec); });
    for (const b of this.root.querySelectorAll("#view .filmbar button")) b.addEventListener("click", () => {
      const f = game.film; if (!f) return;
      const what = b.dataset.film;
      if (what === "toggle") f.playing = !f.playing; else if (what === "speed") f.speed = f.speed === 1 ? 4 : f.speed === 4 ? 16 : 1;
      else if (what === "fight" || what === "floor") { f.playing = false; game.filmSkip(what); } else if (what === "stop") game.stopFilm();
      this.filmBar();
    });
    game.on("film", (on) => { this.filmBar(); if (!on) this.show("title"); });
    game.on("change", () => { if (game.film) this.filmBar(); });
    this.$("#btn-pause-clip").addEventListener("click", () => { this.closeDialogs(); this.recordClip(); });
    this.$("#btn-pause-title").addEventListener("click", () => { this.closeDialogs(); game.saveRun(); game.setMode("title"); });
    this.renderKeys();
    this.$("#btn-keys-reset").addEventListener("click", () => this.resetKeys());
    this.$("#btn-over-card").addEventListener("click", () => this.openCard(this.overEntry));
    this.$("#btn-over-daylight").addEventListener("click", () => { this.closeDialogs(); game.endRun(true); });
    this.$("#btn-over-deep").addEventListener("click", () => { this.closeDialogs(); game.say("You leave the crown where it fell, and go down."); this.refresh(); });
    this.$("#btn-card-copy").addEventListener("click", () => this.copyText(this.$("#card-text").value, this.$("#card-note")));
    this.$("#btn-over-page").addEventListener("click", () => this.savePage());
    this.$("#btn-card-save").addEventListener("click", () => {
      const c = this.$("#card-slot canvas");
      if (!c) return;
      const a = document.createElement("a");
      a.href = c.toDataURL("image/png"); a.download = `Claude and Magic - ${(this.cardEntry && this.cardEntry.seed) || "expedition"}.png`;
      document.body.appendChild(a); a.click(); a.remove();
      this.$("#card-note").textContent = "Saved, where the browser puts downloads.";
    });
    for (const b of this.root.querySelectorAll("#slots-row button[data-slot]")) b.addEventListener("click", () => { game.setSlot(Number(b.dataset.slot)); this.refreshTitle(); });
    for (const c of [this.$("#automap"), this.$("#bigmap-canvas")]) {
      const cellAt = (e) => { const fl = game.floor; if (!fl) return null; const r = c.getBoundingClientRect(), size = fl.grid.length; return [Math.floor((e.clientX - r.left) / r.width * size), Math.floor((e.clientY - r.top) / r.height * size)]; };
      c.addEventListener("click", (e) => { const at = cellAt(e); if (!at) return; if (game.travel) { game.stopTravel(); return; } if (game.travelTo(at[0], at[1]) && c.id === "bigmap-canvas") this.closeDialogs(); });
      c.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        const at = cellAt(e), fl = game.floor;
        if (!at || !fl || !fl.seen.some(([x, y]) => x === at[0] && y === at[1])) return;
        const was = (fl.notes || {})[`${at[0]},${at[1]}`] || "";
        const text = window.prompt("A note for this square (a word or two; empty takes it off):", was);
        if (text !== null) game.setNote(at[0], at[1], text);
      });
    }
    this.$("#title .version").textContent = `Claude and Magic v${CM.version}`;
    this.$("#title .emblem-slot").appendChild(CM.art.emblem(120));
    this.fameOpen = -1;
    this.ending = null;                                                  // "victory" or "lament" while the ending is up (the music follows)
    game.on("over", (won, entry) => this.showEnding(won, entry));
    game.on("crowned", () => this.showCrowning());
    game.on("change", () => this.refresh());
    game.on("mode", (mode) => this.show(mode === "title" ? "title" : "play"));
    game.on("bag", (open) => (open ? this.openBag() : this.show("play")));
    game.on("fx", (fx) => this.fx(fx));
    game.on("turn", () => { this.cmenu = { kind: "main" }; });
    game.on("mode", (mode) => { if (mode !== "combat") this.cmenu = { kind: "main" }; this.xmenu = null; });
    game.on("lore", (text) => this.readWall(text));
    game.on("motif", (name) => { if (CM.music && CM.music.motif) CM.music.motif(name); });
    game.on("hut", () => this.openHut());
    game.on("farm", () => this.openFarm());
    game.on("talk", ({ title, text, lines }) => { this.$("#talk-title").textContent = title; this.$("#talk-text").textContent = text; this.talkMore = (lines || []).slice(); this.$("#talk-more").hidden = !this.talkMore.length; this.openDialog("#dlg-talk"); });
    this.$("#talk-more").addEventListener("click", () => { const next = (this.talkMore || []).shift(); if (next !== undefined) this.$("#talk-text").textContent = next; this.$("#talk-more").hidden = !(this.talkMore || []).length; });
    game.on("riddle", (k) => this.askRiddle(k));
    game.on("choice", (c) => this.askChoice(c));
    this.$("#view .sky").addEventListener("click", () => { if (game.mode !== "title") this.openCalendar(); });
    game.on("building", (id) => { if (id === "home" && game.homeLevel() >= 1) this.openHome(); else if (id === "tavern") this.openTavern(); else if (id === "merchant") game.openBag(true); else if (id === "smith") this.openSmith(); else if (id === "library" && game.villageLevel("library") >= 1) this.openLibrary(); else if (id === "temple" && game.villageLevel("shrine") >= 1) this.openTemple(); else if (id === "guildhall" && game.villageLevel("guildhall") >= 1) this.openGuild(); else if (id === "garden" && game.villageLevel("garden") >= 1) this.openGarden(); else if (id === "chronicler" && game.villageLevel("chronicler") >= 1) this.openChronicler(); else this.openBuilding(id); });
    this.$("#btn-library-build").addEventListener("click", () => { this.$("#library-note").textContent = game.build("library") || "The library rises a level."; this.openLibrary(true); });
    this.$("#btn-guild-build").addEventListener("click", () => { this.$("#guild-note").textContent = game.build("guildhall") || "The guildhall rises a level."; this.openGuild(true); });
    this.$("#btn-home-build").addEventListener("click", () => { this.$("#home-note").textContent = game.build("home") || "The house rises a level."; this.openHome(true); });
    this.$("#btn-building-build").addEventListener("click", () => { const P = CM.TOWN_PLOTS[this.buildingId] || {}; if (P.village) { this.$("#building-note").textContent = game.build(P.village) || `${P.name} rises a level.`; this.openBuilding(this.buildingId, true); } });
    game.on("teleported", () => this.flash(".blink", 60));
    game.on("fell", () => this.flash(".fall", 350));
    this.show("title");
  }

  flash(sel, ms) {
    if (CM.reducedMotion && sel !== ".fall") return;
    const el = this.$("#view " + sel);
    el.classList.add("on");
    setTimeout(() => el.classList.remove("on"), ms);
  }

  attachCanvas(where) {
    const slot = where === "title" ? this.$("#title .backdrop-slot") : this.$("#view .canvas-slot");
    if (this.canvas.parentNode !== slot) slot.appendChild(this.canvas);
    this.canvas.className = where === "title" ? "backdrop" : "";
  }

  show(screen) {
    for (const s of this.root.querySelectorAll(".screen")) s.classList.toggle("on", s.id === screen);
    this.screen = screen;
    if (screen === "title") { this.attachCanvas("title"); this.refreshTitle(); }
    if (screen === "play") this.attachCanvas("play");
    this.refresh();
  }

  // ---- a hero's sheet ----
  openSheet(i) {
    const g = this.game, h = g.party[i];
    if (!h) return;
    this.sheetOf = i;
    this.renderSheet();
    this.openDialog("#dlg-sheet");
  }

  renderSheet() {
    const g = this.game, h = g.party[this.sheetOf];
    if (!h || !this.$("#dlg-sheet").classList.contains("on") && this.sheetOf === undefined) return;
    const c = CM.CLASSES[h.cls] || CM.CLASSES.Knight, st = h.status || {}, fallen = h.hp <= 0;
    this.$("#sheet-title").textContent = `${h.name} - ${h.cls}, level ${h.level}${fallen ? " (fallen)" : ""}`;
    const next = CM.xpForLevel(h.level + 1);
    const eff = g.effective(h);
    const left = this.$("#sheet-left");
    left.innerHTML = "";
    left.appendChild(this.portrait(h.cls, 96));
    const facts = document.createElement("div");
    facts.className = "facts";
    facts.innerHTML = `<div>${c.role}${c.cast ? `, casts <b>${CM.CASTS[c.cast]}</b>` : ""}</div>
      <div>Experience ${h.xp} / ${next} for level ${h.level + 1}</div>
      <div>Health ${Math.max(0, h.hp)} / ${h.max}${h.maxmp ? ` &nbsp; Magic ${h.mp} / ${h.maxmp}` : ""}</div>
      <div>Attack ${eff.atk}${eff.atk !== h.atk ? ` (${h.atk})` : ""} &nbsp; Defence ${eff.df}${eff.df !== h.df ? ` (${h.df})` : ""} + gear ${CM.gearDefence(h)} &nbsp; Hits ${Math.round(g.hitChance(h) * 100)}%</div>
      <div class="rowpick"><span>Row:</span><button data-row="front" class="${h.row === "front" ? "on" : ""}">Front</button><button data-row="back" class="${h.row === "back" ? "on" : ""}">Back</button>
        <small>${g.mode === "combat" ? "not in a fight" : h.row === "front" ? "takes the blows" : h.cls === "Rogue" || h.cls === "Ranger" ? "strikes from safety" : "safer, hits for half"}</small></div>
      <div class="rowpick"><span>Formation:</span>${Object.entries(CM.FORMATIONS).map(([id, f]) => `<button data-formation="${id}" class="${(g.formation || "line") === id ? "on" : ""}" title="${this.esc(f.what)}">${f.name}</button>`).join("")}
        <small>${this.esc(CM.FORMATIONS[g.formation || "line"].what)}</small></div>
      <div class="list-title">Gear</div>
      ${CM.setWorn(h) ? `<div class="gold">${CM.SETS[CM.setWorn(h)].name} set, all three worn: ${CM.SETS[CM.setWorn(h)].what}.</div>` : ""}
      ${CM.relicsWorn(h) >= 2 ? `<div class="gold">The guardians' things, worn together: ${CM.RELIC_SET.two.what}${CM.relicsWorn(h) >= 3 ? "; " + CM.RELIC_SET.three.what : ""}.</div>` : ""}${h.oil && h.oil.fights > 0 ? `<div>Oiled: ${CM.ELEMENT_NAMES[h.oil.element]} on the weapon for ${CM.plural(h.oil.fights, "more fight")}.</div>` : ""}
      <div class="gear-list">${CM.SLOTS.map((slot) => { const it = h[slot]; return `<div><span class="slot">${CM.SLOT_NAMES[slot]}</span><span class="icon-slot" data-slot="${slot}"></span> ${it ? `<b class="rarity-${CM.rarityOf(it)}" title="${this.esc(CM.itemCard(it))}">${this.esc(it.unknown ? CM.baseName(it) : it.name)}</b> <small>${this.esc(CM.itemLabel(it))}</small>` : "<small>-</small>"}${it && !["weapon", "armor"].includes(slot) && g.mode !== "combat" ? ` <button data-off="${slot}">Take off</button>` : ""}</div>`; }).join("")}</div>`;
    for (const span of facts.querySelectorAll(".icon-slot")) { const it = h[span.dataset.slot]; if (it) span.appendChild(this.icon(it, 20)); }
    for (const b of facts.querySelectorAll("button[data-row]")) b.addEventListener("click", () => { if (g.setRow(h, b.dataset.row)) this.renderSheet(); });
    for (const b of facts.querySelectorAll("button[data-formation]")) b.addEventListener("click", () => { if (g.setFormation(b.dataset.formation)) this.renderSheet(); });
    for (const b of facts.querySelectorAll("button[data-off]")) b.addEventListener("click", () => { const note = g.takeOff(this.sheetOf, b.dataset.off); if (note) g.say(note); this.renderSheet(); });
    { const ready = g.mode !== "combat" && g.readyPower(h), spent = !ready && CM.equipped(h).some((it) => CM.powerOf(it));   // a relic's power, from the sheet, out of a fight
      if (ready || spent) { const b = document.createElement("button"); b.textContent = ready ? `${ready.power.name}: ${ready.power.what}` : "The relic's power is spent for this floor"; b.disabled = !ready || g.mode === "combat"; b.addEventListener("click", () => { g.usePower(this.sheetOf); this.renderSheet(); this.refresh(); }); facts.appendChild(b); }
      if (h.weapon && (h.weapon.marks || 0) >= CM.MARKS_TO_NAME && !h.weapon.named) { const b = document.createElement("button"); b.textContent = `Name the ${CM.baseIdOf(h.weapon)} (${CM.plural(h.weapon.marks, "mark")})`; b.addEventListener("click", () => { const name = window.prompt("A name for it:", ""); if (name) { const note = g.nameWeapon(this.sheetOf, name); if (note) g.say(note); } this.renderSheet(); this.refresh(); }); facts.appendChild(b); } }
    left.appendChild(facts);
    const right = this.$("#sheet-right");
    right.innerHTML = `<table class="stats">${CM.STATS.map((s) => `<tr class="${s === c.key ? "key" : ""}"><td>${CM.STAT_NAMES[s]}</td><td class="v">${g.stat(h, s)}</td><td class="hint">${s === c.key ? "their calling's stat" : CM.STAT_HINTS[s]}</td></tr>`).join("")}</table>
      <div class="list-title">Boons</div><div class="boons">${(h.boons || []).length ? h.boons.map((id) => `<div><b>${CM.BOONS[id].name}</b> - ${CM.BOONS[id].what}</div>`).join("") : "<div class='small'>None yet. Each level earned offers one.</div>"}</div>
      <div class="list-title">Path</div><div class="boons">${h.path && CM.PATHS[h.cls] && CM.PATHS[h.cls][h.path] ? (() => { const P = CM.PATHS[h.cls][h.path]; return `<div><b>${P.name}</b> - ${P.blurb}</div><div><b>${P.t1.name}</b> - ${P.t1.what}</div><div><b>${P.t2.name}</b> - ${h.level >= CM.PATH_AT[1] ? P.t2.what : `at level ${CM.PATH_AT[1]}: ${P.t2.what.charAt(0).toLowerCase() + P.t2.what.slice(1)}`}</div>${P.t3 ? `<div><b>${P.t3.name}</b> - ${h.level >= CM.PATH_AT[2] ? P.t3.what : `at level ${CM.PATH_AT[2]}: ${P.t3.what.charAt(0).toLowerCase() + P.t3.what.slice(1)}`}</div>` : ""}`; })() : `<div class='small'>${CM.needsPath(h) ? "A path waits to be chosen, below." : `Chosen at level ${CM.PATH_AT[0]}: two ways for a ${h.cls} to grow.`}</div>`}</div>
      ${h.quirk ? `<div class="list-title">Quirk</div><div class="boons"><div><b>${CM.QUIRKS[h.quirk].name}</b> - ${CM.QUIRKS[h.quirk].what}</div></div>` : ""}
      ${h.origin && CM.ORIGINS[h.origin] ? `<div class="list-title">Origin</div><div class="boons"><div><b>${CM.ORIGINS[h.origin].name}</b> - ${CM.ORIGINS[h.origin].what}</div></div>` : ""}
      ${h.second ? `<div class="list-title">Second calling</div><div class="boons"><div><b>${h.second}</b> - its first two spells or skills are theirs</div></div>` : ""}
      ${h.familiar ? `<div class="list-title">Familiar</div><div class="boons"><div><b>${CM.FAMILIARS[h.familiar].name}</b> - ${CM.FAMILIARS[h.familiar].what}</div></div>` : ""}
      ${Object.keys(h.spellLevels || {}).length ? `<div class="list-title">Spells deepened</div><div class="boons">${Object.entries(h.spellLevels).map(([id, l]) => `<div><b>${CM.ABILITIES[id].name}</b> - level ${l}</div>`).join("")}</div>` : ""}
      ${(() => { const f = g.bondOf(h); return f ? `<div class="list-title">Bond</div><div class="boons"><div><b>Old friends</b> - with ${this.esc(f.name)}: +1 attack and defence, heals between them half again as kind, and a fall avenged with a doubled blow.</div></div>` : ""; })()}
      ${(h.learned || []).length ? `<div class="list-title">Learned from tomes</div><div class="boons">${h.learned.map((id) => `<div><b>${CM.ABILITIES[id].name}</b> - ${CM.ABILITIES[id].what}</div>`).join("")}</div>` : ""}
      <div class="list-title">Ailments</div><div class="ails">${Object.keys(st).length ? Object.keys(st).map((s) => `<div><b>${CM.STATUSES[s].mark} ${CM.STATUSES[s].name}</b> - ${CM.STATUSES[s].hint}${st[s] < 900 ? ` (${st[s]} more rounds)` : ""}</div>`).join("") : "<div class='small'>None.</div>"}</div>`;
    const boon = this.$("#sheet-boon");
    boon.innerHTML = "";
    if (h.pending > 0) {
      const offer = g.offerBoons(h);
      boon.innerHTML = `<div class="list-title gold">Level ${h.level}: choose a boon${h.pending > 1 ? ` (${h.pending} to choose)` : ""}</div>`;
      const row = document.createElement("div");
      row.className = "offer";
      for (const id of offer) {
        const b = document.createElement("button");
        b.innerHTML = `<b>${CM.BOONS[id].name}</b><small>${CM.BOONS[id].what}</small>`;
        b.addEventListener("click", () => { g.chooseBoon(h, id); this.renderSheet(); });
        row.appendChild(b);
      }
      boon.appendChild(row);
    }
    if (g.needsFamiliar(h)) {
      const title = document.createElement("div");
      title.className = "list-title gold";
      title.textContent = `Level ${CM.FAMILIAR_AT}: a familiar for ${h.name}`;
      boon.appendChild(title);
      const row = document.createElement("div");
      row.className = "offer";
      for (const [id, F] of Object.entries(CM.FAMILIARS)) {
        if (!F.cls.includes(h.cls)) continue;
        const b = document.createElement("button");
        b.innerHTML = `<b>${F.name.replace(/^(a|an) /, (m) => m.toUpperCase())}</b><small>${F.what}</small>`;
        b.addEventListener("click", () => { g.chooseFamiliar(h, id); this.renderSheet(); });
        row.appendChild(b);
      }
      boon.appendChild(row);
    }
    if (CM.needsPath(h)) {
      const title = document.createElement("div");
      title.className = "list-title gold";
      title.textContent = `Level ${CM.PATH_AT[0]}: choose ${h.name}'s path`;
      boon.appendChild(title);
      const row = document.createElement("div");
      row.className = "offer";
      for (const [id, P] of Object.entries(CM.PATHS[h.cls])) {
        const b = document.createElement("button");
        b.innerHTML = `<b>${P.name}</b><small>${P.blurb} Now: ${P.t1.what}. At level ${CM.PATH_AT[1]}: ${P.t2.what.charAt(0).toLowerCase() + P.t2.what.slice(1)}.</small>`;
        b.addEventListener("click", () => { g.choosePath(h, id); this.renderSheet(); });
        row.appendChild(b);
      }
      boon.appendChild(row);
    }
  }

  dialogOpen() { return Boolean(this.root.querySelector(".dialog.on")); }
  // ---- films: a run watched in the real view ----
  openFilms() {
    const g = this.game, box = this.$("#film-list"), films = CM.store.get("films", []);
    box.innerHTML = films.length ? "" : `<div class="unlock"><small>No film yet: every run's end keeps one, the last six.</small></div>`;
    for (const f of films) {
      const row = document.createElement("div"); row.className = "recruit"; row.style.gridTemplateColumns = "1fr auto auto";
      row.innerHTML = `<div><b>${this.esc(f.name)}</b> <small>${this.esc(f.seed)}, ${f.won ? "crowned" : "floor " + f.floor}, ${this.esc(f.date)}</small></div>`;
      const w = document.createElement("button"); w.textContent = "Watch"; w.addEventListener("click", () => { this.closeDialogs(); this.watch(Object.assign({}, f.spec, { log: CM.unpackLog(f.spec.log) })); });
      const c = document.createElement("button"); c.textContent = "Copy the code"; c.addEventListener("click", () => this.copyText(CM.filmCode(Object.assign({}, f.spec, { log: CM.unpackLog(f.spec.log) })), this.$("#film-note")));
      row.appendChild(w); row.appendChild(c); box.appendChild(row);
    }
    this.$("#film-note").textContent = "";
    this.openDialog("#dlg-film");
  }
  watch(spec) {
    const g = this.game;
    if (!g.startFilm(spec)) { this.$("#film-note").textContent = "That isn't a film."; return; }
    this.show("play");
    this.filmBar();
  }
  filmBar() {
    const g = this.game, bar = this.$("#view .filmbar"), f = g.film;
    bar.classList.toggle("on", Boolean(f));
    if (!f) return;
    bar.querySelector("[data-film=toggle]").textContent = f.playing ? "Pause" : "Play";
    bar.querySelector("[data-film=speed]").textContent = `${f.speed}x`;
    const line = f.spec.log[f.at - 1] || [], scene = { parley: "a parley", talk: "a word with someone", choose: "a choice", chooseBoon: "a boon", kneel: "at an altar", drink: "at a fountain", rest: "the camp", secondCalling: "a second calling" }[line[0]] || (this.game.mode === "combat" ? "a fight" : "");
    bar.querySelector("span").textContent = `${f.at} of ${f.spec.log.length}${scene ? ` - ${scene}` : ""}`;
  }
  // ten seconds of the view, recorded (the canvas's stream, where the browser can) and saved as a .webm
  recordClip() {
    const g = this.game;
    if (!this.canvas.captureStream || typeof MediaRecorder === "undefined") { g.say("This browser can't record the view."); return; }
    if (this.recorder) return;
    const stream = this.canvas.captureStream(30), chunks = [];
    let rec;
    try { rec = new MediaRecorder(stream, { mimeType: MediaRecorder.isTypeSupported("video/webm;codecs=vp9") ? "video/webm;codecs=vp9" : "video/webm" }); } catch (e) { g.say("This browser can't record the view."); return; }
    this.recorder = rec;
    rec.ondataavailable = (e) => { if (e.data && e.data.size) chunks.push(e.data); };
    rec.onstop = () => {
      this.recorder = null;
      const blob = new Blob(chunks, { type: "video/webm" }), a = document.createElement("a");
      a.href = URL.createObjectURL(blob); a.download = `Claude and Magic - ${g.seed || "clip"}.webm`;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(a.href), 2000);
      g.say("The clip is saved, where the browser puts downloads.");
    };
    rec.start();
    g.say("Recording ten seconds of the view...");
    setTimeout(() => { if (rec.state !== "inactive") rec.stop(); }, 10000);
  }
  // ---- the village ----
  openVillage() { this.renderVillage(); this.openDialog("#dlg-village"); }
  // the next level of a building, raised at its own door: a line and a button inserted at the foot of the building's dialog
  raiseFooter(sel, villageId, after) {
    const g = this.game, root = this.$(sel + " .box"), old = root.querySelector(".raise"); if (old) old.remove();
    const V = CM.VILLAGE[villageId]; if (!V) return;
    const lvl = g.villageLevel(villageId), d = document.createElement("div"); d.className = "raise small";
    if (lvl >= V.costs.length) d.textContent = `${V.name} is as grand as it can be.`;
    else { d.textContent = `Raise ${V.name} (level ${lvl} of ${V.costs.length}): ${V.levels[lvl]} - `; const b = document.createElement("button"); b.textContent = `${V.costs[lvl]} renown (you have ${g.renown()})`; b.disabled = g.renown() < V.costs[lvl]; b.addEventListener("click", () => { const n = g.build(villageId); if (n) g.say(n); if (after) after(); this.refresh(); }); d.appendChild(b); }
    root.insertBefore(d, root.querySelector(".end"));
  }
  // the garden: the beds above the alchemist's bench
  openFarm() {
    const g = this.game, L = g.villageLevel("farm"), F = g.farm(), head = this.$("#farm-head"), rows = this.$("#farm-rows"), more = this.$("#farm-more"); rows.innerHTML = ""; more.innerHTML = "";
    const act = (fn) => { this.$("#farm-note").textContent = fn() || "Done."; this.openFarm(); this.refresh(); };
    const btn = (into, text, fn, off) => { const b = document.createElement("button"); b.textContent = text; b.disabled = Boolean(off); b.addEventListener("click", () => act(fn)); into.appendChild(b); return b; };
    this.$("#dlg-farm h2").textContent = CM.t("farm.title"); this.$("#dlg-hut h2").textContent = CM.t("hut.title"); this.$("#dlg-hut .lore").textContent = CM.t("hut.lead");
    if (L < 1) { head.textContent = CM.t("farm.fallow"); return this.openDialog("#dlg-farm"); }
    head.textContent = `${CM.season(g).charAt(0).toUpperCase() + CM.season(g).slice(1)}, day ${F.days + 1} of the farm. Level ${L}: ${CM.VILLAGE.farm.levels.slice(0, L).map((w) => w.split(":")[0].toLowerCase()).join(", ")}. A row grows a stage every dawn the party sees, and is cut at the fourth; past ripe three dawns, it rots.${F.scarecrow ? " A scarecrow stands." : " No scarecrow: crows take a ripe row in ten."}`;
    const seeds = g.bag.map((it, i) => [it, i]).filter(([it]) => it.kind === "seed");
    for (let i = 0; i < g.farmRows(); i++) { const r = F.rows[i], row = document.createElement("div"); row.className = "recruit"; row.style.gridTemplateColumns = "1fr auto";
      const left = r ? CM.FARM.rotAfter + 1 - (r.ripeFor || 0) : 0, state = !r ? "" : r.stage < CM.FARM.stages ? "stage " + r.stage + " of " + CM.FARM.stages : r.ripeFor ? "ripe, " + left + (left === 1 ? " dawn" : " dawns") + " before it rots" : "ripe";
      const t = document.createElement("div"); t.innerHTML = r ? "<b>Row " + (i + 1) + ": " + this.esc(CM.CROPS[r.crop].name) + "</b> <small>" + state + "</small>" : "<b>Row " + (i + 1) + "</b> <small>empty</small>"; row.appendChild(t);
      const a = document.createElement("div"); a.className = "hire";
      if (r) btn(a, r.stage >= CM.FARM.stages ? "Cut it" : "Not ripe", () => g.cut(i), r.stage < CM.FARM.stages);
      else if (seeds.length) { const sel = document.createElement("select"); sel.innerHTML = `<option value="">Sow...</option>` + seeds.map(([it, bi]) => `<option value="${bi}"${g.canSow(it.crop) ? "" : " disabled"}>${this.esc(it.name)}${g.canSow(it.crop) ? "" : " (not in " + CM.season(g) + ")"}</option>`).join(""); sel.addEventListener("change", () => { if (sel.value !== "") act(() => g.sow(i, Number(sel.value))); }); a.appendChild(sel); }
      else { const s = document.createElement("small"); s.textContent = "no seed in the pack (the Merchant's House sells the season's)"; a.appendChild(s); }
      row.appendChild(a); rows.appendChild(row); }
    { const st = document.createElement("div"); st.className = "small"; const count = {}; for (const s of F.store) count[s.id] = (count[s.id] || 0) + 1; st.textContent = `The store: ${Object.keys(count).length ? Object.entries(count).map(([id, n]) => `${n} ${id}`).join(", ") : "bare"}. Seed in the chest: ${Object.entries(F.seeds).filter(([, n]) => n > 0).map(([c, n]) => `${n} ${CM.CROPS[c].name.toLowerCase()}`).join(", ") || "none"}.`; more.appendChild(st); }
    if (F.store.length) btn(more, "Take what the store holds", () => g.collectFarm());
    if (!F.scarecrow) btn(more, "Put up a scarecrow (a deadwood and an old tunic)", () => g.setScarecrow());
    if (seeds.length) btn(more, "Seed into the chest, for the farmhand", () => g.storeSeeds());
    if (L >= 3) { btn(more, F.hand > F.days ? `The farmhand is paid for ${F.hand - F.days} dawns` : `Hire a farmhand (${CM.FARM.handGold} gold a season)`, () => g.hireHand(), F.hand > F.days);
      const sel = document.createElement("select"); sel.innerHTML = `<option value="">${F.order ? "He sows " + CM.CROPS[F.order].name.toLowerCase() : "Tell him what to sow"}...</option><option value="-">Nothing</option>` + Object.keys(CM.CROPS).map((c) => `<option value="${c}">${this.esc(CM.CROPS[c].name)} (${CM.CROPS[c].sow.join(", ")})</option>`).join(""); sel.addEventListener("change", () => { if (sel.value) act(() => g.orderHand(sel.value === "-" ? null : sel.value)); }); more.appendChild(sel); }
    if (L >= 5) btn(more, F.cowFed > F.days ? `The cow is fed for ${F.cowFed - F.days} dawns` : "Feed the cow a cabbage (milk a dawn for a week)", () => g.feedCow(), F.cowFed > F.days);
    if (F.notes.length) { const n = document.createElement("div"); n.className = "small"; n.textContent = `Lately: ${F.notes.slice(-4).join("; ")}.`; more.appendChild(n); }
    this.hireRow(more, ["dog"], () => this.openFarm());               // (the farm's dog, once there's a cow to mind)
    this.openDialog("#dlg-farm");
  }
  dishButtons(into, run) {                                              // the dishes the pack's things would make, and the apron
    const g = this.game, cook = g.cookOf(), can = Object.keys(CM.DISHES).filter((id) => CM.canCook(g.bag, id));
    const head = document.createElement("div"); head.className = "small"; head.textContent = `${cook ? `${cook.name} wears the apron: a cook of level ${cook.cook.level}, ${cook.cook.made} dishes made; the dishes last ${cook.cook.level ? CM.plural(cook.cook.level, "floor") + " longer" : "no longer yet"}.` : "Nobody wears the apron: a cook's dishes last longer, and at the third level a cook makes them on the floor for a torch."} ${can.length ? "" : "Nothing in the pack makes a dish: the farm's, the Wood's and the beasts' things do."}`; into.appendChild(head);
    for (const id of can) { const D = CM.DISHES[id], b = document.createElement("button"); b.textContent = `${D.name} (${D.needs.map(CM.needName).join(", ")}): ${D.what}, ${CM.plural(D.floors, "floor")}`; b.addEventListener("click", () => run(() => g.cookDish(id))); into.appendChild(b); }
    const sel = document.createElement("select"); sel.innerHTML = `<option value="">The apron to...</option>` + g.party.map((h, i) => `<option value="${i}"${h.cook ? " disabled" : ""}>${this.esc(h.name)}${h.cook ? " (wears it)" : ""}</option>`).join(""); sel.addEventListener("change", () => { if (sel.value !== "") run(() => g.takeApron(Number(sel.value))); }); into.appendChild(sel);
  }
  openHut() {
    const g = this.game, box = this.$("#hut-list"); box.innerHTML = "";
    const hides = g.bag.filter((i) => i.kind === "hide"); const sm = document.createElement("div"); sm.className = "small"; sm.textContent = `Hides in the pack: ${hides.length ? hides.map((h) => h.name.toLowerCase()).join(", ") : "none"}.`; box.appendChild(sm);
    for (const [id, T] of Object.entries(CM.TANNING)) { const b = document.createElement("button"); b.textContent = `${T.name} (${T.any ? CM.plural(T.hides, "hide") : "a " + T.of + " hide"}): ${T.what}`; b.disabled = hides.filter((h) => T.any || h.hide === T.of).length < T.hides; b.addEventListener("click", () => { this.$("#hut-note").textContent = g.tan(id) || "Done."; this.openHut(); this.refresh(); }); box.appendChild(b); }
    this.openDialog("#dlg-hut");
  }
  openGarden() {
    const g = this.game, root = this.$("#dlg-alchemist .box"), old = root.querySelector("#garden-town"); if (old) old.remove();
    const G = g.garden(), beds = g.bedsOf(), extra = document.createElement("div"); extra.id = "garden-town";
    extra.innerHTML = `<div class="list-title">The beds (${G.beds.length} of ${beds} planted; a bed grows one more every run that ends, up to ${CM.BED_MAX})</div>`;
    G.beds.forEach((b, i) => { const btn = document.createElement("button"); btn.textContent = `Harvest ${CM.plural(b.n, CM.INGREDIENTS[b.ingredient].name)}`; btn.addEventListener("click", () => { const n = g.harvest(i); if (n) g.say(n); this.openGarden(); this.refresh(); }); extra.appendChild(btn); });
    if (G.beds.length < beds) g.bag.forEach((it, row) => { if (it.kind !== "ingredient") return; const btn = document.createElement("button"); btn.textContent = `Plant ${it.name}`; btn.addEventListener("click", () => { const n = g.plant(row); if (n) g.say(n); this.openGarden(); this.refresh(); }); extra.appendChild(btn); });
    root.insertBefore(extra, root.querySelector(".end"));
    this.renderAlchemist(); this.raiseFooter("#dlg-alchemist", "garden", () => this.openGarden()); this.openDialog("#dlg-alchemist");
  }
  // the chronicler's house: the title's boards under one roof
  openChronicler() {
    const g = this.game, box = this.$("#chronicler-rooms"); box.innerHTML = "";
    const room = (title) => { const d = document.createElement("div"); d.innerHTML = `<div class="list-title">${title}</div>`; const inner = document.createElement("div"); d.appendChild(inner); box.appendChild(d); return inner; };
    { const r = room("The table"); const f = document.createElement("button"); f.textContent = "The films of runs"; f.addEventListener("click", () => this.openFilms()); r.appendChild(f); const s = document.createElement("button"); s.textContent = "The statistics"; s.addEventListener("click", () => this.openStats()); r.appendChild(s); }
    { const r = room("The calendar"); const cal = CM.calendarOf(g.fame); r.innerHTML = `<div class="small">The year as the town keeps it: a festival a month, in the week around the fifteenth; this run is ${this.esc(CM.dateWords(g))}.</div>` + cal.map((m) => `<div class="small"><b>${m.name}</b> (${m.season}): ${this.esc(m.festivalName)} - ${this.esc(CM.FESTIVALS[m.festival].what)}.${m.runs ? ` ${CM.plural(m.runs, "run")} here${m.crowns ? `, ${m.crowns} crowned` : ""}.` : ""}</div>`).join(""); }
    { const r = room("The Hall of Fame"); const fame = (g.fame || []).slice(0, 10); r.innerHTML = fame.length ? fame.map((e) => `<div class="small"><b>${this.esc(e.name)}</b>: ${e.won ? "crowned" : e.bottom ? "to the bottom of the world" : `fell on floor ${e.floor}`}, ${e.gold.toLocaleString()} gold, ${this.esc(e.date)} (${this.esc(e.party.join(", "))})</div>`).join("") : "<div class='small'>No run has ended yet.</div>"; }
    { const r = room("The ledger"); const led = (g.ledger || []).slice(-10).reverse(); r.innerHTML = led.length ? led.map((l) => `<div class="small">${this.esc(l.d)}: ${this.esc(l.sd)}, floor ${l.f}${l.w ? ", crowned" : ""}${l.b ? ", the bottom" : ""} - ${l.k} slain, ${l.s} steps, ${l.g} gold</div>`).join("") : "<div class='small'>Nothing written yet.</div>"; }
    { const r = room("The memorial's book"); const m = (g.memorial || []).slice(0, 12); r.innerHTML = m.length ? m.map((x) => `<div class="small"><b>${this.esc(x.name)}</b> the ${x.cls}, level ${x.level}, floor ${x.floor}${x.candle ? " - a candle burns" : ""}${x.epitaph ? ` - "${this.esc(x.epitaph)}"` : ""}</div>`).join("") : "<div class='small'>No names. May it stay so.</div>"; }
    this.openDialog("#dlg-chronicler");
  }
  // the town's walls, written on: the smith's sign, the tavern's wall, the library's shelf
  brought(kind) {
    const g = this.game;
    if (kind === "smith") { const named = ((g.compendium || {}).named || [])[0]; return named ? `The sign over the forge bears a blade: ${named.name}, the first named here.` : "The sign over the forge is a plain hammer; the first weapon named by a party of this house goes on it."; }
    if (kind === "tavern") { const best = (g.fame || []).find((e) => e.won) || (g.fame || [])[0]; return best ? `Painted on the tavern's wall, badly: ${best.party.join(", ")} - ${best.won ? "who took the crown" : `who reached floor ${best.floor}`}.` : "The tavern's wall is bare plaster; the first run that comes home is painted on it."; }
    if (kind === "library") { const n = ((g.village || {}).chaptersPaid || []).length; return `The shelf: ${n ? CM.plural(n, "chapter") + " of Caer Duin copied fair" : "no chapter copied fair yet"}, and ${CM.plural((g.libraryState().pages || 0), "lost page")}.`; }
    return "";
  }
  // the library: the desk (the journal's boards), Wren's copying, the tomes, the shelved pages, the gazetteer
  openLibrary(keepNote) {
    const g = this.game, V = CM.VILLAGE.library, lvl = g.villageLevel("library"), L = g.libraryState(), box = this.$("#library-rooms"), note = this.$("#library-note");
    const say = (t) => { note.textContent = t || "Done."; this.openLibrary(true); this.refresh(); };
    this.$("#library-what").textContent = `Level ${lvl} of ${V.costs.length}. ${lvl ? V.levels.slice(0, lvl).join("; ") + "." : ""}` + (lvl < V.costs.length ? ` Next, for ${V.costs[lvl]} renown (you have ${g.renown()}): ${V.levels[lvl]}.` : "");
    const bb = this.$("#btn-library-build"); bb.style.display = lvl < V.costs.length ? "" : "none"; if (lvl < V.costs.length) { bb.textContent = `Build, ${V.costs[lvl]} renown`; bb.disabled = g.renown() < V.costs[lvl]; }
    if (!keepNote) note.textContent = "";
    box.innerHTML = "";
    const room = (title) => { const d = document.createElement("div"); d.innerHTML = `<div class="list-title">${title}</div>`; const inner = document.createElement("div"); d.appendChild(inner); box.appendChild(d); return inner; };
    const btn = (parent, text, fn) => { const b = document.createElement("button"); b.textContent = text; b.addEventListener("click", fn); parent.appendChild(b); return b; };
    { const r = room("The reading desk"); for (const [page, label] of [["codex", "The codex"], ["things", "The compendium of things"], ["journal", "This run's journal, bestiary and combos"]]) btn(r, label, () => { this.journalPage = page; this.openJournal(); }); }
    { const r = room("Wren, the chronicler"); const W = CM.VILLAGERS.chronicler; r.innerHTML = `<div class="small">${this.esc(W.greet.join(" "))} ${this.esc(this.brought("library"))}</div>`; btn(r, "Read the Book of Caer Duin", () => { this.bookOpen = true; this.openVillage(); }); }
    { const r = room(`The tomes (one out at a time${L.lent ? `: ${this.esc(CM.TOMES[L.lent.tome] || "a tome")} is out with this party` : ""})`); Object.keys(CM.TOMES).forEach((id) => { const b = btn(r, `Borrow the ${CM.TOMES[id]}`, () => say(g.borrowTome(id))); b.disabled = Boolean(L.lent); }); }
    { const r = room("The shelf of lost pages"); r.innerHTML = `<div class="small">${L.pages ? `${CM.plural(L.pages, "lost page")} found and copied here: fire, frost or lightning on every foe, once each, torn from tomes no one has whole.` : "Empty. The Lost Page scrolls found below are copied here."}</div>`; }
    { const r = room("A hedge-wizard, for hire"); this.hireRow(r, ["wizard"], () => this.openLibrary(true)); }
    if (lvl >= 5) { const r = room("The gazetteer"); r.innerHTML = `<div class="small">The first ${CM.GAZETTEER_FLOORS} floors of any seed, mapped: on a new run their walls are on the map before the party is on them.</div>`; }
    this.openDialog("#dlg-library");
  }
  // the temple in town: the camp's temple dialog, at town prices, with the shrine's candles, the history and the vigil beneath
  openTemple() {
    const g = this.game, root = this.$("#dlg-temple .box"), old = root.querySelector("#temple-town"); if (old) old.remove();
    const extra = document.createElement("div"); extra.id = "temple-town";
    const P = CM.VILLAGERS.priest, lvl = g.villageLevel("shrine");
    extra.innerHTML = `<div class="list-title">Father Osric</div><div class="small">${this.esc(P.greet.join(" "))} <i>${this.esc(CM.PATRIARCH_HISTORY[Math.min(4, lvl)])}</i> Prices in town are a tenth less.</div>`;
    const candles = document.createElement("div"); (g.memorial || []).slice(0, 8).forEach((m, i) => { const b = document.createElement("button"); b.textContent = m.candle ? `${m.name}: a candle burns` : `A candle for ${m.name} (${CM.CANDLE_COST[lvl >= 2 ? 1 : 0]} renown)`; b.disabled = Boolean(m.candle); b.addEventListener("click", () => { const n = g.lightCandle(i); if (n) g.say(n); this.openTemple(); this.refresh(); }); candles.appendChild(b); }); extra.appendChild(candles);
    if (lvl >= 5) { const v = document.createElement("div"); v.innerHTML = `<div class="list-title">The vigil (once a hero)</div>`; g.party.forEach((h, hi) => { if (h.hp <= 0 || h.vigil || !(h.scars || []).length) return; for (const s of h.scars) { const keep = document.createElement("button"); keep.textContent = `${h.name} keeps ${CM.SCARS[s].name}`; keep.addEventListener("click", () => { const n = g.vigil(hi, s, true); if (n) g.say(n); this.openTemple(); this.refresh(); }); const fade = document.createElement("button"); fade.textContent = `${h.name} lets ${CM.SCARS[s].name} fade`; fade.addEventListener("click", () => { const n = g.vigil(hi, s, false); if (n) g.say(n); this.openTemple(); this.refresh(); }); v.appendChild(keep); v.appendChild(fade); } }); extra.appendChild(v); }
    root.insertBefore(extra, root.querySelector(".end"));
    this.raiseFooter("#dlg-temple", "shrine", () => this.openTemple()); this.openDialog("#dlg-temple");
  }
  // the guildhall: the trainers, the second calling, the contracts, the roster and the muster
  openGuild(keepNote) {
    const g = this.game, V = CM.VILLAGE.guildhall, lvl = g.villageLevel("guildhall"), box = this.$("#guild-rooms"), note = this.$("#guild-note");
    this.$("#guild-what").textContent = `Level ${lvl} of ${V.costs.length}. ${lvl ? V.levels.slice(0, lvl).join("; ") + "." : ""}` + (lvl < V.costs.length ? ` Next, for ${V.costs[lvl]} renown (you have ${g.renown()}): ${V.levels[lvl]}.` : "");
    const bb = this.$("#btn-guild-build"); bb.style.display = lvl < V.costs.length ? "" : "none"; if (lvl < V.costs.length) { bb.textContent = `Build, ${V.costs[lvl]} renown`; bb.disabled = g.renown() < V.costs[lvl]; }
    if (!keepNote) note.textContent = "";
    box.innerHTML = "";
    const room = (title) => { const d = document.createElement("div"); d.innerHTML = `<div class="list-title">${title}</div>`; const inner = document.createElement("div"); d.appendChild(inner); box.appendChild(d); return inner; };
    { const r = room("Dunmore, and the trainers"); const K = CM.VILLAGERS.keeper, trainers = g.village.trainers || []; r.innerHTML = `<div class="small">${this.esc(K.greet.join(" "))} ${trainers.length ? trainers.map((t) => `<b>${this.esc(t.name)}</b> the ${t.cls} (level ${t.level})`).join(", ") : "No trainer has come home yet."}</div>`; g.party.forEach((h, hi) => { if (h.hp > 0 && (h.boons || []).length) { const b = document.createElement("button"); b.textContent = `${h.name} retires as a trainer`; b.addEventListener("click", () => { note.textContent = g.retire(hi) || "Retired."; this.openGuild(true); this.refresh(); }); r.appendChild(b); } }); }
    { const r = room("The second calling"); const b = document.createElement("button"); b.textContent = "The guild's letter (a hero at twenty takes a second calling)"; b.addEventListener("click", () => this.openSecond()); r.appendChild(b); }
    { const r = room("The week's contracts"); r.innerHTML = `<div class="small">${g.contracts().map(({ c, done }) => `${done ? "✓" : "○"} <b>${this.esc(c.name)}</b>: ${this.esc(c.what)} (${c.renown} renown)`).join("<br>")}</div>`; }
    { const r = room("The roster"); const roster = g.roster(); if (!roster.length) r.innerHTML = "<div class='small'>No party has set out from this browser yet; the first that does is written here.</div>"; roster.forEach((e) => { const row = document.createElement("div"); row.className = "recruit"; row.style.gridTemplateColumns = "1fr auto"; row.innerHTML = `<div><b>${e.party.map((p) => this.esc(p.name)).join(", ")}</b> <small>${e.party.map((p) => p.cls).join(" / ")} - ${e.won ? "crowned" : e.home ? "came home" : `fell on floor ${e.floor}`}, ${this.esc(e.date)}</small></div>`; const b = document.createElement("button"); b.textContent = "Set out again as them"; b.addEventListener("click", () => { this.musterParty = e.party; this.closeDialogs(); this.openCreate(); }); row.appendChild(b); r.appendChild(row); }); const m = g.muster(); if (m) { const b = document.createElement("button"); b.textContent = `Muster: the last party that came home (${m.party.map((p) => p.name).join(", ")})`; b.addEventListener("click", () => { this.musterParty = m.party; this.closeDialogs(); this.openCreate(); }); r.appendChild(b); } }
    this.openDialog("#dlg-guild");
  }
  // the party's own house: its rooms, by the level the house has been raised to
  openHome(keepNote) {
    const g = this.game, lvl = g.homeLevel(), H = g.home(), V = CM.VILLAGE.home, box = this.$("#home-rooms"), note = this.$("#home-note");
    const say = (t) => { note.textContent = t || "Done."; this.openHome(true); this.refresh(); };
    this.$("#home-what").textContent = `Level ${lvl} of ${V.costs.length}.` + (lvl < V.costs.length ? ` Next, for ${V.costs[lvl]} renown (you have ${g.renown()}): ${V.levels[lvl]}.` : "");
    const bb = this.$("#btn-home-build"); bb.style.display = lvl < V.costs.length ? "" : "none"; if (lvl < V.costs.length) { bb.textContent = `Build, ${V.costs[lvl]} renown`; bb.disabled = g.renown() < V.costs[lvl]; }
    if (!keepNote) note.textContent = "";
    box.innerHTML = "";
    const room = (title, body) => { const d = document.createElement("div"); d.innerHTML = `<div class="list-title">${title}</div>`; const inner = document.createElement("div"); d.appendChild(inner); box.appendChild(d); return inner; };
    const btn = (parent, text, fn, title) => { const b = document.createElement("button"); b.textContent = text; if (title) b.title = title; b.addEventListener("click", () => say(fn())); parent.appendChild(b); return b; };
    { const r = room("The hearth"); const b = btn(r, g.floor && g.floor.hearthUsed ? "Rested here already" : "Rest, and go down rested", () => g.hearthRest()); b.disabled = Boolean(g.floor && g.floor.hearthUsed); }
    { const r = room(`The stash (${H.stash.length} of ${CM.HOME_STASH[Math.min(lvl, CM.HOME_STASH.length - 1)]})`);
      H.stash.forEach((it, i) => { const row = document.createElement("div"); row.className = "recruit"; row.style.gridTemplateColumns = "1fr auto"; const t = document.createElement("div"); t.innerHTML = `<b class="rarity-${CM.rarityOf(it)}">${this.esc(CM.itemName(it))}</b> <small>${this.esc(CM.itemLabel(it))}</small>`; t.title = CM.itemCard(it); row.appendChild(t); const b = document.createElement("button"); b.textContent = "Take"; b.addEventListener("click", () => say(g.stashTake(i))); row.appendChild(b); r.appendChild(row); });
      const leave = document.createElement("div"); leave.className = "small"; leave.textContent = "Leave here: "; g.bag.forEach((it, row) => { if (["key", "boxkey"].includes(it.kind)) return; const b = document.createElement("button"); b.textContent = CM.itemName(it); b.title = CM.itemCard(it); b.addEventListener("click", () => say(g.stashPut(row))); leave.appendChild(b); }); r.appendChild(leave); }
    if (lvl >= 2) { const r = room("The trophy wall"), T = g.homeTrophies(); r.innerHTML = `<div class="small">${T.crowns ? `${T.crowns} crown${T.crowns === 1 ? "" : "s"} on the shelf${T.bottoms ? `, and ${T.bottoms} stone${T.bottoms === 1 ? "" : "s"} from the bottom of the world` : ""}.` : "The shelf waits for a crown."} ${T.trophies.length ? "Trophies: " + T.trophies.map((t) => this.esc(t.name)).join(", ") + "." : ""} ${T.named.length ? "Named: " + T.named.map((n) => `${this.esc(n.name)} (${this.esc(n.base)})`).join(", ") + "." : ""} ${T.uniques.length ? "Found: " + T.uniques.map((u) => this.esc(u)).join(", ") + "." : ""}</div>`; }
    if (lvl >= 3) { const r = room(`The kitchen, and the larder (${H.larder || 0} of ${CM.HOME_LARDER} rations)`); g.bag.forEach((it, row) => { if (it.kind === "meat") btn(r, `Cook ${it.name}`, () => g.homeCook(row)); if (it.kind === "ration") btn(r, "A ration to the larder", () => g.larderPut(row)); }); if (H.larder > 0) btn(r, "A ration from the larder", () => g.larderTake()); this.dishButtons(r, (fn) => say(fn())); if (!r.children.length) r.innerHTML = "<div class='small'>Nothing to cook, and nothing to put by.</div>"; }
    if (lvl >= 4) { const r = room("The door-plate"); (g.memorial || []).slice(0, 12).forEach((m, i) => { const row = document.createElement("div"); row.className = "recruit"; row.style.gridTemplateColumns = "1fr auto"; row.innerHTML = `<div><b>${this.esc(m.name)}</b> <small>the ${m.cls}, level ${m.level}, floor ${m.floor}${m.scars && m.scars.length ? ` - ${m.scars.map((s) => CM.SCARS[s] ? CM.SCARS[s].name : s).join(", ")}` : ""}</small></div>`; const b = document.createElement("button"); b.textContent = m.candle ? "A candle burns" : `A candle (${CM.CANDLE_COST[g.villageLevel("shrine") >= 2 ? 1 : 0]} renown)`; b.disabled = Boolean(m.candle); b.addEventListener("click", () => say(g.homeCandle(i))); row.appendChild(b); r.appendChild(row); }); if (!r.children.length) r.innerHTML = "<div class='small'>No names yet. May it stay so.</div>"; }
    if (lvl >= 5) { const r = room("The study"); g.party.forEach((h, i) => { if (h.hp > 0) btn(r, `${h.name} retires home`, () => g.retireHome(i)); }); if (H.retired.length) { const w = document.createElement("div"); w.className = "small"; w.textContent = `Retired here: ${H.retired.map((x) => `${x.name} the ${x.cls}`).join(", ")}. ${H.will ? `The will: ${CM.itemName(H.will)} in every pack.` : "No will yet."} Will a thing from the stash: `; H.stash.forEach((it, i) => { const b = document.createElement("button"); b.textContent = CM.itemName(it); b.addEventListener("click", () => say(g.writeWill(i))); w.appendChild(b); }); r.appendChild(w); } }
    this.openDialog("#dlg-home");
  }
  // a door in the town: the plot's name, what stands there, the levels raised, and the village's build button
  openBuilding(id, keepNote) {
    const g = this.game, P = CM.TOWN_PLOTS[id]; if (!P) return;
    this.buildingId = id;
    const lvl = CM.plotLevel(g, id), V = P.village ? CM.VILLAGE[P.village] : null;
    this.$("#building-title").textContent = P.name;
    this.$("#building-what").textContent = P.what + (lvl ? "" : V ? " Nothing stands here yet but the foundation." : " A foundation only: the town raises it in the updates to come.");
    this.$("#building-levels").innerHTML = V ? (lvl ? V.levels.slice(0, lvl).map((w, i) => `<div>Level ${i + 1}: ${this.esc(w)}</div>`).join("") : "") + (lvl < V.costs.length ? `<div><i>Next, for ${V.costs[lvl]} renown: ${this.esc(V.levels[lvl])}</i> (you have ${g.renown()})</div>` : "<div><i>Complete.</i></div>") : "";
    const b = this.$("#btn-building-build"); b.style.display = V && lvl < V.costs.length ? "" : "none"; if (V && lvl < V.costs.length) { b.textContent = `Build, ${V.costs[lvl]} renown`; b.disabled = g.renown() < V.costs[lvl]; }
    if (!keepNote) this.$("#building-note").textContent = "";
    this.openDialog("#dlg-building");
  }
  renderVillage() {
    const g = this.game, v = g.village || {};
    this.$("#village-renown").textContent = `Renown: ${g.renown()} to spend (${v.renown || 0} earned, ever). The vault holds ${g.vaultCapacity()}.`;
    const note = this.$("#village-note");
    const bb = this.$("#village-buildings"); bb.innerHTML = "";
    for (const [id, B] of Object.entries(CM.VILLAGE)) {
      const lvl = g.villageLevel(id), row = document.createElement("div");
      row.className = "recruit"; row.style.gridTemplateColumns = "1fr auto";
      row.innerHTML = `<div><b>${B.name}</b> <small>level ${lvl} of ${B.costs.length}</small><small>${lvl ? B.levels.slice(0, lvl).map((w) => this.esc(w)).join("; ") : "Not built."}</small>${lvl < B.costs.length ? `<small><i>Next (${B.costs[lvl]} renown): ${this.esc(B.levels[lvl])}</i></small>` : ""}</div>`;
      const b = document.createElement("button");
      b.textContent = lvl < B.costs.length ? `Build, ${B.costs[lvl]} renown` : "Complete";
      b.disabled = lvl >= B.costs.length || g.renown() < B.costs[lvl];
      b.addEventListener("click", () => { note.textContent = g.build(id) || `${B.name} rises a level.`; this.renderVillage(); });
      row.appendChild(b); bb.appendChild(row);
    }
    this.renderVillagers(note);
    this.$("#village-contracts").innerHTML = g.contracts().map(({ c, done }) => `<div class="unlock ${done ? "got" : ""}"><b>${done ? "✓" : "○"} ${this.esc(c.name)}</b> <small>${this.esc(c.what)} - ${c.renown} renown</small></div>`).join("");
    const trainers = v.trainers || [];
    this.$("#village-trainers").innerHTML = trainers.length ? trainers.map((t) => `<div class="unlock got"><b>${this.esc(t.name)}</b> <small>${t.cls}, level ${t.level}: every new ${t.cls} sets out with ${CM.BOONS[t.boon] ? CM.BOONS[t.boon].name : t.boon}</small></div>`).join("") : `<div class="unlock"><small>${g.villageLevel("guildhall") ? "No one has retired yet: a hero who comes home may, at the run's end." : "Build the guildhall first."}</small></div>`;
    const shrine = this.$("#village-shrine"); shrine.innerHTML = "";
    (g.memorial || []).slice(0, 12).forEach((m, i) => {
      const row = document.createElement("div"); row.className = "recruit"; row.style.gridTemplateColumns = "1fr auto";
      row.innerHTML = `<div><b>${this.esc(m.name)}</b> <small>${m.cls}, level ${m.level}, floor ${m.floor}${m.buried ? ` - buried with ${this.esc(m.buried.name)}` : ""}${m.candle ? ` - a candle burns (${this.esc(m.candle)})` : ""}</small>${m.last ? `<small><i>"${this.esc(m.last)}"</i></small>` : ""}<input class="epitaph" type="text" maxlength="60" placeholder="An epitaph (the priest and their ghost will say it)" value="${this.esc(m.epitaph || "")}"></div>`;
      row.querySelector(".epitaph").addEventListener("change", (e) => { g.setEpitaph(i, e.target.value); note.textContent = `An epitaph for ${m.name}.`; });
      if (!m.candle && g.villageLevel("shrine") >= 1) { const b = document.createElement("button"); b.textContent = `Light a candle, ${CM.CANDLE_COST[g.villageLevel("shrine") >= 2 ? 1 : 0]} renown`; b.addEventListener("click", () => { note.textContent = g.lightCandle(i) || `A candle for ${m.name}.`; this.renderVillage(); }); row.appendChild(b); }
      shrine.appendChild(row);
    });
    if (!shrine.children.length) shrine.innerHTML = `<div class="unlock"><small>No name on the memorial yet.</small></div>`;
  }
  // the chronicler, the priest, the keeper: a card each, with what they say and what they do
  renderVillagers(note) {
    const g = this.game, box = this.$("#village-people"), esc = (x) => this.esc(x);
    box.innerHTML = "";
    const card = (V, body, buttons) => {
      const row = document.createElement("div"); row.className = "recruit"; row.style.gridTemplateColumns = "1fr auto";
      const lvl = g.villageLevel(V.building);
      row.innerHTML = `<div><b>${esc(V.name)}</b> <small>${esc(CM.VILLAGE[V.building].name)}${lvl ? "" : ", not yet built"}</small>${lvl ? body : `<small>${esc(V.none)}</small>`}</div>`;
      const acts = document.createElement("div"); acts.style.display = "grid"; acts.style.gap = "4px";
      if (lvl) for (const [label, fn] of buttons) { const b = document.createElement("button"); b.textContent = label; b.addEventListener("click", fn); acts.appendChild(b); }
      row.appendChild(acts); box.appendChild(row);
    };
    const fresh = g.villageLore();
    const W = CM.VILLAGERS.chronicler, rumours = (g.village.rumours || []).filter((r) => !r.seed);
    card(W, `<small>${W.greet.map(esc).join(" ")}</small>${rumours.length ? `<small><i>Promised for the next descent: ${rumours.map((r) => esc(g.rumourText(r))).join("; ")}.</i></small>` : ""}${this.bookOpen ? `<div class="entry">${g.book().map((l) => `<p>${esc(l)}</p>`).join("") || "<p><i>No crown yet. The Book waits for the first.</i></p>"}</div>` : ""}${fresh.length ? `<small><i>Wren has a new page for the village's own chapter (the codex).</i></small>` : ""}`,
      [["Read the Book of Caer Duin", () => { this.bookOpen = !this.bookOpen; this.renderVillage(); }], ["The codex", () => { this.journalPage = "codex"; this.openJournal(); }]]
        .concat(Object.entries(CM.RUMOURS).map(([kind, R]) => [`A rumour: ${R.what.replace("{n}", "...")} (${CM.RUMOUR_COST})`, () => { const err = g.buyRumour(kind); note.textContent = err || `Wren leans in. "${g.rumourText(g.village.rumours[g.village.rumours.length - 1])}."`; this.renderVillage(); }])));
    const P = CM.VILLAGERS.priest;
    card(P, `<small>${P.greet.map(esc).join(" ")}</small><small><i>${esc(CM.PATRIARCH_HISTORY[Math.min(4, g.villageLevel("shrine"))])}</i></small>${this.namesFrom !== undefined ? `<div class="entry">${g.priestNames(this.namesFrom).map((l) => `<p>${esc(l)}</p>`).join("")}</div>` : ""}`,
      [["Hear three names", () => { this.namesFrom = this.namesFrom === undefined ? 0 : (this.namesFrom + 3) % Math.max(1, (g.memorial || []).length); this.renderVillage(); }]]);
    const K = CM.VILLAGERS.keeper, trainers = g.village.trainers || [];
    card(K, `<small>${K.greet.map(esc).join(" ")}</small>${trainers.map((t) => `<small><b>${esc(t.name)}</b> the ${t.cls}${t.how ? `, home ${t.how === "bottom" ? "from the bottom of the world" : t.how === "reminded" ? "having talked the king down" : t.how === "crowned" ? "with the crown" : `alive from floor ${t.floor || "?"}`}` : ""}: ${esc(CM.TRAINER_LINES[t.cls] || "\"I came back. That's the story.\"")}</small>`).join("")}`, []);
  }
  // a wall, read: the carving large, in the hand that cut it, a word at a time at reading speed; Space shows it all
  readWall(text) {
    const el = this.$("#lore-text"), hand = CM.handOf(text);
    el.className = `lore hand hand-${hand}`;
    clearInterval(this.readTimer);
    this.readFull = text;
    if (CM.reducedMotion || this.game.settings.speed === "instant") { el.textContent = text; this.$("#lore-hint").hidden = true; this.openDialog("#dlg-lore"); return; }
    const words = text.split(" "); let n = 0;
    el.textContent = ""; this.$("#lore-hint").hidden = false;
    this.readTimer = setInterval(() => { n++; el.textContent = words.slice(0, n).join(" "); if (n >= words.length) { clearInterval(this.readTimer); this.$("#lore-hint").hidden = true; } }, 90);
    this.openDialog("#dlg-lore");
  }
  finishRead() { clearInterval(this.readTimer); if (this.readFull !== undefined) this.$("#lore-text").textContent = this.readFull; this.$("#lore-hint").hidden = true; }
  // the ending as a page: the chapters completed, in order, as paragraphs; the rest as blank lines
  renderPage(entry, fate) {
    const g = this.game, page = CM.endingPage(g), box = this.$("#over-page");
    this.pageText = { entry, fate, page };
    box.innerHTML = `<div class="list-title">The story, as this party read it</div>` + page.map((p) => p.text ? `<p><b>${this.esc(p.name)}.</b> ${this.esc(p.text)}</p>` : `<p class="blank"><b>${this.esc(p.name)}.</b> <span>${p.done} of ${p.total}</span></p>`).join("");
  }
  savePage() {
    const { entry, fate, page } = this.pageText || {};
    if (!entry) return;
    const W = 760, pad = 40, c = document.createElement("canvas"), p = c.getContext("2d");
    const wrap = (text, font, x, y, width, lh) => { p.font = font; const words = text.split(" "); let line = "", yy = y; for (const w of words) { const t = line ? `${line} ${w}` : w; if (p.measureText(t).width > width && line) { p.fillText(line, x, yy); line = w; yy += lh; } else line = t; } if (line) { p.fillText(line, x, yy); yy += lh; } return yy; };
    const measure = () => { let y = pad + 40; const q = document.createElement("canvas").getContext("2d"); const count = (text, font, lh) => { q.font = font; const words = text.split(" "); let line = "", n = 1; for (const w of words) { const t = line ? `${line} ${w}` : w; if (q.measureText(t).width > W - pad * 2 && line) { line = w; n++; } else line = t; } return n * lh; }; y += count(fate, "italic 15px Georgia", 21) + 20; for (const ch of page) y += ch.text ? count(`${ch.name}. ${ch.text}`, "14px Georgia", 20) + 10 : 26; return y + pad; };
    c.width = W; c.height = measure();
    p.fillStyle = "#E8DCC0"; p.fillRect(0, 0, c.width, c.height);
    p.strokeStyle = "#8A6A3A"; p.lineWidth = 3; p.strokeRect(12, 12, c.width - 24, c.height - 24);
    p.fillStyle = "#3A2C1C"; p.font = "bold 26px Georgia"; p.fillText(this.$("#over-title").textContent, pad, pad + 20);
    let y = pad + 56;
    p.fillStyle = "#4A3A28"; y = wrap(fate, "italic 15px Georgia", pad, y, W - pad * 2, 21) + 20;
    for (const ch of page) {
      if (ch.text) { p.fillStyle = "#2A2016"; y = wrap(`${ch.name}. ${ch.text}`, "14px Georgia", pad, y, W - pad * 2, 20) + 10; }
      else { p.fillStyle = "#8A7A60"; p.font = "italic 13px Georgia"; p.fillText(`${ch.name}.`, pad, y); p.strokeStyle = "#B0A080"; p.lineWidth = 1; p.setLineDash([2, 4]); p.beginPath(); p.moveTo(pad + 160, y - 4); p.lineTo(W - pad, y - 4); p.stroke(); p.setLineDash([]); y += 26; }
    }
    const a = document.createElement("a");
    a.href = c.toDataURL("image/png"); a.download = `Claude and Magic - the page of ${entry.seed || "an expedition"}.png`;
    document.body.appendChild(a); a.click(); a.remove();
  }
  openDialog(sel) { this.closeDialogs(); this.$(sel).classList.add("on"); if (sel === "#dlg-settings") this.showStorage(); }
  closeDialogs() {
    const ending = this.$("#dlg-over").classList.contains("on");
    for (const d of this.root.querySelectorAll(".dialog.on")) d.classList.remove("on");
    if (ending) { this.ending = null; if (this.onEnding) this.onEnding(); }
  }

  // ---- the end of a run: how it went, who came back, what it came to ----
  showEnding(won, entry) {
    const g = this.game, t = entry.tally || {}, board = entry.endless ? g.fameEndless : g.fame, rank = board.indexOf(entry) + 1;
    this.overEntry = entry;
    this.fameBoard = entry.endless ? "endless" : "dungeon";
    this.fameOpen = -1;                                                  // (the Hall of Fame has been re-sorted: an open row would be another's)
    const slot = this.$("#dlg-over .emblem-slot");
    slot.innerHTML = "";
    slot.appendChild(CM.art.emblem(120));
    this.$("#dlg-over").classList.toggle("won", won);
    this.$("#dlg-over").classList.remove("crowning");
    this.$("#over-title").textContent = CM.endlessFall(entry) ? `Floor ${entry.floor} of the endless dark` : entry.dreamed ? CM.ENDINGS.dreamed.title : entry.left ? CM.ENDINGS.left.title : entry.bottom ? "To the bottom of the world" : won && entry.floor > CM.LAST_FLOOR ? `With the crown, into the Deep - and down on floor ${entry.floor}` : won ? "The Lich King is no more" : `The party fell on floor ${entry.floor}`;
    const standing = g.party.filter((h) => h.hp > 0), fallen = g.party.filter((h) => h.hp <= 0);
    const names = (list) => (list.length ? list.map((h) => h.name).join(", ").replace(/, ([^,]*)$/, " and $1") : "The party");
    let text;
    if (CM.endlessFall(entry)) {
      text = `${entry.floor} floors down into a dark with no bottom${won ? ", with the Lich King's crown" : ""}, the last of them fell, in ${CM.themeFor(entry.floor).name} come round again, with ${entry.gold.toLocaleString()} gold. ${names(g.party)} are counted among the deepest.`
        + (t.kills ? ` ${CM.plural(t.kills, "monster")} went down before them.` : "") + " The dark goes on without them. It always did.";
    } else if (entry.dreamed) {
      text = `The crown went into the red stone, and the Root dreamed otherwise. ${names(standing)} climb fifty floors through a city with its bells still up, past a captain at his dinner and a queen singing badly from her barge, with ${entry.gold.toLocaleString()} gold`
        + (fallen.length ? `; ${names(fallen)} ${fallen.length > 1 ? "are" : "is"} there too, in the dream, and wave.` : ", all four of them.") + " The Other Dream is open from the title: go and see what Caer Duin might have been.";
    } else if (entry.left) {
      text = `The Root is still under your feet, dreaming, and you leave it so. ${names(standing)} climb fifty floors into the daylight with the Lich King's crown and ${entry.gold.toLocaleString()} gold`
        + (fallen.length ? `; ${names(fallen)} ${fallen.length > 1 ? "do" : "does"} not come back up.` : ", all four of them.") + " The village prospers. The king will be on his throne again by the time you reach the top; he always was. The codex has a new chapter.";
    } else if (entry.bottom) {
      text = `The Root of the World is still, and the dark below it is only dark. ${names(standing)} climb fifty floors into the daylight with the Lich King's crown and ${entry.gold.toLocaleString()} gold`
        + (fallen.length ? `; ${names(fallen)} ${fallen.length > 1 ? "do" : "does"} not come back up.` : ", all four of them.") + " Nothing is dreaming the king now. The story is over, all the way down.";
    } else if (won && entry.floor > CM.LAST_FLOOR) {
      text = `They took the Lich King's crown and went down into the Deep, where the carvings never went. The last of them fell on floor ${entry.floor}, in ${CM.themeFor(entry.floor).name}, with ${entry.gold.toLocaleString()} gold. The crown lies there with ${names(g.party)}.`
        + (t.kills ? ` ${CM.plural(t.kills, "monster")} went down before them.` : "") + " Somewhere above, another four are sharpening their blades - and they know the way now.";
    } else if (won && entry.reminded) {
      text = `The king sat down, and set the crown on the arm of his throne, and agreed. ${names(standing)} climb twenty floors into the daylight with the Lich King's crown and ${entry.gold.toLocaleString()} gold`
        + (fallen.length ? `; ${names(fallen)} ${fallen.length > 1 ? "do" : "does"} not come back up.` : ", all four of them.") + " No blow was struck in the throne room. The carvings told his story; you told it back to him, and that was enough.";
    } else if (won) {
      text = `The crown rolls from the throne, and the cold goes out of the stone. ${names(standing)} climb twenty floors into the daylight with the Lich King's crown and ${entry.gold.toLocaleString()} gold`
        + (fallen.length ? `; ${names(fallen)} ${fallen.length > 1 ? "do" : "does"} not come back up, and ${fallen.length > 1 ? "their names are" : "that name is"} carved on the last floor beside his.` : ", all four of them.")
        + " The carvings told his story. This one is yours.";
    } else {
      text = `The last of them fell on floor ${entry.floor}, in ${CM.themeFor(entry.floor).name}, with ${entry.gold.toLocaleString()} gold they'll never spend. The dark closes over ${names(g.party)}.`
        + (t.kills ? ` ${CM.plural(t.kills, "monster")} went down before them.` : "") + " Somewhere above, another four are sharpening their blades.";
    }
    this.$("#over-text").textContent = text;
    const roll = this.$("#over-party");
    roll.innerHTML = "";
    for (const h of g.party) {
      const div = document.createElement("div");
      div.className = h.hp > 0 ? "standing" : "fallen";
      div.appendChild(this.portrait(h.cls, 56));
      const who = document.createElement("div");
      who.innerHTML = `<b>${this.esc(h.name)}</b><small>${h.cls}, level ${h.level}</small><small class="fate">${h.hp > 0 ? (won ? "comes home" : "stood to the last") : "fell"}</small>`;
      div.appendChild(who);
      roll.appendChild(div);
    }
    const facts = [["Floors", CM.endlessFall(entry) ? `${entry.floor}, Endless` : `${entry.floor} of ${entry.won || entry.floor > CM.LAST_FLOOR ? CM.BOTTOM : CM.LAST_FLOOR}`], ["Gold", entry.gold.toLocaleString()], ["Monsters slain", t.kills || 0],
      ["Chests opened", t.chests || 0], ["Steps walked", (t.steps || 0).toLocaleString()], ["Fights", `${t.fights || 0}${t.fled ? ` (${t.fled} fled)` : ""}`],
      ["Kit", (CM.KITS[entry.kit] || CM.KITS.pauper).name], ["Difficulty", (CM.DIFFICULTIES[entry.difficulty] || CM.DIFFICULTIES.fair).name], ["Seed", `${entry.seed}${entry.daily ? " (today's)" : ""}`],
      [entry.endless ? "Endless board" : "Hall of Fame", rank ? `${CM.ordinal(rank)} of ${board.length}` : "not among the ten"]];
    if (t.guardians && t.guardians.length) facts.splice(6, 0, ["Guardians slain", this.guardianNames(t.guardians)]);
    if ((g.vaults || []).length) facts.push(["In the vault", g.vaults.map((v) => v.name).join(", ") + ", for the next party"]);
    facts.push(["Renown", `${entry.renown || 0} brought home; the village has ${g.renown()}`]);
    if (entry.titles && entry.titles.length) facts.push(["Earned", entry.titles.map((id) => (CM.ACHIEVEMENTS[id] || { name: id }).name).join(", ")]);
    this.$("#over-tally").innerHTML = facts.map(([k, v]) => `<div><span>${k}</span><b>${this.esc(v)}</b></div>`).join("");
    this.renderRetire();
    this.renderPage(entry, text);
    this.openDialog("#dlg-over");                                      // (opening closes whatever was open - an ending too - so the kind is set after)
    this.ending = won ? "victory" : "lament";
    if (this.onEnding) this.onEnding();
  }

  // the guildhall: a hero who came home may retire as a trainer, at the run's end
  renderRetire() {
    const g = this.game, box = this.$("#over-retire");
    box.innerHTML = "";
    if (g.villageLevel("guildhall") < 1 || g.retiredThisRun) { if (g.retiredThisRun) box.textContent = "A hero has retired to the guildhall."; return; }
    const can = g.party.map((h, i) => [h, i]).filter(([h]) => h.hp > 0 && (h.boons || []).length);
    if (!can.length) return;
    box.appendChild(Object.assign(document.createElement("span"), { textContent: "Retire to the guildhall as a trainer: " }));
    for (const [h, i] of can) {
      const b = document.createElement("button");
      b.textContent = `${h.name} (teaches ${CM.BOONS[h.boons[0]].name})`;
      b.addEventListener("click", () => { const note = g.retire(i); box.textContent = note || `${h.name} hangs up the pack, and will teach every ${h.cls} who comes after.`; });
      box.appendChild(b);
    }
  }

  portrait(cls, size) {
    const look = this.game.settings.look, key = `${look}:${cls}:${size}`;
    if (!this.portraits[key]) this.portraits[key] = CM.art.portrait(cls, size, look);
    const c = document.createElement("canvas");
    c.width = c.height = size;
    c.getContext("2d").drawImage(this.portraits[key], 0, 0);
    return c;
  }

  icon(item, size = 22) {                                               // a thing's picture, by the theme
    const c = CM.art.itemIcon(item, size, this.game.settings.look);
    c.className = "icon";
    return c;
  }

  esc(s) { return String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }

  // ---- settings ----
  // how much of the browser's keeping the game uses: the runs are small now, but a browser gives a site about 5 MB in all
  showStorage() {
    const used = CM.store.used(), kb = Math.round(used / 1024);
    this.$("#set-storage").textContent = `Saved in this browser: ${kb < 1 ? "under 1" : kb.toLocaleString()} KB (runs, the Hall of Fame, settings).${used > 3.5 * 1024 * 1024 ? " That is close to what a browser allows: Export your runs to keep them safe." : ""}  Claude and Magic v${CM.version}, built ${CM.built}.`;
  }
  _settings() {
    const g = this.game, s = g.settings;
    const sound = this.$("#set-sound"), vol = this.$("#set-volume"), music = this.$("#set-music"), mvol = this.$("#set-music-volume");
    const smooth = this.$("#set-smooth"), fps = this.$("#set-fps"), look = this.$("#set-look"), titleLook = this.$("#look"), tap = this.$("#set-tap"), skipWalk = this.$("#set-skipwalk");
    const speed = this.$("#set-speed"), text = this.$("#set-text"), motion = this.$("#set-motion"), contrast = this.$("#set-contrast"), swapab = this.$("#set-swapab"), render = this.$("#set-render"), layout = this.$("#set-layout");
    layout.value = s.layout || "auto";
    const detail = this.$("#set-detail"); detail.value = CM.DETAIL[s.detail] !== undefined ? s.detail : "medium";
    speed.value = s.speed || "normal"; text.value = s.text || "normal"; motion.checked = Boolean(s.motion); contrast.checked = Boolean(s.contrast); swapab.checked = Boolean(s.swapAB); render.value = s.render || "auto";
    for (const sel of [look, titleLook]) sel.innerHTML = Object.entries(CM.LOOKS).map(([id, l]) => `<option value="${id}">${l.name}</option>`).join("");
    sound.checked = s.sound; vol.value = Math.round(s.volume * 100); music.checked = s.music !== false; mvol.value = Math.round((s.musicVolume === undefined ? 0.5 : s.musicVolume) * 100);
    smooth.checked = s.smooth; fps.checked = s.fps; look.value = titleLook.value = s.look || "pixel"; tap.checked = s.tapMove !== false; skipWalk.checked = Boolean(s.skipWalk); this.$("#set-season").value = s.season || ""; this.$("#set-autoland").checked = s.autoLand !== false;
    const note = () => { this.$("#set-look-note").textContent = CM.LOOKS[s.look] ? CM.LOOKS[s.look].what + "." : ""; };
    note();
    const apply = () => {
      s.sound = sound.checked; s.volume = vol.value / 100; s.music = music.checked; s.musicVolume = mvol.value / 100; s.smooth = smooth.checked; s.fps = fps.checked; s.season = this.$("#set-season").value || ""; s.autoLand = this.$("#set-autoland").checked; s.tapMove = tap.checked; s.skipWalk = skipWalk.checked;
      s.speed = speed.value; s.text = text.value; s.motion = motion.checked; s.contrast = contrast.checked; s.swapAB = swapab.checked; s.render = render.value; s.layout = layout.value; s.detail = detail.value;
      g.saveSettings();
      g.emit("settings", s);
    };
    for (const el of [sound, vol, music, mvol, smooth, fps, tap, motion, contrast, swapab]) el.addEventListener("input", apply);
    for (const el of [speed, text, render, layout, detail]) el.addEventListener("change", apply);
    for (const sel of [look, titleLook]) sel.addEventListener("change", () => { s.look = sel.value; look.value = titleLook.value = s.look; note(); apply(); });
  }

  // ---- the statistics: every expedition that ended, summed (CM.statistics over the ledger) ----
  openStats() {
    const g = this.game, box = this.$("#stats"), st = CM.statistics(g.ledger || []), esc = (x) => this.esc(x);
    const bar = (n, of) => `<span class="bar"><i style="width: ${of ? Math.round((n / of) * 100) : 0}%"></i></span>`;
    if (!st.runs) box.innerHTML = `<p class="small">${esc(CM.t("stats.none"))}</p>`;
    else {
      const most = Math.max(1, ...st.bands.map((b) => b.fell + b.through));
      box.innerHTML = `<p>${esc(CM.t("stats.runs", { n: st.runs, crowns: st.crowns, bottoms: st.bottoms, fell: st.fell }))}. ${esc(CM.t("stats.deepest", { n: st.deepest }))}</p>`
        + `<p class="small">${esc(CM.t("stats.first", { first: st.first, last: st.last }))} ${esc(CM.t("stats.totals", { steps: st.steps, fights: st.fights, kills: st.kills, fled: st.fled, chests: st.chests }))}</p>`
        + `<h3>${esc(CM.t("stats.bands"))}</h3><table class="stats">${st.bands.filter((b) => b.fell + b.through).map((b) => `<tr><td>${b.to === Infinity ? "51 and below" : `${b.from} - ${b.to}`}</td><td>${bar(b.fell, most)}</td><td>${b.fell} fell${b.through ? `, ${b.through} went on` : ""}</td></tr>`).join("")}</table>`
        + `<h3>${esc(CM.t("stats.callings"))}</h3><table class="stats">${Object.entries(st.callings).sort((x, y) => y[1].n - x[1].n).map(([c, r]) => `<tr><td>${esc((CM.CLASSES[c] || { name: c }).name)}</td><td>${bar(r.n, st.favourite[1].n)}</td><td>${esc(CM.t("stats.calling.row", { n: r.n, crowns: r.crowns }))}</td></tr>`).join("")}</table>`
        + `<h3>${esc(CM.t("stats.spent"))}</h3><p class="small">${esc(CM.t("stats.spent.total", { n: st.spentTotal }))}</p><table class="stats">${Object.entries(st.spent).sort((x, y) => y[1] - x[1]).map(([w, n]) => `<tr><td>${esc(w)}</td><td>${bar(n, st.spentTotal)}</td><td>${n.toLocaleString()}</td></tr>`).join("")}</table>`
        + `<h3>${esc(CM.t("stats.difficulty"))}</h3><table class="stats">${Object.entries(st.difficulties).map(([d, r]) => `<tr><td>${esc((CM.DIFFICULTIES[d] || { name: d }).name)}</td><td>${bar(r.crowns, r.n)}</td><td>${esc(CM.t("stats.difficulty.row", { n: r.n, crowns: r.crowns, a: r.a }))}</td></tr>`).join("")}</table>`
        + (st.old ? `<p class="small">${esc(CM.t("stats.old", { n: st.old }))}</p>` : "");
    }
    this.openDialog("#dlg-stats");
  }
  // a save or a film that came in the page's link (#save=, #film=): ask, then import or watch
  offerLink(payload) {
    if (!payload) return;
    this.$("#link-title").textContent = CM.t("link.title");
    this.$("#link-text").textContent = CM.t(payload.kind === "film" ? "link.film" : "link.save");
    this.$("#link-note").textContent = "";
    const yes = this.$("#btn-link-yes"), fresh = yes.cloneNode(true);
    yes.replaceWith(fresh);
    fresh.addEventListener("click", () => {
      CM.fromLink(payload.code).then((text) => {
        if (payload.kind === "film") { const spec = text && CM.parseFilm(text); if (!spec) { this.$("#link-note").textContent = CM.t("link.bad"); return; } this.closeDialogs(); this.watch(spec); return; }
        const err = text ? this.game.importText(text) : CM.t("link.bad");
        if (err) { this.$("#link-note").textContent = err; return; }
        this.closeDialogs(); this.refreshTitle(); this.game.titleNote = "Imported from the link."; this.refreshTitle();
      });
    });
    this.openDialog("#dlg-link");
  }
  // the save (or a film code) as a link, in the box and on the clipboard
  makeLink(kind, text, box, note) {
    const base = location.href.split("#")[0];
    CM.toLink(text).then((code) => {
      box.value = `${base}#${kind}=${code}`;
      note.textContent = CM.t(kind === "film" ? "link.film.made" : "link.made");
      if (navigator.clipboard) navigator.clipboard.writeText(box.value).catch(() => {});
    });
  }
  showInstall(on) { const b = this.$("#btn-install"); if (b) { b.hidden = !on; b.textContent = CM.t("install.button"); } }

  toggleFps() {
    this.game.settings.fps = !this.game.settings.fps;
    this.$("#set-fps").checked = this.game.settings.fps;
    this.game.saveSettings();
    this.game.emit("settings", this.game.settings);
  }

  guardianNames(ids) { return ids.map((id) => (CM.GUARDIANS[id] || { name: id }).name.replace(/^The /, "the ")).join(", "); }




  // ---- ways to play: the keys as set, the summary card, the gamepad's focus, a tap on the view ----
  renderKeys() {
    const g = this.game, keys = this.$("#dlg-keys table.kb"), k = g.settings.keys || CM.DEFAULT_KEYS;
    keys.innerHTML = CM.KEY_ACTIONS.map(([id, what]) => `<tr data-action="${id}"><td><kbd>${this.esc(CM.keyName(k[id]))}</kbd>${this.rebinding === id ? " <i>press a key...</i>" : ""}</td><td>${what}</td><td><button data-rebind="${id}">Change</button></td></tr>`).join("")
      + `<tr><td><kbd>Arrows</kbd></td><td>move and turn as well, always</td><td></td></tr><tr><td><kbd>1 - 4</kbd></td><td>a hero's sheet; in a list, the pick</td><td></td></tr>`
      + `<tr><td><kbd>Esc</kbd></td><td>close a screen / pause</td><td></td></tr><tr><td><kbd>F3</kbd></td><td>frames per second</td><td></td></tr>`
      + `<tr><td colspan="3" class="small" style="white-space: normal; max-width: 560px; padding-top: 8px">${this.esc(CM.t("pad.help"))}</td></tr>`;
    for (const b of keys.querySelectorAll("button[data-rebind]")) b.addEventListener("click", () => { this.rebinding = this.rebinding === b.dataset.rebind ? null : b.dataset.rebind; this.rebindingPad = null; this.renderKeys(); });
    const pad = this.$("#dlg-keys table.pad"), P = g.settings.pad || CM.DEFAULT_PAD;
    this.$("#pad-note").textContent = CM.t("pad.note");
    pad.innerHTML = CM.PAD_ACTIONS.map(([id, what]) => `<tr data-action="${id}"><td><kbd>${this.esc(CM.padName(P[id]))}</kbd>${this.rebindingPad === id ? ` <i>${this.esc(CM.t("pad.press"))}</i>` : ""}</td><td>${what}</td><td><button data-rebindpad="${id}">Change</button></td></tr>`).join("")
      + `<tr><td><kbd>Stick, d-pad</kbd></td><td>move and turn, always; in a list, the highlight</td><td></td></tr>`;
    for (const b of pad.querySelectorAll("button[data-rebindpad]")) b.addEventListener("click", () => { this.rebindingPad = this.rebindingPad === b.dataset.rebindpad ? null : b.dataset.rebindpad; this.rebinding = null; this.renderKeys(); });
  }
  // a gamepad's button for an action (the d-pad is the d-pad; one button, one action)
  rebindPad(action, i) {
    const g = this.game, P = g.settings.pad || (g.settings.pad = Object.assign({}, CM.DEFAULT_PAD));
    if (!(action in CM.DEFAULT_PAD) || typeof i !== "number" || i >= 12) { this.rebindingPad = null; this.renderKeys(); return false; }
    for (const other of Object.keys(P)) if (P[other] === i && other !== action) P[other] = CM.DEFAULT_PAD[other] === i ? "" : CM.DEFAULT_PAD[other];
    P[action] = i;
    this.rebindingPad = null;
    g.saveSettings();
    g.emit("settings", g.settings);
    this.renderKeys();
    return true;
  }
  rebind(action, code) {
    const g = this.game, k = g.settings.keys || (g.settings.keys = Object.assign({}, CM.DEFAULT_KEYS));
    if (!CM.DEFAULT_KEYS[action] || !code || code === "Escape" || /^F\d+$/.test(code)) { this.rebinding = null; this.renderKeys(); return false; }
    for (const other of Object.keys(k)) if (k[other] === code && other !== action) k[other] = CM.DEFAULT_KEYS[other] === code ? "" : CM.DEFAULT_KEYS[other];   // (one key, one action)
    k[action] = code;
    this.rebinding = null;
    g.saveSettings();
    g.emit("settings", g.settings);
    this.renderKeys();
    return true;
  }
  resetKeys() { this.game.settings.keys = Object.assign({}, CM.DEFAULT_KEYS); this.game.settings.pad = Object.assign({}, CM.DEFAULT_PAD); this.rebinding = null; this.rebindingPad = null; this.game.saveSettings(); this.game.emit("settings", this.game.settings); this.renderKeys(); }

  // a gamepad's way through buttons: the focus moves along the visible ones, A presses
  padTargets() {
    const open = this.root.querySelector(".dialog.on .box");
    const scope = open || (this.xmenu || (this.game.mode === "combat" && this.cmenu && this.cmenu.kind !== "main") ? this.$("#actions") : null);
    if (!scope) return [];
    return [...scope.querySelectorAll("button")].filter((b) => !b.disabled && b.offsetParent !== null);
  }
  padFocus(delta) {
    const list = this.padTargets();
    for (const b of this.root.querySelectorAll(".padfocus")) b.classList.remove("padfocus");
    if (!list.length) { this.padIndex = -1; return null; }
    this.padIndex = ((this.padIndex === undefined || this.padIndex < 0 ? (delta > 0 ? -1 : 0) : this.padIndex) + delta + list.length) % list.length;
    const b = list[this.padIndex];
    b.classList.add("padfocus");
    if (b.scrollIntoView) b.scrollIntoView({ block: "nearest" });
    return b;
  }
  padPress() {
    const list = this.padTargets();
    if (!list.length) return false;
    const b = list[this.padIndex >= 0 && this.padIndex < list.length ? this.padIndex : 0];
    b.click();
    this.padIndex = -1;
    return true;
  }
  // a tap (or a click) on the view, out of a fight: the sides turn, the top walks, the bottom steps back
  tapView(fx, fy) {
    const g = this.game;
    if (g.mode !== "explore" || !g.settings.tapMove || this.dialogOpen()) return false;
    if (fx < 0.3) g.turn(-1); else if (fx > 0.7) g.turn(1); else if (fy < 0.65) g.move(0); else g.move(2);
    return true;
  }


  // the Lich King is slain: the victory, and the choice - into the daylight, or down into the Deep
  showCrowning() {
    const g = this.game, dlg = this.$("#dlg-over");
    this.overEntry = null;
    const slot = this.$("#dlg-over .emblem-slot");
    slot.innerHTML = "";
    slot.appendChild(CM.art.emblem(120));
    dlg.classList.add("won"); dlg.classList.add("crowning");
    this.$("#over-title").textContent = g.reminded ? "The king remembers" : "The Lich King is no more";
    const standing = g.party.filter((h) => h.hp > 0), names = (list) => (list.length ? list.map((h) => h.name).join(", ").replace(/, ([^,]*)$/, " and $1") : "The party");
    this.$("#over-text").textContent = (g.reminded ? `Mordeth sits on his throne with the crown on its arm, and is dust. ${names(standing)} stand in the quiet with the Lich King's crown and ${g.gold.toLocaleString()} gold. ` : `The crown rolls from the throne, and the cold goes out of the stone. ${names(standing)} stand in the throne room with the Lich King's crown and ${g.gold.toLocaleString()} gold. `)
      + "Behind the throne the floor has split: a shaft goes down into a dark that was never his. The carvings never spoke of it. Climb into the daylight as legends - or go down, and see what the king was listening to.";
    const roll = this.$("#over-party");
    roll.innerHTML = "";
    for (const h of g.party) {
      const div = document.createElement("div");
      div.className = h.hp > 0 ? "standing" : "fallen";
      div.appendChild(this.portrait(h.cls, 56));
      const who = document.createElement("div");
      who.innerHTML = `<b>${this.esc(h.name)}</b><small>${h.cls}, level ${h.level}</small><small class="fate">${h.hp > 0 ? "stands" : "fell"}</small>`;
      div.appendChild(who);
      roll.appendChild(div);
    }
    const t = g.tally || {};
    this.$("#over-tally").innerHTML = [["Floors", `${CM.LAST_FLOOR} of ${CM.LAST_FLOOR} - and ${g.endless ? "no bottom" : (CM.BOTTOM - CM.LAST_FLOOR) + " more"} below`], ["Gold", g.gold.toLocaleString()], ["Monsters slain", t.kills || 0],
      ...(t.towerBest ? [["Mage Tower", `floor ${t.towerBest} of ${CM.TOWER_FLOORS}`]] : []), ["Steps walked", (t.steps || 0).toLocaleString()], ["Guardians slain", (t.guardians || []).length ? this.guardianNames(t.guardians) : "none"]].map(([k, v]) => `<div><span>${k}</span><b>${this.esc(v)}</b></div>`).join("");
    this.openDialog("#dlg-over");
    this.ending = "victory";
    if (this.onEnding) this.onEnding();
  }

  // ---- the dungeon's people and puzzles: a word with someone, a riddle at a door, the journal ----
  askRiddle(k) {
    const g = this.game, f = g.floor.features[k], r = f && CM.RIDDLES[f.riddle];
    if (!r) return;
    const rnd = new CM.Random(CM.hashSeed(`${g.seed}:riddle:${k}:${f.tries || 0}`));
    this.riddle = { k, answers: rnd.shuffle([r.a, ...r.wrong]) };
    this.$("#riddle-q").textContent = r.q;
    const box = this.$("#riddle-answers");
    box.innerHTML = "";
    this.riddle.answers.forEach((a, i) => {
      const b = document.createElement("button");
      b.innerHTML = `<kbd>${i + 1}</kbd>${this.esc(a)}`;
      b.addEventListener("click", () => this.pickRiddle(i + 1));
      box.appendChild(b);
    });
    this.openDialog("#dlg-riddle");
  }
  pickRiddle(n) {
    const r = this.riddle;
    if (!r || !r.answers[n - 1]) return;
    this.closeDialogs();
    this.game.answerRiddle(r.k, r.answers[n - 1]);
    this.riddle = null;
    this.refresh();
  }
  // a choice on the floor: the options as buttons (1-3 pick them too)
  askChoice(c) {
    this.choice = c;
    this.$("#choice-title").textContent = c.title;
    this.$("#choice-text").textContent = c.text;
    const box = this.$("#choice-options");
    box.innerHTML = "";
    c.options.forEach((label, i) => {
      const b = document.createElement("button");
      b.innerHTML = `<kbd>${i + 1}</kbd>${this.esc(label)}`;
      b.addEventListener("click", () => this.pickChoice(i + 1));
      box.appendChild(b);
    });
    this.openDialog("#dlg-choice");
  }
  pickChoice(n) {
    const c = this.choice;
    if (!c || !c.options[n - 1]) return;
    this.closeDialogs();
    this.choice = null;
    if (c.ending) this.game.ending(n - 1); else if (c.parley) this.game.parley(c.k, n - 1); else if (c.rivals) this.game.chooseRivals(c.k, n - 1); else this.game.choose(c.k, n - 1);
    this.refresh();
  }
  // Where to?: the doors and the places of this surface floor, by name, with the walk's length; one click walks the party there
  openWhereTo() {
    const g = this.game, box = this.$("#whereto-list"), places = CM.wayPlaces(g);
    box.innerHTML = places.length ? places.map((p, i) => `<button class="pick" data-i="${i}" ${p.steps === null ? "disabled" : ""}>${this.esc(p.name)} <small>${p.steps === null ? "no known way" : CM.plural(p.steps, "step")}</small></button>`).join("") : `<div class="small">Nowhere to go from here but on foot.</div>`;
    for (const b of box.querySelectorAll("button.pick")) b.addEventListener("click", () => { const p = places[Number(b.dataset.i)]; this.closeDialogs(); if (g.travelTo(p.x, p.y)) g.say(`Off to ${p.name.charAt(0).toLowerCase() + p.name.slice(1)}.`); this.refresh(); });
    this.openDialog("#dlg-whereto");
  }
  openJournal() {
    const g = this.game, box = this.$("#journal-list"), entries = g.journal || [];
    const part = (title, kind, order) => {
      const list = entries.filter((e) => e.kind === kind).sort(order || ((a, b) => a.floor - b.floor));
      if (!list.length) return "";
      return `<div class="list-title">${title}</div>` + list.map((e) => `<div class="entry"><small>${e.floor ? `Floor ${e.floor}` : ""}${e.who ? ` - ${this.esc(e.who)}` : ""}</small><p>${this.esc(e.text)}</p></div>`).join("");
    };
    const html = part("Carved into the stone", "carving") + part("What the dead said", "ghost") + part("Riddles answered", "riddle") + this.bestiaryHtml() + this.combosHtml();
    for (const b of this.root.querySelectorAll("#dlg-journal .boards button")) b.classList.toggle("on", b.dataset.page === (this.journalPage || "journal"));
    if (this.journalPage === "codex") { box.innerHTML = this.codexHtml(); this.openDialog("#dlg-journal"); return; }
    if (this.journalPage === "things") { box.innerHTML = this.compendiumHtml(); this.openDialog("#dlg-journal"); return; }
    if (this.journalPage === "errands") { box.innerHTML = this.errandsHtml(); this.wireErrands(box); this.openDialog("#dlg-journal"); return; }
    box.innerHTML = html || `<div class="small">Nothing yet. Read the walls (Space before a carving), and listen to whoever you meet; the hermit pays for stories.</div>`;
    this.openDialog("#dlg-journal");
  }
  // the errands (64b-people.js): what each of the six asks, taken, done this season; take one, or hand one in, in the town
  errandsHtml() {
    const g = this.game, E = g.errands(), inTown = g.floor && g.floor.number === 0, season = CM.errandSeason();
    const rows = Object.entries(CM.ERRANDS).map(([id, R]) => {
      const t = E.taken[id], who = R.giver.charAt(0).toUpperCase() + R.giver.slice(1);
      if (t) { const left = g.errandLeft(id); return `<div class="entry"><small>${this.esc(who)} - taken</small><p>${this.esc(g.errandAsk(id))}</p><p class="small">${left ? `Still to do: ${this.esc(left)}.` : `Done: ${inTown ? "hand it in." : "hand it in, in the town."}`}</p>${!left && inTown ? `<button data-errand-hand="${id}">Hand it in</button>` : ""}</div>`; }
      if (E.done[id] === season) return `<div class="entry"><small>${this.esc(who)} - done this season</small><p class="small">Nothing more until the season turns.</p></div>`;
      const can = g.errandOffered(id);
      return `<div class="entry"><small>${this.esc(who)} - asks</small><p>${this.esc(R.ask.replace("{n}", CM.errandFloor(id, season) || ""))}</p>${inTown ? `<button data-errand-take="${id}" ${can ? "" : "disabled"}>${can ? "Take it on" : "Three at a time"}</button>` : `<p class="small">Taken in the town.</p>`}</div>`;
    }).join("");
    const perks = Object.keys((g.village || {}).perks || {});
    return `<div class="small">Six of the townsfolk have errands below: three at a time, one from each a season. What they pay is theirs to give.${perks.length ? ` Favours kept: ${perks.map((p) => ({ tavern: "the round at half price", merchant: "a tenth off at the merchant", dog: "the farm's dog" })[p] || p).join(", ")}.` : ""}</div>${rows}`;
  }
  wireErrands(box) {
    const g = this.game;
    for (const b of box.querySelectorAll("[data-errand-take]")) b.addEventListener("click", () => { g.takeErrand(b.dataset.errandTake); this.openJournal(); this.refresh(); });
    for (const b of box.querySelectorAll("[data-errand-hand]")) b.addEventListener("click", () => { const note = g.handInErrand(b.dataset.errandHand); if (note) g.say(note); this.openJournal(); this.refresh(); });
  }
  // a row of followers to take on, where they are to be had
  hireRow(into, ids, after) {
    const g = this.game, row = document.createElement("div"); row.className = "small";
    if (g.follower) { const s = document.createElement("span"); s.textContent = `Behind the party: ${g.followerName()}. `; row.appendChild(s); const b = document.createElement("button"); b.textContent = "Let them go"; b.addEventListener("click", () => { g.dismissFollower(); after(); this.refresh(); }); row.appendChild(b); into.appendChild(row); return; }
    for (const id of ids) { const F = CM.FOLLOWERS[id], why = g.canHire(id), b = document.createElement("button");
      b.textContent = `Take on a ${F.name}${F.price ? `, ${F.price} gold` : ""}`; b.title = why || F.what; b.disabled = Boolean(why);
      b.addEventListener("click", () => { const note = g.hireFollower(id); if (note) g.say(note); after(); this.refresh(); }); row.appendChild(b); }
    into.appendChild(row);
  }
  // the compendium: every base, by group, the unseen as outlines
  compendiumHtml() {
    const groups = CM.compendium(this.game.compendium), esc = (x) => this.esc(x);
    const seen = groups.reduce((n, g) => n + g.seen, 0), total = groups.reduce((n, g) => n + g.total, 0);
    let html = `<div class="small">${seen} of ${total} kinds of thing found, ever. An unknown thing counts once it is named.</div>`;
    const named = (this.game.compendium || {}).named || [];
    if (named.length) html += `<div class="list-title">Named weapons <small>${named.length}</small></div>` + named.map((w) => `<div class="entry"><small>${esc(w.base)}, ${esc(w.bearer)}'s, ${esc(w.date)}</small><p><b>${esc(w.name)}</b>${w.history.length ? ` - ${esc(w.history.join("; "))}` : ""}</p></div>`).join("");
    for (const g of groups) html += `<div class="list-title">${esc(g.name)} <small>${g.seen} of ${g.total}</small></div><div class="things">${g.list.map((b) => `<span class="thing ${b.seen ? "seen" : "unseen"}" title="${b.seen ? `first found on floor ${b.when.floor}, ${esc(b.when.date)}` : "not yet found"}">${b.seen ? esc(b.id) : "?".repeat(Math.min(12, b.id.length))}</span>`).join("")}</div>`;
    return html;
  }
  // the codex: the story in chapters, the unread as blank lines, a lie struck through once the truth below it is read
  codexHtml() {
    const chapters = CM.codex(this.game), esc = (x) => this.esc(x);
    const readAll = chapters.reduce((n, c) => n + c.done, 0), total = chapters.reduce((n, c) => n + c.total, 0);
    let html = `<div class="small">${readAll} of ${total} lines of the story of Caer Duin. Each band's five carvings and its guardian's make a chapter; a line read deeper that gives the lie to one above strikes it through.</div>`;
    for (const c of chapters) {
      html += `<div class="list-title">${esc(c.name)} <small>${c.done} of ${c.total}${c.complete ? " - complete" : ""}</small></div><div class="entry"><p class="epigraph">${esc(c.epigraph)}</p></div>`;
      for (const l of c.lines) {
        if (!l.read) { html += `<div class="entry unread"><small>${l.floor ? `Floor ${l.floor}` : l.who ? esc(l.who) : ""}</small><p class="blank">&nbsp;</p></div>`; continue; }
        html += `<div class="entry"><small>${l.floor ? `Floor ${l.floor}` : ""}${l.who ? ` ${esc(l.who)}` : ""}</small><p${l.struck ? ' class="struck"' : ""}>${esc(l.text)}</p>${l.struck ? `<p class="truth">${esc(l.truth)}</p>` : ""}</div>`;
      }
    }
    return html;
  }

  // the bestiary: every kind met, in the order of the depths, with what it does and what it has been seen to fear
  bestiaryHtml() {
    const g = this.game, b = g.bestiary || {}, kinds = CM.MONSTERS.filter((m) => b[m.name] && b[m.name].seen);
    if (!kinds.length) return "";
    const shape = (m) => { const [hp, atk, df] = m.shape || [1, 1, 1]; const w = []; if (hp >= 1.4) w.push("tough"); else if (hp <= 0.7) w.push("frail"); if (atk >= 1.2) w.push("hits hard"); if (df >= 1.3) w.push("armoured"); else if (df <= 0.7) w.push("thin-skinned"); return w.join(", "); };
    const rows = kinds.map((m) => { const e = b[m.name], words = [shape(m), m.ability ? CM.ABILITY_WORDS[m.ability] : "", m.touch ? `its touch may leave a hero ${CM.STATUSES[m.touch.status].name.toLowerCase()}` : "", m.undead ? "undead" : "", m.row === "back" ? "keeps to the back row" : ""].filter(Boolean);
      return `<div class="entry"><small>${m.deep ? CM.THEMES[m.deep].name : "The first twenty floors"} - met ${e.seen}, slain ${e.slain}</small><p><b>${this.esc(m.name)}</b> - ${this.esc(words.join("; "))}.${e.weak.length ? ` Fears ${e.weak.map((x) => CM.ELEMENT_NAMES[x] || x).join(" and ")}.` : ""}${e.resist.length ? ` Shrugs off ${e.resist.map((x) => CM.ELEMENT_NAMES[x] || x).join(" and ")}.` : ""}</p></div>`; });
    return `<div class="list-title">Bestiary</div>` + rows.join("");
  }
  combosHtml() {
    const found = Object.keys(CM.COMBOS).filter((id) => (this.game.combos || {})[id]);
    const rows = Object.entries(CM.COMBOS).map(([id, c]) => `<div class="entry"><p>${found.includes(id) ? `<b>${c.name}</b> - ${this.esc(c.what)} <small>(done ${this.game.combos[id]} ${this.game.combos[id] === 1 ? "time" : "times"})</small>` : `<b>?</b> <small>A combo not yet found.</small>`}</p></div>`);
    const woven = Object.keys(CM.WEAVES).filter((id) => (this.game.weaves || {})[id]);
    const wrows = Object.entries(CM.WEAVES).map(([id, w]) => `<div class="entry"><p>${woven.includes(id) ? `<b>${w.name}</b> - ${this.esc(w.what)}` : `<b>?</b> <small>A weave not yet found: two casters, one round.</small>`}</p></div>`);
    return `<div class="list-title">Combos (${found.length} of ${Object.keys(CM.COMBOS).length} found)</div>` + rows.join("") + `<div class="list-title">Weaves (${woven.length} of ${Object.keys(CM.WEAVES).length} found)</div>` + wrows.join("");
  }
};
