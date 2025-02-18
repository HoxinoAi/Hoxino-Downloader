<<<<<<< HEAD
import json
import os
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
from download.v6.progress.progress import Progress
from queuemanagement.queuemanagement import DatabaseManager


class TabManager:
    def __init__(self, tab_widget: QTableWidget, tab_name: str):
        """
        初始化标签页管理器
        Args:
            tab_widget: 表格控件
            tab_name: 标签页名称（已完成/下载中/等待中/错误）
        """
        self.tab_widget = tab_widget
        self.tab_name = tab_name
        self.db_manager = DatabaseManager()
        
        # 设置表头
        if self.tab_name == "错误":
            self.tab_widget.setColumnCount(2)
            self.tab_widget.setHorizontalHeaderLabels(["URL", "错误信息"])
        else:
            self.tab_widget.setColumnCount(5)
            self.tab_widget.setHorizontalHeaderLabels([
                "文件名", "大小", "状态", "进度", "时间"
            ])
        
        # 映射标签页名称到数据库表名
        self.table_mapping = {
            "下载中": "downloading",
            "等待中": "waiting",
            "已完成": "downloaded",
            "错误": "error"
        }
        
        # 设置更短的检查间隔
        self.file_check_timer = QTimer()
        self.file_check_timer.timeout.connect(self.check_database_changes)
        self.file_check_timer.start(50)  # 每50ms检查一次
        
        self.last_content = self._get_current_content()
        self.update_table()  # 初始加载
        
        # 进度管理字典
        self.progress_managers = {}

    def _get_current_content(self) -> str:
        """获取当前数据库内容的哈希值"""
        try:
            tasks = self.db_manager.get_tasks_by_type(self.table_mapping[self.tab_name])
            return str(hash(str(tasks)))  # 使用字符串哈希值作为内容标识
        except Exception as e:
            return ""

    def check_database_changes(self):
        """检查数据库是否发生变化"""
        current_content = self._get_current_content()
            # 只有当内容真正发生变化时才更新
        if current_content and current_content != self.last_content:
            self.last_content = current_content
            self.update_table()
                

    def register_progress_manager(self, thread_id: int):
        """注册新的进度管理器"""
        try:
            if thread_id not in self.progress_managers:
                progress_manager = Progress(thread_id)
                # 确保信号连接成功
                progress_manager.progress_updated.connect(self.update_progress)
                self.progress_managers[thread_id] = progress_manager
                return progress_manager
            return self.progress_managers[thread_id]
        except Exception as e:
            import traceback
            return None

    def update_progress(self, thread_id: int, progress: float):
        """更新特定任务的进度"""
        try:
            # 更新表格中的进度
            for row in range(self.tab_widget.rowCount()):
                item_thread_id = self.tab_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
                if item_thread_id == thread_id:
                    progress_text = f"{progress:.1f}%"
                    self.tab_widget.setItem(row, 3, QTableWidgetItem(progress_text))
                    
                    # 如果进度达到100%，更新状态为"已完成"
                    if progress >= 100:
                        self.tab_widget.setItem(row, 2, QTableWidgetItem("已完成"))
                    
                    # 强制更新视图
                    self.tab_widget.viewport().update()
                    break
                
        except Exception as e:
            import traceback

    def update_table(self):
        """更新表格数据"""
        try:
            # 获取任务列表
            tasks = self.db_manager.get_tasks_by_type(self.table_mapping[self.tab_name])
            
            if not tasks:
                self.tab_widget.setRowCount(0)
                return
            
            # 保存当前选中的行
            selected_rows = {self.tab_widget.item(item.row(), 0).text() 
                           for item in self.tab_widget.selectedItems() 
                           if self.tab_widget.item(item.row(), 0)}
            
            # 更新表格
            self.tab_widget.setRowCount(len(tasks))
            
            # 更新内容
            for row, task in enumerate(tasks):
                if self.tab_name == "错误":
                    self.tab_widget.setItem(row, 0, QTableWidgetItem(str(task.get("url", ""))))
                    self.tab_widget.setItem(row, 1, QTableWidgetItem(str(task.get("error_msg", ""))))
                else:
                    # 获取进度值，对于已完成的任务，设置为100%
                    progress = task.get('progress')
                    if task.get('status') == "已完成":
                        progress = 100.0
                    elif progress is None:
                        progress = 0.0
                    else:
                        try:
                            progress = float(progress)
                        except (ValueError, TypeError):
                            progress = 0.0
                    
                    columns = [
                        str(task.get("file_name", "")),
                        self._format_size(task.get("size", 0)),
                        str(task.get("status", "")),
                        f"{progress:.1f}%",
                        str(task.get("time", ""))
                    ]
                    
                    for col, value in enumerate(columns):
                        table_item = QTableWidgetItem(value)
                        if col == 0:  # 在文件名列存储thread_id
                            table_item.setData(Qt.ItemDataRole.UserRole, task.get("thread_id"))
                        self.tab_widget.setItem(row, col, table_item)
                    
                    # 恢复选中状态
                    if str(task.get("file_name", "")) in selected_rows:
                        self.tab_widget.selectRow(row)
                    
                    # 注册进度管理器（仅对下载中的任务）
                    if self.tab_name == "下载中" and task.get("thread_id"):
                        self.register_progress_manager(task["thread_id"])
            
            # 强制更新视图
            self.tab_widget.viewport().update()
            
        except Exception as e:
            import traceback

    def _format_size(self, size_in_bytes: int) -> str:
        """格式化文件大小"""
        try:
            size_in_bytes = float(size_in_bytes)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_in_bytes < 1024:
                    return f"{size_in_bytes:.1f} {unit}"
                size_in_bytes /= 1024
            return f"{size_in_bytes:.1f} TB"
        except (ValueError, TypeError):
            return "0 B"
=======
import json
import os
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
from download.v6.progress.progress import Progress
from queuemanagement.queuemanagement import QueueManagement

class TabManager:
    def __init__(self, tab_widget: QTableWidget, tab_name: str):
        """
        初始化标签页管理器
        Args:
            tab_widget: 表格控件
            tab_name: 标签页名称（downloaded/downloading/waiting/error）
        """
        self.tab_widget = tab_widget
        self.tab_name = tab_name
        
        # 映射标签页名称到对应的json文件
        self.json_mapping = {
            "下载中": "downloading.json",
            "等待中": "waiting.json",
            "已完成": "downloaded.json",
            "错误": "error.json"
        }
        
        # 获取对应的json文件路径
        self.json_path = os.path.join("data", "queuemanagement", self.json_mapping.get(tab_name))
        
        print(f"初始化 {self.tab_name} 标签页管理器")
        
        # 确保队列文件存在
        if not os.path.exists(self.json_path):
            queue_manager = QueueManagement()
            queue_manager.initialize_queue_files()
        
        # 设置更短的检查间隔
        self.file_check_timer = QTimer()
        self.file_check_timer.timeout.connect(self.check_file_changes)
        self.file_check_timer.start(50)  # 每50ms检查一次
        
        self.last_content = self._read_file_content()
        self.update_table()  # 初始加载
        
        # 进度管理字典
        self.progress_managers = {}

    def _read_file_content(self):
        """读取文件内容"""
        try:
            if os.path.exists(self.json_path):
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    # 只在内容确实有问题时才修复
                    if content.endswith(']]') or not content.endswith(']'):
                        return self._fix_json_content(content)
                    return content
            return ""
        except Exception as e:
            print(f"读取文件失败: {str(e)}")
            return ""

    def check_file_changes(self):
        """检查文件是否发生变化"""
        try:
            current_content = self._read_file_content()
            
            # 只有当内容真正发生变化时才更新
            if current_content and current_content != self.last_content:
                try:
                    # 验证JSON格式
                    json.loads(current_content)
                    self.last_content = current_content
                    self.update_table()
                except json.JSONDecodeError:
                    print("检测到无效的JSON格式，跳过更新")
                
        except Exception as e:
            print(f"检查文件变化失败: {str(e)}")

    def register_progress_manager(self, thread_id: int):
        """注册新的进度管理器"""
        try:
            if thread_id not in self.progress_managers:
                progress_manager = Progress(thread_id)
                # 确保信号连接成功
                progress_manager.progress_updated.connect(self.update_progress)
                self.progress_managers[thread_id] = progress_manager
                print(f"已注册进度管理器: thread_id={thread_id}")
                return progress_manager
            return self.progress_managers[thread_id]
        except Exception as e:
            print(f"注册进度管理器失败: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return None

    def update_progress(self, thread_id: int, progress: float):
        """更新特定任务的进度"""
        try:
            print(f"收到进度更新: thread_id={thread_id}, progress={progress:.1f}%")
            # 更新表格中的进度
            for row in range(self.tab_widget.rowCount()):
                item_thread_id = self.tab_widget.item(row, 0).data(Qt.ItemDataRole.UserRole)
                if item_thread_id == thread_id:
                    progress_text = f"{progress:.1f}%"
                    self.tab_widget.setItem(row, 3, QTableWidgetItem(progress_text))
                    
                    # 如果进度达到100%，更新状态为"已完成"
                    if progress >= 100:
                        self.tab_widget.setItem(row, 2, QTableWidgetItem("已完成"))
                    
                    # 强制更新视图
                    self.tab_widget.viewport().update()
                    break
                
        except Exception as e:
            print(f"更新进度失败: {str(e)}")
            import traceback
            print(traceback.format_exc())

    def _fix_json_content(self, content: str) -> str:
        """修复JSON内容中可能存在的格式问题"""
        try:
            # 尝试直接解析
            json.loads(content)
            return content
        except json.JSONDecodeError:
            try:
                fixed_content = content
                # 去除多余的右方括号
                if content.strip().endswith(']]'):
                    fixed_content = content.strip()[:-1]
                # 如果缺少右方括号
                elif not content.strip().endswith(']'):
                    fixed_content = content.strip() + ']'
                
                # 验证修复后的内容
                json.loads(fixed_content)
                return fixed_content
                
            except Exception as fix_error:
                print(f"JSON修复失败: {str(fix_error)}")
                return content

    def update_table(self):
        """更新表格数据"""
        try:
            if not os.path.exists(self.json_path):
                self.tab_widget.setRowCount(0)
                return
            
            # 读取并修复JSON数据
            with open(self.json_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    self.tab_widget.setRowCount(0)
                    return
                
                # 修复JSON内容
                fixed_content = self._fix_json_content(content)
                
                # 如果内容被修复，同时更新文件
                if fixed_content != content:
                    with open(self.json_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                
                data = json.loads(fixed_content)
                if not isinstance(data, list):
                    data = [data]
                
                # 过滤掉无效数据
                data = [item for item in data if isinstance(item, dict)]
                
                # 保存当前选中的行
                selected_rows = {self.tab_widget.item(item.row(), 0).text() 
                               for item in self.tab_widget.selectedItems() 
                               if self.tab_widget.item(item.row(), 0)}
                
                # 更新表格
                self.tab_widget.setRowCount(len(data))
                
                # 更新内容
                for row, item in enumerate(data):
                    if self.tab_name == "错误":
                        self.tab_widget.setItem(row, 0, QTableWidgetItem(str(item.get("url", ""))))
                        self.tab_widget.setItem(row, 1, QTableWidgetItem(str(item.get("error", ""))))
                    else:
                        columns = [
                            str(item.get("file_name", "")),
                            self._format_size(item.get("size", 0)),
                            str(item.get("status", "")),
                            f"{item.get('progress', 0):.1f}%" if "progress" in item else "",
                            str(item.get("time", ""))
                        ]
                        
                        for col, value in enumerate(columns):
                            table_item = QTableWidgetItem(value)
                            self.tab_widget.setItem(row, col, table_item)
                        
                        # 恢复选中状态
                        if str(item.get("file_name", "")) in selected_rows:
                            self.tab_widget.selectRow(row)
                        
                        # 注册进度管理器
                        if self.tab_name == "下载中" and "thread_id" in item:
                            self.register_progress_manager(item["thread_id"])
                
                # 强制更新视图
                self.tab_widget.viewport().update()
                
        except Exception as e:
            print(f"更新表格失败: {str(e)}")
            import traceback
            print(traceback.format_exc())

    def _format_size(self, size_in_bytes: int) -> str:
        """格式化文件大小"""
        try:
            size_in_bytes = float(size_in_bytes)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_in_bytes < 1024:
                    return f"{size_in_bytes:.1f} {unit}"
                size_in_bytes /= 1024
            return f"{size_in_bytes:.1f} TB"
        except (ValueError, TypeError):
            return "0 B"
>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
