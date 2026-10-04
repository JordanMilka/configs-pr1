"""Тесты виртуальной файловой системы."""

import base64
import os
import unittest
import zipfile

from src.vfs import (
    VfsDirectory,
    VfsError,
    VfsFile,
    entry_mode,
    format_info,
    format_summary,
    format_tree,
    is_binary,
    load_vfs,
    split_path,
)
from tests.helpers import make_temp_directory, make_zip

BINARY_DATA = bytes([0, 1, 2, 255, 254])
NESTED = {
    "a/b/c/d.txt": b"deep\n",
    "a/b/e.txt": b"mid\n",
    "a/f.bin": BINARY_DATA,
    "top.txt": b"top\n",
}


class LoadVfsTest(unittest.TestCase):
    """Проверка загрузки VFS из ZIP-архива."""

    def setUp(self):
        """Создать временный каталог для архивов."""
        self.directory = make_temp_directory(self)

    def load(self, entries):
        """Создать архив с записями и загрузить его как VFS."""
        return load_vfs(make_zip(self.directory, "t.zip", entries))

    def test_empty_archive(self):
        """Пустой архив даёт пустую VFS."""
        stats = self.load({}).statistics()
        self.assertEqual((stats.directories, stats.files), (0, 0))

    def test_minimal_archive(self):
        """Архив из одного файла загружается."""
        vfs = self.load({"hello.txt": b"hi\n"})
        self.assertEqual(vfs.root.children["hello.txt"].content, "hi\n")

    def test_nested_archive(self):
        """Вложенные каталоги создаются без явных записей о них."""
        stats = self.load(NESTED).statistics()
        self.assertEqual(stats.directories, 3)
        self.assertEqual(stats.files, 4)
        self.assertEqual(stats.depth, 4)

    def test_explicit_directory_entry(self):
        """Запись о пустом каталоге создаёт каталог."""
        vfs = self.load({"empty/": b""})
        self.assertIsInstance(vfs.root.children["empty"], VfsDirectory)

    def test_binary_file_is_base64(self):
        """Двоичный файл хранится в виде base64."""
        node = self.load(NESTED).root.children["a"].children["f.bin"]
        self.assertTrue(node.binary)
        self.assertEqual(base64.b64decode(node.content), BINARY_DATA)
        self.assertEqual(node.size, len(BINARY_DATA))

    def test_archive_is_not_modified(self):
        """Архив на диске не изменяется, ничего не распаковывается."""
        path = make_zip(self.directory, "t.zip", NESTED)
        with open(path, "rb") as source:
            before = source.read()
        load_vfs(path)
        with open(path, "rb") as source:
            self.assertEqual(source.read(), before)
        self.assertEqual(os.listdir(self.directory), ["t.zip"])


class LoadVfsErrorTest(unittest.TestCase):
    """Проверка ошибок загрузки VFS."""

    def setUp(self):
        """Создать временный каталог для файлов."""
        self.directory = make_temp_directory(self)

    def test_empty_path(self):
        """Пустой путь к VFS приводит к ошибке."""
        with self.assertRaises(VfsError):
            load_vfs("")

    def test_file_not_found(self):
        """Отсутствующий файл приводит к ошибке с понятным текстом."""
        path = os.path.join(self.directory, "missing.zip")
        with self.assertRaises(VfsError) as context:
            load_vfs(path)
        self.assertIn("файл не найден", str(context.exception))

    def test_wrong_format(self):
        """Файл, не являющийся ZIP-архивом, приводит к ошибке."""
        path = os.path.join(self.directory, "broken.zip")
        with open(path, "w", encoding="utf-8") as target:
            target.write("это не архив")
        with self.assertRaises(VfsError) as context:
            load_vfs(path)
        self.assertIn("неверный формат", str(context.exception))

    def test_directory_instead_of_file(self):
        """Путь к каталогу вместо файла приводит к ошибке."""
        with self.assertRaises(VfsError):
            load_vfs(self.directory)

    def test_unsafe_path(self):
        """Путь с ".." в архиве отклоняется."""
        path = make_zip(self.directory, "t.zip", {"../evil.txt": b"x"})
        with self.assertRaises(VfsError):
            load_vfs(path)

    def test_file_and_directory_conflict(self):
        """Файл и каталог с одним именем отклоняются."""
        entries = {"a": b"file", "a/b.txt": b"x"}
        path = make_zip(self.directory, "t.zip", entries)
        with self.assertRaises(VfsError):
            load_vfs(path)


class NodeAttributesTest(unittest.TestCase):
    """Проверка прав, владельца и времени изменения узлов."""

    def setUp(self):
        """Создать архив с явными правами и временем записей."""
        directory = make_temp_directory(self)
        self.path = os.path.join(directory, "m.zip")
        with zipfile.ZipFile(self.path, "w") as archive:
            info = zipfile.ZipInfo("d/f.txt", (2026, 1, 15, 10, 30, 0))
            info.external_attr = 0o640 << 16
            archive.writestr(info, b"x")
            dir_info = zipfile.ZipInfo("d/", (2025, 5, 6, 7, 8, 0))
            dir_info.external_attr = (0o40750 << 16) | 0x10
            archive.writestr(dir_info, b"")

    def test_mode_and_time_from_archive(self):
        """Права и время берутся из записей архива."""
        root = load_vfs(self.path).root
        node = root.children["d"].children["f.txt"]
        self.assertEqual(node.mode, 0o640)
        self.assertEqual(node.mtime, (2026, 1, 15, 10, 30, 0))
        self.assertEqual(root.children["d"].mode, 0o750)
        self.assertEqual(root.children["d"].mtime, (2025, 5, 6, 7, 8, 0))

    def test_default_mode(self):
        """Без атрибутов Unix действуют права по умолчанию."""
        self.assertEqual(entry_mode(zipfile.ZipInfo("f.txt")), 0o644)
        self.assertEqual(entry_mode(zipfile.ZipInfo("d/")), 0o755)

    def test_default_owner(self):
        """Владелец и группа по умолчанию - root."""
        node = load_vfs(self.path).root.children["d"]
        self.assertEqual((node.owner, node.group), ("root", "root"))

    def test_directory_size_is_zero(self):
        """Размер каталога равен нулю."""
        self.assertEqual(load_vfs(self.path).root.children["d"].size, 0)


class HelpersTest(unittest.TestCase):
    """Проверка вспомогательных функций VFS."""

    def setUp(self):
        """Загрузить VFS с вложенными каталогами."""
        directory = make_temp_directory(self)
        self.vfs = load_vfs(make_zip(directory, "n.zip", NESTED))

    def test_is_binary(self):
        """Текст определяется как недвоичный, остальное - как двоичное."""
        self.assertFalse(is_binary("текст".encode("utf-8")))
        self.assertTrue(is_binary(b"\x00abc"))
        self.assertTrue(is_binary(b"\xff\xfe"))

    def test_split_path(self):
        """Путь делится на части, лишние разделители отбрасываются."""
        self.assertEqual(split_path("a//b/./c.txt"), ["a", "b", "c.txt"])

    def test_text_file(self):
        """Текстовый файл хранится строкой."""
        node = VfsFile("x.txt", "привет".encode("utf-8"))
        self.assertFalse(node.binary)
        self.assertEqual(node.content, "привет")

    def test_format_tree(self):
        """Дерево показывает каталоги раньше файлов."""
        expected = "\n".join([
            "/",
            "├── a/",
            "│   ├── b/",
            "│   │   ├── c/",
            "│   │   │   └── d.txt",
            "│   │   └── e.txt",
            "│   └── f.bin [двоичный]",
            "└── top.txt",
        ])
        self.assertEqual(format_tree(self.vfs), expected)

    def test_format_info(self):
        """Сведения содержат все показатели VFS."""
        text = format_info(self.vfs)
        self.assertIn("Каталогов: 3", text)
        self.assertIn("Файлов: 4 (двоичных: 1)", text)
        self.assertIn("Максимальная вложенность: 4", text)

    def test_format_summary(self):
        """Сводка содержит источник, число каталогов и файлов."""
        self.assertIn("каталогов: 3, файлов: 4", format_summary(self.vfs))


if __name__ == "__main__":
    unittest.main()
