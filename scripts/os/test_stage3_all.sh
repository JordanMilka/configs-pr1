#!/bin/sh
# Скрипт реальной ОС: все команды этапов 1-3, рабочие режимы и ошибки.
cd "$(dirname "$0")/../.." || exit 1

python3 scripts/make_vfs.py data

echo ""
echo "1. Все команды в рабочих режимах"
python3 -m src.main --vfs data/nested.zip --script scripts/emulator/stage3_all.txt

echo ""
echo "2. Ошибка: неизвестная команда"
python3 -m src.main --vfs data/nested.zip --script scripts/emulator/stage3_error_unknown.txt

echo ""
echo "3. Ошибка: неверные аргументы"
python3 -m src.main --vfs data/nested.zip --script scripts/emulator/stage3_error_arguments.txt

echo ""
echo "4. Ошибка разбора строки"
python3 -m src.main --vfs data/nested.zip --script scripts/emulator/stage3_error_parse.txt

echo ""
echo "5. Ошибка: VFS не подключена"
python3 -m src.main --script scripts/emulator/stage3_error_no_vfs.txt
