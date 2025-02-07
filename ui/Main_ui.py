from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, 
                            QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
                            QHeaderView, QMessageBox, QMainWindow, QLabel, QSizePolicy, QTabBar, QStylePainter, QStyle, QStyleOptionTab)
from PyQt6.QtCore import Qt, QEvent, QObject, pyqtSignal, QMetaObject, Q_ARG, QTimer, QThread, QVariantAnimation, QUrl
from PyQt6.QtGui import (QLinearGradient, QPalette, QColor, QPainter, QFont,
                      QPen, QCursor)
from ui.setting_ui import SettingUI
from download.v1.url_classification import URLClassification
from ui.tabmanager import TabManager
from ui.list.list import DownloadList
from download.v6.progress.progressbar.ProgressBar import ProgressBar
import os
import json
import time
from ui.Miscellaneous.Backstage import Backstage
from PyQt6.QtWidgets import QApplication
import traceback
from Communications.url_receiver import URLReceiver
import threading
import webbrowser

class MainUI(QMainWindow):
    # 添加一个类级别的信号
    url_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        self.force_quit = False
        self.backstage = Backstage(self)
        self.url_classifier = URLClassification()
        
        # 设置窗口标题
        self.setWindowTitle("Hoxino—Downloader")
        
        # 设置窗口透明度
        self.setWindowOpacity(1) 
        
        # 创建进度条（移到这里）
        self.progress_bar = ProgressBar()
        self.progress_bar.setFixedHeight(50)
        
        # 初始化UI
        self.init_ui()
        self.setup_style()
        self.setup_connections()
        
        # 初始化URL接收器
        self.url_receiver = URLReceiver()
        
        # 直接连接信号到槽函数
        self.url_receiver.url_received.connect(self._handle_url)
        
        # 在新线程中启动URL接收器
        self.receiver_thread = threading.Thread(
            target=self.url_receiver.start,
            daemon=True
        )
        self.receiver_thread.start()

    def init_ui(self):
        """初始化UI"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局（垂直布局）
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)  # 设置适当的边距
        main_layout.setSpacing(10)  # 设置组件之间的间距
        
        # 创建顶部搜索栏布局（水平布局）
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(5)
        
        # 创建输入框
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("请输入...")
        
        # 创建按钮
        self.download_btn = QPushButton("下载")
        self.settings_btn = QPushButton("设置")
        
        # 添加组件到顶部布局
        top_layout.addWidget(self.input_box)
        top_layout.addWidget(self.download_btn)
        top_layout.addWidget(self.settings_btn)
        
        # 创建标签页区域的布局
        tab_area = QWidget()
        tab_layout = QVBoxLayout(tab_area)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # 创建选项卡
        self.tab_widget = QTabWidget()
        
        # 设置自定义的 TabBar
        self.tab_widget.setTabBar(GradientTabBar())
        
        # 设置选项卡
        self.setup_tabs()
        
        # 将选项卡添加到标签页布局
        tab_layout.addWidget(self.tab_widget)
        
        # 创建进度条容器和布局
        progress_container = QWidget()
        progress_layout = QVBoxLayout(progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(0)
        
        # 添加进度条到容器
        progress_layout.addWidget(self.progress_bar)
        self.progress_bar.hide()  # 默认隐藏进度条
        
        # 创建Email标签
        self.email_label = GradientLabel("Author: Hoxino Email Contact: hoxinoaiaky@gmail.com")
        self.email_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.email_label.setFont(QFont("Arial", 10))
        self.email_label.setFixedWidth(400)
        self.email_label.setFixedHeight(30)
        # 添加工具提示
        self.email_label.setToolTip("点击访问 GitHub 仓库")
        
        # 创建底部布局
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.email_label)
        bottom_layout.addStretch()
        
        # 添加所有组件到主布局
        main_layout.addLayout(top_layout)
        main_layout.addWidget(tab_area, 1)  # 设置stretch factor为1，使其填充可用空间
        main_layout.addWidget(progress_container)  # 添加进度条容器
        main_layout.addLayout(bottom_layout)
        
        # 设置中央部件的布局
        central_widget.setLayout(main_layout)
        
        # 设置窗口最小尺寸
        self.setMinimumSize(800, 600)

    def setup_tabs(self):
        """设置标签页"""
        # 创建不同的列表实例
        self.lists = {
            "下载中": self.create_table("下载中"),
            "等待中": self.create_table("等待中"),
            "已完成": self.create_table("已完成"),
            "错误": self.create_table("错误")
        }
        
        # 添加标签页并连接信号
        for name, table in self.lists.items():
            self.tab_widget.addTab(table, name)
            if name == "下载中":
                # 只连接信号，不主动加载数据
                table.row_selected.connect(self.progress_bar.on_task_selected)
        
        # 创建标签页管理器
        self.tab_managers = {}
        for name, table in self.lists.items():
            self.tab_managers[name] = TabManager(table, name)

    def load_downloading_tasks(self, table):
        """加载下载任务数据"""
        try:
            # 读取downloading.json
            downloading_path = os.path.join("data", "queuemanagement", "downloading.json")
            if os.path.exists(downloading_path):
                with open(downloading_path, 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
                
                # 添加任务到列表
                for task in tasks:
                    table.add_task(task)
                    print(f"已加载任务: {task.get('file_name')}")
            else:
                print("downloading.json 文件不存在")
                
        except Exception as e:
            print(f"加载任务失败: {str(e)}")

    def create_table(self, tab_name=None):
        """创建下载列表"""
        table = DownloadList()
        
        # 设置高级样式
        table.setStyleSheet("""
            QTableWidget {
                background: #2b2b2b;
                gridline-color: transparent;
                border: none;
                padding: 5px;
            }
            
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid transparent;
                color: #ecf0f1;
            }
            
            QTableWidget::item:hover {
                background-color: rgba(52, 152, 219, 0.1);
            }
            
            QTableWidget::item:selected {
                background-color: rgba(52, 152, 219, 0.2);
                color: #3498db;
            }
            
            /* 标题栏样式 */
            QHeaderView::section {
                background-color: #2b2b2b;
                color: white;
                padding: 8px;
                border: none;
                border-bottom: 2px solid qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
                font-weight: bold;
                text-align: center;
            }
            
            /* 滚动条样式 */
            QScrollBar:vertical {
                width: 8px;
                background: transparent;
                margin: 0px;
            }
            
            QScrollBar::handle:vertical {
                background: rgba(52, 152, 219, 0.3);
                min-height: 30px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: rgba(46, 204, 113, 0.5);
            }
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: none;
            }
            
            /* 水平滚动条样式 */
            QScrollBar:horizontal {
                height: 8px;
                background: transparent;
                margin: 0px;
            }
            
            QScrollBar::handle:horizontal {
                background: rgba(52, 152, 219, 0.3);
                min-width: 30px;
                border-radius: 4px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background: rgba(46, 204, 113, 0.5);
            }
            
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: none;
            }
        """)
        
        # 设置表格属性
        table.setShowGrid(False)  # 关闭默认网格线
        table.setAlternatingRowColors(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.verticalHeader().setVisible(False)
        
        # 修改这里：改为根据需要显示滚动条
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 根据不同的标签页设置不同的列
        if tab_name == "错误":
            headers = ["URL", "失败原因"]
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)
            
            header = table.horizontalHeader()
            header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
            table.setColumnWidth(0, 200)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            
        elif tab_name == "下载中":
            headers = ["文件名", "大小", "状态", "进度", "时间"]
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)
            
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            column_widths = {1: 100, 2: 80, 3: 100, 4: 150}
            for col, width in column_widths.items():
                table.setColumnWidth(col, width)
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            
        else:  # "等待中"和"已完成"标签页
            headers = ["文件名", "大小", "状态", "时间"]
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)
            
            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            column_widths = {1: 100, 2: 80, 3: 150}
            for col, width in column_widths.items():
                table.setColumnWidth(col, width)
                header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
        
        # 设置表头样式
        header = table.horizontalHeader()
        header.setHighlightSections(False)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        
        return table

    def setup_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            
            /* 输入框样式 */
            QLineEdit {
                background-color: #363636;
                border: 2px solid transparent;
                border-image: none;
                padding: 8px 15px;
                border-radius: 6px;
                color: #ffffff;
                font-size: 14px;
                font-weight: bold;
                min-width: 300px;
                height: 25px;
                selection-background-color: #3498db;
            }
            
            QLineEdit:focus {
                border: 2px solid qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
            }
            
            QLineEdit:hover {
                background-color: #404040;
            }
            
            /* 按钮样式 */
            QPushButton {
                background-color: transparent;
                border: 2px solid qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
                padding: 5px 20px;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                font-size: 13px;
                height: 35px;
                min-width: 80px;
            }
            
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(52, 152, 219, 0.2),
                    stop:0.5 rgba(46, 204, 113, 0.2),
                    stop:1 rgba(52, 152, 219, 0.2)
                );
            }
            
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(52, 152, 219, 0.3),
                    stop:0.5 rgba(46, 204, 113, 0.3),
                    stop:1 rgba(52, 152, 219, 0.3)
                );
            }
            
            /* 选项卡整体容器 */
            QTabWidget::pane {
                border: none;
                background-color: #2b2b2b;
                margin-top: -1px;
            }
            
            /* 选项卡样式 */
            QTabBar::tab {
                background-color: transparent;
                color: #888888;
                padding: 8px 20px;
                margin: 0 2px;
                border: none;
                font-family: "Microsoft YaHei", "Arial";
                font-weight: bold;
                font-size: 14px;
                min-width: 80px;
            }
            
            QTabBar::tab:hover {
                color: #ffffff;
            }
            
            QTabBar::tab:selected {
                color: transparent;
                background: transparent;
                border-bottom: 2px solid qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
            }

            /* 表格和滚动条样式 */
            QTableWidget {
                background: #2b2b2b;
                gridline-color: transparent;
                border: none;
                padding: 5px;
            }
            
            QTableWidget::item {
                padding: 12px 8px;
                border-bottom: 1px solid transparent;
                color: #ecf0f1;
            }

            /* 垂直滚动条 */
            QTableWidget QScrollBar:vertical {
                width: 8px;
                background-color: transparent;
                margin: 0px;
                padding: 0px;
            }

            QTableWidget QScrollBar::handle:vertical {
                background: rgba(52, 152, 219, 0.3);
                min-height: 30px;
                border-radius: 4px;
            }

            QTableWidget QScrollBar::handle:vertical:hover {
                background: rgba(46, 204, 113, 0.5);
            }

            QTableWidget QScrollBar::add-line:vertical,
            QTableWidget QScrollBar::sub-line:vertical {
                height: 0px;
            }

            QTableWidget QScrollBar::add-page:vertical,
            QTableWidget QScrollBar::sub-page:vertical {
                background: none;
            }

            /* 水平滚动条 */
            QTableWidget QScrollBar:horizontal {
                height: 8px;
                background-color: transparent;
                margin: 0px;
                padding: 0px;
            }

            QTableWidget QScrollBar::handle:horizontal {
                background: rgba(52, 152, 219, 0.3);
                min-width: 30px;
                border-radius: 4px;
            }

            QTableWidget QScrollBar::handle:horizontal:hover {
                background: rgba(46, 204, 113, 0.5);
            }

            QTableWidget QScrollBar::add-line:horizontal,
            QTableWidget QScrollBar::sub-line:horizontal {
                width: 0px;
            }

            QTableWidget QScrollBar::add-page:horizontal,
            QTableWidget QScrollBar::sub-page:horizontal {
                background: none;
            }

            /* 滚动条在不滚动时隐藏 */
            QTableWidget QScrollBar:vertical,
            QTableWidget QScrollBar:horizontal {
                background: transparent;
            }

            /* 只在鼠标悬停在表格上时显示滚动条 */
            QTableWidget:hover QScrollBar:vertical,
            QTableWidget:hover QScrollBar:horizontal {
                background: rgba(0, 0, 0, 0.1);
            }
        """)

    def setup_connections(self):
        """设置信号连接"""
        self.settings_btn.clicked.connect(self.open_settings)
        self.download_btn.clicked.connect(self.start_download)

    def open_settings(self):
        self.setting_window = SettingUI()
        self.setting_window.show()

    def start_download(self):
        url = self.input_box.text().strip()
        if url:
            # 启动监控
            from download.Pausemonitoring.Pause_monitoring import pause_monitor
            pause_monitor.start_monitoring()
            
            # 开始下载
            self.url_classifier.classify_url(url)
            self.input_box.clear()  # 清空输入框
        else:
            QMessageBox.warning(self, "警告", "请输入URL")

    def on_row_selected(self, thread_id: int):
        """处理行选择事件"""
        
        self.progress_bar.on_task_selected(thread_id)

    def update_task_list(self):
        """更新任务列表"""
        try:
            # 读取downloading.json
            with open(os.path.join("data", "queuemanagement", "downloading.json"), 'r', encoding='utf-8') as f:
                downloading_tasks = json.load(f)
                
            # 清空现有列表
            self.download_list.setRowCount(0)
            
            # 添加任务到列表
            for task in downloading_tasks:
                self.download_list.add_task(task)
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"更新任务列表失败: {str(e)}")
    
    

    def _force_exit(self):
        """强制退出程序"""
        print("MainUI: 强制退出程序")
        # 在这里添加停止URL接收器的代码
        if hasattr(self, 'url_receiver'):
            self.url_receiver.stop()
        # 关闭所有窗口
        QApplication.closeAllWindows()
        # 退出应用程序
        QApplication.quit()
        # 强制结束进程
        os._exit(0)

    def _handle_url(self, url: str):
        """在主线程中处理URL"""
        print(f"MainUI: 开始处理URL: {url}")
        
        try:
            # 直接在主线程中更新UI
            self.input_box.setText(url)
            
            # 创建独立的确认对话框
            msg_box = QMessageBox()
            msg_box.setWindowTitle("新的下载任务")
            
            # 设置主要文本和详细文本
            msg_box.setText("是否开始下载?")
            msg_box.setInformativeText(
                f"<div style='margin: 10px 0; padding: 10px; "
                f"background: #363636; border-radius: 5px; "
                f"width: 600px; word-wrap: break-word; color: white;'>"
                f"{url}</div>"
            )
            
            # 设置按钮
            yes_btn = msg_box.addButton("开始下载", QMessageBox.ButtonRole.YesRole)
            no_btn = msg_box.addButton("取消", QMessageBox.ButtonRole.NoRole)
            
            # 设置默认按钮
            msg_box.setDefaultButton(yes_btn)
            
            # 设置窗口标志
            msg_box.setWindowFlags(
                Qt.WindowType.WindowStaysOnTopHint |  # 保持在最顶层
                Qt.WindowType.FramelessWindowHint |   # 无边框
                Qt.WindowType.Tool                    # 作为独立工具窗口
            )
            
            # 设置对话框的最小宽度
            msg_box.setMinimumWidth(700)
            
            # 应用自定义样式
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #2b2b2b;
                    border: 2px solid qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #3498db,
                        stop:0.5 #2ecc71,
                        stop:1 #3498db
                    );
                    border-radius: 10px;
                }
                
                QMessageBox QLabel {
                    color: white;
                    font-size: 14px;
                    font-weight: bold;
                    margin: 10px 0;
                    min-width: 600px;
                }
                
                QPushButton {
                    background-color: transparent;
                    border: 2px solid qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 #3498db,
                        stop:0.5 #2ecc71,
                        stop:1 #3498db
                    );
                    border-radius: 5px;
                    color: white;
                    font-weight: bold;
                    min-width: 100px;
                    padding: 8px 20px;
                    margin: 5px;
                }
                
                QPushButton:hover {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(52, 152, 219, 0.2),
                        stop:0.5 rgba(46, 204, 113, 0.2),
                        stop:1 rgba(52, 152, 219, 0.2)
                    );
                }
                
                QPushButton:pressed {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 rgba(52, 152, 219, 0.3),
                        stop:0.5 rgba(46, 204, 113, 0.3),
                        stop:1 rgba(52, 152, 219, 0.3)
                    );
                }
            """)
            
            # 移动到屏幕中心
            screen = QApplication.primaryScreen().geometry()
            msg_box.move(
                screen.center().x() - msg_box.width() // 2,
                screen.center().y() - msg_box.height() // 2
            )
            
            # 显示对话框并获取结果
            print("MainUI: 显示确认对话框")
            msg_box.exec()
            
            # 处理结果
            if msg_box.clickedButton() == yes_btn:
                print("MainUI: 用户确认下载，调用下载方法")
                self.download_btn.click()
                print("MainUI: 下载方法已调用")
            
        except Exception as e:
            print(f"MainUI: 处理URL时出错: {e}")
            import traceback
            print(traceback.format_exc())

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        print("MainUI: 触发关闭事件")
        if not self.force_quit:
            print("MainUI: 转交给后台管理处理")
            self.backstage.handle_close_event(event)
            # 移除停止URL接收器的代码
            return
        
        print("MainUI: 执行强制退出逻辑")
        try:
            # 获取下载中的表格
            downloading_table = self.tab_widget.widget(0)
            print(f"获取到的下载表格类型: {type(downloading_table)}")
            
            if not isinstance(downloading_table, DownloadList):
                print("错误：无法获取下载列表")
                self._force_exit()
                event.accept()
                return

            # 读取 downloading.json 获取所有任务
            downloading_path = os.path.join("data", "queuemanagement", "downloading.json")
            print(f"正在读取文件: {downloading_path}")
            
            with open(downloading_path, 'r', encoding='utf-8') as f:
                downloading_tasks = json.load(f)
                print(f"读取到的任务数: {len(downloading_tasks)}")

            # 筛选出正在下载中的任务
            active_tasks = [
                task for task in downloading_tasks 
                if task.get('status') == '下载中'
            ]
            print(f"正在下载的任务数: {len(active_tasks)}")
            print(f"活动任务详情: {active_tasks}")

            if active_tasks:
                print(f"发现 {len(active_tasks)} 个正在下载的任务")
                reply = QMessageBox.question(
                    self,
                    "确认关闭",
                    "有正在下载的任务，关闭程序将自动暂停这些任务。是否继续？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    print("用户确认暂停下载任务")
                    # 暂停所有正在下载的任务
                    for task in active_tasks:
                        thread_id = task.get('thread_id')
                        url = task.get('url')
                        print(f"处理任务: thread_id={thread_id}, url={url}")
                        
                        # 修改这里的条件判断
                        if isinstance(thread_id, (int, float)) and url:  # 同时处理整数和浮点数类型
                            try:
                                print(f"尝试暂停任务: thread_id={thread_id}, url={url}")
                                thread_id = int(thread_id)  # 确保转换为整数
                                downloading_table._on_pause_download(thread_id, url)
                                time.sleep(0.5)
                                print(f"已调用暂停方法: thread_id={thread_id}")
                            except Exception as e:
                                print(f"暂停任务 {thread_id} 时出错: {str(e)}")
                                print(f"错误堆栈: {traceback.format_exc()}")
                                continue
                        else:
                            print(f"任务数据不完整或类型错误: thread_id={thread_id}({type(thread_id)}), url={url}")
                    
                    print("所有任务暂停处理完成")
                    self._force_exit()
                    event.accept()
                else:
                    print("用户取消退出")
                    event.ignore()
                    self.force_quit = False
            else:
                print("没有正在下载的任务，直接退出")
                self._force_exit()
                event.accept()

        except Exception as e:
            print(f"关闭窗口时出错: {str(e)}")
            print(f"错误堆栈: {traceback.format_exc()}")
            self._force_exit()
            event.accept()

    def _on_tab_changed(self, index):
        """处理标签页切换事件"""
        # 只在"下载中"标签页显示进度条
        if index == 0:  # "下载中"标签页的索引
            self.progress_bar.show()
        else:
            self.progress_bar.hide()

# 添加一个新的渐变标签类
class GradientLabel(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("""
            QLabel {
                background-color: transparent;
                padding: 2px;
            }
        """)
        # 设置鼠标样式为手型
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        # 添加点击事件
        self.setMouseTracking(True)
        
    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            webbrowser.open('https://github.com/HoxinoAi/Hoxino-Downloader')
            
    def enterEvent(self, event):
        """鼠标进入时的效果"""
        self.setStyleSheet("""
            QLabel {
                background-color: rgba(52, 152, 219, 0.1);
                border-radius: 5px;
                padding: 2px;
            }
        """)
        
    def leaveEvent(self, event):
        """鼠标离开时的效果"""
        self.setStyleSheet("""
            QLabel {
                background-color: transparent;
                padding: 2px;
            }
        """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 创建渐变
        gradient = QLinearGradient(0, 0, self.width(), 0)
        gradient.setColorAt(0, QColor("#3498db"))    # 蓝色开始
        gradient.setColorAt(0.5, QColor("#2ecc71"))  # 绿色中间
        gradient.setColorAt(1, QColor("#3498db"))    # 蓝色结束
        
        # 创建渐变画笔
        pen = QPen()
        pen.setBrush(gradient)
        pen.setWidth(1)
        
        # 设置画笔
        painter.setPen(pen)
        
        # 绘制文本，使用 AlignCenter 来实现水平和垂直居中
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text())

class GradientTabBar(QTabBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDrawBase(False)
        
    def paintEvent(self, event):
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        for index in range(self.count()):
            option = QStyleOptionTab()
            self.initStyleOption(option, index)
            
            # 如果是选中的标签，使用渐变色绘制文字
            if self.currentIndex() == index:
                rect = self.tabRect(index)
                gradient = QLinearGradient(rect.left(), 0, rect.right(), 0)
                gradient.setColorAt(0, QColor("#3498db"))
                gradient.setColorAt(0.5, QColor("#2ecc71"))
                gradient.setColorAt(1, QColor("#3498db"))
                
                painter.save()
                painter.setPen(QPen(gradient, 1))
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.tabText(index))
                painter.restore()
            else:
                painter.drawControl(QStyle.ControlElement.CE_TabBarTab, option)