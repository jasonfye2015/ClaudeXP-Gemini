"""The Model Details tab: the card for the model picked at the top - what it was trained on (general chatting,
roleplay, adult), from which years and services, how the training went, and snippets of the conversations it
learned from. Kithylin models carry a card.json (selfmodel.card); others show what their info.json says."""
import html
import json

from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLabel, QTextBrowser, QVBoxLayout, QWidget

from .chat import KITHY, MUTED, SYSTEM, USER

MIX_COLOURS = {"general": "#7FB7E6", "roleplay": "#B48CF0", "adult": "#E68CB4"}
WHAT_IT_MEANS = {
    "general": "everyday talk: how the day went, plans, news, catching up",
    "roleplay": "conversations carried in actions as well as words: *hugs*, *wags*, scenes played out together",
    "adult": "longer adult sessions, mostly roleplayed, with structure from both sides",
}


def _e(s):
    return html.escape(str(s))


def _load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


class ModelDetails(QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.model = None
        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        row = QHBoxLayout()
        self.heading = QLabel("")
        self.heading.setObjectName("title")
        row.addWidget(self.heading, 1)
        self.adult_box = QCheckBox("Show the adult snippets")
        self.adult_box.setChecked(bool(settings.values.get("card_adult", False)))
        self.adult_box.toggled.connect(self._adult_toggled)
        row.addWidget(self.adult_box)
        lay.addLayout(row)
        self.view = QTextBrowser()
        self.view.setObjectName("card")
        self.view.setStyleSheet("QTextBrowser#card { background: #16161f; border: 1px solid #33334a; border-radius: 6px; }")
        lay.addWidget(self.view, 1)

    def _adult_toggled(self, on):
        self.settings.set("card_adult", bool(on))
        self.show_model(self.model)

    def show_model(self, model):
        self.model = model
        if model is None:
            self.heading.setText("No model chosen")
            self.view.setHtml(f"<p style='color:{MUTED}'>Pick a model at the top to see its details.</p>")
            return
        self.heading.setText(model.title)
        folder = model.path.parent
        card = _load(folder / "card.json")
        self.adult_box.setVisible(card is not None)
        self.view.setHtml(self._card_html(card) if card else self._info_html(model))

    # ---- a model without a card --------------------------------------------------------------------------------
    def _info_html(self, model):
        info = model.info or {}
        rows = [("File", model.path.name), ("Size", f"{model.path.stat().st_size / 2**30:.2f} GB"),
                ("Where", str(model.path.parent))]
        for key, label in (("source", "Source"), ("licence", "Licence"), ("notes", "Notes")):
            if info.get(key):
                rows.append((label, info[key]))
        body = "".join(f"<tr><td style='color:{MUTED};padding-right:14px'>{_e(a)}</td><td>{_e(b)}</td></tr>" for a, b in rows)
        return (f"<div style=\"font-family:'Segoe UI'; color:{USER}; font-size:10.5pt\">"
                f"<p style='color:{SYSTEM}'><i>This model has no details card: it isn't one of the Kithylin models "
                f"trained on your logs (or it was made before cards existed). It plays Kithylin from the system "
                f"prompt alone.</i></p><table cellspacing='4'>{body}</table></div>")

    # ---- a Kithylin model's card ----------------------------------------------------------------------------------
    def _card_html(self, c):
        d, t, mix = c.get("data", {}), c.get("training", {}), c.get("mix", {})
        out = [f"<div style=\"font-family:'Segoe UI'; color:{USER}; font-size:10.5pt\">"]
        out.append(f"<p style='color:{MUTED}'>Made {_e(c.get('made', ''))} from <b style='color:{USER}'>{_e(c.get('base', ''))}</b>"
                   f", fine-tuned on {_e(c.get('you', 'your'))}'s own chat logs.</p>")
        if c.get("notes"):
            out.append(f"<p style='color:{SYSTEM}'><i>{_e(c['notes'])}</i></p>")

        # what it learned from
        out.append(self._h("What it learned from"))
        bar = "".join(f"<td width='{max(1, round(v['share_tokens']))}%' bgcolor='{MIX_COLOURS.get(k, '#888')}' "
                      f"style='height:18px'></td>" for k, v in mix.items() if v.get("share_tokens"))
        out.append(f"<table width='100%' cellspacing='0' cellpadding='0'><tr>{bar}</tr></table>")
        rows = []
        for k, v in mix.items():
            swatch = f"<span style='color:{MIX_COLOURS.get(k, '#888')}'>■</span>"
            rows.append(f"<tr><td>{swatch} <b>{_e(v['label'])}</b></td>"
                        f"<td align='right' style='padding:0 12px'>{v['share_tokens']}% of the text</td>"
                        f"<td align='right' style='padding:0 12px'>{v['conversations']:,} conversations</td>"
                        f"<td align='right' style='padding:0 12px'>{v['your_turns']:,} of your turns</td>"
                        f"<td style='color:{MUTED}'>{_e(WHAT_IT_MEANS.get(k, ''))}</td></tr>")
        out.append(f"<table cellspacing='3'>{''.join(rows)}</table>")
        years = d.get("by_year", {})
        services = d.get("by_service", {})
        facts = [("Conversations", f"{d.get('conversations', 0):,} (about {d.get('median_tokens', 0)} tokens each, typically)"),
                 ("Your turns", f"{d.get('your_turns', 0):,}"),
                 ("Text", f"{d.get('tokens', 0):,} tokens"),
                 ("Years", ", ".join(f"{y}: {n:,}" for y, n in years.items()) or _e(d.get("years", "all"))),
                 ("Services", ", ".join(f"{s} {n:,}" for s, n in services.items())),
                 ("People", f"{d.get('contacts', 0):,} different contacts"
                            + ("; most: " + ", ".join(f"{n} ({k})" for n, k in d["top_contacts"][:8])
                               if d.get("top_contacts") else " (names hidden)")),
                 ("Group rooms", "included" if d.get("rooms") else "one-to-one chats only")]
        out.append(self._table(facts))

        # how the training went
        if t:
            out.append(self._h("How the training went"))
            share = f" ({100 * t['steps'] / t['of']:.0f}% of the set)" if t.get("of") else ""
            vl = t.get("val_loss") or []
            loss = " → ".join(f"{v}" for _s, v in vl) if vl else "not measured"
            facts = [("Started", t.get("started", "")),
                     ("Trained", f"{t.get('steps', 0)} of {t.get('of', '?')} steps{share}, {t.get('hours', 0)} hours"),
                     ("Speed", f"{t.get('speed_tok_s', '?')} tokens a second, {t.get('gpu_gb', '?')} GB of graphics memory"),
                     ("Held-out loss", f"{loss}  <span style='color:{MUTED}'>(how surprised it is by chats it never "
                                       f"trained on: lower means it sounds more like you)</span>")]
            out.append(self._table(facts, escape=False))

        # snippets
        snips = c.get("snippets", {})
        if snips:
            out.append(self._h("Snippets of what it learned from"))
            out.append(f"<p style='color:{MUTED}'>A few random pieces of the training conversations: "
                       f"<span style='color:{KITHY}'>you in light blue</span>, the other person in white.</p>")
            for k, items in snips.items():
                label = (mix.get(k) or {}).get("label", k)
                if k == "adult" and not self.adult_box.isChecked():
                    out.append(f"<p><b style='color:{MIX_COLOURS.get(k)}'>{_e(label)}</b> <span style='color:{MUTED}'>"
                               f"- hidden (tick \"Show the adult snippets\")</span></p>")
                    continue
                out.append(f"<p><b style='color:{MIX_COLOURS.get(k, USER)}'>{_e(label)}</b></p>")
                for s in items:
                    head = _e(s.get("service", "")) + (f" with {_e(s['contact'])}" if s.get("contact") else "") \
                        + f", {_e(s.get('year', ''))}"
                    lines = "".join(
                        f"<div style='color:{KITHY if who == 'Kithylin' else USER}; margin:1px 0'>"
                        f"<b>{_e(who)}:</b> {_e(text).replace(chr(10), '<br>')}</div>" for who, text in s.get("turns", []))
                    out.append(f"<table width='100%' cellspacing='0' cellpadding='8' style='margin:4px 0 10px 0'>"
                               f"<tr><td bgcolor='#20202e'><div style='color:{MUTED}; font-size:9pt'>{head}</div>"
                               f"{lines}</td></tr></table>")
        out.append("</div>")
        return "".join(out)

    @staticmethod
    def _h(text):
        return f"<h3 style='color:{SYSTEM}; margin-top:14px'>{_e(text)}</h3>"

    @staticmethod
    def _table(rows, escape=True):
        body = "".join(f"<tr><td style='color:{MUTED}; padding-right:14px' valign='top'>{_e(a)}</td>"
                       f"<td>{_e(b) if escape else b}</td></tr>" for a, b in rows)
        return f"<table cellspacing='3'>{body}</table>"
