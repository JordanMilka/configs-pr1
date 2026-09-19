#!/bin/sh
# Скрипт реальной ОС: проверка ошибок стартового скрипта.
cd "$(dirname "$0")/../.." || exit 1

echo "1. Ошибка в команде: скрипт останавливается"
python3 -m src.main --vfs data/vfs.zip \
    --script scripts/emulator/stage2_error.txt

echo "2. Стартовый скрипт не найден"
python3 -m src.main --vfs data/vfs.zip --script scripts/emulator/none.txt

echo "3. Завершение работы командой exit из скрипта"
python3 -m src.main --script scripts/emulator/stage2_exit.txt
