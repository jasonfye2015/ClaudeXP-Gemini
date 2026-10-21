"""The Internet games' shared 'Zone' window, like XP's Internet games: you must be online, 'Looking for
opponents...', then you're matched with buddies who are awake (or strangers if nobody is), canned-phrase chat
("Hello", "Nice move", "Good game"...), Beginner/Intermediate/Expert skill, and 'Play again?'. Every finished game
goes into each buddy's diary so they remember it (and might IM you about it).

Two-player boards (Checkers, Reversi, Backgammon) let the Zone run the turns: it asks the board whose turn it is
and calls ai_play(). Card tables (Hearts, Spades) have SEATS = 3 and SELF_DRIVEN = True: they run their own
turns and emit finished(result) when the game is over."""
import random

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QActionGroup, QColor, QFont
from PySide6.QtWidgets import (QComboBox, QGroupBox, QHBoxLayout, QLabel, QListWidget, QPushButton, QRadioButton,
                               QVBoxLayout, QWidget)
from shiboken6 import isValid

from .. import network, sound
from .common import GameWindow, message, open_game, save_stats, stats

PHRASES = ["Hello", "Hi, how are you?", "Good luck", "Have fun", "Nice move", "Nice play", "Good game", "Thanks",
           "You're welcome", "Oops", "Sorry", "Be right back", "I'm back", "Hurry up!", "Play again?", "Yes", "No",
           "Bye"]
REPLIES = {"Hello": ["Hello", "Hi, how are you?"], "Hi, how are you?": ["Hello", "Have fun"],
           "Good luck": ["Good luck", "Thanks", "Have fun"], "Have fun": ["Have fun", "Thanks"],
           "Nice move": ["Thanks"], "Nice play": ["Thanks"], "Good game": ["Good game", "Thanks"],
           "Thanks": ["You're welcome"], "Sorry": ["No"], "Oops": [], "Hurry up!": ["Sorry", "Be right back"],
           "Be right back": [], "I'm back": ["Hello"], "Bye": ["Bye"], "Play again?": ["Yes", "Yes", "No"]}
STRANGERS = ["zonemaster88", "CheckMate2k1", "Player_4471", "sk8rboi_99", "GrandmaJoan", "TheProfessor",
             "Kellyxoxo", "DarkKnight77", "QuietStorm", "Pianoman_01", "AceOfSpades", "lucky_7", "MsPacFan"]
SKILLS = ["Beginner", "Intermediate", "Expert"]
INVITE_SECONDS = 15 * 60
_invites = {}                       # buddy name -> when the invitation runs out (a friend offered to play, on Discord)
_panels = []                        # the Zone windows that are open


def invite(name):
    """A buddy will be your opponent: the next match-up seats them (and an open Zone game looks again now)."""
    import time
    _invites[name] = time.time() + INVITE_SECONDS
    for panel in list(_panels):
        if isValid(panel) and not (panel.playing and any(o.name == name for o in panel.opponents)):
            panel.find_opponent(forfeit=False)
            break


def _take_invites():
    import time
    now = time.time()
    names = [n for n, until in _invites.items() if until > now]
    _invites.clear()
    return names


class ZoneBoard(QWidget):
    """What a two-player board provides. moved(who, info): who is 'user' or 'ai'."""
    moved = Signal(str, dict)
    SEATS = 1
    SELF_DRIVEN = False

    def __init__(self):
        super().__init__()
        self.locked = True          # no input until it's the user's turn
        self.banner = ""            # 'Looking for opponents...' etc., painted over the board

    def start(self, user_first):
        raise NotImplementedError

    def turn(self):                 # 'user' or 'ai'
        raise NotImplementedError

    def ai_play(self, level):       # 0..2; make the computer's move (emits moved)
        raise NotImplementedError

    def result(self):               # None while playing, else 'user', 'ai' or 'draw'
        raise NotImplementedError

    def score_text(self):
        return ""

    def colors(self):               # (yours, theirs), or None to keep the window's defaults
        return None

    def paint_banner(self, p):
        if not self.banner:
            return
        p.fillRect(self.rect(), QColor(0, 0, 0, 110))
        f = QFont("Tahoma")
        f.setPixelSize(16)
        f.setBold(True)
        p.setFont(f)
        p.setPen(QColor("white"))
        p.drawText(self.rect(), Qt.AlignCenter | Qt.TextWordWrap, self.banner)


class Opponent:
    def __init__(self, name, buddy, skill):
        self.name, self.buddy, self.skill = name, buddy, skill


class ZonePanel(QWidget):
    def __init__(self, win, title, board, colors):
        super().__init__()
        self.win = win
        self.desktop = win.desktop
        self.title = title
        self.key = title.lower().replace(" ", "_")
        self.board = board
        self.colors = colors            # (your piece name, their piece name)
        self.opponents = []
        self.games_vs = 0
        self.playing = False
        self.user_first = random.random() < 0.5
        self.skill = int(stats("zone").get("skill", 1))
        self.chat_on = True
        self.setObjectName("zone")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("QWidget#zone { background: #ECE9D8; } QGroupBox, QLabel, QRadioButton, QListWidget "
                           "{ font-family: Tahoma; font-size: 11px; }")
        self.ai_timer = QTimer(self)
        self.ai_timer.setSingleShot(True)
        self.ai_timer.timeout.connect(self._ai_turn)
        _panels.append(self)
        self.destroyed.connect(lambda *_a, me=self: _panels.remove(me) if me in _panels else None)
        h = QHBoxLayout(self)
        h.setContentsMargins(6, 6, 6, 6)
        h.addWidget(board, 1)
        side = QVBoxLayout()
        players = QGroupBox("Players")
        pv = QVBoxLayout(players)
        self.players_label = QLabel()
        self.players_label.setTextFormat(Qt.RichText)
        self.players_label.setWordWrap(True)
        pv.addWidget(self.players_label)
        side.addWidget(players)
        self.turn_label = QLabel("")
        f = QFont("Tahoma")
        f.setPixelSize(13)
        f.setBold(True)
        self.turn_label.setFont(f)
        self.turn_label.setWordWrap(True)
        side.addWidget(self.turn_label)
        self.score_label = QLabel("")
        self.score_label.setWordWrap(True)
        side.addWidget(self.score_label)
        chat = QGroupBox("Chat")
        cv = QVBoxLayout(chat)
        self.transcript = QListWidget()
        self.transcript.setWordWrap(True)
        cv.addWidget(self.transcript, 1)
        row = QHBoxLayout()
        self.phrase = QComboBox()
        self.phrase.addItems(PHRASES)
        send = QPushButton("Send")
        send.setFixedWidth(50)
        send.clicked.connect(lambda: self.say(self.phrase.currentText()))
        row.addWidget(self.phrase, 1)
        row.addWidget(send)
        cv.addLayout(row)
        toggles = QHBoxLayout()
        on, off = QRadioButton("Chat On"), QRadioButton("Off")
        on.setChecked(True)
        on.toggled.connect(self._chat_toggled)
        toggles.addWidget(on)
        toggles.addWidget(off)
        cv.addLayout(toggles)
        side.addWidget(chat, 1)
        side_w = QWidget()
        side_w.setLayout(side)
        side_w.setFixedWidth(210)
        h.addWidget(side_w)
        board.moved.connect(self._moved)
        if hasattr(board, "finished"):
            board.finished.connect(self._game_over)
        self.listener = lambda *_quiet: self._disconnected()
        network.get(self.desktop).disconnect_listeners.append(self.listener)
        self._update_players()

    @property
    def opponent(self):
        return self.opponents[0] if self.opponents else None

    def names(self):
        names = [o.name for o in self.opponents]
        return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]

    # ---- matchmaking ------------------------------------------------------------------------------------------
    def find_opponent(self, forfeit=True):
        if self.opponents and forfeit and self.playing:
            self._remember(lambda _o: f"{self._user()} left in the middle of our game")
        self.ai_timer.stop()
        self.opponents = []
        self.games_vs = 0
        self.playing = False
        self.board.locked = True
        self.board.banner = "Looking for opponents..."
        self.board.update()
        self.transcript.clear()
        self._update_players()
        self.turn_label.setText("")
        self.score_label.setText("")
        self.win.status.setText("Connecting to the Zone...")
        QTimer.singleShot(random.randint(2200, 4800), self._matched)

    def _matched(self):
        if not isValid(self):
            return
        if not network.is_connected():
            return self._disconnected()
        for name, buddy in pick_opponents(self.board.SEATS):
            self.opponents.append(Opponent(name, buddy, max(0, min(2, self.skill + random.choice((-1, 0, 0, 1))))))
            self.add_line(f"{name} has joined the game.", system=True)
        sound.play("ding")
        if hasattr(self.board, "set_players"):
            self.board.set_players([o.name for o in self.opponents], [o.skill for o in self.opponents])
        self._update_players()
        self.new_game()
        for o in self.opponents:
            QTimer.singleShot(random.randint(900, 3500), lambda o=o: self.opponent_says(random.choice(
                ["Hello", "Hi, how are you?", "Good luck", "Have fun", None]), o))

    def new_game(self):
        if not self.opponents:
            return
        self.games_vs += 1
        self.playing = True
        self.board.banner = ""
        self.board.start(self.user_first)
        self._update_players()
        self.win.status.setText(f"Connected to the Zone  —  playing with {self.names()}")
        self._next_turn()

    # ---- turns ----------------------------------------------------------------------------------------------------
    def _next_turn(self):
        if not isValid(self) or not self.opponents or not self.playing:
            return
        self.score_label.setText(self.board.score_text())
        if self.board.SELF_DRIVEN:
            return
        res = self.board.result()
        if res is not None:
            return self._game_over(res)
        if self.board.turn() == "user":
            self.board.locked = False
            self.turn_label.setText("Your turn")
        else:
            self.board.locked = True
            self.turn_label.setText(f"{self.opponent.name}'s turn")
            self.ai_timer.start(random.randint(700, 2400))
        self.board.update()

    def _ai_turn(self):
        if not self.opponents or self.board.result() is not None or self.board.turn() != "ai":
            return
        self.board.ai_play(self.opponent.skill)

    def _moved(self, who, info):
        """React in chat: who is 'user', 'ai', or (card tables) a seat number 1-3."""
        speaker = self._seat_opponent(who)
        if who == "user" and info.get("captured", 0) >= 2 and random.random() < 0.6:
            QTimer.singleShot(1200, lambda: self.opponent_says(random.choice(["Nice move", "Oops"]), speaker))
        elif who == "user" and info.get("big") and random.random() < 0.35:
            QTimer.singleShot(1200, lambda: self.opponent_says(random.choice(["Nice move", "Nice play"]), speaker))
        elif who != "user" and info.get("captured", 0) >= 2 and random.random() < 0.3:
            QTimer.singleShot(900, lambda: self.opponent_says("Sorry", speaker))
        elif who != "user" and info.get("oops") and random.random() < 0.5:
            QTimer.singleShot(900, lambda: self.opponent_says("Oops", speaker))
        self.score_label.setText(self.board.score_text())
        self._next_turn()

    def _seat_opponent(self, who):
        if isinstance(who, str) and who.isdigit() and 1 <= int(who) <= len(self.opponents):
            return self.opponents[int(who) - 1]
        return None

    def _game_over(self, res):
        if not self.playing:
            return
        self.playing = False
        self.board.locked = True
        score = self.board.score_text()
        default = {"user": "You won!", "ai": f"{self.opponent.name} won.", "draw": "The game is a draw."}[res]
        text = self.board.result_text() if hasattr(self.board, "result_text") else default
        self.turn_label.setText(text)
        self.score_label.setText(score)
        key = {"user": "wins", "ai": "losses", "draw": "draws"}[res]
        s = stats(self.key)
        s[key] = s.get(key, 0) + 1
        save_stats(self.key, s)
        if hasattr(self.board, "outcome_for"):
            self._remember(self.board.outcome_for)
        else:
            outcome = {"user": f"{self._user()} beat me", "ai": f"I beat {self._user()}", "draw": "it was a draw"}[res]
            self._remember(lambda _o: outcome + (f" ({score})" if score else ""))
        for o in self.opponents:
            QTimer.singleShot(random.randint(600, 2000), lambda o=o: self.opponent_says(
                random.choice(["Good game", "Good game", "Thanks", None]), o))
        wants = all(random.random() < 0.8 for _ in self.opponents)

        def ask():
            if not isValid(self):
                return
            message(self.desktop, f"Internet {self.title}", f"{text}\n\nDo you want to play again with "
                    f"{self.names()}?", ("Yes", "No"), lambda b: self._again(b == "Yes", wants))
        QTimer.singleShot(2200, ask)

    def _again(self, yes, they_want):
        if not yes:
            self._everyone_leaves()
            self.find_opponent(forfeit=False)
            return
        if not they_want:
            quitter = random.choice(self.opponents)
            self.opponent_says(random.choice(["No", "Bye"]), quitter)
            self._everyone_leaves([quitter])
            QTimer.singleShot(1500, lambda: self.find_opponent(forfeit=False))
            return
        for o in self.opponents:
            self.opponent_says(random.choice(["Yes", "Yes", None]), o)
        self.user_first = not self.user_first
        QTimer.singleShot(900, self.new_game)

    def _everyone_leaves(self, who=None):
        for o in who or self.opponents:
            self.add_line(f"{o.name} has left the game.", system=True)

    def _user(self):
        from .. import life
        sim = life.get()
        return sim.user if sim is not None else "my buddy"

    def _remember(self, outcome_for):
        """Write the game into each buddy's diary; sometimes one IMs about it afterwards."""
        from .. import life
        sim = life.get()
        if sim is None:
            return
        reached = False
        for o in self.opponents:
            if not o.buddy or o.name not in sim.buddies:
                continue
            others = [p.name for p in self.opponents if p is not o]
            with_whom = sim.user + (f", {', '.join(others)}" if others else "")
            outcome = outcome_for(o)
            sim.journal.add(o.name, f"Played Internet {self.title} on the Zone with {with_whom}; {outcome}.", "talk")
            if not reached and random.random() < 0.3:
                reached = True
                QTimer.singleShot(random.randint(20000, 60000), lambda n=o.name, oc=outcome: sim.reach_out(
                    n, f"the game of Internet {self.title} you just played with them ({oc})"))

    # ---- chat --------------------------------------------------------------------------------------------------------
    def add_line(self, text, system=False):
        self.transcript.addItem(text)
        item = self.transcript.item(self.transcript.count() - 1)
        if system:
            item.setForeground(QColor("#606060"))
        self.transcript.scrollToBottom()

    def say(self, phrase):
        if not self.opponents:
            return
        self.add_line(f"You: {phrase}")
        replies = REPLIES.get(phrase, [])
        if not replies:
            return
        for o in self.opponents:
            if random.random() < (0.85 if len(self.opponents) == 1 else 0.45):
                QTimer.singleShot(random.randint(1000, 3200), lambda o=o: self.opponent_says(random.choice(replies), o))

    def opponent_says(self, phrase, who=None):
        if phrase is None or not self.opponents or not isValid(self):
            return
        who = who or random.choice(self.opponents)
        if self.chat_on and who in self.opponents:
            self.add_line(f"{who.name}: {phrase}")

    def _chat_toggled(self, on):
        self.chat_on = on
        self.add_line("Chat is now " + ("on." if on else "off. You won't see other players' messages."), system=True)

    # ---- odds and ends ---------------------------------------------------------------------------------------------
    def set_skill(self, level):
        self.skill = level
        s = stats("zone")
        s["skill"] = level
        save_stats("zone", s)
        self._update_players()

    def _update_players(self):
        mine, theirs = self.board.colors() or self.colors
        lines = [f"<b>You</b> ({SKILLS[self.skill]})" + (f" — {mine}" if mine else "")]
        if not self.opponents:
            lines.append("<i>Waiting for players...</i>")
        for i, o in enumerate(self.opponents):
            role = theirs[i] if isinstance(theirs, (list, tuple)) else theirs
            lines.append(f"<b>{o.name}</b> ({SKILLS[o.skill]})" + (f" — {role}" if role else ""))
        self.players_label.setText("<br>".join(lines))

    def _disconnected(self):
        if not isValid(self):
            return
        self.ai_timer.stop()
        if hasattr(self.board, "stop"):
            self.board.stop()
        self.board.locked = True
        self.board.banner = "You have been disconnected from the Zone."
        self.board.update()
        self.opponents = []
        self.playing = False
        self.win.status.setText("Not connected")

    def stop(self):
        self.ai_timer.stop()
        if hasattr(self.board, "stop"):
            self.board.stop()
        if self.opponents and self.playing:
            self._remember(lambda _o: f"{self._user()} left in the middle of our game")
        net = network.get(self.desktop)
        if self.listener in net.disconnect_listeners:
            net.disconnect_listeners.remove(self.listener)


def pick_opponents(n):
    """Buddies who are awake right now (they're 'on the Zone'), topped up with strangers."""
    from .. import life
    from ..programs.people import available
    sim = life.get()
    awake = [name for name, c in sim.buddies.items() if available(c)] if sim is not None else []
    random.shuffle(awake)
    out = [(name, True) for name in _take_invites()[:n]]      # a friend who offered on Discord sits down first
    awake = [a for a in awake if a not in (o for o, _b in out)]
    n -= len(out)
    for _ in range(n):
        if awake and random.random() < 0.85:
            out.append((awake.pop(), True))
        else:
            names = [s for s in STRANGERS if s not in (o for o, _b in out)]
            out.append((random.choice(names), False))
    return out


def open_zone_game(desktop, title, make_board, colors, icon, size=(760, 540)):
    """Open Internet <title>: dial up first if needed, then find opponents. make_board(win) builds the board."""
    if not network.is_connected():
        def answer(button):
            if button == "Yes":
                network.connect(desktop, then=lambda: open_zone_game(desktop, title, make_board, colors, icon, size))
        message(desktop, f"Internet {title}", f"Internet {title} needs a connection to the Internet.\n\n"
                "Do you want to connect now?", ("Yes", "No"), answer, "question")
        return None

    def make():
        win = GameWindow(desktop, lambda w: ZonePanel(w, title, make_board(w), colors))
        panel = win.play
        game = win.menu.addMenu("&Game")
        game.addAction("&Find New Opponent" if panel.board.SEATS == 1 else "&Find New Players",
                       panel.find_opponent, "F2")
        skill = game.addMenu("&Skill Level")
        group = QActionGroup(win)
        for i, name in enumerate(SKILLS):
            act = QAction(name, win, checkable=True, checked=i == panel.skill)
            act.triggered.connect(lambda _c=False, i=i: panel.set_skill(i))
            group.addAction(act)
            skill.addAction(act)
        game.addSeparator()
        game.addAction("&Statistics", lambda: message(desktop, f"Internet {title}", _stats_text(panel.key)))
        game.addSeparator()
        game.addAction("E&xit", lambda: win.frame.request_close())
        win.menu.addMenu("&Help").addAction("&How to Play", lambda: message(
            desktop, f"Internet {title}", getattr(panel.board, "HOW_TO", "")))
        QTimer.singleShot(300, panel.find_opponent)
        return win

    return open_game(desktop, "zone_" + title.lower(), f"Internet {title}", make, icon, size)


def _stats_text(key):
    s = stats(key)
    return f"Wins: {s.get('wins', 0)}\nLosses: {s.get('losses', 0)}\nDraws: {s.get('draws', 0)}"
