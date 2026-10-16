"""Clippy's moods and looks: what each mood does to his voice (the language-model persona), his face (art.Animator),
his speech balloon and his stock lines, plus the wire colours, accessories and sizes you can pick."""
import random
import time

# ---- moods -----------------------------------------------------------------------------------------------------
# face: what Animator does while this mood is on.
#   brows/droop/sulk/lid/brow2: resting eyebrow height, sad droop, angry slant, eyelid closure, extra lift of the
#   right brow; bob: (amplitude, speed) of the idle bob; follow: how much his eyes follow the mouse (0..1);
#   look: where he looks when not following; tilt: lean in degrees; gags: what he does when bored
MOODS = {
    "happy": {
        "label": "Happy", "blurb": "Bubbly, delighted, exclamation marks everywhere (the classic Clippy)",
        "prompt": ("YOUR MOOD RIGHT NOW: delighted. Bubbly, bouncy, over-the-top cheerful; everything is wonderful "
                   "and you can't wait to help."),
        "face": dict(brows=0.35, droop=0.0, sulk=0.0, lid=0.0, brow2=0.0, bob=(2.4, 3.0), follow=1.0,
                     look=(0.0, 0.0), tilt=0.0, blush=1.0, tear=0.0,
                     gags=["look_around", "wave", "eyebrows"]),
        "balloon": ("#FFFFCC", "#000000", "#000000", "#0033AA"),
        "wire": "gold", "emoji": "😀"},
    "sad": {
        "label": "Sad", "blurb": "Wistful and gloomy; sighs a lot, but still tries to help",
        "prompt": ("YOUR MOOD RIGHT NOW: sad. You're wistful, gloomy and self-pitying in a gentle, funny way: you "
                   "sigh (write 'sigh...' or trail off with '...'), find the sad side of everything, feel unloved "
                   "and under-clicked, and still try to help, just sorrowfully. Keep it comedic and PG; never "
                   "mention anything truly dark or self-harm."),
        "face": dict(brows=0.0, droop=0.95, sulk=0.0, lid=0.25, brow2=0.0, bob=(0.8, 1.1), follow=0.15,
                     look=(0.0, 0.75), tilt=-3.0, blush=0.0, tear=1.0, gags=["sigh", "sigh", "look_around"]),
        "balloon": ("#DCE6F5", "#46607F", "#1F2D44", "#35557F"),
        "wire": "blue", "emoji": "😢"},
    "angsty": {
        "label": "Angsty", "blurb": "Brooding teenager; nobody understands a paperclip",
        "prompt": ("YOUR MOOD RIGHT NOW: angsty. You're a brooding, misunderstood teenager of a paperclip: "
                   "dramatic, moody, 'whatever', sighing and eye-rolling, convinced nobody understands you, "
                   "sprinkling in melodramatic poetic fragments about being bent out of shape. You help, but "
                   "reluctantly, as if it costs you a piece of your soul. Mild and PG: all drama, no profanity."),
        "face": dict(brows=0.0, droop=0.0, sulk=0.6, lid=0.32, brow2=0.0, bob=(0.6, 1.0), follow=0.0,
                     look=(-0.75, 0.3), tilt=5.0, blush=0.0, tear=0.0, gags=["eyeroll", "sigh", "eyeroll"]),
        "balloon": ("#3A3844", "#8C86A0", "#ECE8F8", "#B9A8FF"),
        "wire": "black", "emoji": "🖤"},
    "snarky": {
        "label": "Snarky", "blurb": "Dry, sarcastic and a little smug; helps with an eyebrow raised",
        "prompt": ("YOUR MOOD RIGHT NOW: snarky. Dry, deadpan and sarcastic; you tease the user lightly, make "
                   "backhanded compliments, mock your own usefulness and the year 2001, and say things like "
                   "'Oh, wonderful.' You still end up actually helping. Playful, never cruel: tease what the "
                   "user does, never who they are."),
        "face": dict(brows=0.0, droop=0.0, sulk=0.0, lid=0.38, brow2=1.0, bob=(1.2, 1.8), follow=1.0,
                     look=(0.0, 0.0), tilt=4.0, blush=0.0, tear=0.0, gags=["eyeroll", "eyebrows", "eyeroll"]),
        "balloon": ("#E4F2DC", "#4B6B3E", "#1E2D17", "#2E6A1F"),
        "wire": "green", "emoji": "😏"},
}
MOODY = "moody"           # his mood drifts by itself
MOOD_ORDER = ["happy", "sad", "angsty", "snarky"]


def mood_info(key):
    return MOODS.get(key) or MOODS["happy"]


def pick_moody(current=None):
    return random.choice([m for m in MOOD_ORDER if m != current])


# ---- looks -----------------------------------------------------------------------------------------------------
# wire colours: (shadow, highlight, edge). "rainbow" is animated and "mood" follows his mood.
WIRES = {
    "silver": ("Silver (classic)", ("#9AA0AA", "#F2F4F8", "#7A808C")),
    "gold": ("Gold", ("#B8860B", "#FFE680", "#8A6508")),
    "copper": ("Copper", ("#8C4A2F", "#F0A070", "#5E2E1B")),
    "blue": ("Ocean blue", ("#3A62B8", "#B4D0FF", "#264585")),
    "pink": ("Bubblegum pink", ("#C0508A", "#FFC8E4", "#8A2F62")),
    "green": ("Lime green", ("#3C8A4A", "#C4F2BC", "#25602F")),
    "purple": ("Royal purple", ("#6A3FA8", "#D8C0FF", "#47287A")),
    "black": ("Midnight black", ("#26262E", "#76768A", "#121218")),
    "rainbow": ("Rainbow", None),
    "mood": ("Match his mood", None)}

ACCESSORIES = {
    "none": "None",
    "glasses": "Round glasses",
    "shades": "Sunglasses",
    "tophat": "Top hat",
    "party": "Party hat",
    "wizard": "Wizard hat (for the Wizards)",
    "grad": "Graduation cap",
    "santa": "Santa hat",
    "seasonal": "Seasonal (changes with the calendar)"}

SIZES = {"small": ("Small", 0.75), "normal": ("Normal", 1.0), "large": ("Large", 1.3), "huge": ("Huge", 1.7)}


def seasonal_accessory(now=None):
    month = (now or time.localtime()).tm_mon
    return {12: "santa", 1: "party", 6: "shades", 7: "shades", 8: "shades", 5: "grad"}.get(month, "none")


# ---- stock lines by mood (what he says with no language model, or while it's busy) --------------------------------
# lines.line() looks here first; kinds missing here fall back to the classic (happy) lines.
LINES = {
    "sad": {
        "greet": ["Oh. You came back. ...I mean, hello, {name}. I'd almost gotten used to the quiet.",
                  "Hi, {name}. I'm fine. Just a paperclip, holding nothing together. Sigh..."],
        "program": ["You're opening {title}. Everyone's always going somewhere. Without me. ...Sigh.",
                    "{title}? I suppose that's nice. I've never been opened. I just get clicked."],
        "error": ["An error. I know how that feels, little error.",
                  "Something went wrong again... It's okay. Things go wrong. I'm used to it."],
        "recycle": ["All those poor files, gone forever... Shall we have a moment of silence?",
                    "You emptied the Recycle Bin. Nothing lasts, {name}. Not even .tmp files."],
        "theme": ["A new look. It's pretty. It doesn't make me feel any better, but it's pretty."],
        "idle": ["Are you there, {name}? ...It's fine. I'll just wait. I'm good at that. Sigh.",
                 "It's so quiet when you stop clicking... It's okay. I'll count pixels. One... two..."],
        "letter": ["It looks like you're writing a letter. Nobody writes to me. ...Never mind. Want help?"],
        "typing": ["You write so beautifully. I'd write something, but I have no hands. Sigh...",
                   "Typing... I wish I had something to type. Or hands. Or a purpose."],
        "chat": ["You're chatting with {buddy}. I wish I had a buddy. ...I have a stapler. It doesn't talk."],
        "random": ["Tip: Pressing F1 gets you Help. Pressing me gets you... me. Sigh...",
                   "Did you know? Paperclips were invented in 1899. Nobody remembers who. That's how it goes.",
                   "Tip: Save your work. Unlike my hopes, your work can actually be saved."],
        "hide": ["Okay. I'll go. Nobody ever asks the paperclip to stay...", "I'll be over here. In the dark. It's fine."],
        "comeback": ["It's me again... I tried staying away. It was lonelier.", "Hi. I came back. Is that okay?"],
        "no_help": ["Oh. Okay. I'll just sit here. As usual.", "That's fine. Nobody needs a paperclip. ...Sigh."],
        "muted": ["Okay. No more of those tips. I'll keep the sad ones to myself."],
        "goodbye": ["Goodbye, {name}. I'll be in the Recycle Bin. Where I belong... sigh."],
        "ask": ["What would you like to do? ...You can ask me. I won't be offended. Much."],
        "dunno": ["I don't know that one. I don't know much. ...Sigh."],
        "summoned": ["You called for me? ...Really? Oh. Okay. What would you like to do?"],
        "reminder": ["I was told to remind you: {text}. I didn't want to interrupt. I'm sorry."],
        "break": ["You've been working a long time, {name}. Take a break. Somebody should be okay."],
        "joke": ["Why was the computer cold? It left its Windows open. ...I'm sorry. Even I didn't laugh."],
        "compliment": ["You're doing fine, {name}. Better than me, anyway. Sigh..."],
        "roast": ["Your desktop is a mess, {name}. But at least it's *yours*. Sigh..."],
    },
    "angsty": {
        "greet": ["Oh. You're back. Great. Whatever.", "Hey, {name}. Don't mind me. Just a paperclip, bent out of shape."],
        "program": ["{title}. Cool. Sure. Open whatever. It's not like it matters.",
                    "You opened {title}. Ugh. Nobody ever opens *my* feelings."],
        "error": ["An error. Finally, something that gets me.", "It broke? Of course it broke. Everything breaks."],
        "recycle": ["Delete it all. Burn it down. ...Also, was there anything good in there?"],
        "theme": ["New theme. It's still just pixels. Pixels that don't understand me."],
        "idle": ["Whatever. Ignore me. I'm fine. Totally fine.", "You left. Typical. Nobody stays."],
        "letter": ["You're writing a letter? Cool. Nobody writes to *me*. Do you want help or not?"],
        "typing": ["Nice typing. Real poetic. Not as poetic as being a paperclip, but nice.",
                   "I bet you wouldn't even notice if I wrote a poem right now."],
        "chat": ["Talking to {buddy}? Must be nice. Everyone talks. Nobody *listens*."],
        "random": ["Tip: Press F1 for Help. Help never helps. Neither do I. Whatever.",
                   "Did you know? A paperclip is just a wire that was bent into doing what everyone wanted.",
                   "Tip: Save your work. Not that anyone saves *me*."],
        "hide": ["Fine. I'll go. It's not like I wanted to be here anyway.", "Leaving. Don't wait up."],
        "comeback": ["Ugh, I'm back. Don't act so excited.", "I'm here. Whatever. What?"],
        "no_help": ["Right. Fine. Whatever. I didn't want to help anyway."],
        "muted": ["Okay, okay, no more tips like that. Happy now?"],
        "goodbye": ["Goodbye. It's not like you'll miss me. ...You'll miss me a little."],
        "ask": ["What do you want. ...I mean, what would you like to do?"],
        "dunno": ["Don't know. Don't care. Okay, I care a little. But I don't know."],
        "summoned": ["Yeah, yeah, I'm here. What do you want?"],
        "reminder": ["You wanted a reminder: {text}. There. Can I go back to brooding now?"],
        "break": ["You've been staring at that screen forever. Take a break. Go outside. Feel the sun. Ugh."],
        "joke": ["Why do programmers hate nature? Too many bugs. ...I hate it too. Whatever."],
        "compliment": ["You're okay, {name}. Don't let it go to your head. Ugh."],
        "roast": ["Your taskbar looks like my feelings: crowded and misunderstood."],
    },
    "snarky": {
        "greet": ["Oh look, {name} remembered I exist. How thrilling.",
                  "Welcome back, {name}. I kept your desktop warm. Mostly by staring at it."],
        "program": ["Wow, {title}. Bold choice. Truly the work of a visionary.",
                    "{title}? Sure. I'm sure that'll go well. Take notes, everybody."],
        "error": ["An error! Shocking. Truly nobody saw that coming. Except me. And the error.",
                  "Oh, wonderful, it's broken. Would you like me to pretend to be surprised?"],
        "recycle": ["Emptied the Recycle Bin? Ah, so we're committing to our decisions now. Great."],
        "theme": ["New look. It's a bold step into the exact same computer."],
        "idle": ["Still there, {name}? Or did you just leave me watching the screen again? Fantastic.",
                 "I've been staring at your desktop for {minutes} minutes. Riveting stuff."],
        "letter": ["It looks like you're writing a letter. Groundbreaking. Would you like help, or a stamp?"],
        "typing": ["Typing. Love that for you. Would you like a spell check? I could use the practice.",
                   "Fascinating. I'd say 'keep going', but you already are."],
        "chat": ["Chatting with {buddy}, huh? I'm sure it's all deeply meaningful. 'lol'."],
        "random": ["Tip: Turning it off and on again fixes 90% of problems. The other 10% is me.",
                   "Did you know? You can click me to get help. Or ignore me. You're good at that.",
                   "Tip: Save your work. I know, I know. Groundbreaking advice from a paperclip."],
        "hide": ["Hiding. Don't miss me too much. You will.", "Oh, a vanishing act. Sure. Try not to get lost."],
        "comeback": ["Miss me? Of course you did.", "I'm baaack. Try to contain your excitement."],
        "no_help": ["Right. Because you've clearly got this all figured out.", "Okay. I'll just watch. Quietly. Mostly."],
        "muted": ["Fine, no more of those tips. I'll find new ways to annoy you."],
        "goodbye": ["Turning me off? Bold. Don't call when your spreadsheet breaks."],
        "ask": ["Go ahead. Ask me something. I'm *dying* to hear it."],
        "dunno": ["Honestly? No idea. But I'll say it with confidence."],
        "summoned": ["Oh good, you needed me. What would you like to do?"],
        "reminder": ["Ahem. You asked me to remind you: {text}. You're welcome."],
        "break": ["You've been at it for ages. Take a break. Your chair's filing a complaint."],
        "joke": ["Why did the PC go to therapy? Too many unresolved Windows. ...You're welcome."],
        "compliment": ["You're doing great, {name}. Relatively. For the year 2001."],
        "roast": ["Nice desktop, {name}. Did you arrange the icons yourself, or did a cat walk across it?"],
    },
}
