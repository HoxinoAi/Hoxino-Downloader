<<<<<<< HEAD
import os
import requests
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox
from download.util.Settings_util import SettingsUtil
from PyQt6.QtCore import QObject, pyqtSignal
from queuemanagement.queuemanagement import DatabaseManager

# 使用相同的信号发射器
from download.v4.proxy_size_retrieval import error_emitter

class RegularSizeRetrieval:
    def __init__(self, thread_id: int, file_name: str):
        self.thread_id = thread_id
        self.file_name = file_name
        self.settings = SettingsUtil()
        self.db_manager = DatabaseManager()
        self.log_path = os.path.join("data", "log", "First_level_process", f"{thread_id}.txt")
        self.retry_count = 0
        self.max_retries = 2
        self.timeout = 4
        
        # 记录初始化日志
        self.log_message(f"初始化 RegularSizeRetrieval - 线程ID: {thread_id}, 文件名: {file_name}")

    def log_message(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    def retrieve(self, url: str):
        try:
            # 记录开始检索日志
            self.log_message(f"开始检索文件大小 - URL: {url}, 文件名: {self.file_name}")
            
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
                    self.log_message(f"尝试获取文件大小 (HEAD请求, 重试次数: {self.retry_count})")
                    response = requests.head(url, headers=headers, timeout=self.timeout, allow_redirects=True)
                    
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
                    self.log_message(f"请求失败: {str(e)}")
                    self.retry_count += 1
                    if self.retry_count <= self.max_retries:
                        continue
                    self._handle_failure(url, str(e))
                    return

            # 如果所有重试都失败了
            self._handle_failure(url, "无法获取文件大小")

        except Exception as e:
            self._handle_failure(url, str(e))

    def _handle_failure(self, url: str, error_reason: str):
        """处理获取文件大小失败的情况"""
        self.log_message(f"获取文件大小失败: {error_reason}")
        
        try:
            # 添加错误记录
            self.db_manager.add_error_task(
                url=url,
                file_name=self.file_name,  # 使用保存的文件名
                error_msg=f"获取文件大小失败: {error_reason}",
                sign='v4'
            )
            
            # 从downloading队列中移除
            self.db_manager.remove_downloading_task(url)
            
            # 转移等待队列中的第一个URL到下载队列
            self.db_manager.move_next_waiting_to_downloading()
        except Exception as e:
            self.log_message(f"处理错误时发生异常: {str(e)}")

    def _call_determination_of_threaquantity(self, url: str, file_size: int):
        """调用线程数量确定函数"""
        try:
            self.log_message(f"开始调用线程数量确定函数 - thread_id: {self.thread_id}")
            from download.v5.thread_determination import ThreadDetermination
            thread_determination = ThreadDetermination(
                thread_id=self.thread_id,
                url=url,
                file_name=self.file_name,  # 使用保存的文件名
                file_size=file_size
            )
            thread_determination.determine()
        except Exception as e:
            self.log_message(f"调用线程数量确定函数失败: {str(e)}")
            raise

    def _update_file_size_in_downloading(self, url: str, file_size: int):
        """更新downloading表中的文件大小"""
        try:
            if self.db_manager.update_file_size(url, self.thread_id, file_size):
                self.log_message(f"已更新文件大小到数据库: {file_size} bytes")
            else:
                self.log_message("更新文件大小失败：未找到匹配的任务")
        except Exception as e:
            self.log_message(f"更新文件大小失败: {str(e)}")
            raise

    @staticmethod
    def _show_error_dialog(title: str, message: str):
        """在主线程中显示错误对话框"""
        QMessageBox.warning(None, title, message)

=======
import os
import json
import requests
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox
from download.util.Settings_util import SettingsUtil
from PyQt6.QtCore import QObject, pyqtSignal
from playwright.sync_api import sync_playwright

# 使用相同的信号发射器
from download.v4.proxy_size_retrieval import error_emitter

class RegularSizeRetrieval:
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

        # 连接信号到主线程的处理函数
        error_emitter.error_signal.connect(self._show_error_dialog)

    def log_message(self, message: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    def _get_base_url(self, url: str) -> str:
        """从下载 URL 中提取官网地址"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return f"{parsed.scheme}://{parsed.netloc}"
        except Exception as e:
            self.log_message(f"提取官网地址失败: {str(e)}")
            return None

    def retrieve(self, url: str):
        try:
            # 通知开始获取文件大小
            from download.Pausemonitoring.Pause_monitoring import pause_monitor
            pause_monitor.update_progress(
                url=url,
                thread_id=self.thread_id,
                stage="开始获取文件大小"
            )

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
                    self.log_message(f"尝试获取文件大小 (HEAD请求, 重试次数: {self.retry_count})")
                    response = requests.head(url, headers=headers, timeout=self.timeout, allow_redirects=True)
                    
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
                    self.log_message(f"请求失败: {str(e)}")
                    self.retry_count += 1
                    if self.retry_count <= self.max_retries:
                        continue
                    self._handle_failure(url, str(e))
                    return

            # 如果所有重试都失败了
            self._handle_failure(url, "无法获取文件大小")

        except Exception as e:
            self._handle_failure(url, str(e))

    def _log_response(self, response_text: str):
        """记录响应内容到日志中"""
        self.log_message("-" * 50)  # 开始分隔线
        self.log_message(response_text)  # 记录响应内容
        self.log_message("-" * 50)  # 结束分隔线

    def _update_status_bar(self):
        # TODO: 更新UI状态栏显示重试次数
        pass

    def _handle_failure(self, url: str, error_reason: str):
        self.log_message(f"获取文件大小失败: {error_reason}")
        
        # 通知获取失败
        from download.Pausemonitoring.Pause_monitoring import pause_monitor
        pause_monitor.update_progress(
            url=url,
            thread_id=self.thread_id,
            stage=f"常规方式获取文件大小失败: {error_reason}"
        )
        
        # 添加到错误队列
        error_data = {
            "url": url,
            "error": f"获取文件大小失败: {error_reason}",
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
        
        # 使用信号发射错误消息到主线程
       
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

    @staticmethod
    def _show_error_dialog(title: str, message: str):
        """在主线程中显示错误对话框"""
        QMessageBox.warning(None, title, message)

>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
    