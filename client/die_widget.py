from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore    import Qt, QRect, QPoint, pyqtSignal
from PyQt5.QtGui     import QPainter, QColor, QPen, QLinearGradient, QBrush


_PIPS = {
    1: [(1, 1)],
    2: [(2, 0), (0, 2)],
    3: [(2, 0), (1, 1), (0, 2)],
    4: [(0, 0), (2, 0), (0, 2), (2, 2)],
    5: [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)],
    6: [(0, 0), (0, 1), (0, 2), (2, 0), (2, 1), (2, 2)],
}


class DieWidget(QWidget):
    clicked = pyqtSignal()

    def __init__(self, size: int = 90, parent=None):
        super().__init__(parent)
        self._size  = size
        self._value = 1
        self._held  = False
        self._enabled_for_hold = False
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)


    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, v: int):
        self._value = max(1, min(6, v))
        self.update()

    @property
    def held(self) -> bool:
        return self._held

    @held.setter
    def held(self, h: bool):
        self._held = h
        self.update()

    def set_hold_enabled(self, enabled: bool):
        self._enabled_for_hold = enabled

    def reset(self):
        self._value = 1
        self._held  = False
        self.update()


    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        s   = self._size
        arc = int(s * 0.22)
        body = QRect(2, 2, s - 8, s - 8)

        p.setPen(Qt.NoPen)
        p.setBrush(QColor(0, 0, 0, 40))
        p.drawRoundedRect(body.translated(4, 4), arc, arc)

        grad = QLinearGradient(0, 0, 0, s)
        grad.setColorAt(0, QColor("#FDFDFD"))
        grad.setColorAt(1, QColor("#D8D8D8"))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor("#B5B5B5"), 1.5))
        p.drawRoundedRect(body, arc, arc)

        if self._held:
            p.setPen(Qt.NoPen)
            p.setBrush(QColor(255, 102, 0, 110))
            p.drawRoundedRect(body, arc, arc)

        cell = (s - 8) // 3
        pip_r = max(4, int(cell * 0.35))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#222222"))
        for col, row in _PIPS.get(self._value, []):
            cx = body.x() + col * cell + cell // 2
            cy = body.y() + row * cell + cell // 2
            p.drawEllipse(QPoint(cx, cy), pip_r, pip_r)

        p.end()


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._enabled_for_hold:
            self.clicked.emit()
