from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from config import WORK_TIME_CONFIG,EMAIL_CONFIG
conn = None
cursor = None
driver = None
visited_urls = set()
is_working_time = False
monitoring_active = False



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
