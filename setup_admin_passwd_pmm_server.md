# パスワード変更

下記でパスワード変更可能

```bash
docker compose exec -t pmm-server change-admin-password your_secure_password
```

# 権限追加

testuserにパフォーマンススキーマへの一部アクセスを許可する権限を追加する

```bash
docker exec mysql8.4 mysql -u root -prootpassword -e "
GRANT SELECT ON performance_schema.events_statements_summary_by_digest TO 'testuser'@'%';
GRANT SELECT ON performance_schema.events_statements_current TO 'testuser'@'%';
GRANT SELECT ON performance_schema.events_statements_history TO 'testuser'@'%';
FLUSH PRIVILEGES;
"
```
