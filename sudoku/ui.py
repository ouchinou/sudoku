"""Qt6 Sudoku application – main window and game logic."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from sudoku.generator import Difficulty, generate_puzzle

# ─────────────────────────────────────────────────────────────────────────────
# Colours
# ─────────────────────────────────────────────────────────────────────────────
COLOR_BG = "#1e1e2e"
COLOR_SURFACE = "#313244"
COLOR_GRID_LINE_THICK = "#cdd6f4"
COLOR_GRID_LINE_THIN = "#585b70"
COLOR_TEXT_GIVEN = "#cdd6f4"
COLOR_TEXT_USER = "#89b4fa"
COLOR_TEXT_ERROR = "#f38ba8"
COLOR_HINT = "#a6e3a1"
COLOR_SELECTED_BG = "#45475a"
COLOR_RELATED_BG = "#313244"
COLOR_BTN = "#585b70"
COLOR_BTN_HOVER = "#7f849c"
COLOR_ACCENT = "#cba6f7"

CELL_SIZE = 58


# ─────────────────────────────────────────────────────────────────────────────
# Cell widget
# ─────────────────────────────────────────────────────────────────────────────
class SudokuCell(QLabel):
    """Single cell in the Sudoku grid."""

    def __init__(self, row: int, col: int, grid, parent=None):
        self._grid = grid
        super().__init__(parent)
        self.row = row
        self.col = col
        self.given = False
        self.user_value = 0
        self.correct_value = 0
        self.has_error = False
        self.hint_shown = False

        self.setFixedSize(CELL_SIZE, CELL_SIZE)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont("Segoe UI", 20, QFont.Weight.Bold)
        self.setFont(font)
        self._refresh_style(selected=False, related=False)

    # ── style ──────────────────────────────────────────────────────────────
    def _refresh_style(self, selected: bool, related: bool):
        if self.given:
            text_color = COLOR_TEXT_GIVEN
        elif self.hint_shown:
            text_color = COLOR_HINT
        elif self.has_error:
            text_color = COLOR_TEXT_ERROR
        else:
            text_color = COLOR_TEXT_USER

        if selected:
            bg = COLOR_SELECTED_BG
        elif related:
            bg = COLOR_RELATED_BG
        else:
            bg = "transparent"

        self.setStyleSheet(
            f"color: {text_color}; background-color: {bg}; border: none;"
        )

    def set_selected(self, selected: bool, related: bool = False):
        self._refresh_style(selected, related)

    def mark_error(self, error: bool):
        self.has_error = error
        self._refresh_style(False, False)

    def set_hint(self):
        self.hint_shown = True
        self.has_error = False
        self.user_value = self.correct_value
        self.setText(str(self.correct_value))
        self._refresh_style(False, False)

    # ── mouse ──────────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        self._grid.cell_clicked(self.row, self.col)


# ─────────────────────────────────────────────────────────────────────────────
# Grid widget (draws thick / thin borders via nested frames)
# ─────────────────────────────────────────────────────────────────────────────
class SudokuGrid(QWidget):
    """3×3 block container that draws the Sudoku grid with proper borders."""

    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.cells: list[list[SudokuCell]] = []
        self._build()

    def _build(self):
        outer = QGridLayout(self)
        outer.setSpacing(3)  # thick border between boxes
        outer.setContentsMargins(3, 3, 3, 3)

        for box_r in range(3):
            for box_c in range(3):
                box_frame = QFrame()
                box_frame.setStyleSheet(
                    f"background-color: {COLOR_SURFACE}; border: none;"
                )
                box_layout = QGridLayout(box_frame)
                box_layout.setSpacing(1)  # thin border inside box
                box_layout.setContentsMargins(0, 0, 0, 0)

                for cell_r in range(3):
                    for cell_c in range(3):
                        row = box_r * 3 + cell_r
                        col = box_c * 3 + cell_c
                        while len(self.cells) <= row:
                            self.cells.append([])
                        cell = SudokuCell(row, col, self, box_frame)
                        self.cells[row].append(cell)
                        box_layout.addWidget(cell, cell_r, cell_c)

                outer.addWidget(box_frame, box_r, box_c)

        self.setStyleSheet(f"background-color: {COLOR_GRID_LINE_THICK};")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def cell_clicked(self, row: int, col: int):
        self.main_window.select_cell(row, col)


# ─────────────────────────────────────────────────────────────────────────────
# Main window
# ─────────────────────────────────────────────────────────────────────────────
class SudokuWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sudoku")
        self.puzzle: list[list[int]] = []
        self.solution: list[list[int]] = []
        self.selected: tuple[int, int] | None = None
        self.error_count = 0
        self.hint_count = 0
        self._build_ui()
        self._start_game(Difficulty.EASY)

    # ── UI construction ────────────────────────────────────────────────────
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        central.setStyleSheet(f"background-color: {COLOR_BG};")

        # Title
        title = QLabel("SUDOKU")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLOR_ACCENT}; background: transparent;")
        main_layout.addWidget(title)

        # Difficulty + new game row
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(12)

        self.difficulty_box = QComboBox()
        for d in Difficulty:
            self.difficulty_box.addItem(d.value, d)
        self.difficulty_box.setStyleSheet(self._combo_style())
        self.difficulty_box.setFont(QFont("Segoe UI", 12))
        ctrl_row.addWidget(self.difficulty_box)

        new_btn = QPushButton("Nouvelle partie")
        new_btn.setStyleSheet(self._btn_style())
        new_btn.setFont(QFont("Segoe UI", 12))
        new_btn.clicked.connect(self._on_new_game)
        ctrl_row.addWidget(new_btn)

        hint_btn = QPushButton("Indice")
        hint_btn.setStyleSheet(self._btn_style(accent=True))
        hint_btn.setFont(QFont("Segoe UI", 12))
        hint_btn.clicked.connect(self._on_hint)
        ctrl_row.addWidget(hint_btn)

        main_layout.addLayout(ctrl_row)

        # Grid
        self.grid_widget = SudokuGrid(self)
        grid_container = QHBoxLayout()
        grid_container.addStretch()
        grid_container.addWidget(self.grid_widget)
        grid_container.addStretch()
        main_layout.addLayout(grid_container)

        # Number pad
        numpad_row = QHBoxLayout()
        numpad_row.setSpacing(6)
        numpad_row.addStretch()
        self.num_buttons: list[QPushButton] = []
        for n in range(1, 10):
            btn = QPushButton(str(n))
            btn.setFixedSize(48, 48)
            btn.setStyleSheet(self._btn_style())
            btn.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            btn.clicked.connect(lambda _, v=n: self._enter_number(v))
            numpad_row.addWidget(btn)
            self.num_buttons.append(btn)

        erase_btn = QPushButton("⌫")
        erase_btn.setFixedSize(48, 48)
        erase_btn.setStyleSheet(self._btn_style())
        erase_btn.setFont(QFont("Segoe UI", 16))
        erase_btn.clicked.connect(lambda: self._enter_number(0))
        numpad_row.addWidget(erase_btn)
        numpad_row.addStretch()
        main_layout.addLayout(numpad_row)

        # Status bar
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 11))
        self.status_label.setStyleSheet(
            f"color: {COLOR_TEXT_USER}; background: transparent;"
        )
        main_layout.addWidget(self.status_label)

        # Keyboard shortcuts
        for n in range(1, 10):
            sc = QShortcut(QKeySequence(str(n)), self)
            sc.activated.connect(lambda v=n: self._enter_number(v))
        del_sc = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        del_sc.activated.connect(lambda: self._enter_number(0))
        back_sc = QShortcut(QKeySequence(Qt.Key.Key_Backspace), self)
        back_sc.activated.connect(lambda: self._enter_number(0))
        # Arrow navigation
        for key, dr, dc in [
            (Qt.Key.Key_Up, -1, 0),
            (Qt.Key.Key_Down, 1, 0),
            (Qt.Key.Key_Left, 0, -1),
            (Qt.Key.Key_Right, 0, 1),
        ]:
            sc = QShortcut(QKeySequence(key), self)
            sc.activated.connect(lambda dr=dr, dc=dc: self._move_selection(dr, dc))

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFixedSize(self.sizeHint())

    # ── styles ─────────────────────────────────────────────────────────────
    def _btn_style(self, accent: bool = False) -> str:
        bg = COLOR_ACCENT if accent else COLOR_BTN
        hover = "#b4befe" if accent else COLOR_BTN_HOVER
        return (
            f"QPushButton {{ background-color: {bg}; color: {COLOR_BG}; "
            f"border: none; border-radius: 6px; padding: 6px 14px; }}"
            f"QPushButton:hover {{ background-color: {hover}; }}"
            f"QPushButton:pressed {{ background-color: {COLOR_BTN}; }}"
        )

    def _combo_style(self) -> str:
        return (
            f"QComboBox {{ background-color: {COLOR_BTN}; color: {COLOR_TEXT_GIVEN}; "
            f"border: none; border-radius: 6px; padding: 6px 12px; }}"
            f"QComboBox::drop-down {{ border: none; }}"
            f"QComboBox QAbstractItemView {{ background-color: {COLOR_SURFACE}; "
            f"color: {COLOR_TEXT_GIVEN}; selection-background-color: {COLOR_BTN_HOVER}; }}"
        )

    # ── game logic ─────────────────────────────────────────────────────────
    def _start_game(self, difficulty: Difficulty):
        self.puzzle, self.solution = generate_puzzle(difficulty)
        self.error_count = 0
        self.hint_count = 0
        self.selected = None
        self._populate_grid()
        self._update_status()

    def _populate_grid(self):
        for r in range(9):
            for c in range(9):
                cell = self.grid_widget.cells[r][c]
                val = self.puzzle[r][c]
                cell.given = val != 0
                cell.correct_value = self.solution[r][c]
                cell.user_value = val
                cell.has_error = False
                cell.hint_shown = False
                cell.setText(str(val) if val != 0 else "")
                cell.set_selected(False)

    def _on_new_game(self):
        difficulty = self.difficulty_box.currentData()
        self._start_game(difficulty)

    def select_cell(self, row: int, col: int):
        self.selected = (row, col)
        self._highlight_cells(row, col)

    def _highlight_cells(self, sel_r: int, sel_c: int):
        box_r, box_c = (sel_r // 3) * 3, (sel_c // 3) * 3
        for r in range(9):
            for c in range(9):
                cell = self.grid_widget.cells[r][c]
                selected = r == sel_r and c == sel_c
                related = not selected and (
                    r == sel_r
                    or c == sel_c
                    or (box_r <= r < box_r + 3 and box_c <= c < box_c + 3)
                )
                cell.set_selected(selected, related)

    def _move_selection(self, dr: int, dc: int):
        if self.selected is None:
            self.select_cell(0, 0)
            return
        r, c = self.selected
        r = (r + dr) % 9
        c = (c + dc) % 9
        self.select_cell(r, c)

    def _enter_number(self, value: int):
        if self.selected is None:
            return
        r, c = self.selected
        cell = self.grid_widget.cells[r][c]
        if cell.given or cell.hint_shown:
            return

        cell.user_value = value
        cell.hint_shown = False
        if value == 0:
            cell.has_error = False
            cell.setText("")
            cell.set_selected(True)
        else:
            cell.setText(str(value))
            if value != self.solution[r][c]:
                cell.mark_error(True)
                self.error_count += 1
                self._update_status()
                self._show_hint_tip(r, c)
            else:
                cell.mark_error(False)
                cell.set_selected(True)
                if self._is_complete():
                    self._on_victory()

    def _show_hint_tip(self, row: int, col: int):
        """Show a tooltip-style message when the user makes an error."""
        cell = self.grid_widget.cells[row][col]
        correct = self.solution[row][col]
        self.status_label.setStyleSheet(
            f"color: {COLOR_TEXT_ERROR}; background: transparent;"
        )
        self.status_label.setText(
            f"Erreur en ({row+1},{col+1}) – la bonne valeur est {correct}. "
            f"Erreurs : {self.error_count}"
        )

    def _on_hint(self):
        """Reveal the correct value for the selected empty/wrong cell."""
        if self.selected is None:
            self.status_label.setStyleSheet(
                f"color: {COLOR_TEXT_USER}; background: transparent;"
            )
            self.status_label.setText("Sélectionnez une case d'abord.")
            return
        r, c = self.selected
        cell = self.grid_widget.cells[r][c]
        if cell.given or cell.hint_shown:
            self.status_label.setStyleSheet(
                f"color: {COLOR_TEXT_USER}; background: transparent;"
            )
            self.status_label.setText("Cette case est déjà remplie.")
            return
        self.hint_count += 1
        cell.set_hint()
        self._update_status()
        if self._is_complete():
            self._on_victory()

    def _is_complete(self) -> bool:
        for r in range(9):
            for c in range(9):
                cell = self.grid_widget.cells[r][c]
                if cell.user_value != self.solution[r][c]:
                    return False
        return True

    def _on_victory(self):
        difficulty = self.difficulty_box.currentData()
        msg = QMessageBox(self)
        msg.setWindowTitle("Félicitations !")
        msg.setText(
            f"🎉 Puzzle résolu en {self.difficulty_box.currentText()} !\n"
            f"Erreurs : {self.error_count}  |  Indices utilisés : {self.hint_count}"
        )
        msg.setStyleSheet(f"background-color: {COLOR_BG}; color: {COLOR_TEXT_GIVEN};")
        msg.exec()

    def _update_status(self):
        self.status_label.setStyleSheet(
            f"color: {COLOR_TEXT_USER}; background: transparent;"
        )
        self.status_label.setText(
            f"Erreurs : {self.error_count}  |  Indices : {self.hint_count}"
        )
