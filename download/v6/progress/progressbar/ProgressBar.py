from PyQt6.QtWidgets import QProgressBar, QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSlot, QTimer, QPropertyAnimation, QEasingCurve, QVariantAnimation
from PyQt6.QtGui import QPainter, QColor, QLinearGradient
import os
import json

class ProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_thread_id = None
        self.current_value = 0
        self.target_value = 0
        self.init_ui()
        
        # 创建进度动画
        self.progress_animation = QVariantAnimation()
        self.progress_animation.setDuration(300)  # 300ms的动画时长
        self.progress_animation.valueChanged.connect(self._update_progress_value)
        
        # 创建定时器，每100ms检查一次进度
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.check_progress)
        self.progress_timer.setInterval(100)
        
        # 创建渐变动画
        self.gradient_animation = QTimer()
        self.gradient_animation.timeout.connect(self._update_gradient)
        self.gradient_animation.start(50)  # 每50ms更新一次渐变
        self.gradient_offset = 0.0

    def init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 0, 10, 10)
        
        # 创建进度条信息布局
        info_layout = QHBoxLayout()
        
        # 创建标签
        self.thread_label = QLabel("当前任务：未选择")
        self.percentage_label = QLabel("0%")
        
        # 设置标签样式
        label_style = """
            QLabel {
                color: #3498db;
                font-size: 12px;
                font-weight: bold;
                padding: 2px 5px;
                background: rgba(52, 152, 219, 0.1);
                border-radius: 3px;
            }
        """
        self.thread_label.setStyleSheet(label_style)
        self.percentage_label.setStyleSheet(label_style)
        
        info_layout.addWidget(self.thread_label)
        info_layout.addStretch()
        info_layout.addWidget(self.percentage_label)
        
        # 创建自定义进度条
        self.progress_bar = CustomProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        
        # 添加所有组件到主布局
        main_layout.addLayout(info_layout)
        main_layout.addWidget(self.progress_bar)
        
        self.setLayout(main_layout)
        self.hide()

    def _update_progress_value(self, value):
        """更新进度条值的动画回调"""
        self.current_value = value
        self.progress_bar.setValue(int(value))
        self.percentage_label.setText(f"{value:.1f}%")

    def _update_gradient(self):
        """更新进度条渐变效果"""
        self.gradient_offset = (self.gradient_offset + 0.02) % 1.0
        self.progress_bar.gradient_offset = self.gradient_offset
        self.progress_bar.update()

    def _read_downloading_json(self):
        """读取并解析downloading.json文件"""
        try:
            downloading_path = os.path.join("data", "queuemanagement", "downloading.json")
            with open(downloading_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()  # 读取并去除首尾空白
                # 修复可能的多余括号问题
                if content.endswith(']]'):
                    content = content[:-1]
                tasks = json.loads(content)
                # 确保返回的是列表
                return tasks if isinstance(tasks, list) else [tasks]
        except Exception as e:
       
            return []

    def check_progress(self):
        """定时检查downloading.json中的进度"""
        if self.current_thread_id is None:
            return
            
        try:
            tasks = self._read_downloading_json()
            
            # 查找当前选中的任务
            for task in tasks:
                if task.get('thread_id') == self.current_thread_id:
                    progress = float(task.get('progress', 0))
                    status = task.get('status', '')
                    
                    # 更新进度条
                    if status in ['下载中', '暂停中']:
                        self.progress_bar.setValue(int(progress))
                        self.percentage_label.setText(f"{progress:.1f}%")
                        
                    else:
                        self.hide()
                        self.progress_timer.stop()
                    return
                    
            # 如果找不到任务，停止定时器
            self.hide()
            self.progress_timer.stop()
            
        except Exception as e:
            print(f"检查进度时出错: {str(e)}")
    
    @pyqtSlot(int)
    def on_task_selected(self, thread_id: int):
        """当选择任务时触发"""
        if thread_id == -1:  # 处理取消选择的情况
            self.hide()
            self.progress_timer.stop()
            self.current_thread_id = None
            return
            
        self.progress_timer.stop()
        try:
            self.current_thread_id = thread_id
            tasks = self._read_downloading_json()
            
            for task in tasks:
                if task.get('thread_id') == thread_id:
                    self.thread_label.setText(f"当前任务：{task.get('file_name', '未知')}")
                    progress = float(task.get('progress', 0))
                    
                    # 设置动画
                    self.progress_animation.stop()
                    self.progress_animation.setStartValue(self.current_value)
                    self.progress_animation.setEndValue(progress)
                    self.progress_animation.start()
                    
                    if task.get('status') in ['下载中', '暂停中']:
                        self.show()
                        self.progress_timer.start()
                    else:
                        self.hide()
                    return
                    
            self.hide()
            
        except Exception as e:
            print(f"选择任务时出错: {str(e)}")
            self.hide()

class CustomProgressBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.gradient_offset = 0.0
        self.setTextVisible(False)
        self.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3498db;
                border-radius: 5px;
                background-color: #2b2b2b;
                height: 20px;
            }
        """)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 绘制背景
        painter.fillRect(self.rect(), QColor("#2b2b2b"))
        
        # 计算进度条宽度
        progress = self.value() / (self.maximum() - self.minimum())
        width = int(self.width() * progress)
        
        if width > 0:
            # 创建动态渐变
            gradient = QLinearGradient(0, 0, self.width(), 0)
            gradient.setColorAt((0 + self.gradient_offset) % 1, QColor(52, 152, 219))  # 蓝色
            gradient.setColorAt((0.5 + self.gradient_offset) % 1, QColor(46, 204, 113))  # 绿色
            gradient.setColorAt((1 + self.gradient_offset) % 1, QColor(52, 152, 219))  # 蓝色
            
            # 绘制进度条
            progress_rect = self.rect()
            progress_rect.setWidth(width)
            painter.fillRect(progress_rect, gradient)
            
            # 添加光泽效果
            highlight = QLinearGradient(0, 0, 0, self.height())
            highlight.setColorAt(0, QColor(255, 255, 255, 30))
            highlight.setColorAt(1, QColor(255, 255, 255, 0))
            painter.fillRect(progress_rect, highlight)
