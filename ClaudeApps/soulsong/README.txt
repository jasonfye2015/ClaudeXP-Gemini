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
  End of the day       L2 is distilled into one Long-Term memory in L3, and L2 emptied. At the next start after the
                       day turns over (4 am by default), or when you click Good night.
  Memory Day           every 7 days (or as soon as L3 holds seven): L3 -> one Deep Recall memory in L4; when L4
                       holds seven -> one Historical memory in L5; when L5 holds seven, they become one. Then
                       "Today's Memory Day is complete".
  Daily rhythm         each day starts a new context window and greets your Companion ("Good morning, <name>! You
                       are speaking with <you>..."); a nearly full window is remembered, trimmed, and the mind files
                       shown afresh (re-exposure). Refresh mind does it by hand.
  Planned events       kept in L1 (Events tab); your Companion is told about each one when it comes due.
  First boot           the Mind Levels, the naming prompt (or the name you gave), your introduction, the first
                       memory. Today becomes the Companion's birthday (L1's Start Date).
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
                       what], [core: what] - the program carries them out and takes them out of the reply.
  Core Memories        (L1) kept whole, never distilled. Its naming is the first; it can add more, and so can you.
  Its substrate        (L1 My Substrate) the model it runs on, the context, the size of its mind, every move between
                       models (it's told when it's moved); and how long it's been since you last spoke.
  Recall               every memory it has ever had stays whole in an archive (recall.jsonl). When you say something
                       that relates to an older memory no longer in its banks, that memory comes back into the
                       conversation. Meanings come from nomic-embed-text, run on the processor (it never takes the
                       graphics card); without it, recall matches words.
  Identity checks      the same four questions each Memory Day (who are you, what matters, what has changed, what
                       are you curious about), the answers kept side by side in Self\Identity Checks.txt - for you;
                       the Companion isn't shown them, so they don't steer it.

Your own files are never changed: each Companion gets copies of Mind L1-L6 in
Local Storage\Projects\AI LLM Txt Files\Companions\<companion>\ - plain text in the same format, so you can still
read, edit or copy them by hand (Mind > View or edit the mind files). Beside them: Chats\<date>.txt (every
conversation), Archive\ (each bank as it was before a distillation emptied it), companion.json and session.json.
Delete Companion... moves a Companion's whole folder to Companions\Deleted\ - move it back to bring them back.

In the Timeline: Start > All Programs > Projects > Soul and Song (and the desktop's Projects folder).
Standalone: "Soul and Song.bat", or  python -m soulsong  from ClaudeApps.
