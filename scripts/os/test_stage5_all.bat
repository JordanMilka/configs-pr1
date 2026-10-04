@echo off
rem Скрипт реальной ОС: команды chown, rm и help во всех рабочих режимах.
cd /d "%~dp0..\.."

python scripts\make_vfs.py data
set EMU_OWNER=alice:staff

echo.
echo 1. Все команды этапа 5 на вложенной VFS
python -m src.main --vfs data\nested.zip --script scripts\emulator\stage5_all.txt

echo.
echo 2. chown, rm и help на VFS с несколькими файлами
python -m src.main --vfs data\several.zip --script scripts\emulator\stage5_several.txt

echo.
echo 3. Переменная окружения EMU_OWNER=%EMU_OWNER% в записи владельца
python -m src.main --vfs data\nested.zip --script scripts\emulator\stage5_env.txt
