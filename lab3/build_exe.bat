@echo off
rem Сборка lab3.exe (нужен установленный Python 3.9+ для Windows)
pip install pyinstaller
pyinstaller --onefile --windowed --name lab3 main.py
echo.
echo Готово: dist\lab3.exe
pause
