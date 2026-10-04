"""Вспомогательные функции для тестов: создание ZIP-архивов."""

import os
import tempfile
import zipfile

DIRECTORY_TYPE = 0o40000
FILE_TYPE = 0o100000
UNIX_SHIFT = 16


def make_zip(directory, name, entries):
    """Создать ZIP-архив во временном каталоге.

    :param directory: каталог, в котором создаётся архив.
    :param name: имя файла архива.
    :param entries: словарь "путь записи -> содержимое в байтах".
    :return: полный путь к созданному архиву.
    """
    path = os.path.join(directory, name)
    with zipfile.ZipFile(path, "w") as archive:
        for entry_name, data in entries.items():
            archive.writestr(entry_name, data)
    return path


def make_temp_directory(test_case):
    """Создать временный каталог, удаляемый после теста.

    :param test_case: экземпляр unittest.TestCase.
    :return: путь к созданному каталогу.
    """
    holder = tempfile.TemporaryDirectory()
    test_case.addCleanup(holder.cleanup)
    return holder.name


def make_unix_zip(directory, name, records, mtime=(2026, 1, 15, 10, 30, 0)):
    """Создать ZIP-архив с правами доступа и временем изменения.

    :param directory: каталог, в котором создаётся архив.
    :param name: имя файла архива.
    :param records: словарь "путь записи -> (содержимое, права)";
        путь, оканчивающийся на "/", задаёт каталог.
    :param mtime: время изменения всех записей.
    :return: полный путь к созданному архиву.
    """
    path = os.path.join(directory, name)
    with zipfile.ZipFile(path, "w") as archive:
        for entry_name, (data, mode) in records.items():
            info = zipfile.ZipInfo(entry_name, mtime)
            kind = DIRECTORY_TYPE if entry_name.endswith("/") else FILE_TYPE
            info.external_attr = (kind | mode) << UNIX_SHIFT
            archive.writestr(info, data)
    return path
