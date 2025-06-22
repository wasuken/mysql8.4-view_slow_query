-- MySQL Exporter用ユーザー作成
CREATE USER 'exporter'@'%' IDENTIFIED BY 'exporterpass' WITH MAX_USER_CONNECTIONS 3;
GRANT PROCESS ON *.* TO 'exporter'@'%';
GRANT REPLICATION CLIENT ON *.* TO 'exporter'@'%';
GRANT SELECT ON performance_schema.* TO 'exporter'@'%';
GRANT SELECT ON information_schema.* TO 'exporter'@'%';
FLUSH PRIVILEGES;
