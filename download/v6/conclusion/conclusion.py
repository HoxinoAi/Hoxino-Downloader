<<<<<<< HEAD
import os
from datetime import datetime
from typing import Dict, List
from download.util.Settings_util import SettingsUtil
from queuemanagement.queuemanagement import DatabaseManager

class Conclusion:
    def __init__(self, primary_thread_id: int):
        """
        初始化结论处理类
        Args:
            primary_thread_id: 一级线程ID
        """
        self.primary_thread_id = primary_thread_id
        self.settings = SettingsUtil()
        self.db_manager = DatabaseManager()
        
        # 设置日志路径
        self.log_dir = os.path.join("data", "log", "conclusion")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, f"{primary_thread_id}.txt")
        
    def log_message(self, message: str):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
            
    def process(self, file_name: str, download_path: str):
        """处理下载完成的任务
        Args:
            file_name: 文件名
            download_path: 文件下载路径
        """
        try:
            self.log_message(f"开始处理任务: {file_name}")
            
            # 1. 从downloading表移动到downloaded表，并保存下载路径
            if self.db_manager.move_task_to_downloaded(file_name, download_path):
                self.log_message(f"成功将任务移动到已完成: {file_name}")
            else:
                self.log_message(f"移动任务失败: {file_name}")
                return
            
            # 2. 检查waiting表并移动任务到downloading表
            self._check_waiting_tasks()
            
        except Exception as e:
            self.log_message(f"处理失败: {str(e)}")
            
    def _check_waiting_tasks(self):
        """检查等待中的任务"""
        try:
            # 获取最大任务数
            max_tasks = self.settings.get_max_tasks()
            
            # 获取当前下载中的任务数
            current_tasks = self.db_manager.get_downloading_count()
            
            # 如果下载中的任务数小于最大任务数，则从等待队列中移动任务
            if current_tasks < max_tasks:
                # 移动下一个等待任务到下载队列
                if self.db_manager.move_next_waiting_to_downloading():
                    self.log_message("已将等待任务移动到下载队列")
                    
                    # 获取更新后的下载任务列表
                    downloading_tasks = self.db_manager.get_downloading_tasks()
                    
                    # 调用FirstLevelThread管理器
                    from download.v2.first_level_thread import FirstLevelThread
                    FirstLevelThread.manage_threads(downloading_tasks, max_tasks)
                    
        except Exception as e:
            self.log_message(f"检查等待任务失败: {str(e)}")
=======
import os
import json
from datetime import datetime
from typing import Dict, List
from download.util.Settings_util import SettingsUtil

class Conclusion:
    def __init__(self, primary_thread_id: int):
        """
        初始化结论处理类
        Args:
            primary_thread_id: 一级线程ID
        """
        self.primary_thread_id = primary_thread_id
        self.settings = SettingsUtil()
        self.base_path = os.path.join("data", "queuemanagement")
        self.downloading_path = os.path.join(self.base_path, "downloading.json")
        self.downloaded_path = os.path.join(self.base_path, "downloaded.json")
        self.waiting_path = os.path.join(self.base_path, "waiting.json")
        
        # 设置日志路径
        self.log_dir = os.path.join("data", "log", "conclusion")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, f"{primary_thread_id}.txt")
        
    def log_message(self, message: str):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
            
    def process(self, url: str):
        """处理下载完成的URL"""
        try:
            self.log_message(f"开始处理URL: {url}")
            
            # 1. 从downloading.json移动到downloaded.json
            self._move_to_downloaded(url)
            
            # 2. 检查waiting.json并移动任务到downloading.json
            self._check_waiting_tasks()
            
        except Exception as e:
            self.log_message(f"处理失败: {str(e)}")
            
    def _move_to_downloaded(self, url: str):
        """将URL从downloading移动到downloaded"""
        with open(self.downloading_path, 'r', encoding='utf-8') as f:
                downloading_tasks = json.load(f)
            
            # 找到对应的任务
        task_to_move = None
        remaining_tasks = []
            
        for task in downloading_tasks:
                if task["url"] == url:
                    task_to_move = task.copy()
                    task_to_move["status"] = "已完成"
                    task_to_move["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                else:
                    remaining_tasks.append(task)
            
            # 更新downloading.json
        with open(self.downloading_path, 'w', encoding='utf-8') as f:
                json.dump(remaining_tasks, f, ensure_ascii=False, indent=4)
            
            
            
    def _check_waiting_tasks(self):
        """检查等待中的任务"""
        try:
            # 获取最大任务数
            max_tasks = self.settings.get_max_tasks()
            
            # 读取当前下载中的任务
            with open(self.downloading_path, 'r', encoding='utf-8') as f:
                downloading_tasks = json.load(f)
            
            # 如果下载中的任务数小于最大任务数，则从等待队列中移动任务
            if len(downloading_tasks) < max_tasks:
                # 读取等待中的任务
                with open(self.waiting_path, 'r', encoding='utf-8') as f:
                    waiting_tasks = json.load(f)
                
                if waiting_tasks:
                    # 移动第一个等待中的任务
                    task_to_move = waiting_tasks.pop(0)
                    task_to_move["status"] = "下载中"
                    
                    # 更新waiting.json
                    with open(self.waiting_path, 'w', encoding='utf-8') as f:
                        json.dump(waiting_tasks, f, ensure_ascii=False, indent=4)
                    
                    # 更新downloading.json
                    downloading_tasks.append(task_to_move)
                    with open(self.downloading_path, 'w', encoding='utf-8') as f:
                        json.dump(downloading_tasks, f, ensure_ascii=False, indent=4)
                    
                    self.log_message(f"已将等待任务移动到下载队列: {task_to_move['url']}")
                    
                    # 调用FirstLevelThread管理器
                    from download.v2.first_level_thread import FirstLevelThread
                    FirstLevelThread.manage_threads(downloading_tasks, max_tasks)
                    
        except Exception as e:
            self.log_message(f"检查等待任务失败: {str(e)}")
>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
