@echo off
rem Скрипт реальной ОС: VFS с вложенностью не менее трёх уровней.
cd /d "%~dp0..\.."

python scripts\make_vfs.py data

echo.
echo 1. Каталоги до шести уровней вложенности
python -m src.main --vfs data\nested.zip --script scripts\emulator\stage3_nested.txt
