@echo off
rem Скрипт реальной ОС: изменения VFS существуют только в памяти, архив не меняется.
cd /d "%~dp0..\.."

python scripts\make_vfs.py data
echo.
echo Контрольная сумма архива до запуска:
python -c "import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], 'rb').read()).hexdigest())" data\nested.zip

echo.
echo Запуск 1: скрипт удаляет почти всю VFS
python -m src.main --vfs data\nested.zip --script scripts\emulator\stage5_memory.txt

echo.
echo Запуск 2: VFS снова загружена целиком, дерево в начале то же
python -m src.main --vfs data\nested.zip --script scripts\emulator\stage5_memory.txt

echo.
echo Контрольная сумма архива после запуска - должна совпасть:
python -c "import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], 'rb').read()).hexdigest())" data\nested.zip
