#!/bin/sh
# Скрипт реальной ОС: ошибки загрузки VFS.
cd "$(dirname "$0")/../.." || exit 1

python3 scripts/make_vfs.py data

echo ""
echo "1. Файл VFS не найден"
python3 -m src.main --vfs data/missing.zip --script scripts/emulator/stage3_all.txt

echo ""
echo "2. Неверный формат: файл не является ZIP-архивом"
python3 -m src.main --vfs data/broken.zip --script scripts/emulator/stage3_all.txt

echo ""
echo "3. Вместо архива указан каталог"
python3 -m src.main --vfs data --script scripts/emulator/stage3_all.txt

echo ""
echo "4. Команда VFS без параметра --vfs"
python3 -m src.main --script scripts/emulator/stage3_error_no_vfs.txt
