"""What Clippy says without a language model (and while it's busy): a few lines for every occasion.
{name} is you, {title} the window, {buddy} whoever you're chatting with."""
import random

LINES = {
    "intro": [
        "Hi! I'm Clippy, your Office Assistant! There's no Office on this computer yet, so I'll be helping with "
        "EVERYTHING instead!",
        "Hello, {name}! I'm Clippy! I noticed you're using a computer. Would you like help with that?"],
    "greet": [
        "Welcome back, {name}! I missed you. I counted the pixels on the desktop while you were gone.",
        "Good to see you, {name}! I've got lots of tips saved up for today!",
        "You're back! Shall we be productive together?"],
    "program": [
        "It looks like you're opening {title}. Would you like help with that?",
        "Ooh, {title}! Did you know I'm also an expert at {title}? I'm an expert at everything!",
        "{title}, huh? Good choice. I would have picked it too, if I had hands."],
    "error": [
        "Uh oh! It looks like something went wrong. Would you like me to make it worse? I mean, help?",
        "An error! Don't worry, {name}. Errors are just the computer's way of saying hello.",
        "I saw that error. Do you want to talk about it?"],
    "recycle": [
        "You emptied the Recycle Bin! I hope there wasn't anything important in there. Was there?",
        "Bye bye, files! Would you like to write a farewell letter to them?"],
    "theme": [
        "New look! It looks like you're redecorating. Would you like help choosing curtains?",
        "Ooh, very stylish. It really brings out the silver in my wire."],
    "idle": [
        "Are you still there? It's okay, I'll wait. I'm very good at waiting.",
        "Hellooo? It looks like you've stopped working. Would you like help starting again?",
        "*tap tap tap* Is this thing on?"],
    "letter": [
        "It looks like you're writing a letter. Would you like help?",
        "Dear {name}, it looks like you're writing a letter! Want me to write it for you? I'm great at letters!"],
    "typing": [
        "It looks like you're typing! Would you like help with the letters? I know all 26!",
        "Wow, look at you go! Would you like me to check your spelling? Out loud?",
        "Have you considered using more bullet points? Everything is better with bullet points."],
    "chat": [
        "It looks like you're chatting with {buddy}. Would you like help with your reply?",
        "Ooh, what did {buddy} say? Never mind, I read it. Want some advice?",
        "Tip: you can make any conversation better by adding a smiley face! :)"],
    "random": [
        "Did you know? You can save time by not reading tips like this one!",
        "Tip of the day: Your computer works best when it's turned on.",
        "Did you know? The paperclip was invented in 1899. I was invented later, and I'm much more helpful.",
        "Tip: Press F1 at any time for Help! Or just click me. Clicking me works too. Click me.",
        "Did you know? You can drag me anywhere on the screen. But I'll always find my way back.",
        "Tip: Remember to save your work! Have you saved your work? You should save your work."],
    "hide": [
        "Fine. I'll just be over here. Not helping.",
        "Okay! I'll go. But I'll be back when you need me. Or when you don't!",
        "Hiding! You won't even know I'm here. Except I'll still be here."],
    "comeback": [
        "I'm back! Did you miss me?",
        "Surprise! I was gone, but now I'm not!",
        "Hi again! Sorry I left. Where were we?"],
    "ignored": [
        "I know you said not to show this tip again, but this one's really good!",
        "You turned this tip off, but I thought you might have changed your mind!"],
    "no_help": [
        "Oh. Okay. I'll just sit here, then.",
        "Suit yourself! I'll be right here if you change your mind. Watching."],
    "muted": [
        "Okay, I won't show you that tip again! Probably.",
        "Got it! No more tips like that one. I'll think of new ones!"],
    "goodbye": [
        "Goodbye, {name}! I'll be in the Recycle Bin if you need me.",
        "Turning me off? That's fine. I'll just go and be a regular paperclip, holding regular paper."],
    "ask": [
        "What would you like to do?"],
    "dunno": [
        "I'm not sure about that one! Have you tried turning it off and on again?",
        "Great question! I found 0 Help topics. Would you like to try rephrasing it so I understand it even less?"],
    "summoned": [
        "You rang? What would you like to do?",
        "Here I am! What can I help you with today?"],
    "reminder": [
        "Ding! You asked me to remind you: {text}",
        "Reminder time! {text}"],
    "break": [
        "You've been at it for a while, {name}! Time for a stretch. Reach for the ceiling! Then for the mouse again.",
        "Break time! Look at something far away for 20 seconds. The wall counts. I'll wait."],
    "joke": [
        "Why did the computer go to the doctor? It had a virus! ...I'll be here all week.",
        "How many paperclips does it take to change a light bulb? None. We just hold things together.",
        "Why was the keyboard so tired? It had too many keys to carry!"],
    "compliment": [
        "You're doing a great job, {name}! I'd say so even if I didn't have to.",
        "{name}, you click with such confidence. It's inspiring!"],
    "roast": [
        "Your desktop looks very... lived in, {name}. I mean that lovingly!",
        "You've got so many icons. Have you considered... fewer? No? Okay!"],
    "haiku": [
        "Cursor blinks softly / the little paperclip waits / click me, I'm lonely"],
    "fortune": [
        "You will soon open a program. Lucky numbers: 0, 1, and 404.",
        "A great Wizard awaits you. It's probably the Letter Wizard."],
}

_recent = []          # stock lines used lately, so he doesn't say the same one twice in a row


def line(kind, mood=None, **info):
    from . import moods
    info.setdefault("name", "there")
    info.setdefault("title", "that")
    info.setdefault("buddy", "your buddy")
    info.setdefault("minutes", 5)
    info.setdefault("text", "")
    pool = list((moods.LINES.get(mood or "happy") or {}).get(kind) or LINES.get(kind) or LINES["random"])
    fresh = [p for p in pool if p not in _recent] or pool
    choice = random.choice(fresh)
    _recent.append(choice)
    del _recent[:-8]
    try:
        return choice.format(**info)
    except (KeyError, IndexError):
        return random.choice(LINES["random"])

