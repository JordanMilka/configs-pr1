"""Вспомогательные функции для тестов: создание ZIP-архивов."""

import os
import tempfile
import zipfile


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
