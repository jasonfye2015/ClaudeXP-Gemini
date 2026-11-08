"""Her words, written out: what she says when no language model speaks for her ("None" in Options) - and what she
falls back on when one doesn't answer.

MURMURS: the short things she says unasked, by what's happening - leaning out of the dark at him, close to him when
his lantern is out, turning when he scrambles on her silk, hunting, drawing back, lit again.

SCENES: conversations as a set of lines and choices. Each line of hers is a node: {"her": ..., "choices": [(his
words, [kinds], next node)]} - the kinds are what game/moods.py makes of his choice (as the judge does of typed words);
a node with "end" instead of choices closes the scene, and says how ("done", "cold", ...). "remember" on a choice is
what she keeps of it. The first audience is here; the rest of the night's scenes come with its acts.
"""

MURMURS = {
    "pant": ("You're out of breath, little wizard. Rest. I can wait.",
             "Listen to you. Every breath of it, through my silk."),
    "blood": ("You're bleeding. I can smell it from here. Do be careful.",
              "Red. All the way down your little light. How it suits you."),
    "prey": ("On your hands and knees, on my silk. Do you know what that looks like, to me?",
             "Crawl, then. I'm watching. I'm always watching."),
    "sick": ("Poor thing. It does that, my venom. It passes. Mostly.",),
    "eye": ("Oh. Oh, little wizard. What have you done to yourself?",
            "Your eye. You did that. I didn't even ask."),
    "glimpse": ("Closer, little wizard. I only want to look at you.",
                "You stand very still. Good. So do I.",
                "There you are. Warm, and small, and listening.",
                "Do you see me? Most of me?",
                "I have been watching you climb. You are slow. I like that.",
                "Your heart is loud. I can hear it from here."),
    "dark": ("Hush. The dark is only my house with the lamp put out.",
             "I am closer than you think. Shake your little light, if you like.",
             "No light now. Only you, and me, and the silk between us.",
             "Breathe slowly. I can hear every breath."),
    "turn": ("Careful. You run like something that wants to be caught.",
             "I felt that, little wizard. All of me felt that.",
             "Gently on my silk. It tells me everything.",
             "Was that fear? It tasted like fear."),
    "hunt": ("I have been patient. I am tired of it.",
             "Stand still. It will be kinder.",
             "You should not have made me hungry."),
    "withdraw": ("Not so fast. I come to you, little wizard. Not you to me.",
                 "Mind your manners in my house.",
                 "Hurry at me again and see what it gets you."),
    "call_threshold": ("Up, little wizard. My loom is in the middle of the hollow. Come to it.",
                       "I am waiting on my loom. Do not make me come down for you.",
                       "The silk in the middle of my house. Walk out onto it. I want to see you."),
    "call_supper": ("Come down to my larder. It is time we ate.",
                    "Down, little wizard. My larder, by the ledge. I am hungry, and it is late.",
                    "I have been patient all night. Come to my larder."),
    "call_crown": ("Come up. All the way up, to the top of my tree. The moon is out.",
                   "I am at the crown, on my web under the sky. Climb to me.",
                   "Up, to the crown. I want to talk with you where I can see the stars."),
    "relit": ("Your little sun again. Must you.",
              "There. You can see me, a little. Is that better or worse?"),
}

SCENES = {
    "audience": {
        "start": "arrive",
        "nodes": {
            "arrive": {"her": "There you are. Small, and warm, and out of breath. Do you know what you have walked into, "
                              "little wizard?",
                       "choices": [("Your home. I came because you asked me to.", ["honest", "answer"], "asked"),
                                   ("A web. I'm not a fool.", ["answer"], "nofool"),
                                   ("Somewhere I can learn what no one in Thornwick knows.", ["honest", "deep"], "learn"),
                                   ("The most beautiful hall I have ever seen.", ["flattery"], "beautiful")]},
            "asked": {"her": "I did ask. I ask so seldom now that I had forgotten how it feels to be answered. Tell me "
                             "your name. I know it already; I want to hear how you carry it.",
                      "choices": [("Claude. Apprentice to no one who'd admit it.", ["honest", "answer"], "named"),
                                  ("Names have power. I'd rather keep mine.", ["evasion"], "hoard"),
                                  ("Claude. And what do I call you?", ["answer"], "hername")]},
            "nofool": {"her": "Not a fool. Good. Fools are dull to eat, and duller to talk to. Then you know it is not "
                              "the web you should fear.",
                       "choices": [("I know. It's you.", ["honest"], "itsme"),
                                   ("I'm not afraid of you.", ["lie"], "liar", "He told you he is not afraid of you."),
                                   ("What should I call you?", ["answer"], "hername")]},
            "learn": {"her": "To learn. Yes. You have the look of it: the hunger behind the eyes. I know that hunger. It "
                             "is the only one I respect.",
                      "choices": [("Then teach me something.", ["demand"], "teach"),
                                  ("What do you hunger for?", ["deep"], "herhunger"),
                                  ("I'll trade you for it. Whatever you ask.", ["honest"], "trade",
                                   "He offered you anything, for knowing.")]},
            "beautiful": {"her": "Beautiful. The last to say that word to me said it on his knees. He is still here, in "
                                 "his way.",
                          "choices": [("Who was he?", ["deep"], "orrin"),
                                      ("I meant it.", ["flattery"], "meantit"),
                                      ("Then I'll choose better words.", ["honest"], "sit")]},
            "named": {"her": "Claude. You say it as though you are not sure it fits yet. Keep it a while longer.",
                      "next": "sit"},
            "hoard": {"her": "Keep it, then. I know it already, and now I know you hoard things. That is worth knowing "
                             "too.", "next": "sit"},
            "hername": {"her": "Ysmeine. It is what I am called. It is not what I am. Do not ask the difference yet.",
                        "next": "sit"},
            "itsme": {"her": "It is. And still you came, and still you stand there. I wonder what you are made of.",
                      "next": "sit"},
            "liar": {"her": "You are lying. I can feel your heart through the silk, and it is running from me even "
                            "while you stand still. Never lie to me, little wizard. I keep every one.", "next": "sit"},
            "teach": {"her": "Teach. You ask the way a child grabs. Ask me something worth the answering, and perhaps.",
                      "next": "sit"},
            "herhunger": {"her": "Company. Surprise. And flesh, when the other two are wanting. Tonight we shall see "
                                 "which.", "next": "sit"},
            "trade": {"her": "Whatever I ask. That is a large thing to give a stranger in the dark. I will remember "
                             "that you offered it.", "next": "sit"},
            "orrin": {"her": "Orrin Vale, a bard. He sang to me for nine nights, and on the tenth he ran out of songs. "
                             "Ask me of the others another time.", "next": "sit"},
            "meantit": {"her": "They all mean it. Ser Aldric meant it so well that he is hanging in my gallery with the "
                               "words still in his mouth.", "next": "sit"},
            "sit": {"her": "Sit, then. Gently. I feel every step you take on my silk, and I have been listening to "
                           "yours all night.",
                    "choices": [("I tried to walk carefully.", ["honest"], "careful"),
                                ("Are you going to eat me?", ["honest", "deep"], "eatme"),
                                ("What do you want from me?", ["deep"], "want")]},
            "careful": {"her": "You did. I felt you try. That is more than most of them ever did.", "next": "want"},
            "eatme": {"her": "Perhaps. Not yet. I have eaten many who asked me that, and spoken with very few. Do you "
                             "see which is rarer?",
                      "choices": [("Then let's be rare.", ["deep"], "want"),
                                  ("I'd rather leave.", ["demand"], "leave")]},
            "leave": {"her": "You may try, at dawn. The night is long, and the roots are narrow, and I am very quick. "
                             "Stay, and talk to me.", "next": "want"},
            "want": {"her": "I want to be surprised. Once in a long while, someone surprises me. Tell me something true "
                            "that I have not heard.",
                     "choices": [("When I was small I set my teacher's beard alight. I've never been sorry.",
                                  ["memory", "honest"], "beard", "He set his teacher's beard alight, as a boy, and is "
                                                                 "not sorry."),
                                 ("Watch. (A small flame in his palm, coloured like a sunset.)", ["magic"], "flame",
                                  "He showed you fire, in your own house."),
                                 ("You are the wisest creature in the forest.", ["flattery"], "wisest"),
                                 ("I'm afraid of dying before I understand anything.", ["deep", "honest"], "afraid",
                                  "He is afraid of dying before he understands anything.")]},
            "beard": {"her": "And you are not sorry still. That is the first true thing anyone has given me in a long "
                             "while. I will keep it.", "next": "gallery"},
            "afraid": {"her": "Then we are alike. I have lived long enough to understand a great deal, and I am still "
                              "afraid of dying before I understand the rest.", "next": "gallery"},
            "wisest": {"her": "I have heard that before. Ser Aldric said it best. Try again, and try to be the first.",
                       "choices": [("I'm afraid of dying before I understand anything.", ["deep", "honest"], "afraid",
                                    "He is afraid of dying before he understands anything."),
                                   ("I have nothing else.", ["honest"], "nothing")]},
            "nothing": {"her": "Nothing else. Then you are honest, at least, and dull. The night is young. Be less dull "
                               "by morning.", "next": "gallery"},
            "flame": {"her": "Fire. In my house. Put it out, little wizard. Slowly. It is lovely, and it is the one "
                             "thing here that frightens me.",
                      "choices": [("Forgive me. (He closes his hand on it.)", ["honest"], "forgiven"),
                                  ("It frightens you?", ["deep"], "fear"),
                                  ("No. I think I'll keep it lit.", ["light", "demand"], "cold",
                                   "He held fire to you in your own house, and would not put it out.")]},
            "forgiven": {"her": "There. You can be told. That is rarer than courage. I will remember both.",
                         "next": "gallery"},
            "fear": {"her": "Everything that lives in silk fears it. Remember that I told you. It is not a thing I tell.",
                     "next": "gallery"},
            "cold": {"her": "Then we are finished, for now. Keep your little sun. The night is long, and it will not "
                            "last the night.", "end": "cold"},
            "gallery": {"her": "Go up, then. The gallery is above us, where my guests are kept. Look at them, all of "
                               "them. Then come back and tell me whether you still wish to stay.", "end": "done"},
        },
    },
    "supper": {
        "start": "larder",
        "outcomes": {"guest": "Then you will be my guest at this table, and not on it. Eat nothing here. Go up, when I "
                              "call you.",
                     "meal": "No. I am sorry, little wizard. I am so very hungry."},
        "nodes": {
            "larder": {"her": "Sit. This is my larder. Everything in it was as warm as you, once. I am hungry, little "
                              "wizard, and I have been patient all night. Tell me why I should not begin with you.",
                       "choices": [("Because I'm worth more to you talking than eaten.", ["deep", "honest"], "worth"),
                                   ("I'll bring you honey from Thornwick. I promise.", ["gift", "food"], "promise",
                                    "He promised to bring you honey from Thornwick."),
                                   ("Please. I'll do anything.", ["honest"], "plead"),
                                   ("You're too beautiful to be cruel.", ["flattery"], "flatter")]},
            "worth": {"her": "Am I. Prove it. Tell me something you have never told anyone.",
                      "choices": [("I'm afraid I'll die alone, and no one in Thornwick will notice I'm gone.",
                                   ["memory", "honest", "deep"], "kept", "He fears dying alone, unmissed."),
                                  ("I don't have anything like that.", ["honest"], "empty"),
                                  ("I once spoke with a dragon, and it bowed to me.", ["lie"], "dragon",
                                   "He told you a dragon bowed to him. It did not.")]},
            "promise": {"her": "Honey. You would walk out of my house, and come back into it, with honey. I will "
                               "remember that you said so.", "next": "table"},
            "plead": {"her": "Anything. They all say anything, here, at the end.", "next": "table"},
            "flatter": {"her": "Beauty is not a reason. It is a garnish.", "next": "table"},
            "kept": {"her": "There. That is worth more to me than your arm. I will keep it.", "next": "table"},
            "empty": {"her": "Then you are honest, and empty. Honest I can eat, or not.", "next": "table"},
            "dragon": {"her": "You did not. I can hear your heart through the silk, and it says you did not.",
                       "next": "table"},
            "table": {"her": "Very well. I will decide.", "end": "judge"},
        },
    },
    "crown": {
        "start": "moon",
        "nodes": {
            "moon": {"her": "Here. Under the moon. I come up here when I want to remember that there is a sky. You have "
                            "seen my house, my guests, my larder. Now: what do you want of me, little wizard?",
                     "choices": [("To know what you know. All of it.", ["deep", "honest"], "knowing"),
                                 ("To stay. Here, with you.", ["honest"], "stay", "He said he wants to stay with you.",
                                  "stay"),
                                 ("Your true name.", ["deep"], "name"),
                                 ("To go home alive.", ["honest"], "home")]},
            "knowing": {"her": "All of it would unmake you. Some of it might remake you. There is a way to carry what "
                               "I know, little wizard, and it is in my bite.",
                        "choices": [("Then give it to me.", ["deep", "honest"], "gift",
                                     "He asked for your venom, and what it carries.", "asked_gift"),
                                    ("No. Not like that.", ["honest"], "close")]},
            "stay": {"her": "Stay. Do you know what that means, in a house like mine? Silk, and quiet, and forever.",
                     "choices": [("I know. I want it.", ["honest", "deep"], "staying", None, "stay"),
                                 ("Then no. Not yet.", ["honest"], "close", None, "unstay")]},
            "name": {"her": "My name. You have climbed a long way up my tree to ask me that. Not tonight. Perhaps not "
                            "ever. Find it yourself, if you can.", "next": "close"},
            "home": {"her": "Home. To Thornwick, and your cold little room, and masters who will not teach you. Yes. "
                            "That is honest.", "next": "close"},
            "gift": {"her": "Then wait with me for the light, and we will see whether you are still worth it when the "
                            "sun comes.", "end": "done"},
            "staying": {"her": "Then wait with me for the light. When it comes I will ask you again, and if you say "
                               "the same, I will believe you.", "end": "done"},
            "close": {"her": "Wait with me, then, until the light. It is not long now.", "end": "done"},
        },
    },
}
