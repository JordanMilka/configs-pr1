"""Тесты команд эмулятора командной оболочки."""

import unittest

from src.commands import CommandError, ExitRequested, execute


class ExecuteTest(unittest.TestCase):
    """Проверка выполнения команд этапа 1."""

    def test_ls_without_arguments(self):
        """Команда ls без аргументов сообщает об их отсутствии."""
        self.assertEqual(execute(["ls"]), "ls: аргументы отсутствуют")

    def test_ls_with_arguments(self):
        """Команда ls выводит своё имя и аргументы."""
        self.assertEqual(execute(["ls", "-l", "/tmp"]), "ls: -l /tmp")

    def test_cd_with_one_argument(self):
        """Команда cd принимает один аргумент."""
        self.assertEqual(execute(["cd", "/home"]), "cd: /home")

    def test_cd_with_two_arguments(self):
        """Команда cd сообщает об избыточных аргументах."""
        with self.assertRaises(CommandError):
            execute(["cd", "a", "b"])

    def test_unknown_command(self):
        """Неизвестная команда приводит к ошибке."""
        with self.assertRaises(CommandError):
            execute(["unknown"])

    def test_exit(self):
        """Команда exit запрашивает завершение работы."""
        with self.assertRaises(ExitRequested):
            execute(["exit"])

    def test_exit_with_argument(self):
        """Команда exit не принимает аргументов."""
        with self.assertRaises(CommandError):
            execute(["exit", "now"])


if __name__ == "__main__":
    unittest.main()
