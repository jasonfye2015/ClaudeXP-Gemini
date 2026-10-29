"""Telegram and Discord, for the programs that talk through them (Soul and Song, Kithylin AI): a bot of the user's
own on each, answered by the program. telegram.py and discordlink.py do the talking - the bot's token checked and
kept, who may talk (the user by a code, the people they invite by theirs, anyone else told once that it's private),
listening, sending, pictures - and each program gives its own words: what its bot says it is, and to whom.

A program uses a messenger through the same few pieces: Link(folder, words=...) - the bot and who's linked, kept in
the program's own folder - its classify(message), send(chat, text), typing(chat), download(picture), code(...) and
connect(token); and Listener(link, deliver) - start(), stop(), alive(). setup(app, sends) and intro(app, who) are its
How to connect steps and its window's opening words, with the program's name in them."""
