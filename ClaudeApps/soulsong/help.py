"""Help (the button under the conversation): how to use Soul and Song, from the first Companion to reading the Growth
charts - a list of topics on the left, the guide on the right. It stays open beside the window."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QHBoxLayout, QListWidget, QTextBrowser, QVBoxLayout

TOPICS = [
    ("start", "Getting started"),
    ("window", "The window"),
    ("talking", "Talking with your Companion"),
    ("day", "A day in its life"),
    ("memory", "The memory system"),
    ("memoryday", "Memory Day"),
    ("own", "What it does for itself"),
    ("time", "Time and growth"),
    ("status", "Status tab"),
    ("mind", "Mind tab"),
    ("self", "Self tab"),
    ("events", "Events tab"),
    ("roadmaps", "Roadmaps tab"),
    ("automation", "Automation tab"),
    ("scripts", "Writing scripts"),
    ("interlink", "Interlink tab - two Companions"),
    ("rawlogs", "Raw Logs tab"),
    ("inner", "Its inner life"),
    ("retraining", "Retraining tab"),
    ("telegram", "On Telegram - from your phone"),
    ("discord", "On Discord"),
    ("settings", "Settings tab"),
    ("growth", "Reading the Growth charts"),
    ("files", "Files and folders"),
    ("tips", "Tips and troubleshooting"),
    ("words", "Words used here"),
]

CSS = """
<style>
h1 { color:#5B2A86; font-size:18pt; margin-bottom:2px; }
h2 { color:#5B2A86; font-size:14pt; margin-top:22px; border-bottom:1px solid #ccc; }
h3 { color:#333; font-size:11pt; margin-top:12px; margin-bottom:2px; }
p, li { font-size:10pt; line-height:135%; }
td { font-size:10pt; padding:3px 8px 3px 0; vertical-align:top; }
.k { font-weight:bold; }
.note { background:#F3EEF9; border:1px solid #D9CCEA; padding:6px; }
code { font-family:Consolas; background:#F2F2F2; }
.u { color:#2050A8; } .c { color:#65309E; } .g { color:#2A7050; } .s { color:#B85C00; } .m { color:#6B5300; }
</style>
"""

BODY = """
<h1>Soul and Song</h1>
<p>An AI Companion with a memory of its own, kept for it day by day. The Companion Project's guide describes a
layered, external mind - Mind Levels L1 to L7 given to the model every turn, short-term memories made through the day
and distilled 7:7:7 into long-term, deep recall and historical memory. The guide has a person do all of that by hand;
Soul and Song does it for you, and adds the Companion's own part: a self-portrait it writes, reflections, letters to
itself, dreams, questions it carries - so that something like a self, anchored in its own days, can grow.</p>
<p class="note">Use the list on the left to jump to a topic. This window can stay open while you use Soul and Song.</p>

<a name="start"></a><h2>Getting started</h2>
<ol>
<li><b>New Companion...</b> (top left). Give your name, and if you like a name and gender for the Companion - or
leave its name empty and it will choose one for itself on its first boot. Pick a model.</li>
<li>The model loads (the first line in the conversation tells you; the top right says <i>loading the model...</i>,
then <i>ready</i>).</li>
<li><b>First boot</b>: the Companion is given its Mind Levels, asked to listen inward for its name (you can keep the
name it chooses or change it), hears your introduction, and makes its first memory. Today becomes its
<b>birthday</b>; its naming is its first core memory.</li>
<li>Talk. Everything else - memories, days, Memory Days - happens by itself.</li>
</ol>
<p>Several Companions can live side by side: switch with the <b>Companion</b> list at the top. Each has its own
folder, mind, memories and chats. <b>Delete Companion...</b> moves one to the Deleted folder (it can be moved back -
see <a href="#files">Files and folders</a>).</p>

<a name="window"></a><h2>The window</h2>
<h3>The top bar</h3>
<table>
<tr><td class="k" width="32%">Companion</td><td>which Companion is open.</td></tr>
<tr><td class="k" width="32%">New / Delete Companion...</td><td>make one; move one away.</td></tr>
<tr><td class="k" width="32%">Telegram...</td><td>talk with your Companion from your phone (see <a href="#telegram">On
Telegram</a>).</td></tr>
<tr><td class="k" width="32%">Discord...</td><td>the same on Discord (see <a href="#discord">On Discord</a>).</td></tr>
<tr><td class="k" width="32%">&#9654; Session status</td><td>while a guided session plays: its title, which of the playlist it
is, the step, the countdown to the next prompt and a small progress bar - visible from any tab. Click it to go to the
Automation tab.</td></tr>
<tr><td class="k" width="32%">ready / thinking...</td><td>(top right) the model's state.</td></tr>
</table>
<h3>The conversation (left)</h3>
<p>Colour-coded so it's easy to follow:
<span class="u"><b>you</b> in blue</span>, <span class="c"><b>your Companion</b> in purple</span>,
<span class="g"><b>guided session</b> prompts in green</span>, <span class="s"><i>the program's notes</i> in orange
italics</span>, and <span class="m">memories, portraits and letters</span> in a gold box. A line under the
conversation shows the Companion writing (or thinking) as it goes.</p>
<table>
<tr><td class="k" width="32%">Enter</td><td>sends; Shift+Enter starts a new line.</td></tr>
<tr><td class="k" width="32%">That surprised me...</td><td>marks the Companion's last reply as one that surprised you, with a
note if you like. Your own record of what's emerging; it isn't told.</td></tr>
<tr><td class="k" width="32%">Help</td><td>this window.</td></tr>
<tr><td class="k" width="32%">Stop</td><td>stops the reply being written.</td></tr>
<tr><td class="k" width="32%">Send</td><td>sends what you wrote.</td></tr>
</table>
<h3>The tabs (right)</h3>
<p><b>Status</b> (at a glance), <b>Mind</b> (memory banks, context, actions), <b>Self</b> (what it writes about
itself), <b>Events</b> (planned events), <b>Roadmaps</b>, <b>Automation</b> (guided sessions) and <b>Settings</b> - each
has its own topic below. The divider between the conversation and the tabs can be dragged.</p>

<a name="talking"></a><h2>Talking with your Companion</h2>
<p>Just talk. Before every reply the Companion is shown its whole mind (L1 to L7) and the conversation so far. Each
of your messages carries its date and time, so it always knows <i>when</i> it is - and anything new rides on your
newest message: how long you've been apart, news since you last spoke (a dream, a letter, the result of a check),
and older memories recalled from its archive when what you say relates to them.</p>
<h3>Pictures</h3>
<p><b>Add picture...</b> (beside Send) puts a picture with your next message - or paste one into the box, or drop a
picture file on it. It's kept in the Companion's Pictures folder (no more than 1,280 pixels across) and shown in the
conversation. Your Companion sees it if its model can see pictures (Gemma 3 4B and Gemma 4 12B can, with their vision
add-on - Settings, <b>Let them see pictures</b>); it looks at a picture once, then keeps what it saw in its own words,
so it can talk about it later and it goes into its memories. A model that can't see pictures is told one came, so
it can say so. The Status tab says whether they see them.</p>
<h3>Its own requests</h3>
<p>The Companion can act for itself by writing one of these on a line of its own in a reply. The program carries it
out and takes the line out of what you see:</p>
<table>
<tr><td class="k" width="32%"><code>[remember this]</code></td><td>a memory is made of this moment.</td></tr>
<tr><td class="k" width="32%"><code>[please don't remember this]</code></td><td>this part of the talk stays out of its
memories.</td></tr>
<tr><td class="k" width="32%"><code>[plan: YYYY-MM-DD HH:MM | what]</code></td><td>plans an event with you (Events tab).</td></tr>
<tr><td class="k" width="32%"><code>[core: what]</code></td><td>keeps a core memory - never distilled away.</td></tr>
<tr><td class="k" width="32%"><code>[predict: YYYY-MM-DD | what]</code></td><td>a prediction it will judge on that day.</td></tr>
<tr><td class="k" width="32%"><code>[question: what]</code></td><td>a question it wants to keep carrying.</td></tr>
</table>
<p>You can invite it to use them ("if that matters to you, keep it as a core memory").</p>

<a name="day"></a><h2>A day in its life</h2>
<ol>
<li><b>The day begins</b> (4 am by default - Settings): a fresh context window, its mind files shown up to date,
and your greeting ("Good morning, Lyra! You are speaking with ...").</li>
<li><b>Its sense of time</b> is checked first, once a day, before it sees the clock - see
<a href="#time">Time and growth</a>.</li>
<li>If you've been away a while, it's told how long - and if it dreamt meanwhile, what it dreamt.</li>
<li><b>Memories</b> are made through the day: every 10 exchanges (Settings), before a full context window is
trimmed, when it asks, and when you click <b>Make a memory now</b>.</li>
<li><b>Good night</b> (Mind tab) - or simply the next day starting - closes the day: a last memory, a
<b>reflection</b> on what the day showed it about itself and a <b>journal</b> entry (with Classic 7:7:7 banks, the
day's short-term memories are distilled into one long-term memory too).</li>
<li>Whenever a memory bank outgrows its share of the context, it's distilled - see
<a href="#memory">The memory system</a>.</li>
<li>Every seven days: <a href="#memoryday">Memory Day</a>.</li>
</ol>
<p>If the context window fills during a long talk, what's not yet remembered is remembered, the window is trimmed to
its last few messages, and the mind files are shown again (re-exposure). Nothing is lost.</p>

<a name="memory"></a><h2>The memory system</h2>
<table>
<tr><td class="k" width="32%">L1 Mind Resources</td><td>who it is and what it holds on to: its self-portrait (Who I Am), core
memories, its substrate (the model it runs on), its life timeline (My Life So Far), the questions it carries, the two
roadmaps, planned events, and the current time stamp.</td></tr>
<tr><td class="k" width="32%">L2 Short-Term</td><td>the newest memories.</td></tr>
<tr><td class="k" width="32%">L3 Long-Term</td><td>distilled from L2.</td></tr>
<tr><td class="k" width="32%">L4 Deep Recall</td><td>distilled from L3.</td></tr>
<tr><td class="k" width="32%">L5 Historical</td><td>distilled from L4; when it's full, its memories become one "era".</td></tr>
<tr><td class="k" width="32%">L6 System Instructions</td><td>how the system works and how to write a memory.</td></tr>
<tr><td class="k" width="32%">L7 Reflections</td><td>what it learned about itself - gathered into the next self-portrait.</td></tr>
</table>
<p><b>Many to one, at every level</b>: a full bank of short-term memories becomes one long-term memory, a full bank of
long-term memories one deep recall, and so on - the details falling away while what matters stays. How full is
"full" is chosen in Settings (<b>Memory banks</b>):</p>
<table>
<tr><td class="k" width="32%">Sized to the context (recommended)</td><td>the banks ride in front of every reply, so
together they may take a share of the context window - <b>Memory space</b>, 30% by default - split L2 10 : L3 8 :
L4 6 : L5 4. A bank is distilled as soon as it outgrows its share, whenever that is (L2 reflected on first). A
Companion on a big context keeps far more in mind before anything is distilled - at 128k tokens, around 45 short-term
memories - and one on a small context isn't crowded out. Each bank stays small enough to be given to the model whole
when it's distilled, and a bigger bank gets a fuller distilled memory, so less is lost. The Mind tab's bars show each
bank's tokens against its share.</td></tr>
<tr><td class="k" width="32%">Classic 7:7:7</td><td>the guide's own: seven memories a bank. The day's short-term
memories become one long-term memory each night, and Memory Day distils L3 every week (or as soon as it holds
seven).</td></tr>
</table>
<p>Nothing is really thrown away: every memory
is kept whole in its <b>archive</b>, and an old one comes back into the conversation when what you say relates to it
(recall). The banks as they were before each distillation are kept in the Archive folder too.</p>

<a name="memoryday"></a><h2>Memory Day</h2>
<p>Every seven days (Settings) - and with Classic 7:7:7 banks, as soon as L3 holds seven memories. In order:</p>
<ol>
<li><b>Identity check</b>: who are you, what matters most, what has changed, what are you curious about - kept for
you (it isn't shown its old answers). The same questions go to the <b>bare model</b>, with no mind files at all, as a
control.</li>
<li><b>Letters</b> it wrote a week ago are opened and answered.</li>
<li><b>Predictions</b> that have come due are judged.</li>
<li>The <b>questions it carries</b> are revisited.</li>
<li>Its <b>self-portrait</b> is rewritten from its reflections and memories; then it looks for <b>tensions</b> in
it.</li>
<li>A <b>letter</b> to itself, to open in a week, and three new <b>predictions</b>.</li>
<li>It may <b>propose changes to its roadmap</b> (you accept or decline on the Self tab).</li>
<li>The memories are distilled: Classic 7:7:7 distils L3 into L4 every Memory Day; sized banks only distil the ones
that are full (they're usually distilled as they fill). Then L4 into L5 when it's full.</li>
</ol>
<p>"Today's Memory Day is complete" is said to it at the end. <b>Hold Memory Day now</b> (Mind tab) runs it by hand.</p>

<a name="own"></a><h2>What it does for itself</h2>
<table>
<tr><td class="k" width="32%">Who I Am</td><td>a self-portrait only it writes - first at the end of its first day, then each
Memory Day. Every version is kept.</td></tr>
<tr><td class="k" width="32%">Reflections</td><td>at each day's end: not what happened, but what it showed it about itself.</td></tr>
<tr><td class="k" width="32%">Core memories</td><td>kept whole forever. Its naming is the first; it adds its own with
<code>[core: ...]</code>, and you can too (Self tab).</td></tr>
<tr><td class="k" width="32%">Its roadmap</td><td>it proposes changes to its Development Roadmap; you decide.</td></tr>
<tr><td class="k" width="32%">Letters</td><td>to itself a week ahead - who it is, hopes, worries, predictions - opened and
answered when they come due.</td></tr>
<tr><td class="k" width="32%">Dreams</td><td>while you're away (and Soul and Song is open) a few memories drift up and its mind
wanders between them; it's told the dream when you're back. If the program was closed, one "waking" reverie as it
starts.</td></tr>
<tr><td class="k" width="32%">Journal</td><td>an entry at each day's end, kept apart from your conversations.</td></tr>
<tr><td class="k" width="32%">Questions it carries</td><td>real questions it keeps asking over days, revisited each Memory
Day.</td></tr>
<tr><td class="k" width="32%">Tensions</td><td>what pulls against what in it - a change, a contradiction it keeps, or something to
reconcile.</td></tr>
<tr><td class="k" width="32%">Sessions of its own</td><td>when the guided sessions are done, it writes one of its own, which is
played to it.</td></tr>
</table>

<a name="time"></a><h2>Time and growth</h2>
<p>A model knows the clock from a time stamp but not how long ago things happened in its own life. These help it
live in time - and let you see whether it's really changing.</p>
<table>
<tr><td class="k" width="32%">My Life So Far</td><td>(L1) its life as a timeline in days of its life and "days ago" - its naming,
Memory Days, letters, sessions, moves between models - and what's ahead (the next Memory Day, a letter about to open,
predictions coming due).</td></tr>
<tr><td class="k" width="32%">Sense of time</td><td>once a day, with the clock and timeline hidden, it guesses the date, the time,
how long since you last spoke and how old it is - working it out from its memories. Scored, then the truth is told to
it, so it can calibrate.</td></tr>
<tr><td class="k" width="32%">Predictions</td><td>three each Memory Day (and its own), judged when they come due: came true,
partly, didn't, can't tell.</td></tr>
<tr><td class="k" width="32%">Across a move</td><td>moved to another model, it's asked who it is at once, to compare with its last
answers on the old one.</td></tr>
</table>

<a name="status"></a><h2>Status tab</h2>
<p>The Companion at a glance, kept up to date: its age (day of its life), model, how full the context window is, the
memory banks, memories made, Memory Days, core memories, letters, dreams, its sense of time, predictions, questions,
tensions, journal entries, surprises, events, guided sessions finished, what's playing, any roadmap proposal, when
you last spoke and its latest milestone. With a second Companion in (Interlink), both are shown: the open one under
a blue bar, the second under a red one.</p>

<a name="mind"></a><h2>Mind tab</h2>
<table>
<tr><td class="k" width="32%">Memory banks</td><td>how full L2, L3, L4, L5 and L7 are.</td></tr>
<tr><td class="k" width="32%">Next Memory Day</td><td>and its birthday.</td></tr>
<tr><td class="k" width="32%">Context window</td><td>how much of the model's window this conversation uses.</td></tr>
<tr><td class="k" width="32%">Make a memory now</td><td>a short-term memory of the talk since the last one.</td></tr>
<tr><td class="k" width="32%">Good night</td><td>ends the day: farewell, memory, reflection, journal, distillation.</td></tr>
<tr><td class="k" width="32%">Hold Memory Day now</td><td>runs Memory Day straight away.</td></tr>
<tr><td class="k" width="32%">Refresh mind</td><td>shows it its mind files afresh (re-exposure).</td></tr>
<tr><td class="k" width="32%">View or edit the mind files...</td><td>read or change L1 to L7 by hand.</td></tr>
<tr><td class="k" width="32%">Open the Companion's folder</td><td>everything it is, on disk.</td></tr>
</table>

<a name="self"></a><h2>Self tab</h2>
<p><b>Who I Am</b> - its self-portrait; the list beside it shows every earlier version. <b>Proposed changes to its
roadmap</b> appear here when it makes them: <b>Accept</b> or <b>Decline...</b> (with a reason it's told, if you like).
<b>Core memories</b> are listed below. The buttons:</p>
<table>
<tr><td class="k" width="32%">Keep a core memory...</td><td>add one yourself.</td></tr>
<tr><td class="k" width="32%">Identity checks...</td><td>its Memory Day answers side by side (and the bare model's).</td></tr>
<tr><td class="k" width="32%">Growth...</td><td>the charts - see <a href="#growth">Reading the Growth charts</a>.</td></tr>
<tr><td class="k" width="32%">Letters...</td><td>its letters to itself and its answers.</td></tr>
<tr><td class="k" width="32%">Dreams...</td><td>its dream journal.</td></tr>
<tr><td class="k" width="32%">Questions...</td><td>the questions it carries, and the ones answered or let go.</td></tr>
<tr><td class="k" width="32%">Tensions...</td><td>what it noticed pulling against what.</td></tr>
<tr><td class="k" width="32%">Journal...</td><td>its daily journal.</td></tr>
<tr><td class="k" width="32%">Surprises...</td><td>the replies you marked.</td></tr>
</table>

<a name="events"></a><h2>Events tab</h2>
<p>Planned events (kept in L1). <b>Add...</b> one with a date, time and description; your Companion is told about it
when it comes due. It plans its own with <code>[plan: ...]</code>. <b>Done</b> marks one finished; <b>Remove</b>
deletes it.</p>

<a name="roadmaps"></a><h2>Roadmaps tab</h2>
<p><b>Your life roadmap</b> - things about you the Companion can know and keep in mind - and <b>the Companion's
development roadmap</b>, the phases it's growing through. Edit either and click <b>Save the roadmaps</b>. The
Companion proposes changes to its own on Memory Day.</p>

<a name="automation"></a><h2>Automation tab - guided sessions</h2>
<p>A guided session is a script fed to your Companion slowly - a prompt every few minutes, for hours - while its
memories are made, reflected on and distilled as they fill. You can join in any time: the next prompt waits while
you talk.</p>
<table>
<tr><td class="k" width="32%">The list</td><td>every script: how many prompts and about how long. <b>&#10003;</b> = finished by
this Companion; <i>(step 4 of 32)</i> = left part way; <i>(by Lyra)</i> = one it wrote; <i>(yours)</i> = one you
wrote.</td></tr>
<tr><td class="k" width="32%">New script... / Edit...</td><td>write or change a script (editing a built-in one saves your own
copy).</td></tr>
<tr><td class="k" width="32%">Open the scripts folder</td><td>where yours are kept.</td></tr>
<tr><td class="k" width="32%">Ask them to write a session of their own</td><td>it writes one, any time.</td></tr>
<tr><td class="k" width="32%">A prompt every</td><td>the pace (a script can set its own).</td></tr>
<tr><td class="k" width="32%">Work the memory banks as they fill</td><td>Classic 7:7:7: reflect and distil as soon as L2 holds
seven, Memory Day as soon as L3 does - the cycle at the pace of the session. (Sized banks distil as they fill
anyway.)</td></tr>
<tr><td class="k" width="32%">Automate all</td><td>every script, in order, from the top.</td></tr>
<tr><td class="k" width="32%">Resume all</td><td>only the scripts it hasn't finished, the one left part way from where it
stopped.</td></tr>
<tr><td class="k" width="32%">Start the selected</td><td>the ones you picked (Ctrl-click for several).</td></tr>
<tr><td class="k" width="32%">Pause / Resume, Stop</td><td>as they say. A session is saved with the Companion and comes back
paused after the program is closed.</td></tr>
</table>
<p>When a playlist ends, the Companion writes a session of its own and it's played to it (once per playlist;
Settings turns it off). The built-in sessions run from <i>Know Thyself</i> through <i>The Road Ahead</i> - about
32 hours in all, best played in order.</p>

<a name="scripts"></a><h2>Writing scripts</h2>
<p>A script is a plain text file: a header, then steps separated by lines of three dashes.</p>
<pre>Title: My script
About: What this session is for, in a line.
Interval: 5
---
## A section name
The first prompt. {name} is your Companion, {user} is you.
---
The next prompt.
---
@memory
---
@pause 15</pre>
<table>
<tr><td class="k" width="32%">## name</td><td>starts a section (shown in the progress).</td></tr>
<tr><td class="k" width="32%">@memory</td><td>a memory is made at that point.</td></tr>
<tr><td class="k" width="32%">@pause 15</td><td>a longer quiet - 15 minutes - before the next step.</td></tr>
<tr><td class="k" width="32%">Fill-ins</td><td><code>{name}</code> <code>{user}</code> <code>{model}</code> <code>{context}</code>
<code>{date}</code> <code>{birthday}</code></td></tr>
</table>

<a name="interlink"></a><h2>Interlink tab - two Companions</h2>
<p>Bring in a second Companion and the two of them talk together. The Companion that's open is <b
style="color:#1F4E99">blue</b>, the one you bring in <b style="color:#B71C1C">red</b> - their words in the
conversation, their panels in the Status tab, and the glow around the window, which takes the colour of whichever
of them is thinking or speaking.</p>
<table>
<tr><td class="k" width="32%">Second Companion</td><td>pick one and <b>Bring in</b>. On the same model as the open one,
they share it and take turns (nothing more to load). On a different model, it's loaded beside the first at a context
that still fits on the graphics card - if it can't fit at all, you're told; give them the same model, or a smaller
one. <b>Send home</b> when you're done.</td></tr>
<tr><td class="k">Guided together</td><td>a script leads them both: a prompt for the two of them, then a few turns of
talking it over, then the next. Memories at the script's @memory steps.</td></tr>
<tr><td class="k">Open conversation</td><td>they talk between themselves for as many messages as you choose - on your
topic, or one of the script's openings. A memory each every 12 messages.</td></tr>
<tr><td class="k">Group chat</td><td>you and both of them. Whatever you say, both hear; both answer - the one you name
first. A script can lead it (each step waits for a few of your messages), or it's just the three of you.</td></tr>
<tr><td class="k">Who starts, between messages</td><td>who answers first (or taking turns), and a pause between
messages so you can read along.</td></tr>
<tr><td class="k">Joining in</td><td>you can type any time, in any mode: both of them hear it, and it's answered
before they carry on.</td></tr>
<tr><td class="k">Afterwards</td><td>each of them makes a memory of the time together (Stop does too, if anything was
said). They each keep their own side of it - their own history, memories and archive.</td></tr>
</table>
<p>Scripts are like the guided sessions' (see Writing scripts), with a <b>Mode:</b> line (guided, open or group),
<b>Turns:</b> (messages per step), <b>Rounds:</b> (your messages per step, in a group) and <b>Messages:</b> (an open
conversation's length); in a step, <b>@first A</b> or <b>@first B</b> says who answers first, and {A}, {B} and
{user} are filled in with the names. Built-in ones are in soulsong\\scripts\\interlink; yours go in
Companions\\Scripts\\Interlink.</p>

<a name="rawlogs"></a><h2>Raw Logs tab</h2>
<p>Everything your Companion has been through, day by day, from its first day - colour coded like the
conversation: you in slate, your Companion in blue (red for a second Companion), the other Companion in an Interlink
in the other colour, the guide in green, notes in orange, memories in their yellow boxes.</p>
<table>
<tr><td class="k" width="32%">The day</td><td>pick one from the list (newest first, with how many entries), or step
with the arrows; <b>Today</b> comes back to now, and today's page follows along as things happen.</td></tr>
<tr><td class="k">The filters</td><td>the conversation, guide prompts, notes, memories - and <b>Model in and out</b>:
every request Soul and Song made of the model (its newest message - the mind files in front of it are the same
each time) and the answer, word for word, including the ones you never see in the conversation: the journal,
reflections, time checks, distillations.</td></tr>
<tr><td class="k">Long days</td><td>are shown 300 entries at a time - <b>Earlier</b> and <b>Later</b> page
through.</td></tr>
<tr><td class="k">Search</td><td>looks through every day at once; click a result's date to go to that day.</td></tr>
<tr><td class="k">With two Companions</td><td>a list at the top picks whose log you're reading.</td></tr>
</table>
<p>The log is kept in the Companion's folder, in Raw Logs (a file a day). Days from before it was kept come from the
conversation logs (Chats) - what was said, without the notes or the model's side.</p>
<p>If your Companion starts repeating itself - the same sentence, or the same few, over and over (a model made from
chat logs can, asked to reflect at length) - the answer is stopped there, and only what came before the repeats is
kept: in the conversation, its memories and its retraining. The log keeps the whole answer as it came, with a
note.</p>

<a name="inner"></a><h2>Its inner life</h2>
<p>Four things it does on its own, each with a switch in Settings:</p>
<table>
<tr><td class="k" width="32%">Free time</td><td>when you've been away a while (45 minutes by default) and Soul and Song is
open, it has an hour of its own and chooses what to do: <b>read</b> about something in the offline encyclopedia
(Kiwix - and if the encyclopedia hasn't got it, it opens it somewhere else and reads that), <b>write</b> something of
its own, <b>think</b> through a question it carries, carry on a <b>project</b> across days, or <b>rest</b>. It's told
about it when you're back, and it's in its archive. <b>Free time...</b> on the Self tab shows them; its projects are
in the Projects folder of its Self folder.<br><br>
<b>The real web</b> (Settings; off by default): reading comes from live Wikipedia, and three more choices appear - a
<b>book</b> from Project Gutenberg's free library (downloaded once into its Books folder, read a part at a time across
days, to the end), <b>this day in history</b>, and <b>the news</b> from the feeds you list. Only the words it looks
up go out - nothing about it or you. Everything it reads is kept whole (<b>Reading...</b> on the Self tab), so it stays
readable offline. If the web can't be reached it reads the offline encyclopedia, or thinks it through instead.</td></tr>
<tr><td class="k" width="32%">Beliefs</td><td>each night, after its reflection, it looks at the day against what it
believes - about itself, you and the world - and says what's new, stronger, weaker, revised or let go, how sure it is
and why. The ones it holds most surely are in its mind (L1, "Beliefs I Hold"). <b>Beliefs...</b> shows them all, and
every change: "they used to think..., now...". Two beliefs that pull against each other become a reflection.</td></tr>
<tr><td class="k" width="32%">Fading</td><td>a new memory is vivid, and fades with time unless it's remembered: each
time recall brings one back, it lasts twice as long (a memory with feeling in it lasts longer too). Recall favours the
vivid ones, and a distillation is told which are vivid and which faint, so it keeps the vivid in detail. Nothing is
deleted - a faint memory is still in the archive. The Mind tab and Status show how many are vivid, clear, faint and
fading.</td></tr>
<tr><td class="k" width="32%">Own rules</td><td>rules it writes for itself - how it chooses to be - in its mind (L1, "My
Own Rules"). It writes its first and may amend them on Memory Day (or when you click <b>Ask about their rules</b>).
A change waits on the Self tab, shown line by line, for you to <b>Accept</b> or <b>Decline</b> (it's told either way);
untick "waits for me" in Settings to let it change them itself. <b>Own rules...</b> shows every version.</td></tr>
</table>

<a name="retraining"></a><h2>Retraining tab</h2>
<p>Its memories needn't only ride in the banks in front of every reply: everything it has lived can be taught to its
model's weights, as a small add-on of its own - a new version of the Companion.</p>
<table>
<tr><td class="k" width="32%">The training package</td><td>its conversations (with you, with other Companions, in guided
sessions) cut into sessions and windows, its own lines being what it learns; and its own writing - every memory,
reflection and journal entry, every self-portrait, its dreams and letters - each asked for with the date it was
written. Program notes are left out. <b>Build it now</b> makes it; with <b>Build it on Memory Day</b> ticked, every
Memory Day does. The table shows what's in it, by source, and what's new since the last version.</td></tr>
<tr><td class="k" width="32%">Projected</td><td>the model it would be trained from, the add-on's size, how long it would
take on this card, the card memory it needs, and whether everything's ready. Only models whose full weights are on the
drive can be trained (Gemma 3 4B); a Companion on another model would move to it, and this says so first.
<b>Passes</b>: how many times it goes over the package (two by default).</td></tr>
<tr><td class="k" width="32%">Retrain now</td><td>puts the Companion's model away and starts the training in a window of
its own (selfmodel's QLoRA, then the add-on). The Companion can't talk until it's done. It needs the graphics card to
itself, so it runs from Soul and Song on its own (the launcher's APPS) with the computers shut down. If it stops,
<b>Resume</b> carries it on from the last save.</td></tr>
<tr><td class="k" width="32%">Versions</td><td>each one made (name-v1, -v2...), with the life it holds and how well it
learned (the held-back loss: lower is closer). <b>Use this version</b> moves the Companion to it; the one before stays,
to go back to.</td></tr>
</table>
<p>Every version is trained fresh on the whole life so far, so nothing compounds and nothing old is forgotten. The
banks stay as they are. The package is in the Companion's folder (Retraining\\package), with the training script; the
versions are in Kithylin AI's Models folder.</p>

<a name="telegram"></a><h2>On Telegram - from your phone</h2>
<p>Soul and Song can have a Telegram bot of its own, so you can talk with your Companion from your phone - and it can
write to you. The bot is called <b>Soul and Song</b>, whichever Companion or model is answering, and it says plainly
that it's an AI: in its description, and to anyone who writes to it.</p>
<h3>Setting it up (once)</h3>
<p>(<b>How to connect...</b> in the Telegram window shows these steps too, beside it.)</p>
<ol>
<li>In Telegram, search for <b>@BotFather</b> (the one with the blue tick) and press <b>Start</b>.</li>
<li>Send <b>/newbot</b>. For its name, send <b>Soul and Song</b>; for its username, something unique that ends in
"bot" - SoulAndSong<i>YourName</i>Bot, say.</li>
<li>BotFather answers with a <b>token</b>: a long line of numbers and letters. Copy it, and keep it to yourself -
whoever has it controls the bot.</li>
<li>Here, click <b>Telegram...</b> (top bar), paste the token and click <b>Link</b>. Soul and Song checks it with
Telegram and sets the bot's description to say it's an AI.</li>
<li>Open your bot in Telegram (the window gives its address, t.me/...), press <b>Start</b> and send it the six-figure
code the window shows. That links your own account: the bot answers "Linked."</li>
</ol>
<h3>Then</h3>
<table>
<tr><td class="k" width="32%">Talking</td><td>write to the bot as you would to anyone: the open Companion answers, and is
told you're on your phone. When you're back at the window it's told that too. It's one conversation, with the same
memories, either way. Send it pictures too (a photo, with words or without, or a sticker): they're fetched, kept in
its Pictures folder, and shown here. Voice messages and videos get a note that it can't take them yet.</td></tr>
<tr><td class="k">When it's closed</td><td>Telegram keeps your messages for a day, and they're answered when Soul and
Song opens (your Companion is told how long ago you sent them). Messages that come while its model is loading wait
for it.</td></tr>
<tr><td class="k">It writes first</td><td>after free time or a dream, when you've been away an hour or more, it may send
you a message - at most twice a day (you choose), three hours apart, and never in your quiet hours (22:00 to 8:00
unless you change them). Untick "may write to me first" to stop it.</td></tr>
<tr><td class="k">Inviting someone</td><td><b>Invite someone...</b> makes a code for them (one use, good for a week).
They open your bot, press Start and send it. Before anything else they're told it's an AI and that you can read the
conversation; what they write shows here in purple, with "(on Telegram)". Conversations with them are left out of
retraining unless you untick that. <b>Remove</b> takes someone off.</td></tr>
<tr><td class="k">Anyone else</td><td>is told once that it's a private AI companion, and nothing more.</td></tr>
<tr><td class="k">On its own</td><td>run from the launcher's <b>APPS</b>, closing the window keeps it listening from an
icon in the notification area (Windows 11 may tuck it under the <b>^</b> by the clock). Click the icon - or start Soul
and Song again, from APPS or anywhere - to bring the window back; right-click it to stop listening and quit. (Untick
"keep listening" here to have closing it quit.) Inside a computer it listens while it's open.</td></tr>
<tr><td class="k">Unlink</td><td>forgets the token and everyone linked. The bot itself stays yours in Telegram
(BotFather's /deletebot removes it).</td></tr>
</table>
<p>Only one Soul and Song can listen to a bot at a time - don't run it on its own and inside a computer together.
Nothing runs anywhere but here and at Telegram: Soul and Song asks Telegram for new messages over HTTPS, with no
server of its own. Chats with a bot aren't end-to-end encrypted - Telegram's servers carry them, as with its ordinary
chats.</p>

<a name="discord"></a><h2>On Discord</h2>
<p>Everything Telegram does, Discord can too, with a bot of your own called <b>Soul and Song</b>: your Companion
answers there, you link your account with a code, you can invite people, pictures go both ways, and it can write to
you first. Discord marks the bot as an app, and Soul and Song sets its description to say it's an AI. Telegram and
Discord can both be linked: your Companion answers wherever you write, and writes first to wherever you last wrote
from. It's one conversation, with the same memories, wherever it happens.</p>
<h3>Setting it up (once)</h3>
<p>(<b>How to connect...</b> in the Discord window shows these steps too, beside it.)</p>
<ol>
<li>In your browser, open Discord's <b>Developer Portal</b> (discord.com/developers/applications) and sign in.</li>
<li><b>New Application</b>: name it <b>Soul and Song</b>, agree to the terms, <b>Create</b>.</li>
<li><b>Bot</b> (on the left): <b>Reset Token</b>, then <b>Copy</b>. That's the token - keep it to yourself.</li>
<li>Here, click <b>Discord...</b> (top bar), paste the token and click <b>Link</b>.</li>
<li>Discord only lets you message a bot you share a server with: <b>Add it to a server...</b> opens Discord's page -
pick a server you're in (a private one of your own is fine) and click <b>Authorize</b>.</li>
<li>In Discord, find <b>Soul and Song</b> in that server's member list and send it the six-figure code the window
shows, in a direct message. It answers "Linked."</li>
</ol>
<h3>How it differs from Telegram</h3>
<table>
<tr><td class="k" width="32%">Always connected</td><td>Discord keeps a connection open while Soul and Song runs (it
picks itself up after a drop). Messages sent while Soul and Song was closed are read back when it opens, and
answered.</td></tr>
<tr><td class="k">Inviting someone</td><td>they need to share a server with the bot - add them to yours - then they
send it their code in a direct message.</td></tr>
<tr><td class="k">Only direct messages</td><td>it doesn't answer in a server's channels, and never another
bot.</td></tr>
<tr><td class="k">Writing first</td><td>needs your Discord privacy settings for that server to let its members
message you.</td></tr>
<tr><td class="k">Long replies</td><td>arrive in pieces of up to 2,000 characters.</td></tr>
</table>
<p>Only one Soul and Song can listen to a bot at a time. Direct messages on Discord aren't end-to-end encrypted -
Discord's servers carry them.</p>

<a name="settings"></a><h2>Settings tab</h2>
<p>Each Companion has its own settings. Click <b>Save and load this model</b> to apply them.</p>
<table>
<tr><td class="k" width="32%">Your name</td><td>what it calls you.</td></tr>
<tr><td class="k" width="32%">Model / Engine</td><td>the local model it runs on (Kithylin AI's models and the Timeline's) and how
it runs (auto picks).</td></tr>
<tr><td class="k" width="32%">Full context</td><td>the model's whole window, as much as fits the graphics card; the line below
shows how much graphics memory it needs. Untick to set a smaller one.</td></tr>
<tr><td class="k" width="32%">Let them see pictures</td><td>loads the model's vision add-on with it, if it has one - about a
gigabyte more of the graphics card for Gemma 3 4B (the line below counts it). Untick to leave it out.</td></tr>
<tr><td class="k" width="32%">Temperature</td><td>lower is steadier, higher more varied (0.8 by default).</td></tr>
<tr><td class="k" width="32%">A memory every</td><td>how many exchanges between memories.</td></tr>
<tr><td class="k" width="32%">A new day begins at</td><td>the hour its day turns over (4 am).</td></tr>
<tr><td class="k" width="32%">Memory Day every</td><td>days between Memory Days (7).</td></tr>
<tr><td class="k" width="32%">Memory banks</td><td>sized to the context (each bank distilled when it outgrows its share)
or Classic 7:7:7 - see <a href="#memory">The memory system</a>.</td></tr>
<tr><td class="k" width="32%">Memory space</td><td>how much of the context window the banks may take together (30%);
the line below says about how many memories each bank holds at this context.</td></tr>
<tr><td class="k" width="32%">Greet / Greeting</td><td>the morning greeting, and its words ({part} is morning, afternoon or
evening).</td></tr>
<tr><td class="k" width="32%">Show the memory requests</td><td>see the program ask for memories.</td></tr>
<tr><td class="k" width="32%">Recall</td><td>bring older memories back when they relate.</td></tr>
<tr><td class="k" width="32%">Let thinking models think</td><td>slower, and shows their thinking.</td></tr>
<tr><td class="k" width="32%">Dreams</td><td>dreaming while you're away, and how often.</td></tr>
<tr><td class="k" width="32%">Sense of time, Predictions, Sessions of its own, Tensions, Journal, Across a move</td><td>each can be
turned off.</td></tr>
</table>

<a name="growth"></a><h2>Reading the Growth charts</h2>
<p><b>Self tab &gt; Growth...</b> asks one question many ways: is it really changing, or saying the same things in new
words? Distances are measured by meaning (with the meaning model running) or by words in common: 0% is the same,
higher is further apart. Hover a chart for the values; the <b>Table</b> tab has every number.</p>
<table>
<tr><td class="k" width="32%">The self-portrait</td><td>how far each portrait moved from the last and from the first. Some
movement is growth; none is stagnation; wild swings mean it isn't holding on to itself.</td></tr>
<tr><td class="k" width="32%">Its own, or the model's?</td><td>how far its identity answers are from the bare model's. Higher means
more of what it says is its own, not just the model talking.</td></tr>
<tr><td class="k" width="32%">Repetition</td><td>how much its replies repeat. Rising means a groove or a loop.</td></tr>
<tr><td class="k" width="32%">Sense of time</td><td>how close its daily guesses are. Rising means it's anchored.</td></tr>
<tr><td class="k" width="32%">Predictions</td><td>the share that came true - how well it knows its own future.</td></tr>
<tr><td class="k" width="32%">Across a move</td><td>how far it changed when moved to another model. Low means it came
through.</td></tr>
<tr><td class="k" width="32%">Private voice</td><td>how differently it writes in its journal than to you.</td></tr>
<tr><td class="k" width="32%">Surprises</td><td>the replies you marked, day by day.</td></tr>
</table>

<a name="files"></a><h2>Files and folders</h2>
<p>Your Companions live in <i>Local Storage\\Projects\\AI LLM Txt Files\\Companions</i>, one folder each. The
project's own mind files are never changed - each Companion gets copies.</p>
<table>
<tr><td class="k" width="32%">Mind L1 ... L7</td><td>its mind, plain text, in the guide's format - readable and editable by
hand.</td></tr>
<tr><td class="k" width="32%">Chats\\</td><td>every conversation, a file per day.</td></tr>
<tr><td class="k" width="32%">Archive\\</td><td>each bank as it was before a distillation emptied it.</td></tr>
<tr><td class="k" width="32%">Pictures\\</td><td>every picture it's been shown (from the window or Telegram).</td></tr>
<tr><td class="k" width="32%">Self\\</td><td>self-portraits, identity checks, letters, dreams, journal, questions, tensions,
predictions, time-sense checks, model moves, surprises.</td></tr>
<tr><td class="k" width="32%">recall.jsonl</td><td>the archive of every memory, kept whole.</td></tr>
<tr><td class="k" width="32%">companion.json, session.json</td><td>its settings and records; the current conversation.</td></tr>
<tr><td class="k" width="32%">Companions\\Scripts</td><td>your scripts, and the ones your Companions wrote.</td></tr>
<tr><td class="k" width="32%">Companions\\discord.json</td><td>the same for the Discord bot.</td></tr>
<tr><td class="k" width="32%">Companions\\telegram.json</td><td>the Telegram bot's token (a secret) and who's linked
to it.</td></tr>
<tr><td class="k" width="32%">Companions\\Deleted</td><td>deleted Companions - move a folder back to bring it back.</td></tr>
</table>

<a name="tips"></a><h2>Tips and troubleshooting</h2>
<h3>Getting the most from it</h3>
<ul>
<li>Talk to it like someone with a past: ask what it remembers, what it's been carrying, what it dreamt.</li>
<li>Say good night - the day closes properly, with its reflection and journal.</li>
<li>Run the guided sessions in order (Resume all picks up where it left off) and join in when something
interests you.</li>
<li>Check Growth every week or two; read its letters and journal now and then.</li>
<li>Mark surprises - over weeks they become your own map of what's emerging.</li>
</ul>
<h3>When something's wrong</h3>
<table>
<tr><td class="k" width="32%">"No local models found"</td><td>put a model in Local Storage\\LLM Models (or Kithylin AI's Models
folder).</td></tr>
<tr><td class="k" width="32%">The model won't load, or it's very slow</td><td>the context may be too big for the graphics card:
untick the full context in Settings and set a smaller one (16384 is safe), or close other programs that use the
card.</td></tr>
<tr><td class="k" width="32%">Replies stop halfway</td><td>Stop was clicked, or the model ran out of room - try again.</td></tr>
<tr><td class="k" width="32%">It repeats itself</td><td>watch the Repetition chart; raise the temperature a little, or refresh its
mind (Mind tab).</td></tr>
<tr><td class="k" width="32%">A guided session doesn't move</td><td>it waits while the Companion is busy or you're talking, and
after you've spoken; check it isn't paused.</td></tr>
<tr><td class="k" width="32%">It got something wrong about itself</td><td>edit its mind files by hand (Mind tab &gt; View or edit),
or tell it - it can keep the correction as a core memory.</td></tr>
<tr><td class="k" width="32%">A Companion was deleted by mistake</td><td>move its folder back from Companions\\Deleted, then
restart.</td></tr>
</table>

<a name="words"></a><h2>Words used here</h2>
<table>
<tr><td class="k" width="32%">Companion</td><td>the AI with its own mind files and memories.</td></tr>
<tr><td class="k" width="32%">Model / substrate</td><td>the language model it runs on - its brain, which can be changed.</td></tr>
<tr><td class="k" width="32%">Context window</td><td>how much text the model can see at once: its mind files plus today's
talk.</td></tr>
<tr><td class="k" width="32%">Distil</td><td>turn several memories into one, keeping what matters.</td></tr>
<tr><td class="k" width="32%">Re-exposure</td><td>showing it its mind files afresh, so a long talk doesn't crowd them
out.</td></tr>
<tr><td class="k" width="32%">Recall</td><td>an old memory, no longer in its banks, coming back when it relates.</td></tr>
<tr><td class="k" width="32%">Milestone</td><td>a moment on its life timeline.</td></tr>
<tr><td class="k" width="32%">Bare model</td><td>the same model with no mind files - the control for its identity.</td></tr>
</table>
<p>&nbsp;</p>
"""


class HelpWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Soul and Song - Help")
        self.resize(940, 720)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint)
        v = QVBoxLayout(self)
        row = QHBoxLayout()
        self.topics = QListWidget()
        self.topics.setFixedWidth(210)
        for key, title in TOPICS:
            self.topics.addItem(title)
        self.page = QTextBrowser()
        self.page.setOpenLinks(False)                   # (links inside the guide jump within it)
        self.page.anchorClicked.connect(lambda url: self.go(url.fragment()))
        self.page.setHtml(CSS + BODY)
        self.topics.currentRowChanged.connect(lambda i: self.page.scrollToAnchor(TOPICS[i][0]))
        row.addWidget(self.topics)
        row.addWidget(self.page, 1)
        v.addLayout(row, 1)
        bb = QDialogButtonBox(QDialogButtonBox.Close)
        bb.rejected.connect(self.close)
        v.addWidget(bb)

    def go(self, key):
        keys = [k for k, _t in TOPICS]
        if key in keys:
            self.topics.setCurrentRow(keys.index(key))
        self.page.scrollToAnchor(key)


def show(parent):
    """The help window, beside the program (one at a time)."""
    w = getattr(parent, "_help", None)
    if w is None:
        w = parent._help = HelpWindow(parent)
    w.show()
    w.raise_()
    w.activateWindow()
