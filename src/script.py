"""Чтение стартового скрипта эмулятора.

Стартовый скрипт — это текстовый файл, каждая строка которого
является командой эмулятора. Пустые строки и строки-комментарии,
начинающиеся со знака решётки, пропускаются.
"""

COMMENT_SIGN = "#"
ENCODING = "utf-8"


class ScriptError(Exception):
    """Ошибка чтения стартового скрипта."""


def read_script_lines(path):
    """Прочитать строки стартового скрипта.

    :param path: путь к файлу стартового скрипта.
    :return: список строк файла без символов перевода строки.
    :raises ScriptError: если файл не найден или не читается.
    """
    try:
        with open(path, encoding=ENCODING) as script_file:
            return script_file.read().splitlines()
    except OSError as error:
        raise ScriptError(
            "не удалось прочитать файл {0}: {1}".format(path, error)
        )


def is_executable_line(line):
    """Проверить, нужно ли выполнять строку скрипта.

    :param line: строка стартового скрипта.
    :return: False для пустой строки и комментария, иначе True.
    """
    stripped = line.strip()
    if not stripped:
        return False
    return not stripped.startswith(COMMENT_SIGN)
