@echo off
rem Сборка lab2.exe (нужен установленный Python 3.9+ для Windows)
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --windowed --name lab2 main.py
echo.
echo Готово: dist\lab2.exe
pause
