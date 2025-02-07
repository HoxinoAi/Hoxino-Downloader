import os
import json
import requests
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox
from download.util.Settings_util import SettingsUtil
from PyQt6.QtCore import QObject, pyqtSignal

# 创建一个信号发射器类
class ErrorSignalEmitter(QObject):
    error_signal = pyqtSignal(str, str)  # 参数：标题，消息

# 创建一个全局的信号发射器实例
error_emitter = ErrorSignalEmitter()

class ProxySizeRetrieval:
    def __init__(self, thread_id: int):
        self.thread_id = thread_id
        self.settings = SettingsUtil()
        self.log_path = os.path.join("data", "log", "First_level_process", f"{thread_id}.txt")
        self.error_queue_path = os.path.join("data", "queuemanagement", "error.json")
        self.waiting_path = os.path.join("data", "queuemanagement", "waiting.json")
        self.downloading_path = os.path.join("data", "queuemanagement", "downloading.json")
        self.retry_count = 0
        self.max_retries = 2
        self.timeout = 4

    def log_message(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    def retrieve(self, url: str):
        try:
            # 通知开始获取文件大小
            from download.Pausemonitoring.Pause_monitoring import pause_monitor
            pause_monitor.update_progress(
                url=url,
                thread_id=self.thread_id,
                stage="开始通过代理获取文件大小"
            )

            # 代理配置
            proxy_config = self.settings.get_proxy_config()
            proxies = {
                'http': f'http://{proxy_config["host"]}:{proxy_config["port"]}',
                'https': f'http://{proxy_config["host"]}:{proxy_config["port"]}'
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Pragma': 'no-cache',
                'Cache-Control': 'no-cache',
            }

            self.retry_count = 0
            while self.retry_count <= self.max_retries:
                try:
                    self.log_message(f"尝试获取文件大小 (HEAD请求通过代理, 重试次数: {self.retry_count})")
                    response = requests.head(
                        url, 
                        headers=headers, 
                        proxies=proxies,
                        timeout=self.timeout,
                        allow_redirects=True
                    )
                    
                    self.log_message(f"响应状态码: {response.status_code}")
                    self.log_message(f"响应头: {dict(response.headers)}")
                    
                    # 检查是否获取到正确的文件大小
                    content_length = response.headers.get('content-length')
                    if content_length:
                        try:
                            file_size = int(content_length)
                            self.log_message(f"从响应头获取到文件大小: {file_size}")
                            self._update_file_size_in_downloading(url, file_size)
                            self._call_determination_of_threaquantity(url, file_size)
                            return
                        except ValueError:
                            self.log_message("无法解析Content-Length值")
                    
                    self.retry_count += 1
                    
                except requests.exceptions.RequestException as e:
                    self.log_message(f"代理请求失败: {str(e)}")
                    self.retry_count += 1
                    if self.retry_count <= self.max_retries:
                        continue
                    self._handle_failure(url, str(e))
                    return

            # 如果所有重试都失败了
            self._handle_failure(url, "无法通过代理获取文件大小")

        except Exception as e:
            self._handle_failure(url, str(e))

    def _handle_failure(self, url: str, error_reason: str):
        self.log_message(f"获取文件大小失败: {error_reason}")
        
        # 通知获取失败
        from download.Pausemonitoring.Pause_monitoring import pause_monitor
        pause_monitor.update_progress(
            url=url,
            thread_id=self.thread_id,
            stage=f"代理方式获取文件大小失败: {error_reason}"
        )
        
        # 添加到错误队列
        error_data = {
            "url": url,
            "error": "代理服务器故障，请检查代理，或许是资源不允许代理",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(self.error_queue_path, 'r+', encoding='utf-8') as f:
            error_queue = json.load(f)
            error_queue.append(error_data)
            f.seek(0)
            json.dump(error_queue, f, ensure_ascii=False, indent=4)

        # 从downloading队列中移除
        self._remove_from_downloading(url)
        
        # 转移等待队列中的第一个URL到下载队列
        self._move_next_waiting_to_downloading()
        
        # 直接发送错误信号，不需要连接到本地方法
       

    def _call_determination_of_threaquantity(self, url: str, file_size: int):
        """调用线程数量确定函数"""
        try:
            self.log_message(f"开始调用线程数量确定函数 - thread_id: {self.thread_id}")
            from download.v5.thread_determination import ThreadDetermination
            thread_determination = ThreadDetermination(
                thread_id=self.thread_id,  # 确保正确传递thread_id
                url=url,
                file_size=file_size
            )
            thread_determination.determine()
        except Exception as e:
            self.log_message(f"调用线程数量确定函数失败: {str(e)}")
            raise

    def _remove_from_downloading(self, url: str):
        with open(self.downloading_path, 'r', encoding='utf-8') as f:
            downloading = json.load(f)
        downloading = [task for task in downloading if task['url'] != url]
        with open(self.downloading_path, 'w', encoding='utf-8') as f:
            json.dump(downloading, f, ensure_ascii=False, indent=4)

    def _move_next_waiting_to_downloading(self):
        with open(self.waiting_path, 'r', encoding='utf-8') as f:
            waiting = json.load(f)
        
        if waiting:
            next_task = waiting.pop(0)
            next_task['status'] = "下载中"
            
            with open(self.waiting_path, 'w', encoding='utf-8') as f:
                json.dump(waiting, f, ensure_ascii=False, indent=4)
                
            with open(self.downloading_path, 'r+', encoding='utf-8') as f:
                downloading = json.load(f)
                downloading.append(next_task)
                f.seek(0)
                json.dump(downloading, f, ensure_ascii=False, indent=4)

    def _update_file_size_in_downloading(self, url: str, file_size: int):
        """更新downloading.json中的文件大小"""
        try:
            with open(self.downloading_path, 'r', encoding='utf-8') as f:
                downloading = json.load(f)
                
            # 获取当前任务的文件名
            current_filename = None
            for task in downloading:
                if task['url'] == url and task['thread_id'] == self.thread_id:
                    current_filename = task.get('file_name')
                    break
                    
            if not current_filename:
                self.log_message("无法找到对应的文件名")
                return
                
            # 找到匹配URL和文件名的任务并更新文件大小
            updated = False
            for task in downloading:
                if (task['url'] == url and 
                    task.get('file_name') == current_filename and 
                    task['thread_id'] == self.thread_id):
                    task['size'] = file_size
                    self.log_message(f"已更新文件大小到downloading.json: {file_size} bytes (文件名: {current_filename})")
                    updated = True
                    break
                    
            if not updated:
                self.log_message(f"未找到匹配的下载任务 (URL: {url}, 文件名: {current_filename})")
                return
                
            with open(self.downloading_path, 'w', encoding='utf-8') as f:
                json.dump(downloading, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            self.log_message(f"更新文件大小失败: {str(e)}")
