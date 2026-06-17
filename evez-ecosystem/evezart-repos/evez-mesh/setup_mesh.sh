#!/bin/bash
set -e

echo ">> Initializing EvezArt Unified Environment..."

if ! command -v brew &> /dev/null; then
    echo ">> Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo ">> Homebrew detected."
fi

REPOS=(
    "https://github.com/EvezArt/evez-digital-twin.git"
    "https://github.com/EvezArt/project-nomad-evez.git"
    "https://github.com/EvezArt/evez-mesh.git"
    "https://github.com/EvezArt/evez-synapse-engine.git"
)

mkdir -p ~/evez_stack && cd ~/evez_stack

for repo in "${REPOS[@]}"; do
    dir_name=$(basename "$repo" .git)
    if [ ! -d "$dir_name" ]; then
        echo ">> Cloning $dir_name..."
        git clone "$repo"
    else
        echo ">> $dir_name already exists. Pulling latest..."
        cd "$dir_name" && git pull && cd ..
    fi
done

cd ~/evez_stack/evez-mesh
python3 -m venv venv
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || true
pip install --upgrade pip
pip install playwright python-telegram-bot cryptography

playwrightinstall chromium

echo ">> System environment successfully configured."
echo ""
echo "Next steps:"
echo "  1. cd ~/evez_stack/project-nomad-evez && python3 nomad_vault.py"
echo "  2. Edit nomad_vault.py to seed your TELEGRAM_BOT_TOKEN"
echo "  3. sudo cp ~/evez_stack/evez-mesh/evez_daemon.service /etc/systemd/system/"
echo "  4. sudo systemctl enable evez_daemon && sudo systemctl start evez_daemon"
