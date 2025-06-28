import sqlite3
import pandas as pd

conn = None
cursor = None
driver = None
visited_urls = set()
is_working_time = False
monitoring_active = False

def init_database():
    """初始化数据库（使用现有数据库结构，不添加时间字段）"""
    global conn, cursor, visited_urls
    
    print("🗄️ 连接现有数据库...")
    
    # 连接现有数据库
    conn = sqlite3.connect("rent_data.db")
    cursor = conn.cursor()

    # 检查表是否存在，如果不存在则创建（保持原有结构）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rent (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        community TEXT,
        area TEXT,
        price TEXT,
        phone TEXT,
        url TEXT UNIQUE
    )
    ''')
    
    conn.commit()

    # 加载已存在的URL
    cursor.execute("SELECT url FROM rent")
    visited_urls = set(row[0] for row in cursor.fetchall())
    print(f"🧠 已有房源记录：{len(visited_urls)} 条")
    
    # 显示最新的几条记录
    cursor.execute("SELECT community, price FROM rent ORDER BY id DESC LIMIT 3")
    recent_records = cursor.fetchall()
    if recent_records:
        print("📋 最新的几条记录:")
        for i, (community, price) in enumerate(recent_records, 1):
            print(f"   {i}. {community} | {price}")

def save_house_to_db(house_info):
    """保存房源到数据库（使用原有数据库结构）"""
    global cursor, conn, visited_urls
    
    try:
        # 检查是否已存在（双重检查）
        cursor.execute("SELECT id FROM rent WHERE url = ?", (house_info['url'],))
        existing = cursor.fetchone()
        
        if existing:
            print(f"⚠️ 房源已存在: {house_info['community']}")
            return False
        
        # 插入新记录（不包含时间字段）
        cursor.execute('''
        INSERT INTO rent (community, area, price, phone, url)
        VALUES (?, ?, ?, ?, ?)
        ''', (house_info['community'], house_info['area'], house_info['price'], 
              house_info['phone'], house_info['url']))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"🆕 新增房源：{house_info['community']} | {house_info['price']}")
            visited_urls.add(house_info['url'])
            return True
        return False
        
    except sqlite3.IntegrityError as e:
        # URL重复的情况
        if "UNIQUE constraint failed" in str(e):
            print(f"⚠️ URL重复，跳过: {house_info['community']}")
            return False
        else:
            print(f"❌ 数据库约束错误: {e}")
            return False
    except Exception as e:
        print(f"❌ 保存房源失败: {e}")
        return False
    
def update_csv():
    """更新CSV文件（使用原有数据库结构）"""
    global conn
    
    try:
        # 直接按ID排序（最新的ID在前面）
        df = pd.read_sql_query("SELECT * FROM rent ORDER BY id DESC", conn)
        df.to_csv("房源信息.csv", index=False, encoding="utf-8-sig")
        print(f"📊 CSV文件已更新，共 {len(df)} 条记录")
    except Exception as e:
        print(f"❌ 更新CSV失败: {e}")