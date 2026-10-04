#!/bin/sh
# Скрипт реальной ОС: VFS с вложенностью не менее трёх уровней.
cd "$(dirname "$0")/../.." || exit 1

python3 scripts/make_vfs.py data

echo ""
echo "1. Каталоги до шести уровней вложенности"
python3 -m src.main --vfs data/nested.zip --script scripts/emulator/stage3_nested.txt
