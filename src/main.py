"""Точка входа эмулятора командной оболочки.

Запуск: python -m src.main
"""

import tkinter as tk

from src.gui import EmulatorWindow


def main():
    """Создать окно эмулятора и запустить цикл обработки событий."""
    root = tk.Tk()
    EmulatorWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
