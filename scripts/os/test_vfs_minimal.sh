#!/bin/sh
# Скрипт реальной ОС: минимальные варианты VFS (пустой архив и один файл).
cd "$(dirname "$0")/../.." || exit 1

python3 scripts/make_vfs.py data

echo ""
echo "1. Пустой архив"
python3 -m src.main --vfs data/empty.zip --script scripts/emulator/stage3_empty.txt

echo ""
echo "2. Архив из одного файла"
python3 -m src.main --vfs data/minimal.zip --script scripts/emulator/stage3_minimal.txt
