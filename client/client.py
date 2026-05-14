import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QStackedWidget,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QMessageBox, QFrame, QSizePolicy
)
from PyQt5.QtCore    import Qt, QTimer, pyqtSlot, QObject
from PyQt5.QtGui     import QFont, QColor, QPalette, QLinearGradient, QPainter, QBrush

from die_widget  import DieWidget
from scoreboard  import ScoreBoardWidget
from model       import Game
from network     import NetworkClient

SERVER_PORT = 5000

class LobbyScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dots = 0
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._animate_dots)

        outer = QVBoxLayout(self)
        outer.setAlignment(Qt.AlignCenter)

        card = QFrame(self)
        card.setObjectName("Card")
        card.setFixedWidth(380)
        card.setStyleSheet("""
            QFrame#Card {
                background: rgba(35,35,35,245);
                border: 1px solid #555555;
                border-radius: 18px;
            }
        """)

        vbox = QVBoxLayout(card)
        vbox.setSpacing(14)
        vbox.setContentsMargins(50, 36, 50, 44)

        title = QLabel("YAHTZEE")
        title.setAlignment(Qt.AlignCenter)
        f = QFont("Georgia", 28, QFont.Bold)
        title.setFont(f)
        title.setStyleSheet("color: #FF6600; letter-spacing: 4px;")
        vbox.addWidget(title)

        subtitle = QLabel("Multiplayer Network Edition")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #AAAAAA; font-size: 11px;")
        vbox.addWidget(subtitle)

        vbox.addSpacing(10)

        vbox.addWidget(self._label("Server IP:"))
        self.ip_field = self._text_field("localhost")
        vbox.addWidget(self.ip_field)

        vbox.addWidget(self._label("Nickname:"))
        self.nick_field = self._text_field("Player")
        vbox.addWidget(self.nick_field)

        vbox.addSpacing(6)

        self.find_btn = QPushButton("Find Game")
        self.find_btn.setFixedHeight(44)
        self.find_btn.setStyleSheet("""
            QPushButton {
                background: #FF6600; color: white;
                border: none; border-radius: 8px;
                font-size: 15px; font-weight: bold;
            }
            QPushButton:hover   { background: #CC5200; }
            QPushButton:pressed { background: #AA4400; }
            QPushButton:disabled{ background: #555555; }
        """)
        vbox.addWidget(self.find_btn)

        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #AAAAAA; font-size: 13px;")
        self.status_label.setWordWrap(True)
        vbox.addWidget(self.status_label)

        outer.addWidget(card)


    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-weight: bold; font-size: 13px; color: #E0E0E0;")
        return lbl

    def _text_field(self, placeholder: str) -> QLineEdit:
        field = QLineEdit()
        field.setPlaceholderText(placeholder)
        field.setText(placeholder)
        field.setFixedHeight(38)
        field.setAlignment(Qt.AlignCenter)
        field.setStyleSheet("""
            QLineEdit {
                border: 1px solid #555555; border-radius: 6px;
                font-size: 14px; padding: 0 10px;
                background: #333333; color: #FFFFFF;
            }
            QLineEdit:focus { border: 1px solid #FF6600; }
        """)
        return field
    
    def paintEvent(self, event):
        p = QPainter(self)
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0, QColor("#1A1A1A"))
        grad.setColorAt(1, QColor("#0A0A0A"))
        p.fillRect(self.rect(), QBrush(grad))

    @property
    def ip(self) -> str:
        return self.ip_field.text().strip()

    @property
    def nickname(self) -> str:
        return self.nick_field.text().strip()

    def set_status(self, text: str):
        self.status_label.setText(text)
        if "Waiting" in text:
            self._dots = 0
            self._anim_timer.start(500)
        else:
            self._anim_timer.stop()

    def set_controls_enabled(self, enabled: bool):
        self.find_btn.setEnabled(enabled)
        self.ip_field.setEnabled(enabled)
        self.nick_field.setEnabled(enabled)

    def reset(self):
        self.set_status("")
        self.set_controls_enabled(True)
        self._anim_timer.stop()

    def _animate_dots(self):
        self._dots = (self._dots % 4) + 1
        self.status_label.setText("Waiting for opponent" + "." * self._dots)

class GameScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        main = QHBoxLayout(self)
        main.setContentsMargins(16, 12, 16, 12)
        main.setSpacing(24)

        left = QVBoxLayout()
        left.setAlignment(Qt.AlignCenter)
        left.setSpacing(20)

        info_row = QHBoxLayout()
        self.turn_label = QLabel("Waiting…")
        self.turn_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FF6600;")
        self.rolls_label = QLabel("ROLLS LEFT: 3")
        self.rolls_label.setStyleSheet("font-size: 13px; color: #E0E0E0;")
        info_row.addWidget(self.turn_label)
        info_row.addStretch()
        info_row.addWidget(self.rolls_label)
        left.addLayout(info_row)

        dice_row = QHBoxLayout()
        dice_row.setSpacing(12)
        self.dice_widgets = [DieWidget(90) for _ in range(5)]
        for dw in self.dice_widgets:
            dice_row.addWidget(dw)
        left.addLayout(dice_row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(14)
        self.roll_btn    = self._btn("Roll Dice",  "#FF6600")
        self.concede_btn = self._btn("Concede",    "#DC3545")
        btn_row.addWidget(self.roll_btn)
        btn_row.addWidget(self.concede_btn)
        left.addLayout(btn_row)

        left_container = QWidget()
        left_container.setLayout(left)
        left_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        main.addWidget(left_container, 3)

        self.scoreboard = ScoreBoardWidget()
        self.scoreboard.setMinimumWidth(500)
        self.scoreboard.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        main.addWidget(self.scoreboard, 0)

    def _btn(self, text: str, color: str) -> QPushButton:
        b = QPushButton(text)
        b.setFixedHeight(42)
        b.setMinimumWidth(130)
        b.setStyleSheet(f"""
            QPushButton {{
                background: {color}; color: white;
                border: none; border-radius: 8px;
                font-size: 14px; font-weight: bold;
            }}
            QPushButton:hover    {{ opacity: 0.85; }}
            QPushButton:disabled {{ background: #AAAAAA; }}
        """)
        return b

class GameController(QObject):

    def __init__(self, game: Game, screen: GameScreen, net: NetworkClient, window: "MainWindow"):
        super().__init__()
        self._game   = game
        self._screen = screen
        self._net    = net
        self._window = window

        self._my_turn   = False
        self._normal_sel: list[int]   = []
        self._override_sel: list[int] = []

        for i, dw in enumerate(screen.dice_widgets):
            dw.clicked.connect(lambda checked=False, idx=i: self._toggle_hold(idx))

        screen.scoreboard.category_selected.connect(self._select_category)

        screen.roll_btn.clicked.connect(self._roll_dice)
        screen.concede_btn.clicked.connect(self._concede)

        self._set_controls_enabled(False)

    def set_my_turn(self, is_my_turn: bool):
        self._my_turn = is_my_turn
        for i, d in enumerate(self._game.dice):
            d.held = False
            self._screen.dice_widgets[i].held = False
        self._set_controls_enabled(is_my_turn)
        if is_my_turn:
            self._screen.turn_label.setText("Your turn")
            self._screen.turn_label.setStyleSheet(
                "font-weight: bold; font-size: 14px; color: #FF6600;")
        else:
            self._screen.turn_label.setText("Opponent's turn")
            self._screen.turn_label.setStyleSheet(
                "font-weight: bold; font-size: 14px; color: #888;")
        self._screen.rolls_label.setText(f"ROLLS LEFT: {3 - self._game.roll_count}")

    def stop_timer(self):
        pass

    def _toggle_hold(self, idx: int):
        if not self._my_turn:
            return
        d = self._game.dice[idx]
        d.held = not d.held
        self._screen.dice_widgets[idx].held = d.held

    def _roll_dice(self):
        if not self._my_turn:
            return
        self._game.roll_dice()
        self._update_dice_display()

        self._normal_sel   = self._game.normal_selectable()
        self._override_sel = self._game.override_selectable()
        self._update_selectable()
        self._update_player_statics()

        self._screen.rolls_label.setText(f"ROLLS LEFT: {3 - self._game.roll_count}")

        if self._game.roll_count >= 3:
            self._screen.roll_btn.setEnabled(False)

        self._net.send({
            "type": "ROLL",
            "payload": {
                "count": self._game.roll_count,
                "dice":  self._game.dice_values,
            }
        })

    @pyqtSlot(int)
    def _select_category(self, idx: int):
        if not self._my_turn:
            return
        if self._game.entries[idx].chosen:
            return

        use_override = idx in self._override_sel
        self._game.select_category(idx, use_override)
        pts = self._game.entries[idx].score

        self._screen.scoreboard.select_player_category(idx, pts)
        self._update_player_statics()

        self._net.send({
            "type": "SELECT",
            "payload": {
                "category":    idx,
                "override":    use_override,
                "score":       pts,
                "upper":       self._game.player.upper_score,
                "upperBonus":  self._game.player.upper_bonus,
                "yahtzeeBonus":self._game.player.yahtzee_bonus,
                "grand":       self._game.player.total,
                "gameOver":    self._game.is_game_over(),
            }
        })

        self.set_my_turn(False)
        self._game.roll_count = 0
        self._normal_sel   = []
        self._override_sel = []
        self._update_selectable()

    def apply_remote(self, msg: dict):
        mtype   = msg.get("type", "")
        payload = msg.get("payload", {})

        if mtype == "ROLL":
            dice = payload.get("dice", [])
            for i, val in enumerate(dice):
                self._game.dice[i].value = val
                self._game.dice[i].held  = False
            self._update_dice_display()

        elif mtype == "SELECT":
            idx   = payload.get("category", -1)
            pts   = payload.get("score", 0)
            upper = payload.get("upper", 0)
            bonus = payload.get("upperBonus", 0)
            yb    = payload.get("yahtzeeBonus", 0)
            grand = payload.get("grand", 0)

            if idx >= 0:
                self._screen.scoreboard.select_opp_category(idx, pts)
            self._screen.scoreboard.update_opp_statics(upper, bonus, yb, grand)

            self._game.roll_count = 0
            self._normal_sel   = []
            self._override_sel = []
            self._update_selectable()
            self.set_my_turn(True)

    def _concede(self):
        ans = QMessageBox.question(
            self._window, "Confirm",
            "Are you sure you want to concede? Opponent will win.",
            QMessageBox.Yes | QMessageBox.No
        )
        if ans == QMessageBox.Yes:
            self.stop_timer()
            self._net.send({"type": "END", "payload": {"concede": True}})
            self._window.return_to_lobby("You conceded.")
            self._net.close()

    def _update_dice_display(self):
        for i, d in enumerate(self._game.dice):
            self._screen.dice_widgets[i].value = d.value
            self._screen.dice_widgets[i].held  = d.held

    def _update_selectable(self):
        all_sel = list(set(self._normal_sel) | set(self._override_sel))
        self._screen.scoreboard.set_player_selectable(all_sel)
        sb = self._screen.scoreboard
        for i, row in enumerate(sb.player_rows):
            if i in all_sel:
                pts = self._game.get_possible_score(i, i in self._override_sel)
                row.set_preview(f"{row._name} ({pts})")
                row.set_selectable(True)
            else:
                if not self._game.entries[i].chosen:
                    row.reset_label()
                row.set_selectable(False)

    def _update_player_statics(self):
        p = self._game.player
        self._screen.scoreboard.update_player_statics(
            p.upper_score, p.upper_bonus, p.yahtzee_bonus, p.total
        )

    def _set_controls_enabled(self, enabled: bool):
        self._screen.roll_btn.setEnabled(enabled)
        self._screen.concede_btn.setEnabled(True)
        for dw in self._screen.dice_widgets:
            dw.set_hold_enabled(enabled)
        if not enabled:
            self._screen.roll_btn.setEnabled(False)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Yahtzee – Network Edition")
        self.resize(1150, 700)
        self.setMinimumSize(900, 580)

        self._net: NetworkClient | None = None
        self._ctrl: GameController | None = None
        self._in_game = False
        self._nickname = "Player"

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._lobby  = LobbyScreen()
        self._game_w = GameScreen()
        self._stack.addWidget(self._lobby)
        self._stack.addWidget(self._game_w)

        self._lobby.find_btn.clicked.connect(self._on_find_game)

    def _on_find_game(self):
        ip   = self._lobby.ip
        nick = self._lobby.nickname
        if not ip or not nick:
            self._lobby.set_status("Please enter IP and nickname.")
            return

        self._nickname = nick
        self._lobby.set_controls_enabled(False)
        self._lobby.set_status("Connecting…")

        try:
            print(f"[CLIENT] Connecting to {ip}:{SERVER_PORT} as '{nick}'")
            net = NetworkClient(ip, SERVER_PORT, nick)
            net.message_received.connect(self._handle_network, Qt.QueuedConnection)
            net.connection_error.connect(self._on_net_error, Qt.QueuedConnection)
            net.connect_to_server()
            print(f"[CLIENT] Connected and HELLO sent!")
            self._net = net
            net.start()
            print(f"[CLIENT] Reader thread started")
            self._lobby.set_status("Waiting for opponent")
        except Exception as e:
            print(f"[CLIENT] Connection FAILED: {e}")
            self._lobby.set_status(f"Connection error: {e}")
            self._lobby.set_controls_enabled(True)

    @pyqtSlot(dict)
    def _handle_network(self, msg: dict):
        print(f"[CLIENT] _handle_network called: {msg}")
        mtype   = msg.get("type", "")
        payload = msg.get("payload", {})

        if mtype == "MATCHED":
            i_start = payload.get("yourTurn", False)
            game = Game(self._nickname)
            self._game_w.scoreboard.reset()
            for dw in self._game_w.dice_widgets:
                dw.reset()
            self._ctrl = GameController(game, self._game_w, self._net, self)
            self._ctrl.set_my_turn(i_start)
            self._stack.setCurrentWidget(self._game_w)
            self._in_game = True
            who = "You go first!" if i_start else "Opponent goes first."
            QMessageBox.information(self, "Matched!", f"Game found! {who}")

        elif mtype in ("ROLL", "SELECT", "UPDATE"):
            if self._ctrl:
                self._ctrl.apply_remote(msg)

        elif mtype == "END":
            reason = payload.get("reason", "")
            your_s = payload.get("yourScore")
            opp_s  = payload.get("opponentScore")
            winner = payload.get("winner", "")

            parts = ["Game over."]
            if reason:
                parts.append(reason)
            if your_s is not None:
                parts.append(f"\nYour score:     {your_s}")
                parts.append(f"Opponent score: {opp_s}")
                parts.append(f"Winner: {winner}")

            self.return_to_lobby("\n".join(parts))
            if self._net:
                self._net.close()

    @pyqtSlot(str)
    def _on_net_error(self, error: str):
        self.return_to_lobby(f"Network error: {error}")

    def return_to_lobby(self, message: str):
        if self._ctrl:
            self._ctrl.stop_timer()
            self._ctrl = None
        self._in_game = False
        self._stack.setCurrentWidget(self._lobby)
        self._lobby.reset()
        if message:
            QMessageBox.information(self, "Game Over", message)

    def closeEvent(self, event):
        if self._in_game:
            ans = QMessageBox.question(
                self, "Quit",
                "Quitting now ends the game and your opponent wins.\nDo you want to quit?",
                QMessageBox.Yes | QMessageBox.No
            )
            if ans != QMessageBox.Yes:
                event.ignore()
                return
            if self._net:
                try:
                    self._net.send({"type": "END", "payload": {"concede": True}})
                    self._net.close()
                except Exception:
                    pass
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.Window,        QColor("#1A1A1A"))
    pal.setColor(QPalette.WindowText,    QColor("#E0E0E0"))
    pal.setColor(QPalette.Base,          QColor("#2A2A2A"))
    pal.setColor(QPalette.AlternateBase, QColor("#333333"))
    pal.setColor(QPalette.Button,        QColor("#333333"))
    pal.setColor(QPalette.ButtonText,    QColor("#E0E0E0"))
    pal.setColor(QPalette.Highlight,     QColor("#FF6600"))
    pal.setColor(QPalette.HighlightedText, QColor("#FFFFFF"))
    app.setPalette(pal)

    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
