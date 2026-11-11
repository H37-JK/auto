@echo off
chcp 65001 >nul
where py >nul 2>nul && (py -3 "%~dp0autoclick.py" & goto :eof)
where python >nul 2>nul && (python "%~dp0autoclick.py" & goto :eof)
echo Python이 설치되어 있지 않습니다. https://www.python.org/downloads/ 에서 설치하세요.
pause
