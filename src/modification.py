"""Команды chown и rm: изменение VFS в памяти.

Команды меняют только дерево VFS, хранящееся в памяти. ZIP-архив
на диске никогда не изменяется: после перезапуска эмулятора VFS
снова загружается в исходном виде. Перед изменением проверяются
все операнды, поэтому при ошибке VFS остаётся нетронутой.
"""

from src.errors import CommandError
from src.options import parse_options
from src.paths import find_node, locate
from src.vfs import CURRENT_PART, PARENT_PART, SEPARATOR, VfsDirectory

CHOWN_FLAGS = "R"
RECURSIVE_CHOWN_FLAG = "R"
OWNER_SEPARATOR = ":"
NAME_START_SYMBOL = "_"
NAME_EXTRA_SYMBOLS = "_-"
RM_FLAGS = "rfv"
RECURSIVE_REMOVE_FLAG = "r"
FORCE_FLAG = "f"
VERBOSE_FLAG = "v"
DOT_PARTS = (CURRENT_PART, PARENT_PART)
INVALID_OWNER = "chown: неверный владелец или группа: '{0}'"
NO_OWNER = "chown: не указан владелец"
NO_CHOWN_FILE = "chown: не указан файл после '{0}'"
NO_RM_OPERAND = "rm: пропущен операнд"
REMOVE_DOT = "rm: невозможно удалить '{0}': нельзя удалять '.' и '..'"
REMOVE_ROOT = "rm: невозможно удалить '{0}': это корневой каталог"
REMOVE_DIRECTORY = "rm: невозможно удалить '{0}': это каталог"
REMOVE_CURRENT = (
    "rm: невозможно удалить '{0}': это текущий каталог или содержит его"
)
REMOVED_FILE = "удалён '{0}'"
REMOVED_DIRECTORY = "удалён каталог '{0}'"


def is_valid_name(name):
    """Проверить имя пользователя или группы.

    :param name: имя.
    :return: True, если имя начинается с буквы или "_" и состоит из
        букв, цифр, "_" и "-".
    """
    first = name[:1]
    if not (first.isalpha() or first == NAME_START_SYMBOL):
        return False
    return all(
        symbol.isalnum() or symbol in NAME_EXTRA_SYMBOLS for symbol in name
    )


def is_valid_spec(owner, separator, group):
    """Проверить части записи владельца.

    :param owner: часть до двоеточия.
    :param separator: двоеточие или пустая строка, если его нет.
    :param group: часть после двоеточия.
    :return: True, если есть хотя бы одно имя, все имена корректны, а
        двоеточие не стоит без группы.
    """
    names = [name for name in (owner, group) if name]
    if separator and not group:
        return False
    return bool(names) and all(is_valid_name(name) for name in names)


def parse_owner(spec):
    """Разобрать запись владельца вида "ВЛАДЕЛЕЦ[:ГРУППА]" или ":ГРУППА".

    :param spec: запись владельца из командной строки.
    :return: пара (владелец, группа); отсутствующая часть - None.
    :raises CommandError: если запись неверна. Запись "ВЛАДЕЛЕЦ:" без
        группы не поддерживается: списка пользователей в эмуляторе нет.
    """
    owner, separator, group = spec.partition(OWNER_SEPARATOR)
    if not is_valid_spec(owner, separator, group):
        raise CommandError(INVALID_OWNER.format(spec))
    return (owner or None, group or None)


def iter_nodes(node):
    """Обойти узел и всё его содержимое.

    :param node: файл или каталог VFS.
    :return: итератор по узлу и всем вложенным узлам.
    """
    yield node
    if isinstance(node, VfsDirectory):
        for child in node.children.values():
            yield from iter_nodes(child)


def command_chown(arguments, session):
    """Сменить владельца и группу файлов и каталогов.

    Запись владельца: "имя", "имя:группа" или ":группа". Ключ -R
    обрабатывает каталоги вместе с содержимым. Проверка существования
    пользователей не выполняется: подойдёт любое корректное имя.

    :param arguments: список аргументов команды.
    :param session: состояние сеанса.
    :return: пустая строка: при успехе chown ничего не выводит.
    :raises CommandError: если запись владельца неверна, нет операндов
        или путь не существует.
    """
    flags, operands = parse_options("chown", arguments, CHOWN_FLAGS)
    if not operands:
        raise CommandError(NO_OWNER)
    if not operands[1:]:
        raise CommandError(NO_CHOWN_FILE.format(operands[0]))
    owner, group = parse_owner(operands[0])
    targets = [locate("chown", session, label) for label in operands[1:]]
    for target in targets:
        nodes = [target.node]
        if RECURSIVE_CHOWN_FLAG in flags:
            nodes = iter_nodes(target.node)
        for node in nodes:
            node.owner = owner or node.owner
            node.group = group or node.group
    return ""


def last_part(label):
    """Получить последнюю часть пути, введённого пользователем.

    :param label: путь так, как его ввёл пользователь.
    :return: последнее имя пути без завершающих "/".
    """
    return label.rstrip(SEPARATOR).split(SEPARATOR)[-1]


def check_removable(session, target, flags):
    """Проверить, что узел можно удалить.

    :param session: состояние сеанса.
    :param target: объект Target с найденным узлом.
    :param flags: множество букв ключей команды.
    :raises CommandError: для ".", "..", корня, каталога без ключа -r
        и каталога, в котором находится текущий каталог сеанса.
    """
    label = target.label
    if last_part(label) in DOT_PARTS:
        raise CommandError(REMOVE_DOT.format(label))
    if not target.parts:
        raise CommandError(REMOVE_ROOT.format(label))
    is_directory = isinstance(target.node, VfsDirectory)
    if is_directory and RECURSIVE_REMOVE_FLAG not in flags:
        raise CommandError(REMOVE_DIRECTORY.format(label))
    if session.cwd[:len(target.parts)] == target.parts:
        raise CommandError(REMOVE_CURRENT.format(label))


def is_inside(parts, ancestor):
    """Проверить, что путь лежит строго внутри другого пути.

    :param parts: список имён проверяемого пути.
    :param ancestor: список имён предполагаемого родителя.
    :return: True, если ancestor - собственный префикс parts.
    """
    return len(parts) > len(ancestor) and parts[:len(ancestor)] == ancestor


def drop_nested(targets):
    """Убрать узлы, которые удалятся вместе с родительским каталогом.

    :param targets: список объектов Target.
    :return: список без вложенных узлов.
    """
    return [
        target
        for target in targets
        if not any(is_inside(target.parts, other.parts) for other in targets)
    ]


def collect_targets(session, operands, flags):
    """Найти и проверить все узлы, которые нужно удалить.

    Ничего не удаляется, пока проверены не все операнды. Повторяющиеся
    операнды учитываются один раз. С ключом -f несуществующие пути
    пропускаются без ошибки.

    :param session: состояние сеанса.
    :param operands: список путей.
    :param flags: множество букв ключей команды.
    :return: список объектов Target.
    :raises CommandError: если какой-либо узел нельзя удалить.
    """
    targets = []
    seen = set()
    for label in operands:
        try:
            target = locate("rm", session, label)
        except CommandError:
            if FORCE_FLAG in flags:
                continue
            raise
        check_removable(session, target, flags)
        if tuple(target.parts) not in seen:
            seen.add(tuple(target.parts))
            targets.append(target)
    return drop_nested(targets)


def removal_message(target):
    """Составить сообщение об удалении (ключ -v команды rm).

    :param target: объект Target удалённого узла.
    :return: строка вида "удалён 'путь'".
    """
    if isinstance(target.node, VfsDirectory):
        return REMOVED_DIRECTORY.format(target.label)
    return REMOVED_FILE.format(target.label)


def command_rm(arguments, session):
    """Удалить файлы и каталоги из VFS (только в памяти).

    Ключи: -r (удалять каталоги вместе с содержимым), -f (не считать
    ошибкой несуществующие пути), -v (сообщать об удалении). Нельзя
    удалять корень, "." и "..", а также каталог, содержащий текущий.

    :param arguments: список аргументов команды.
    :param session: состояние сеанса.
    :return: сообщения об удалении при ключе -v, иначе пустая строка.
    :raises CommandError: если нет операндов, путь не существует или
        узел нельзя удалить; в этом случае ничего не удаляется.
    """
    flags, operands = parse_options("rm", arguments, RM_FLAGS)
    if not operands:
        if FORCE_FLAG in flags:
            return ""
        raise CommandError(NO_RM_OPERAND)
    targets = collect_targets(session, operands, flags)
    for target in targets:
        parent = find_node(session.root, target.parts[:-1])
        del parent.children[target.parts[-1]]
    if VERBOSE_FLAG not in flags:
        return ""
    return "\n".join(removal_message(target) for target in targets)
