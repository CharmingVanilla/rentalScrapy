# email_notifier.py

import smtplib
from email.mime.text import MIMEText
from email.header import Header

# ⚠️ 修改为你的邮箱和授权码
MAIL_USER = "你的QQ邮箱@qq.com"
MAIL_PASS = "你的授权码"
MAIL_HOST = "smtp.qq.com"
MAIL_PORT = 465  # QQ 邮箱用 SSL

def send_email(subject, content, to_email=None):
    sender = MAIL_USER
    receivers = [to_email or MAIL_USER]  # 默认发给自己

    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = Header("房源爬虫提醒", 'utf-8')
    message['To'] = Header("你", 'utf-8')
    message['Subject'] = Header(subject, 'utf-8')

    try:
        smtpObj = smtplib.SMTP_SSL(MAIL_HOST, MAIL_PORT)
        smtpObj.login(MAIL_USER, MAIL_PASS)
        smtpObj.sendmail(sender, receivers, message.as_string())
        print("📧 提醒邮件已发送")
    except Exception as e:
        print("❌ 邮件发送失败：", e)
