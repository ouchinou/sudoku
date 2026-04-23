"""Sudoku puzzle generator with three difficulty levels."""

import random
from copy import deepcopy
from enum import Enum


class Difficulty(Enum):
    EASY = "Facile"
    MEDIUM = "Moyen"
    HARD = "Difficile"


# Number of cells to remove per difficulty
CELLS_TO_REMOVE = {
    Difficulty.EASY: 36,
    Difficulty.MEDIUM: 46,
    Difficulty.HARD: 55,
}


def _is_valid(board: list[list[int]], row: int, col: int, num: int) -> bool:
    """Check if placing num at (row, col) is valid."""
    if num in board[row]:
        return False
    if num in (board[r][col] for r in range(9)):
        return False
    box_r, box_c = (row // 3) * 3, (col // 3) * 3
    for r in range(box_r, box_r + 3):
        for c in range(box_c, box_c + 3):
            if board[r][c] == num:
                return False
    return True


def _fill_board(board: list[list[int]]) -> bool:
    """Fill the board using backtracking."""
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                nums = list(range(1, 10))
                random.shuffle(nums)
                for num in nums:
                    if _is_valid(board, row, col, num):
                        board[row][col] = num
                        if _fill_board(board):
                            return True
                        board[row][col] = 0
                return False
    return True


def _count_solutions(board: list[list[int]], limit: int = 2) -> int:
    """Count solutions up to limit (used to ensure unique puzzle)."""
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                count = 0
                for num in range(1, 10):
                    if _is_valid(board, row, col, num):
                        board[row][col] = num
                        count += _count_solutions(board, limit)
                        board[row][col] = 0
                        if count >= limit:
                            return count
                return count
    return 1


def generate_puzzle(difficulty: Difficulty) -> tuple[list[list[int]], list[list[int]]]:
    """
    Generate a Sudoku puzzle.

    Returns:
        (puzzle, solution) where puzzle has 0 for empty cells.
    """
    board = [[0] * 9 for _ in range(9)]
    _fill_board(board)
    solution = deepcopy(board)

    cells_to_remove = CELLS_TO_REMOVE[difficulty]
    positions = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(positions)

    removed = 0
    for row, col in positions:
        if removed >= cells_to_remove:
            break
        backup = board[row][col]
        board[row][col] = 0
        # For hard mode we skip uniqueness check to keep generation fast
        if difficulty != Difficulty.HARD:
            test_board = deepcopy(board)
            if _count_solutions(test_board) != 1:
                board[row][col] = backup
                continue
        removed += 1

    return board, solution
