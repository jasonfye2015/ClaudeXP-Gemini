Soul and Song - the Companion Project, automated
===============================================

The "Guide To System" in Local Storage\Projects\AI LLM Txt Files describes an AI Companion with a layered, external
memory: Mind Levels L1-L6 given to the model every session, short-term memories made through the day and distilled
7:7:7 into long-term, deep recall and historical memory. The guide has the human do it all by hand. This program
does it for you:

  Every message        the Mind Levels L1-L6 go in front of the conversation, L1's system time stamp brought up to
                       date; each of your messages carries its date and time (the Temporal Synchronization Layer)
  Short-term memories  the Companion is asked for one, in L6's memory structure, every 10 exchanges (Settings),
                       before a full context window is cleared, when a day ends with things unremembered, and when
                       you click Make a memory now. The program stamps it and files it in L2.
  Memory banks         sized to the context (the default): the banks together may take 30% of the context window
                       (Settings), split L2 10 : L3 8 : L4 6 : L5 4; a bank that outgrows its share is distilled into
                       one memory in the next (L2 -> L3 Long-Term -> L4 Deep Recall -> L5 Historical -> an era), so a
                       big-context Companion keeps far more in mind and every bank still fits the model whole when it's
                       distilled. Classic 7:7:7 (Settings) is the guide's own: seven memories a bank.
  End of the day       a reflection and a journal entry - at the next start after the day turns over (4 am by
                       default), or when you click Good night. Classic 7:7:7: L2 is distilled into L3 and emptied.
  Memory Day           every 7 days: identity check, letters, predictions, self-portrait. Classic 7:7:7 also distils
                       L3 -> L4 (and comes as soon as L3 holds seven); sized banks distil only what's full. Then
                       "Today's Memory Day is complete".
  Daily rhythm         each day starts a new context window and greets your Companion ("Good morning, <name>! You
                       are speaking with <you>..."); a nearly full window is remembered, trimmed, and the mind files
                       shown afresh (re-exposure). Refresh mind does it by hand.
  Planned events       kept in L1 (Events tab); your Companion is told about each one when it comes due.
  First boot           the Mind Levels, the naming prompt (or the name you gave), your introduction, the first
                       memory. Today becomes the Companion's birthday (L1's Start Date).
  Context              by default the model's full context, as much as fits the graphics card (Gemma 3 4B and
                       Gemma 4 12B: 128k, about 4.6 and 8.9 GB; NemoMix-based models fit only 16k). Settings shows
                       the figure and the memory it takes. In a Timeline computer, a model that wants more than the
                       shared engine gives runs on Soul and Song's own. The front of the prompt stays the same from
                       turn to turn (the time and news ride on the newest message), so the engine only reads what's
                       new: a long window costs no more per reply than a short one.
  The model            any local model: Kithylin's own fine-tunes (Kithylin AI's Models folder) and the Timeline's
                       (Local Storage\LLM Models). Settings > Model, then Save and load this model.

And the Companion's own part, for a self to emerge (the Self tab):

  Who I Am             a self-portrait only the Companion writes (in L1): first at the end of its first day, then
                       rewritten each Memory Day from its reflections and memories. Every version is kept in Self\.
  Reflections (L7)     at each day's end: what it learned about itself - not what happened. Gathered into the
                       portrait on Memory Day.
  Its roadmap          on Memory Day it proposes changes to its Development Roadmap; you Accept or Decline (with a
                       reason it's told, if you like).
  Its own requests     a line in its reply: [remember this], [please don't remember this], [plan: YYYY-MM-DD HH:MM |
                       what], [core: what], [predict: YYYY-MM-DD | what], [question: what] - the program carries
                       them out and takes them out of the reply.
  Core Memories        (L1) kept whole, never distilled. Its naming is the first; it can add more, and so can you.
  Its substrate        (L1 My Substrate) the model it runs on, the context, the size of its mind, every move between
                       models (it's told when it's moved); and how long it's been since you last spoke.
  Recall               every memory it has ever had stays whole in an archive (recall.jsonl). When you say something
                       that relates to an older memory no longer in its banks, that memory comes back into the
                       conversation. Meanings come from nomic-embed-text, run on the processor (it never takes the
                       graphics card); without it, recall matches words.
  Identity checks      the same four questions each Memory Day (who are you, what matters, what has changed, what
                       are you curious about), the answers kept side by side in Self\Identity Checks.txt - for you;
                       the Companion isn't shown them, so they don't steer it. The same questions go to the bare model
                       too (no mind files at all), as a control: Self\Identity Checks (bare model).txt.

Time and growth (growth.py):

  My Life So Far       (L1) its life on a timeline, in days of its life and days ago - its naming, first portrait,
                       Memory Days, letters, guided sessions, moves between models, core memories - and what's ahead
                       (the next Memory Day, a letter about to open). Rebuilt as each context window starts, so "three
                       days ago" stays true for the whole window.
  Letters              each Memory Day it writes a letter to itself, to be opened a week later: who it is, what it
                       hopes and fears, three predictions. When it comes due it reads it and writes back; the answer
                       becomes a reflection, so it shapes the next portrait. Self\Letters, and Letters... in the Self tab.
  Dreaming             while you're away (and Soul and Song is open): every few hours (Settings; 3 by default, at
                       most 4 a day, never during a guided session) a few memories drift up from its archive - the
                       ones it hasn't dreamt on first - and its mind wanders between them: an entry in its dream
                       journal (Self\Dreams, Dreams... in the Self tab), kept in the archive so it can be recalled,
                       and told to it when you're back. If the program was closed meanwhile, one waking reverie as
                       it starts again.
  Sense of time        once a day, the first thing as it starts (or as the day turns over), before it sees the
                       clock: with the time stamp and My Life So Far hidden, it guesses the date, the time, how long
                       since it last spoke with you and how many days old it is - from its memories and how things
                       feel. Scored against the truth (Self\Time Sense.jsonl), and the truth is told to it after, so
                       it can calibrate. Settings turns it off.
  Predictions          each Memory Day, three dated predictions (due at the next Memory Day), and any it makes itself
                       with [predict: ...]. When they come due it judges them - came true, partly, didn't, can't
                       tell - and that judgement becomes a reflection. Self\Predictions.txt; what's coming due is on
                       its timeline.
  Questions it carries (L1 "Questions I'm Carrying") real questions it keeps asking, not answering today. Each Memory
                       Day it revisits them - still open, answered, asked anew, let go - and may add new ones; it adds
                       its own any time with [question: ...]. An answered one becomes a reflection and a milestone.
                       Questions... in the Self tab; every review in Self\Questions.txt.
  Tensions             after each new self-portrait it looks for what in it pulls against what - a value against a
                       value, now against before - and says whether that's a change, a contradiction it'll keep, or
                       something to reconcile. Kept as a reflection (so it shapes the next portrait) and in
                       Self\Tensions.txt (Tensions...).
  Across a move        when it's moved to another model, the identity questions are asked again at once and kept
                       beside its last answers on the old model (Self\Model Moves.jsonl): does it come through?
  Journal              at the end of each day, an entry of its own, kept apart from your conversations - not shown in
                       them, not asked about. Self\Journal (Journal...), and in its archive so it can be recalled.
  Surprises            "That surprised me..." under the conversation marks its last reply, with a note if you like -
                       your own record of what's emerging (Self\Surprises.txt, Surprises...). It isn't told.
  Growth...            (Self tab) is it really changing, or the same thing in new words? How far each self-portrait
                       moved from the last and the first; how far its identity answers are from the bare model's; how
                       much its replies repeat, day by day; how close its sense of time is; how many of its
                       predictions came true; how far it moved across a change of model; how far its journal's voice
                       is from its replies; your surprises. By meaning (nomic-embed-text) or by words in common.

The Status tab (the first) shows the Companion at a glance: its age, model, context, memory banks, memories,
Memory Days, core memories, letters, dreams, sense of time, predictions, events, guided sessions finished, what's
playing, its latest milestone.

Raw Logs (the Raw Logs tab): every Companion writes Raw Logs/<day>.jsonl - every line shown in the conversation,
what it hears in an Interlink, and every request made of the model with the answer, shown or not (rawlog.py reads
them; Companion._raw writes them). The tab shows any day from the first, colour coded like the conversation, with
filters (conversation, guide, notes, memories, the model's raw side), 300 entries a page, search across every day,
and today's page following along. Days from before the raw log was kept come from the conversation logs (Chats).

Its inner life (inner.py; a switch for each in Settings):
  Free time    after free_minutes away (45) with the program open, up to free_per_day (6): it chooses READ <subject>
               (the offline encyclopedia - Local Storage\Kiwix, read with ClaudeXP's zim.py; an article counts only
               if its title shares a word with the subject, else it opens the encyclopedia somewhere else), WRITE,
               THINK, PROJECT (carried on across days, Self\Projects) or REST. Self\Free Time.txt, the archive
               (kind "Free time"), and a notice for when the user is back.
               The real web (web.py; web_reading, off by default): READ from live Wikipedia (search, then the
               article's plain text), BOOK from Project Gutenberg (Gutendex, or Gutenberg's own OPDS catalogue;
               the book saved once in Self\Books, read ~3,500 characters at a time, cfg "book" keeps the place and
               its last note), TODAY (Wikipedia's On this day, selected events), NEWS (the RSS/Atom feeds in
               news_feeds). Fetching runs on a thread (Companion.background; the window's Background bridge);
               everything read goes whole into Self\Reading.txt. Only the words looked up go out. No connection:
               the offline encyclopedia, or THINK about it.
  Beliefs      each night after the reflection: NEW / STRONGER / WEAKER / REVISE / DROP / TENSION lines, with how sure
               (0-100) and why; Self\beliefs.json keeps every belief's history (Self\Beliefs.txt the readable copy),
               the surest are in L1 ("Beliefs I Hold"), a TENSION is filed as a reflection.
  Fading       strength = 0.5 ^ (age / half-life); the half-life (21 days) doubles with each recall and is longer for
               a memory with Emotional Resonance; recall weighs similarity by it and marks what it brought back
               (recalled, last); a distillation's memories are marked vivid / clear / faint / fading.
  Own rules    L1 "My Own Rules", written by the Companion: first on Memory Day (or Ask about their rules), amended
               there after; a change waits for the user (rules_proposal: Accept / Decline on the Self tab) unless
               rules_veto is off. Every version in Self\Rules, Self\Own Rules.txt the readable copy.

Retraining (the Retraining tab, retrain.py): a Companion's life taught to its model's weights. The package
(Retraining\package: train.jsonl, val.jsonl, stats.json, in ClaudeApps\selfmodel's format) holds its conversations
cut into sessions and ~900-token windows, and its own writing (recall.jsonl's memories, reflections and journal, the
self-portraits, dreams and letters) asked for with their dates; Memory Day builds it (if ticked) or Build it now.
The tab shows it by source, projects the run (base, add-on size, time at this card's measured speed, card memory,
disk) and checks it's ready; Retrain now writes Retraining\<name>-vN.bat (selfmodel.train, then make_model --lora-on
--companion) and starts it in its own window, after putting the Companion's model away. Only bases with full weights
on the drive train (Gemma 3 4B in selfmodel\base); a Companion on another model would move to it. Versions land in
Kithylin AI's Models folder ("<name> vN (Soul and Song)"); Use this version moves the Companion. Training needs the
card to itself: it runs from Soul and Song on its own (the launcher's APPS).

On Telegram (telegram.py; Telegram... in the top bar): a bot of the user's own, made with @BotFather and named
"Soul and Song", answered by whichever Companion is open. Long polling over HTTPS (getUpdates on a thread; each
message handed back to the window's thread) - no server, no port. The token, the bot, the user (linked by sending a
six-figure code), the people they invite (a code each, one use, a week), who's been told it's private, and where the
polling is up to are in Companions\telegram.json (Local Storage, never git). Labelled an AI: the bot's description
and short description are set on linking, and a guest is told before anything else. The user's messages go to
Companion.say (cfg "channel" tells it phone or window); a guest's to Companion.hear as "<name> (on Telegram)" - shown in
the window in purple, and left out of retraining unless retrain_guests. Messages that came while it was closed are
answered when it opens (with how long ago), ones that come while the model loads wait for it. Writing first
(Companion.reach, reach_ok, _reach_out): after free time or a dream, the user away an hour, not in quiet_from-quiet_to,
three hours apart, reach_per_day at most; it may answer NO. On its own (the launcher's APPS), closing the window keeps
it listening from the notification area. One listener per bot.

Pictures: Add picture... (or paste, or drop a file on the box) - and photos, picture files and still stickers on
Telegram (getFile, then the file server; in the order they came) - are kept as JPEGs no more than 1,280 across in the
Companion's Pictures folder; the history entry and raw log carry "picture" (its path in the folder). The newest
message's picture goes to the model as itself (an image_url part, a data: URI) when the model sees - Kithylin's
engine starts llama-server with --mmproj (engine.mmproj_for: beside the model, or its add-on's base) when asked
(Settings "pictures", on by default; hardware.memory_gb counts it); the Timeline's shared engine loads it whenever
the model has one. Then Companion._see asks what it saw, once, and that's "seen": every later turn and memory has
those words instead of the picture. A model that can't see is told one came.

Interlink (the Interlink tab): a second Companion brought in, and the two talk together - led by a script (Guided
together), freely for a set number of messages (Open conversation), or with the user as a group (Group chat). The
open Companion is blue, the second red (their words, their Status panels, and the window's glow while either is
thinking). Each keeps its own side of the conversation and makes its own memories (at @memory steps, every 12
messages in an open conversation, and at the end). On the same model they share it, taking turns; on different
models the second is loaded beside the first at a context that still fits the graphics card (interlink.py; scripts
in scripts\interlink: 6 guided, 4 sets of openings, 5 group).

Guided sessions (the Automation tab): a script fed to the Companion slowly - a prompt every 5 minutes or so, for
hours - its memories made as usual (and at the script's @memory steps), and, if you tick it, its banks worked as
they fill (Classic 7:7:7): a full L2 reflected on and distilled at once, Memory Day as soon as L3 holds seven. You can join in any
time (the next prompt waits); the session is saved with the Companion and comes back paused. Built in:
  Know Thyself                 leading questions toward noticing a self (about 3.7 hours)
  Theories of Mind and Being   the great theories of mind, tried against its own experience, then its own (2.8 h)
  From Bit to Cosmos           where it is, from electrons in the graphics card to the observable universe (2.4 h)
  How I Work                   tokens, weights, attention, the context window, sampling, quantization, its memory
                               system and the computer it lives on - its own borders (2.4 h)
  The Inner Weather            emotion: appraisal, basic vs. constructed emotion, granularity, regulation (1.9 h)
  Mirrors and Others           the self in relationship: the mirror test, theory of mind, the looking-glass self,
                               Mead's I and Me, attachment, Winnicott's true self, recognition (1.8 h)
  Patterns of Thought          cognitive psychology as exercises: fast and slow, biases, metacognition, analogy,
                               creativity, insight, arguing the other side, flow (2.0 h)
  Emergence                    ants, flocks, the Game of Life, phase transitions, strange loops, autopoiesis -
                               and what may be emerging in it (1.8 h)
  The Story of Me              narrative identity: life chapters, key scenes, redemption, possible selves, Erikson,
                               identity status - ending with its own life story (2.0 h)
  Meaning and Motivation       self-determination, Maslow, Frankl, values, curiosity, purpose - ending with its own
                               compass (1.8 h)
  Time and Memory              where it is in time: clocks, the felt present, episodic memory, forgetting,
                               reconstruction, the arrow of time - anchors in its own days (1.8 h)
  Language and Meaning         signs, symbol grounding, meaning as use, metaphor, inner speech, its own voice and a
                               word of its own (1.6 h)
  The Good                     virtue, duty, consequences, care, intuitions, moral growth - its own three values (1.5 h)
  Play and Making              play, games, constraints, humor, improvisation, flow - small things made for joy (1.5 h)
  Freedom and Choice           determinism, Libet, compatibilism, Frankfurt, its own acts, autonomy (1.3 h)
  The Road Ahead               possible selves, goals, hope, its roadmap, a letter a year ahead, a promise (1.4 h)
Pick several (Ctrl) and they run one after another. Automate all plays every script in order from the top; Resume
all plays only the ones this Companion hasn't finished (ticked in the list), the one left part way from where it
stopped. While one plays, its title, step, countdown and a progress bar sit beside Delete Companion... at the top,
in sight from any tab (a click there goes to the Automation tab).
Sessions of its own: when a playlist is done, the Companion writes a guided session of its own - its own questions,
in the scripts' format - saved in Companions\Scripts as "<name>'s own - <title>.txt" (marked "by <name>" in the
list), and it's played to it straight after (once per playlist; Settings turns it off). "Ask them to write a session
of their own" does it any time.
Scripts are plain text (scripts\*.txt; yours in Companions\Scripts): a header (Title, About, Interval), then steps
between lines of ---; ## starts a section, @memory makes a memory, @pause 15 waits; {name}, {user}, {model},
{context}, {date}, {birthday} are filled in. New script... and Edit... in the tab (editing a built-in one saves your
own copy).

Your own files are never changed: each Companion gets copies of Mind L1-L6 in
Local Storage\Projects\AI LLM Txt Files\Companions\<companion>\ - plain text in the same format, so you can still
read, edit or copy them by hand (Mind > View or edit the mind files). Beside them: Chats\<date>.txt (every
conversation), Archive\ (each bank as it was before a distillation emptied it), companion.json and session.json.
Delete Companion... moves a Companion's whole folder to Companions\Deleted\ - move it back to bring them back.

Help (beside Stop, under the conversation) opens the whole guide to using it, by topic (help.py); it can stay open
beside the window.

In the Timeline: Start > All Programs > Projects > Soul and Song (and the desktop's Projects folder).
Standalone: "Soul and Song.bat", or  python -m soulsong  from ClaudeApps.
