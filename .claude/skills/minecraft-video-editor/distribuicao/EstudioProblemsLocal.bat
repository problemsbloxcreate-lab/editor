@echo off
chcp 65001 >nul
rem Estúdio Problems Local: baixa e roda a versão mais nova do instalador (repositório público problemsbloxcreate-lab/editor).
rem Se este .bat estiver ao lado do EstudioProblemsLocal.ps1, usa o arquivo local.
if exist "%~dp0EstudioProblemsLocal.ps1" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0EstudioProblemsLocal.ps1" %*
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$f=Join-Path $env:TEMP 'EstudioProblemsLocal.ps1'; Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/problemsbloxcreate-lab/editor/main/.claude/skills/minecraft-video-editor/distribuicao/EstudioProblemsLocal.ps1' -OutFile $f; & $f %*"
)
pause
