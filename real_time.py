import time
import pandas as pd
import schedule
from datetime import datetime
from config import WORK_TIME_CONFIG, ANTI_DETECTION_CONFIG, EMAIL_CONFIG
from utils import (
    is_work_time, 
    get_next_check_interval, 
    check_and_update_work_status,
    cleanup,
    get_next_check_interval,
    start_work_session,
    show_waiting_status
)
from database import (
    init_database
)
from monitor import (
    init_browser,
    monitor_first_page, 
)
from email_sender import(
    send_work_status_email
)

#全局变量
conn = None
cursor = None
driver = None
visited_urls = set()
is_working_time = False
monitoring_active = False

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
            monitor_first_page()  # 立即执行一次
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

        # 初始化时就设置正确的状态
        monitoring_active = is_work_time()
        next_check_time = None
        
        print(f"📊 初始状态：工作时间={is_work_time()}, 监控激活={monitoring_active}")
        print("=" * 60)
        
        while True:
            current_time = datetime.now()
            current_is_work_time = is_work_time()
            
            # 状态变化检测和管理
            if current_is_work_time and not monitoring_active:
                monitoring_active = True
                next_check_time = None  # 重置，立即执行首次监控
                print("🚀 进入工作时间，启动监控...")
                
            elif not current_is_work_time and monitoring_active:
                monitoring_active = False
                next_check_time = None
                print("💤 离开工作时间，停止监控...")
            
            # 执行监控逻辑
            if current_is_work_time and monitoring_active:
                if next_check_time is None or current_time >= next_check_time:
                    try:
                        print(f"\n🔍 开始执行监控 - {current_time.strftime('%H:%M:%S')}")
                        monitor_first_page()
                        
                        # 设置下次检查时间
                        next_interval = get_next_check_interval()
                        next_check_time = current_time + pd.Timedelta(minutes=next_interval)
                        print(f"✅ 监控完成，下次检查: {next_check_time.strftime('%H:%M:%S')} (间隔 {next_interval} 分钟)")
                        
                    except Exception as e:
                        print(f"❌ 监控出错: {e}")
                        next_check_time = current_time + pd.Timedelta(minutes=1)
                        print(f"🔄 1分钟后重试")
                else:
                    # 显示等待状态
                    show_waiting_status(current_time, next_check_time)
            time.sleep(30)  
            
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
        # # 下次监控时间
        # next_check_time = None
        
        # # 运行定时任务
        # while True:
        #     schedule.run_pending()
        #     print("1")
            
        #     # 如果在工作时间且到了检查时间
        #     if is_work_time() and monitoring_active:
        #         current_time = datetime.now()
        #         print("2")
                
        #         if next_check_time is None or current_time >= next_check_time:
        #             # 执行监控
        #             monitor_first_page()
        #             print("3")                   
        #             # 设置下次检查时间（随机间隔）
        #             next_interval = get_next_check_interval()
        #             next_check_time = current_time + pd.Timedelta(minutes=next_interval)
        #             print(f"⏰ 下次检查时间: {next_check_time.strftime('%H:%M:%S')} (间隔 {next_interval} 分钟)")
        
        #     time.sleep(30)  # 每30秒检查一次任务
            


if __name__ == "__main__":
    main()