<<<<<<< HEAD
import os
import time
from typing import Dict
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal
from queuemanagement.queuemanagement import DatabaseManager
import traceback

class Progress(QObject):
    progress_updated = pyqtSignal(str, float)  # (file_name, progress)
    
    def __init__(self, file_name: str):
        """
        初始化进度监控
        Args:
            file_name: 文件名（唯一标识）
        """
        super().__init__()
        self.file_name = file_name
        self.db_manager = DatabaseManager()
        
        # 创建进度日志目录和文件
        self.log_dir = os.path.join("data", "log", "progress")
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 确保文件名安全且添加前缀
        safe_filename = self._get_safe_filename(file_name)
        self.log_path = os.path.join(self.log_dir, f"progress_{safe_filename}.txt")
        
        # 打印初始化信息
        self.log_message(f"初始化进度监控")
        self.log_message(f"传入的文件名: {file_name}")
        self.log_message(f"日志文件路径: {self.log_path}")
        
        # 存储每个二级线程的进度
        self.thread_progress: Dict[int, dict] = {}
        self.max_progress = 0.0
        
        # 获取线程数
        self.expected_threads = self._get_thread_count()
        
        # 添加进度计算时间控制
        self.last_db_update = 0
        self.db_update_interval = 2.0  # 2秒更新一次数据库
        
        # 缓存最新的总进度
        self.cached_total_progress = 0.0
        
    def _get_safe_filename(self, filename: str) -> str:
        """生成安全的文件名"""
        invalid_chars = '<>:"/\\|?*'
        safe_name = ''.join(c if c not in invalid_chars else '_' for c in str(filename))
        return safe_name
        
    def _get_thread_count(self) -> int:
        """获取文件的线程数"""
        try:
            thread_count = self.db_manager.get_thread_count_by_filename(self.file_name)
            self.log_message(f"查询到的线程数: {thread_count}")
            return thread_count if thread_count and thread_count > 0 else 10
        except Exception as e:
            self.log_message(f"获取线程数失败: {str(e)}")
            return 10
            
    def update_progress(self, secondary_thread_id: int, progress: float, chunk_size: int = 1):
        """更新指定线程的进度"""
        try:
            progress = round(max(0, min(100, progress)), 2)
            
            # 记录之前的进度
            old_progress = self.thread_progress.get(secondary_thread_id, {}).get('progress', 0)
            
            # 更新线程进度
            self.thread_progress[secondary_thread_id] = {
                'progress': progress,
                'size': chunk_size
            }
            
            # 计算新的总进度
            total_progress = self._calculate_total_progress()
            
            # 只在进度有变化时更新
            if total_progress != self.cached_total_progress:
                self.cached_total_progress = total_progress
                self.progress_updated.emit(self.file_name, total_progress)
                # 定期更新数据库
                current_time = time.time()
                if current_time - self.last_db_update >= self.db_update_interval:
                    self._batch_update_progress()
                    self.last_db_update = current_time
                    self.log_message("触发数据库更新")
                
        except Exception as e:
            self.log_message(f"更新进度失败: {str(e)}")
            self.log_message(traceback.format_exc())
            
    def _batch_update_progress(self):
        """批量更新数据库中的进度"""
        try:
            with self.db_manager.get_connection() as conn:
                # 更新总进度
                conn.execute("""
                    UPDATE downloading 
                    SET progress = ?
                    WHERE file_name = ?
                """, (self.cached_total_progress, self.file_name))
                
                # 批量更新二级线程进度
                for thread_id, info in self.thread_progress.items():
                    conn.execute(f"""
                        UPDATE downloading 
                        SET progress_{thread_id} = ?
                        WHERE file_name = ?
                    """, (info['progress'], self.file_name))
                
                conn.commit()
                
                # 添加日志记录
                self.log_message(f"更新总进度: {self.cached_total_progress}%")
                self.log_message(f"更新线程进度: {dict(self.thread_progress)}")
                
        except Exception as e:
            self.log_message(f"批量更新进度失败: {str(e)}")
            self.log_message(traceback.format_exc())  # 添加详细错误信息
        
    def _calculate_total_progress(self) -> float:
        """
        计算总进度（所有二级线程进度的算术平均值）
        每2秒计算一次
        Returns:
            float: 平均进度（0-100）
        """
        try:
            if not self.thread_progress or self.expected_threads <= 0:
                return 0.0
            
            # 计算所有已汇报线程的进度总和
            total_progress = sum(info['progress'] for info in self.thread_progress.values())
            
            # 计算平均进度（未汇报的线程按0%计算）
            average_progress = total_progress / self.expected_threads
            
            # 更新最大进度记录
            self.max_progress = max(self.max_progress, average_progress)
            
           
            
            return round(average_progress, 2)
            
        except Exception as e:
            self.log_message(f"计算总进度失败: {str(e)}")
            return 0.0
        
    def _write_progress(self):
        """将所有线程的进度写入日志文件"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(self.log_path, 'w', encoding='utf-8') as f:
            f.write(f"[{timestamp}] 下载进度报告:\n")
            for thread_id, info in sorted(self.thread_progress.items()):
                f.write(f"二级线程 {thread_id}: {info['progress']:.2f}% (分片大小: {info['size']} bytes)\n")
            
            # 计算加权总进度
            total_progress = self._calculate_total_progress()
            f.write(f"\n总体进度: {total_progress:.2f}%\n")
            
    def log_message(self, message: str):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
=======
import os
import json
import time
from typing import Dict
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal

class Progress(QObject):
    # 添加进度更新信号
    progress_updated = pyqtSignal(int, float)  # (thread_id, progress)
    
    def __init__(self, primary_thread_id: int):
        """
        初始化进度监控
        Args:
            primary_thread_id: 一级线程ID
        """
        super().__init__()
        self.primary_thread_id = primary_thread_id
        
        # 创建进度日志目录和文件
        self.log_dir = os.path.join("data", "log", "progress")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, f"{primary_thread_id}.txt")
        
        # 存储每个二级线程的进度和分片大小
        self.thread_progress: Dict[int, dict] = {}
        
        # 下载管理文件路径
        self.downloading_path = os.path.join("data", "queuemanagement", "downloading.json")
        
        # 添加最大进度记录
        self.max_progress = 0.0
        
      
        
    def update_progress(self, secondary_thread_id: int, progress: float, chunk_size: int = 1):
        """更新指定二级线程的进度"""
        self.thread_progress[secondary_thread_id] = {
            'progress': progress,
            'size': chunk_size
        }
        
        # 计算总进度
        current_progress = self._calculate_total_progress()
        
        # 确保进度只能增加，不能减少
        if current_progress > self.max_progress:
            self.max_progress = current_progress
            # 写入日志和更新文件
            self._write_progress()
            self._update_downloading_json()
        
        # 发出进度更新信号
        self.progress_updated.emit(secondary_thread_id, progress)
        
    def _calculate_total_progress(self) -> float:
        """
        计算总进度（所有二级线程进度的算术平均值）
        Returns:
            float: 平均进度（0-100）
        """
        if not self.thread_progress:
            return 0.0
        
        # 直接计算所有线程进度的平均值
        total_progress = sum(info['progress'] for info in self.thread_progress.values())
        average_progress = total_progress / len(self.thread_progress)
        
        return round(average_progress, 2)
        
    def _write_progress(self):
        """将所有线程的进度写入日志文件"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(self.log_path, 'w', encoding='utf-8') as f:
            f.write(f"[{timestamp}] 下载进度报告:\n")
            for thread_id, info in sorted(self.thread_progress.items()):
                f.write(f"二级线程 {thread_id}: {info['progress']:.2f}% (分片大小: {info['size']} bytes)\n")
            
            # 计算加权总进度
            total_progress = self._calculate_total_progress()
            f.write(f"\n总体进度: {total_progress:.2f}%\n")
                
    def _update_downloading_json(self):
        """更新downloading.json中的进度"""
        try:
            if not self.thread_progress:
                return
                
            max_retries = 5
            retry_delay = 0.1  # 100ms
            
            for attempt in range(max_retries):
                try:
                    # 读取当前文件内容
                    try:
                        with open(self.downloading_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            # 检查并修复JSON格式
                            if content.endswith(']]'):
                                content = content[:-1]
                            downloading_tasks = json.loads(content)
                            if not isinstance(downloading_tasks, list):
                                downloading_tasks = [downloading_tasks]
                        
                        # 只更新匹配的任务进度
                        for task in downloading_tasks:
                            if task.get('thread_id') == self.primary_thread_id:
                                existing_progress = float(task.get('progress', 0))
                                # 只有当新进度大于现有进度时才更新
                                if self.max_progress > existing_progress:
                                    task['progress'] = self.max_progress
                                    
                        
                        # 写回文件
                        with open(self.downloading_path, 'w', encoding='utf-8') as f:
                            json.dump(downloading_tasks, f, ensure_ascii=False, indent=4)
                        
                        # 如果成功，跳出重试循环
                        break
                        
                    except json.JSONDecodeError as e:
                        self.log_message(f"JSON解析错误: {str(e)}")
                        if attempt == max_retries - 1:
                            raise
                            
                except PermissionError:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    raise
                    
        except Exception as e:
            self.log_message(f"更新进度过程中发生错误: {str(e)}")
            
    def log_message(self, message: str):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
