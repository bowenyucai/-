import datetime
import ntplib
import os
import socket
from win10toast import ToastNotifier
import logging

# --------------------- 配置区域 ---------------------
NTP_SERVERS = [
    'time.windows.com',
    'pool.ntp.org',
    'ntp.aliyun.com'
]                                     # 可更换为 time.windows.com 等服务器
ALLOWED_DAYS = [0, 2, 4]              # 周一=0，周三=2，周五=4
NOTIFICATION_DURATION = 10            # 通知显示时长（秒）

# --------------------- 核心功能 ---------------------
def get_ntp_time():
    """从NTP服务器获取精确时间"""
    client = ntplib.NTPClient()
    try:
        response = client.request(NTP_SERVERS, version=3, timeout=5)
        return datetime.datetime.fromtimestamp(response.tx_time)
    except (socket.gaierror, ntplib.NTPException) as e:
        raise RuntimeError(f"NTP服务器连接失败：{str(e)}")

def set_system_time(target_time):
    """设置Windows系统时间（需要管理员权限）"""
    try:
        date_str = target_time.strftime("%Y-%m-%d")
        time_str = target_time.strftime("%H:%M:%S")
        os.system(f'date {date_str}')
        os.system(f'time {time_str}')
        return True
    except Exception as e:
        raise RuntimeError(f"时间设置失败：{str(e)}")

def show_notification(title, message):
    """显示Windows通知"""
    try:
        ToastNotifier().show_toast(title, message, duration=NOTIFICATION_DURATION)
    except Exception as e:
        print(f"通知发送失败：{str(e)}")

# --------------------- 主逻辑 ---------------------
def should_calibrate():
    """检查校准条件"""
    now = datetime.datetime.now()
    
    # 检查星期几条件
    if now.weekday() not in ALLOWED_DAYS:
        return False
    
    # 检查时间是否晚于20:00
    if now.time() < datetime.time(20, 0):
        return False
    
    return True

def main():
    if not should_calibrate():
        print("当前不符合校准条件")
        return

    try:
        # 获取网络时间
        ntp_time = get_ntp_time()
        local_time = datetime.datetime.now()
        
        # 计算时间差
        time_diff = abs((ntp_time - local_time).total_seconds())
        
        # 如果误差超过5秒才校准
        if time_diff > 5:
            if set_system_time(ntp_time):
                msg = f"校准成功！\n旧时间：{local_time}\n新时间：{ntp_time}"
                show_notification("系统时间已更新", msg)
        else:
            show_notification("时间检查", "系统时间误差在允许范围内（<5秒）")
            
    except Exception as e:
        show_notification("校准失败", str(e))

logging.basicConfig(filename='time_sync.log', level=logging.INFO)
if __name__ == "__main__":
    main()