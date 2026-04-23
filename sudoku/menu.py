"""Startup menu – lets the user choose a game."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Re-use the colour palette from the Sudoku UI
COLOR_BG = "#1e1e2e"
COLOR_SURFACE = "#313244"
COLOR_ACCENT = "#cba6f7"
COLOR_TEXT = "#cdd6f4"
COLOR_BTN = "#585b70"
COLOR_BTN_HOVER = "#7f849c"


class MenuWindow(QWidget):
    """Full-screen-ish launcher that opens individual game windows."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Launcher")
        self.setFixedSize(400, 420)
        self.setStyleSheet(f"background-color: {COLOR_BG};")
        self._game_windows: list = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.setSpacing(20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("🎮 Game Launcher")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 26, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLOR_ACCENT}; background: transparent;")
        layout.addWidget(title)

        subtitle = QLabel("Choisissez un jeu")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setFont(QFont("Segoe UI", 12))
        subtitle.setStyleSheet(f"color: {COLOR_TEXT}; background: transparent;")
        layout.addWidget(subtitle)

        layout.addSpacing(16)

        # Sudoku button
        sudoku_btn = self._make_button("♟  Sudoku", "#89b4fa")
        sudoku_btn.clicked.connect(self._open_sudoku)
        layout.addWidget(sudoku_btn)

        # Checkers button
        checkers_btn = self._make_button("⚫  Jeu de Dames", "#a6e3a1")
        checkers_btn.clicked.connect(self._open_checkers)
        layout.addWidget(checkers_btn)

        layout.addStretch()

        # Quit button
        quit_btn = self._make_button("Quitter", COLOR_BTN, small=True)
        quit_btn.clicked.connect(self.close)
        layout.addWidget(quit_btn)

    def _make_button(self, text: str, color: str, small: bool = False) -> QPushButton:
        btn = QPushButton(text)
        h = 48 if small else 64
        btn.setFixedHeight(h)
        font_size = 11 if small else 14
        btn.setFont(QFont("Segoe UI", font_size, QFont.Weight.Bold))
        btn.setStyleSheet(
            f"QPushButton {{ background-color: {color}; color: {COLOR_BG}; "
            f"border: none; border-radius: 10px; padding: 8px 24px; }}"
            f"QPushButton:hover {{ background-color: {COLOR_BTN_HOVER}; color: {COLOR_TEXT}; }}"
            f"QPushButton:pressed {{ background-color: {COLOR_SURFACE}; }}"
        )
        return btn

    def _open_sudoku(self):
        from sudoku.ui import SudokuWindow

        win = SudokuWindow()
        win.show()
        self._game_windows.append(win)

    def _open_checkers(self):
        from sudoku.checkers import CheckersWindow

        win = CheckersWindow()
        win.show()
        self._game_windows.append(win)
