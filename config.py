from datetime import datetime
import logging
import os


# # 配置日志
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler(f'monitor_{datetime.now().strftime("%Y%m%d")}.log'),
#         logging.StreamHandler()
#     ]
# )
# 配置日志
log_dir = 'monitor'
log_filename = f'monitor_{datetime.now().strftime("%Y%m%d")}.log'
log_filepath = os.path.join(log_dir, log_filename)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filepath, encoding='utf-8'),
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
    'check_interval': {'min': 5, 'max': 8}  # 随机间隔1-2分钟
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


# GLOBAL_STATE = {
#     'monitoring_active': False,
#     'driver': None,
#     'conn': None,
#     'cursor': None,
#     'visited_urls': set(),
#     'next_check_time': None
# }

