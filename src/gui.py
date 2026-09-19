"""Графический интерфейс эмулятора командной оболочки.

Окно содержит область вывода диалога и однострочное поле ввода.
Заголовок окна формируется по данным реальной операционной
системы в формате "Эмулятор - [username@hostname]".
"""

import getpass
import socket
import tkinter as tk

from src.commands import CommandError, ExitRequested, execute
from src.parser import ParseError, parse_line

OUTPUT_HEIGHT = 24
OUTPUT_WIDTH = 80
PROMPT = "$ "
WELCOME = "Эмулятор оболочки. Доступны команды: ls, cd, exit."


def get_user_name():
    """Получить имя текущего пользователя ОС.

    :return: имя пользователя или "user", если оно недоступно.
    """
    try:
        return getpass.getuser()
    except OSError:
        return "user"


def build_title():
    """Сформировать заголовок окна по данным реальной ОС.

    :return: строка вида "Эмулятор - [username@hostname]".
    """
    return "Эмулятор - [{0}@{1}]".format(
        get_user_name(), socket.gethostname()
    )


class EmulatorWindow:
    """Окно эмулятора с полем вывода и полем ввода команд."""

    def __init__(self, master):
        """Создать и настроить виджеты окна.

        :param master: корневое окно Tk.
        """
        self.master = master
        self.master.title(build_title())
        self.output = tk.Text(
            master,
            height=OUTPUT_HEIGHT,
            width=OUTPUT_WIDTH,
            state=tk.DISABLED,
        )
        self.entry = tk.Entry(master)
        self.place_widgets()
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus_set()
        self.write(WELCOME)

    def place_widgets(self):
        """Разместить виджеты в окне."""
        self.output.pack(fill=tk.BOTH, expand=True)
        self.entry.pack(fill=tk.X)

    def write(self, text):
        """Добавить строку текста в область вывода.

        :param text: выводимый текст.
        """
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)

    def on_enter(self, event):
        """Обработать нажатие клавиши Enter в поле ввода.

        :param event: событие Tk о нажатии клавиши.
        :return: строка "break", останавливающая обработку.
        """
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        self.write(PROMPT + line)
        self.run_line(line)
        return "break"

    def run_line(self, line):
        """Разобрать и выполнить одну строку ввода.

        :param line: строка, введённая пользователем.
        """
        try:
            tokens = parse_line(line)
        except ParseError as error:
            self.write("ошибка разбора: {0}".format(error))
            return
        if not tokens:
            return
        self.run_command(tokens)

    def run_command(self, tokens):
        """Выполнить команду и показать её результат.

        :param tokens: непустой список токенов строки ввода.
        """
        try:
            self.write(execute(tokens))
        except CommandError as error:
            self.write(str(error))
        except ExitRequested:
            self.master.destroy()
