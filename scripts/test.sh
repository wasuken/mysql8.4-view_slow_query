#!/bin/bash

# 1. まずテストテーブルを作成
docker compose exec -T mysql mysql -u testuser -ptestpass testdb << 'EOF'
-- テストテーブル作成
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255),
    name VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT,
    INDEX idx_email(email),
    INDEX idx_created_at(created_at)
);

-- 都度いれると悪魔的な秒数になるのでリセット
DELETE FROM users;
-- サンプルデータ挿入
INSERT INTO users (email, name, description) VALUES
('user1@test.com', 'Test User 1', 'This is a test user with some description'),
('user2@test.com', 'Test User 2', 'Another test user for testing purposes'),
('user3@test.com', 'Test User 3', 'Third test user with more details');

-- データ確認
SELECT COUNT(*) as total_users FROM users;
EOF

# 2. 確実にスロークエリになる複数行クエリ
docker compose exec -T mysql mysql -u testuser -ptestpass testdb << 'EOF'

-- 複雑な複数行クエリ（確実にslow.logに記録される）
SELECT 
    u1.id as user1_id,
    u1.email as user1_email,
    u1.name as user1_name,
    u2.id as user2_id,
    u2.email as user2_email,
    u2.name as user2_name,
    CONCAT(u1.name, ' -> ', u2.name) as relationship,
    LENGTH(CONCAT(u1.description, u2.description)) as total_desc_length,
    SLEEP(8) as delay_seconds
FROM 
    users u1
    CROSS JOIN users u2
WHERE 
    u1.id != u2.id
    AND u1.email LIKE '%test%'
    AND u2.email LIKE '%test%'
    AND LENGTH(u1.name) > 5
    AND LENGTH(u2.name) > 5
ORDER BY 
    u1.created_at DESC,
    u2.created_at DESC,
    total_desc_length DESC
LIMIT 10;

EOF

# 3. より簡単な確実なスロークエリ
docker compose exec -T mysql mysql -u testuser -ptestpass testdb << 'EOF'
-- シンプルな複数行クエリ
SELECT 
    'Critical Test Query' as test_type,
    NOW() as execution_time,
    CONNECTION_ID() as connection_id,
    DATABASE() as current_database,
    USER() as current_user_info,
    SLEEP(12) as sleep_seconds,
    'This is a multi-line query for testing slow query monitoring' as description
FROM DUAL;

EOF

# 4. information_schemaを使った安全なクエリ
docker compose exec -T mysql mysql -u testuser -ptestpass testdb << 'EOF'

-- information_schemaを使った複雑クエリ
SELECT 
    t.table_schema,
    t.table_name,
    t.table_type,
    c.column_name,
    c.data_type,
    c.is_nullable,
    CONCAT(t.table_schema, '.', t.table_name, '.', c.column_name) as full_column_name,
    COUNT(*) OVER (PARTITION BY t.table_schema, t.table_name) as columns_in_table,
    ROW_NUMBER() OVER (PARTITION BY t.table_schema ORDER BY t.table_name, c.ordinal_position) as row_num,
    SLEEP(6) as delay_for_testing
FROM 
    information_schema.tables t
    INNER JOIN information_schema.columns c 
        ON t.table_schema = c.table_schema 
        AND t.table_name = c.table_name
WHERE 
    t.table_schema = 'testdb'
    AND t.table_type = 'BASE TABLE'
    AND c.data_type IN ('int', 'varchar', 'text', 'timestamp')
ORDER BY 
    t.table_name ASC,
    c.ordinal_position ASC
LIMIT 50;

EOF
