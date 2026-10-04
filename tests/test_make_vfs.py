"""Тесты создания образцов VFS и их загрузки эмулятором."""

import os
import unittest

from scripts.make_vfs import make_samples
from src.vfs import VfsError, load_vfs
from tests.helpers import make_temp_directory

MIN_NESTED_DEPTH = 3


class SamplesTest(unittest.TestCase):
    """Проверка образцов VFS, создаваемых для скриптов реальной ОС."""

    def setUp(self):
        """Создать образцы во временном каталоге."""
        self.directory = make_temp_directory(self)
        self.paths = make_samples(self.directory)

    def load(self, name):
        """Загрузить образец по имени без расширения."""
        return load_vfs(os.path.join(self.directory, name + ".zip"))

    def test_all_files_created(self):
        """Создаются четыре архива и один файл неверного формата."""
        self.assertEqual(len(self.paths), 5)
        for path in self.paths:
            self.assertTrue(os.path.isfile(path))

    def test_empty_sample(self):
        """Пустой образец не содержит файлов."""
        self.assertEqual(self.load("empty").statistics().files, 0)

    def test_minimal_sample(self):
        """Минимальный образец содержит один файл."""
        self.assertEqual(self.load("minimal").statistics().files, 1)

    def test_several_sample(self):
        """Образец с несколькими файлами содержит двоичный файл."""
        stats = self.load("several").statistics()
        self.assertGreater(stats.files, 1)
        self.assertEqual(stats.binary, 1)

    def test_nested_sample(self):
        """Вложенный образец содержит не менее трёх уровней."""
        stats = self.load("nested").statistics()
        self.assertGreaterEqual(stats.depth, MIN_NESTED_DEPTH)

    def test_broken_sample(self):
        """Образец неверного формата вызывает ошибку загрузки."""
        with self.assertRaises(VfsError):
            self.load("broken")


if __name__ == "__main__":
    unittest.main()
