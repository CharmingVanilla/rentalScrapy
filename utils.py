import time
from datetime import datetime
from datetime import time as dt_time
import random
from config import WORK_TIME_CONFIG, ANTI_DETECTION_CONFIG
from email_sender import send_work_status_email
conn = None
cursor = None
driver = None
visited_urls = set()
is_working_time = False
monitoring_active = False

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

def show_waiting_status(current_time, next_check_time):
    """显示等待状态"""
    time_diff = next_check_time - current_time
    if time_diff.total_seconds() > 0:
        minutes = int(time_diff.total_seconds() // 60)
        seconds = int(time_diff.total_seconds() % 60)
        
        # 每分钟显示一次，避免刷屏
        if seconds % 60 == 0:
            print(f"😴 休息中... 还有 {minutes}分{seconds}秒开始下次抓取")