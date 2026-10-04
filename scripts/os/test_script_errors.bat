@echo off
rem Скрипт реальной ОС: проверка ошибок стартового скрипта.
cd /d "%~dp0..\.."

python scripts\make_vfs.py data

echo.
echo 1. Ошибка в команде: скрипт останавливается
python -m src.main --vfs data\nested.zip --script scripts\emulator\stage2_error.txt

echo.
echo 2. Стартовый скрипт не найден
python -m src.main --vfs data\nested.zip --script scripts\emulator\none.txt

echo.
echo 3. Завершение работы командой exit из скрипта
python -m src.main --script scripts\emulator\stage2_exit.txt
