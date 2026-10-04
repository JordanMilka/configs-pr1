@echo off
rem Скрипт реальной ОС: все команды этапов 1-3, рабочие режимы и ошибки.
cd /d "%~dp0..\.."

python scripts\make_vfs.py data

echo.
echo 1. Все команды в рабочих режимах
python -m src.main --vfs data\nested.zip --script scripts\emulator\stage3_all.txt

echo.
echo 2. Ошибка: неизвестная команда
python -m src.main --vfs data\nested.zip --script scripts\emulator\stage3_error_unknown.txt

echo.
echo 3. Ошибка: неверные аргументы
python -m src.main --vfs data\nested.zip --script scripts\emulator\stage3_error_arguments.txt

echo.
echo 4. Ошибка разбора строки
python -m src.main --vfs data\nested.zip --script scripts\emulator\stage3_error_parse.txt

echo.
echo 5. Ошибка: VFS не подключена
python -m src.main --script scripts\emulator\stage3_error_no_vfs.txt
