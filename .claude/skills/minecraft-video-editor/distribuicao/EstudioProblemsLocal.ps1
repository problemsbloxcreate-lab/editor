# Estúdio Problems Local — instalador de um clique (Windows 10/11, sem administrador).
# Deixa este PC editando os vídeos longos do canal Problems EXATAMENTE como o PC do Matheus (skills minecraft-video-editor +
# minecraft-cinematic), com atualização automática do código (versões liberadas no GitHub) e da mídia (canal do Estúdio).
#
#   EstudioProblemsLocal.bat                         (dois cliques; baixa a versão mais nova deste script)
#   powershell -ExecutionPolicy Bypass -File EstudioProblemsLocal.ps1 [-Raiz <pasta>] [-Trabalho <pasta>] [-SemCineCam] [-Midia <pasta MIDIA_editor>]
#
# O que faz (pode rodar de novo: só completa o que falta):
#  1. ferramentas: Git, ffmpeg e uv (winget, escopo do usuário); Python 3.14 + ambiente com as versões exatas (requirements-lock.txt)
#  2. código: clone só de .claude/skills do repositório problemsbloxcreate-lab/editor, na última versão liberada (tag local-v*)
#     e atalhos (junction) em ~/.claude/skills para o Claude Code achar as skills
#  3. Claude Code (instalador oficial) — o login é com a conta Claude da equipe que este PC vai usar
#  4. mídia: da pasta MIDIA_editor (-Midia) ou depois, sozinha, pelo canal do Estúdio (pareamento na 1ª vez)
#  5. CineCam (Minecraft 1.20.1 + Forge, ~2 GB; pule com -SemCineCam) e FilmCraft (baixa sozinho no 1º job)
#  6. serviço em segundo plano que inicia com o Windows (http://127.0.0.1:4790) + checagem (doctor.py)
param(
  [string]$Raiz = (Join-Path $env:LOCALAPPDATA "EstudioProblems"),
  [string]$Trabalho = (Join-Path $env:USERPROFILE "EstudioProblems"),
  [string]$Midia = "",
  [switch]$SemCineCam,
  [string]$Repo = "https://github.com/problemsbloxcreate-lab/editor.git",
  [string]$PyVer = "3.14"
)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
function Passo($t) { Write-Host "`n== $t" -ForegroundColor Cyan }
function Tem($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }
function Recarregar-Path { $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" + [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + $env:Path }
function Winget($id) {
  if (-not (Tem winget)) { throw "winget não encontrado: instale o 'App Installer' pela Microsoft Store e rode de novo." }
  winget install -e --id $id --scope user --accept-source-agreements --accept-package-agreements --silent | Out-Host
  if ($LASTEXITCODE -ne 0) { winget install -e --id $id --accept-source-agreements --accept-package-agreements --silent | Out-Host }
  Recarregar-Path
}

Write-Host "Estúdio Problems Local — instalação em $Raiz (trabalho: $Trabalho)" -ForegroundColor Green
New-Item -ItemType Directory -Force $Raiz, $Trabalho | Out-Null

Passo "1/6 Ferramentas"
if (-not (Tem git)) { Winget "Git.Git" }
if (-not (Tem ffmpeg)) { Winget "Gyan.FFmpeg" }
if (-not (Tem uv)) { Winget "astral-sh.uv" }
foreach ($c in "git", "ffmpeg", "uv") { if (-not (Tem $c)) { throw "$c não ficou disponível; feche e abra o terminal e rode de novo." } }
$Venv = Join-Path $Raiz "venv"
$Py = Join-Path $Venv "Scripts\python.exe"
if (-not (Test-Path $Py)) { uv python install $PyVer; uv venv $Venv --python $PyVer }

Passo "2/6 Código (GitHub, versão liberada)"
$App = Join-Path $Raiz "app"
if (-not (Test-Path (Join-Path $App ".git"))) {
  git clone --filter=blob:none --no-checkout $Repo $App
  git -C $App sparse-checkout set --no-cone ".claude/skills/minecraft-video-editor/" ".claude/skills/minecraft-cinematic/"
}
git -C $App fetch --tags --force --quiet origin
$tag = git -C $App tag --list "local-v*" --sort=-v:refname | Select-Object -First 1
if ($tag) { git -C $App -c advice.detachedHead=false checkout -f $tag } else { git -C $App checkout -f main; Write-Host "  (ainda não há versão liberada: usando a main)" -ForegroundColor Yellow }
$Skills = Join-Path $App ".claude\skills"
$Ed = Join-Path $Skills "minecraft-video-editor"
uv pip install --python $Py -r (Join-Path $Ed "distribuicao\requirements-lock.txt")
$Home2 = Join-Path $env:USERPROFILE ".claude\skills"
New-Item -ItemType Directory -Force $Home2 | Out-Null
foreach ($s in "minecraft-video-editor", "minecraft-cinematic") {
  $dst = Join-Path $Home2 $s
  if (-not (Test-Path $dst)) { New-Item -ItemType Junction -Path $dst -Target (Join-Path $Skills $s) | Out-Null; Write-Host "  ~/.claude/skills/$s -> clone" }
  elseif (-not ((Get-Item $dst).LinkType)) { Write-Host "  ATENÇÃO: $dst já existe e não é atalho do clone; não mexi (o Claude Code vai usar a cópia antiga)." -ForegroundColor Yellow }
}
& $Py -X utf8 (Join-Path $Ed "scripts\paths.py") --set work_dir $Trabalho | Out-Null
& $Py -X utf8 (Join-Path $Ed "scripts\paths.py") --set media_dir (Join-Path $Trabalho "midia") | Out-Null

Passo "3/6 Claude Code"
if (-not (Tem claude)) {
  Invoke-RestMethod https://claude.ai/install.ps1 | Invoke-Expression
  Recarregar-Path
}
if (Tem claude) { Write-Host "  Claude Code: OK. Se ainda não entrou, abra um terminal, rode 'claude' e entre com a conta Claude da equipe deste PC." }
else { Write-Host "  Claude Code não ficou no PATH: feche e abra o terminal depois." -ForegroundColor Yellow }

Passo "4/6 Mídia"
if ($Midia -and (Test-Path (Join-Path $Midia "instalar_midia.py"))) {
  & $Py -X utf8 (Join-Path $Midia "instalar_midia.py") --skills $Skills --sim
} else {
  Write-Host "  A mídia (SFX, músicas, skins, extensão do Premiere) chega sozinha pelo Estúdio depois que você abrir o Editor no site e parear este PC."
}

Passo "5/6 CineCam e FilmCraft"
if (-not $SemCineCam) {
  & $Py -X utf8 (Join-Path $Skills "minecraft-cinematic\scripts\setup_cinecam.py")
} else { Write-Host "  CineCam pulado (-SemCineCam): as cinemáticas ficam desligadas neste PC até rodar setup_cinecam.py." }
Write-Host "  FilmCraft: baixa sozinho no 1º job que precisar."

Passo "6/6 Serviço em segundo plano"
$Pyw = Join-Path $Venv "Scripts\pythonw.exe"
$Srv = Join-Path $Ed "app\server.py"
$Vbs = Join-Path $Raiz "EstudioProblemsLocal.vbs"
@"
' Estúdio Problems Local: serviço sem janela. Código 3 = versão nova instalada -> reabre com o código novo.
Set sh = CreateObject("WScript.Shell")
Do
  rc = sh.Run("""$Pyw"" -X utf8 ""$Srv"" --sem-navegador", 0, True)
  If rc <> 3 Then Exit Do
Loop
"@ | Set-Content -Encoding Unicode $Vbs
$Startup = [Environment]::GetFolderPath("Startup")
$lnk = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $Startup "Estúdio Problems Local.lnk"))
$lnk.TargetPath = "wscript.exe"; $lnk.Arguments = "`"$Vbs`""; $lnk.Save()
$aberto = $false; try { $aberto = (Invoke-WebRequest -UseBasicParsing http://127.0.0.1:4790/api/ping -TimeoutSec 2).StatusCode -eq 200 } catch {}
if (-not $aberto) { Start-Process wscript.exe "`"$Vbs`"" }
& $Py -X utf8 (Join-Path $Ed "scripts\doctor.py")
Write-Host "`nPronto. Página local: http://127.0.0.1:4790  |  No site: Estúdio Problems > Editor > Automático > 'No meu PC'." -ForegroundColor Green
