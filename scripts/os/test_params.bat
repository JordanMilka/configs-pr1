@echo off
rem Скрипт реальной ОС: проверка всех параметров командной строки.
cd /d "%~dp0..\.."

echo 1. Запуск без параметров
python -m src.main

echo 2. Запуск только с параметром --vfs
python -m src.main --vfs data\vfs.zip

echo 3. Запуск только с параметром --script
python -m src.main --script scripts\emulator\stage2_demo.txt

echo 4. Запуск с обоими параметрами
python -m src.main --vfs data\vfs.zip --script scripts\emulator\stage2_demo.txt
