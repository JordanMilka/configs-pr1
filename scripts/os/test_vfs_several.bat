@echo off
rem Скрипт реальной ОС: VFS с несколькими файлами, пустым каталогом и двоичным файлом.
cd /d "%~dp0..\.."

python scripts\make_vfs.py data

echo.
echo 1. Несколько файлов
python -m src.main --vfs data\several.zip --script scripts\emulator\stage3_several.txt
