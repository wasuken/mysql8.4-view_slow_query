#!/bin/bash
# scripts/generate_slow_queries.sh

echo "Generating test slow queries..."

docker compose exec -T mysql mysql -u testuser -ptestpass testdb <<'EOF'
-- 確実にスロークエリになるテスト
SELECT SLEEP(2), 'Test slow query 1' as description, NOW() as timestamp;
SELECT SLEEP(1.5), 'Test slow query 2' as description, NOW() as timestamp;

-- information_schemaを使った重いクエリ
SELECT 
    table_schema,
    COUNT(*) as table_count,
    SUM(data_length + index_length) as total_size
FROM information_schema.tables 
WHERE table_schema NOT IN ('mysql', 'performance_schema', 'sys')
GROUP BY table_schema;

-- 時間のかかる計算
SELECT 
    n,
    n * n as square,
    SQRT(n) as square_root
FROM (
    SELECT @row := @row + 1 as n
    FROM information_schema.columns c1, 
         information_schema.columns c2,
         (SELECT @row := 0) r
    LIMIT 5000
) numbers
WHERE n % 100 = 0;

EOF

echo "Test queries executed. Check the slow log:"
echo "cat mysql/logs/slow.log"
