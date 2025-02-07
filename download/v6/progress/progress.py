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
