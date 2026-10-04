@echo off
rem Скрипт реальной ОС: обработка ошибок chown, rm и help (по скрипту на ошибку).
cd /d "%~dp0..\.."

python scripts\make_vfs.py data
for %%f in (scripts\emulator\stage5_errors\*.txt) do (
    echo.
    echo Ошибка: %%f
    python -m src.main --vfs data\nested.zip --script %%f
)
