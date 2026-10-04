"""Создание образцов VFS для проверки эмулятора.

ZIP-архивы не хранятся в репозитории, поэтому скрипты реальной ОС
создают их этим модулем в каталоге data (по умолчанию) перед запуском
эмулятора. Запуск: python3 scripts/make_vfs.py [КАТАЛОГ]
"""

import argparse
import os
import zipfile

DEFAULT_DIRECTORY = "data"
ARCHIVE_SUFFIX = ".zip"
BROKEN_NAME = "broken"
BROKEN_TEXT = "Это текстовый файл, а не ZIP-архив.\n"
ENCODING = "utf-8"
FIXED_TIME = (2026, 1, 15, 10, 30, 0)
FILE_MODE = 0o644
DIRECTORY_MODE = 0o755
FILE_TYPE = 0o100000
DIRECTORY_TYPE = 0o40000
UNIX_MODE_SHIFT = 16
MSDOS_DIRECTORY = 0x10
MODES = {
    "etc/motd": 0o444,
    "home/user/.profile": 0o600,
    "home/user/docs/report.txt": 0o640,
    "home/user/empty_dir/": 0o700,
}
WORDS = b"apple\napple\nApple\nbanana\ncherry\ncherry\ncherry\napple\n"
PNG_HEADER = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00])
RANDOM_BYTES = bytes([0x00, 0x01, 0x02, 0xFE, 0xFF])

EMPTY = {}

MINIMAL = {
    "hello.txt": "Привет из VFS!\n".encode(ENCODING),
}

SEVERAL = {
    "readme.txt": "Учебная VFS с несколькими файлами.\n".encode(ENCODING),
    "fruits.txt": b"apple\napple\nbanana\ncherry\ncherry\ncherry\n",
    "notes.txt": "Первая строка\nВторая строка\n".encode(ENCODING),
    "data.bin": RANDOM_BYTES,
    "empty/": b"",
}

NESTED = {
    "home/user/docs/report.txt": "Отчёт за квартал.\n".encode(ENCODING),
    "home/user/docs/words.txt": WORDS,
    "home/user/.profile": b"export PATH=/usr/bin\n",
    "home/user/docs/archive/2026/summary.txt": b"summary\nsummary\n",
    "home/user/pictures/logo.png": PNG_HEADER,
    "home/user/empty_dir/": b"",
    "etc/hostname": b"emulator\n",
    "etc/motd": "Добро пожаловать!\n".encode(ENCODING),
    "var/log/app.log": b"start\nwork\nwork\nstop\n",
}

SAMPLES = {
    "empty": EMPTY,
    "minimal": MINIMAL,
    "several": SEVERAL,
    "nested": NESTED,
}


def entry_info(name):
    """Создать описание записи с правами и фиксированным временем.

    :param name: путь записи; каталог оканчивается на "/".
    :return: объект ZipInfo с атрибутами Unix.
    """
    is_directory = name.endswith("/")
    default = DIRECTORY_MODE if is_directory else FILE_MODE
    kind = DIRECTORY_TYPE if is_directory else FILE_TYPE
    info = zipfile.ZipInfo(name, FIXED_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = (kind | MODES.get(name, default)) << UNIX_MODE_SHIFT
    if is_directory:
        info.external_attr |= MSDOS_DIRECTORY
    return info


def write_archive(path, entries):
    """Создать ZIP-архив с заданными записями.

    Время изменения всех записей одинаково, чтобы вывод ls -l не
    зависел от момента создания образца.

    :param path: путь к создаваемому архиву.
    :param entries: словарь "путь записи -> содержимое в байтах".
    """
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in entries.items():
            archive.writestr(entry_info(name), data)


def write_broken(path):
    """Создать файл неверного формата для проверки ошибок загрузки.

    :param path: путь к создаваемому файлу.
    """
    with open(path, "w", encoding=ENCODING) as target:
        target.write(BROKEN_TEXT)


def make_samples(directory):
    """Создать все образцы VFS в каталоге.

    :param directory: каталог для архивов; создаётся при отсутствии.
    :return: список путей к созданным файлам.
    """
    os.makedirs(directory, exist_ok=True)
    paths = []
    for name, entries in SAMPLES.items():
        path = os.path.join(directory, name + ARCHIVE_SUFFIX)
        write_archive(path, entries)
        paths.append(path)
    broken = os.path.join(directory, BROKEN_NAME + ARCHIVE_SUFFIX)
    write_broken(broken)
    paths.append(broken)
    return paths


def main(argv=None):
    """Разобрать параметры и создать образцы VFS.

    :param argv: список аргументов или None, чтобы взять sys.argv.
    """
    parser = argparse.ArgumentParser(description="Создание образцов VFS.")
    parser.add_argument(
        "directory",
        nargs="?",
        default=DEFAULT_DIRECTORY,
        help="каталог для архивов (по умолчанию: data)",
    )
    for path in make_samples(parser.parse_args(argv).directory):
        print("создан файл: {0}".format(path))


if __name__ == "__main__":
    main()
