"""Тесты команд chown и rm."""

import os
import unittest

from src.commands import execute
from src.errors import CommandError
from src.modification import is_valid_name, parse_owner
from src.session import Session
from src.vfs import load_vfs
from tests.helpers import make_temp_directory, make_unix_zip

RECORDS = {
    "docs/": (b"", 0o755),
    "docs/a.txt": (b"a\n", 0o644),
    "docs/b.txt": (b"b\n", 0o644),
    "docs/deep/": (b"", 0o755),
    "docs/deep/c.txt": (b"c\n", 0o644),
    "empty/": (b"", 0o755),
    "top.txt": (b"t\n", 0o644),
}


class ModificationTestCase(unittest.TestCase):
    """Общая подготовка: сеанс с VFS и вызов команд."""

    def setUp(self):
        """Создать архив, сеанс с VFS и сеанс без неё."""
        directory = make_temp_directory(self)
        self.path = make_unix_zip(directory, "t.zip", RECORDS)
        self.session = Session(load_vfs(self.path))

    def run_command(self, *tokens):
        """Выполнить команду и вернуть её вывод."""
        return execute(list(tokens), self.session)

    def assert_error(self, expected, *tokens):
        """Проверить, что команда завершается ошибкой с текстом."""
        with self.assertRaises(CommandError) as context:
            execute(list(tokens), self.session)
        self.assertEqual(str(context.exception), expected)

    def owner_of(self, label):
        """Получить пару (владелец, группа) узла по пути."""
        node = self.find(label)
        return (node.owner, node.group)

    def find(self, label):
        """Найти узел VFS по абсолютному пути."""
        node = self.session.root
        for part in label.strip("/").split("/"):
            if part:
                node = node.children[part]
        return node

    def exists(self, label):
        """Проверить, что узел с таким абсолютным путём существует."""
        try:
            self.find(label)
        except KeyError:
            return False
        return True


class ParseOwnerTest(unittest.TestCase):
    """Проверка разбора записи владельца."""

    def test_owner_only(self):
        """Запись "имя" задаёт только владельца."""
        self.assertEqual(parse_owner("bob"), ("bob", None))

    def test_owner_and_group(self):
        """Запись "имя:группа" задаёт обе части."""
        self.assertEqual(parse_owner("bob:staff"), ("bob", "staff"))

    def test_group_only(self):
        """Запись ":группа" задаёт только группу."""
        self.assertEqual(parse_owner(":staff"), (None, "staff"))

    def test_invalid_specs(self):
        """Неверные записи отклоняются."""
        for spec in ("bob:", ":", "1bob", "b ob", "a:b:c", "bo$b"):
            with self.subTest(spec=spec):
                with self.assertRaises(CommandError):
                    parse_owner(spec)

    def test_is_valid_name(self):
        """Допустимы буквы, цифры, "_" и "-" после первой буквы."""
        self.assertTrue(is_valid_name("user_1-a"))
        self.assertTrue(is_valid_name("_svc"))
        self.assertFalse(is_valid_name("-x"))
        self.assertFalse(is_valid_name(""))


class ChownTest(ModificationTestCase):
    """Проверка команды chown."""

    def test_owner(self):
        """Смена только владельца."""
        self.assertEqual(self.run_command("chown", "bob", "top.txt"), "")
        self.assertEqual(self.owner_of("/top.txt"), ("bob", "root"))

    def test_owner_and_group(self):
        """Смена владельца и группы."""
        self.run_command("chown", "bob:staff", "top.txt")
        self.assertEqual(self.owner_of("/top.txt"), ("bob", "staff"))

    def test_group_only(self):
        """Смена только группы."""
        self.run_command("chown", ":staff", "top.txt")
        self.assertEqual(self.owner_of("/top.txt"), ("root", "staff"))

    def test_several_files(self):
        """Владелец меняется у всех указанных файлов."""
        self.run_command("chown", "bob", "top.txt", "docs/a.txt")
        self.assertEqual(self.owner_of("/top.txt")[0], "bob")
        self.assertEqual(self.owner_of("/docs/a.txt")[0], "bob")

    def test_directory_without_recursion(self):
        """Без -R меняется только сам каталог."""
        self.run_command("chown", "bob", "docs")
        self.assertEqual(self.owner_of("/docs")[0], "bob")
        self.assertEqual(self.owner_of("/docs/a.txt")[0], "root")

    def test_recursive(self):
        """С -R меняется всё содержимое каталога."""
        self.run_command("chown", "-R", "bob:staff", "docs")
        for label in ("/docs", "/docs/a.txt", "/docs/deep/c.txt"):
            self.assertEqual(self.owner_of(label), ("bob", "staff"))
        self.assertEqual(self.owner_of("/top.txt"), ("root", "root"))

    def test_root_directory(self):
        """Владельца корня тоже можно сменить."""
        self.run_command("chown", "bob", "/")
        self.assertEqual(self.owner_of("/")[0], "bob")

    def test_relative_path(self):
        """Путь отсчитывается от текущего каталога."""
        self.run_command("cd", "docs")
        self.run_command("chown", "bob", "a.txt")
        self.assertEqual(self.owner_of("/docs/a.txt")[0], "bob")

    def test_listing_shows_new_owner(self):
        """Новый владелец виден в ls -l."""
        self.run_command("chown", "alice:dev", "top.txt")
        self.assertIn("alice dev", self.run_command("ls", "-l", "top.txt"))

    def test_no_operands(self):
        """Без операндов команда сообщает об ошибке."""
        self.assert_error("chown: не указан владелец", "chown")
        self.assert_error("chown: не указан владелец", "chown", "-R")

    def test_no_file(self):
        """Без файла команда сообщает об ошибке."""
        self.assert_error("chown: не указан файл после 'bob'", "chown", "bob")

    def test_invalid_owner(self):
        """Неверная запись владельца приводит к ошибке."""
        self.assert_error(
            "chown: неверный владелец или группа: 'bob:'",
            "chown", "bob:", "top.txt",
        )

    def test_missing_file_changes_nothing(self):
        """Ошибка в одном из путей отменяет все изменения."""
        self.assert_error(
            "chown: nope: нет такого файла или каталога",
            "chown", "bob", "top.txt", "nope",
        )
        self.assertEqual(self.owner_of("/top.txt")[0], "root")

    def test_unknown_option(self):
        """Неизвестный ключ приводит к ошибке."""
        self.assert_error(
            "chown: неверный ключ -- 'x'", "chown", "-x", "bob", "top.txt"
        )


class RmTest(ModificationTestCase):
    """Проверка команды rm."""

    def test_remove_file(self):
        """Файл удаляется, остальные остаются."""
        self.assertEqual(self.run_command("rm", "top.txt"), "")
        self.assertFalse(self.exists("/top.txt"))
        self.assertTrue(self.exists("/docs/a.txt"))

    def test_remove_several_files(self):
        """Удаляются все указанные файлы."""
        self.run_command("rm", "docs/a.txt", "docs/b.txt")
        self.assertFalse(self.exists("/docs/a.txt"))
        self.assertFalse(self.exists("/docs/b.txt"))

    def test_remove_relative(self):
        """Путь отсчитывается от текущего каталога."""
        self.run_command("cd", "docs")
        self.run_command("rm", "a.txt", "deep/c.txt")
        self.assertFalse(self.exists("/docs/a.txt"))
        self.assertFalse(self.exists("/docs/deep/c.txt"))

    def test_remove_directory_recursively(self):
        """С -r каталог удаляется вместе с содержимым."""
        self.run_command("rm", "-r", "docs")
        self.assertFalse(self.exists("/docs"))
        self.assertTrue(self.exists("/top.txt"))

    def test_remove_empty_directory(self):
        """Пустой каталог тоже удаляется с ключом -r."""
        self.run_command("rm", "-r", "empty")
        self.assertFalse(self.exists("/empty"))

    def test_directory_without_recursion(self):
        """Без -r каталог удалить нельзя."""
        self.assert_error(
            "rm: невозможно удалить 'docs': это каталог", "rm", "docs"
        )
        self.assertTrue(self.exists("/docs"))

    def test_force_ignores_missing(self):
        """С -f несуществующие пути не считаются ошибкой."""
        self.assertEqual(self.run_command("rm", "-f", "nope", "top.txt"), "")
        self.assertFalse(self.exists("/top.txt"))

    def test_force_without_operands(self):
        """Команда rm -f без операндов ничего не делает."""
        self.assertEqual(self.run_command("rm", "-f"), "")

    def test_force_does_not_remove_directories(self):
        """Ключ -f не отменяет запрет на удаление каталогов."""
        self.assert_error(
            "rm: невозможно удалить 'docs': это каталог", "rm", "-f", "docs"
        )

    def test_verbose(self):
        """Ключ -v сообщает об удалённых файлах и каталогах."""
        text = self.run_command("rm", "-rv", "top.txt", "docs")
        self.assertEqual(text, "удалён 'top.txt'\nудалён каталог 'docs'")

    def test_combined_flags(self):
        """Ключи можно объединять."""
        self.assertEqual(self.run_command("rm", "-rf", "docs", "nope"), "")
        self.assertFalse(self.exists("/docs"))

    def test_duplicate_and_nested_operands(self):
        """Повторы и вложенные пути удаляются без ошибок."""
        text = self.run_command(
            "rm", "-rv", "docs", "docs", "docs/a.txt", "docs/deep"
        )
        self.assertEqual(text, "удалён каталог 'docs'")
        self.assertFalse(self.exists("/docs"))

    def test_missing_file(self):
        """Несуществующий путь приводит к ошибке."""
        self.assert_error(
            "rm: nope: нет такого файла или каталога", "rm", "nope"
        )

    def test_missing_changes_nothing(self):
        """Ошибка в одном из путей отменяет все удаления."""
        self.assert_error(
            "rm: nope: нет такого файла или каталога",
            "rm", "top.txt", "nope",
        )
        self.assertTrue(self.exists("/top.txt"))

    def test_no_operands(self):
        """Без операндов команда сообщает об ошибке."""
        self.assert_error("rm: пропущен операнд", "rm")
        self.assert_error("rm: пропущен операнд", "rm", "-r")

    def test_root_is_protected(self):
        """Корень удалить нельзя."""
        self.assert_error(
            "rm: невозможно удалить '/': это корневой каталог",
            "rm", "-r", "/",
        )
        self.assertTrue(self.exists("/docs"))

    def test_dot_entries_are_protected(self):
        """Удалять "." и ".." нельзя."""
        self.run_command("cd", "docs")
        for label in (".", "..", "./", "deep/."):
            with self.subTest(label=label):
                self.assert_error(
                    "rm: невозможно удалить '{0}': нельзя удалять '.' и '..'"
                    .format(label),
                    "rm", "-r", label,
                )

    def test_current_directory_is_protected(self):
        """Нельзя удалить каталог, в котором находится сеанс."""
        self.run_command("cd", "docs/deep")
        message = (
            "rm: невозможно удалить '/docs': это текущий каталог "
            "или содержит его"
        )
        self.assert_error(message, "rm", "-r", "/docs")
        self.assertTrue(self.exists("/docs/deep"))

    def test_unknown_option(self):
        """Неизвестный ключ приводит к ошибке."""
        self.assert_error("rm: неверный ключ -- 'x'", "rm", "-x", "top.txt")

    def test_without_vfs(self):
        """Без VFS удалять нечего, а с -f ошибки нет."""
        empty = Session()
        with self.assertRaises(CommandError):
            execute(["rm", "x"], empty)
        self.assertEqual(execute(["rm", "-f", "x"], empty), "")


class MemoryOnlyTest(ModificationTestCase):
    """Проверка того, что архив на диске не изменяется."""

    def test_archive_is_untouched(self):
        """После chown и rm архив остаётся прежним."""
        with open(self.path, "rb") as source:
            before = source.read()
        self.run_command("chown", "-R", "bob:staff", "/")
        self.run_command("rm", "-r", "docs", "empty")
        with open(self.path, "rb") as source:
            self.assertEqual(source.read(), before)
        self.assertEqual(os.listdir(os.path.dirname(self.path)), ["t.zip"])

    def test_reload_restores_vfs(self):
        """Повторная загрузка архива даёт исходную VFS."""
        self.run_command("rm", "-r", "docs")
        reloaded = Session(load_vfs(self.path))
        self.assertIn("docs", execute(["ls"], reloaded))

    def test_vfs_info_reflects_changes(self):
        """vfs-info показывает состояние VFS после удаления."""
        self.run_command("rm", "-r", "docs", "empty")
        self.assertIn("Каталогов: 0", self.run_command("vfs-info"))
        self.assertIn("Файлов: 1 ", self.run_command("vfs-info"))


if __name__ == "__main__":
    unittest.main()
