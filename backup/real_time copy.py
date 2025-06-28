def main():
    """主函数"""
    print("🏠 智能房源监控系统启动（反爬虫增强版）")
    print("=" * 60)
    
    # 显示工作时间和反爬虫配置
    min_interval = WORK_TIME_CONFIG['check_interval']['min']
    max_interval = WORK_TIME_CONFIG['check_interval']['max']
    print(f"⏰ 工作时间: {WORK_TIME_CONFIG['start_time']} - {WORK_TIME_CONFIG['end_time']}")
    print(f"🔄 检查频率: 随机 {min_interval}-{max_interval} 分钟")
    print(f"🎭 反爬虫措施: 多User-Agent + 随机延迟 + 人类行为模拟")
    print(f"🎯 每次最多检查: {ANTI_DETECTION_CONFIG['max_houses_per_session']} 个房源")
    print("=" * 60)
    
    # 检查邮箱配置
    if EMAIL_CONFIG['sender_email'] == 'your_email@qq.com':
        print("⚠️ 请先配置邮箱信息!")
        print("修改 EMAIL_CONFIG 中的:")
        print("- sender_email: 你的邮箱")
        print("- sender_password: 你的邮箱授权码")
        print("- receiver_email: 接收通知的邮箱")
        print("=" * 60)
        return
    
    try:
        # 初始化
        init_database()
        init_browser()
        
        # 检查当前是否应该工作
        current_time = datetime.now().strftime('%H:%M:%S')
        if is_work_time():
            print(f"🟢 {current_time} - 当前在工作时间内，立即开始监控")
            start_work_session()
            #monitor_first_page()  # 立即执行一次
            simple_test_monitor()
        else:
            print(f"🔴 {current_time} - 当前不在工作时间内")
            start_time = WORK_TIME_CONFIG['start_time']
            print(f"   ⏰ 将在 {start_time} 自动开始监控")
        
        # 设置动态定时任务
        schedule.every(1).minutes.do(check_and_update_work_status)  # 每分钟检查工作状态
        
        print(f"⏰ 动态定时任务已设置")
        print("💡 按 Ctrl+C 停止监控")
        print("📧 系统状态变化时会发送邮件通知")
        print("🛡️ 反爬虫保护已启用")
        print("=" * 60)
        
        # 下次监控时间
        next_check_time = None
        
        # 运行定时任务
        while True:
            schedule.run_pending()
            
            # 如果在工作时间且到了检查时间
            if is_work_time() and monitoring_active:
                current_time = datetime.now()
                
                if next_check_time is None or current_time >= next_check_time:
                    # 执行监控
                    monitor_first_page()
                    
                    # 设置下次检查时间（随机间隔）
                    # next_interval = get_next_check_interval()
                    # next_check_time = current_time + pd.Timedelta(minutes=next_interval)
                    # print(f"⏰ 下次检查时间: {next_check_time.strftime('%H:%M:%S')} (间隔 {next_interval} 分钟)")
                    
                    try:
                        # 设置下次检查时间（随机间隔）
                        next_interval = get_next_check_interval()
                        print(f"🔍 调试 - next_interval: {next_interval}, 类型: {type(next_interval)}")
                        
                        next_check_time = current_time + pd.Timedelta(minutes=next_interval)
                        print(f"⏰ 下次检查时间: {next_check_time.strftime('%H:%M:%S')} (间隔 {next_interval} 分钟)")
                        
                    except Exception as e:
                        print(f"❌ 时间计算错误: {e}")
                        print(f"错误类型: {type(e)}")
                        try:
                            print(f"next_interval: {next_interval}")
                            print(f"next_interval 类型: {type(next_interval)}")
                        except:
                            print("next_interval 未定义")
                        
                        # 使用备用方案 - 设置1分钟后继续
                        print("⏰ 使用备用延迟方案，1分钟后继续...")
                        import time
                        current_time = pd.Timestamp.now()
                        #next_check_time = current_time + pd.Timedelta(minutes=1)
                        next_check_time = current_time + timedelta(minutes=1)
                        print(f"⏰ 备用下次检查时间: {next_check_time.strftime('%H:%M:%S')}")

            time.sleep(30)  # 每30秒检查一次任务
            
    except KeyboardInterrupt:
        print("\n🛑 用户中断监控")
        # 如果在工作时间被中断，发送通知
        if monitoring_active:
            try:
                interrupt_notification = [{
                    'community': '系统通知',
                    'area': '监控中断',
                    'price': f"中断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    'phone': '用户手动',
                    'url': '无'
                }]
                send_work_status_email("⚠️ 房源监控系统被中断", interrupt_notification, is_start=False)
            except:
                pass
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
    finally:
        cleanup()


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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
import schedule
from datetime import datetime, timedelta
from datetime import time as dt_time
import logging
import random

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'monitor_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

# 邮件配置 - 请修改为你的邮箱信息
EMAIL_CONFIG = {
    'smtp_server': 'smtp.qq.com',          # QQ邮箱，其他邮箱请修改
    'smtp_port': 587,
    'sender_email': '2113037343@qq.com',   # 发送方邮箱
    'sender_password': 'xtytizjzrpoybhha',   # 邮箱授权码
    'receiver_email': '2113037343@qq.com'    # 接收方邮箱
}

# 工作时间配置
WORK_TIME_CONFIG = {
    'start_time': '06:00',  # 早上6点开始工作
    'end_time': '23:59',    # 晚上11:59结束工作（避免跨天问题）
    'check_interval': {'min': 5, 'max': 15}  # 随机间隔5-15分钟
}

# 反爬虫配置
ANTI_DETECTION_CONFIG = {
    'user_agents': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
    ],
    'page_delays': {'min': 3, 'max': 8},      # 页面间延迟3-8秒
    'action_delays': {'min': 1, 'max': 4},    # 操作间延迟1-4秒
    'scroll_probability': 0.7,                # 70%概率进行滚动
    'max_houses_per_session': 8               # 每次最多检查8个房源
}

# 全局变量
conn = None
cursor = None
driver = None
visited_urls = set()
is_working_time = False
monitoring_active = False

def is_work_time():
    """检查当前是否在工作时间内"""
    current_time = datetime.now().time()
    start_time = dt_time.fromisoformat(WORK_TIME_CONFIG['start_time'])
    end_time = dt_time.fromisoformat(WORK_TIME_CONFIG['end_time'])
    
    return start_time <= current_time <= end_time

def log_work_status():
    """记录工作状态"""
    current_time = datetime.now().strftime('%H:%M:%S')
    if is_work_time():
        print(f"🟢 {current_time} - 工作时间内，监控活跃")
    else:
        start_time = WORK_TIME_CONFIG['start_time']
        end_time = WORK_TIME_CONFIG['end_time']
        print(f"🔴 {current_time} - 非工作时间，监控暂停")
        print(f"   ⏰ 工作时间: {start_time} - {end_time}")

def start_work_session():
    """开始工作会话"""
    global monitoring_active
    
    if not monitoring_active:
        print(f"\n🌅 {datetime.now().strftime('%H:%M:%S')} - 开始今日房源监控")
        print("=" * 60)
        monitoring_active = True
        
        # 发送开始工作通知邮件
        try:
            start_notification = [{
                'community': '系统通知',
                'area': '监控启动',
                'price': f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                'phone': '系统自动',
                'url': '无'
            }]
            send_work_status_email("🌅 房源监控系统启动", start_notification, is_start=True)
        except:
            pass

def end_work_session():
    """结束工作会话"""
    global monitoring_active
    
    if monitoring_active:
        print(f"\n🌙 {datetime.now().strftime('%H:%M:%S')} - 结束今日房源监控")
        print("=" * 60)
        monitoring_active = False
        
        # 发送结束工作通知邮件
        try:
            # 获取今日新增房源统计（通过ID范围估算）
            cursor.execute("SELECT COUNT(*) FROM rent")
            total_count = cursor.fetchone()[0] if cursor.fetchone() else 0
            
            end_notification = [{
                'community': '系统通知',
                'area': '监控结束', 
                'price': f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                'phone': f'数据库总计: {total_count}套',
                'url': '无'
            }]
            send_work_status_email("🌙 房源监控系统结束", end_notification, is_start=False)
        except:
            pass

def send_work_status_email(subject, info_list, is_start=True):
    """发送工作状态邮件"""
    try:
        if is_start:
            body = f"房源监控系统已启动 🌅\n\n"
            body += f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            body += f"工作时间: {WORK_TIME_CONFIG['start_time']} - {WORK_TIME_CONFIG['end_time']}\n"
            body += f"检查频率: 每{WORK_TIME_CONFIG['check_interval']}分钟\n\n"
            body += "系统将在工作时间内自动监控第一页房源，\n发现新房源时会立即发送邮件通知。\n\n"
            body += "祝您找到心仪的房子！ 🏠"
        else:
            body = f"房源监控系统已结束 🌙\n\n"
            body += f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            # 添加统计信息
            try:
                cursor.execute("SELECT COUNT(*) FROM rent")
                result = cursor.fetchone()
                total_count = result[0] if result else 0
                body += f"数据库总计房源: {total_count} 套\n\n"
            except:
                body += "统计信息获取失败\n\n"
                
            body += "系统将在明天工作时间自动重新启动。\n\n"
            body += "晚安！明天继续为您监控房源 😴"
        
        # 发送邮件
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['receiver_email']  
        msg['Subject'] = Header(subject, 'utf-8')
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        server.send_message(msg)
        server.quit()
        
        print(f"📧 {'启动' if is_start else '结束'}通知邮件发送成功")
        
    except Exception as e:
        print(f"❌ 状态邮件发送失败: {e}")

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

def init_browser():
    """初始化浏览器（增强反检测）"""
    global driver
    
    print("🚗 初始化反检测浏览器...")
    
    options = Options()
    options.add_argument('--headless')  # 无界面运行，如果想看到浏览器可以注释这行
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1366,768')  # 常见分辨率
    
    # 反检测配置
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-extensions')
    options.add_argument('--no-first-run')
    options.add_argument('--disable-default-apps')
    options.add_argument('--disable-background-networking')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-features=TranslateUI')
    options.add_argument('--disable-web-security')
    
    # 随机选择用户代理
    user_agent = random.choice(ANTI_DETECTION_CONFIG['user_agents'])
    options.add_argument(f'--user-agent={user_agent}')
    print(f"🎭 使用用户代理: {user_agent[:50]}...")
    
    # 禁用自动化特征
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # 设置首选项
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.managed_default_content_settings.images": 1  # 允许图片，更像真实用户
    }
    options.add_experimental_option("prefs", prefs)
    
    driver = webdriver.Chrome(options=options)
    
    # JavaScript反检测
    driver.execute_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en-US', 'en']});
        Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
        
        // 删除automation标识
        delete window.chrome;
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        // 模拟真实浏览器的一些属性
        Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
        Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
    """)
    
    print("✅ 反检测浏览器初始化完成")

def human_like_behavior():
    """模拟人类行为"""
    global driver
    
    try:
        # 随机滚动行为
        if random.random() < ANTI_DETECTION_CONFIG['scroll_probability']:
            scroll_actions = [
                lambda: driver.execute_script("window.scrollTo(0, Math.random() * 500);"),
                lambda: driver.execute_script("window.scrollBy(0, Math.random() * 300);"),
                lambda: driver.execute_script("window.scrollTo(0, document.body.scrollHeight * Math.random());")
            ]
            
            # 执行1-3个滚动动作
            num_actions = random.randint(1, 3)
            for _ in range(num_actions):
                action = random.choice(scroll_actions)
                action()
                time.sleep(random.uniform(0.5, 1.5))
        
        # 随机鼠标移动（在headless模式下虽然不可见，但会执行）
        if random.random() < 0.3:  # 30%概率
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(driver)
                # 移动到页面中的随机位置
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                actions.move_by_offset(x, y).perform()
                time.sleep(random.uniform(0.3, 0.8))
            except:
                pass
                
    except Exception as e:
        # 静默处理错误，不影响主流程
        pass

def random_delay(delay_type='page'):
    """随机延迟"""
    if delay_type == 'page':
        delay_range = ANTI_DETECTION_CONFIG['page_delays']
    else:
        delay_range = ANTI_DETECTION_CONFIG['action_delays']
    
    delay = random.uniform(delay_range['min'], delay_range['max'])
    print(f"⏳ 随机等待 {delay:.1f} 秒...")
    time.sleep(delay)

def get_next_check_interval():
    """获取下次检查的随机间隔"""
    min_interval = WORK_TIME_CONFIG['check_interval']['min']
    max_interval = WORK_TIME_CONFIG['check_interval']['max']
    interval = random.randint(min_interval, max_interval)
    return interval

def send_email_notification(new_houses):
    """发送邮件通知"""
    if not new_houses:
        return
        
    try:
        print(f"📧 准备发送邮件通知 {len(new_houses)} 套新房源...")
        
        # 邮件主题
        subject = f"🏠 发现 {len(new_houses)} 套新房源！"
        
        # 邮件正文
        body = f"在 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 发现 {len(new_houses)} 套新房源:\n\n"
        
        for i, house in enumerate(new_houses, 1):
            body += f"【房源 {i}】\n"
            body += f"小区: {house['community']}\n"
            body += f"面积: {house['area']}\n"
            body += f"租金: {house['price']}\n"
            body += f"电话: {house['phone']}\n"
            body += f"链接: {house['url']}\n"
            body += "-" * 50 + "\n"
        
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['receiver_email']
        msg['Subject'] = Header(subject, 'utf-8')
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 发送邮件
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port'])
        server.starttls()
        server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
        server.send_message(msg)
        server.quit()
        
        print(f"✅ 邮件发送成功！通知了 {len(new_houses)} 套新房源")
        
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")

def extract_house_info(url):
    """提取单个房源信息（增强反检测）"""
    global driver, visited_urls
    
    try:
        # 随机延迟访问
        access_delay = random.uniform(2, 5)
        time.sleep(access_delay)
        
        driver.get(url)
        
        # 模拟真实用户的页面加载等待
        load_delay = random.uniform(3, 6)
        time.sleep(load_delay)

        # 等待页面关键元素加载
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
        except:
            print(f"⚠️ 页面加载超时: {url}")
            return None
        
        # 模拟用户浏览行为
        human_like_behavior()

        # 获取真实URL
        try:
            canonical_url = driver.find_element(By.CSS_SELECTOR, 'link[rel="canonical"]').get_attribute("href").strip()
            if canonical_url.startswith("//"):
                canonical_url = "https:" + canonical_url
            url = canonical_url
        except:
            url = driver.current_url
        
        # 检查是否已存在
        if url in visited_urls:
            return None

        # 模拟用户查看页面的行为
        view_delay = random.uniform(2, 4)
        time.sleep(view_delay)

        # 获取电话 - 增加更多反检测措施
        try:
            # 随机等待，模拟用户寻找电话按钮的时间
            search_delay = random.uniform(1, 3)
            time.sleep(search_delay)
            
            button = driver.find_element(By.ID, "showmoretel")
            
            # 模拟鼠标悬停
            if random.random() < 0.5:
                try:
                    from selenium.webdriver.common.action_chains import ActionChains
                    actions = ActionChains(driver)
                    actions.move_to_element(button).perform()
                    time.sleep(random.uniform(0.5, 1.5))
                except:
                    pass
            
            # 点击前的短暂延迟
            time.sleep(random.uniform(0.5, 1.5))
            button.click()
            
            # 等待电话号码加载，模拟网络延迟
            phone_load_delay = random.uniform(2, 4)
            time.sleep(phone_load_delay)
            
            phone = driver.find_element(By.ID, "nocallname").text.strip()
        except:
            print(f"❌ 无法获取电话，跳过: {url}")
            return None

        # 模拟用户记录信息的时间
        record_delay = random.uniform(1, 2)
        time.sleep(record_delay)

        # 其余信息提取逻辑保持不变...
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

        # 获取租金
        try:
            price_number = driver.find_element(By.CSS_SELECTOR, "span.f24.arial.fb").text.strip()
            price_unit = driver.find_element(By.XPATH, '//span[contains(text(), "元/月")]').text.strip()
            price = price_number + price_unit
        except:
            price = "未知价格"

        # 获取面积
        try:
            area = driver.find_element(By.CSS_SELECTOR, "span.fb.pr10").text.strip()
        except:
            area = "未知面积"

        return {
            'community': community,
            'area': area,
            'price': price,
            'phone': phone,
            'url': url
        }
        
    except Exception as e:
        print(f"❌ 提取房源信息失败: {e}")
        return None

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

def monitor_first_page():
    """监控第一页房源（增强反检测）"""
    global driver
    
    # 检查是否在工作时间
    if not is_work_time():
        log_work_status()
        return
    
    print(f"\n🔍 开始监控第一页 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 随机选择页面（偶尔访问其他页面，更像真实用户）
        page_urls = [
            "https://jx.fccs.com/rent/search/fr1_so5.html",  # 主要监控页面
            "https://jx.fccs.com/rent/search/fr1_so5_p2.html",  # 偶尔访问
            "https://jx.fccs.com/rent/search/fr1_so5_p3.html"   # 偶尔访问
        ]
        
        # 90%时间访问主页面，10%时间访问其他页面
        if random.random() < 0.9:
            target_url = page_urls[0]
        else:
            target_url = random.choice(page_urls[1:])
            print(f"🎲 随机访问其他页面增加真实性")
        
        print(f"🌐 访问页面: {target_url}")
        driver.get(target_url)
        
        # 随机页面加载延迟
        random_delay('page')
        
        # 模拟人类浏览行为
        human_like_behavior()
        
        # 提取详情页链接
        elements = driver.find_elements(By.CSS_SELECTOR, "li.item.leaselist a")
        detail_links = list(set([el.get_attribute("href") for el in elements if el.get_attribute("href")]))

        print(f"📄 找到 {len(detail_links)} 个房源链接")
        
        # 限制每次检查的房源数量，避免过于频繁
        max_houses = ANTI_DETECTION_CONFIG['max_houses_per_session']
        if len(detail_links) > max_houses:
            # 随机选择要检查的房源
            detail_links = random.sample(detail_links, max_houses)
            print(f"🎯 随机选择 {max_houses} 个房源进行检查")

        new_houses = []
        
        # 检查每个房源
        for i, url in enumerate(detail_links, 1):
            print(f"🔍 检查房源 {i}/{len(detail_links)}")
            
            # 先快速检查是否已存在
            if url in visited_urls:
                print(f"⚠️ 已存在，跳过")
                # 即使跳过也要有延迟，模拟用户思考时间
                random_delay('action')
                continue
            
            # 随机延迟，模拟用户点击间隔
            random_delay('page')
            
            # 提取房源信息
            house_info = extract_house_info(url)
            if house_info:
                # 保存到数据库
                if save_house_to_db(house_info):
                    new_houses.append(house_info)
            
            # 每处理几个房源后，进行一次长延迟
            if i % 3 == 0 and i < len(detail_links):
                long_delay = random.uniform(10, 20)
                print(f"🛌 中场休息 {long_delay:.1f} 秒，模拟用户查看详情...")
                time.sleep(long_delay)

        # 如果有新房源，发送邮件通知
        if new_houses:
            print(f"🎉 发现 {len(new_houses)} 套新房源!")
            send_email_notification(new_houses)
            update_csv()
        else:
            print("📝 没有发现新房源")
        
        # 监控完成后的随机行为
        if random.random() < 0.3:  # 30%概率
            print("🎭 执行随机浏览行为...")
            # 访问首页或其他页面，增加真实性
            random_pages = [
                "https://jx.fccs.com/",
                "https://jx.fccs.com/rent/",
                "https://jx.fccs.com/rent/search/"
            ]
            random_page = random.choice(random_pages)
            driver.get(random_page)
            random_delay('page')
            human_like_behavior()
            
    except Exception as e:
        print(f"❌ 监控过程中发生错误: {e}")
        # 出错后增加额外延迟
        error_delay = random.uniform(30, 60)
        print(f"😴 错误恢复等待 {error_delay:.1f} 秒...")
        time.sleep(error_delay)

def check_and_update_work_status():
    """检查并更新工作状态"""
    global monitoring_active
    
    current_is_work_time = is_work_time()
    
    # 如果当前是工作时间但监控未激活，则启动
    if current_is_work_time and not monitoring_active:
        start_work_session()
    
    # 如果当前不是工作时间但监控仍激活，则结束
    elif not current_is_work_time and monitoring_active:
        end_work_session()

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

def cleanup():
    """清理资源"""
    global driver, conn
    
    print("🧹 正在清理资源...")
    
    if driver:
        driver.quit()
        print("✅ 浏览器已关闭")
    
    if conn:
        conn.close()
        print("✅ 数据库连接已关闭")

def main():
    """主函数"""
    print("🏠 智能房源监控系统启动")
    print("=" * 60)
    
    # 显示工作时间配置
    print(f"⏰ 工作时间: {WORK_TIME_CONFIG['start_time']} - {WORK_TIME_CONFIG['end_time']}")
    print(f"🔄 检查频率: 每{WORK_TIME_CONFIG['check_interval']}分钟")
    print("=" * 60)
    
    # 检查邮箱配置
    if EMAIL_CONFIG['sender_email'] == 'your_email@qq.com':
        print("⚠️ 请先配置邮箱信息!")
        print("修改 EMAIL_CONFIG 中的:")
        print("- sender_email: 你的邮箱")
        print("- sender_password: 你的邮箱授权码")
        print("- receiver_email: 接收通知的邮箱")
        print("=" * 60)
        return
    
    try:
        # 初始化
        init_database()
        init_browser()
        
        # 检查当前是否应该工作
        current_time = datetime.now().strftime('%H:%M:%S')
        if is_work_time():
            print(f"🟢 {current_time} - 当前在工作时间内，立即开始监控")
            start_work_session()
            monitor_first_page()  # 立即执行一次
        else:
            print(f"🔴 {current_time} - 当前不在工作时间内")
            start_time = WORK_TIME_CONFIG['start_time']
            print(f"   ⏰ 将在 {start_time} 自动开始监控")
        
        # 设置定时任务
        schedule.every(WORK_TIME_CONFIG['check_interval']).minutes.do(monitor_first_page)
        schedule.every(1).minutes.do(check_and_update_work_status)  # 每分钟检查工作状态
        
        print(f"⏰ 定时任务已设置")
        print("💡 按 Ctrl+C 停止监控")
        print("📧 系统状态变化时会发送邮件通知")
        print("=" * 60)
        
        # 运行定时任务
        while True:
            schedule.run_pending()
            time.sleep(30)  # 每30秒检查一次任务
            
    except KeyboardInterrupt:
        print("\n🛑 用户中断监控")
        # 如果在工作时间被中断，发送通知
        if monitoring_active:
            try:
                interrupt_notification = [{
                    'community': '系统通知',
                    'area': '监控中断',
                    'price': f"中断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    'phone': '用户手动',
                    'url': '无'
                }]
                send_work_status_email("⚠️ 房源监控系统被中断", interrupt_notification, is_start=False)
            except:
                pass
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
    finally:
        cleanup()

def simple_test_monitor():
    """简化版监控测试"""
    try:
        print("🧪 简化测试开始...")
        
        # 只测试基本的网页访问
        driver.get("https://jx.fccs.com/rent/search/fr1_so5.html")
        print("✅ 网页访问成功")
        
        # 简单延迟
        time.sleep(3)
        print("✅ 延迟完成")
        
        # 查找元素
        elements = driver.find_elements(By.CSS_SELECTOR, "li.item.leaselist a")
        print(f"✅ 找到 {len(elements)} 个元素")
        
        print("🎉 简化测试完成")
        
    except Exception as e:
        print(f"❌ 简化测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()