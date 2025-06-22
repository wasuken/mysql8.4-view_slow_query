#!/bin/bash
# setup_discord.sh

echo "🔧 MySQL Slow Query Monitor Setup (Discord対応)"

# Webhook URL設定
read -p "Discord Webhook URL: " DISCORD_WEBHOOK
read -p "Slack Webhook URL (optional): " SLACK_WEBHOOK

# .envファイル生成
cat > .env << EOF
SLACK_WEBHOOK=$SLACK_WEBHOOK
DISCORD_WEBHOOK=$DISCORD_WEBHOOK
CRITICAL_THRESHOLD=10
WARNING_THRESHOLD=5
EOF

echo "✅ Configuration saved to .env"

# ディレクトリ作成
mkdir -p monitor mysql/{conf.d,logs} reports scripts

# requirements.txt作成
cat > monitor/requirements.txt << EOF
requests==2.31.0
watchdog==3.0.0
EOF

echo "🚀 Setup complete! Run: docker compose up -d"
