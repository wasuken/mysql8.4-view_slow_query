import os
import re
import time
import requests
import json
import hashlib
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SlowQueryHandler(FileSystemEventHandler):
    def __init__(self):
        self.slack_webhook = os.environ.get('SLACK_WEBHOOK')
        self.discord_webhook = os.environ.get('DISCORD_WEBHOOK')
        self.critical_threshold = int(os.environ.get('CRITICAL_THRESHOLD', 10))
        self.warning_threshold = int(os.environ.get('WARNING_THRESHOLD', 5))

        # 通知頻度制御用
        self.last_alerts = {}
        self.cooldown_minutes = 5

        # デバッグ情報
        print("=== INITIALIZATION DEBUG ===")
        print(f"Log file exists: {os.path.exists('/logs/slow.log')}")
        print(f"Log directory: {os.listdir('/logs') if os.path.exists('/logs') else 'Not found'}")
        print(f"Critical threshold: {self.critical_threshold}s")
        print(f"Warning threshold: {self.warning_threshold}s")
        print("============================")

    def on_modified(self, event):
        print(f"📁 File modified: {event.src_path}")
        if event.src_path.endswith('slow.log'):
            print("🔍 slow.log modified, checking queries...")
            self.check_slow_queries()

    def check_slow_queries(self):
        try:
            with open('/logs/slow.log', 'r') as f:
                lines = f.readlines()

            print(f"📊 Log file has {len(lines)} lines")

            # 最新のクエリをチェック
            for i, line in enumerate(reversed(lines)):
                if 'Query_time:' in line:
                    print(f"🕐 Found Query_time line: {line.strip()}")
                    match = re.search(r'Query_time: (\d+\.?\d*)', line)
                    if match:
                        query_time = float(match.group(1))
                        context_lines = lines[-(i+10):]  # より多くのコンテキスト

                        # 実際のクエリを抽出（改良版）
                        actual_query = self.extract_query(context_lines)

                        # クエリのハッシュ生成（重複通知防止）
                        query_hash = hashlib.md5(actual_query.encode()).hexdigest()

                        print(f"⚡ Query detected: {query_time}s")
                        print(f"📝 Query content: {actual_query[:100]}...")

                        if query_time >= self.critical_threshold:
                            print(f"🚨 CRITICAL ALERT: {query_time}s >= {self.critical_threshold}s")
                            if self.should_send_alert(query_hash, 'critical'):
                                self.send_critical_alert(query_time, actual_query, query_hash)
                        elif query_time >= self.warning_threshold:
                            print(f"⚠️ WARNING ALERT: {query_time}s >= {self.warning_threshold}s")
                            if self.should_send_alert(query_hash, 'warning'):
                                self.send_warning_alert(query_time, actual_query, query_hash)
                    break

        except Exception as e:
            print(f"❌ Error monitoring slow queries: {e}")

    def extract_query(self, context_lines):
        """実際のクエリを抽出する改良版"""
        query_lines = []
        found_query_start = False

        for line in context_lines:
            line = line.strip()

            # コメント行はスキップ
            if line.startswith('#') or line.startswith('--'):
                continue

            # 空行はスキップ
            if not line:
                continue

            # SQLキーワードで始まる行を探す
            if re.match(r'^(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)', line, re.IGNORECASE):
                found_query_start = True

            if found_query_start:
                query_lines.append(line)

                # セミコロンで終わったら終了
                if line.endswith(';'):
                    break

        if query_lines:
            return ' '.join(query_lines)
        else:
            # フォールバック：コメント以外の最初の行
            for line in context_lines:
                if not line.startswith('#') and line.strip():
                    return line.strip()
            return "Query not found"

    def should_send_alert(self, query_hash, alert_type):
        """通知頻度制御"""
        now = datetime.now()
        key = f"{query_hash}_{alert_type}"

        if key in self.last_alerts:
            if now - self.last_alerts[key] < timedelta(minutes=self.cooldown_minutes):
                print(f"🔇 Alert suppressed (cooldown): {key}")
                return False

        self.last_alerts[key] = now
        return True

    def send_critical_alert(self, query_time, query_text, query_hash):
        """緊急アラート送信（Discord Embed対応）"""

        print(f"📤 Sending critical alert: {query_time}s")

        # Discord通知（リッチEmbed）
        if self.discord_webhook:
            # クエリテキストを適切な長さに調整
            display_query = query_text
            if len(query_text) > 800:
                display_query = query_text[:800] + "..."

            discord_payload = {
                "username": "MySQL Monitor",
                "avatar_url": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/mysql/mysql-original.svg",
                "embeds": [{
                    "title": "🚨 CRITICAL SLOW QUERY DETECTED",
                    "color": 15158332,  # 赤色
                    "timestamp": datetime.now().isoformat(),
                    "fields": [
                        {
                            "name": "⏱️ Query Time",
                            "value": f"**{query_time} seconds**",
                            "inline": True
                        },
                        {
                            "name": "🎯 Threshold",
                            "value": f"{self.critical_threshold}s",
                            "inline": True
                        },
                        {
                            "name": "🖥️ Server",
                            "value": "MySQL Container",
                            "inline": True
                        },
                        {
                            "name": "📝 SQL Query",
                            "value": f"```sql\n{display_query}\n```",
                            "inline": False
                        },
                        {
                            "name": "🔗 Query Hash",
                            "value": f"`{query_hash[:8]}`",
                            "inline": True
                        },
                        {
                            "name": "🕐 Detection Time",
                            "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            "inline": True
                        }
                    ],
                    "footer": {
                        "text": "MySQL Slow Query Monitor",
                        "icon_url": "https://cdn.jsdelivr.net/gh/devicons/devicon/icons/mysql/mysql-original.svg"
                    }
                }]
            }

            try:
                response = requests.post(self.discord_webhook, json=discord_payload)
                if response.status_code == 204:
                    print("✅ Discord critical alert sent successfully")
                else:
                    print(f"❌ Discord notification failed: {response.status_code}")
                    print(f"Response: {response.text}")
            except Exception as e:
                print(f"❌ Discord error: {e}")

    def send_warning_alert(self, query_time, query_text, query_hash):
        """警告アラート送信"""

        print(f"📤 Sending warning alert: {query_time}s")

        # Discord通知
        if self.discord_webhook:
            display_query = query_text
            if len(query_text) > 400:
                display_query = query_text[:400] + "..."

            discord_payload = {
                "username": "MySQL Monitor",
                "embeds": [{
                    "title": "⚠️ Slow Query Warning",
                    "color": 16776960,  # 黄色
                    "timestamp": datetime.now().isoformat(),
                    "fields": [
                        {
                            "name": "⏱️ Query Time",
                            "value": f"{query_time}s",
                            "inline": True
                        },
                        {
                            "name": "🎯 Warning Threshold",
                            "value": f"{self.warning_threshold}s",
                            "inline": True
                        },
                        {
                            "name": "📝 Query",
                            "value": f"```sql\n{display_query}\n```",
                            "inline": False
                        }
                    ]
                }]
            }

            try:
                response = requests.post(self.discord_webhook, json=discord_payload)
                if response.status_code == 204:
                    print("✅ Discord warning alert sent successfully")
                else:
                    print(f"❌ Discord warning failed: {response.status_code}")
            except Exception as e:
                print(f"❌ Discord warning error: {e}")

if __name__ == "__main__":
    print("🚀 Starting MySQL Slow Query Monitor...")

    event_handler = SlowQueryHandler()
    observer = Observer()
    observer.schedule(event_handler, '/logs', recursive=False)
    observer.start()

    print("MySQL Slow Query Monitor started...")
    print(f"Critical threshold: {event_handler.critical_threshold}s")
    print(f"Warning threshold: {event_handler.warning_threshold}s")
    print(f"Slack webhook: {'Configured' if event_handler.slack_webhook else 'Not configured'}")
    print(f"Discord webhook: {'Configured' if event_handler.discord_webhook else 'Not configured'}")

    # 初期ファイルチェック
    if os.path.exists('/logs/slow.log'):
        print("✅ slow.log file found")
        with open('/logs/slow.log', 'r') as f:
            lines = f.readlines()
        print(f"📊 Current log file has {len(lines)} lines")
    else:
        print("⚠️ slow.log file not found yet")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
