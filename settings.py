# 使用容器网络内的服务名连接
DATABASE = {
    'host': 'mysql',          # docker容器名
    'port': 3306,
    'user': 'crawler',
    'password': 'crawler_pass',
    'database': 'property_db',
    'charset': 'utf8mb4'
}

ITEM_PIPELINES = {
    'your_project.pipelines.MySQLPipeline': 300,
}