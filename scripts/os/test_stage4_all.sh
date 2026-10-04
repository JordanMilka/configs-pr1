#!/bin/sh
# Скрипт реальной ОС: команды ls, cd, cat, uniq во всех рабочих режимах.
cd "$(dirname "$0")/../.." || exit 1

python3 scripts/make_vfs.py data

echo ""
echo "1. Все команды этапа 4 на вложенной VFS"
python3 -m src.main --vfs data/nested.zip --script scripts/emulator/stage4_all.txt

echo ""
echo "2. Команды этапа 4 на VFS с несколькими файлами"
python3 -m src.main --vfs data/several.zip --script scripts/emulator/stage4_several.txt
