"""Работа с путями внутри VFS.

Пути бывают абсолютными (начинаются с "/") и относительными
(отсчитываются от текущего каталога сеанса). Части "." и ".."
обрабатываются так же, как в UNIX; выше корня подняться нельзя.
"""

from collections import namedtuple

from src.errors import CommandError
from src.vfs import CURRENT_PART, PARENT_PART, SEPARATOR, VfsDirectory

NOT_FOUND = "{0}: {1}: нет такого файла или каталога"

Target = namedtuple("Target", ["label", "parts", "node"])


def normalize(cwd, path):
    """Привести путь к списку имён от корня VFS.

    :param cwd: список имён текущего каталога.
    :param path: абсолютный или относительный путь.
    :return: список имён от корня, без "." и "..".
    """
    parts = [] if path.startswith(SEPARATOR) else list(cwd)
    for part in path.split(SEPARATOR):
        if not part or part == CURRENT_PART:
            continue
        if part == PARENT_PART:
            if parts:
                parts.pop()
        else:
            parts.append(part)
    return parts


def find_node(root, parts):
    """Найти узел VFS по списку имён от корня.

    :param root: корневой каталог VFS.
    :param parts: список имён от корня.
    :return: найденный узел или None, если пути не существует.
    """
    node = root
    for part in parts:
        if not isinstance(node, VfsDirectory):
            return None
        node = node.children.get(part)
        if node is None:
            return None
    return node


def format_path(parts):
    """Составить абсолютный путь из списка имён.

    :param parts: список имён от корня.
    :return: строка вида "/home/user"; для корня - "/".
    """
    return SEPARATOR + SEPARATOR.join(parts)


def locate(command, session, label):
    """Найти узел VFS по пути, введённому пользователем.

    :param command: имя команды для сообщения об ошибке.
    :param session: состояние сеанса.
    :param label: путь так, как его ввёл пользователь.
    :return: объект Target с путём, списком имён и найденным узлом.
    :raises CommandError: если пути не существует.
    """
    parts = normalize(session.cwd, label)
    node = find_node(session.root, parts)
    if node is None:
        raise CommandError(NOT_FOUND.format(command, label))
    return Target(label, parts, node)
