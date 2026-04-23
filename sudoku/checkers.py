"""Checkers game (8x8) with PvP and PvC modes.

This module contains:
- board rendering widgets,
- game rules (mandatory captures, promotions, chain captures),
- a simple minimax AI with alpha-beta pruning.
"""

import random
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# ---- UI colors -------------------------------------------------------------
COLOR_BG = "#1e1e2e"
COLOR_SURFACE = "#313244"
COLOR_ACCENT = "#cba6f7"
COLOR_TEXT = "#cdd6f4"
COLOR_BUTTON = "#585b70"
COLOR_BUTTON_HOVER = "#7f849c"

DARK_SQUARE_COLOR = "#45475a"
LIGHT_SQUARE_COLOR = "#cdd6f4"
SELECTED_SQUARE_COLOR = "#f9e2af"
VALID_MOVE_SQUARE_COLOR = "#a6e3a1"

BLACK_PIECE_COLOR = "#11111b"
BLACK_KING_COLOR = "#313244"
WHITE_PIECE_COLOR = "#eff1f5"
WHITE_KING_COLOR = "#bac2de"
PIECE_OUTLINE_COLOR = "#6c7086"

# ---- Board constants -------------------------------------------------------
BOARD_SIZE = 8
SQUARE_SIZE = 72

EMPTY = 0
BLACK = 1
WHITE = 2
BLACK_KING = 3
WHITE_KING = 4

MIN_SCORE = -999999
MAX_SCORE = 999999


def is_black_piece(piece_value: int) -> bool:
    """Return True when the value is a black pawn/king."""
    return piece_value in (BLACK, BLACK_KING)


def is_white_piece(piece_value: int) -> bool:
    """Return True when the value is a white pawn/king."""
    return piece_value in (WHITE, WHITE_KING)


def is_king(piece_value: int) -> bool:
    """Return True when the value is a king."""
    return piece_value in (BLACK_KING, WHITE_KING)


def piece_color(piece_value: int) -> int:
    """Return BLACK or WHITE according to the piece value."""
    return BLACK if is_black_piece(piece_value) else WHITE


class BoardSquare(QWidget):
    """Single UI square of the checkers board."""

    def __init__(
        self,
        row_index: int,
        col_index: int,
        board_widget: "CheckersBoard",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._row_index = row_index
        self._col_index = col_index
        self._board_widget = board_widget
        self._piece_value = EMPTY
        self._display_state = "normal"  # normal | selected | valid

        self.setFixedSize(SQUARE_SIZE, SQUARE_SIZE)

    def set_piece(self, piece_value: int) -> None:
        """Set piece value to draw in this square."""
        self._piece_value = piece_value
        self.update()

    def set_state(self, display_state: str) -> None:
        """Set square visual state: normal, selected or valid move."""
        self._display_state = display_state
        self.update()

    def paintEvent(self, a0: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_dark_square = (self._row_index + self._col_index) % 2 == 1
        if self._display_state == "selected":
            background_color = QColor(SELECTED_SQUARE_COLOR)
        elif self._display_state == "valid":
            background_color = QColor(VALID_MOVE_SQUARE_COLOR)
        elif is_dark_square:
            background_color = QColor(DARK_SQUARE_COLOR)
        else:
            background_color = QColor(LIGHT_SQUARE_COLOR)

        painter.fillRect(self.rect(), background_color)

        if self._piece_value == EMPTY:
            return

        margin = 10
        circle_rect = self.rect().adjusted(margin, margin, -margin, -margin)

        if is_black_piece(self._piece_value):
            fill_color = (
                QColor(BLACK_KING_COLOR)
                if is_king(self._piece_value)
                else QColor(BLACK_PIECE_COLOR)
            )
        else:
            fill_color = (
                QColor(WHITE_KING_COLOR)
                if is_king(self._piece_value)
                else QColor(WHITE_PIECE_COLOR)
            )

        painter.setPen(QPen(QColor(PIECE_OUTLINE_COLOR), 2))
        painter.setBrush(QBrush(fill_color))
        painter.drawEllipse(circle_rect)

        if is_king(self._piece_value):
            painter.setPen(QPen(QColor(COLOR_ACCENT), 2))
            crown_font = painter.font()
            crown_font.setPixelSize(22)
            crown_font.setBold(True)
            painter.setFont(crown_font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "♛")

    def mousePressEvent(self, a0: object) -> None:
        """Forward click to the board/controller."""
        self._board_widget.square_clicked(self._row_index, self._col_index)


class CheckersBoard(QWidget):
    """Visual board containing all squares."""

    def __init__(
        self,
        main_window: "CheckersWindow",
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._window = main_window
        self.squares: list[list[BoardSquare]] = []

        layout = QGridLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        for row_index in range(BOARD_SIZE):
            row_squares: list[BoardSquare] = []
            for col_index in range(BOARD_SIZE):
                square = BoardSquare(row_index, col_index, self, self)
                layout.addWidget(square, row_index, col_index)
                row_squares.append(square)
            self.squares.append(row_squares)

        self.setStyleSheet(f"background-color: {LIGHT_SQUARE_COLOR};")

    def square_clicked(self, row_index: int, col_index: int) -> None:
        """Forward square click to game logic."""
        self._window.handle_click(row_index, col_index)


class CheckersWindow(QMainWindow):
    """Main window for checkers with game rules + AI."""

    # Human plays white in PvC mode, AI plays black.
    AI_DEPTH = {"Facile": 2, "Moyen": 4, "Difficile": 6}

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Jeu de Dames")

        self.vs_ai = False
        self.ai_difficulty = "Moyen"
        self.current_player = WHITE
        self.selected_piece: Optional[tuple[int, int]] = None
        self.valid_destinations: list[tuple[int, int]] = []
        self.must_capture_pieces: list[tuple[int, int]] = []
        self.chain_capture_piece: Optional[tuple[int, int]] = None
        self._ai_thinking = False

        self._reset_state()
        self._build_ui()
        self._refresh_board()

    def _reset_state(self) -> None:
        """Reset board and turn state for a new game."""
        self.board = [[EMPTY] * BOARD_SIZE for _ in range(BOARD_SIZE)]

        # Black pawns on rows 0..2 (dark squares), white on rows 5..7.
        for row_index in range(3):
            for col_index in range(BOARD_SIZE):
                if (row_index + col_index) % 2 == 1:
                    self.board[row_index][col_index] = BLACK

        for row_index in range(5, BOARD_SIZE):
            for col_index in range(BOARD_SIZE):
                if (row_index + col_index) % 2 == 1:
                    self.board[row_index][col_index] = WHITE

        self.current_player = WHITE
        self.selected_piece: Optional[tuple[int, int]] = None
        self.valid_destinations: list[tuple[int, int]] = []
        self.must_capture_pieces: list[tuple[int, int]] = []
        self.chain_capture_piece: Optional[tuple[int, int]] = None

        self._ai_thinking = False

    def _build_ui(self) -> None:
        """Build all Qt widgets for the checkers window."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        central_widget.setStyleSheet(f"background-color: {COLOR_BG};")

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(24, 24, 24, 24)
        root_layout.setSpacing(14)

        title_label = QLabel("JEU DE DAMES")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {COLOR_ACCENT}; background: transparent;")
        root_layout.addWidget(title_label)

        # Control row: mode and AI difficulty.
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(10)

        self.mode_box = QComboBox()
        self.mode_box.addItem("Joueur vs Joueur", False)
        self.mode_box.addItem("Contre l'ordinateur", True)
        self.mode_box.setFont(QFont("Segoe UI", 11))
        self.mode_box.setStyleSheet(self._combo_style())
        controls_layout.addWidget(self.mode_box)

        self.diff_box = QComboBox()
        for difficulty_label in self.AI_DEPTH:
            self.diff_box.addItem(difficulty_label)
        self.diff_box.setCurrentText("Moyen")
        self.diff_box.setFont(QFont("Segoe UI", 11))
        self.diff_box.setStyleSheet(self._combo_style())
        self.diff_box.setEnabled(False)
        controls_layout.addWidget(self.diff_box)

        self.mode_box.currentIndexChanged.connect(self._on_mode_changed)
        root_layout.addLayout(controls_layout)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 12))
        self.status_label.setStyleSheet(
            f"color: {COLOR_TEXT}; background: transparent;"
        )
        root_layout.addWidget(self.status_label)

        self.board_widget = CheckersBoard(self)
        board_wrapper_layout = QHBoxLayout()
        board_wrapper_layout.addStretch()
        board_wrapper_layout.addWidget(self.board_widget)
        board_wrapper_layout.addStretch()
        root_layout.addLayout(board_wrapper_layout)

        new_game_button = QPushButton("Nouvelle partie")
        new_game_button.setFont(QFont("Segoe UI", 12))
        new_game_button.setStyleSheet(
            f"QPushButton {{ background-color: {COLOR_BUTTON}; "
            f"color: {COLOR_TEXT}; border: none; border-radius: 8px; "
            f"padding: 8px 20px; }}"
            f"QPushButton:hover {{ background-color: {COLOR_BUTTON_HOVER}; }}"
        )
        new_game_button.clicked.connect(self._new_game)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(new_game_button)
        button_layout.addStretch()
        root_layout.addLayout(button_layout)

        self.setFixedSize(self.sizeHint())
        self._update_status()

    def _combo_style(self) -> str:
        """Return stylesheet for combo boxes."""
        return (
            f"QComboBox {{ background-color: {COLOR_BUTTON}; "
            f"color: {COLOR_TEXT}; "
            f"border: none; border-radius: 6px; padding: 5px 10px; }}"
            f"QComboBox::drop-down {{ border: none; }}"
            f"QComboBox QAbstractItemView {{ "
            f"background-color: {COLOR_SURFACE}; "
            f"color: {COLOR_TEXT}; "
            f"selection-background-color: {COLOR_BUTTON_HOVER}; }}"
        )

    def _on_mode_changed(self) -> None:
        """Enable/disable AI difficulty controls based on selected mode."""
        self.vs_ai = bool(self.mode_box.currentData())
        self.diff_box.setEnabled(self.vs_ai)

    def _in_bounds(self, row_index: int, col_index: int) -> bool:
        """Return True if position is on the board."""
        return 0 <= row_index < BOARD_SIZE and 0 <= col_index < BOARD_SIZE

    def _movement_directions(self, piece_value: int) -> list[tuple[int, int]]:
        """Return legal movement directions for a piece."""
        if is_king(piece_value):
            return [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        if piece_color(piece_value) == WHITE:
            return [(-1, -1), (-1, 1)]
        return [(1, -1), (1, 1)]

    def _get_jumps(
        self,
        row_index: int,
        col_index: int,
        board_state: Optional[list[list[int]]] = None,
    ) -> list[tuple[int, int]]:
        """Return landing squares for capture moves from a given piece."""
        if board_state is None:
            board_state = self.board

        piece_value = board_state[row_index][col_index]
        if piece_value == EMPTY:
            return []

        jumps: list[tuple[int, int]] = []
        owner_color = piece_color(piece_value)

        for delta_row, delta_col in self._movement_directions(piece_value):
            middle_row = row_index + delta_row
            middle_col = col_index + delta_col
            landing_row = row_index + 2 * delta_row
            landing_col = col_index + 2 * delta_col

            if not self._in_bounds(landing_row, landing_col):
                continue
            if board_state[landing_row][landing_col] != EMPTY:
                continue

            middle_piece = board_state[middle_row][middle_col]
            if middle_piece != EMPTY and piece_color(middle_piece) != owner_color:
                jumps.append((landing_row, landing_col))

        return jumps

    def _get_simple_moves(
        self,
        row_index: int,
        col_index: int,
    ) -> list[tuple[int, int]]:
        """Return non-capturing moves for current board state."""
        piece_value = self.board[row_index][col_index]
        if piece_value == EMPTY:
            return []

        legal_moves: list[tuple[int, int]] = []
        for delta_row, delta_col in self._movement_directions(piece_value):
            next_row = row_index + delta_row
            next_col = col_index + delta_col
            if self._in_bounds(next_row, next_col):
                if self.board[next_row][next_col] == EMPTY:
                    legal_moves.append((next_row, next_col))

        return legal_moves

    def _compute_must_capture_pieces(self) -> list[tuple[int, int]]:
        """List current player pieces that have at least one capture."""
        must_capture_positions: list[tuple[int, int]] = []

        for row_index in range(BOARD_SIZE):
            for col_index in range(BOARD_SIZE):
                piece_value = self.board[row_index][col_index]
                if piece_value == EMPTY:
                    continue
                if piece_color(piece_value) != self.current_player:
                    continue
                if self._get_jumps(row_index, col_index):
                    must_capture_positions.append((row_index, col_index))

        return must_capture_positions

    def _promote_if_needed(self, row_index: int, col_index: int) -> None:
        """Promote pawn to king when reaching opposite side."""
        piece_value = self.board[row_index][col_index]
        if piece_value == WHITE and row_index == 0:
            self.board[row_index][col_index] = WHITE_KING
        elif piece_value == BLACK and row_index == BOARD_SIZE - 1:
            self.board[row_index][col_index] = BLACK_KING

    def _switch_player(self) -> None:
        """Pass turn to the other player and trigger AI if needed."""
        self.current_player = BLACK if self.current_player == WHITE else WHITE
        self.selected_piece = None
        self.valid_destinations = []
        self.chain_capture_piece = None
        self.must_capture_pieces = self._compute_must_capture_pieces()

        if self.vs_ai and self.current_player == BLACK:
            self._ai_thinking = True
            self._update_status()
            QTimer.singleShot(200, self._do_ai_move)

    def handle_click(self, row_index: int, col_index: int) -> None:
        """Handle user click on board square."""
        # Ignore clicks during AI turn.
        if self._ai_thinking:
            return
        if self.vs_ai and self.current_player == BLACK:
            return

        # If user clicks a highlighted destination, apply move immediately.
        if (
            self.selected_piece is not None
            and (row_index, col_index) in self.valid_destinations
        ):
            self._apply_move(self.selected_piece, row_index, col_index)
            return

        # During chain capture, only selected piece can remain active.
        if self.chain_capture_piece is not None:
            if (row_index, col_index) == self.chain_capture_piece:
                self.selected_piece = self.chain_capture_piece
                chain_row, chain_col = self.chain_capture_piece
                self.valid_destinations = self._get_jumps(chain_row, chain_col)
                self._refresh_board()
            return

        clicked_piece = self.board[row_index][col_index]
        if clicked_piece == EMPTY:
            self.selected_piece = None
            self.valid_destinations = []
            self._refresh_board()
            return

        if piece_color(clicked_piece) != self.current_player:
            self.selected_piece = None
            self.valid_destinations = []
            self._refresh_board()
            return

        if (
            self.must_capture_pieces
            and (row_index, col_index) not in self.must_capture_pieces
        ):
            self._update_status(hint="Vous devez capturer !")
            return

        self.selected_piece = (row_index, col_index)
        if self.must_capture_pieces:
            self.valid_destinations = self._get_jumps(row_index, col_index)
        else:
            self.valid_destinations = self._get_simple_moves(
                row_index,
                col_index,
            )

        self._refresh_board()

    # ---- AI engine ---------------------------------------------------------
    def _all_moves_for(
        self,
        board_state: list[list[int]],
        player_color: int,
    ) -> list[tuple[int, int, int, int]]:
        """Return all legal moves for a player on a board state.

        Output item format: (src_row, src_col, dst_row, dst_col)
        Captures are returned exclusively when at least one capture exists.
        """
        capture_moves: list[tuple[int, int, int, int]] = []
        normal_moves: list[tuple[int, int, int, int]] = []

        for row_index in range(BOARD_SIZE):
            for col_index in range(BOARD_SIZE):
                piece_value = board_state[row_index][col_index]
                if piece_value == EMPTY:
                    continue
                if piece_color(piece_value) != player_color:
                    continue

                jumps = self._get_jumps(row_index, col_index, board_state)
                for dst_row, dst_col in jumps:
                    capture_moves.append((row_index, col_index, dst_row, dst_col))

                # Keep simple moves only if no capture has been found so far.
                if not capture_moves:
                    for dst_row, dst_col in self._get_simple_moves_on(
                        row_index,
                        col_index,
                        board_state,
                    ):
                        normal_moves.append((row_index, col_index, dst_row, dst_col))

        return capture_moves if capture_moves else normal_moves

    def _get_simple_moves_on(
        self,
        row_index: int,
        col_index: int,
        board_state: list[list[int]],
    ) -> list[tuple[int, int]]:
        """Return simple (non-capturing) moves on an arbitrary board."""
        piece_value = board_state[row_index][col_index]
        if piece_value == EMPTY:
            return []

        legal_moves: list[tuple[int, int]] = []
        for delta_row, delta_col in self._movement_directions(piece_value):
            next_row = row_index + delta_row
            next_col = col_index + delta_col
            if 0 <= next_row < BOARD_SIZE and 0 <= next_col < BOARD_SIZE:
                if board_state[next_row][next_col] == EMPTY:
                    legal_moves.append((next_row, next_col))

        return legal_moves

    def _apply_move_on(
        self,
        board_state: list[list[int]],
        src_row: int,
        src_col: int,
        dst_row: int,
        dst_col: int,
    ) -> list[list[int]]:
        """Return a copied board state after applying one move."""
        new_board = [row_values[:] for row_values in board_state]

        moved_piece = new_board[src_row][src_col]
        new_board[dst_row][dst_col] = moved_piece
        new_board[src_row][src_col] = EMPTY

        # Capture handling.
        if abs(dst_row - src_row) == 2:
            captured_row = (src_row + dst_row) // 2
            captured_col = (src_col + dst_col) // 2
            new_board[captured_row][captured_col] = EMPTY

        # Promotion handling.
        if new_board[dst_row][dst_col] == WHITE and dst_row == 0:
            new_board[dst_row][dst_col] = WHITE_KING
        elif new_board[dst_row][dst_col] == BLACK and dst_row == BOARD_SIZE - 1:
            new_board[dst_row][dst_col] = BLACK_KING

        return new_board

    def _evaluate(self, board_state: list[list[int]]) -> int:
        """Evaluate board from black perspective.

        Positive scores are better for black.
        """
        score = 0

        for row_index in range(BOARD_SIZE):
            for col_index in range(BOARD_SIZE):
                piece_value = board_state[row_index][col_index]
                if piece_value == EMPTY:
                    continue

                piece_score = 16 if is_king(piece_value) else 10

                # Positional bonus: progress + center control.
                if not is_king(piece_value):
                    advancement = (
                        row_index
                        if is_black_piece(piece_value)
                        else (BOARD_SIZE - 1 - row_index)
                    )
                    piece_score += advancement

                center_bonus = 1 if 2 <= row_index <= 5 and 2 <= col_index <= 5 else 0
                piece_score += center_bonus

                if is_black_piece(piece_value):
                    score += piece_score
                else:
                    score -= piece_score

        return score

    def _minimax(
        self,
        board_state: list[list[int]],
        depth: int,
        alpha: int,
        beta: int,
        maximizing: bool,
    ) -> int:
        """Minimax with alpha-beta pruning."""
        player_color = BLACK if maximizing else WHITE
        legal_moves = self._all_moves_for(board_state, player_color)

        if depth == 0 or not legal_moves:
            return self._evaluate(board_state)

        if maximizing:
            best_score = MIN_SCORE
            for src_row, src_col, dst_row, dst_col in legal_moves:
                child_board = self._apply_move_on(
                    board_state,
                    src_row,
                    src_col,
                    dst_row,
                    dst_col,
                )

                # Keep simplified chain-capture handling for search continuity.
                if abs(dst_row - src_row) == 2 and self._get_jumps(
                    dst_row,
                    dst_col,
                    child_board,
                ):
                    follow_up_moves = self._all_moves_for(child_board, BLACK)
                    for (
                        f_src_row,
                        f_src_col,
                        f_dst_row,
                        f_dst_col,
                    ) in follow_up_moves:
                        child_board_2 = self._apply_move_on(
                            child_board,
                            f_src_row,
                            f_src_col,
                            f_dst_row,
                            f_dst_col,
                        )
                        score = self._minimax(
                            child_board_2,
                            depth - 1,
                            alpha,
                            beta,
                            False,
                        )
                        best_score = max(best_score, score)
                        alpha = max(alpha, best_score)
                        if beta <= alpha:
                            break
                else:
                    score = self._minimax(
                        child_board,
                        depth - 1,
                        alpha,
                        beta,
                        False,
                    )
                    best_score = max(best_score, score)
                    alpha = max(alpha, best_score)

                if beta <= alpha:
                    break

            return best_score

        best_score = MAX_SCORE
        for src_row, src_col, dst_row, dst_col in legal_moves:
            child_board = self._apply_move_on(
                board_state,
                src_row,
                src_col,
                dst_row,
                dst_col,
            )
            score = self._minimax(child_board, depth - 1, alpha, beta, True)
            best_score = min(best_score, score)
            beta = min(beta, best_score)
            if beta <= alpha:
                break

        return best_score

    def _best_ai_move(self) -> Optional[tuple[int, int, int, int]]:
        """Compute best move for black AI according to selected level."""
        search_depth = self.AI_DEPTH.get(self.diff_box.currentText(), 4)
        legal_moves = self._all_moves_for(self.board, BLACK)
        if not legal_moves:
            return None

        # Easy level occasionally picks random legal moves.
        if self.diff_box.currentText() == "Facile" and random.random() < 0.3:
            return random.choice(legal_moves)

        best_score = MIN_SCORE
        best_move: Optional[tuple[int, int, int, int]] = None

        random.shuffle(legal_moves)
        for src_row, src_col, dst_row, dst_col in legal_moves:
            child_board = self._apply_move_on(
                self.board,
                src_row,
                src_col,
                dst_row,
                dst_col,
            )
            score = self._minimax(
                child_board,
                search_depth - 1,
                MIN_SCORE,
                MAX_SCORE,
                False,
            )
            if score > best_score:
                best_score = score
                best_move = (src_row, src_col, dst_row, dst_col)

        return best_move

    def _do_ai_move(self) -> None:
        """Execute one AI move."""
        ai_move = self._best_ai_move()
        self._ai_thinking = False
        if ai_move is None:
            self._show_winner("Blancs")
            return

        src_row, src_col, dst_row, dst_col = ai_move
        self._apply_move((src_row, src_col), dst_row, dst_col)

    def _do_ai_chain_jump(self) -> None:
        """Continue mandatory chain captures for AI player."""
        if self.chain_capture_piece is None:
            self._ai_thinking = False
            return

        src_row, src_col = self.chain_capture_piece
        possible_jumps = self._get_jumps(src_row, src_col)

        if not possible_jumps:
            self._ai_thinking = False
            self._switch_player()
            self._refresh_board()
            self._check_game_over()
            return

        # Easy mode keeps some randomness during chains as well.
        if self.diff_box.currentText() == "Facile" and random.random() < 0.4:
            dst_row, dst_col = random.choice(possible_jumps)
        else:
            search_depth = max(
                1,
                self.AI_DEPTH.get(self.diff_box.currentText(), 4) - 1,
            )
            best_score = MIN_SCORE
            best_jump = possible_jumps[0]

            shuffled_jumps = list(possible_jumps)
            random.shuffle(shuffled_jumps)
            for jump_row, jump_col in shuffled_jumps:
                child_board = self._apply_move_on(
                    self.board,
                    src_row,
                    src_col,
                    jump_row,
                    jump_col,
                )
                score = self._minimax(
                    child_board,
                    search_depth - 1,
                    MIN_SCORE,
                    MAX_SCORE,
                    False,
                )
                if score > best_score:
                    best_score = score
                    best_jump = (jump_row, jump_col)

            dst_row, dst_col = best_jump

        self._ai_thinking = False
        self._apply_move((src_row, src_col), dst_row, dst_col)

    def _apply_move(
        self,
        source_position: tuple[int, int],
        dst_row: int,
        dst_col: int,
    ) -> None:
        """Apply one move on the live board and handle turn flow."""
        src_row, src_col = source_position
        moving_piece = self.board[src_row][src_col]
        is_capture = abs(dst_row - src_row) == 2

        self.board[dst_row][dst_col] = moving_piece
        self.board[src_row][src_col] = EMPTY

        if is_capture:
            captured_row = (src_row + dst_row) // 2
            captured_col = (src_col + dst_col) // 2
            self.board[captured_row][captured_col] = EMPTY

        self._promote_if_needed(dst_row, dst_col)

        # If another jump is possible, keep same player's turn.
        if is_capture:
            further_jumps = self._get_jumps(dst_row, dst_col)
            if further_jumps:
                self.chain_capture_piece = (dst_row, dst_col)
                self.selected_piece = (dst_row, dst_col)
                self.valid_destinations = further_jumps
                self._refresh_board()

                # Human continues manually; AI continues automatically.
                if self.vs_ai and self.current_player == BLACK:
                    self._ai_thinking = True
                    self._update_status()
                    QTimer.singleShot(220, self._do_ai_chain_jump)
                return

        self._switch_player()
        self._refresh_board()
        self._check_game_over()

    def _refresh_board(self) -> None:
        """Refresh all board squares based on current state."""
        valid_positions = set(self.valid_destinations)
        for row_index in range(BOARD_SIZE):
            for col_index in range(BOARD_SIZE):
                square_widget = self.board_widget.squares[row_index][col_index]
                square_widget.set_piece(self.board[row_index][col_index])
                if self.selected_piece == (row_index, col_index):
                    square_widget.set_state("selected")
                elif (row_index, col_index) in valid_positions:
                    square_widget.set_state("valid")
                else:
                    square_widget.set_state("normal")

        self._update_status()

    def _update_status(self, hint: str = "") -> None:
        """Update status text under the title."""
        if self._ai_thinking:
            self.status_label.setText("Ordinateur réfléchit...")
            return

        if self.vs_ai:
            if self.current_player == WHITE:
                player_label = "Blancs (vous)"
            else:
                player_label = "Noirs (ordinateur)"
        else:
            if self.current_player == WHITE:
                player_label = "Blancs"
            else:
                player_label = "Noirs"

        status_text = f"Tour des {player_label}"
        if self.must_capture_pieces:
            status_text += "  |  Capture obligatoire !"
        if hint:
            status_text += f"  ·  {hint}"

        self.status_label.setText(status_text)

    def _check_game_over(self) -> None:
        """Check if game is finished and show winner popup if needed."""
        black_piece_count = sum(
            1
            for row_index in range(BOARD_SIZE)
            for col_index in range(BOARD_SIZE)
            if is_black_piece(self.board[row_index][col_index])
        )
        white_piece_count = sum(
            1
            for row_index in range(BOARD_SIZE)
            for col_index in range(BOARD_SIZE)
            if is_white_piece(self.board[row_index][col_index])
        )

        # Check if current player can move at all.
        current_player_has_move = False
        for row_index in range(BOARD_SIZE):
            for col_index in range(BOARD_SIZE):
                piece_value = self.board[row_index][col_index]
                if piece_value == EMPTY:
                    continue
                if piece_color(piece_value) != self.current_player:
                    continue
                if self._get_simple_moves(row_index, col_index):
                    current_player_has_move = True
                    break
                if self._get_jumps(row_index, col_index):
                    current_player_has_move = True
                    break
            if current_player_has_move:
                break

        if black_piece_count == 0 or (
            self.current_player == BLACK and not current_player_has_move
        ):
            self._show_winner("Blancs")
        elif white_piece_count == 0 or (
            self.current_player == WHITE and not current_player_has_move
        ):
            self._show_winner("Noirs")

    def _show_winner(self, winner_label: str) -> None:
        """Display winner popup dialog."""
        message_box = QMessageBox(self)
        message_box.setWindowTitle("Partie terminée")
        message_box.setText(f"Les {winner_label} ont gagné !")
        message_box.setStyleSheet(f"background-color: {COLOR_BG}; color: {COLOR_TEXT};")
        message_box.exec()

    def _new_game(self) -> None:
        """Start a new game using selected mode and difficulty."""
        self.vs_ai = bool(self.mode_box.currentData())
        self.ai_difficulty = self.diff_box.currentText()

        self._reset_state()
        self.must_capture_pieces = self._compute_must_capture_pieces()
        self._refresh_board()
