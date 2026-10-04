"""Тесты команд ls и cd."""

import unittest

from src.commands import execute
from src.errors import CommandError
from src.session import Session
from src.vfs import load_vfs
from tests.helpers import make_temp_directory, make_unix_zip

RECORDS = {
    "docs/": (b"", 0o755),
    "docs/a.txt": (b"aaa\n", 0o644),
    "docs/.hidden": (b"h", 0o600),
    "docs/big.txt": (b"0123456789ab\n", 0o644),
    "docs/deep/": (b"", 0o755),
    "docs/deep/b.txt": (b"b\n", 0o640),
    "empty/": (b"", 0o700),
    "data.bin": (bytes([0, 255, 1]), 0o644),
    "Zeta.txt": (b"z\n", 0o644),
    "alpha.txt": (b"alpha\n", 0o444),
}


class NavigationTestCase(unittest.TestCase):
    """Общая подготовка: сеанс с VFS и вызов команд."""

    def setUp(self):
        """Создать сеанс с VFS и сеанс без неё."""
        directory = make_temp_directory(self)
        path = make_unix_zip(directory, "t.zip", RECORDS)
        self.session = Session(load_vfs(path))
        self.empty_session = Session()

    def run_command(self, *tokens):
        """Выполнить команду в сеансе с VFS и вернуть её вывод."""
        return execute(list(tokens), self.session)

    def assert_error(self, expected, *tokens):
        """Проверить, что команда завершается ошибкой с текстом."""
        with self.assertRaises(CommandError) as context:
            execute(list(tokens), self.session)
        self.assertEqual(str(context.exception), expected)


class LsTest(NavigationTestCase):
    """Проверка команды ls."""

    def test_root(self):
        """Без аргументов показывается текущий каталог."""
        self.assertEqual(
            self.run_command("ls"),
            "alpha.txt  data.bin  docs  empty  Zeta.txt",
        )

    def test_directory_argument(self):
        """С аргументом показывается указанный каталог."""
        self.assertEqual(
            self.run_command("ls", "docs"), "a.txt  big.txt  deep"
        )

    def test_hidden_files(self):
        """Скрытые имена показываются только с ключом -a."""
        self.assertNotIn(".hidden", self.run_command("ls", "docs"))
        self.assertEqual(
            self.run_command("ls", "-a", "docs"),
            ".  ..  .hidden  a.txt  big.txt  deep",
        )

    def test_dot_entries_in_root(self):
        """В корне ".." показывает тот же корень."""
        text = self.run_command("ls", "-la", "/")
        self.assertEqual(text.splitlines()[1].split()[-1], "..")

    def test_long_format(self):
        """Ключ -l показывает права, владельца, размер и время."""
        expected = "\n".join([
            "-r--r--r-- root root 6 2026-01-15 10:30 alpha.txt",
            "-rw-r--r-- root root 3 2026-01-15 10:30 data.bin",
            "drwxr-xr-x root root 0 2026-01-15 10:30 docs",
            "drwx------ root root 0 2026-01-15 10:30 empty",
            "-rw-r--r-- root root 2 2026-01-15 10:30 Zeta.txt",
        ])
        self.assertEqual(self.run_command("ls", "-l"), expected)

    def test_long_format_alignment(self):
        """В подробном списке размеры выровнены по правому краю."""
        text = self.run_command("ls", "-l", "docs")
        self.assertIn("root root  4 2026-01-15 10:30 a.txt", text)
        self.assertIn("root root 13 2026-01-15 10:30 big.txt", text)
        self.assertIn("root root  0 2026-01-15 10:30 deep", text)

    def test_file_argument(self):
        """Для файла выводится его имя."""
        self.assertEqual(self.run_command("ls", "docs/a.txt"), "docs/a.txt")

    def test_file_long(self):
        """Для файла с ключом -l выводится строка со сведениями."""
        text = self.run_command("ls", "-l", "docs/a.txt")
        self.assertTrue(text.startswith("-rw-r--r-- root root 4 "))

    def test_several_operands(self):
        """Несколько каталогов выводятся с заголовками."""
        expected = "docs:\na.txt  big.txt  deep\n\nempty:"
        self.assertEqual(self.run_command("ls", "docs", "empty"), expected)

    def test_files_and_directories(self):
        """Файлы выводятся списком до каталогов с заголовками."""
        expected = "data.bin\n\nempty:"
        self.assertEqual(self.run_command("ls", "empty", "data.bin"), expected)

    def test_empty_directory(self):
        """Пустой каталог даёт пустой вывод."""
        self.assertEqual(self.run_command("ls", "empty"), "")

    def test_relative_to_current_directory(self):
        """Относительные пути отсчитываются от текущего каталога."""
        self.run_command("cd", "docs")
        self.assertEqual(self.run_command("ls"), "a.txt  big.txt  deep")
        self.assertEqual(self.run_command("ls", "deep"), "b.txt")
        self.assertEqual(self.run_command("ls", ".."), (
            "alpha.txt  data.bin  docs  empty  Zeta.txt"))

    def test_missing_path(self):
        """Несуществующий путь приводит к ошибке."""
        self.assert_error(
            "ls: nope: нет такого файла или каталога", "ls", "nope"
        )

    def test_missing_among_several(self):
        """Ошибка в одном из операндов отменяет весь вывод."""
        self.assert_error(
            "ls: nope: нет такого файла или каталога", "ls", "docs", "nope"
        )

    def test_unknown_option(self):
        """Неизвестный ключ приводит к ошибке."""
        self.assert_error("ls: неверный ключ -- 'z'", "ls", "-z")

    def test_without_vfs(self):
        """Без VFS корень пуст."""
        self.assertEqual(execute(["ls"], self.empty_session), "")
        with self.assertRaises(CommandError):
            execute(["ls", "docs"], self.empty_session)


class CdTest(NavigationTestCase):
    """Проверка команды cd."""

    def test_absolute_path(self):
        """Переход по абсолютному пути."""
        self.assertEqual(self.run_command("cd", "/docs/deep"), "")
        self.assertEqual(self.session.cwd_path(), "/docs/deep")

    def test_relative_path(self):
        """Переход по относительному пути."""
        self.run_command("cd", "docs")
        self.run_command("cd", "deep")
        self.assertEqual(self.session.cwd_path(), "/docs/deep")

    def test_parent(self):
        """Переход на уровень выше."""
        self.run_command("cd", "docs/deep")
        self.run_command("cd", "../..")
        self.assertEqual(self.session.cwd_path(), "/")

    def test_parent_of_root(self):
        """Из корня подняться выше нельзя, но ошибки нет."""
        self.run_command("cd", "..")
        self.assertEqual(self.session.cwd_path(), "/")

    def test_without_arguments(self):
        """Без аргументов cd переходит в корень."""
        self.run_command("cd", "docs")
        self.run_command("cd")
        self.assertEqual(self.session.cwd_path(), "/")

    def test_missing_directory(self):
        """Несуществующий каталог приводит к ошибке."""
        self.assert_error(
            "cd: nope: нет такого файла или каталога", "cd", "nope"
        )
        self.assertEqual(self.session.cwd_path(), "/")

    def test_file_is_not_directory(self):
        """Переход в файл приводит к ошибке."""
        self.assert_error(
            "cd: data.bin: не является каталогом", "cd", "data.bin"
        )

    def test_too_many_arguments(self):
        """Больше одного аргумента приводит к ошибке."""
        self.assert_error("cd: слишком много аргументов", "cd", "a", "b")

    def test_without_vfs(self):
        """Без VFS можно перейти только в корень."""
        self.assertEqual(execute(["cd", "/"], self.empty_session), "")
        with self.assertRaises(CommandError):
            execute(["cd", "docs"], self.empty_session)


if __name__ == "__main__":
    unittest.main()
