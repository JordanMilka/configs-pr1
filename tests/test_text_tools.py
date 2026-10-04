"""Тесты команд cat и uniq."""

import base64
import unittest

from src.commands import execute
from src.errors import CommandError
from src.session import Session
from src.vfs import load_vfs
from tests.helpers import make_temp_directory, make_unix_zip

BINARY = bytes([0, 1, 2, 255])
RECORDS = {
    "docs/": (b"", 0o755),
    "docs/one.txt": (b"one\ntwo\n", 0o644),
    "docs/two.txt": (b"three\n", 0o644),
    "docs/nonl.txt": (b"no newline", 0o644),
    "docs/blank.txt": (b"a\n\nb\n", 0o644),
    "docs/words.txt": (
        b"apple\napple\nApple\nbanana\ncherry\ncherry\ncherry\napple\n",
        0o644,
    ),
    "docs/empty.txt": (b"", 0o644),
    "bin.dat": (BINARY, 0o644),
}


class TextToolsTestCase(unittest.TestCase):
    """Общая подготовка: сеанс с VFS и вызов команд."""

    def setUp(self):
        """Создать сеанс с VFS."""
        directory = make_temp_directory(self)
        path = make_unix_zip(directory, "t.zip", RECORDS)
        self.session = Session(load_vfs(path))

    def run_command(self, *tokens):
        """Выполнить команду и вернуть её вывод."""
        return execute(list(tokens), self.session)

    def assert_error(self, expected, *tokens):
        """Проверить, что команда завершается ошибкой с текстом."""
        with self.assertRaises(CommandError) as context:
            execute(list(tokens), self.session)
        self.assertEqual(str(context.exception), expected)


class CatTest(TextToolsTestCase):
    """Проверка команды cat."""

    def test_single_file(self):
        """Выводится содержимое файла без лишнего перевода строки."""
        self.assertEqual(self.run_command("cat", "docs/one.txt"), "one\ntwo")

    def test_several_files(self):
        """Файлы склеиваются в порядке аргументов."""
        self.assertEqual(
            self.run_command("cat", "docs/one.txt", "docs/two.txt"),
            "one\ntwo\nthree",
        )

    def test_file_without_trailing_newline(self):
        """Файл без перевода строки склеивается со следующим."""
        self.assertEqual(
            self.run_command("cat", "docs/nonl.txt", "docs/two.txt"),
            "no newlinethree",
        )

    def test_relative_path(self):
        """Файл ищется относительно текущего каталога."""
        self.run_command("cd", "docs")
        self.assertEqual(self.run_command("cat", "two.txt"), "three")

    def test_number_lines(self):
        """Ключ -n нумерует строки, включая пустые."""
        self.assertEqual(
            self.run_command("cat", "-n", "docs/blank.txt"),
            "     1\ta\n     2\t\n     3\tb",
        )

    def test_number_continues_across_files(self):
        """Нумерация продолжается в следующем файле."""
        text = self.run_command("cat", "-n", "docs/one.txt", "docs/two.txt")
        self.assertTrue(text.endswith("     3\tthree"))

    def test_binary_file_is_base64(self):
        """Двоичный файл выводится в виде base64."""
        expected = base64.b64encode(BINARY).decode("ascii")
        self.assertEqual(self.run_command("cat", "bin.dat"), expected)

    def test_empty_file(self):
        """Пустой файл даёт пустой вывод."""
        self.assertEqual(self.run_command("cat", "docs/empty.txt"), "")

    def test_no_arguments(self):
        """Без файла команда сообщает об ошибке."""
        self.assert_error("cat: не указан файл", "cat")

    def test_missing_file(self):
        """Несуществующий файл приводит к ошибке."""
        self.assert_error(
            "cat: nope.txt: нет такого файла или каталога", "cat", "nope.txt"
        )

    def test_missing_among_several(self):
        """Ошибка в одном из файлов отменяет весь вывод."""
        self.assert_error(
            "cat: nope.txt: нет такого файла или каталога",
            "cat", "docs/one.txt", "nope.txt",
        )

    def test_directory(self):
        """Каталог выводить нельзя."""
        self.assert_error("cat: docs: является каталогом", "cat", "docs")

    def test_unknown_option(self):
        """Неизвестный ключ приводит к ошибке."""
        self.assert_error("cat: неверный ключ -- 'x'", "cat", "-x", "a")


class UniqTest(TextToolsTestCase):
    """Проверка команды uniq."""

    def test_default(self):
        """Подряд идущие повторы схлопываются, далёкие остаются."""
        expected = "apple\nApple\nbanana\ncherry\napple"
        self.assertEqual(self.run_command("uniq", "docs/words.txt"), expected)

    def test_count(self):
        """Ключ -c добавляет число повторов."""
        expected = "\n".join([
            "      2 apple",
            "      1 Apple",
            "      1 banana",
            "      3 cherry",
            "      1 apple",
        ])
        self.assertEqual(
            self.run_command("uniq", "-c", "docs/words.txt"), expected
        )

    def test_duplicates(self):
        """Ключ -d оставляет только повторяющиеся строки."""
        self.assertEqual(
            self.run_command("uniq", "-d", "docs/words.txt"),
            "apple\ncherry",
        )

    def test_unique(self):
        """Ключ -u оставляет только неповторяющиеся строки."""
        self.assertEqual(
            self.run_command("uniq", "-u", "docs/words.txt"),
            "Apple\nbanana\napple",
        )

    def test_ignore_case(self):
        """Ключ -i не различает регистр."""
        self.assertEqual(
            self.run_command("uniq", "-i", "docs/words.txt"),
            "apple\nbanana\ncherry\napple",
        )

    def test_combined_flags(self):
        """Ключи можно объединять."""
        expected = "\n".join([
            "      3 apple",
            "      1 banana",
            "      3 cherry",
            "      1 apple",
        ])
        self.assertEqual(
            self.run_command("uniq", "-ci", "docs/words.txt"), expected
        )

    def test_count_and_duplicates(self):
        """Ключи -c и -d работают вместе."""
        expected = "      2 apple\n      3 cherry"
        self.assertEqual(
            self.run_command("uniq", "-c", "-d", "docs/words.txt"), expected
        )

    def test_empty_file(self):
        """Пустой файл даёт пустой вывод."""
        self.assertEqual(self.run_command("uniq", "docs/empty.txt"), "")

    def test_no_arguments(self):
        """Без файла команда сообщает об ошибке."""
        self.assert_error("uniq: не указан файл", "uniq")
        self.assert_error("uniq: не указан файл", "uniq", "-c")

    def test_extra_operand(self):
        """Второй операнд не поддерживается."""
        self.assert_error(
            "uniq: лишний операнд 'b'", "uniq", "docs/one.txt", "b"
        )

    def test_missing_file(self):
        """Несуществующий файл приводит к ошибке."""
        self.assert_error(
            "uniq: x: нет такого файла или каталога", "uniq", "x"
        )

    def test_directory(self):
        """Каталог обработать нельзя."""
        self.assert_error("uniq: docs: является каталогом", "uniq", "docs")

    def test_binary_file(self):
        """Двоичный файл обработать нельзя."""
        self.assert_error("uniq: bin.dat: двоичный файл", "uniq", "bin.dat")

    def test_conflicting_flags(self):
        """Ключи -d и -u несовместимы."""
        self.assert_error(
            "uniq: ключи -d и -u несовместимы",
            "uniq", "-d", "-u", "docs/words.txt",
        )

    def test_unknown_option(self):
        """Неизвестный ключ приводит к ошибке."""
        self.assert_error(
            "uniq: неверный ключ -- 'x'", "uniq", "-x", "docs/words.txt"
        )


if __name__ == "__main__":
    unittest.main()
