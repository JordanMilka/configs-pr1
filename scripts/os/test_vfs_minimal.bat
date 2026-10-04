@echo off
rem Скрипт реальной ОС: минимальные варианты VFS (пустой архив и один файл).
cd /d "%~dp0..\.."

python scripts\make_vfs.py data

echo.
echo 1. Пустой архив
python -m src.main --vfs data\empty.zip --script scripts\emulator\stage3_empty.txt

echo.
echo 2. Архив из одного файла
python -m src.main --vfs data\minimal.zip --script scripts\emulator\stage3_minimal.txt
