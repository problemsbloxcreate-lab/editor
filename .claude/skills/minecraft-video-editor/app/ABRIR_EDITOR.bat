@echo off
chcp 65001 >nul
title Editor Problems
cd /d "%~dp0"
echo Editor Problems: abrindo http://localhost:4790  (feche esta janela para desligar a interface; jobs em andamento continuam)
python -X utf8 server.py %*
pause
