from PyQt6.QtWidgets import QMenu, QMessageBox
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QAction
import pyperclip
import json
import os

class DownloadingMenu(QObject):
    # 定义信号
    pause_download = pyqtSignal(int, str)  # 发送 thread_id 和 url
    delete_task = pyqtSignal(int, str)  # 发送 thread_id 和 url
    resume_download = pyqtSignal(int, str)  # 发送 thread_id 和 url
    
    def __init__(self, parent=None):
        super().__init__(parent)  # 必须调用父类的初始化
        self.menu = QMenu(parent)
        self.pause_action = QAction("暂停下载", self.menu)
        self.delete_action = QAction("删除任务", self.menu)
        self.downloading_path = os.path.join("data", "queuemanagement", "downloading.json")
        
        # 添加动作到菜单
        self.menu.addAction(self.pause_action)
        self.menu.addAction(self.delete_action)
        
        # 初始化时就连接信号
        self.pause_action.triggered.connect(self._on_pause)
        self.delete_action.triggered.connect(self._on_delete)
        
        self.thread_id = None
        self.url = None
        self.file_name = None  # 添加文件名属性
        self.init_menu()
        
    def init_menu(self):
        """初始化菜单项"""
        # 设置菜单样式
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: #ecf0f1;
                border: 1px solid #3498db;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 2px;
                margin: 2px 5px;
            }
            QMenu::item:selected {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
                color: white;
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
            QMenu::icon {
                padding-left: 10px;
            }
        """)
        
        # 创建菜单项
        self.copy_url_action = QAction("复制URL", self.menu)
        self.menu.addSeparator()  # 添加分隔线
        self.menu.addAction(self.copy_url_action)
        
        # 连接信号
        self.copy_url_action.triggered.connect(self._on_copy_url)
        
    def show_menu(self, pos, file_name: str):
        """显示右键菜单"""
        try:
            # 保存文件名到实例变量
            self.file_name = file_name
            
            with open(self.downloading_path, 'r', encoding='utf-8') as f:
                downloading_tasks = json.load(f)
                
            # 查找匹配的任务
            for task in downloading_tasks:
                if task['file_name'] == file_name:
                    self.thread_id = task['thread_id']
                    self.url = task['url']
                    
                    # 根据任务状态设置菜单文本
                    is_paused = task.get('status') == '暂停中'
                    self.pause_action.setText("继续下载" if is_paused else "暂停下载")
                    
                    # 显示菜单
                    self.menu.exec(pos)
                    break
                    
        except Exception as e:
            print(f"获取任务信息失败: {str(e)}")
        
    def _on_pause(self):
        """处理暂停/继续下载"""
        if self.thread_id is not None and self.url is not None:
            try:
                # 检查当前状态
                with open(self.downloading_path, 'r', encoding='utf-8') as f:
                    downloading_tasks = json.load(f)
                    
                for task in downloading_tasks:
                    if task['thread_id'] == self.thread_id and task['url'] == self.url:
                        if task['status'] == '暂停中':
                            # 更新状态为下载中
                            task['status'] = '下载中'
                            with open(self.downloading_path, 'w', encoding='utf-8') as f:
                                json.dump(downloading_tasks, f, ensure_ascii=False, indent=4)
                            
                            # 发送继续下载信号
                            self.resume_download.emit(self.thread_id, self.url)
                        else:
                            # 如果是下载状态，发送暂停下载信号
                            self.pause_download.emit(self.thread_id, self.url)
                        break
                    
            except Exception as e:
                print(f"更新任务状态失败: {str(e)}")
        
    def _on_copy_url(self):
        """复制URL到剪贴板"""
        if self.file_name:
            task_info = self._get_task_info(self.file_name)
            if task_info:
                _, url = task_info
                pyperclip.copy(url)
                QMessageBox.information(
                    self.menu,
                    "复制成功",
                    f"URL已复制到剪贴板:\n{url[:100]}{'...' if len(url) > 100 else ''}",
                    QMessageBox.StandardButton.Ok
                )
            else:
                QMessageBox.warning(
                    self.menu,
                    "复制失败",
                    "未找到对应的URL",
                    QMessageBox.StandardButton.Ok
                )
                
    def _get_task_info(self, file_name: str) -> tuple[int, str] | None:
        """
        从downloading.json中获取任务信息
        Args:
            file_name: 文件名
        Returns:
            tuple: (thread_id, url) 如果找到，否则 None
        """
        try:
            with open(self.downloading_path, 'r', encoding='utf-8') as f:
                downloading_tasks = json.load(f)
                
            # 查找匹配的任务
            for task in downloading_tasks:
                if task['file_name'] == file_name:
                    return task['thread_id'], task['url']
                    
            return None
            
        except Exception as e:
            print(f"获取任务信息失败: {str(e)}")
            return None
        
    def _on_delete(self):
        """处理删除任务"""
        if self.thread_id is not None and self.url is not None:
         # 发送删除任务信号
                    self.delete_task.emit(self.thread_id, self.url)
                    
                    # 清理当前任务信息
                    self.thread_id = None
                    self.url = None
                    self.file_name = None
                    
                    # 不需要调用hide()，菜单会自动关闭
                    self.menu.close()  # 使用close()替代hide()
                    
  

    def update_menu_state(self, is_paused: bool):
        """更新菜单项状态"""
        self.pause_action.setText("继续下载" if is_paused else "暂停下载")
