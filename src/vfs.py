"""Виртуальная файловая система (VFS) эмулятора.

Источником VFS служит ZIP-архив. Архив целиком читается в память:
на диск ничего не распаковывается, а сам архив открывается только
для чтения и никогда не изменяется. Текстовые файлы хранятся в
виде строк, двоичные - в виде строк base64.
"""

import base64
import zipfile
import zlib
from collections import namedtuple

ENCODING = "utf-8"
ASCII = "ascii"
SEPARATOR = "/"
WINDOWS_SEPARATOR = "\\"
CURRENT_PART = "."
PARENT_PART = ".."
NUL_BYTE = b"\x00"
ROOT_NAME = "/"
DEFAULT_OWNER = "root"
DEFAULT_GROUP = "root"
DEFAULT_FILE_MODE = 0o644
DEFAULT_DIRECTORY_MODE = 0o755
PERMISSION_MASK = 0o777
UNIX_MODE_SHIFT = 16
DEFAULT_MTIME = (1980, 1, 1, 0, 0, 0)
BINARY_MARK = " [двоичный]"
TREE_BRANCH = "├── "
TREE_LAST = "└── "
TREE_PIPE = "│   "
TREE_SPACE = "    "
LAST_INDEX = -1
ARCHIVE_ERRORS = (
    zipfile.BadZipFile,
    RuntimeError,
    NotImplementedError,
    zlib.error,
    EOFError,
)

Statistics = namedtuple(
    "Statistics", ["directories", "files", "binary", "size", "depth"]
)


class VfsError(Exception):
    """Ошибка загрузки или разбора VFS."""


def is_binary(data):
    """Определить, являются ли данные двоичными.

    :param data: содержимое файла в виде байтов.
    :return: True, если данные содержат нулевой байт или не являются
        корректным текстом в кодировке UTF-8.
    """
    if NUL_BYTE in data:
        return True
    try:
        data.decode(ENCODING)
    except UnicodeDecodeError:
        return True
    return False


class VfsNode:
    """Общая часть файла и каталога VFS.

    Размер каталога равен нулю. Права, владелец, группа и время
    изменения хранятся только в памяти.
    """

    size = 0

    def __init__(self, name, mode, mtime):
        """Создать узел.

        :param name: имя узла без пути.
        :param mode: права доступа в виде числа (например, 0o644).
        :param mtime: время изменения: (год, месяц, день, час, минута,
            секунда).
        """
        self.name = name
        self.mode = mode
        self.mtime = mtime
        self.owner = DEFAULT_OWNER
        self.group = DEFAULT_GROUP


class VfsFile(VfsNode):
    """Файл VFS.

    Текстовое содержимое хранится строкой, двоичное - строкой base64.
    """

    def __init__(
        self, name, data, mode=DEFAULT_FILE_MODE, mtime=DEFAULT_MTIME
    ):
        """Создать файл по его имени и содержимому.

        :param name: имя файла без пути.
        :param data: содержимое файла в виде байтов.
        :param mode: права доступа.
        :param mtime: время изменения.
        """
        super().__init__(name, mode, mtime)
        self.size = len(data)
        self.binary = is_binary(data)
        if self.binary:
            self.content = base64.b64encode(data).decode(ASCII)
        else:
            self.content = data.decode(ENCODING)


class VfsDirectory(VfsNode):
    """Каталог VFS."""

    def __init__(
        self, name, mode=DEFAULT_DIRECTORY_MODE, mtime=DEFAULT_MTIME
    ):
        """Создать пустой каталог.

        :param name: имя каталога без пути.
        :param mode: права доступа.
        :param mtime: время изменения.
        """
        super().__init__(name, mode, mtime)
        self.children = {}

    def sorted_children(self):
        """Получить содержимое каталога в порядке показа.

        :return: список узлов: сначала каталоги, затем файлы, внутри
            каждой группы - по имени.
        """
        return sorted(
            self.children.values(),
            key=lambda node: (isinstance(node, VfsFile), node.name),
        )


class Vfs:
    """Виртуальная файловая система, загруженная в память."""

    def __init__(self, source, root):
        """Создать VFS.

        :param source: путь к ZIP-архиву, из которого загружена VFS.
        :param root: корневой каталог VfsDirectory.
        """
        self.source = source
        self.root = root

    def statistics(self):
        """Подсчитать сведения о содержимом VFS.

        :return: объект Statistics с числом каталогов (без корня),
            файлов, двоичных файлов, общим размером в байтах и
            максимальной вложенностью узлов.
        """
        directories = files = binary = size = depth = 0
        stack = [(self.root, 0)]
        while stack:
            node, level = stack.pop()
            depth = max(depth, level)
            if isinstance(node, VfsFile):
                files += 1
                size += node.size
                binary += node.binary
                continue
            if node is not self.root:
                directories += 1
            stack.extend(
                (child, level + 1) for child in node.children.values()
            )
        return Statistics(directories, files, binary, size, depth)


def split_path(name):
    """Разделить путь внутри архива на составные части.

    :param name: путь записи ZIP-архива.
    :return: список имён каталогов и файла без пустых частей.
    :raises VfsError: если путь абсолютный или содержит "..".
    """
    unified = name.replace(WINDOWS_SEPARATOR, SEPARATOR)
    parts = [
        part
        for part in unified.split(SEPARATOR)
        if part and part != CURRENT_PART
    ]
    if unified.startswith(SEPARATOR) or PARENT_PART in parts:
        raise VfsError("небезопасный путь в архиве: {0}".format(name))
    return parts


def make_directories(start, parts, name, mtime=DEFAULT_MTIME):
    """Создать цепочку каталогов, пропуская уже существующие.

    :param start: каталог, с которого начинается цепочка.
    :param parts: имена вложенных каталогов.
    :param name: путь записи архива для сообщения об ошибке.
    :param mtime: время изменения новых каталогов.
    :return: самый глубокий каталог цепочки.
    :raises VfsError: если на месте каталога уже есть файл.
    """
    current = start
    for part in parts:
        child = current.children.get(part)
        if child is None:
            child = VfsDirectory(part, mtime=mtime)
            current.children[part] = child
        elif isinstance(child, VfsFile):
            raise VfsError("файл и каталог с одним именем: {0}".format(name))
        current = child
    return current


def entry_mode(info):
    """Получить права доступа записи ZIP-архива.

    :param info: описание записи архива (ZipInfo).
    :return: права из атрибутов Unix или значения по умолчанию, если
        архив создан не в Unix.
    """
    mode = (info.external_attr >> UNIX_MODE_SHIFT) & PERMISSION_MASK
    if mode:
        return mode
    if info.is_dir():
        return DEFAULT_DIRECTORY_MODE
    return DEFAULT_FILE_MODE


def add_entry(root, info, data):
    """Добавить запись ZIP-архива в дерево VFS.

    :param root: корневой каталог VFS.
    :param info: описание записи архива (ZipInfo).
    :param data: содержимое записи в виде байтов.
    :raises VfsError: если путь небезопасен или имя уже занято.
    """
    parts = split_path(info.filename)
    if not parts:
        return
    mode = entry_mode(info)
    if info.is_dir():
        directory = make_directories(
            root, parts, info.filename, info.date_time
        )
        directory.mode = mode
        directory.mtime = info.date_time
        return
    directory = make_directories(
        root, parts[:-1], info.filename, info.date_time
    )
    name = parts[-1]
    if name in directory.children:
        raise VfsError(
            "повторяющийся путь в архиве: {0}".format(info.filename)
        )
    directory.children[name] = VfsFile(name, data, mode, info.date_time)


def build_tree(archive):
    """Построить дерево VFS по открытому ZIP-архиву.

    :param archive: открытый на чтение объект ZipFile.
    :return: корневой каталог VfsDirectory.
    """
    root = VfsDirectory(ROOT_NAME)
    for info in archive.infolist():
        data = b"" if info.is_dir() else archive.read(info)
        add_entry(root, info, data)
    return root


def load_vfs(path):
    """Загрузить VFS из ZIP-архива в память.

    :param path: путь к ZIP-архиву.
    :return: объект Vfs.
    :raises VfsError: если путь не задан, файл не найден или не
        читается, либо его формат неверен.
    """
    if not path:
        raise VfsError("путь к VFS не задан")
    try:
        with zipfile.ZipFile(path, "r") as archive:
            root = build_tree(archive)
    except FileNotFoundError as error:
        raise VfsError("файл не найден: {0}".format(path)) from error
    except OSError as error:
        raise VfsError(
            "не удалось прочитать {0}: {1}".format(path, error)
        ) from error
    except ARCHIVE_ERRORS as error:
        raise VfsError(
            "неверный формат архива {0}: {1}".format(path, error)
        ) from error
    return Vfs(path, root)


def format_summary(vfs):
    """Составить краткую сводку о загруженной VFS.

    :param vfs: объект Vfs.
    :return: строка с источником, числом каталогов и файлов.
    """
    stats = vfs.statistics()
    return "{0} (каталогов: {1}, файлов: {2})".format(
        vfs.source, stats.directories, stats.files
    )


def format_info(vfs):
    """Составить подробные сведения о загруженной VFS.

    :param vfs: объект Vfs.
    :return: многострочный текст со сведениями о VFS.
    """
    stats = vfs.statistics()
    lines = [
        "Источник VFS: {0}".format(vfs.source),
        "Каталогов: {0}".format(stats.directories),
        "Файлов: {0} (двоичных: {1})".format(stats.files, stats.binary),
        "Общий размер: {0} байт".format(stats.size),
        "Максимальная вложенность: {0}".format(stats.depth),
    ]
    return "\n".join(lines)


def node_label(node):
    """Получить подпись узла для показа в дереве.

    :param node: файл или каталог VFS.
    :return: имя узла; у каталога добавлен "/", у двоичного файла -
        пометка.
    """
    if isinstance(node, VfsDirectory):
        return node.name + SEPARATOR
    if node.binary:
        return node.name + BINARY_MARK
    return node.name


def render_tree(directory, prefix=""):
    """Нарисовать содержимое каталога в виде дерева.

    :param directory: каталог VfsDirectory.
    :param prefix: отступ, накопленный на верхних уровнях.
    :return: список строк дерева.
    """
    lines = []
    children = directory.sorted_children()
    for child in children:
        last = child is children[LAST_INDEX]
        branch = TREE_LAST if last else TREE_BRANCH
        lines.append(prefix + branch + node_label(child))
        if isinstance(child, VfsDirectory):
            shift = TREE_SPACE if last else TREE_PIPE
            lines.extend(render_tree(child, prefix + shift))
    return lines


def format_tree(vfs):
    """Составить дерево всей VFS.

    :param vfs: объект Vfs.
    :return: многострочный текст, первая строка которого - корень.
    """
    return "\n".join([ROOT_NAME] + render_tree(vfs.root))
