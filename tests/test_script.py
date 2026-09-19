"""Тесты чтения стартового скрипта эмулятора."""

import os
import tempfile
import unittest

from src.script import ScriptError, is_executable_line, read_script_lines

SCRIPT_TEXT = "# комментарий\nls\n\ncd $HOME\n"
EXPECTED_LINES = 4


class ReadScriptLinesTest(unittest.TestCase):
    """Проверка чтения файла стартового скрипта."""

    def setUp(self):
        """Создать временный файл стартового скрипта."""
        handle, self.path = tempfile.mkstemp(suffix=".txt")
        os.close(handle)
        with open(self.path, "w", encoding="utf-8") as script_file:
            script_file.write(SCRIPT_TEXT)

    def tearDown(self):
        """Удалить временный файл стартового скрипта."""
        os.remove(self.path)

    def test_lines_are_read(self):
        """Все строки файла попадают в результат."""
        self.assertEqual(len(read_script_lines(self.path)), EXPECTED_LINES)

    def test_missing_file(self):
        """Отсутствующий файл приводит к ошибке скрипта."""
        with self.assertRaises(ScriptError):
            read_script_lines(self.path + ".none")


class IsExecutableLineTest(unittest.TestCase):
    """Проверка отбора строк скрипта для выполнения."""

    def test_command(self):
        """Строка с командой выполняется."""
        self.assertTrue(is_executable_line("ls -l"))

    def test_empty_line(self):
        """Пустая строка пропускается."""
        self.assertFalse(is_executable_line("   "))

    def test_comment(self):
        """Строка-комментарий пропускается."""
        self.assertFalse(is_executable_line("  # описание"))


if __name__ == "__main__":
    unittest.main()
