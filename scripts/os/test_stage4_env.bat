@echo off
rem Скрипт реальной ОС: переменные окружения реальной ОС в путях команд.
cd /d "%~dp0..\.."

python scripts\make_vfs.py data

set EMU_DIR=/home/user/docs
set EMU_FILE=words.txt

echo.
echo Переменные окружения реальной ОС в путях: EMU_DIR=%EMU_DIR%, EMU_FILE=%EMU_FILE%
python -m src.main --vfs data\nested.zip --script scripts\emulator\stage4_env.txt
