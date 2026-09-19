"""Параметры командной строки эмулятора.

Поддерживаются два параметра: путь к физическому расположению
VFS и путь к стартовому скрипту эмулятора. Модуль также готовит
отладочный вывод всех заданных параметров при запуске.
"""

import argparse
from collections import namedtuple

NOT_SET = "не задан"
FIRST_LINE = "Параметры запуска:"

Config = namedtuple("Config", ["vfs_path", "script_path"])


def build_parser():
    """Создать разборщик параметров командной строки.

    :return: настроенный объект ArgumentParser.
    """
    parser = argparse.ArgumentParser(
        prog="shell-emulator",
        description="Эмулятор командной оболочки ОС.",
    )
    parser.add_argument(
        "--vfs",
        dest="vfs_path",
        default=None,
        help="путь к физическому расположению VFS",
    )
    parser.add_argument(
        "--script",
        dest="script_path",
        default=None,
        help="путь к стартовому скрипту эмулятора",
    )
    return parser


def parse_arguments(argv=None):
    """Разобрать параметры командной строки.

    :param argv: список аргументов или None, чтобы взять sys.argv.
    :return: объект Config с параметрами запуска.
    """
    values = build_parser().parse_args(argv)
    return Config(values.vfs_path, values.script_path)


def format_value(value):
    """Представить значение параметра для отладочного вывода.

    :param value: значение параметра или None.
    :return: значение параметра или пометка о том, что он не задан.
    """
    if value is None:
        return NOT_SET
    return value


def format_config(config):
    """Собрать отладочный вывод всех заданных параметров.

    :param config: объект Config с параметрами запуска.
    :return: многострочный текст с параметрами запуска.
    """
    lines = [
        FIRST_LINE,
        "  путь к VFS: {0}".format(format_value(config.vfs_path)),
        "  путь к стартовому скрипту: {0}".format(
            format_value(config.script_path)
        ),
    ]
    return "\n".join(lines)
