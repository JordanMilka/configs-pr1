@echo off
rem Скрипт реальной ОС: ошибки загрузки VFS.
cd /d "%~dp0..\.."

python scripts\make_vfs.py data

echo.
echo 1. Файл VFS не найден
python -m src.main --vfs data\missing.zip --script scripts\emulator\stage3_all.txt

echo.
echo 2. Неверный формат: файл не является ZIP-архивом
python -m src.main --vfs data\broken.zip --script scripts\emulator\stage3_all.txt

echo.
echo 3. Вместо архива указан каталог
python -m src.main --vfs data --script scripts\emulator\stage3_all.txt

echo.
echo 4. Команда VFS без параметра --vfs
python -m src.main --script scripts\emulator\stage3_error_no_vfs.txt
