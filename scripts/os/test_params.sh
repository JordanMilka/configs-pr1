#!/bin/sh
# Скрипт реальной ОС: проверка всех параметров командной строки.
cd "$(dirname "$0")/../.." || exit 1

python3 scripts/make_vfs.py data

echo ""
echo "1. Запуск без параметров"
python3 -m src.main

echo ""
echo "2. Запуск только с параметром --vfs"
python3 -m src.main --vfs data/nested.zip

echo ""
echo "3. Запуск только с параметром --script"
python3 -m src.main --script scripts/emulator/stage2_demo.txt

echo ""
echo "4. Запуск с обоими параметрами"
python3 -m src.main --vfs data/nested.zip --script scripts/emulator/stage2_demo.txt
