"""Тесты работы с путями VFS и сеансом."""

import unittest

from src.errors import CommandError
from src.paths import find_node, format_path, locate, normalize
from src.session import Session
from src.vfs import VfsDirectory, load_vfs
from tests.helpers import make_temp_directory, make_zip

ENTRIES = {"a/b/c.txt": b"c\n", "top.txt": b"t\n"}


class NormalizeTest(unittest.TestCase):
    """Проверка нормализации путей."""

    def test_absolute(self):
        """Абсолютный путь не зависит от текущего каталога."""
        self.assertEqual(normalize(["x"], "/a/b"), ["a", "b"])

    def test_relative(self):
        """Относительный путь отсчитывается от текущего каталога."""
        self.assertEqual(normalize(["a"], "b/c"), ["a", "b", "c"])

    def test_dots(self):
        """Части "." и лишние слэши игнорируются."""
        self.assertEqual(normalize([], "./a//b/."), ["a", "b"])

    def test_parent(self):
        """Часть ".." поднимает на уровень выше."""
        self.assertEqual(normalize(["a", "b"], "../c"), ["a", "c"])

    def test_parent_of_root(self):
        """Выше корня подняться нельзя."""
        self.assertEqual(normalize([], "../.."), [])

    def test_root(self):
        """Путь "/" даёт корень."""
        self.assertEqual(normalize(["a"], "/"), [])

    def test_format_path(self):
        """Путь собирается обратно в строку."""
        self.assertEqual(format_path(["a", "b"]), "/a/b")
        self.assertEqual(format_path([]), "/")


class LocateTest(unittest.TestCase):
    """Проверка поиска узлов и работы сеанса."""

    def setUp(self):
        """Создать сеанс с VFS."""
        directory = make_temp_directory(self)
        self.vfs = load_vfs(make_zip(directory, "t.zip", ENTRIES))
        self.session = Session(self.vfs)

    def test_find_node(self):
        """Существующий узел находится, несуществующий - нет."""
        self.assertIsNotNone(find_node(self.vfs.root, ["a", "b", "c.txt"]))
        self.assertIsNone(find_node(self.vfs.root, ["a", "nope"]))

    def test_find_through_file(self):
        """Путь через файл не существует."""
        self.assertIsNone(find_node(self.vfs.root, ["top.txt", "x"]))

    def test_locate_relative(self):
        """Поиск учитывает текущий каталог сеанса."""
        self.session.cwd = ["a"]
        target = locate("ls", self.session, "b")
        self.assertEqual(target.parts, ["a", "b"])
        self.assertIsInstance(target.node, VfsDirectory)

    def test_locate_missing(self):
        """Отсутствующий путь приводит к ошибке с именем команды."""
        with self.assertRaises(CommandError) as context:
            locate("cat", self.session, "zzz")
        self.assertEqual(
            str(context.exception),
            "cat: zzz: нет такого файла или каталога",
        )


class SessionTest(unittest.TestCase):
    """Проверка состояния сеанса."""

    def test_empty_session(self):
        """Без VFS корень пуст, текущий каталог - корень."""
        session = Session()
        self.assertEqual(session.root.children, {})
        self.assertEqual(session.cwd_path(), "/")

    def test_attach_resets_directory(self):
        """Подключение VFS возвращает в корень."""
        directory = make_temp_directory(self)
        vfs = load_vfs(make_zip(directory, "t.zip", ENTRIES))
        session = Session()
        session.cwd = ["old"]
        session.attach(vfs)
        self.assertEqual(session.cwd, [])
        self.assertIs(session.root, vfs.root)

    def test_cwd_path(self):
        """Текущий каталог выводится абсолютным путём."""
        session = Session()
        session.cwd = ["home", "user"]
        self.assertEqual(session.cwd_path(), "/home/user")


if __name__ == "__main__":
    unittest.main()
