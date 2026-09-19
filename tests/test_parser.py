"""Тесты разбора строки ввода и раскрытия переменных."""

import os
import unittest

from src.parser import ParseError, expand_variables, parse_line


class ExpandVariablesTest(unittest.TestCase):
    """Проверка раскрытия переменных окружения."""

    def setUp(self):
        """Подготовить тестовую переменную окружения."""
        os.environ["EMULATOR_TEST_DIR"] = "/tmp/emulator"

    def tearDown(self):
        """Удалить тестовую переменную окружения."""
        del os.environ["EMULATOR_TEST_DIR"]

    def test_plain_variable(self):
        """Переменная без скобок раскрывается."""
        self.assertEqual(
            expand_variables("$EMULATOR_TEST_DIR"), "/tmp/emulator"
        )

    def test_braced_variable(self):
        """Переменная в фигурных скобках раскрывается."""
        self.assertEqual(
            expand_variables("${EMULATOR_TEST_DIR}/a"), "/tmp/emulator/a"
        )

    def test_unknown_variable(self):
        """Неизвестная переменная заменяется пустой строкой."""
        self.assertEqual(expand_variables("$NO_SUCH_VARIABLE_X"), "")

    def test_lonely_dollar_sign(self):
        """Одиночный знак доллара остаётся без изменений."""
        self.assertEqual(expand_variables("price $ 5"), "price $ 5")

    def test_unclosed_brace(self):
        """Незакрытая скобка приводит к ошибке разбора."""
        with self.assertRaises(ParseError):
            expand_variables("${HOME")


class ParseLineTest(unittest.TestCase):
    """Проверка разделения строки на токены."""

    def test_empty_line(self):
        """Пустая строка даёт пустой список токенов."""
        self.assertEqual(parse_line("   "), [])

    def test_command_and_arguments(self):
        """Строка делится на команду и аргументы."""
        self.assertEqual(parse_line("ls -l dir"), ["ls", "-l", "dir"])

    def test_extra_spaces(self):
        """Лишние пробелы между токенами игнорируются."""
        self.assertEqual(parse_line("cd    home"), ["cd", "home"])


if __name__ == "__main__":
    unittest.main()
