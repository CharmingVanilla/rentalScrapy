from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from datetime import datetime
import random
from config import  ANTI_DETECTION_CONFIG
from database import(
     save_house_to_db,
     update_csv )
from email_sender import (
    send_email_notification)
from utils import (
    is_work_time, 
    log_work_status, 
    random_delay)

conn = None
cursor = None
driver = None
visited_urls = set()
is_working_time = False
monitoring_active = False

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

