"""Тесты разбора параметров командной строки."""

import unittest

from src.config import NOT_SET, format_config, parse_arguments


class ParseArgumentsTest(unittest.TestCase):
    """Проверка разбора параметров командной строки."""

    def test_without_arguments(self):
        """Без параметров оба пути остаются незаданными."""
        config = parse_arguments([])
        self.assertIsNone(config.vfs_path)
        self.assertIsNone(config.script_path)

    def test_vfs_path(self):
        """Параметр --vfs сохраняет путь к VFS."""
        config = parse_arguments(["--vfs", "data/vfs.zip"])
        self.assertEqual(config.vfs_path, "data/vfs.zip")

    def test_script_path(self):
        """Параметр --script сохраняет путь к стартовому скрипту."""
        config = parse_arguments(["--script", "start.txt"])
        self.assertEqual(config.script_path, "start.txt")

    def test_both_paths(self):
        """Оба параметра могут быть заданы одновременно."""
        config = parse_arguments(
            ["--vfs", "data/vfs.zip", "--script", "start.txt"]
        )
        self.assertEqual(config.vfs_path, "data/vfs.zip")
        self.assertEqual(config.script_path, "start.txt")


class FormatConfigTest(unittest.TestCase):
    """Проверка отладочного вывода параметров запуска."""

    def test_values_are_shown(self):
        """Заданные параметры попадают в отладочный вывод."""
        text = format_config(parse_arguments(["--vfs", "data/vfs.zip"]))
        self.assertIn("data/vfs.zip", text)

    def test_missing_value(self):
        """Незаданный параметр помечается специальным текстом."""
        text = format_config(parse_arguments([]))
        self.assertIn(NOT_SET, text)


if __name__ == "__main__":
    unittest.main()
