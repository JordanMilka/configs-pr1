@echo off
rem Скрипт реальной ОС: проверка всех параметров командной строки.
cd /d "%~dp0..\.."

python scripts\make_vfs.py data

echo.
echo 1. Запуск без параметров
python -m src.main

echo.
echo 2. Запуск только с параметром --vfs
python -m src.main --vfs data\nested.zip

echo.
echo 3. Запуск только с параметром --script
python -m src.main --script scripts\emulator\stage2_demo.txt

echo.
echo 4. Запуск с обоими параметрами
python -m src.main --vfs data\nested.zip --script scripts\emulator\stage2_demo.txt
