#!/usr/bin/env bash
# ===================================================================
#  Anti-spam botni bepul Linux serverida (Ubuntu/Debian) 24/7 ishlatish.
#
#  Mos keladi: Oracle Cloud Always Free, Google Cloud e2-micro,
#  yoki istalgan Ubuntu VPS.
#
#  ISHLATISH (serverga SSH orqali kirgach):
#    curl -fsSL <shu faylning manzili> -o setup-server.sh
#    bash setup-server.sh
#
#  Yoki fayl allaqachon serverda bo'lsa:
#    bash setup-server.sh
#
#  Skript nima qiladi:
#    - Python va git o'rnatadi
#    - loyihani /opt/antispam-bot ga klonlaydi
#    - virtual muhit yaratib, kutubxonalarni o'rnatadi
#    - tokenni so'rab, .env fayliga xavfsiz saqlaydi
#    - systemd xizmatini yaratadi: server qayta yuklansa ham bot
#      o'zi ishga tushadi, qulab tushsa o'zi qayta ko'tariladi
# ===================================================================

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/ssha70359-ship-it/telegram-bot.git}"
APP_DIR="/opt/antispam-bot"
SERVICE_NAME="antispam-bot"
RUN_USER="${SUDO_USER:-$USER}"

echo
echo "=== Anti-spam bot: serverga o'rnatish ==="
echo

if [ "$(id -u)" -ne 0 ]; then
    echo "XATO: bu skriptni root huquqi bilan ishga tushiring:"
    echo "  sudo bash $0"
    exit 1
fi

# --- 1. Kerakli dasturlar ------------------------------------------
echo "[1/5] Python va git o'rnatilmoqda..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq python3 python3-venv python3-pip git

# --- 2. Loyiha kodi -------------------------------------------------
if [ -d "$APP_DIR/.git" ]; then
    echo "[2/5] Loyiha allaqachon mavjud, yangilanmoqda..."
    git -C "$APP_DIR" pull --ff-only
else
    echo "[2/5] Loyiha klonlanmoqda..."
    echo "      Repozitoriya yopiq (private) bo'lsa, GitHub foydalanuvchi nomi"
    echo "      va Personal Access Token so'raladi."
    git clone "$REPO_URL" "$APP_DIR"
fi

# --- 3. Virtual muhit ----------------------------------------------
echo "[3/5] Kutubxonalar o'rnatilmoqda..."
python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/.venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

# --- 4. Token -------------------------------------------------------
ENV_FILE="$APP_DIR/.env"
if [ -f "$ENV_FILE" ] && grep -q "TELEGRAM_BOT_TOKEN=." "$ENV_FILE"; then
    echo "[4/5] .env fayli allaqachon mavjud, tegilmadi."
else
    echo "[4/5] @BotFather bergan bot tokenini kiriting:"
    read -r -p "TOKEN: " BOT_TOKEN
    if [ -z "$BOT_TOKEN" ]; then
        echo "XATO: token kiritilmadi."
        exit 1
    fi
    cat > "$ENV_FILE" <<EOF
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
SPAM_SCORE_THRESHOLD=3
LOG_LEVEL=INFO
EOF
    chmod 600 "$ENV_FILE"
fi

# --- 5. systemd xizmati ---------------------------------------------
echo "[5/5] Avtomatik ishga tushish sozlanmoqda..."
cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=Telegram anti-spam bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/python $APP_DIR/antispam_bot.py
# Qulab tushsa yoki internet uzilsa - o'zi qayta ko'tariladi
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

chown -R "$RUN_USER" "$APP_DIR"
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

sleep 3
echo
echo "=== TAYYOR ==="
systemctl --no-pager --lines=0 status "$SERVICE_NAME" || true
echo
echo "Foydali buyruqlar:"
echo "  Loglarni jonli ko'rish:   sudo journalctl -u $SERVICE_NAME -f"
echo "  To'xtatish:               sudo systemctl stop $SERVICE_NAME"
echo "  Qayta ishga tushirish:    sudo systemctl restart $SERVICE_NAME"
echo "  Kodni yangilash:          sudo bash $0"
echo
