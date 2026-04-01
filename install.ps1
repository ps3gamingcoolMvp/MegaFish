# MegaFish Installer — Windows
# Usage: irm https://megafish.sh/install.ps1 | iex

$ErrorActionPreference = "Stop"

$REPO        = "https://github.com/ps3gamingcoolMvp/MegaFish.git"
$INSTALL_DIR = "$env:USERPROFILE\.megafish\app"
$MARKER_DIR  = "$env:USERPROFILE\.megafish"

function ok($msg)   { Write-Host "  ✓ $msg" -ForegroundColor Red }
function run($msg)  { Write-Host "  ● $msg..." -ForegroundColor Red }
function fail($msg) { Write-Host "  ✗ $msg" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host @"
                          .
                          A       ;
                |   ,--,-/ \---,-/|  ,
               _|\,'. /|      /|   ``/|-.
           \`.'    /|      ,            ``;.
          ,'\   A     A         A   A _ /| ``.;
        ,/  _              A       _  / _   /|  ;
       /\  / \   ,  ,           A  /    /     ``/|
      /_| | _ \         ,     ,             ,/  \
     // | |/ ``.\  ,-      ,       ,   ,/ ,/      \/
     / @| |@  / /'   \  \      ,              >  /|    ,--.
    |\_/   \_/ /      |  |           ,  ,/        \  ./' __:..
    |  __ __  |       |  | .--.  ,         >  >   |-'   /     ``
  ,/| /  '  \ |       |  |     \      ,           |    /
 /  |<--.__,->|       |  | .    ``.        >  >    /   (
/_,' \\  ^  /  \     /  /   ``.    >--            /^\   |
      \\___/    \   /  /      \__'     \   \   \/   \  |
       ``.   |/          ,  ,                  /``\    \  )
         \  '  |/    ,       V    \          /        ``-\
          ``|/  '  V      V           \    \.'            \_
           '``-.       V       V        \./'\
               ``|/-.      \ /   \ /,---``\
                /   ``._____V_____V'
                           '     '
"@ -ForegroundColor Red

Write-Host @"
███╗   ███╗███████╗ ██████╗  █████╗ ███████╗██╗███████╗██╗  ██╗
████╗ ████║██╔════╝██╔════╝ ██╔══██╗██╔════╝██║██╔════╝██║  ██║
██╔████╔██║█████╗  ██║  ███╗███████║█████╗  ██║███████╗███████║
██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║██╔══╝  ██║╚════██║██╔══██║
██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║██║     ██║███████║██║  ██║
╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝
"@ -ForegroundColor Red

Write-Host "  MegaFish Installer v0.2.0" -ForegroundColor Red
Write-Host "  ──────────────────────────────────────────────────────────────" -ForegroundColor Red
Write-Host ""

# ── Prerequisites ────────────────────────────────────────────────

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    fail "git is required. Install Git for Windows: https://git-scm.com/download/win"
}
ok "git"

$pyOk = $false
foreach ($cmd in @("python3", "python")) {
    if (Get-Command $cmd -ErrorAction SilentlyContinue) {
        $ver = & $cmd -c "import sys; print(sys.version_info >= (3,11))" 2>$null
        if ($ver -eq "True") { $pyOk = $true; $PYTHON = $cmd; break }
    }
}
if (-not $pyOk) {
    fail "Python 3.11+ is required. Install from: https://www.python.org/downloads/"
}
ok "Python 3.11+"

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    fail "Node.js 18+ is required. Install from: https://nodejs.org"
}
ok "Node.js"

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    fail "Docker is required. Install Docker Desktop: https://docker.com/products/docker-desktop"
}
ok "Docker"

if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    fail "Ollama is required. Install from: https://ollama.com/download/windows"
}
ok "Ollama"

# ── Clone repo ───────────────────────────────────────────────────

Write-Host ""
if (Test-Path "$INSTALL_DIR\.git") {
    run "Updating MegaFish"
    git -C $INSTALL_DIR pull --quiet
    ok "Updated"
} else {
    run "Downloading MegaFish"
    New-Item -ItemType Directory -Force -Path (Split-Path $INSTALL_DIR) | Out-Null
    git clone --quiet $REPO $INSTALL_DIR
    ok "Downloaded"
}

# ── Python packages ──────────────────────────────────────────────

run "Installing Python packages"
Set-Location "$INSTALL_DIR\backend"
& $PYTHON -m venv .venv
& ".venv\Scripts\pip" install -r requirements.txt --quiet
ok "Python packages"

# ── Node packages ────────────────────────────────────────────────

run "Installing Node packages"
Set-Location $INSTALL_DIR
npm install --silent
Set-Location frontend
npm install --silent
Set-Location $INSTALL_DIR
ok "Node packages"

# ── Neo4j ────────────────────────────────────────────────────────

run "Starting Neo4j"
$neo4jRunning = docker ps 2>$null | Select-String "megafish-neo4j"
if (-not $neo4jRunning) {
    docker run -d --name megafish-neo4j `
        -p 7474:7474 -p 7687:7687 `
        -e NEO4J_AUTH=neo4j/megafish `
        neo4j:5.18-community 2>$null | Out-Null
}
ok "Neo4j"

# ── .env ─────────────────────────────────────────────────────────

if (-not (Test-Path "$INSTALL_DIR\.env") -and (Test-Path "$INSTALL_DIR\.env.example")) {
    Copy-Item "$INSTALL_DIR\.env.example" "$INSTALL_DIR\.env"
    ok ".env created"
}

# ── megafish command ─────────────────────────────────────────────

run "Installing megafish command"
$batDir  = "$env:USERPROFILE\.megafish\bin"
$batFile = "$batDir\megafish.bat"
New-Item -ItemType Directory -Force -Path $batDir | Out-Null

@"
@echo off
cd /d "$INSTALL_DIR\backend"
".venv\Scripts\python" -m cli.main %*
"@ | Set-Content $batFile

# Add to user PATH if not already there
$userPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($userPath -notlike "*$batDir*") {
    [Environment]::SetEnvironmentVariable("PATH", "$userPath;$batDir", "User")
    Write-Host "  ● Added $batDir to PATH (restart terminal to use megafish)" -ForegroundColor DarkGray
}
ok "megafish command installed"

# ── Marker ───────────────────────────────────────────────────────

New-Item -ItemType Directory -Force -Path $MARKER_DIR | Out-Null
New-Item -ItemType File -Force -Path "$MARKER_DIR\.installed" | Out-Null

# ── Done ─────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  ✓ MegaFish installed." -ForegroundColor Red
Write-Host ""
Write-Host "  Restart your terminal, then run: megafish" -ForegroundColor Red
Write-Host ""

# ── Optional: pull model ─────────────────────────────────────────

$pullModel = Read-Host "  Pull qwen2.5:7b model now? (recommended, ~4.7GB) [y/N]"
if ($pullModel -eq "y" -or $pullModel -eq "Y") {
    run "Pulling qwen2.5:7b (this may take a while)"
    ollama pull qwen2.5:7b
    ok "qwen2.5:7b ready"
    Write-Host ""
}
