"""Тесты команд эмулятора командной оболочки."""

import unittest

from src.commands import CommandError, ExitRequested, execute
from src.session import Session
from src.vfs import load_vfs
from tests.helpers import make_temp_directory, make_zip

ENTRIES = {"docs/a.txt": b"a\n", "image.bin": bytes([0, 255])}


class ExecuteTest(unittest.TestCase):
    """Проверка выполнения команд-заглушек и exit."""

    def setUp(self):
        """Создать сеанс без VFS."""
        self.session = Session()

    def test_ls_without_arguments(self):
        """Команда ls без аргументов сообщает об их отсутствии."""
        self.assertEqual(
            execute(["ls"], self.session), "ls: аргументы отсутствуют"
        )

    def test_ls_with_arguments(self):
        """Команда ls выводит своё имя и аргументы."""
        self.assertEqual(
            execute(["ls", "-l", "/tmp"], self.session),
            "ls: -l /tmp",
        )

    def test_cd_with_one_argument(self):
        """Команда cd принимает один аргумент."""
        self.assertEqual(
            execute(["cd", "/home"], self.session), "cd: /home"
        )

    def test_cd_with_two_arguments(self):
        """Команда cd сообщает об избыточных аргументах."""
        with self.assertRaises(CommandError):
            execute(["cd", "a", "b"], self.session)

    def test_unknown_command(self):
        """Неизвестная команда приводит к ошибке."""
        with self.assertRaises(CommandError):
            execute(["unknown"], self.session)

    def test_exit(self):
        """Команда exit запрашивает завершение работы."""
        with self.assertRaises(ExitRequested):
            execute(["exit"], self.session)

    def test_exit_with_argument(self):
        """Команда exit не принимает аргументов."""
        with self.assertRaises(CommandError):
            execute(["exit", "now"], self.session)


class VfsCommandsTest(unittest.TestCase):
    """Проверка служебных команд vfs-info и vfs-tree."""

    def setUp(self):
        """Создать сеансы с VFS и без неё."""
        directory = make_temp_directory(self)
        path = make_zip(directory, "t.zip", ENTRIES)
        self.session = Session(load_vfs(path))
        self.empty_session = Session()

    def test_vfs_info(self):
        """Команда vfs-info показывает сведения о VFS."""
        text = execute(["vfs-info"], self.session)
        self.assertIn("Каталогов: 1", text)
        self.assertIn("Файлов: 2 (двоичных: 1)", text)

    def test_vfs_tree(self):
        """Команда vfs-tree показывает дерево VFS."""
        expected = "/\n├── docs/\n│   └── a.txt\n└── image.bin [двоичный]"
        self.assertEqual(execute(["vfs-tree"], self.session), expected)

    def test_vfs_info_with_arguments(self):
        """Команда vfs-info не принимает аргументов."""
        with self.assertRaises(CommandError):
            execute(["vfs-info", "x"], self.session)

    def test_vfs_tree_with_arguments(self):
        """Команда vfs-tree не принимает аргументов."""
        with self.assertRaises(CommandError):
            execute(["vfs-tree", "x"], self.session)

    def test_vfs_info_without_vfs(self):
        """Без VFS команда vfs-info сообщает об ошибке."""
        with self.assertRaises(CommandError) as context:
            execute(["vfs-info"], self.empty_session)
        self.assertIn("--vfs", str(context.exception))

    def test_vfs_tree_without_vfs(self):
        """Без VFS команда vfs-tree сообщает об ошибке."""
        with self.assertRaises(CommandError):
            execute(["vfs-tree"], self.empty_session)


if __name__ == "__main__":
    unittest.main()
