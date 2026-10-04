"""Тесты разбора ключей команд."""

import unittest

from src.errors import CommandError
from src.options import parse_options


class ParseOptionsTest(unittest.TestCase):
    """Проверка разделения аргументов на ключи и операнды."""

    def test_no_arguments(self):
        """Без аргументов нет ни ключей, ни операндов."""
        self.assertEqual(parse_options("ls", [], "la"), (set(), []))

    def test_separate_flags(self):
        """Ключи можно писать раздельно."""
        flags, operands = parse_options("ls", ["-l", "-a", "x"], "la")
        self.assertEqual(flags, {"l", "a"})
        self.assertEqual(operands, ["x"])

    def test_combined_flags(self):
        """Ключи можно объединять в один аргумент."""
        flags, _ = parse_options("ls", ["-la"], "la")
        self.assertEqual(flags, {"l", "a"})

    def test_operands_and_flags_mixed(self):
        """Ключи допустимы после операндов."""
        flags, operands = parse_options("ls", ["a", "-l", "b"], "la")
        self.assertEqual(flags, {"l"})
        self.assertEqual(operands, ["a", "b"])

    def test_double_dash_ends_options(self):
        """Аргумент "--" делает все следующие аргументы операндами."""
        flags, operands = parse_options("ls", ["--", "-l"], "la")
        self.assertEqual(flags, set())
        self.assertEqual(operands, ["-l"])

    def test_single_dash_is_operand(self):
        """Одиночный дефис считается операндом."""
        _, operands = parse_options("cat", ["-"], "n")
        self.assertEqual(operands, ["-"])

    def test_unknown_flag(self):
        """Неизвестная буква ключа приводит к ошибке."""
        with self.assertRaises(CommandError) as context:
            parse_options("ls", ["-lz"], "la")
        self.assertIn("неверный ключ -- 'z'", str(context.exception))

    def test_long_option(self):
        """Длинные ключи не поддерживаются."""
        with self.assertRaises(CommandError) as context:
            parse_options("ls", ["--all"], "la")
        self.assertIn("неизвестный ключ '--all'", str(context.exception))


if __name__ == "__main__":
    unittest.main()
