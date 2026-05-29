#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$PROJECT_DIR/.venv"
AUTOSTART_DIR="$HOME/.config/autostart"
DESKTOP_FILE="$AUTOSTART_DIR/pessoal-pappers.desktop"

echo "Criando ambiente virtual..."
python3 -m venv "$VENV"

echo "Instalando dependências..."
"$VENV/bin/pip" install --upgrade pip -q
"$VENV/bin/pip" install -r "$PROJECT_DIR/requirements.txt" -q

echo "Registrando autostart..."
mkdir -p "$AUTOSTART_DIR"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Pessoal Pappers
Exec=$VENV/bin/python $PROJECT_DIR/scraper.py
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
EOF

echo ""
echo "Pronto! O script rodará automaticamente toda vez que você ligar o PC."
echo ""
echo "Lembre-se de preencher EMAIL_PASSWORD no arquivo .env com sua senha de app do Gmail."
echo "Gere em: https://myaccount.google.com/apppasswords"
