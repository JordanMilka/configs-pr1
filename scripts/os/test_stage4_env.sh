#!/bin/sh
# Скрипт реальной ОС: переменные окружения реальной ОС в путях команд.
cd "$(dirname "$0")/../.." || exit 1

python3 scripts/make_vfs.py data

export EMU_DIR=/home/user/docs
export EMU_FILE=words.txt

echo ""
echo "Переменные окружения реальной ОС в путях: EMU_DIR=$EMU_DIR, EMU_FILE=$EMU_FILE"
python3 -m src.main --vfs data/nested.zip --script scripts/emulator/stage4_env.txt
