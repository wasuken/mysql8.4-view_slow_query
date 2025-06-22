.PHONY: start stop analyze report clean

# docker compose起動
start:
	docker compose up -d
	@echo "MySQL started. Waiting for initialization..."
	@sleep 10

# MySQL停止
stop:
	docker compose down

# 基本分析
analyze:
	@echo "Running slow query analysis..."
	docker compose run --rm percona-toolkit pt-query-digest /logs/slow.log

# レポート生成
report:
	@echo "Generating report..."
	docker compose run --rm percona-toolkit pt-query-digest /logs/slow.log > ./reports/report_$(shell date +%Y%m%d_%H%M).txt
	@echo "Report saved to ./reports/"

genlog:
	@echo "Generating Slow query logs..."
	bash ./scripts/gen_slowq.sh
	@echo "finish."


# ログとレポートのクリーンアップ
clean:
	rm -f ./mysql/logs/slow.log
	rm -f ./reports/*.txt

# 完全リセット
reset: stop clean
	docker compose down -v
	docker system prune -f
