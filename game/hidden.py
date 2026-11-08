"""What she hides (phase 4f) - kept out of the README and the plan on purpose: a secret for the player to find.

Her name is not Ysmeine. Before the oak was hollow she was a woman, Ilsabet, who lived in it and cut her name into its
heart; the night it went hollow she wove herself into something that would not die. What she was, she keeps wrapped
in her own crown - the one she will not speak of, wrapped tighter than the rest, with nothing beneath it.

Found across nights (his notes are kept): the word burnt under the crown (Light, up there) can't be read - until he's
seen through her eyes the oak long ago (her venom's last vision), and then he can. What she is comes together from
Maudren's journal, the one in the crown, and that same vision. Knowing both, he can speak it - in her scenes, or typed
to her - and if he does, dawn brings The hidden.

    NAME
    unlock(known)          -> pages his notes now write, from what they already hold: [ids]
    knows(known)           -> can he speak it?
    spoken(text)           -> does what he typed say it?
    SPEAK, ANSWER          the script's line, and hers"""

NAME = "Ilsabet"
PAGES = {
    "true_name": ("Old marks", "The word, read",
                  "The word under the crown. I could not read it - until I had seen through her eyes, and then I could, "
                  "as if I had always known it: " + NAME.upper() + ". The hand that cut it was hers. When she had hands."),
    "what_she_was": ("Her", "What she was",
                     "The one in the crown, wrapped tightest, with nothing beneath it - it is her. What she was: a woman "
                     "who lived in the oak while it was green, and cut her name into its heart, and the night it went "
                     "hollow wove herself into something that would not die. She keeps herself up there, wrapped. She "
                     "will not speak of it."),
}
SPEAK = f"(You say it, softly.) {NAME}."
ANSWER = (f"...{NAME}. No one has said that since the oak was green. You found her - the woman I was, wrapped in my "
          "own crown. Stay with me until the light, little wizard, and I will tell you all of it.")
SAID_TO_MODEL = (f"He has found your true name and what you were, and he speaks it to you, softly: {NAME}. No one has "
                 "said it since the oak was green. It undoes you. Answer him - two or three sentences - and ask him to "
                 "stay until the light, so you can tell him everything")


def unlock(known):
    out = []
    if "mark_crown" in known and "vision_before" in known and "true_name" not in known:
        out.append("true_name")
    if {"unnamed", "journal", "vision_before"} <= set(known) and "what_she_was" not in known:
        out.append("what_she_was")
    return out


def knows(known):
    return "true_name" in known and "what_she_was" in known


def spoken(text):
    return NAME.lower() in (text or "").lower()
