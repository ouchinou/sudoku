"""Entry point – shows the game launcher menu."""

import sys

from PyQt6.QtWidgets import QApplication

from sudoku.menu import MenuWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Game Launcher")
    window = MenuWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
