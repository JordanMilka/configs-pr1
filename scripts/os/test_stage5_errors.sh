#!/bin/sh
# Скрипт реальной ОС: обработка ошибок chown, rm и help (по скрипту на ошибку).
cd "$(dirname "$0")/../.." || exit 1

python3 scripts/make_vfs.py data
for script in scripts/emulator/stage5_errors/*.txt; do
    echo ""
    echo "Ошибка: $script"
    python3 -m src.main --vfs data/nested.zip --script "$script"
done
