#!/bin/sh
# Скрипт реальной ОС: изменения VFS существуют только в памяти, архив не меняется.
cd "$(dirname "$0")/../.." || exit 1

python3 scripts/make_vfs.py data
HASH='import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())'

echo ""
echo "Контрольная сумма архива до запуска:"
python3 -c "$HASH" data/nested.zip

echo ""
echo "Запуск 1: скрипт удаляет почти всю VFS"
python3 -m src.main --vfs data/nested.zip --script scripts/emulator/stage5_memory.txt

echo ""
echo "Запуск 2: VFS снова загружена целиком, дерево в начале то же"
python3 -m src.main --vfs data/nested.zip --script scripts/emulator/stage5_memory.txt

echo ""
echo "Контрольная сумма архива после запуска (должна совпасть):"
python3 -c "$HASH" data/nested.zip
