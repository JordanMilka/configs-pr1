"""Графический интерфейс эмулятора командной оболочки.

Окно содержит область вывода диалога и однострочное поле ввода.
Заголовок окна формируется по данным реальной операционной
системы в формате "Эмулятор - [username@hostname]". При запуске
окно показывает параметры командной строки, загружает VFS и, если
задан стартовый скрипт, выполняет его. Если VFS загрузить не
удалось, об ошибке сообщается, а стартовый скрипт не выполняется.
"""

import getpass
import socket
import tkinter as tk

from src.commands import COMMANDS, CommandError, ExitRequested, execute
from src.config import format_config
from src.parser import ParseError, parse_line
from src.session import Session
from src.script import ScriptError, is_executable_line, read_script_lines
from src.vfs import VfsError, format_summary, load_vfs

OUTPUT_HEIGHT = 24
OUTPUT_WIDTH = 80
MIN_WINDOW_WIDTH = 640
MIN_WINDOW_HEIGHT = 400
PADDING = 4
FONT = "TkFixedFont"
PROMPT = "{0}$ "
START_DELAY_MS = 100
FIRST_LINE_NUMBER = 1
WELCOME = "Эмулятор оболочки. Доступны команды: {0}."
VFS_LOADED = "VFS загружена: {0}"
VFS_ERROR = "ошибка загрузки VFS: {0}"
SCRIPT_SKIPPED = "Стартовый скрипт не выполнен: VFS не загружена."
SCRIPT_DONE = "Стартовый скрипт выполнен."
SCRIPT_STOPPED = "Скрипт остановлен из-за ошибки в строке {0}."


def get_user_name():
    """Получить имя текущего пользователя ОС.

    :return: имя пользователя или "user", если оно недоступно.
    """
    try:
        return getpass.getuser()
    except OSError:
        return "user"


def build_prompt(session):
    """Сформировать приглашение к вводу с текущим каталогом.

    :param session: состояние сеанса.
    :return: строка вида "/home/user$ ".
    """
    return PROMPT.format(session.cwd_path())


def build_title():
    """Сформировать заголовок окна по данным реальной ОС.

    :return: строка вида "Эмулятор - [username@hostname]".
    """
    return "Эмулятор - [{0}@{1}]".format(
        get_user_name(), socket.gethostname()
    )


class EmulatorWindow:
    """Окно эмулятора с полем вывода и полем ввода команд."""

    def __init__(self, master, config):
        """Создать и настроить виджеты окна.

        :param master: корневое окно Tk.
        :param config: объект Config с параметрами запуска.
        """
        self.master = master
        self.config = config
        self.session = Session()
        self.closed = False
        self.master.title(build_title())
        self.master.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.output = tk.Text(
            master,
            height=OUTPUT_HEIGHT,
            width=OUTPUT_WIDTH,
            state=tk.DISABLED,
            font=FONT,
        )
        self.entry = tk.Entry(master, font=FONT)
        self.place_widgets()
        self.entry.bind("<Return>", self.on_enter)
        self.entry.focus_set()
        self.write(WELCOME.format(", ".join(COMMANDS)))
        self.master.after(START_DELAY_MS, self.start)

    def place_widgets(self):
        """Разместить виджеты в окне.

        Поле ввода размещается первым и прижимается к нижнему краю,
        поэтому оно сохраняет свою высоту при любом размере окна.
        """
        self.entry.pack(
            side=tk.BOTTOM, fill=tk.X, padx=PADDING, pady=PADDING
        )
        self.output.pack(
            side=tk.TOP,
            fill=tk.BOTH,
            expand=True,
            padx=PADDING,
            pady=PADDING,
        )

    def start(self):
        """Показать параметры, загрузить VFS, выполнить скрипт."""
        self.write(format_config(self.config))
        vfs_ready = self.connect_vfs()
        script_path = self.config.script_path
        if script_path is None:
            return
        if vfs_ready:
            self.run_script(script_path)
        else:
            self.write(SCRIPT_SKIPPED)

    def connect_vfs(self):
        """Загрузить VFS, заданную параметром командной строки.

        :return: True, если VFS не требуется или успешно загружена,
            и False, если при загрузке произошла ошибка.
        """
        path = self.config.vfs_path
        if path is None:
            return True
        try:
            vfs = load_vfs(path)
        except VfsError as error:
            self.write(VFS_ERROR.format(error))
            return False
        self.session.attach(vfs)
        self.write(VFS_LOADED.format(format_summary(vfs)))
        return True

    def write(self, text):
        """Добавить строку текста в область вывода.

        :param text: выводимый текст.
        """
        self.output.config(state=tk.NORMAL)
        self.output.insert(tk.END, text + "\n")
        self.output.see(tk.END)
        self.output.config(state=tk.DISABLED)
        self.output.update_idletasks()

    def on_enter(self, event):
        """Обработать нажатие клавиши Enter в поле ввода.

        :param event: событие Tk о нажатии клавиши.
        :return: строка "break", останавливающая обработку.
        """
        line = self.entry.get()
        self.entry.delete(0, tk.END)
        self.write(build_prompt(self.session) + line)
        self.run_line(line)
        return "break"

    def run_line(self, line):
        """Разобрать и выполнить одну строку ввода.

        :param line: строка, введённая пользователем.
        :return: True, если строка выполнена без ошибок.
        """
        try:
            tokens = parse_line(line)
        except ParseError as error:
            self.write("ошибка разбора: {0}".format(error))
            return False
        if not tokens:
            return True
        return self.run_command(tokens)

    def run_command(self, tokens):
        """Выполнить команду и показать её результат.

        :param tokens: непустой список токенов строки ввода.
        :return: True, если команда выполнена без ошибок.
        """
        try:
            output = execute(tokens, self.session)
            if output:
                self.write(output)
        except CommandError as error:
            self.write(str(error))
            return False
        except ExitRequested:
            self.closed = True
            self.master.destroy()
        return True

    def run_script(self, path):
        """Выполнить стартовый скрипт эмулятора.

        На экране отображается как ввод, так и вывод, что имитирует
        диалог с пользователем. Выполнение прекращается на первой
        ошибке.

        :param path: путь к файлу стартового скрипта.
        """
        try:
            lines = read_script_lines(path)
        except ScriptError as error:
            self.write("ошибка стартового скрипта: {0}".format(error))
            return
        for number, line in enumerate(lines, FIRST_LINE_NUMBER):
            if self.closed:
                return
            if not self.run_script_line(line):
                self.write(SCRIPT_STOPPED.format(number))
                return
        if not self.closed:
            self.write(SCRIPT_DONE)

    def run_script_line(self, line):
        """Показать строку скрипта и выполнить её.

        :param line: строка стартового скрипта.
        :return: True, если строка выполнена без ошибок.
        """
        if not is_executable_line(line):
            return True
        self.write(build_prompt(self.session) + line.strip())
        return self.run_line(line)
