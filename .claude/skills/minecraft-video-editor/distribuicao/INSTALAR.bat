@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul || (echo Python nao encontrado. Instale o Python 3.11+ em python.org marcando "Add python.exe to PATH" e rode de novo. & pause & exit /b 1)
where ffmpeg >nul 2>nul || (echo ffmpeg nao encontrado. Instalando com winget... & winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements)
python -X utf8 instalar.py %*
pause
