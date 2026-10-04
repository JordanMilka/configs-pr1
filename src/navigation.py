"""Команды ls и cd: просмотр каталогов VFS и переход между ними.

Все операции только читают VFS из памяти. Текущий каталог хранится
в объекте Session и меняется командой cd.
"""

from collections import namedtuple

from src.errors import CommandError
from src.options import parse_options
from src.paths import find_node, locate
from src.vfs import VfsDirectory, VfsFile

LS_FLAGS = "la"
LONG_FLAG = "l"
ALL_FLAG = "a"
HIDDEN_PREFIX = "."
CURRENT_NAME = "."
PARENT_NAME = ".."
NAME_SEPARATOR = "  "
SECTION_SEPARATOR = "\n\n"
MAX_CD_ARGUMENTS = 1
NOT_DIRECTORY = "{0}: {1}: не является каталогом"
DIRECTORY_MARK = "d"
FILE_MARK = "-"
PERMISSION_LETTERS = "rwxrwxrwx"
TOP_PERMISSION_BIT = 0o400
TIME_FORMAT = "{0:04d}-{1:02d}-{2:02d} {3:02d}:{4:02d}"
LONG_LINE = "{0} {1} {2} {3} {4} {5}"

LongRow = namedtuple(
    "LongRow", ["mode", "owner", "group", "size", "mtime", "name"]
)


def sort_key(entry):
    """Получить ключ сортировки записи каталога.

    :param entry: пара (имя, узел).
    :return: ключ: имя без учёта регистра, затем имя как есть.
    """
    name = entry[0]
    return (name.lower(), name)


def describe_mode(node):
    """Записать тип и права узла в виде строки "drwxr-xr-x".

    :param node: файл или каталог VFS.
    :return: строка из десяти символов.
    """
    kind = DIRECTORY_MARK if isinstance(node, VfsDirectory) else FILE_MARK
    letters = [
        letter if node.mode & (TOP_PERMISSION_BIT >> index) else FILE_MARK
        for index, letter in enumerate(PERMISSION_LETTERS)
    ]
    return kind + "".join(letters)


def long_row(name, node):
    """Подготовить ячейки строки подробного списка для узла.

    :param name: имя, под которым узел показывается в списке.
    :param node: файл или каталог VFS.
    :return: объект LongRow со строковыми ячейками.
    """
    return LongRow(
        describe_mode(node),
        node.owner,
        node.group,
        str(node.size),
        TIME_FORMAT.format(*node.mtime),
        name,
    )


def format_long(entries):
    """Составить подробный список (ls -l) с выровненными столбцами.

    :param entries: список пар (имя, узел).
    :return: многострочный текст, по строке на запись.
    """
    rows = [long_row(name, node) for name, node in entries]
    owner_width = max((len(row.owner) for row in rows), default=0)
    group_width = max((len(row.group) for row in rows), default=0)
    size_width = max((len(row.size) for row in rows), default=0)
    return "\n".join(
        LONG_LINE.format(
            row.mode,
            row.owner.ljust(owner_width),
            row.group.ljust(group_width),
            row.size.rjust(size_width),
            row.mtime,
            row.name,
        )
        for row in rows
    )


def render_entries(entries, flags):
    """Показать записи в коротком или подробном виде.

    :param entries: список пар (имя, узел).
    :param flags: множество букв ключей команды.
    :return: текст для вывода.
    """
    if LONG_FLAG in flags:
        return format_long(entries)
    return NAME_SEPARATOR.join(name for name, _ in entries)


def directory_entries(session, target, flags):
    """Получить записи каталога с учётом ключа -a.

    :param session: состояние сеанса.
    :param target: объект Target с найденным каталогом.
    :param flags: множество букв ключей команды.
    :return: список пар (имя, узел). Скрытые имена (с точки)
        пропускаются, если нет ключа -a; с ним в начало добавляются
        "." и "..".
    """
    children = sorted(target.node.children.items(), key=sort_key)
    if ALL_FLAG not in flags:
        return [
            entry
            for entry in children
            if not entry[0].startswith(HIDDEN_PREFIX)
        ]
    parent = find_node(session.root, target.parts[:-1])
    return [(CURRENT_NAME, target.node), (PARENT_NAME, parent)] + children


def add_header(label, body, headed):
    """Добавить к списку заголовок "путь:", если он нужен.

    :param label: путь так, как его ввёл пользователь.
    :param body: текст списка.
    :param headed: True, если в команде несколько операндов.
    :return: текст с заголовком или без него.
    """
    if not headed:
        return body
    lines = [label + ":"]
    if body:
        lines.append(body)
    return "\n".join(lines)


def build_sections(session, targets, flags):
    """Составить блоки вывода ls для всех операндов.

    Сначала выводятся файлы одним списком, затем каталоги по
    отдельности; при нескольких операндах у каталогов есть заголовки.

    :param session: состояние сеанса.
    :param targets: список объектов Target.
    :param flags: множество букв ключей команды.
    :return: список текстовых блоков.
    """
    sections = []
    files = [(item.label, item.node) for item in targets
             if isinstance(item.node, VfsFile)]
    if files:
        sections.append(render_entries(sorted(files, key=sort_key), flags))
    headed = bool(targets[1:])
    directories = sorted(
        (item for item in targets if isinstance(item.node, VfsDirectory)),
        key=lambda item: item.label,
    )
    for item in directories:
        entries = directory_entries(session, item, flags)
        body = render_entries(entries, flags)
        sections.append(add_header(item.label, body, headed))
    return sections


def command_ls(arguments, session):
    """Показать содержимое каталогов или сведения о файлах.

    Поддерживаются ключи -l (подробный список) и -a (показывать
    скрытые имена, "." и ".."). Без операндов показывается текущий
    каталог.

    :param arguments: список аргументов команды.
    :param session: состояние сеанса.
    :return: текст для вывода (пустая строка для пустого каталога).
    :raises CommandError: если ключ неверен или путь не существует.
    """
    flags, operands = parse_options("ls", arguments, LS_FLAGS)
    targets = [
        locate("ls", session, label) for label in operands or [CURRENT_NAME]
    ]
    return SECTION_SEPARATOR.join(build_sections(session, targets, flags))


def command_cd(arguments, session):
    """Сменить текущий каталог.

    Без аргументов выполняется переход в корень VFS.

    :param arguments: список аргументов команды.
    :param session: состояние сеанса.
    :return: пустая строка: при успехе cd ничего не выводит.
    :raises CommandError: если аргументов больше одного, путь не
        существует или указывает не на каталог.
    """
    if len(arguments) > MAX_CD_ARGUMENTS:
        raise CommandError("cd: слишком много аргументов")
    if not arguments:
        session.cwd = []
        return ""
    target = locate("cd", session, arguments[0])
    if not isinstance(target.node, VfsDirectory):
        raise CommandError(NOT_DIRECTORY.format("cd", arguments[0]))
    session.cwd = target.parts
    return ""
