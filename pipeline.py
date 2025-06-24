# pipelines.py
import pymysql

class MySQLPipeline:
    def __init__(self):
        self.conn = pymysql.connect(
            host='mysql',
            user='crawler',
            password='crawler_pass',
            database='property_db',
            charset='utf8mb4'
        )
        self.cursor = self.conn.cursor()

    def process_item(self, item, spider):
        sql = """
        INSERT INTO properties (title, price, url, phone, address)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE phone=VALUES(phone), price=VALUES(price)
        """
        self.cursor.execute(sql, (
            item['title'],
            item['price'],
            item['url'],
            item['phone'],
            item['address']
        ))
        self.conn.commit()
        return item

    def close_spider(self, spider):
        self.conn.close()