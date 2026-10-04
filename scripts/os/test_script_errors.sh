#!/bin/sh
# Скрипт реальной ОС: проверка ошибок стартового скрипта.
cd "$(dirname "$0")/../.." || exit 1

python3 scripts/make_vfs.py data

echo ""
echo "1. Ошибка в команде: скрипт останавливается"
python3 -m src.main --vfs data/nested.zip --script scripts/emulator/stage2_error.txt

echo ""
echo "2. Стартовый скрипт не найден"
python3 -m src.main --vfs data/nested.zip --script scripts/emulator/none.txt

echo ""
echo "3. Завершение работы командой exit из скрипта"
python3 -m src.main --script scripts/emulator/stage2_exit.txt
