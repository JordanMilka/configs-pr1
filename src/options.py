"""Разбор ключей команд в стиле UNIX.

Ключи записываются одной буквой после дефиса и могут объединяться:
"-la" равносильно "-l -a". Аргумент "--" заканчивает список ключей,
одиночный дефис считается обычным операндом.
"""

from src.errors import CommandError

OPTION_SIGN = "-"
END_OF_OPTIONS = "--"
LONG_OPTION_PREFIX = "--"


def read_cluster(name, argument, allowed):
    """Прочитать буквы ключей из одного аргумента.

    :param name: имя команды для сообщения об ошибке.
    :param argument: аргумент, начинающийся с дефиса.
    :param allowed: строка допустимых букв ключей.
    :return: список букв ключей.
    :raises CommandError: если ключ не поддерживается командой.
    """
    if argument.startswith(LONG_OPTION_PREFIX):
        raise CommandError(
            "{0}: неизвестный ключ '{1}'".format(name, argument)
        )
    letters = list(argument[len(OPTION_SIGN):])
    for letter in letters:
        if letter not in allowed:
            raise CommandError(
                "{0}: неверный ключ -- '{1}'".format(name, letter)
            )
    return letters


def parse_options(name, arguments, allowed):
    """Разделить аргументы команды на ключи и операнды.

    :param name: имя команды для сообщений об ошибках.
    :param arguments: список аргументов команды.
    :param allowed: строка допустимых букв ключей.
    :return: кортеж из множества букв ключей и списка операндов.
    :raises CommandError: если встретился неподдерживаемый ключ.
    """
    flags = set()
    operands = []
    options_done = False
    for argument in arguments:
        if options_done or argument == OPTION_SIGN:
            operands.append(argument)
        elif argument == END_OF_OPTIONS:
            options_done = True
        elif argument.startswith(OPTION_SIGN):
            flags.update(read_cluster(name, argument, allowed))
        else:
            operands.append(argument)
    return flags, operands
