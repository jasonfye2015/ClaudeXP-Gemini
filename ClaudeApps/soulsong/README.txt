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

Your own files are never changed: each Companion gets copies of Mind L1-L6 in
Local Storage\Projects\AI LLM Txt Files\Companions\<companion>\ - plain text in the same format, so you can still
read, edit or copy them by hand (Mind > View or edit the mind files). Beside them: Chats\<date>.txt (every
conversation), Archive\ (each bank as it was before a distillation emptied it), companion.json and session.json.

In the Timeline: Start > All Programs > Projects > Soul and Song (and the desktop's Projects folder).
Standalone: "Soul and Song.bat", or  python -m soulsong  from ClaudeApps.
