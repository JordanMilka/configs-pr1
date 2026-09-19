#!/bin/sh
# Скрипт реальной ОС: проверка всех параметров командной строки.
cd "$(dirname "$0")/../.." || exit 1

echo "1. Запуск без параметров"
python3 -m src.main

echo "2. Запуск только с параметром --vfs"
python3 -m src.main --vfs data/vfs.zip

echo "3. Запуск только с параметром --script"
python3 -m src.main --script scripts/emulator/stage2_demo.txt

echo "4. Запуск с обоими параметрами"
python3 -m src.main --vfs data/vfs.zip \
    --script scripts/emulator/stage2_demo.txt
