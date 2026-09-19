"""Разбор строки ввода эмулятора командной оболочки.

Модуль отвечает за раскрытие переменных окружения реальной ОС
и за разделение строки на имя команды и её аргументы.
"""

import os

VARIABLE_SIGN = "$"
BRACE_OPEN = "{"
BRACE_CLOSE = "}"
NAME_EXTRA_SYMBOL = "_"
NOT_FOUND = -1


class ParseError(Exception):
    """Ошибка разбора строки ввода."""


def is_name_symbol(symbol):
    """Проверить, может ли символ входить в имя переменной.

    :param symbol: проверяемый символ.
    :return: True, если символ допустим в имени переменной.
    """
    return symbol.isalnum() or symbol == NAME_EXTRA_SYMBOL


def read_braced_name(text, start):
    """Прочитать имя переменной в фигурных скобках.

    :param text: исходная строка.
    :param start: позиция открывающей скобки.
    :return: кортеж из имени переменной и позиции после имени.
    :raises ParseError: если закрывающая скобка отсутствует.
    """
    end = text.find(BRACE_CLOSE, start)
    if end == NOT_FOUND:
        raise ParseError("не закрыта фигурная скобка в имени переменной")
    return text[start + 1:end], end + 1


def read_plain_name(text, start):
    """Прочитать имя переменной без фигурных скобок.

    :param text: исходная строка.
    :param start: позиция первого символа имени.
    :return: кортеж из имени переменной и позиции после имени.
    """
    end = start
    while end < len(text) and is_name_symbol(text[end]):
        end += 1
    return text[start:end], end


def read_variable_name(text, start):
    """Прочитать имя переменной, начиная с позиции после знака доллара.

    :param text: исходная строка.
    :param start: позиция первого символа имени.
    :return: кортеж из имени переменной и позиции после имени.
    """
    if start < len(text) and text[start] == BRACE_OPEN:
        return read_braced_name(text, start)
    return read_plain_name(text, start)


def expand_variables(text):
    """Раскрыть переменные окружения вида $HOME и ${HOME}.

    Неизвестная переменная заменяется пустой строкой, как это
    принято в UNIX-подобных оболочках.

    :param text: строка ввода пользователя.
    :return: строка с подставленными значениями переменных.
    :raises ParseError: если имя переменной записано неверно.
    """
    parts = []
    position = 0
    while position < len(text):
        if text[position] != VARIABLE_SIGN:
            parts.append(text[position])
            position += 1
            continue
        name, position = read_variable_name(text, position + 1)
        if not name:
            parts.append(VARIABLE_SIGN)
        else:
            parts.append(os.environ.get(name, ""))
    return "".join(parts)


def parse_line(line):
    """Разобрать строку ввода на список токенов.

    Первый токен списка является именем команды, остальные -
    её аргументами. Для пустой строки возвращается пустой список.

    :param line: строка, введённая пользователем.
    :return: список токенов строки.
    :raises ParseError: если строку не удалось разобрать.
    """
    return expand_variables(line).split()
