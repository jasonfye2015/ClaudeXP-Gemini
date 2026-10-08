"""The Internet games' shared 'Zone' window, like XP's Internet Checkers/Reversi: you must be online,
'Looking for opponents...', then you're matched with one of your buddies who's awake (or a stranger if nobody
is), canned-phrase chat ("Hello", "Nice move", "Good game"...), Beginner/Intermediate/Expert skill, and
'Play again?'. Every finished game goes into the buddy's diary so they remember it (and might IM you)."""
import random

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter
from PySide6.QtWidgets import (QComboBox, QGroupBox, QHBoxLayout, QLabel, QListWidget, QPushButton, QRadioButton,
                               QVBoxLayout, QWidget)
from shiboken6 import isValid

from .. import network, sound
from .common import GameWindow, message, open_game, save_stats, stats

PHRASES = ["Hello", "Hi, how are you?", "Good luck", "Have fun", "Nice move", "Good game", "Thanks",
           "You're welcome", "Oops", "Sorry", "Be right back", "I'm back", "Hurry up!", "Play again?", "Yes", "No",
           "Bye"]
REPLIES = {"Hello": ["Hello", "Hi, how are you?"], "Hi, how are you?": ["Hello", "Have fun"],
           "Good luck": ["Good luck", "Thanks", "Have fun"], "Have fun": ["Have fun", "Thanks"],
           "Nice move": ["Thanks"], "Good game": ["Good game", "Thanks"], "Thanks": ["You're welcome"],
           "Sorry": ["No"], "Oops": [], "Hurry up!": ["Sorry", "Be right back"], "Be right back": [],
           "I'm back": ["Hello"], "Bye": ["Bye"], "Play again?": ["Yes", "Yes", "No"]}
STRANGERS = ["zonemaster88", "CheckMate2k1", "Player_4471", "sk8rboi_99", "GrandmaJoan", "TheProfessor",
             "Kellyxoxo", "DarkKnight77", "QuietStorm", "Pianoman_01"]
SKILLS = ["Beginner", "Intermediate", "Expert"]


class ZoneBoard(QWidget):
    """What each game's board provides. Signals: moved(who, info), where who is 'user' or 'ai'."""
    moved = Signal(str, dict)

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


class ZonePanel(QWidget):
    def __init__(self, win, title, board, colors):
        super().__init__()
        self.win = win
        self.desktop = win.desktop
        self.title = title
        self.key = title.lower().replace(" ", "_")
        self.board = board
        self.colors = colors            # (your piece name, their piece name)
        self.opponent = None            # (name, is_buddy)
        self.games_vs = 0
        self.games_vs_started = False
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
        h = QHBoxLayout(self)
        h.setContentsMargins(6, 6, 6, 6)
        h.addWidget(board, 1)
        side = QVBoxLayout()
        players = QGroupBox("Players")
        pv = QVBoxLayout(players)
        self.you_label = QLabel()
        self.them_label = QLabel()
        for lab in (self.you_label, self.them_label):
            lab.setTextFormat(Qt.RichText)
            pv.addWidget(lab)
        side.addWidget(players)
        self.turn_label = QLabel("")
        f = QFont("Tahoma")
        f.setPixelSize(13)
        f.setBold(True)
        self.turn_label.setFont(f)
        self.turn_label.setWordWrap(True)
        side.addWidget(self.turn_label)
        self.score_label = QLabel("")
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
        self.listener = lambda *_quiet: self._disconnected()
        net = network.get(self.desktop)
        net.disconnect_listeners.append(self.listener)
        self._update_players()

    # ---- matchmaking ------------------------------------------------------------------------------------------
    def find_opponent(self, forfeit=True):
        if self.opponent and forfeit and self.board.result() is None and self.games_vs_started:
            self._remember("left in the middle of our game")
        self.ai_timer.stop()
        self.opponent = None
        self.games_vs = 0
        self.games_vs_started = False
        self.board.locked = True
        self.board.banner = "Looking for opponents..."
        self.board.update()
        self.transcript.clear()
        self._update_players()
        self.turn_label.setText("")
        self.win.status.setText("Connecting to the Zone...")
        QTimer.singleShot(random.randint(2200, 4800), self._matched)

    def _matched(self):
        if not isValid(self):
            return
        if not network.is_connected():
            return self._disconnected()
        self.opponent = pick_opponent()
        self.opp_skill = max(0, min(2, self.skill + random.choice((-1, 0, 0, 1))))
        name = self.opponent[0]
        self.add_line(f"{name} has joined the game.", system=True)
        sound.play("ding")
        self._update_players()
        self.new_game()
        QTimer.singleShot(random.randint(900, 2500), lambda: self.opponent_says(random.choice(
            ["Hello", "Hi, how are you?", "Good luck", "Have fun", None])))

    def new_game(self):
        self.games_vs += 1
        self.games_vs_started = True
        self.board.banner = ""
        self.board.start(self.user_first)
        self._update_players()
        self.win.status.setText(f"Connected to the Zone  —  playing {self.opponent[0]}")
        self._next_turn()

    # ---- turns ----------------------------------------------------------------------------------------------------
    def _next_turn(self):
        if not isValid(self) or self.opponent is None:
            return
        res = self.board.result()
        self.score_label.setText(self.board.score_text())
        if res is not None:
            return self._game_over(res)
        name = self.opponent[0]
        if self.board.turn() == "user":
            self.board.locked = False
            self.turn_label.setText("Your turn")
        else:
            self.board.locked = True
            self.turn_label.setText(f"{name}'s turn")
            self.ai_timer.start(random.randint(700, 2400))
        self.board.update()

    def _ai_turn(self):
        if self.opponent is None or self.board.result() is not None or self.board.turn() != "ai":
            return
        self.board.ai_play(self.opp_skill)

    def _moved(self, who, info):
        if who == "user" and info.get("captured", 0) >= 2 and random.random() < 0.6:
            QTimer.singleShot(1200, lambda: self.opponent_says(random.choice(["Nice move", "Oops"])))
        elif who == "user" and info.get("big") and random.random() < 0.35:
            QTimer.singleShot(1200, lambda: self.opponent_says("Nice move"))
        elif who == "ai" and info.get("captured", 0) >= 2 and random.random() < 0.3:
            QTimer.singleShot(900, lambda: self.opponent_says("Sorry"))
        self._next_turn()

    def _game_over(self, res):
        self.board.locked = True
        name = self.opponent[0]
        score = self.board.score_text()
        text = {"user": "You won!", "ai": f"{name} won.", "draw": "The game is a draw."}[res]
        self.turn_label.setText(text)
        s = stats(self.key)
        s[{"user": "wins", "ai": "losses", "draw": "draws"}[res]] = s.get({"user": "wins", "ai": "losses",
                                                                           "draw": "draws"}[res], 0) + 1
        save_stats(self.key, s)
        outcome = {"user": "they beat me", "ai": "I beat them", "draw": "it was a draw"}[res]
        self._remember(outcome + (f" ({score})" if score else ""))
        QTimer.singleShot(800, lambda: self.opponent_says("Good game"))
        again = random.random() < 0.75

        def ask():
            if not isValid(self):
                return
            message(self.desktop, f"Internet {self.title}", f"{text}\n\nDo you want to play again with {name}?",
                    ("Yes", "No"), lambda b: self._again(b == "Yes", again))
        QTimer.singleShot(1800, ask)

    def _again(self, yes, they_want):
        if not yes:
            self.add_line(f"{self.opponent[0]} has left the game.", system=True)
            self.find_opponent(forfeit=False)
            return
        if not they_want:
            self.opponent_says(random.choice(["No", "Bye"]))
            self.add_line(f"{self.opponent[0]} has left the game.", system=True)
            QTimer.singleShot(1500, lambda: self.find_opponent(forfeit=False))
            return
        self.opponent_says("Yes")
        self.user_first = not self.user_first
        QTimer.singleShot(900, self.new_game)

    def _remember(self, outcome):
        """Write the game into the buddy's diary; sometimes they IM about it afterwards."""
        if not self.opponent or not self.opponent[1]:
            return
        from .. import life
        sim = life.get()
        name = self.opponent[0]
        if sim is None or name not in sim.buddies:
            return
        note = f"Played Internet {self.title} on the Zone against {sim.user}; {outcome}."
        sim.journal.add(name, note, "talk")
        if random.random() < 0.3:
            QTimer.singleShot(random.randint(20000, 60000), lambda: sim.reach_out(
                name, f"the game of Internet {self.title} you just played against them ({outcome})"))

    # ---- chat --------------------------------------------------------------------------------------------------------
    def add_line(self, text, system=False):
        self.transcript.addItem(text)
        item = self.transcript.item(self.transcript.count() - 1)
        if system:
            item.setForeground(QColor("#606060"))
        self.transcript.scrollToBottom()

    def say(self, phrase):
        if self.opponent is None:
            return
        self.add_line(f"You: {phrase}")
        replies = REPLIES.get(phrase, [])
        if replies and random.random() < 0.85:
            QTimer.singleShot(random.randint(1000, 2600), lambda: self.opponent_says(random.choice(replies)))

    def opponent_says(self, phrase):
        if phrase is None or self.opponent is None or not isValid(self):
            return
        if self.chat_on:
            self.add_line(f"{self.opponent[0]}: {phrase}")

    def _chat_toggled(self, on):
        self.chat_on = on
        self.add_line("Chat is now " + ("on." if on else "off. You won't see your opponent's messages."), system=True)

    # ---- odds and ends ---------------------------------------------------------------------------------------------
    def set_skill(self, level):
        self.skill = level
        s = stats("zone")
        s["skill"] = level
        save_stats("zone", s)
        self._update_players()

    def _update_players(self):
        mine, theirs = self.board.colors() or self.colors
        self.you_label.setText(f"<b>You</b> ({SKILLS[self.skill]}) — {mine}")
        if self.opponent is None:
            self.them_label.setText("<i>Waiting for an opponent...</i>")
        else:
            self.them_label.setText(f"<b>{self.opponent[0]}</b> ({SKILLS[self.opp_skill]}) — {theirs}")

    def _disconnected(self):
        if not isValid(self):
            return
        self.ai_timer.stop()
        self.board.locked = True
        self.board.banner = "You have been disconnected from the Zone."
        self.board.update()
        self.opponent = None
        self.win.status.setText("Not connected")

    def stop(self):
        self.ai_timer.stop()
        if self.opponent and self.board.result() is None and getattr(self, "games_vs_started", False):
            self._remember("left in the middle of our game")
        net = network.get(self.desktop)
        if self.listener in net.disconnect_listeners:
            net.disconnect_listeners.remove(self.listener)


def pick_opponent():
    """A buddy who's awake right now (they're 'on the Zone'), else a stranger."""
    from .. import life
    from ..programs.people import available
    sim = life.get()
    if sim is not None:
        awake = [name for name, c in sim.buddies.items() if available(c)]
        if awake and random.random() < 0.85:
            return random.choice(awake), True
    return random.choice(STRANGERS), False


def open_zone_game(desktop, title, make_board, colors, icon, size=(760, 540)):
    """Open Internet <title>: dial up first if needed, then find an opponent."""
    if not network.is_connected():
        def answer(button):
            if button == "Yes":
                network.connect(desktop, then=lambda: open_zone_game(desktop, title, make_board, colors, icon, size))
        message(desktop, f"Internet {title}", f"Internet {title} needs a connection to the Internet.\n\n"
                "Do you want to connect now?", ("Yes", "No"), answer, "question")
        return None

    def make():
        win = GameWindow(desktop, lambda w: ZonePanel(w, title, make_board(), colors))
        panel = win.play
        game = win.menu.addMenu("&Game")
        game.addAction("&Find New Opponent", panel.find_opponent, "F2")
        skill = game.addMenu("&Skill Level")
        from PySide6.QtGui import QAction, QActionGroup
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
