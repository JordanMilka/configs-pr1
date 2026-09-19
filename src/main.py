"""Точка входа эмулятора командной оболочки.

Запуск: python -m src.main [--vfs ПУТЬ] [--script ПУТЬ]
"""

import tkinter as tk

from src.config import parse_arguments
from src.gui import EmulatorWindow


def main():
    """Разобрать параметры, создать окно и запустить цикл событий."""
    config = parse_arguments()
    root = tk.Tk()
    EmulatorWindow(root, config)
    root.mainloop()


if __name__ == "__main__":
    main()
