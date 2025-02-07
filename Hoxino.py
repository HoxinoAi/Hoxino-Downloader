from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMessageBox
from PyQt6.QtGui import QIcon
from ui.Main_ui import MainUI
from queuemanagement.queuemanagement import QueueManagement
import sys
import os

def main():
    # 初始化应用
    app = QApplication(sys.argv)
    
    # 检查系统托盘是否可用
    if not QSystemTrayIcon.isSystemTrayAvailable():
        QMessageBox.critical(None, "系统托盘",
                           "系统托盘不可用，程序无法正常运行")
        sys.exit(1)

    # 设置应用程序图标
    icon_path = os.path.join("resources", "icons", "app_icon.png")
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
    
    # 初始化队列文件
    queue_manager = QueueManagement()
    queue_manager.initialize_queue_files()
    
    # 设置应用程序不会在最后一个窗口关闭时退出
    app.setQuitOnLastWindowClosed(False)
    
    # 创建并显示主窗口
    window = MainUI()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
