"""Тесты команды help и справочных текстов."""

import unittest

from src.commands import COMMANDS, execute
from src.errors import CommandError
from src.help_text import HELP, format_entry, format_list
from src.session import Session

GUI_WIDTH = 80


class HelpCoverageTest(unittest.TestCase):
    """Проверка того, что справка соответствует реестру команд."""

    def test_every_command_has_help(self):
        """У каждой команды есть справка и наоборот."""
        self.assertEqual(set(COMMANDS), set(HELP))

    def test_lines_fit_window(self):
        """Строки справки помещаются в ширину окна эмулятора."""
        texts = [format_list(list(COMMANDS))]
        texts += [format_entry(name) for name in COMMANDS]
        for text in texts:
            for line in text.splitlines():
                with self.subTest(line=line):
                    self.assertLessEqual(len(line), GUI_WIDTH)

    def test_usage_starts_with_name(self):
        """Строка использования начинается с имени команды."""
        for name, entry in HELP.items():
            with self.subTest(command=name):
                self.assertTrue(entry.usage.startswith(name))


class HelpCommandTest(unittest.TestCase):
    """Проверка выполнения help."""

    def setUp(self):
        """Создать сеанс без VFS."""
        self.session = Session()

    def test_list(self):
        """Без аргументов выводится список всех команд."""
        text = execute(["help"], self.session)
        self.assertTrue(text.startswith("Доступные команды:"))
        for name in COMMANDS:
            with self.subTest(command=name):
                self.assertIn("  " + HELP[name].usage, text)
        self.assertTrue(text.endswith("Подробнее: help КОМАНДА"))

    def test_list_order(self):
        """Команды выводятся в порядке реестра."""
        lines = execute(["help"], self.session).splitlines()
        shown = [line.split()[0] for line in lines[1:len(COMMANDS) + 1]]
        self.assertEqual(shown, list(COMMANDS))

    def test_list_columns_aligned(self):
        """Описания команд начинаются в одном столбце."""
        lines = execute(["help"], self.session).splitlines()
        columns = {
            line.index(HELP[name].summary)
            for line, name in zip(lines[1:], COMMANDS)
        }
        self.assertEqual(len(columns), 1)

    def test_entry_with_options(self):
        """Справка по команде с ключами перечисляет ключи."""
        text = execute(["help", "uniq"], self.session)
        for key in ("-c", "-d", "-u", "-i"):
            self.assertIn("  " + key + "  ", text)
        self.assertIn("Ключи:", text)

    def test_entry_without_options(self):
        """Справка по команде без ключей не содержит разделов."""
        text = execute(["help", "exit"], self.session)
        self.assertEqual(text, "exit\n  завершить работу эмулятора")

    def test_help_about_help(self):
        """Справка по самой команде help выводится."""
        self.assertTrue(
            execute(["help", "help"], self.session).startswith("help [")
        )

    def test_unknown_command(self):
        """Для неизвестной команды сообщается об ошибке."""
        with self.assertRaises(CommandError) as context:
            execute(["help", "pwd"], self.session)
        self.assertEqual(str(context.exception), "help: нет справки по 'pwd'")

    def test_too_many_arguments(self):
        """Больше одного аргумента приводит к ошибке."""
        with self.assertRaises(CommandError) as context:
            execute(["help", "ls", "cd"], self.session)
        self.assertEqual(
            str(context.exception), "help: слишком много аргументов"
        )


if __name__ == "__main__":
    unittest.main()
