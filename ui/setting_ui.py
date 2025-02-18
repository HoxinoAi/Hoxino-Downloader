<<<<<<< HEAD
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QComboBox, QCheckBox, QLineEdit, QPushButton,
                            QGridLayout, QFileDialog, QFrame, QMessageBox,
                            QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
import json
import os
from ui.PerformanceEvaluation.performance_evaluator import PerformanceEvaluator
import winreg
import sys
from queuemanagement.queuemanagement import DatabaseManager

class SettingUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedWidth(600)
        self.performance_evaluator = PerformanceEvaluator()
        self.init_ui()
        self.setup_style()
        self.load_settings()

    def init_ui(self):
        self.setMinimumSize(800, 300)  # 设置最小尺寸而不是固定尺寸
        
        layout = QVBoxLayout()

        # 最大任务数量
        task_layout = QHBoxLayout()
        task_label = QLabel("最大任务数量:")
        task_label.setFixedWidth(100)  # 固定标签宽度
        self.task_combo = QComboBox()
        self.task_combo.setFixedWidth(80)  # 固定下拉框宽度
        self.task_combo.addItems([str(i) for i in range(1, 7)])
        
        # 评估结果标签
        self.task_evaluation_label = QLabel()
        self.task_evaluation_label.setWordWrap(True)
        self.task_evaluation_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # 水平方向可扩展
            QSizePolicy.Policy.Preferred   # 垂直方向首选高度
        )
        
        task_layout.addWidget(task_label)
        task_layout.addWidget(self.task_combo)
        task_layout.addWidget(self.task_evaluation_label, 1)  # 添加拉伸因子1
        
        # 线程数量
        thread_layout = QHBoxLayout()
        thread_label = QLabel("线程数量:")
        thread_label.setFixedWidth(100)  # 固定标签宽度
        self.thread_combo = QComboBox()
        self.thread_combo.setFixedWidth(80)  # 固定下拉框宽度
        thread_options = ["动态优化"] + [str(i) for i in range(1, 33)]
        self.thread_combo.addItems(thread_options)
        
        # 评估结果标签
        self.thread_evaluation_label = QLabel()
        self.thread_evaluation_label.setWordWrap(True)
        self.thread_evaluation_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # 水平方向可扩展
            QSizePolicy.Policy.Preferred   # 垂直方向首选高度
        )
        
        thread_layout.addWidget(thread_label)
        thread_layout.addWidget(self.thread_combo)
        thread_layout.addWidget(self.thread_evaluation_label, 1)  # 添加拉伸因子1

        # 添加到主布局
        layout.addLayout(task_layout)
        layout.addLayout(thread_layout)

        # 代理设置
        proxy_layout = QGridLayout()
        proxy_layout.setSpacing(10)
        
        # 代理复选框
        self.proxy_check = QCheckBox("代理配置")
        self.proxy_check.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        
        # 代理输入框 - 移除 setEnabled(False)
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("主机地址 (例如: 127.0.0.1)")
        self.host_input.setMinimumWidth(300)  # 增加宽度
        self.host_input.setText("127.0.0.1")  # 设置默认值
        
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("端口号 (例如: 7890)")
        self.port_input.setMinimumWidth(200)  # 增加宽度
        self.port_input.setText("7890")  # 设置默认值
        
        # 使用新的布局方式
        proxy_container = QWidget()
        proxy_container_layout = QHBoxLayout(proxy_container)
        proxy_container_layout.setContentsMargins(0, 0, 0, 0)
        proxy_container_layout.setSpacing(10)
        
        proxy_container_layout.addWidget(self.proxy_check)
        proxy_container_layout.addWidget(self.host_input)
        proxy_container_layout.addWidget(self.port_input)
        proxy_container_layout.addStretch()
        
        # 将代理容器添加到主布局
        layout.addWidget(proxy_container)

        # 下载地址
        download_layout = QHBoxLayout()
        download_label = QLabel("下载地址:")
        self.download_path_label = QLabel()  # 替换原来的预览框
        self.browse_btn = QPushButton("浏览")
        download_layout.addWidget(download_label)
        download_layout.addWidget(self.download_path_label)
        download_layout.addWidget(self.browse_btn)

        # 保存按钮
        self.save_btn = QPushButton("保存")

        # 添加所有组件到主布局
        layout.addLayout(download_layout)
        layout.addWidget(self.save_btn)

        # 添加一条分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3498db;")
        layout.addWidget(separator)

        # 添加开机自启动选项
        autostart_layout = QHBoxLayout()
        self.autostart_check = QCheckBox("开机自启动")
        self.autostart_check.setFont(QFont("Microsoft YaHei", 10))
        
        # 检查当前是否已设置开机自启
        self.autostart_check.setChecked(self.is_autostart_enabled())
        
        autostart_layout.addWidget(self.autostart_check)
        autostart_layout.addStretch()
        
        layout.addLayout(autostart_layout)

        # 添加清除数据的按钮布局
        buttons_layout = QHBoxLayout()
        
        # 添加清除数据按钮
        clear_btn = QPushButton("清除数据")
        clear_btn.setFixedWidth(100)
        clear_btn.clicked.connect(self.clear_data)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                color: white;
                height: 25px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        buttons_layout.addWidget(clear_btn)
        buttons_layout.addStretch()  # 添加弹性空间，使按钮靠左对齐
        
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        
        # 设置信号连接
        self.setup_connections()

    def setup_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            
            /* 标签样式 */
            QLabel {
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                padding: 5px;
            }
            
            /* 下拉框样式 */
            QComboBox {
                background-color: #363636;
                border: 2px solid transparent;
                border-radius: 6px;
                padding: 5px 10px;
                min-width: 80px;
                color: white;
                font-weight: bold;
            }
            
            QComboBox:hover {
                background-color: #404040;
                border: 2px solid qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            
            /* 输入框样式 */
            QLineEdit {
                background-color: #363636;
                border: 2px solid transparent;
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                font-size: 13px;
                font-weight: bold;
                min-height: 20px;
            }
            
            QLineEdit:disabled {
                background-color: #2b2b2b;
                color: #666666;
                border: 2px solid #404040;
            }
            
            QLineEdit:focus {
                border: 2px solid qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
            }
            
            QLineEdit:hover:!disabled {
                background-color: #404040;
                border: 2px solid rgba(52, 152, 219, 0.5);
            }
            
            /* 复选框样式 */
            QCheckBox {
                spacing: 8px;
                color: white;
                font-weight: bold;
            }
            
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #3498db;
                background: #363636;
            }
            
            QCheckBox::indicator:hover {
                border: 2px solid qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
            }
            
            QCheckBox::indicator:checked {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
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
                padding: 8px 20px;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                font-size: 13px;
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
            
            /* 清除数据按钮特殊样式 */
            QPushButton[accessibleName="clear-btn"] {
                border: 2px solid qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e74c3c,
                    stop:0.5 #c0392b,
                    stop:1 #e74c3c
                );
            }
            
            QPushButton[accessibleName="clear-btn"]:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(231, 76, 60, 0.2),
                    stop:0.5 rgba(192, 57, 43, 0.2),
                    stop:1 rgba(231, 76, 60, 0.2)
                );
            }
            
            /* 评估结果标签样式 */
            QLabel[accessibleName="evaluation-label"] {
                background-color: #363636;
                border-radius: 6px;
                padding: 8px;
                margin: 5px;
                font-size: 12px;
            }
            
            /* 分隔线样式 */
            QFrame[frameShape="4"] {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
                height: 2px;
                border: none;
                margin: 10px 0px;
            }
        """)

        # 更新评估标签的样式
        evaluation_style = """
            QLabel {
                padding: 8px;
                border-radius: 4px;
                background-color: #363636;
                margin-left: 10px;
                margin-right: 10px;  /* 添加右边距 */
            }
        """
        self.task_evaluation_label.setStyleSheet(evaluation_style)
        self.thread_evaluation_label.setStyleSheet(evaluation_style)

        # 更新代理输入框样式
        self.setStyleSheet(self.styleSheet() + """
            /* 代理输入框样式 */
            QLineEdit {
                background-color: #363636;
                border: 2px solid transparent;
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                font-size: 13px;
                font-weight: bold;
                min-height: 20px;
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
                border: 2px solid rgba(52, 152, 219, 0.5);
            }
        """)

    def setup_connections(self):
        self.save_btn.clicked.connect(self.save_settings)
        self.browse_btn.clicked.connect(self.browse_directory)
        self.task_combo.currentTextChanged.connect(self.update_performance_evaluation)
        self.thread_combo.currentTextChanged.connect(self.update_performance_evaluation)
        self.proxy_check.toggled.connect(self.update_proxy_state)
        self.autostart_check.toggled.connect(self.toggle_autostart)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择下载目录",
            os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.download_path_label.setText(directory)

    def update_performance_evaluation(self):
        """更新性能评估结果"""
        try:
            max_tasks = int(self.task_combo.currentText())
            threads_setting = self.thread_combo.currentText()
            
            if threads_setting == "动态优化":
                self.task_evaluation_label.setText(
                    f"CPU核心数: {self.performance_evaluator.cpu_count}\n"
                    f"可用内存: {self.performance_evaluator.memory.available / (1024**3):.2f}GB"
                )
                self.thread_evaluation_label.setText(
                    "使用动态优化模式，将根据系统状态自动调整线程数，"
                    "可以更好地平衡性能和资源使用"
                )
                style = """
                    QLabel {
                        padding: 8px;
                        border-radius: 4px;
                        background-color: #2ecc71;
                        color: white;
                        margin-left: 10px;
                        margin-right: 10px;
                    }
                """
                self.thread_evaluation_label.setStyleSheet(style)
                return
                
            threads_per_task = int(threads_setting)
            result = self.performance_evaluator.evaluate_settings(max_tasks, threads_per_task)
            
            # 设置评估结果的颜色
            if result["warning_level"] == 0:
                color = "#2ecc71"  # 绿色
            elif result["warning_level"] == 1:
                color = "#f1c40f"  # 黄色
            else:
                color = "#e74c3c"  # 红色
                
            # 构建评估信息
            total_threads = max_tasks * threads_per_task
            system_info = result["system_info"]
            
            task_info = (
                f"CPU核心数: {system_info['cpu_cores']} | "
                f"可用内存: {system_info['available_memory_gb']}GB | "
                f"CPU频率: {system_info['cpu_freq']}MHz"
            )
            
            thread_info = (
                f"总线程数: {total_threads} | "
                f"{'✓ 配置合适' if result['is_suitable'] else '⚠ 配置可能影响性能'}"
            )
            
            if result["messages"]:
                thread_info += f" | {result['messages'][0]}"
            
            # 设置评估结果样式和内容
            style = f"""
                QLabel {{
                    padding: 8px;
                    border-radius: 4px;
                    background-color: {color};
                    color: white;
                    margin-left: 10px;
                    margin-right: 10px;
                }}
            """
            
            self.task_evaluation_label.setText(task_info)
            self.task_evaluation_label.setStyleSheet(style)
            
            self.thread_evaluation_label.setText(thread_info)
            self.thread_evaluation_label.setStyleSheet(style)
            
        except ValueError:
            # 处理无效输入
            self.task_evaluation_label.setText("输入无效")
            self.thread_evaluation_label.setText("输入无效")
            style = """
                QLabel {
                    padding: 8px;
                    border-radius: 4px;
                    background-color: #e74c3c;
                    color: white;
                    margin-left: 10px;
                    margin-right: 10px;
                }
            """
            self.task_evaluation_label.setText("输入无效")
            self.thread_evaluation_label.setText("输入无效")
            self.task_evaluation_label.setStyleSheet(style)
            self.thread_evaluation_label.setStyleSheet(style)

    def update_proxy_state(self, checked):
        # 移除输入框的启用/禁用控制
        pass

    def load_settings(self):
        settings_path = os.path.join("setting", "setting.json")
        if os.path.exists(settings_path):
           
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                # 设置最大任务数
                max_tasks = str(settings.get('max_tasks', '1'))
                self.task_combo.setCurrentText(max_tasks)
                
                # 设置线程数
                threads = settings.get('threads', '动态优化')  # 默认使用动态优化
                self.thread_combo.setCurrentText(str(threads))
                
                # 设置下载路径
                self.download_path_label.setText(settings.get('download_path', ''))
                
                # 设置代理
                proxy_enabled = settings.get('proxy', False)
                self.proxy_check.setChecked(proxy_enabled)
                
                # 设置代理地址，如果没有保存的设置就使用默认值
                if 'proxy_address' in settings:
                    host, port = settings['proxy_address'].split(':')
                    self.host_input.setText(host)
                    self.port_input.setText(port)
                else:
                    self.host_input.setText("127.0.0.1")
                    self.port_input.setText("7890")
                
            

    def save_settings(self):
        """保存设置前进行性能评估"""
        try:
            max_tasks = int(self.task_combo.currentText())
            threads_setting = self.thread_combo.currentText()
            
            # 只有当不是"动态优化"时才进行评估
            if threads_setting != "动态优化":
                threads_per_task = int(threads_setting)
                
                # 进行性能评估
                is_suitable = self.performance_evaluator.show_evaluation_dialog(
                    max_tasks, 
                    threads_per_task
                )
                
                # 如果评估结果不适合，询问用户是否继续
                if not is_suitable:
                    reply = QMessageBox.question(
                        self,
                        "确认设置",
                        "当前设置可能会影响系统性能，是否仍要继续？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.No:
                        return
            
            # 继续原有的保存逻辑
            settings = {
                'max_tasks': max_tasks,
                'threads': threads_setting,
                'download_path': self.download_path_label.text(),
                'proxy': self.proxy_check.isChecked()
            }
            
            if self.host_input.text() and self.port_input.text():
                settings['proxy_address'] = f"{self.host_input.text()}:{self.port_input.text()}"

            # 确保目录存在
            os.makedirs(os.path.join("setting"), exist_ok=True)
            
            # 保存设置
            settings_path = os.path.join("setting", "setting.json")
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            # 显示成功消息并关闭窗口
            QMessageBox.information(self, "成功", "设置已保存！")
            self.close()
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存设置时发生错误：{str(e)}")

    def clear_data(self):
        """清除数据函数"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除所有数据吗？此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            import shutil
            import os
            
            try:
                # 清除数据目录，但保留db文件夹
                if os.path.exists("data"):
                    # 获取所有子目录
                    for item in os.listdir("data"):
                        item_path = os.path.join("data", item)
                        # 跳过db目录
                        if item != "db" and os.path.exists(item_path):
                            if os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                            else:
                                os.remove(item_path)
                
                # 清空数据库表
                db_manager = DatabaseManager()
                if not db_manager.clear_all_tables():
                    raise Exception("清空数据库表失败")
                
                # 创建其他必要的目录
                os.makedirs(os.path.join("data", "log", "First_level_process"), exist_ok=True)
                os.makedirs(os.path.join("data", "log", "Second_level_process"), exist_ok=True)
                os.makedirs(os.path.join("data", "temp"), exist_ok=True)
                os.makedirs(os.path.join("data", "pause_record"), exist_ok=True)
                os.makedirs(os.path.join("data", "Pausemonitoring"), exist_ok=True)
                os.makedirs(os.path.join("data", "installtemp"), exist_ok=True)
                
                QMessageBox.information(self, "成功", "数据已成功清除！")
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"清除数据时发生错误：{str(e)}")

    def is_autostart_enabled(self) -> bool:
        """检查是否已启用开机自启"""
        try:
            # 打开注册表项
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            
            try:
                # 尝试获取值
                value, _ = winreg.QueryValueEx(key, "Hoxino-Downloader")
                # 获取当前程序路径
                current_path = os.path.abspath(sys.executable)
                # 检查路径是否匹配
                return value == f'"{current_path}"'
            except WindowsError:
                return False
            finally:
                winreg.CloseKey(key)
        except WindowsError:
            return False
            
    def toggle_autostart(self, checked: bool):
        """切换开机自启动状态"""
        try:
            # 获取程序路径
            exe_path = os.path.abspath(sys.executable)
            
            # 打开注册表项
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_READ
            )
            
            if checked:
                # 添加到开机启动
                winreg.SetValueEx(
                    key,
                    "Hoxino-Downloader",
                    0,
                    winreg.REG_SZ,
                    f'"{exe_path}"'
                )
                QMessageBox.information(
                    self,
                    "设置成功",
                    "已添加到开机启动项！",
                    QMessageBox.StandardButton.Ok
                )
            else:
                # 从开机启动中移除
                try:
                    winreg.DeleteValue(key, "Hoxino-Downloader")
                    QMessageBox.information(
                        self,
                        "设置成功",
                        "已从开机启动项移除！",
                        QMessageBox.StandardButton.Ok
                    )
                except WindowsError:
                    pass
                    
            winreg.CloseKey(key)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "设置失败",
                f"设置开机自启动失败：\n{str(e)}",
                QMessageBox.StandardButton.Ok
            )
            # 恢复复选框状态
            self.autostart_check.setChecked(not checked)
=======
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QComboBox, QCheckBox, QLineEdit, QPushButton,
                            QGridLayout, QFileDialog, QFrame, QMessageBox,
                            QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
import json
import os
from queuemanagement.queuemanagement import QueueManagement
from ui.PerformanceEvaluation.performance_evaluator import PerformanceEvaluator
import winreg
import sys

class SettingUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setFixedWidth(600)
        self.performance_evaluator = PerformanceEvaluator()
        self.init_ui()
        self.setup_style()
        self.load_settings()

    def init_ui(self):
        self.setMinimumSize(800, 300)  # 设置最小尺寸而不是固定尺寸
        
        layout = QVBoxLayout()

        # 最大任务数量
        task_layout = QHBoxLayout()
        task_label = QLabel("最大任务数量:")
        task_label.setFixedWidth(100)  # 固定标签宽度
        self.task_combo = QComboBox()
        self.task_combo.setFixedWidth(80)  # 固定下拉框宽度
        self.task_combo.addItems([str(i) for i in range(1, 7)])
        
        # 评估结果标签
        self.task_evaluation_label = QLabel()
        self.task_evaluation_label.setWordWrap(True)
        self.task_evaluation_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # 水平方向可扩展
            QSizePolicy.Policy.Preferred   # 垂直方向首选高度
        )
        
        task_layout.addWidget(task_label)
        task_layout.addWidget(self.task_combo)
        task_layout.addWidget(self.task_evaluation_label, 1)  # 添加拉伸因子1
        
        # 线程数量
        thread_layout = QHBoxLayout()
        thread_label = QLabel("线程数量:")
        thread_label.setFixedWidth(100)  # 固定标签宽度
        self.thread_combo = QComboBox()
        self.thread_combo.setFixedWidth(80)  # 固定下拉框宽度
        thread_options = ["动态优化"] + [str(i) for i in range(1, 33)]
        self.thread_combo.addItems(thread_options)
        
        # 评估结果标签
        self.thread_evaluation_label = QLabel()
        self.thread_evaluation_label.setWordWrap(True)
        self.thread_evaluation_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,  # 水平方向可扩展
            QSizePolicy.Policy.Preferred   # 垂直方向首选高度
        )
        
        thread_layout.addWidget(thread_label)
        thread_layout.addWidget(self.thread_combo)
        thread_layout.addWidget(self.thread_evaluation_label, 1)  # 添加拉伸因子1

        # 添加到主布局
        layout.addLayout(task_layout)
        layout.addLayout(thread_layout)

        # 代理设置
        proxy_layout = QGridLayout()
        proxy_layout.setSpacing(10)
        
        # 代理复选框
        self.proxy_check = QCheckBox("代理配置")
        self.proxy_check.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        
        # 代理输入框 - 移除 setEnabled(False)
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("主机地址 (例如: 127.0.0.1)")
        self.host_input.setMinimumWidth(300)  # 增加宽度
        self.host_input.setText("127.0.0.1")  # 设置默认值
        
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("端口号 (例如: 7890)")
        self.port_input.setMinimumWidth(200)  # 增加宽度
        self.port_input.setText("7890")  # 设置默认值
        
        # 使用新的布局方式
        proxy_container = QWidget()
        proxy_container_layout = QHBoxLayout(proxy_container)
        proxy_container_layout.setContentsMargins(0, 0, 0, 0)
        proxy_container_layout.setSpacing(10)
        
        proxy_container_layout.addWidget(self.proxy_check)
        proxy_container_layout.addWidget(self.host_input)
        proxy_container_layout.addWidget(self.port_input)
        proxy_container_layout.addStretch()
        
        # 将代理容器添加到主布局
        layout.addWidget(proxy_container)

        # 下载地址
        download_layout = QHBoxLayout()
        download_label = QLabel("下载地址:")
        self.download_path_label = QLabel()  # 替换原来的预览框
        self.browse_btn = QPushButton("浏览")
        download_layout.addWidget(download_label)
        download_layout.addWidget(self.download_path_label)
        download_layout.addWidget(self.browse_btn)

        # 保存按钮
        self.save_btn = QPushButton("保存")

        # 添加所有组件到主布局
        layout.addLayout(download_layout)
        layout.addWidget(self.save_btn)

        # 添加一条分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #3498db;")
        layout.addWidget(separator)

        # 添加开机自启动选项
        autostart_layout = QHBoxLayout()
        self.autostart_check = QCheckBox("开机自启动")
        self.autostart_check.setFont(QFont("Microsoft YaHei", 10))
        
        # 检查当前是否已设置开机自启
        self.autostart_check.setChecked(self.is_autostart_enabled())
        
        autostart_layout.addWidget(self.autostart_check)
        autostart_layout.addStretch()
        
        layout.addLayout(autostart_layout)

        # 添加清除数据的按钮布局
        buttons_layout = QHBoxLayout()
        
        # 添加清除数据按钮
        clear_btn = QPushButton("清除数据")
        clear_btn.setFixedWidth(100)
        clear_btn.clicked.connect(self.clear_data)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                border: none;
                padding: 5px 15px;
                border-radius: 3px;
                color: white;
                height: 25px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        buttons_layout.addWidget(clear_btn)
        buttons_layout.addStretch()  # 添加弹性空间，使按钮靠左对齐
        
        layout.addLayout(buttons_layout)

        self.setLayout(layout)
        
        # 设置信号连接
        self.setup_connections()

    def setup_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            
            /* 标签样式 */
            QLabel {
                color: #ffffff;
                font-size: 13px;
                font-weight: bold;
                padding: 5px;
            }
            
            /* 下拉框样式 */
            QComboBox {
                background-color: #363636;
                border: 2px solid transparent;
                border-radius: 6px;
                padding: 5px 10px;
                min-width: 80px;
                color: white;
                font-weight: bold;
            }
            
            QComboBox:hover {
                background-color: #404040;
                border: 2px solid qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
            }
            
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            
            /* 输入框样式 */
            QLineEdit {
                background-color: #363636;
                border: 2px solid transparent;
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                font-size: 13px;
                font-weight: bold;
                min-height: 20px;
            }
            
            QLineEdit:disabled {
                background-color: #2b2b2b;
                color: #666666;
                border: 2px solid #404040;
            }
            
            QLineEdit:focus {
                border: 2px solid qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
            }
            
            QLineEdit:hover:!disabled {
                background-color: #404040;
                border: 2px solid rgba(52, 152, 219, 0.5);
            }
            
            /* 复选框样式 */
            QCheckBox {
                spacing: 8px;
                color: white;
                font-weight: bold;
            }
            
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border-radius: 4px;
                border: 2px solid #3498db;
                background: #363636;
            }
            
            QCheckBox::indicator:hover {
                border: 2px solid qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
            }
            
            QCheckBox::indicator:checked {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
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
                padding: 8px 20px;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                font-size: 13px;
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
            
            /* 清除数据按钮特殊样式 */
            QPushButton[accessibleName="clear-btn"] {
                border: 2px solid qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e74c3c,
                    stop:0.5 #c0392b,
                    stop:1 #e74c3c
                );
            }
            
            QPushButton[accessibleName="clear-btn"]:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(231, 76, 60, 0.2),
                    stop:0.5 rgba(192, 57, 43, 0.2),
                    stop:1 rgba(231, 76, 60, 0.2)
                );
            }
            
            /* 评估结果标签样式 */
            QLabel[accessibleName="evaluation-label"] {
                background-color: #363636;
                border-radius: 6px;
                padding: 8px;
                margin: 5px;
                font-size: 12px;
            }
            
            /* 分隔线样式 */
            QFrame[frameShape="4"] {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
                height: 2px;
                border: none;
                margin: 10px 0px;
            }
        """)

        # 更新评估标签的样式
        evaluation_style = """
            QLabel {
                padding: 8px;
                border-radius: 4px;
                background-color: #363636;
                margin-left: 10px;
                margin-right: 10px;  /* 添加右边距 */
            }
        """
        self.task_evaluation_label.setStyleSheet(evaluation_style)
        self.thread_evaluation_label.setStyleSheet(evaluation_style)

        # 更新代理输入框样式
        self.setStyleSheet(self.styleSheet() + """
            /* 代理输入框样式 */
            QLineEdit {
                background-color: #363636;
                border: 2px solid transparent;
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                font-size: 13px;
                font-weight: bold;
                min-height: 20px;
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
                border: 2px solid rgba(52, 152, 219, 0.5);
            }
        """)

    def setup_connections(self):
        self.save_btn.clicked.connect(self.save_settings)
        self.browse_btn.clicked.connect(self.browse_directory)
        self.task_combo.currentTextChanged.connect(self.update_performance_evaluation)
        self.thread_combo.currentTextChanged.connect(self.update_performance_evaluation)
        self.proxy_check.toggled.connect(self.update_proxy_state)
        self.autostart_check.toggled.connect(self.toggle_autostart)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            "选择下载目录",
            os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly
        )
        if directory:
            self.download_path_label.setText(directory)

    def update_performance_evaluation(self):
        """更新性能评估结果"""
        try:
            max_tasks = int(self.task_combo.currentText())
            threads_setting = self.thread_combo.currentText()
            
            if threads_setting == "动态优化":
                self.task_evaluation_label.setText(
                    f"CPU核心数: {self.performance_evaluator.cpu_count}\n"
                    f"可用内存: {self.performance_evaluator.memory.available / (1024**3):.2f}GB"
                )
                self.thread_evaluation_label.setText(
                    "使用动态优化模式，将根据系统状态自动调整线程数，"
                    "可以更好地平衡性能和资源使用"
                )
                style = """
                    QLabel {
                        padding: 8px;
                        border-radius: 4px;
                        background-color: #2ecc71;
                        color: white;
                        margin-left: 10px;
                        margin-right: 10px;
                    }
                """
                self.thread_evaluation_label.setStyleSheet(style)
                return
                
            threads_per_task = int(threads_setting)
            result = self.performance_evaluator.evaluate_settings(max_tasks, threads_per_task)
            
            # 设置评估结果的颜色
            if result["warning_level"] == 0:
                color = "#2ecc71"  # 绿色
            elif result["warning_level"] == 1:
                color = "#f1c40f"  # 黄色
            else:
                color = "#e74c3c"  # 红色
                
            # 构建评估信息
            total_threads = max_tasks * threads_per_task
            system_info = result["system_info"]
            
            task_info = (
                f"CPU核心数: {system_info['cpu_cores']} | "
                f"可用内存: {system_info['available_memory_gb']}GB | "
                f"CPU频率: {system_info['cpu_freq']}MHz"
            )
            
            thread_info = (
                f"总线程数: {total_threads} | "
                f"{'✓ 配置合适' if result['is_suitable'] else '⚠ 配置可能影响性能'}"
            )
            
            if result["messages"]:
                thread_info += f" | {result['messages'][0]}"
            
            # 设置评估结果样式和内容
            style = f"""
                QLabel {{
                    padding: 8px;
                    border-radius: 4px;
                    background-color: {color};
                    color: white;
                    margin-left: 10px;
                    margin-right: 10px;
                }}
            """
            
            self.task_evaluation_label.setText(task_info)
            self.task_evaluation_label.setStyleSheet(style)
            
            self.thread_evaluation_label.setText(thread_info)
            self.thread_evaluation_label.setStyleSheet(style)
            
        except ValueError:
            # 处理无效输入
            self.task_evaluation_label.setText("输入无效")
            self.thread_evaluation_label.setText("输入无效")
            style = """
                QLabel {
                    padding: 8px;
                    border-radius: 4px;
                    background-color: #e74c3c;
                    color: white;
                    margin-left: 10px;
                    margin-right: 10px;
                }
            """
            self.task_evaluation_label.setText("输入无效")
            self.thread_evaluation_label.setText("输入无效")
            self.task_evaluation_label.setStyleSheet(style)
            self.thread_evaluation_label.setStyleSheet(style)

    def update_proxy_state(self, checked):
        # 移除输入框的启用/禁用控制
        pass

    def load_settings(self):
        settings_path = os.path.join("setting", "setting.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    
                # 设置最大任务数
                max_tasks = str(settings.get('max_tasks', '1'))
                self.task_combo.setCurrentText(max_tasks)
                
                # 设置线程数
                threads = settings.get('threads', '动态优化')  # 默认使用动态优化
                self.thread_combo.setCurrentText(str(threads))
                
                # 设置下载路径
                self.download_path_label.setText(settings.get('download_path', ''))
                
                # 设置代理
                proxy_enabled = settings.get('proxy', False)
                self.proxy_check.setChecked(proxy_enabled)
                
                # 设置代理地址，如果没有保存的设置就使用默认值
                if 'proxy_address' in settings:
                    host, port = settings['proxy_address'].split(':')
                    self.host_input.setText(host)
                    self.port_input.setText(port)
                else:
                    self.host_input.setText("127.0.0.1")
                    self.port_input.setText("7890")
                
            except Exception as e:
                print(f"加载设置文件失败: {e}")

    def save_settings(self):
        """保存设置前进行性能评估"""
        try:
            max_tasks = int(self.task_combo.currentText())
            threads_setting = self.thread_combo.currentText()
            
            # 只有当不是"动态优化"时才进行评估
            if threads_setting != "动态优化":
                threads_per_task = int(threads_setting)
                
                # 进行性能评估
                is_suitable = self.performance_evaluator.show_evaluation_dialog(
                    max_tasks, 
                    threads_per_task
                )
                
                # 如果评估结果不适合，询问用户是否继续
                if not is_suitable:
                    reply = QMessageBox.question(
                        self,
                        "确认设置",
                        "当前设置可能会影响系统性能，是否仍要继续？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.No:
                        return
            
            # 继续原有的保存逻辑
            settings = {
                'max_tasks': max_tasks,
                'threads': threads_setting,
                'download_path': self.download_path_label.text(),
                'proxy': self.proxy_check.isChecked()
            }
            
            if self.host_input.text() and self.port_input.text():
                settings['proxy_address'] = f"{self.host_input.text()}:{self.port_input.text()}"

            # 确保目录存在
            os.makedirs(os.path.join("setting"), exist_ok=True)
            
            # 保存设置
            settings_path = os.path.join("setting", "setting.json")
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            # 显示成功消息并关闭窗口
            QMessageBox.information(self, "成功", "设置已保存！")
            self.close()
                
        except Exception as e:
            QMessageBox.warning(self, "错误", f"保存设置时发生错误：{str(e)}")

    def clear_data(self):
        """清除数据函数"""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除所有数据吗？此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            import shutil
            import os
            
            try:
                # 清除数据目录
                if os.path.exists("data"):
                    shutil.rmtree("data")
                
                # 重新初始化必要的目录和文件
                queue_manager = QueueManagement()
                queue_manager.initialize_queue_files()
                
                # 创建其他必要的目录
                os.makedirs(os.path.join("data", "log", "First_level_process"), exist_ok=True)
                os.makedirs(os.path.join("data", "log", "Second_level_process"), exist_ok=True)
                os.makedirs(os.path.join("data", "temp"), exist_ok=True)
                os.makedirs(os.path.join("data", "download_state"), exist_ok=True)
                os.makedirs(os.path.join("data", "pause_record"), exist_ok=True)
                os.makedirs(os.path.join("data", "Pausemonitoring"), exist_ok=True)
                os.makedirs(os.path.join("data", "installtemp"), exist_ok=True)
                
                QMessageBox.information(self, "成功", "数据已成功清除！")
                
            except Exception as e:
                QMessageBox.warning(self, "错误", f"清除数据时发生错误：{str(e)}")

    def is_autostart_enabled(self) -> bool:
        """检查是否已启用开机自启"""
        try:
            # 打开注册表项
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_READ
            )
            
            try:
                # 尝试获取值
                value, _ = winreg.QueryValueEx(key, "Hoxino-Downloader")
                # 获取当前程序路径
                current_path = os.path.abspath(sys.executable)
                # 检查路径是否匹配
                return value == f'"{current_path}"'
            except WindowsError:
                return False
            finally:
                winreg.CloseKey(key)
        except WindowsError:
            return False
            
    def toggle_autostart(self, checked: bool):
        """切换开机自启动状态"""
        try:
            # 获取程序路径
            exe_path = os.path.abspath(sys.executable)
            
            # 打开注册表项
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_READ
            )
            
            if checked:
                # 添加到开机启动
                winreg.SetValueEx(
                    key,
                    "Hoxino-Downloader",
                    0,
                    winreg.REG_SZ,
                    f'"{exe_path}"'
                )
                QMessageBox.information(
                    self,
                    "设置成功",
                    "已添加到开机启动项！",
                    QMessageBox.StandardButton.Ok
                )
            else:
                # 从开机启动中移除
                try:
                    winreg.DeleteValue(key, "Hoxino-Downloader")
                    QMessageBox.information(
                        self,
                        "设置成功",
                        "已从开机启动项移除！",
                        QMessageBox.StandardButton.Ok
                    )
                except WindowsError:
                    pass
                    
            winreg.CloseKey(key)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "设置失败",
                f"设置开机自启动失败：\n{str(e)}",
                QMessageBox.StandardButton.Ok
            )
            # 恢复复选框状态
            self.autostart_check.setChecked(not checked)
>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
