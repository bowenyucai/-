import sys
import os
import json
import winreg
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QListWidget, QListWidgetItem, QProgressBar,
                             QFileDialog, QMessageBox, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QIcon

class SteamCleanerWorker(QThread):
    """后台工作线程，负责扫描和删除空文件夹"""
    scan_progress = pyqtSignal(int, str)  # 进度百分比, 当前路径
    scan_complete = pyqtSignal(list)      # 扫描完成时发送空文件夹列表
    removal_complete = pyqtSignal()       # 删除完成信号

    def __init__(self, steam_paths):
        super().__init__()
        self.steam_paths = steam_paths
        self.folders_to_remove = []
        self.is_running = True
        self.total_folders = 0
        self.scanned_folders = 0

    def run(self):
        """线程主函数"""
        self.folders_to_remove = self.scan_empty_folders()
        self.scan_complete.emit(self.folders_to_remove)

    def scan_empty_folders(self):
        """扫描所有Steam库中的空文件夹"""
        empty_folders = []
        common_dirs = []
        
        # 收集所有common目录
        for path in self.steam_paths:
            common_path = os.path.join(path, "steamapps", "common")
            if os.path.exists(common_path):
                common_dirs.append(common_path)
        
        # 计算总文件夹数（用于进度显示）
        self.total_folders = sum([sum(1 for _ in os.walk(d)) for d in common_dirs])
        self.scanned_folders = 0
        
        # 扫描每个common目录
        for common_dir in common_dirs:
            if not self.is_running:
                return []
            
            for root, dirs, files in os.walk(common_dir, topdown=False):
                if not self.is_running:
                    return []
                
                # 更新进度
                self.scanned_folders += 1
                progress = int((self.scanned_folders / self.total_folders) * 100) if self.total_folders else 0
                self.scan_progress.emit(progress, root)
                
                # 检查空文件夹
                for name in dirs:
                    dir_path = os.path.join(root, name)
                    try:
                        if not os.listdir(dir_path):  # 文件夹为空
                            empty_folders.append(dir_path)
                    except (PermissionError, FileNotFoundError):
                        continue
        
        return empty_folders

    def remove_empty_folders(self):
        """删除所有空文件夹"""
        for folder in self.folders_to_remove:
            if not self.is_running:
                break
            try:
                shutil.rmtree(folder)
            except Exception as e:
                print(f"删除失败: {folder} - {str(e)}")
        self.removal_complete.emit()

    def stop(self):
        """停止当前操作"""
        self.is_running = False


class SteamCleanerGUI(QMainWindow):
    """Steam空文件夹清理工具主界面"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steam 空文件夹清理工具")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon(self.create_icon()))
        
        # 应用变量
        self.steam_paths = []
        self.empty_folders = []
        self.worker_thread = None
        
        # 初始化UI
        self.init_ui()
        
        # 自动查找Steam路径
        self.find_steam_paths()
    
    def create_icon(self):
        """创建应用图标（简单几何图形）"""
        from PyQt5.QtGui import QPainter, QPixmap
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(0, 100, 200))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 24, 24)
        painter.setBrush(QColor(200, 50, 50))
        painter.drawRect(10, 10, 12, 12)
        painter.end()
        return pixmap
    
    def init_ui(self):
        """初始化用户界面"""
        # 主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题区域
        title_layout = QHBoxLayout()
        title_label = QLabel("Steam 空文件夹清理工具")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: #2c3e50;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Steam路径区域
        path_group = QGroupBox("Steam 库路径")
        path_layout = QVBoxLayout(path_group)
        
        self.path_label = QLabel("未检测到Steam路径")
        self.path_label.setWordWrap(True)
        self.path_label.setStyleSheet("color: #7f8c8d; background: #f8f9fa; padding: 10px; border-radius: 5px;")
        self.path_label.setFont(QFont("Arial", 10))
        
        path_btn_layout = QHBoxLayout()
        self.find_path_btn = QPushButton("自动查找")
        self.find_path_btn.setFont(QFont("Arial", 10))
        self.find_path_btn.setStyleSheet("background-color: #3498db; color: white; padding: 8px;")
        self.find_path_btn.clicked.connect(self.find_steam_paths)
        
        self.manual_path_btn = QPushButton("手动选择")
        self.manual_path_btn.setFont(QFont("Arial", 10))
        self.manual_path_btn.setStyleSheet("background-color: #2ecc71; color: white; padding: 8px;")
        self.manual_path_btn.clicked.connect(self.manual_select_path)
        
        path_btn_layout.addWidget(self.find_path_btn)
        path_btn_layout.addWidget(self.manual_path_btn)
        path_btn_layout.addStretch()
        
        path_layout.addWidget(self.path_label)
        path_layout.addLayout(path_btn_layout)
        
        # 操作区域
        action_layout = QHBoxLayout()
        self.scan_btn = QPushButton("扫描空文件夹")
        self.scan_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.scan_btn.setStyleSheet("background-color: #9b59b6; color: white; padding: 10px;")
        self.scan_btn.setMinimumHeight(40)
        self.scan_btn.clicked.connect(self.start_scan)
        self.scan_btn.setEnabled(False)
        
        self.clean_btn = QPushButton("清理所有空文件夹")
        self.clean_btn.setFont(QFont("Arial", 10, QFont.Bold))
        self.clean_btn.setStyleSheet("background-color: #e74c3c; color: white; padding: 10px;")
        self.clean_btn.setMinimumHeight(40)
        self.clean_btn.clicked.connect(self.start_clean)
        self.clean_btn.setEnabled(False)
        
        action_layout.addWidget(self.scan_btn)
        action_layout.addWidget(self.clean_btn)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFont(QFont("Arial", 9))
        self.progress_bar.setStyleSheet("QProgressBar { height: 25px; }")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("就绪")
        
        # 结果区域
        result_group = QGroupBox("扫描结果")
        result_layout = QVBoxLayout(result_group)
        
        self.result_list = QListWidget()
        self.result_list.setFont(QFont("Arial", 9))
        self.result_list.setStyleSheet("QListWidget { background-color: #f8f9fa; }")
        
        self.result_count = QLabel("找到 0 个空文件夹")
        self.result_count.setFont(QFont("Arial", 10))
        self.result_count.setStyleSheet("color: #7f8c8d; padding: 5px;")
        self.result_count.setAlignment(Qt.AlignRight)
        
        result_layout.addWidget(self.result_list)
        result_layout.addWidget(self.result_count)
        
        # 状态栏
        self.status_bar = QLabel("就绪")
        self.status_bar.setFont(QFont("Arial", 9))
        self.status_bar.setStyleSheet("color: #7f8c8d; background: #ecf0f1; padding: 8px; border-radius: 5px;")
        
        # 添加到主布局
        main_layout.addLayout(title_layout)
        main_layout.addWidget(path_group)
        main_layout.addLayout(action_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(result_group, 1)  # 添加伸缩因子使结果区域可扩展
        main_layout.addWidget(self.status_bar)
    
    def find_steam_paths(self):
        """查找Steam安装路径"""
        paths = []
        
        # Windows注册表查找
        if sys.platform == "win32":
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
                    path = winreg.QueryValueEx(key, "SteamPath")[0]
                    if os.path.isdir(path):
                        paths.append(os.path.normpath(path))
            except Exception:
                pass
            
            # 常见安装路径
            win_paths = [
                os.path.expandvars(r"%ProgramFiles(x86)%\Steam"),
                os.path.expandvars(r"%ProgramFiles%\Steam"),
                r"C:\Program Files (x86)\Steam",
                r"C:\Program Files\Steam"
            ]
            
            for path in win_paths:
                if os.path.isdir(path) and path not in paths:
                    paths.append(path)
        
        # Linux路径
        elif sys.platform == "linux":
            linux_paths = [
                os.path.expanduser("~/.steam/steam"),
                os.path.expanduser("~/.local/share/Steam")
            ]
            for path in linux_paths:
                if os.path.isdir(path) and path not in paths:
                    paths.append(path)
        
        # macOS路径
        elif sys.platform == "darwin":
            mac_paths = [
                os.path.expanduser("~/Library/Application Support/Steam")
            ]
            for path in mac_paths:
                if os.path.isdir(path) and path not in paths:
                    paths.append(path)
        
        # 添加额外的库路径
        if paths:
            main_path = paths[0]
            vdf_path = os.path.join(main_path, "steamapps", "libraryfolders.vdf")
            if os.path.isfile(vdf_path):
                try:
                    with open(vdf_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if '"path"' in line:
                                parts = line.strip().split('"')
                                if len(parts) >= 5:
                                    path = parts[3].replace("\\\\", "\\")
                                    norm_path = os.path.normpath(path)
                                    if os.path.isdir(norm_path) and norm_path not in paths:
                                        paths.append(norm_path)
                except Exception:
                    pass
        
        self.steam_paths = paths
        
        if paths:
            path_text = "检测到以下Steam库路径:\n" + "\n".join(paths)
            self.path_label.setText(path_text)
            self.scan_btn.setEnabled(True)
            self.status_bar.setText(f"找到 {len(paths)} 个Steam库路径")
        else:
            self.path_label.setText("未检测到Steam路径，请手动选择")
            self.status_bar.setText("未找到Steam路径")
    
    def manual_select_path(self):
        """手动选择Steam路径"""
        path = QFileDialog.getExistingDirectory(self, "选择Steam安装目录")
        if path:
            # 验证是否是Steam目录
            steamapps_path = os.path.join(path, "steamapps")
            if os.path.isdir(steamapps_path):
                self.steam_paths = [path]
                self.path_label.setText(f"手动选择路径:\n{path}")
                self.scan_btn.setEnabled(True)
                self.status_bar.setText(f"已选择Steam路径: {path}")
            else:
                QMessageBox.warning(self, "路径无效", "选择的路径不是有效的Steam安装目录")
    
    def start_scan(self):
        """开始扫描空文件夹"""
        if not self.steam_paths:
            QMessageBox.warning(self, "路径错误", "未找到Steam路径，请先选择路径")
            return
        
        # 重置UI状态
        self.result_list.clear()
        self.result_count.setText("找到 0 个空文件夹")
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("扫描中... 0%")
        self.scan_btn.setEnabled(False)
        self.clean_btn.setEnabled(False)
        self.status_bar.setText("正在扫描空文件夹...")
        
        # 创建并启动工作线程
        self.worker_thread = SteamCleanerWorker(self.steam_paths)
        self.worker_thread.scan_progress.connect(self.update_scan_progress)
        self.worker_thread.scan_complete.connect(self.scan_complete)
        self.worker_thread.finished.connect(self.thread_finished)
        self.worker_thread.start()
    
    def update_scan_progress(self, progress, current_path):
        """更新扫描进度"""
        self.progress_bar.setValue(progress)
        self.progress_bar.setFormat(f"扫描中... {progress}%")
        self.status_bar.setText(f"扫描中: {os.path.basename(current_path)}...")
    
    def scan_complete(self, empty_folders):
        """扫描完成处理"""
        self.empty_folders = empty_folders
        
        # 显示结果
        for folder in empty_folders:
            item = QListWidgetItem(folder)
            self.result_list.addItem(item)
        
        count = len(empty_folders)
        self.result_count.setText(f"找到 {count} 个空文件夹")
        
        # 更新UI状态
        if count > 0:
            self.clean_btn.setEnabled(True)
            self.status_bar.setText(f"扫描完成！找到 {count} 个空文件夹")
        else:
            self.status_bar.setText("扫描完成！未找到空文件夹")
        
        self.scan_btn.setEnabled(True)
    
    def start_clean(self):
        """开始清理空文件夹"""
        if not self.empty_folders:
            return
        
        # 确认对话框
        reply = QMessageBox.question(
            self, 
            "确认清理",
            f"确定要删除 {len(self.empty_folders)} 个空文件夹吗？此操作不可撤销！",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.No:
            return
        
        # 更新UI状态
        self.progress_bar.setRange(0, 0)  # 不确定进度模式
        self.progress_bar.setFormat("清理中...")
        self.status_bar.setText("正在删除空文件夹...")
        self.scan_btn.setEnabled(False)
        self.clean_btn.setEnabled(False)
        
        # 启动删除操作
        self.worker_thread.removal_complete.connect(self.clean_complete)
        self.worker_thread.remove_empty_folders()
    
    def clean_complete(self):
        """清理完成处理"""
        # 重置UI
        self.result_list.clear()
        self.result_count.setText("找到 0 个空文件夹")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("就绪")
        
        # 显示结果
        count = len(self.empty_folders)
        self.status_bar.setText(f"清理完成！已删除 {count} 个空文件夹")
        QMessageBox.information(
            self, 
            "清理完成", 
            f"成功删除 {count} 个空文件夹！"
        )
        
        # 重置状态
        self.empty_folders = []
        self.scan_btn.setEnabled(True)
    
    def thread_finished(self):
        """线程完成时清理资源"""
        self.worker_thread = None
    
    def closeEvent(self, event):
        """窗口关闭事件处理"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.stop()
            self.worker_thread.wait(2000)  # 等待线程结束
        
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 设置应用样式
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f7fa;
        }
        QGroupBox {
            font-size: 12px;
            font-weight: bold;
            border: 1px solid #dce4ec;
            border-radius: 5px;
            margin-top: 20px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top center;
            padding: 0 5px;
        }
        QPushButton {
            border-radius: 4px;
            min-width: 80px;
        }
        QPushButton:hover {
            background-color: #3498db;
        }
        QListWidget {
            border: 1px solid #dce4ec;
            border-radius: 4px;
        }
    """)
    
    window = SteamCleanerGUI()
    window.show()
    sys.exit(app.exec_())