<<<<<<< HEAD
import os
import time
import requests
from typing import Dict
from download.util.Settings_util import SettingsUtil
from download.v6.install.Secondary_thread_install import SecondaryThreadInstall

class SecondaryThreadRequest:
    def __init__(self, primary_thread_id: int, secondary_thread_id: int, chunk_info: Dict, temp_dir: str, download_mode: str, file_name: str):
        self.primary_thread_id = primary_thread_id
        self.secondary_thread_id = secondary_thread_id
        self.chunk_info = chunk_info
        self.temp_dir = temp_dir
        self.download_mode = download_mode
        self.file_name = file_name
        self.settings = SettingsUtil()
        
        # 设置重试参数
        self.retry_count = 0
        self.max_retries = 6
        self.timeout = 7
        
        # 设置日志路径
        self.log_dir = os.path.join("data", "log", "Second_level_process", str(primary_thread_id))
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, f"{secondary_thread_id}.txt")
        
    def log_message(self, message: str):
        """写入日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
            
    def start(self):
        """开始请求"""
        
        
        self.log_message("开始请求过程")
        
        while self.retry_count < self.max_retries:
            try:
                headers = {
                    'Range': f'bytes={self.chunk_info["start"]}-{self.chunk_info["end"]}',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                # 通知准备发送请求
                
                
                if self.download_mode == "proxy":
                    proxy_config = self.settings.get_proxy_config()
                    proxies = {
                        'http': f'http://{proxy_config["host"]}:{proxy_config["port"]}',
                        'https': f'http://{proxy_config["host"]}:{proxy_config["port"]}'
                    }
                    self.log_message("使用代理模式请求")
                    
                   
                    response = requests.get(
                        self.chunk_info['url'], 
                        headers=headers, 
                        proxies=proxies, 
                        timeout=self.timeout, 
                        stream=True
                    )
                else:
                    self.log_message("使用常规模式请求")
                    
                    
                    response = requests.get(
                        self.chunk_info['url'], 
                        headers=headers, 
                        timeout=self.timeout, 
                        stream=True
                    )
                    
                # 检查响应状态码
                if response.status_code in [200, 206]:
                    self.log_message("请求成功，开始下载")
                   
                    
                    self._start_download()
                    break
                else:
                    error_msg = f"请求返回错误状态码: {response.status_code}"
                    raise Exception(error_msg)
                    
            except Exception as e:
                self.retry_count += 1
                error_msg = str(e)
                self.log_message(f"请求失败: {error_msg}")
                
               
                if self.retry_count < self.max_retries:
                    self.log_message(f"等待重试 (第 {self.retry_count} 次)")
                    
                    time.sleep(1)  # 等待1秒后重试
                else:
                    self.log_message("请求失败，已达到最大重试次数")
                    
                 
                    
    def _start_download(self):
        """启动下载"""
        
        install = SecondaryThreadInstall(
            primary_thread_id=self.primary_thread_id,
            secondary_thread_id=self.secondary_thread_id,
            chunk_info=self.chunk_info,
            temp_dir=self.temp_dir,
            download_mode=self.download_mode,
            file_name=self.file_name
        )
        install.start()
=======
import os
import time
import requests
from typing import Dict
from download.util.Settings_util import SettingsUtil
from download.v6.install.Secondary_thread_install import SecondaryThreadInstall

class SecondaryThreadRequest:
    def __init__(self, primary_thread_id: int, secondary_thread_id: int, chunk_info: Dict, temp_dir: str, download_mode: str):
        self.primary_thread_id = primary_thread_id
        self.secondary_thread_id = secondary_thread_id
        self.chunk_info = chunk_info
        self.temp_dir = temp_dir
        self.download_mode = download_mode
        self.settings = SettingsUtil()
        
        # 设置重试参数
        self.retry_count = 0
        self.max_retries = 6
        self.timeout = 7
        
        # 设置日志路径
        self.log_dir = os.path.join("data", "log", "Second_level_process", str(primary_thread_id))
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, f"{secondary_thread_id}.txt")
        
    def log_message(self, message: str):
        """写入日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
            
    def start(self):
        """开始请求"""
        from download.Pausemonitoring.Pause_monitoring import pause_monitor
        
        # 通知开始请求过程
        pause_monitor.update_progress(
            url=self.chunk_info['url'],
            thread_id=self.primary_thread_id,
            stage=f"二级线程 {self.secondary_thread_id} 开始请求阶段"
        )
        
        self.log_message("开始请求过程")
        
        while self.retry_count < self.max_retries:
            try:
                headers = {
                    'Range': f'bytes={self.chunk_info["start"]}-{self.chunk_info["end"]}',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                # 通知准备发送请求
                pause_monitor.update_progress(
                    url=self.chunk_info['url'],
                    thread_id=self.primary_thread_id,
                    stage=f"二级线程 {self.secondary_thread_id} 准备发送请求"
                )
                
                if self.download_mode == "proxy":
                    proxy_config = self.settings.get_proxy_config()
                    proxies = {
                        'http': f'http://{proxy_config["host"]}:{proxy_config["port"]}',
                        'https': f'http://{proxy_config["host"]}:{proxy_config["port"]}'
                    }
                    self.log_message("使用代理模式请求")
                    
                    # 通知使用代理模式
                    pause_monitor.update_progress(
                        url=self.chunk_info['url'],
                        thread_id=self.primary_thread_id,
                        stage=f"二级线程 {self.secondary_thread_id} 使用代理模式发送请求"
                    )
                    
                    response = requests.get(
                        self.chunk_info['url'], 
                        headers=headers, 
                        proxies=proxies, 
                        timeout=self.timeout, 
                        stream=True
                    )
                else:
                    self.log_message("使用常规模式请求")
                    
                    # 通知使用常规模式
                    pause_monitor.update_progress(
                        url=self.chunk_info['url'],
                        thread_id=self.primary_thread_id,
                        stage=f"二级线程 {self.secondary_thread_id} 使用常规模式发送请求"
                    )
                    
                    response = requests.get(
                        self.chunk_info['url'], 
                        headers=headers, 
                        timeout=self.timeout, 
                        stream=True
                    )
                    
                # 检查响应状态码
                if response.status_code in [200, 206]:
                    self.log_message("请求成功，开始下载")
                    
                    # 通知请求成功
                    pause_monitor.update_progress(
                        url=self.chunk_info['url'],
                        thread_id=self.primary_thread_id,
                        stage=f"二级线程 {self.secondary_thread_id} 请求成功，准备开始下载"
                    )
                    
                    self._start_download()
                    break
                else:
                    error_msg = f"请求返回错误状态码: {response.status_code}"
                    raise Exception(error_msg)
                    
            except Exception as e:
                self.retry_count += 1
                error_msg = str(e)
                self.log_message(f"请求失败: {error_msg}")
                
                # 通知请求失败
                pause_monitor.update_progress(
                    url=self.chunk_info['url'],
                    thread_id=self.primary_thread_id,
                    stage=f"二级线程 {self.secondary_thread_id} 请求失败: {error_msg}"
                )
                
                if self.retry_count < self.max_retries:
                    self.log_message(f"等待重试 (第 {self.retry_count} 次)")
                    
                    # 通知准备重试
                    pause_monitor.update_progress(
                        url=self.chunk_info['url'],
                        thread_id=self.primary_thread_id,
                        stage=f"二级线程 {self.secondary_thread_id} 准备第 {self.retry_count} 次重试"
                    )
                    
                    time.sleep(1)  # 等待1秒后重试
                else:
                    self.log_message("请求失败，已达到最大重试次数")
                    
                    # 通知达到最大重试次数
                    pause_monitor.update_progress(
                        url=self.chunk_info['url'],
                        thread_id=self.primary_thread_id,
                        stage=f"二级线程 {self.secondary_thread_id} 请求失败，已达到最大重试次数"
                    )
                    
    def _start_download(self):
        """启动下载"""
        
        install = SecondaryThreadInstall(
            primary_thread_id=self.primary_thread_id,
            secondary_thread_id=self.secondary_thread_id,
            chunk_info=self.chunk_info,
            temp_dir=self.temp_dir,
            download_mode=self.download_mode
        )
        install.start()
>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
