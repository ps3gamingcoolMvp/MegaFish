#!/usr/bin/env bash
# MegaFish Installer — macOS & Linux
# Usage: curl -fsSL https://megafish.sh/install.sh | bash

set -e

REPO="https://github.com/Inventor-ai-god/MegaFish.git"
INSTALL_DIR="$HOME/.megafish/app"
WRAPPER="/usr/local/bin/megafish"
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${RED}${BOLD}"
cat << 'FISH'
                          .
                          A       ;
                |   ,--,-/ \---,-/|  ,
               _|\,'. /|      /|   `/|-.
           \`.'    /|      ,            `;.
          ,'\   A     A         A   A _ /| `.;
        ,/  _              A       _  / _   /|  ;
       /\  / \   ,  ,           A  /    /     `/|
      /_| | _ \         ,     ,             ,/  \
     // | |/ `.\  ,-      ,       ,   ,/ ,/      \/
     / @| |@  / /'   \  \      ,              >  /|    ,--.
    |\_/   \_/ /      |  |           ,  ,/        \  ./' __:..
    |  __ __  |       |  | .--.  ,         >  >   |-'   /     `
  ,/| /  '  \ |       |  |     \      ,           |    /
 /  |<--.__,->|       |  | .    `.        >  >    /   (
/_,' \\  ^  /  \     /  /   `.    >--            /^\   |
      \\___/    \   /  /      \__'     \   \   \/   \  |
       `.   |/          ,  ,                  /`\    \  )
         \  '  |/    ,       V    \          /        `-\
          `|/  '  V      V           \    \.'            \_
           '`-.       V       V        \./'\
               `|/-.      \ /   \ /,---`\
                /   `._____V_____V'
                           '     '
FISH

cat << 'LOGO'
███╗   ███╗███████╗ ██████╗  █████╗ ███████╗██╗███████╗██╗  ██╗
████╗ ████║██╔════╝██╔════╝ ██╔══██╗██╔════╝██║██╔════╝██║  ██║
██╔████╔██║█████╗  ██║  ███╗███████║█████╗  ██║███████╗███████║
██║╚██╔╝██║██╔══╝  ██║   ██║██╔══██║██╔══╝  ██║╚════██║██╔══██║
██║ ╚═╝ ██║███████╗╚██████╔╝██║  ██║██║     ██║███████║██║  ██║
╚═╝     ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝
LOGO
echo -e "${NC}"
echo -e "${RED}${BOLD}  MegaFish Installer v0.2.0${NC}"
echo -e "${RED}  ──────────────────────────────────────────────────────────────${NC}"
echo ""

check() { command -v "$1" >/dev/null 2>&1; }
ok()    { echo -e "  ${RED}${BOLD}✓${NC} $1"; }
run()   { echo -e "  ${RED}●${NC} $1..."; }
fail()  { echo -e "  ${RED}${BOLD}✗${NC} $1"; }

OS="$(uname -s)"

# ── Prerequisites ────────────────────────────────────────────────

run "Checking prerequisites"

if ! check git; then
    fail "git is required — install it and re-run."
    exit 1
fi

# Install Homebrew first on macOS if missing
if [[ "$OS" == "Darwin" ]] && ! check brew; then
    run "Installing Homebrew"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    eval "$(/opt/homebrew/bin/brew shellenv)" 2>/dev/null || eval "$(/usr/local/bin/brew shellenv)" 2>/dev/null || true
fi

if ! check python3 || ! python3 -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
    run "Installing Python 3.11"
    if [[ "$OS" == "Darwin" ]]; then
        brew install python@3.11 || true
    elif [[ "$OS" == "Linux" ]]; then
        sudo apt-get install -y python3.11 python3.11-venv 2>/dev/null || true
    fi
fi
ok "Python 3.11+"

if ! check uv; then
    run "Installing uv"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi
ok "uv"

if ! check node || ! node -e "process.exit(parseInt(process.versions.node) >= 18 ? 0 : 1)" 2>/dev/null; then
    run "Installing Node.js"
    if [[ "$OS" == "Darwin" ]]; then
        brew install node || true
    elif [[ "$OS" == "Linux" ]]; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
fi
ok "Node.js 18+"

if check ollama; then
    ok "Ollama"
else
    run "Installing Ollama"
    curl -fsSL https://ollama.com/install.sh | sh
    ok "Ollama"
fi

# ── Clone repo ───────────────────────────────────────────────────

echo ""
if [ -d "$INSTALL_DIR/.git" ]; then
    run "Updating MegaFish"
    git -C "$INSTALL_DIR" pull --quiet
    ok "Updated"
else
    run "Downloading MegaFish"
    mkdir -p "$(dirname "$INSTALL_DIR")"
    git clone --quiet "$REPO" "$INSTALL_DIR"
    ok "Downloaded"
fi

# ── Python packages ──────────────────────────────────────────────

run "Installing Python packages"
cd "$INSTALL_DIR/backend"
uv venv --python 3.11 .venv --quiet 2>/dev/null || true
uv pip install -r requirements.txt --quiet
ok "Python packages"

# ── Node packages ────────────────────────────────────────────────

run "Installing Node packages"
cd "$INSTALL_DIR"
npm install --silent
cd frontend && npm install --silent
ok "Node packages"

# ── Neo4j ────────────────────────────────────────────────────────

run "Installing Neo4j"
if ! check neo4j; then
    brew install neo4j || true
fi
neo4j-admin dbms set-initial-password megafish 2>/dev/null || true
neo4j start 2>/dev/null || true
ok "Neo4j"

# ── .env ─────────────────────────────────────────────────────────

if [ ! -f "$INSTALL_DIR/.env" ] && [ -f "$INSTALL_DIR/.env.example" ]; then
    cp "$INSTALL_DIR/.env.example" "$INSTALL_DIR/.env"
    ok ".env created"
fi

# ── megafish command ─────────────────────────────────────────────

run "Installing megafish command"
VENV_PYTHON="$INSTALL_DIR/backend/.venv/bin/python"
WRAPPER_TMP="$(mktemp)"
cat > "$WRAPPER_TMP" << WRAPEOF
#!/usr/bin/env bash
cd "$INSTALL_DIR/backend"
exec "$VENV_PYTHON" -m cli.main "\$@"
WRAPEOF
sudo mv "$WRAPPER_TMP" "$WRAPPER"
sudo chmod +x "$WRAPPER"
ok "megafish command installed"

# ── Marker ───────────────────────────────────────────────────────

mkdir -p "$HOME/.megafish"
touch "$HOME/.megafish/.installed"

# ── Done ─────────────────────────────────────────────────────────

echo ""
echo -e "  ${RED}${BOLD}✓ MegaFish installed.${NC}"
echo ""
echo -e "  Run: ${RED}${BOLD}megafish${NC}"
echo ""

# ── Optional: pull model ─────────────────────────────────────────

read -p "  Pull qwen2.5:7b model now? (recommended, ~4.7GB) [y/N] " pull_model
if [[ "$pull_model" == "y" || "$pull_model" == "Y" ]]; then
    run "Pulling qwen2.5:7b (this may take a while)"
    ollama pull qwen2.5:7b
    ok "qwen2.5:7b ready"
    echo ""
fi
