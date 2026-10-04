#!/bin/sh
# Скрипт реальной ОС: VFS с несколькими файлами, пустым каталогом и двоичным файлом.
cd "$(dirname "$0")/../.." || exit 1

python3 scripts/make_vfs.py data

echo ""
echo "1. Несколько файлов"
python3 -m src.main --vfs data/several.zip --script scripts/emulator/stage3_several.txt
