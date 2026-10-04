"""Состояние сеанса работы эмулятора."""

from src.paths import format_path
from src.vfs import ROOT_NAME, VfsDirectory


class Session:
    """Состояние одного сеанса: подключённая VFS и текущий каталог.

    Объект передаётся обработчикам команд. Если VFS не подключена,
    корневой каталог считается пустым.
    """

    def __init__(self, vfs=None):
        """Создать сеанс.

        :param vfs: объект Vfs или None, если VFS не подключена.
        """
        self.vfs = None
        self.cwd = []
        self.empty_root = VfsDirectory(ROOT_NAME)
        if vfs is not None:
            self.attach(vfs)

    @property
    def root(self):
        """Корневой каталог: из VFS или пустой, если VFS нет."""
        if self.vfs is None:
            return self.empty_root
        return self.vfs.root

    def attach(self, vfs):
        """Подключить VFS и перейти в её корень.

        :param vfs: объект Vfs.
        """
        self.vfs = vfs
        self.cwd = []

    def cwd_path(self):
        """Получить абсолютный путь текущего каталога.

        :return: строка вида "/home/user"; для корня - "/".
        """
        return format_path(self.cwd)
