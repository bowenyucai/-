import datetime
import subprocess
import platform
import time
import psutil
from threading import Timer
from win10toast import ToastNotifier

# --------------------- 配置区域 ---------------------
WEIXIN_PATHS = {
    'Windows': r'C:\Program Files\Tencent\WeChat\WeChat.exe',
    'Darwin': '/Applications/WeChat.app',
}

TENCENT_MEETING_PATHS = {
    'Windows': r'C:\Program Files\Tencent\WeMeet\WeMeetApp.exe',
    'Darwin': '/Applications/TencentMeeting.app',
}

DELAY_MINUTES = 10  # 微信启动后等待时间（分钟）

# --------------------- 功能函数 ---------------------
def show_notification(title, message):
    """显示Windows通知"""
    if platform.system() == 'Windows':
        try:
            ToastNotifier().show_toast(title, message, duration=5)
        except Exception as e:
            print(f"通知发送失败：{str(e)}")

def is_process_running(process_name):
    """检查指定进程是否正在运行"""
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == process_name:
            return True
    return False

def start_tencent_meeting():
    """启动腾讯会议（带检测）"""
    system = platform.system()
    path = TENCENT_MEETING_PATHS.get(system)
    
    if not path:
        print(f"未配置{system}系统的腾讯会议路径")
        return

    process_name = "TencentMeeting.exe" if system == "Windows" else "TencentMeeting"
    
    try:
        if not is_process_running(process_name):
            subprocess.Popen([path])
            show_notification("程序通知", "腾讯会议已自动启动")
        else:
            print("腾讯会议已在运行")
    except Exception as e:
        print(f"腾讯会议启动失败：{str(e)}")
        show_notification("错误通知", f"腾讯会议启动失败：{str(e)}")

def delayed_operation():
    """延时启动腾讯会议"""
    print(f"{DELAY_MINUTES}分钟后启动腾讯会议...")
    time.sleep(DELAY_MINUTES * 60)
    start_tencent_meeting()

# --------------------- 原有功能更新 ---------------------
def launch_wechat():
    system = platform.system()
    path = WEIXIN_PATHS.get(system)
    
    if not path:
        print(f"未配置{system}系统的微信路径")
        return

    try:
        if system == 'Windows':
            subprocess.Popen([path])
            # 启动延时线程
            Timer(0, delayed_operation).start()
        elif system == 'Darwin':
            subprocess.Popen(['open', path])
        print("微信启动成功")
        show_notification("程序通知", "微信已自动启动")
    except Exception as e:
        print(f"启动失败：{str(e)}")
        show_notification("错误通知", f"微信启动失败：{str(e)}")

# ... 原有should_launch()和main逻辑保持不变 ...