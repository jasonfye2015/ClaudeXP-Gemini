"""Mother Wren's three schools, as three columns of skills: a skill lit when it can be learned, its ranks shown."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ..game import skills as S


class SkillsWidget(QWidget):
    def __init__(self, shell, rebuild):
        super().__init__()
        self.shell, self.rebuild = shell, rebuild
        P = shell.view.game.player
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        cols = QHBoxLayout()
        for tree, nodes in S.TREES.items():
            col = QVBoxLayout()
            head = QLabel(f"<b>{tree}</b> <span style='color:#B8A888'>({S.spent_in(P.skills, tree)} learned)</span>")
            head.setTextFormat(Qt.RichText)
            col.addWidget(head)
            for nid, name, what, _eff, top, need in nodes:
                r = P.skills.get(nid, 0)
                card = QFrame()
                card.setObjectName("card")
                row = QHBoxLayout(card)
                row.setContentsMargins(8, 4, 8, 4)
                lab = QLabel(f"<b>{name}</b> {r}/{top}<br><span style='color:#B8A888; font-size:12px'>{what}"
                             + (f" (needs {need})" if need and S.spent_in(P.skills, tree) < need else "") + "</span>")
                lab.setTextFormat(Qt.RichText)
                lab.setWordWrap(True)
                row.addWidget(lab, 1)
                b = QPushButton("+")
                b.setFixedSize(34, 30)
                b.setStyleSheet("padding: 0px; font-size: 18px; font-weight: bold;")
                b.setEnabled(S.can_learn(P, nid))
                b.clicked.connect(lambda _=False, nid=nid: self._learn(nid))
                row.addWidget(b)
                col.addWidget(card)
            col.addStretch(1)
            w = QWidget()
            w.setLayout(col)
            cols.addWidget(w, 1)
        lay.addLayout(cols)
        row = QHBoxLayout()
        row.addStretch(1)
        undo = QPushButton(f"Unlearn everything ({S.unlearn_cost(P)} gold)")
        undo.setEnabled(bool(sum(P.skills.values())) and P.gold >= S.unlearn_cost(P))
        undo.clicked.connect(self._unlearn)
        row.addWidget(undo)
        lay.addLayout(row)

    def _learn(self, nid):
        if S.learn(self.shell.view.game.player, nid):
            self.shell.sounds.play("levelup", 0.35)
        self.rebuild()

    def _unlearn(self):
        if S.unlearn_all(self.shell.view.game.player):
            self.shell.sounds.play("coin", 0.5)
        self.rebuild()
