import json
import os
from datetime import datetime
import threading
from typing import Dict
import time

class PauseMonitoring:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.monitoring_file = os.path.join("data", "Pausemonitoring", "Pausemonitoring.json")
            self.lock = threading.Lock()
            self.is_running = False
            self.monitor_thread = None
            self.initialized = True
            
            try:
                # 确保目录存在
                os.makedirs(os.path.dirname(self.monitoring_file), exist_ok=True)
                
                # 检查文件是否存在，不存在则创建
                if not os.path.exists(self.monitoring_file):
                    print(f"创建监控文件: {self.monitoring_file}")
                    self.monitoring_data = {}
                    with open(self.monitoring_file, 'w', encoding='utf-8') as f:
                        json.dump(self.monitoring_data, f, ensure_ascii=False, indent=4)
                else:
                    # 读取现有文件
                    with open(self.monitoring_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        self.monitoring_data = json.loads(content) if content else {}
                
            except Exception as e:
                print(f"初始化监控文件时出错: {str(e)}")
                # 出错时创建新的空文件
                self.monitoring_data = {}
                try:
                    with open(self.monitoring_file, 'w', encoding='utf-8') as f:
                        json.dump(self.monitoring_data, f, ensure_ascii=False, indent=4)
                except Exception as write_error:
                    print(f"创建新文件时出错: {str(write_error)}")

    def _get_key(self, url: str, thread_id: int) -> str:
        """生成唯一键值"""
        return f"{url}_{thread_id}"

    def start_monitoring(self):
        """启动监控线程"""
        if not self.is_running:
            self.is_running = True
            self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitor_thread.start()

    def stop_monitoring(self):
        """停止监控线程"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def _monitoring_loop(self):
        """监控循环"""
        while self.is_running:
            # 这里可以添加定期检查或其他监控逻辑
            time.sleep(1)  # 每秒检查一次

    def update_progress(self, url: str, thread_id: int, stage: str, file_name: str = None):
        """
        更新URL的进度信息
        
        Args:
            url: 下载的URL
            thread_id: 处理该URL的线程ID
            stage: 当前进度阶段
            file_name: 文件名（可选）
        """
        with self.lock:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            key = self._get_key(url, thread_id)
            
            if key not in self.monitoring_data:
                self.monitoring_data[key] = {
                    "url": url,
                    "thread_id": thread_id,
                    "file_name": file_name,
                    "stages": [],
                    "current_stage": stage,
                    "last_update": current_time
                }
            elif file_name and not self.monitoring_data[key].get("file_name"):
                # 如果已存在记录但没有文件名，则更新文件名
                self.monitoring_data[key]["file_name"] = file_name
            
            self.monitoring_data[key]["stages"].append({
                "stage": stage,
                "timestamp": current_time
            })
            self.monitoring_data[key]["current_stage"] = stage
            self.monitoring_data[key]["last_update"] = current_time
            
            # 保存到json文件
            self._save_to_json()

    def get_url_progress(self, url: str, thread_id: int = None) -> dict:
        """
        获取指定URL的进度信息
        
        Args:
            url: 下载URL
            thread_id: 线程ID（可选）
        
        Returns:
            如果指定了thread_id，返回特定线程的进度
            否则返回所有匹配该URL的进度
        """
        if thread_id is not None:
            key = self._get_key(url, thread_id)
            return self.monitoring_data.get(key, {})
        else:
            # 返回所有匹配该URL的进度
            return {
                key: data for key, data in self.monitoring_data.items()
                if data.get("url") == url
            }

    def get_all_progress(self) -> dict:
        """获取所有URL的进度信息"""
        return self.monitoring_data

    def _save_to_json(self):
        """将监控数据保存到json文件"""
        with open(self.monitoring_file, 'w', encoding='utf-8') as f:
            json.dump(self.monitoring_data, f, ensure_ascii=False, indent=4)

# 创建单例实例
pause_monitor = PauseMonitoring()
