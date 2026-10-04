"""Команды cat и uniq: чтение и фильтрация текстовых файлов VFS.

Команды читают файлы из памяти и ничего не изменяют. Двоичные файлы
хранятся в VFS в виде base64: cat выводит их в таком виде, а uniq
отказывается с ними работать.
"""

import itertools

from src.errors import CommandError
from src.options import parse_options
from src.paths import locate
from src.vfs import VfsDirectory

CAT_FLAGS = "n"
NUMBER_FLAG = "n"
NUMBER_FORMAT = "{0:6d}\t{1}"
FIRST_NUMBER = 1
UNIQ_FLAGS = "cdui"
COUNT_FLAG = "c"
DUPLICATES_FLAG = "d"
UNIQUE_FLAG = "u"
IGNORE_CASE_FLAG = "i"
COUNT_FORMAT = "{0:7d} {1}"
SINGLE_COUNT = 1
NEWLINE = "\n"
IS_DIRECTORY = "{0}: {1}: является каталогом"
IS_BINARY = "{0}: {1}: двоичный файл"


def read_file(command, session, label):
    """Найти файл VFS по пути, введённому пользователем.

    :param command: имя команды для сообщения об ошибке.
    :param session: состояние сеанса.
    :param label: путь так, как его ввёл пользователь.
    :return: файл VfsFile.
    :raises CommandError: если пути нет или он указывает на каталог.
    """
    node = locate(command, session, label).node
    if isinstance(node, VfsDirectory):
        raise CommandError(IS_DIRECTORY.format(command, label))
    return node


def trim_newline(text):
    """Убрать один завершающий перевод строки.

    Окно эмулятора само добавляет перевод строки после вывода команды.

    :param text: текст вывода.
    :return: текст без одного завершающего перевода строки.
    """
    if text.endswith(NEWLINE):
        return text[:-len(NEWLINE)]
    return text


def number_lines(text):
    """Пронумеровать строки текста (ключ -n команды cat).

    :param text: текст вывода.
    :return: текст, в котором перед каждой строкой стоит её номер.
    """
    return NEWLINE.join(
        NUMBER_FORMAT.format(number, line)
        for number, line in enumerate(text.splitlines(), FIRST_NUMBER)
    )


def command_cat(arguments, session):
    """Вывести содержимое файлов, склеивая их друг за другом.

    Ключ -n нумерует строки. Двоичные файлы выводятся в base64. Если
    хотя бы один файл не найден, ничего не выводится.

    :param arguments: список аргументов команды.
    :param session: состояние сеанса.
    :return: текст для вывода.
    :raises CommandError: если файл не указан, не найден, это каталог
        или ключ неверен.
    """
    flags, operands = parse_options("cat", arguments, CAT_FLAGS)
    if not operands:
        raise CommandError("cat: не указан файл")
    files = [read_file("cat", session, label) for label in operands]
    text = "".join(file.content for file in files)
    if NUMBER_FLAG in flags:
        return number_lines(text)
    return trim_newline(text)


def read_uniq_input(session, operands):
    """Получить файл, который обрабатывает uniq.

    :param session: состояние сеанса.
    :param operands: список операндов команды.
    :return: текстовый файл VfsFile.
    :raises CommandError: если операнд не один, файл не найден, это
        каталог или двоичный файл.
    """
    if not operands:
        raise CommandError("uniq: не указан файл")
    if operands[1:]:
        raise CommandError(
            "uniq: лишний операнд '{0}'".format(operands[1])
        )
    file = read_file("uniq", session, operands[0])
    if file.binary:
        raise CommandError(IS_BINARY.format("uniq", operands[0]))
    return file


def group_lines(lines, ignore_case):
    """Объединить подряд идущие одинаковые строки.

    :param lines: список строк.
    :param ignore_case: True, чтобы не различать регистр.
    :return: список пар (первая строка группы, число строк в группе).
    """
    key = str.casefold if ignore_case else None
    groups = []
    for _, items in itertools.groupby(lines, key=key):
        group = list(items)
        groups.append((group[0], len(group)))
    return groups


def is_selected(count, flags):
    """Проверить, нужно ли выводить группу строк.

    :param count: число подряд идущих одинаковых строк.
    :param flags: множество букв ключей команды.
    :return: для -d - группы с повторами, для -u - группы из одной
        строки, без этих ключей - все группы.
    """
    if DUPLICATES_FLAG in flags:
        return count > SINGLE_COUNT
    if UNIQUE_FLAG in flags:
        return count == SINGLE_COUNT
    return True


def command_uniq(arguments, session):
    """Убрать подряд идущие повторяющиеся строки файла.

    Ключи: -c (перед строкой выводится число повторов), -d (только
    повторяющиеся строки), -u (только неповторяющиеся строки), -i
    (не различать регистр). Ключи -d и -u несовместимы. Как и в UNIX,
    сравниваются только соседние строки.

    :param arguments: список аргументов команды.
    :param session: состояние сеанса.
    :return: текст для вывода.
    :raises CommandError: при неверных ключах, несовместимых ключах
        или неподходящем файле.
    """
    flags, operands = parse_options("uniq", arguments, UNIQ_FLAGS)
    if DUPLICATES_FLAG in flags and UNIQUE_FLAG in flags:
        raise CommandError("uniq: ключи -d и -u несовместимы")
    file = read_uniq_input(session, operands)
    groups = group_lines(
        file.content.splitlines(), IGNORE_CASE_FLAG in flags
    )
    lines = [
        COUNT_FORMAT.format(count, line) if COUNT_FLAG in flags else line
        for line, count in groups
        if is_selected(count, flags)
    ]
    return NEWLINE.join(lines)
