<<<<<<< HEAD
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from ui.menu.menu import DownloadingMenu
from ui.menu.menu1 import CompletedMenu
import json
import os
import time
import shutil
import msvcrt  # Windows 文件锁
import threading
from PyQt6.QtGui import QPainter
from queuemanagement.queuemanagement import DatabaseManager

class DownloadList(QTableWidget):
    row_selected = pyqtSignal(int)  # 当选中行时发出，携带一级线程ID
    
    def __init__(self, parent=None, tab_name=None):
        """初始化下载列表
        Args:
            parent: 父窗口
            tab_name: 标签页名称（'下载中'/'等待中'/'已完成'/'错误'）
        """
        super().__init__(parent)
        
        # 保留基本属性
        self.selected_row = None
        self.context_menu = DownloadingMenu(self)
        self.completed_menu = CompletedMenu(self)
        self._last_update_time = {}
        self.update_lock = threading.Lock()
        self._is_processing = False
        self.tab_name = tab_name
        self.db_manager = DatabaseManager()
        
        # 保留信号连接
        self.itemSelectionChanged.connect(self._handle_selection_changed)
        self.context_menu.pause_download.connect(self._on_pause_download)
        self.context_menu.delete_task.connect(self._on_delete_task)
        self.completed_menu.delete_local_file.connect(self._on_delete_completed_file)
        
        # 移除所有样式设置和列定义，这些将由 Main_ui.py 处理

    def _handle_selection_changed(self):
        """处理选择变化，从数据库获取最新的thread_id和url"""
        if self._is_processing:  # 避免重复处理
            return
            
        try:
            self._is_processing = True
            selected_items = self.selectedItems()
            
            if not selected_items:
                # 没有选中项，发送-1表示取消选择
                QTimer.singleShot(0, lambda: self.row_selected.emit(-1))
                return
            
            # 获取选中行的文件名
            current_row = selected_items[0].row()
            file_name_item = self.item(current_row, 0)
            if not file_name_item:
                return
            
            file_name = file_name_item.text()
            # 添加日志
            self.log_message(f"选中行: {current_row}")
            self.log_message(f"获取到文件名: {file_name}")
            self.log_message(f"该行所有列的内容: {[self.item(current_row, i).text() for i in range(self.columnCount())]}")
            
            # 获取存储的额外数据
            thread_id = file_name_item.data(Qt.ItemDataRole.UserRole)
            url = file_name_item.data(Qt.ItemDataRole.UserRole + 1)
            self.log_message(f"存储的额外数据 - thread_id: {thread_id}, url: {url}")
            
            # 使用QTimer延迟执行数据库查询和信号发送
            def delayed_process():
                try:
                    # 从数据库获取最新的thread_id
                    task_info = self.db_manager.get_task_by_filename(file_name)
                    
                    if task_info:
                        thread_id = task_info.get('thread_id')
                        if thread_id is not None:
                            self.log_message(f"选中任务: file_name={file_name}, thread_id={thread_id}")
                            self.row_selected.emit(thread_id)
                            return
                    
                    # 如果没找到匹配的任务
                    self.log_message(f"未找到任务信息: file_name={file_name}")
                    self.row_selected.emit(-1)
                    
                except Exception as e:
                    self.log_message(f"获取任务信息失败: {str(e)}")
                    self.row_selected.emit(-1)
            
            # 使用QTimer延迟执行
            QTimer.singleShot(0, delayed_process)
            
        except Exception as e:
            self.log_message(f"选择处理失败: {str(e)}")
            QTimer.singleShot(0, lambda: self.row_selected.emit(-1))
        
        finally:
            self._is_processing = False

    def contextMenuEvent(self, event):
        """处理右键点击事件"""
        item = self.itemAt(event.pos())
        if item is not None:
            row = item.row()
            file_name = self.item(row, 0).text()
            status_item = self.item(row, 2)
            
            if status_item:
                status = status_item.text()
                
                if status in ["下载中", "暂停中"]:
                    # 显示下载中的右键菜单
              
                    self.context_menu.show_menu(event.globalPos(), file_name)
                    
                elif status == "已完成":
                    # 从数据库中获取文件路径
                
                    file_path = self.db_manager.get_downloaded_file_path(file_name)
                    
                    if file_path:
                        self.completed_menu.show_menu(event.globalPos(), file_path)
                    else:
                        QMessageBox.warning(
                            self,
                            "警告",
                            "无法找到文件或文件已被移动/删除",
                            QMessageBox.StandardButton.Ok
                        )

    def update_task_status(self, thread_id: int, status: str, progress: float = None):
        """更新任务状态，添加节流和线程安全保护"""
        
        with self.update_lock:  # 使用线程锁
                # 检查更新频率
                current_time = time.time()
                if thread_id in self._last_update_time:
                    if current_time - self._last_update_time[thread_id] < 0.1:  # 100ms 节流
                        return
                
                self._last_update_time[thread_id] = current_time
                
                # 查找对应行
                target_row = -1
                for row in range(self.rowCount()):
                    if self.item(row, 0).data(Qt.ItemDataRole.UserRole) == thread_id:
                        target_row = row
                        break
                
                if target_row >= 0:
                    # 更新状态
                    status_item = self.item(target_row, 2)
                    if status_item:
                        status_item.setText(status)
                    
                    # 更新进度
                    if progress is not None:
                        progress_item = self.item(target_row, 3)
                        if progress_item:
                            progress_item.setText(f"{progress:.2f}%")
                    
                    # 强制更新显示
                    self.viewport().update()
                


    def add_task(self, task_data: dict):
        """添加任务到列表"""
        try:
            row_position = self.rowCount()
            self.insertRow(row_position)
            
            # 获取任务数据，设置默认值
            file_name = task_data.get('file_name', '未知文件')
            size = task_data.get('size', '0 B')
            status = task_data.get('status', '等待中')
            progress = task_data.get('progress', 0)
            time_str = task_data.get('time', time.strftime("%Y-%m-%d %H:%M:%S"))
            thread_id = task_data.get('thread_id')
            url = task_data.get('url', '')

            # 创建并设置各列的项目
            items = [
                (file_name, thread_id, url),  # 第一列：文件名，存储thread_id和url
                (size, None, None),           # 第二列：大小
                (status, None, None),         # 第三列：状态
                (f"{progress:.1f}%", None, None),  # 第四列：进度
                (time_str, None, None)        # 第五列：时间
            ]

            for col, (text, user_role, user_role_plus) in enumerate(items):
                item = QTableWidgetItem(str(text))
                if user_role is not None:
                    item.setData(Qt.ItemDataRole.UserRole, user_role)
                if user_role_plus is not None:
                    item.setData(Qt.ItemDataRole.UserRole + 1, user_role_plus)
                self.setItem(row_position, col, item)

            
        except Exception as e:

            import traceback

    def update_task(self, thread_id: int, status: str = None, progress: float = None):
        """更新任务状态和进度"""
        
        # 查找对应的行
        for row in range(self.rowCount()):
            if self.item(row, 0).data(Qt.ItemDataRole.UserRole) == thread_id:
                if status:
                    self.item(row, 2).setText(status)
                if progress is not None:
                    self.item(row, 3).setText(f"{progress:.1f}%")
                   
                break

    def _close_primary_thread(self, thread_id: int):
        """关闭一级线程"""
        try:
            # 创建关闭信号文件
            signal_dir = os.path.join("data", "thread_signal")
            os.makedirs(signal_dir, exist_ok=True)
            signal_file = os.path.join(signal_dir, f"{thread_id}_close.signal")
            
            # 写入关闭信号
            with open(signal_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'thread_id': thread_id,
                    'action': 'close',
                    'timestamp': time.time()
                }, f, ensure_ascii=False, indent=4)
                
            # 更新UI状态
            self.update_task(thread_id, status="已关闭")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"关闭线程失败: {str(e)}",
                QMessageBox.StandardButton.Ok
            )

    def _on_pause_download(self, file_name: str):
        """处理暂停下载信号"""
        try:
            
            # 更新任务状态为暂停中
            if self.db_manager.update_task_status(file_name, "暂停中"):
                
                # 获取任务信息
                task_info = self.db_manager.get_task_by_filename(file_name)
                if task_info:
                    thread_id = task_info.get('thread_id')
                    
                    # 暂停所有相关的下载线程
                    # 调用类方法暂停所有相关线程
                    
                    # 隐藏右键菜单
                    self.context_menu.menu.hide()
                
                
        except Exception as e:
            import traceback

    def _on_delete_task(self, file_name: str, thread_id: int):
        """处理删除任务信号，强制删除所有相关资源"""
        try:
            
            # 确认删除
            reply = QMessageBox.question(
                self,
                "确认删除",
                "确定要删除此任务吗？这将强制停止所有相关进程并删除所有文件。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.log_message(f"开始强制删除任务: {file_name}, thread_id: {thread_id}")
                
                # 1. 先关闭一级线程
                try:
                    self._close_primary_thread(thread_id)
                    time.sleep(0.1)
                except Exception as e:
                    self.log_message(f"关闭一级线程失败: {str(e)}")

                # 2. 强制删除数据库记录
                try:
                    if self.tab_name == "下载中":
                        result = self.db_manager.remove_downloading_by_filename(file_name)
                        chunks_result = self.db_manager.delete_chunks_by_filename(file_name)
                        
                    elif self.tab_name == "等待中":
                        
                        result = self.db_manager.remove_task_by_type("waiting", file_name)
                    self.log_message(f"删除数据库记录: {file_name}")
                except Exception as e:
                    self.log_message(f"删除数据库记录时出错: {str(e)}")

                # 3. 删除临时文件和目录
                try:
                    # 删除 installtemp 目录
                    install_temp_dir = os.path.join("data", "installtemp", file_name)
                    if os.path.exists(install_temp_dir):
                        shutil.rmtree(install_temp_dir, ignore_errors=True)
                        self.log_message(f"删除临时目录: {install_temp_dir}")

                    # 删除 task 目录
                    temp_dir = os.path.join("data", "temp", f"task_{thread_id}")
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        self.log_message(f"删除任务临时目录: {temp_dir}")
                        
                except Exception as e:
                    self.log_message(f"删除文件时出错: {str(e)}")

                # 4. 从UI中删除对应行
                for row in range(self.rowCount()):
                    if self.item(row, 0).text() == file_name:
                        self.removeRow(row)
                        self.log_message(f"从UI删除任务行: {file_name}")
                        break

                self.log_message(f"成功完成删除任务: {file_name}")
                
        except Exception as e:
            error_msg = f"删除任务失败: {str(e)}"
            self.log_message(error_msg)
            QMessageBox.critical(
                self,
                "错误",
                error_msg,
                QMessageBox.StandardButton.Ok
            )

    def log_message(self, message: str):
        """写入日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_dir = os.path.join("data", "log", "ui")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "download_list.log")
        
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

   

    def _on_delete_completed_file(self, file_path: str):
        """处理删除已完成文件的信号"""
        try:
            file_name = os.path.basename(file_path)
            db_manager = DatabaseManager()
            
            # 从UI中删除对应行
            for row in range(self.rowCount()):
                if self.item(row, 0).text() == file_name:
                    self.removeRow(row)
                    break
            
            # 从downloaded表中删除记录
            if db_manager.remove_downloaded_task(file_name):
                self.log_message(f"已从数据库移除已完成任务: {file_name}")
            else:
                self.log_message(f"从数据库移除已完成任务失败: {file_name}")
                
        except Exception as e:
            self.log_message(f"删除已完成文件失败: {str(e)}")

    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            item = self.itemAt(event.pos())
            if item is None:  # 点击空白处
                self.clearSelection()  # 清除选择
                # 发送取消选择信号
                self.row_selected.emit(-1)
            else:
                # 获取选中行的文件名和thread_id
                current_row = item.row()
                file_name_item = self.item(current_row, 0)
                if file_name_item:
                    file_name = file_name_item.text()
                    # 从数据库获取最新的thread_id
                    task_info = self.db_manager.get_task_by_filename(file_name)
                    if task_info and task_info.get('thread_id') is not None:
                        thread_id = task_info.get('thread_id')
                        # 发送选中信号
                        self.row_selected.emit(thread_id)
                        # 使用动画效果处理选择
                        super(DownloadList, self).mousePressEvent(event)
                    else:
                        # 如果没找到匹配的任务，发送取消选择信号
                        self.row_selected.emit(-1)
        else:
            super().mousePressEvent(event)
=======
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from ui.menu.menu import DownloadingMenu
from ui.menu.menu1 import CompletedMenu
import json
import os
import time
import shutil
import msvcrt  # Windows 文件锁
import threading
from PyQt6.QtGui import QPainter

class DownloadList(QTableWidget):
    row_selected = pyqtSignal(int)  # 当选中行时发出，携带一级线程ID
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.selected_row = None
        self.context_menu = DownloadingMenu(self)
        self.completed_menu = CompletedMenu(self)
        self.downloading_path = os.path.join("data", "queuemanagement", "downloading.json")
        self._last_update_time = {}
        self.update_lock = threading.Lock()
        self._is_processing = False  # 添加处理标志
        
        # 只保留一个信号连接
        self.itemSelectionChanged.connect(self._handle_selection_changed)
        self.context_menu.pause_download.connect(self._on_pause_download)
        self.context_menu.resume_download.connect(self._on_resume_download)
        self.context_menu.delete_task.connect(self._on_delete_task)
        self.completed_menu.delete_local_file.connect(self._on_delete_completed_file)
        
    def init_ui(self):
        """初始化UI"""
        # 设置选择模式为单行选择
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        
        # 禁止编辑
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # 设置表格样式
        self.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                gridline-color: #3498db;
                color: white;
                border: none;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
            }
            QHeaderView::section {
                background-color: #363636;
                padding: 5px;
                border: 1px solid #3498db;
                color: white;
            }
        """)
        
    def _handle_selection_changed(self):
        """处理选择变化，从downloading.json获取最新的thread_id和url"""
        if self._is_processing:  # 避免重复处理
            return
        
        try:
            self._is_processing = True
            selected_items = self.selectedItems()
            
            if not selected_items:
                # 没有选中项，发送-1表示取消选择
                self.row_selected.emit(-1)
                return
            
            # 获取选中行的文件名
            current_row = selected_items[0].row()
            file_name_item = self.item(current_row, 0)
            if not file_name_item:
                return
            
            file_name = file_name_item.text()
            
            # 从downloading.json获取最新的thread_id
            try:
                with open(self.downloading_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content.endswith(']]'):  # 修复可能的JSON格式问题
                        content = content[:-1]
                    tasks = json.loads(content)
                    
                    if not isinstance(tasks, list):
                        tasks = [tasks]
                    
                    # 查找匹配的任务
                    for task in tasks:
                        if task.get('file_name') == file_name:
                            thread_id = task.get('thread_id')
                            if thread_id is not None:
                                self.log_message(f"选中任务: file_name={file_name}, thread_id={thread_id}")
                                self.row_selected.emit(thread_id)
                                return
                            
                    # 如果没找到匹配的任务
                    self.log_message(f"未找到任务信息: file_name={file_name}")
                    self.row_selected.emit(-1)
                    
            except Exception as e:
                self.log_message(f"获取任务信息失败: {str(e)}")
                self.row_selected.emit(-1)
            
        finally:
            self._is_processing = False

    def contextMenuEvent(self, event):
        """处理右键点击事件"""
        print("开始处理右键菜单事件")  # 添加日志
        item = self.itemAt(event.pos())
        if item is not None:
            row = item.row()
            file_name = self.item(row, 0).text()
            status_item = self.item(row, 2)
            print(f"右键点击: 行={row}, 文件名={file_name}")  # 添加日志
            
            if status_item:
                status = status_item.text()
                print(f"任务状态: {status}")  # 添加日志
                if status in ["下载中", "暂停中"]:
                    # 显示下载中的右键菜单
                    print("显示下载中菜单")  # 添加日志
                    self.context_menu.show_menu(event.globalPos(), file_name)
                elif status == "已完成":
                    # 从downloaded.json中获取文件路径
                    print("尝试获取已完成文件路径")  # 添加日志
                    file_path = self._get_downloaded_file_path(file_name)
                    if file_path:
                        print(f"找到文件路径: {file_path}")  # 添加日志
                        self.completed_menu.show_menu(event.globalPos(), file_path)
                    else:
                        print("未找到文件路径")  # 添加日志
                        QMessageBox.warning(
                            self,
                            "警告",
                            "无法找到文件或文件已被移动/删除",
                            QMessageBox.StandardButton.Ok
                        )

    def _get_downloaded_file_path(self, file_name: str) -> str | None:
        """从downloaded.json获取文件保存路径"""
        try:
            downloaded_path = os.path.join("data", "queuemanagement", "downloaded.json")
            if not os.path.exists(downloaded_path):
                return None
            
            with open(downloaded_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # 清理可能的多余数据
                if content.endswith(']]]'):
                    content = content[:-1]
                if content.endswith(']]'):
                    content = content[:-1]
                downloaded_list = json.loads(content)
            
            if not isinstance(downloaded_list, list):
                downloaded_list = [downloaded_list]
            
            # 查找匹配的文件
            for item in downloaded_list:
                if item.get('file_name') == file_name:
                    file_path = item.get('save_path')
                    if file_path and os.path.exists(file_path):
                        return file_path
            return None
        
        except Exception as e:
            print(f"获取已下载文件路径失败: {str(e)}")
            return None

    def _get_task_info(self, file_name: str) -> tuple[int, str] | None:
        """根据文件名从downloading.json获取最新的thread_id和url"""
        try:
            with open(self.downloading_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content.endswith(']]'):
                    content = content[:-1]
                tasks = json.loads(content)
                
                if not isinstance(tasks, list):
                    tasks = [tasks]
                
                # 查找匹配的任务
                for task in tasks:
                    if task.get('file_name') == file_name:
                        thread_id = task.get('thread_id')
                        url = task.get('url')
                        if thread_id is not None and url:
                            self.log_message(f"获取任务信息: file_name={file_name}, thread_id={thread_id}, url={url}")
                            return thread_id, url
                            
                self.log_message(f"未找到任务信息: file_name={file_name}")
                return None
                
        except Exception as e:
            self.log_message(f"获取任务信息失败: {str(e)}")
            return None

    def update_task_status(self, thread_id: int, status: str, progress: float = None):
        """更新任务状态，添加节流和线程安全保护"""
        try:
            with self.update_lock:  # 使用线程锁
                # 检查更新频率
                current_time = time.time()
                if thread_id in self._last_update_time:
                    if current_time - self._last_update_time[thread_id] < 0.1:  # 100ms 节流
                        return
                
                self._last_update_time[thread_id] = current_time
                
                # 查找对应行
                target_row = -1
                for row in range(self.rowCount()):
                    if self.item(row, 0).data(Qt.ItemDataRole.UserRole) == thread_id:
                        target_row = row
                        break
                
                if target_row >= 0:
                    # 更新状态
                    status_item = self.item(target_row, 2)
                    if status_item:
                        status_item.setText(status)
                    
                    # 更新进度
                    if progress is not None:
                        progress_item = self.item(target_row, 3)
                        if progress_item:
                            progress_item.setText(f"{progress:.2f}%")
                    
                    # 强制更新显示
                    self.viewport().update()
                
        except Exception as e:
            print(f"更新任务状态失败: {str(e)}")

    def add_task(self, task_data: dict):
        """添加任务到列表"""
        try:
            row_position = self.rowCount()
            self.insertRow(row_position)
            
            # 获取任务数据，设置默认值
            file_name = task_data.get('file_name', '未知文件')
            size = task_data.get('size', '0 B')
            status = task_data.get('status', '等待中')
            progress = task_data.get('progress', 0)
            time_str = task_data.get('time', time.strftime("%Y-%m-%d %H:%M:%S"))
            thread_id = task_data.get('thread_id')
            url = task_data.get('url', '')

            # 创建并设置各列的项目
            items = [
                (file_name, thread_id, url),  # 第一列：文件名，存储thread_id和url
                (size, None, None),           # 第二列：大小
                (status, None, None),         # 第三列：状态
                (f"{progress:.1f}%", None, None),  # 第四列：进度
                (time_str, None, None)        # 第五列：时间
            ]

            for col, (text, user_role, user_role_plus) in enumerate(items):
                item = QTableWidgetItem(str(text))
                if user_role is not None:
                    item.setData(Qt.ItemDataRole.UserRole, user_role)
                if user_role_plus is not None:
                    item.setData(Qt.ItemDataRole.UserRole + 1, user_role_plus)
                self.setItem(row_position, col, item)

            print(f"已添加任务: {file_name}, thread_id: {thread_id}, 状态: {status}")
            
        except Exception as e:
            print(f"添加任务失败: {str(e)}")
            import traceback
            print(traceback.format_exc())

    def update_task(self, thread_id: int, status: str = None, progress: float = None):
        """更新任务状态和进度"""
        print(f"DownloadList - 更新任务: thread_id={thread_id}, status={status}, progress={progress}")
        
        # 查找对应的行
        for row in range(self.rowCount()):
            if self.item(row, 0).data(Qt.ItemDataRole.UserRole) == thread_id:
                if status:
                    self.item(row, 2).setText(status)
                if progress is not None:
                    self.item(row, 3).setText(f"{progress:.1f}%")
                   
                break

    def _close_primary_thread(self, thread_id: int):
        """关闭一级线程"""
        try:
            # 创建关闭信号文件
            signal_dir = os.path.join("data", "thread_signal")
            os.makedirs(signal_dir, exist_ok=True)
            signal_file = os.path.join(signal_dir, f"{thread_id}_close.signal")
            
            # 写入关闭信号
            with open(signal_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'thread_id': thread_id,
                    'action': 'close',
                    'timestamp': time.time()
                }, f, ensure_ascii=False, indent=4)
                
            # 更新UI状态
            self.update_task(thread_id, status="已关闭")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"关闭线程失败: {str(e)}",
                QMessageBox.StandardButton.Ok
            )

    def _on_pause_download(self, thread_id: int, url: str):
        """处理暂停下载信号"""
        # 添加弹窗确认方法正在运行
      
        
        try:
            # 读取 downloading.json
            with open(self.downloading_path, 'r', encoding='utf-8') as f:
                downloading_tasks = json.load(f)
                
            # 读取 Pausemonitoring.json
            pause_monitoring_path = os.path.join("data", "Pausemonitoring", "Pausemonitoring.json")
            with open(pause_monitoring_path, 'r', encoding='utf-8') as f:
                pause_data = json.load(f)
                
            # 检查是否已进入下载阶段
            is_downloading = False
            if str(thread_id) in pause_data:
                stages = pause_data[str(thread_id)].get('stages', [])
                for stage in stages:
                    if '二级线程' in stage and '开始下载' in stage:
                        is_downloading = True
                        break
                
            # 查找匹配的任务并更新状态和进度标记
            for task in downloading_tasks:
                if task['thread_id'] == thread_id and task['url'] == url:
                    task['status'] = '暂停中'
                    # 直接添加 has_progress 字段，因为能暂停说明已经开始下载
                    task['has_progress'] = True
                    
            # 写回 downloading.json
            with open(self.downloading_path, 'w', encoding='utf-8') as f:
                json.dump(downloading_tasks, f, ensure_ascii=False, indent=4)
            
            # 创建暂停记录目录和文件
            pause_record_dir = os.path.join("data", "pause_record")
            os.makedirs(pause_record_dir, exist_ok=True)
            pause_record_path = os.path.join(pause_record_dir, "pause_status.json")
            
            # 读取现有暂停记录
            try:
                with open(pause_record_path, 'r', encoding='utf-8') as f:
                    pause_records = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                pause_records = {}
            
            # 更新暂停记录
            pause_records[str(thread_id)] = {
                'url': url,
                'is_downloading': is_downloading,
                'timestamp': time.time()
            }
            
            # 保存暂停记录
            with open(pause_record_path, 'w', encoding='utf-8') as f:
                json.dump(pause_records, f, ensure_ascii=False, indent=4)
            
            # 根据下载状态执行不同操作
            if is_downloading:
                # 已经在下载阶段，保存进度信息
                progress_dir = os.path.join("data", "download_state", str(thread_id))
                os.makedirs(progress_dir, exist_ok=True)
                
                # 保存暂停时的基本信息
                pause_info = {
                    'thread_id': thread_id,
                    'url': url,
                    'pause_time': time.time(),
                    'status': 'paused_downloading'
                }
                
                with open(os.path.join(progress_dir, "pause_info.json"), 'w', encoding='utf-8') as f:
                    json.dump(pause_info, f, ensure_ascii=False, indent=4)
                    
                self.log_message(f"任务 {thread_id} 处于下载阶段，已保存进度信息")
            else:
                # 未进入下载阶段，直接关闭一级线程
                self._close_primary_thread(thread_id)
                self.log_message(f"任务 {thread_id} 未开始下载，已关闭一级线程")
                
            # 更新UI状态
            self.update_task(thread_id, status="暂停中")
            self.context_menu.menu.hide()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"暂停下载失败: {str(e)}",
                QMessageBox.StandardButton.Ok
            )
        
    def _on_delete_task(self, thread_id: int, url: str):
        """处理删除任务信号"""
        lock_file = None
        try:
            # 创建锁文件目录
            lock_dir = os.path.join("data", "locks")
            os.makedirs(lock_dir, exist_ok=True)
            lock_path = os.path.join(lock_dir, f"delete_task_{thread_id}.lock")
            
            # 获取独占锁
            try:
                lock_file = open(lock_path, 'w')
                # Windows 文件锁定
                msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            except Exception as e:
                self.log_message(f"无法获取文件锁: {str(e)}")
                return
            
            reply = QMessageBox.question(
                self,
                "确认删除",
                "确定要删除此任务吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # 1. 首先关闭相关线程
                self._close_primary_thread(thread_id)
                time.sleep(0.5)
                
                # 2. 删除 downloading.json 中的任务数据
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        with open(self.downloading_path, 'r', encoding='utf-8') as f:
                            downloading_tasks = json.load(f)
                        
                        downloading_tasks = [
                            task for task in downloading_tasks 
                            if not (task['thread_id'] == thread_id and task['url'] == url)
                        ]
                        
                        with open(self.downloading_path, 'w', encoding='utf-8') as f:
                            json.dump(downloading_tasks, f, ensure_ascii=False, indent=4)
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise
                        time.sleep(0.5)
                
                # 3. 删除相关目录和文件
                directories_to_delete = [
                    os.path.join("data", "temp", str(thread_id)),
                    os.path.join("data", "download_state", str(thread_id)),
                    os.path.join("data", "installtemp", str(thread_id))
                ]
                
                for directory in directories_to_delete:
                    if os.path.exists(directory):
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                shutil.rmtree(directory)
                                self.log_message(f"已删除目录: {directory}")
                                break
                            except Exception as e:
                                if attempt == max_retries - 1:
                                    self.log_message(f"删除目录失败 {directory}: {str(e)}")
                                time.sleep(0.5)
                
                # 4. 删除暂停状态记录
                pause_status_path = os.path.join("data", "pause_record", "pause_status.json")
                if os.path.exists(pause_status_path):
                    try:
                        with open(pause_status_path, 'r', encoding='utf-8') as f:
                            pause_records = json.load(f)
                        
                        if str(thread_id) in pause_records:
                            del pause_records[str(thread_id)]
                            with open(pause_status_path, 'w', encoding='utf-8') as f:
                                json.dump(pause_records, f, ensure_ascii=False, indent=4)
                            self.log_message(f"已删除暂停记录: thread_id {thread_id}")
                    except Exception as e:
                        self.log_message(f"删除暂停记录失败: {str(e)}")
                
                # 5. 从UI中删除对应行
                for row in range(self.rowCount()):
                    if (self.item(row, 0).data(Qt.ItemDataRole.UserRole) == thread_id):
                        self.removeRow(row)
                        break
                
                self.selected_row = None
                
                self.log_message(f"任务删除成功: thread_id {thread_id}, url {url}")
                
        except Exception as e:
            self.log_message(f"删除任务失败: {str(e)}")
            QMessageBox.critical(
                self,
                "错误",
                f"删除任务失败: {str(e)}",
                QMessageBox.StandardButton.Ok
            )
        finally:
            if lock_file:
                try:
                    # 释放 Windows 文件锁
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                    lock_file.close()
                    os.remove(lock_path)
                except:
                    pass

    def log_message(self, message: str):
        """写入日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_dir = os.path.join("data", "log", "ui")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "download_list.log")
        
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    def _on_resume_download(self, thread_id: int, url: str):
        """处理继续下载信号"""
        try:
            # 更新 downloading.json 中的状态
            with open(self.downloading_path, 'r', encoding='utf-8') as f:
                downloading_tasks = json.load(f)
            
            # 获取文件名
            file_name = None
            for task in downloading_tasks:
                if task['thread_id'] == thread_id and task['url'] == url:
                    task['status'] = '下载中'
                    file_name = task.get('file_name')
                    break
                
            if not file_name:
                self.log_message(f"任务 {thread_id} 继续下载失败：无法找到对应的文件名")
                return

            with open(self.downloading_path, 'w', encoding='utf-8') as f:
                json.dump(downloading_tasks, f, ensure_ascii=False, indent=4)

            # 创建新的一级线程
            from download.v2.first_level_thread import FirstLevelThread
            thread = FirstLevelThread(thread_id)
            thread.url = url
            thread.file_name = file_name
            
            # 将线程添加到活跃线程列表中
            FirstLevelThread._active_threads[thread_id] = thread
            
            # 启动线程
            thread.start()
            
            # 删除暂停记录
            pause_record_path = os.path.join("data", "pause_record", "pause_status.json")
            try:
                with open(pause_record_path, 'r', encoding='utf-8') as f:
                    pause_records = json.load(f)
                if str(thread_id) in pause_records:
                    del pause_records[str(thread_id)]
                    with open(pause_record_path, 'w', encoding='utf-8') as f:
                        json.dump(pause_records, f, ensure_ascii=False, indent=4)
            except FileNotFoundError:
                pass
            
            # 更新UI状态
            self.update_task(thread_id, status="下载中")
            self.context_menu.update_menu_state(is_paused=False)
            
            self.log_message(f"任务 {thread_id} 已重新启动下载")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "错误",
                f"继续下载失败: {str(e)}",
                QMessageBox.StandardButton.Ok
            )

    def paintEvent(self, event):
        """重写绘制事件，确保正确结束painter"""
        try:
            painter = QPainter(self.viewport())
            try:
                super().paintEvent(event)
            finally:
                painter.end()
        except Exception as e:
            print(f"绘制错误: {str(e)}")

    def _on_delete_completed_file(self, file_path: str):
        """处理删除已完成文件的信号"""
        try:
            # 从UI中删除对应行
            for row in range(self.rowCount()):
                file_name = os.path.basename(file_path)
                if self.item(row, 0).text() == file_name:
                    self.removeRow(row)
                    break
            
            # 从downloading.json中删除记录
            try:
                with open(self.downloading_path, 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
                
                tasks = [task for task in tasks if task.get('save_path') != file_path]
                
                with open(self.downloading_path, 'w', encoding='utf-8') as f:
                    json.dump(tasks, f, indent=4, ensure_ascii=False)
                    
            except Exception as e:
                print(f"更新downloading.json失败: {str(e)}")
                
        except Exception as e:
            print(f"删除已完成文件失败: {str(e)}")

    def mousePressEvent(self, event):
        """处理鼠标点击事件"""
        item = self.itemAt(event.pos())
        if item is None:  # 点击空白处
            self.clearSelection()  # 清除选择
            self.row_selected.emit(-1)  # 发送一个无效的thread_id表示取消选择
        else:
            super().mousePressEvent(event)  # 正常处理点击事件
>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
