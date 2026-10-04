"""Тесты стартовых скриптов эмулятора.

Каждый скрипт из scripts/emulator выполняется без графического
интерфейса. Скрипты, в имени которых есть слово error, обязаны
остановиться на ошибке, остальные - дойти до конца или до exit.
"""

import os
import unittest
from unittest import mock

from scripts.make_vfs import make_samples
from src.commands import execute
from src.errors import CommandError, ExitRequested
from src.parser import ParseError, parse_line
from src.script import is_executable_line, read_script_lines
from src.session import Session
from src.vfs import load_vfs
from tests.helpers import make_temp_directory

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts", "emulator")
ERROR_MARK = "error"
NO_VFS_SCRIPTS = ("stage3_error_no_vfs",)
OWN_SAMPLES = ("empty", "minimal", "several")
STAGE2_PREFIX = "stage2_"
ENVIRONMENT = {
    "EMU_DIR": "/home/user/docs",
    "EMU_FILE": "words.txt",
    "EMU_OWNER": "alice:staff",
}


def find_scripts():
    """Найти все стартовые скрипты эмулятора.

    :return: отсортированный список путей к файлам .txt.
    """
    found = []
    for folder, _, names in os.walk(SCRIPTS):
        found.extend(
            os.path.join(folder, name)
            for name in names
            if name.endswith(".txt")
        )
    return sorted(found)


def expects_error(path):
    """Определить, должен ли скрипт остановиться на ошибке.

    :param path: путь к стартовому скрипту.
    :return: True, если слово error есть в имени файла или каталога.
    """
    folder = os.path.basename(os.path.dirname(path))
    name = os.path.basename(path)
    return ERROR_MARK in name or ERROR_MARK in folder


def run_script(session, path):
    """Выполнить скрипт без графического интерфейса.

    :param session: состояние сеанса.
    :param path: путь к стартовому скрипту.
    :return: True, если скрипт выполнен без ошибок, иначе False.
    """
    for line in read_script_lines(path):
        if not is_executable_line(line):
            continue
        try:
            tokens = parse_line(line)
            if tokens:
                execute(tokens, session)
        except ExitRequested:
            return True
        except (CommandError, ParseError):
            return False
    return True


class ScriptsTest(unittest.TestCase):
    """Проверка всех стартовых скриптов эмулятора."""

    def setUp(self):
        """Создать образцы VFS и задать переменные окружения."""
        self.samples = make_temp_directory(self)
        make_samples(self.samples)
        patcher = mock.patch.dict(os.environ, ENVIRONMENT)
        patcher.start()
        self.addCleanup(patcher.stop)

    def make_session(self, name):
        """Создать сеанс с VFS, которую ожидает скрипт."""
        if name in NO_VFS_SCRIPTS:
            return Session()
        sample = name.split("_")[-1]
        sample = sample if sample in OWN_SAMPLES else "nested"
        return Session(load_vfs(os.path.join(self.samples, sample + ".zip")))

    def test_scripts_found(self):
        """Скрипты этапов 2-5 найдены."""
        names = [os.path.basename(path) for path in find_scripts()]
        for expected in ("stage2_demo.txt", "stage3_all.txt"):
            self.assertIn(expected, names)
        self.assertIn("stage4_all.txt", names)
        self.assertIn("cd_file.txt", names)
        self.assertIn("stage5_all.txt", names)
        self.assertIn("rm_root.txt", names)

    def test_every_script(self):
        """Скрипты ведут себя так, как заявлено в их названии."""
        for path in find_scripts():
            name = os.path.splitext(os.path.basename(path))[0]
            with self.subTest(script=name):
                result = run_script(self.make_session(name), path)
                self.assertEqual(result, not expects_error(path))

    def test_stage2_scripts_without_vfs(self):
        """Скрипты этапа 2 работают и без VFS (с пустым корнем)."""
        for path in find_scripts():
            name = os.path.splitext(os.path.basename(path))[0]
            if not name.startswith(STAGE2_PREFIX):
                continue
            with self.subTest(script=name):
                result = run_script(Session(), path)
                self.assertEqual(result, not expects_error(path))


if __name__ == "__main__":
    unittest.main()
