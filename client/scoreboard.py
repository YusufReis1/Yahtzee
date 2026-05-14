from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QFrame, QVBoxLayout,
    QSizePolicy, QScrollArea
)
from PyQt5.QtCore    import Qt, pyqtSignal
from PyQt5.QtGui     import QPainter, QColor, QPen, QFont


class ScoreRowWidget(QWidget):
    clicked = pyqtSignal(int)

    _BG_DEFAULT  = QColor("#1E1E1E")
    _BG_HOVER    = QColor("#3D2A0A")
    _BG_CHOSEN   = QColor(220, 90, 0, 180)
    _BG_STATIC   = QColor("#252525")

    def __init__(self, index: int, name: str, static: bool = False, parent=None):
        super().__init__(parent)
        self.index        = index
        self._name        = name
        self._score_text  = ""
        self._preview_text = ""
        self._chosen      = False
        self._selectable  = False
        self._static      = static
        self._hovering    = False

        self.setFixedHeight(30)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMouseTracking(True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 2, 10, 2)

        bold = QFont()
        bold.setBold(static)

        self.name_label  = QLabel(name)
        self.name_label.setFont(bold)
        self.score_label = QLabel("")
        self.score_label.setFont(bold)
        self.score_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.score_label.setMinimumWidth(40)

        layout.addWidget(self.name_label, 1)
        layout.addWidget(self.score_label)

        self.setAutoFillBackground(False)


    def set_score(self, pts: int):
        self._score_text = str(pts)
        self.score_label.setText(self._score_text)

    def set_preview(self, text: str):
        self._preview_text = text
        self.name_label.setText(text)

    def reset_label(self):
        self._preview_text = ""
        self.name_label.setText(self._name)

    def set_chosen(self, chosen: bool, pts: int | None = None):
        self._chosen    = chosen
        self._selectable = False
        if pts is not None:
            self.set_score(pts)
        self.update()

    def set_selectable(self, selectable: bool):
        self._selectable = selectable
        self.setCursor(Qt.PointingHandCursor if selectable else Qt.ArrowCursor)
        self.update()


    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        if self._chosen:
            bg = self._BG_CHOSEN
            fg = QColor("white")
        elif self._hovering and self._selectable:
            bg = self._BG_HOVER
            fg = QColor("#222222")
        elif self._static:
            bg = self._BG_STATIC
            fg = QColor("#333333")
        else:
            bg = self._BG_DEFAULT
            fg = QColor("#333333")

        p.setPen(Qt.NoPen)
        p.setBrush(bg)
        p.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)

        sep_x = self.width() - self.score_label.width() - 14
        p.setPen(QPen(QColor("#DDDDDD"), 1))
        p.drawLine(sep_x, 4, sep_x, self.height() - 4)

        p.end()
        self.name_label.setStyleSheet(f"color: {'white' if self._chosen else '#E0E0E0'};")
        self.score_label.setStyleSheet(f"color: {'white' if self._chosen else '#E0E0E0'};")
        super().paintEvent(event)


    def enterEvent(self, event):
        self._hovering = True
        self.update()

    def leaveEvent(self, event):
        self._hovering = False
        self.name_label.setText(self._preview_text if self._preview_text else self._name)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._selectable and not self._chosen:
            self.clicked.emit(self.index)



_CATEGORY_NAMES = [
    "Ones", "Twos", "Threes", "Fours", "Fives", "Sixes",
    "Three of a Kind", "Four of a Kind", "Full House",
    "Small Straight", "Large Straight", "Chance", "Yahtzee",
]

_STATIC_NAMES = ["Upper Total", "Upper Bonus", "Yahtzee Bonus", "Grand Total"]


def _make_column(title: str, is_opponent: bool) -> tuple[QWidget, list, list]:
    col = QWidget()
    vbox = QVBoxLayout(col)
    vbox.setSpacing(2)
    vbox.setContentsMargins(0, 0, 0, 0)

    header = QLabel(title)
    header.setAlignment(Qt.AlignCenter)
    font = QFont()
    font.setBold(True)
    font.setPointSize(10)
    header.setFont(font)
    header.setStyleSheet("color: #FF6600;")
    vbox.addWidget(header)

    sep = QFrame()
    sep.setFrameShape(QFrame.HLine)
    sep.setStyleSheet("color: #444444;")
    vbox.addWidget(sep)

    cat_rows = []
    for i, name in enumerate(_CATEGORY_NAMES):
        row = ScoreRowWidget(i, name)
        if is_opponent:
            row.setEnabled(False)
        vbox.addWidget(row)
        cat_rows.append(row)

    sep2 = QFrame()
    sep2.setFrameShape(QFrame.HLine)
    sep2.setStyleSheet("color: #444444;")
    vbox.addWidget(sep2)

    static_rows = []
    for i, name in enumerate(_STATIC_NAMES):
        row = ScoreRowWidget(100 + i, name, static=True)
        vbox.addWidget(row)
        static_rows.append(row)

    vbox.addStretch(1)
    return col, cat_rows, static_rows


class ScoreBoardWidget(QWidget):
    category_selected = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        outer = QHBoxLayout(self)
        outer.setSpacing(16)
        outer.setContentsMargins(8, 8, 8, 8)

        self.setStyleSheet("""
            ScoreBoardWidget {
                background: #1A1A1A;
                border: 1px solid #444444;
                border-radius: 8px;
            }
        """)

        p_col, self.player_rows, self.player_static = _make_column("Your Scores",     False)
        o_col, self.opp_rows,    self.opp_static    = _make_column("Opponent Scores",  True)

        outer.addWidget(p_col)

        div = QFrame()
        div.setFrameShape(QFrame.VLine)
        div.setStyleSheet("color: #444444;")
        outer.addWidget(div)

        outer.addWidget(o_col)

        for row in self.player_rows:
            row.clicked.connect(self.category_selected)

    def set_player_selectable(self, indices: list[int]):
        for i, row in enumerate(self.player_rows):
            row.set_selectable(i in indices)

    def set_player_preview(self, idx: int, text: str):
        self.player_rows[idx].set_preview(text)

    def select_player_category(self, idx: int, pts: int):
        self.player_rows[idx].set_chosen(True, pts)
        self.player_rows[idx].set_selectable(False)

    def update_player_statics(self, upper: int, bonus: int, y_bonus: int, grand: int):
        for row, pts in zip(self.player_static, [upper, bonus, y_bonus, grand]):
            row.set_score(pts)


    def select_opp_category(self, idx: int, pts: int):
        self.opp_rows[idx].set_chosen(True, pts)

    def update_opp_statics(self, upper: int, bonus: int, y_bonus: int, grand: int):
        for row, pts in zip(self.opp_static, [upper, bonus, y_bonus, grand]):
            row.set_score(pts)

    def reset(self):
        for row in self.player_rows + self.opp_rows:
            row.set_chosen(False)
            row.set_selectable(False)
            row.set_score(0)
            row.reset_label()
        for row in self.player_static + self.opp_static:
            row.set_score(0)
