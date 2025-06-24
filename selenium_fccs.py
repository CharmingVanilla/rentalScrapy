from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import csv
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import sqlite3
import pandas as pd
from email_notifier import send_email


# 连接数据库（自动创建）
conn = sqlite3.connect("rent_data.db")
cursor = conn.cursor()

# 创建表（只会创建一次）
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

# ✅ 一次性读出所有已存的 URL，放进集合中
cursor.execute("SELECT url FROM rent")
visited_urls = set(row[0] for row in cursor.fetchall())
print(f"🧠 已有房源记录：{len(visited_urls)} 条")

# 初始化浏览器
options = Options()
# options.add_argument('--headless')  # 可选：无界面运行
options.add_argument('--disable-gpu')
driver = webdriver.Chrome(options=options)

# 多页链接
max_page = 59
page_urls = [f"https://jx.fccs.com/rent/search/p{i}.html" for i in range(7, max_page + 1)]

results = []

for page_url in page_urls:
    print(f"\n📄 正在抓取页面：{page_url}")
    driver.get(page_url)
    time.sleep(2)

    # 提取所有详情页链接
    elements = driver.find_elements(By.CSS_SELECTOR, "li.item.leaselist a")
    detail_links = list(set([el.get_attribute("href") for el in elements if el.get_attribute("href")]))

    print(f"  - 本页共找到 {len(detail_links)} 个房源链接")

    for url in detail_links:
        driver.get(url)
        time.sleep(2)

        # 等待页面加载
        try:
            WebDriverWait(driver, 2).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
        except:
            print("⚠️ 页面加载超时：", url)
            continue

        #✅ 真实 URL
        try:
            url = driver.find_element(By.CSS_SELECTOR, 'link[rel="canonical"]').get_attribute("href").strip()
            if url.startswith("//"):
                url = "https:" + url
        except:
            url = driver.current_url
        
        if url in visited_urls:
            print(f"⚠️ 已存在，跳过：{url}")
            continue

        # ✅ 抓不到电话就跳过该条房源
        try:
            button = driver.find_element(By.ID, "showmoretel")
            button.click()
            time.sleep(1)
            phone = driver.find_element(By.ID, "nocallname").text.strip()
        except:
            print("❌ 无法获取电话，跳过：", driver.current_url)
            continue

        # ✅ 多策略提取小区名
        community = ""
        try:
            match = re.search(r'rongIMChat\.houseMsg\.floor\s*=\s*"([^"]+)"', driver.page_source)
            if match:
                community = match.group(1).strip()
        except:
            pass

        if not community:
            try:
                community = driver.find_element(By.XPATH, '//span[@id="floor"]/following-sibling::a/strong').text.strip()
            except:
                pass

        if not community:
            try:
                community = driver.find_element(By.CSS_SELECTOR, 'a.w_1_6').text.strip()
            except:
                pass

        if not community:
            try:
                li_elements = driver.find_elements(By.CSS_SELECTOR, "ul.house-info li")
                for li in li_elements:
                    if "小区" in li.text and li.find_elements(By.TAG_NAME, "a"):
                        community = li.find_element(By.TAG_NAME, "a").text.strip()
                        break
            except:
                pass

        if not community:
            try:
                title_text = driver.title
                match = re.search(r'[「\[](.+?)[」\]]', title_text)
                if match:
                    community = match.group(1).strip()
            except:
                pass

        if not community:
            try:
                li_elements = driver.find_elements(By.CSS_SELECTOR, "ul.house-info li")
                for li in li_elements:
                    if "地址" in li.text:
                        community = li.text.replace("地址：", "").strip()
                        break
            except:
                pass

        if not community:
            community = "未知小区"

        # ✅ 租金
        try:
            price_number = driver.find_element(By.CSS_SELECTOR, "span.f24.arial.fb").text.strip()
            price_unit = driver.find_element(By.XPATH, '//span[contains(text(), "元/月")]').text.strip()
            price = price_number + price_unit
        except:
            price = ""

        # ✅ 面积
        try:
            area = driver.find_element(By.CSS_SELECTOR, "span.fb.pr10").text.strip()
        except:
            area = ""



        # # ✅ 保存页面（可选）
        # with open("debug_detail.html", "w", encoding="utf-8") as f:
        #     f.write(driver.page_source)

        print(f"✅ {community} | {area} | {price} | {phone} | {url}")
        #results.append([community, area, price, phone, url])
        
        cursor.execute('''
        INSERT OR IGNORE INTO rent (community, area, price, phone, url)
        VALUES (?, ?, ?, ?, ?)
        ''', (community, area, price, phone, url))
        conn.commit()

        if cursor.rowcount > 0:
            print(f"🆕 新增房源：{community} | {price}")
            visited_urls.add(url)
            # msg = f"小区：{community}\n面积：{area}\n价格：{price}\n电话：{phone}\n链接：{url}"
            # send_email("发现新房源！", msg)
        
conn = sqlite3.connect("rent_data.db")
df = pd.read_sql_query("SELECT * FROM rent", conn)
df.to_csv("房源信息.csv", index=False, encoding="utf-8-sig")


# # 保存为 CSV
# with open("房源信息.csv", "w", encoding="utf-8-sig", newline="") as f:
#     writer = csv.writer(f)
#     writer.writerow(["小区", "面积", "租金", "电话", "详情链接"])
#     writer.writerows(results)

driver.quit()
print("\n🎉 全部抓取完成，数据已保存到 房源信息.csv")
