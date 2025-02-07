from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QMessageBox, QCheckBox, QApplication
from PyQt6.QtCore import QSettings, QTimer
from PyQt6.QtGui import QIcon, QAction
import os
import sys

class Backstage:
    def __init__(self, main_window):
        """
        初始化后台管理类
        Args:
            main_window: 主窗口实例
        """
        self.main_window = main_window
        self.settings = QSettings('Hoxino', 'HoxinoDownload')
        
        # 确保托盘图标在初始化时就显示
        self.init_tray()
        print("后台管理初始化完成")  # 添加调试信息
        
    def init_tray(self):
        """初始化系统托盘"""
        self.tray_icon = QSystemTrayIcon(self.main_window)
        
        # 设置托盘图标
        icon_path = os.path.join("resources", "icons", "app_icon.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            print(f"警告: 找不到图标文件 {icon_path}")
            
        # 创建托盘菜单并设置样式
        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                border: 1px solid #3498db;
                border-radius: 6px;
                padding: 5px;
            }
            
            QMenu::item {
                padding: 8px 25px;
                border-radius: 4px;
                margin: 2px 5px;
                color: #ffffff;
                font-family: 'Microsoft YaHei', sans-serif;
            }
            
            QMenu::item:selected {
                background-color: rgba(52, 152, 219, 0.2);
                color: #3498db;
            }
            
            QMenu::separator {
                height: 1px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
                margin: 5px 15px;
            }
            
            QMenu::indicator {
                width: 0px;
                height: 0px;
            }
        """)
        
        # 添加显示/隐藏动作
        show_action = QAction("显示主窗口", self.main_window)
        show_action.triggered.connect(self.show_main_window)
        tray_menu.addAction(show_action)
        
        # 添加分隔线
        tray_menu.addSeparator()
        
        # 添加退出动作
        quit_action = QAction("退出", self.main_window)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(tray_menu)
        
        # 连接托盘图标的双击事件
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # 显示托盘图标
        self.tray_icon.show()
        print("托盘图标初始化完成")  # 添加调试信息
        
    def tray_icon_activated(self, reason):
        """处理托盘图标的激活事件"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_main_window()
            
    def show_main_window(self):
        """显示主窗口"""
        self.main_window.show()
        self.main_window.activateWindow()
        
    def handle_close_event(self, event):
        """处理窗口关闭事件"""
        print("Backstage: 开始处理关闭事件")
        
        if not self.settings.value('hide_minimize_prompt', False, type=bool):
            msg_box = QMessageBox()
            msg_box.setWindowTitle("关闭提示")
            msg_box.setText("是否要退出程序？")
            msg_box.setIcon(QMessageBox.Icon.Question)
            
            checkbox = QCheckBox("不再显示此提示")
            msg_box.setCheckBox(checkbox)
            
            minimize_btn = msg_box.addButton("最小化到托盘", QMessageBox.ButtonRole.AcceptRole)
            quit_btn = msg_box.addButton("退出程序", QMessageBox.ButtonRole.RejectRole)
            
            result = msg_box.exec()
            
            if checkbox.isChecked():
                self.settings.setValue('hide_minimize_prompt', True)
            
            clicked_button = msg_box.clickedButton()
            if clicked_button is None or clicked_button == minimize_btn:  # 用户点击了关闭按钮（X）或最小化
                event.ignore()
                self.minimize_to_tray()
            else:  # 用户选择退出
                # 设置force_quit标志
                self.main_window.force_quit = True
                self.tray_icon.hide()
                # 接受关闭事件，让MainUI处理实际的退出逻辑
                event.accept()
        else:
            event.ignore()
            self.minimize_to_tray()
            
    def minimize_to_tray(self):
        """最小化到托盘"""
        print("Backstage: 执行最小化到托盘")  # 调试信息
        self.main_window.hide()
        self.tray_icon.showMessage(
            "Hoxino Download",
            "程序已最小化到系统托盘",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )
        
    def delayed_quit(self):
        """延时退出，确保事件能够正确处理"""
        print("Backstage: 准备延时退出")
        self.main_window.force_quit = True
        self.tray_icon.hide()
        # 使用短暂延时确保事件能够处理
        QTimer.singleShot(100, self.execute_quit)

    def execute_quit(self):
        """执行实际的退出操作"""
        print("Backstage: 执行实际的退出操作")
        self.main_window.close()

    def quit_application(self):
        """从托盘菜单退出"""
        print("Backstage: 从托盘菜单退出")
        self.delayed_quit()
        
    @staticmethod
    def is_system_tray_available():
        """检查系统托盘是否可用"""
        return QSystemTrayIcon.isSystemTrayAvailable()
