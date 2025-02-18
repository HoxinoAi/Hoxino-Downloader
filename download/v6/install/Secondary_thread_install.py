<<<<<<< HEAD
import os
import time
import requests
import json
import hashlib
from typing import Dict
from download.util.Settings_util import SettingsUtil
from queuemanagement.queuemanagement import DatabaseManager
import multiprocessing
from multiprocessing import Manager
import signal
import sys

class SecondaryThreadInstall:
    # 类级别的共享事件字典，用于存储每个文件的终止事件
    terminate_events = {}

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
        self.progress_timeout = 10
        self.last_progress_time = time.time()
        
        # 设置日志路径
        self.log_dir = os.path.join("data", "log", "Second_level_process", str(primary_thread_id))
        self.log_path = os.path.join(self.log_dir, f"{secondary_thread_id}.txt")
        
        # 确保日志目录存在并清理旧日志
        self._ensure_log_directory()
        self._clean_old_log()
        
        # 设置下载文件路径
        self.install_temp_dir = os.path.join("data", "installtemp", str(file_name))
        os.makedirs(self.install_temp_dir, exist_ok=True)
        self.chunk_file_path = os.path.join(self.install_temp_dir, f"chunk_{secondary_thread_id}")
        self.paused_chunk_file_path = os.path.join(self.install_temp_dir, f"chunk_{secondary_thread_id}_pausing")
        
        # 记录当前下载的大小
        self.current_downloaded_size = 0
        
        # 设置状态文件路径
        
        # 获取或创建共享终止事件
        if self.file_name not in self.terminate_events:
            self.terminate_events[self.file_name] = multiprocessing.Event()
        self.terminate_event = self.terminate_events[self.file_name]
        
    def _ensure_log_directory(self):
        """确保日志目录存在"""
        os.makedirs(self.log_dir, exist_ok=True)

    def _clean_old_log(self):
        """清理旧的日志文件"""

        if os.path.exists(self.log_path):
                os.remove(self.log_path)
                self.log_message(f"已清理旧日志文件: {self.log_path}")

        
    def log_message(self, message: str):
        """写入日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
            
    def update_progress(self, downloaded_size: int):
        """更新下载进度"""
        try:
            # 修正进度计算
            total_downloaded = downloaded_size  # 当前已下载的大小
            chunk_total_size = self.chunk_info["size"]  # 当前分片的总大小
            
            # 计算进度
            progress = round((total_downloaded / chunk_total_size) * 100, 2)
            self.last_progress_time = time.time()
            self.current_downloaded_size = downloaded_size
            
            
            # 只更新UI，不保存状态
            from download.v6.Secondary_thread.DownloadConfig import DownloadConfig
            progress_tracker = DownloadConfig.progress_instances.get(self.file_name)
            if progress_tracker:
                progress_tracker.update_progress(
                    secondary_thread_id=self.secondary_thread_id,
                    progress=progress,
                    chunk_size=self.chunk_info["size"]
                )
            
        except Exception as e:
            self.log_message(f"更新进度失败: {str(e)}")
            import traceback
            self.log_message(traceback.format_exc())
        
    def _get_headers(self) -> dict:
        """根据文件类型获取请求头"""
        url = self.chunk_info['url']
        file_extension = os.path.splitext(url)[1].lower()
        
        # 基础请求头
        headers = {
            'Range': f'bytes={self.chunk_info["start"]}-{self.chunk_info["end"]}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        
        # 根据文件类型设置Accept
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
            headers['Accept'] = 'image/webp,image/apng,image/*,*/*;q=0.8'
        elif file_extension in ['.mp4', '.avi', '.mkv', '.mov']:
            headers['Accept'] = 'video/*,*/*;q=0.8'
        elif file_extension in ['.mp3', '.wav', '.flac', '.aac']:
            headers['Accept'] = 'audio/*,*/*;q=0.8'
        elif file_extension in ['.pdf']:
            headers['Accept'] = 'application/pdf,*/*;q=0.8'
        elif file_extension in ['.doc', '.docx']:
            headers['Accept'] = 'application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,*/*;q=0.8'
        elif file_extension in ['.zip', '.rar', '.7z']:
            headers['Accept'] = 'application/zip,application/x-rar-compressed,application/x-7z-compressed,*/*;q=0.8'
        else:
            # 默认接受所有类型
            headers['Accept'] = '*/*'
        
        return headers

    def _check_terminate_flag(self) -> bool:
        """检查是否需要终止下载"""
        try:
            db_manager = DatabaseManager()
            return db_manager.check_downloading_status(self.file_name)
        except Exception as e:
            self.log_message(f"检查终止标志失败: {str(e)}")
            import traceback
            self.log_message(traceback.format_exc())
            return False

  

    def verify_file_integrity(self, file_path: str) -> bool:
        """
        验证下载文件的完整性
        返回: bool, True 表示文件完整，False 表示文件损坏
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.log_message(f"文件不存在: {file_path}")
                return False
                
            # 检查文件大小
            actual_size = os.path.getsize(file_path)
            expected_size = self.chunk_info["size"]
            
            if actual_size != expected_size:
                self.log_message(f"文件大小不匹配:")
                self.log_message(f"预期大小: {expected_size} 字节")
                self.log_message(f"实际大小: {actual_size} 字节")
                self.log_message(f"差异: {actual_size - expected_size} 字节")
                self.log_message(f"分片起始位置: {self.chunk_info['start']}")
                self.log_message(f"分片结束位置: {self.chunk_info['end']}")
                return False
                
            # 计算文件的MD5值
            md5_hash = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    md5_hash.update(chunk)
            file_hash = md5_hash.hexdigest()
            
            # 如果chunk_info中有MD5值，则进行比对
            if "md5" in self.chunk_info:
                expected_hash = self.chunk_info["md5"]
                if file_hash != expected_hash:
                    self.log_message(f"文件MD5不匹配: 预期 {expected_hash}, 实际 {file_hash}")
                    return False
            
            self.log_message("文件完整性验证通过")
            return True
            
        except Exception as e:
            self.log_message(f"文件完整性验证失败: {str(e)}")
            return False

    def start(self):
        try:
            current_position = 0
            db_manager = DatabaseManager()
            
            # 检查是否存在暂停的文件
            if os.path.exists(self.paused_chunk_file_path):
                try:
                    downloaded_size = os.path.getsize(self.paused_chunk_file_path)
                    # 记录续传信息
                    self.log_message("=" * 50)
                    self.log_message(f"分片{self.secondary_thread_id}续传检查:")
                    self.log_message(f"起始位置: {self.chunk_info['start']}")
                    self.log_message(f"已下载: {downloaded_size}")
                    self.log_message(f"分片大小: {self.chunk_info['size']}")
                    self.log_message(f"分片结束位置: {self.chunk_info['end']}")
                    
                    if downloaded_size > 0 and downloaded_size <= self.chunk_info["size"]:
                        # 重命名文件，移除暂停标记
                        os.rename(self.paused_chunk_file_path, self.chunk_file_path)
                        current_position = self.chunk_info["start"] + downloaded_size
                        self.current_downloaded_size = downloaded_size
                        self.log_message(f"续传位置: {current_position}")
                    else:
                        self.log_message("文件大小异常，将重新下载")
                        os.remove(self.paused_chunk_file_path)
                        current_position = self.chunk_info["start"]
                        self.current_downloaded_size = 0
                    
                    self.log_message("=" * 50)
                except Exception as e:
                    self.log_message(f"处理暂停文件时出错: {str(e)}")
                    if os.path.exists(self.paused_chunk_file_path):
                        os.remove(self.paused_chunk_file_path)
                    current_position = self.chunk_info["start"]
                    self.current_downloaded_size = 0
            else:
                # 新下载或清理后的重新下载
                if os.path.exists(self.chunk_file_path):
                    os.remove(self.chunk_file_path)
                current_position = self.chunk_info["start"]
                self.current_downloaded_size = 0

            while self.retry_count < self.max_retries:
                try:
                    # 每次循环都检查暂停状态
                    if db_manager.check_downloading_status(self.file_name):
                        self.log_message("检测到暂停状态，停止下载")
                        # 如果存在正在下载的文件，重命名为暂停状态
                        if os.path.exists(self.chunk_file_path):
                            try:
                                os.rename(self.chunk_file_path, self.paused_chunk_file_path)
                                self.log_message(f"已将文件重命名为暂停状态: {self.paused_chunk_file_path}")
                            except Exception as e:
                                self.log_message(f"重命名文件失败: {str(e)}")
                        # 保存当前下载状态
                        return False
                    
                    headers = self._get_headers()
                    if current_position > 0:
                        headers['Range'] = f'bytes={current_position}-{self.chunk_info["end"]}'
                    
                    # 发送请求
                    if self.download_mode == "proxy":
                        proxy_config = self.settings.get_proxy_config()
                        proxies = {
                            'http': f'http://{proxy_config["host"]}:{proxy_config["port"]}',
                            'https': f'http://{proxy_config["host"]}:{proxy_config["port"]}'
                        }
                        response = requests.get(
                            self.chunk_info['url'],
                            headers=headers,
                            stream=True,
                            proxies=proxies,
                            timeout=30
                        )
                    else:
                        response = requests.get(
                            self.chunk_info['url'],
                            headers=headers,
                            stream=True,
                            timeout=30
                        )
                    
                    response.raise_for_status()
                    
                    # 打开临时文件
                    with open(self.chunk_file_path, 'ab' if current_position > 0 else 'wb') as f:
                        if current_position > 0:
                            f.seek(current_position)
                        
                        for chunk in response.iter_content(chunk_size=8192):
                            # 每次写入数据前检查暂停状态
                            if db_manager.check_downloading_status(self.file_name):
                                self.log_message("检测到暂停状态，停止下载")
                                try:
                                    # 关闭文件句柄
                                    f.close()
                                    # 重命名为暂停状态
                                    os.rename(self.chunk_file_path, self.paused_chunk_file_path)
                                    self.log_message(f"已将文件重命名为暂停状态: {self.paused_chunk_file_path}")
                                except Exception as e:
                                    self.log_message(f"重命名文件失败: {str(e)}")

                                return False
                                
                            if chunk:
                                f.write(chunk)
                                self.current_downloaded_size += len(chunk)
                                self.update_progress(self.current_downloaded_size)
                    
                    # 验证文件完整性
                    if self.verify_file_integrity(self.chunk_file_path):
                        self.log_message("分片下载完成且验证通过")
                        self._notify_merge()
                        return True
                    
                    return False
                    
                except Exception as e:
                    self.retry_count += 1
                    self.log_message(f"下载失败 (重试 {self.retry_count}/{self.max_retries}): {str(e)}")
                    if self.retry_count >= self.max_retries:
                        raise
                    time.sleep(1)
                
        except Exception as e:
            self.log_message(f"下载过程出错: {str(e)}")
            raise

    def _notify_merge(self):
        """通知合并类下载完成"""
        try:
            from download.v6.Secondary_thread.DownloadConfig import DownloadConfig
            # 获取对应的Merge实例
            merge = DownloadConfig.merge_instances.get(self.primary_thread_id)
            if merge:
                # 发送当前二级线程ID到合并类的信号队列
                merge.signal_queue.put(self.secondary_thread_id)
                self.log_message(f"已发送完成信号到合并监控，二级线程ID: {self.secondary_thread_id}")
            else:
                self.log_message("错误：未找到合并监控实例")
        except Exception as e:
            self.log_message(f"发送合并信号失败: {str(e)}")

    def _handle_max_retries(self, error_message: str):
        """处理达到最大重试次数的情况"""
        try:
            db_manager = DatabaseManager()
            
            # 从downloading表中移除任务
            if db_manager.remove_downloading_task(self.chunk_info['url']):
                self.log_message("已从下载列表移除任务")
                
                # 添加到错误表
                if db_manager.add_error_task(
                    url=self.chunk_info['url'],
                    file_name=self.chunk_info.get('file_name', 'unknown'),
                    error_msg=f"达到最大重试次数({self.max_retries})：{error_message}",
                    sign='v6'
                ):
                    self.log_message(f"已将任务添加到错误列表: {self.chunk_info['url']}")
                else:
                    self.log_message("添加到错误列表失败")
            else:
                self.log_message("从下载列表移除任务失败")
                
        except Exception as e:
            self.log_message(f"处理错误任务时出错: {str(e)}")

  
=======
import os
import time
import requests
import json
import hashlib
from typing import Dict
from download.util.Settings_util import SettingsUtil

class SecondaryThreadInstall:
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
        self.progress_timeout = 10  # 10秒无进度更新视为超时
        self.last_progress_time = time.time()
        
        # 设置日志路径
        self.log_dir = os.path.join("data", "log", "Second_level_process", str(primary_thread_id))
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, f"{secondary_thread_id}.txt")
        
        # 设置下载文件路径
        self.install_temp_dir = os.path.join("data", "installtemp", str(primary_thread_id))
        os.makedirs(self.install_temp_dir, exist_ok=True)
        self.chunk_file_path = os.path.join(self.install_temp_dir, f"chunk_{secondary_thread_id}")
        
        # 添加暂停相关属性
        self.pause_flag = False
        self.resume_position = 0  # 续传位置
        
    def log_message(self, message: str):
        """写入日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
            
    def update_progress(self, downloaded_size: int):
        """更新下载进度"""
        progress = (downloaded_size / self.chunk_info["size"]) * 100
        self.last_progress_time = time.time()
        
        # 发送进度到progress类
        from download.v6.progress.progress import Progress
        progress_tracker = Progress(self.primary_thread_id)
        progress_tracker.update_progress(self.secondary_thread_id, progress)
        
    def _get_headers(self) -> dict:
        """根据文件类型获取请求头"""
        url = self.chunk_info['url']
        file_extension = os.path.splitext(url)[1].lower()
        
        # 基础请求头
        headers = {
            'Range': f'bytes={self.chunk_info["start"]}-{self.chunk_info["end"]}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        
        # 根据文件类型设置Accept
        if file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
            headers['Accept'] = 'image/webp,image/apng,image/*,*/*;q=0.8'
        elif file_extension in ['.mp4', '.avi', '.mkv', '.mov']:
            headers['Accept'] = 'video/*,*/*;q=0.8'
        elif file_extension in ['.mp3', '.wav', '.flac', '.aac']:
            headers['Accept'] = 'audio/*,*/*;q=0.8'
        elif file_extension in ['.pdf']:
            headers['Accept'] = 'application/pdf,*/*;q=0.8'
        elif file_extension in ['.doc', '.docx']:
            headers['Accept'] = 'application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,*/*;q=0.8'
        elif file_extension in ['.zip', '.rar', '.7z']:
            headers['Accept'] = 'application/zip,application/x-rar-compressed,application/x-7z-compressed,*/*;q=0.8'
        else:
            # 默认接受所有类型
            headers['Accept'] = '*/*'
        
        return headers

    def check_pause_status(self) -> bool:
        """检查是否需要暂停下载"""
        try:
            pause_record_path = os.path.join("data", "pause_record", "pause_status.json")
            if os.path.exists(pause_record_path):
                with open(pause_record_path, 'r', encoding='utf-8') as f:
                    pause_records = json.load(f)
                    if str(self.primary_thread_id) in pause_records:
                        return True
            return False
        except Exception as e:
            self.log_message(f"检查暂停状态失败: {str(e)}")
            return False

    def save_download_state(self, downloaded_size: int):
        """保存下载状态，用于续传"""
        try:
            state_dir = os.path.join("data", "download_state", str(self.primary_thread_id))
            os.makedirs(state_dir, exist_ok=True)
            state_file = os.path.join(state_dir, f"chunk_{self.secondary_thread_id}.json")
            
            state = {
                'downloaded_size': downloaded_size,
                'chunk_start': self.chunk_info["start"],
                'chunk_end': self.chunk_info["end"],
                'url': self.chunk_info["url"],
                'timestamp': time.time()
            }
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=4)
                
            self.log_message(f"保存下载状态: 已下载 {downloaded_size} 字节")
            
        except Exception as e:
            self.log_message(f"保存下载状态失败: {str(e)}")

    def verify_file_integrity(self, file_path: str) -> bool:
        """
        验证下载文件的完整性
        返回: bool, True 表示文件完整，False 表示文件损坏
        """
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                self.log_message(f"文件不存在: {file_path}")
                return False
                
            # 检查文件大小
            actual_size = os.path.getsize(file_path)
            expected_size = self.chunk_info["size"]
            
            if actual_size != expected_size:
                self.log_message(f"文件大小不匹配: 预期 {expected_size} 字节, 实际 {actual_size} 字节")
                return False
                
            # 计算文件的MD5值
            md5_hash = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    md5_hash.update(chunk)
            file_hash = md5_hash.hexdigest()
            
            # 如果chunk_info中有MD5值，则进行比对
            if "md5" in self.chunk_info:
                expected_hash = self.chunk_info["md5"]
                if file_hash != expected_hash:
                    self.log_message(f"文件MD5不匹配: 预期 {expected_hash}, 实际 {file_hash}")
                    return False
            
            self.log_message("文件完整性验证通过")
            return True
            
        except Exception as e:
            self.log_message(f"文件完整性验证失败: {str(e)}")
            return False

    def start(self):
        """开始下载"""
        from download.Pausemonitoring.Pause_monitoring import pause_monitor
        
        # 初始化下载位置
        current_position = 0
        
        while self.retry_count < self.max_retries:
            try:
                # 检查是否有之前的下载进度
                state_dir = os.path.join("data", "download_state", str(self.primary_thread_id))
                state_file = os.path.join(state_dir, f"chunk_{self.secondary_thread_id}.json")
                
                if os.path.exists(state_file):
                    try:
                        with open(state_file, 'r', encoding='utf-8') as f:
                            state = json.load(f)
                            current_position = state.get('downloaded_size', 0)
                            self.log_message(f"找到之前的下载进度: {current_position} 字节")
                    except Exception as e:
                        self.log_message(f"读取下载状态失败: {str(e)}")
                        current_position = 0
                
                # 更新请求头的Range
                headers = self._get_headers()
                if current_position > 0:
                    headers['Range'] = f'bytes={self.chunk_info["start"] + current_position}-{self.chunk_info["end"]}'
                    self.log_message(f"从位置 {current_position} 继续下载")
                    
                    # 通知继续下载
                    pause_monitor.update_progress(
                        url=self.chunk_info['url'],
                        thread_id=self.primary_thread_id,
                        stage=f"二级线程 {self.secondary_thread_id} 继续下载，已下载: {current_position} 字节"
                    )
                
                # 发送请求
                if self.download_mode == "proxy":
                    proxy_config = self.settings.get_proxy_config()
                    proxies = {
                        'http': f'http://{proxy_config["host"]}:{proxy_config["port"]}',
                        'https': f'http://{proxy_config["host"]}:{proxy_config["port"]}'
                    }
                    response = requests.get(
                        self.chunk_info['url'],
                        headers=headers,
                        proxies=proxies,
                        stream=True
                    )
                else:
                    response = requests.get(
                        self.chunk_info['url'],
                        headers=headers,
                        stream=True
                    )
                
                if response.status_code in [200, 206]:
                    # 以追加模式打开文件
                    mode = 'ab' if current_position > 0 else 'wb'
                    with open(self.chunk_file_path, mode) as f:
                        downloaded_size = current_position
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                # 检查暂停信号
                                if self.check_pause_status():
                                    self.log_message("检测到暂停信号")
                                    self.save_download_state(downloaded_size)
                                    pause_monitor.update_progress(
                                        url=self.chunk_info['url'],
                                        thread_id=self.primary_thread_id,
                                        stage=f"二级线程 {self.secondary_thread_id} 已暂停，已下载: {downloaded_size} 字节"
                                    )
                                    return
                                
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                
                                # 更新进度
                                current_time = time.time()
                                if current_time - self.last_progress_time >= 3:
                                    self.update_progress(downloaded_size)
                                    self.last_progress_time = current_time
                                    
                                    # 保存当前状态用于断点续传
                                    self.save_download_state(downloaded_size)
                                    
                                    # 通知下载进度
                                    progress_percentage = (downloaded_size / self.chunk_info["size"]) * 100
                                    pause_monitor.update_progress(
                                        url=self.chunk_info['url'],
                                        thread_id=self.primary_thread_id,
                                        stage=f"二级线程 {self.secondary_thread_id} 下载进度: {progress_percentage:.2f}%"
                                    )
                                
                                # 检查进度超时
                                if current_time - self.last_progress_time > self.progress_timeout:
                                    raise Exception("下载进度超时")
                    
                    # 下载完成后进行完整性检查
                    if self.verify_file_integrity(self.chunk_file_path):
                        self.log_message("下载完成且文件完整性验证通过")
                        self.update_progress(downloaded_size)
                        
                        # 删除状态文件
                        if os.path.exists(state_file):
                            os.remove(state_file)
                            self.log_message("已删除下载状态文件")
                        
                        # 通知下载完成
                        pause_monitor.update_progress(
                            url=self.chunk_info['url'],
                            thread_id=self.primary_thread_id,
                            stage=f"二级线程 {self.secondary_thread_id} 下载完成且验证通过"
                        )
                        
                        self._notify_merge()
                        break
                    else:
                        self.log_message("文件完整性验证失败，准备重试下载")
                        # 保存当前进度
                        self.save_download_state(downloaded_size)
                        self.retry_count += 1
                        if self.retry_count < self.max_retries:
                            time.sleep(1)
                            continue
                        else:
                            raise Exception("文件完整性验证失败且已达到最大重试次数")
                else:
                    raise Exception(f"下载返回错误状态码: {response.status_code}")
                
            except Exception as e:
                self.retry_count += 1
                self.log_message(f"下载失败，重试次数 {self.retry_count}/{self.max_retries}: {str(e)}")
                
                if self.retry_count >= self.max_retries:
                    self.log_message("达到最大重试次数，将任务移至错误列表")
                    self._handle_max_retries(str(e))
                    return
                
                # 保存当前进度用于下次重试
                if 'downloaded_size' in locals():
                    self.save_download_state(downloaded_size)
                
                time.sleep(2 ** self.retry_count)  # 指数退避
                continue

    def _notify_merge(self):
        """通知合并类下载完成"""
        try:
            from download.v6.Secondary_thread.DownloadConfig import DownloadConfig
            # 获取对应的Merge实例
            merge = DownloadConfig.merge_instances.get(self.primary_thread_id)
            if merge:
                merge.signal_queue.put(self.secondary_thread_id)
                self.log_message("已发送完成信号到合并监控")
            else:
                self.log_message("错误：未找到合并监控实例")
        except Exception as e:
            self.log_message(f"发送合并信号失败: {str(e)}")

    def _handle_max_retries(self, error_message: str):
        """处理达到最大重试次数的情况"""
        try:
            # 1. 从 downloading.json 中移除任务
            downloading_path = os.path.join("data", "queuemanagement", "downloading.json")
            error_path = os.path.join("data", "queuemanagement", "error.json")
            
            # 确保目录存在
            os.makedirs(os.path.dirname(error_path), exist_ok=True)
            
            # 读取当前下载列表
            with open(downloading_path, 'r', encoding='utf-8') as f:
                downloading_tasks = json.load(f)
            
            # 找到并移除当前任务
            updated_tasks = [
                task for task in downloading_tasks 
                if not (task.get('thread_id') == self.primary_thread_id and 
                       task.get('url') == self.chunk_info['url'])
            ]
            
            # 保存更新后的下载列表
            with open(downloading_path, 'w', encoding='utf-8') as f:
                json.dump(updated_tasks, f, ensure_ascii=False, indent=4)
            
            # 2. 添加到 error.json
            error_entry = {
                "url": self.chunk_info['url'],
                "error": f"达到最大重试次数({self.max_retries})：{error_message}",
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "thread_id": self.primary_thread_id
            }
            
            # 读取现有的错误列表
            try:
                with open(error_path, 'r', encoding='utf-8') as f:
                    error_list = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                error_list = []
            
            # 确保error_list是列表类型
            if not isinstance(error_list, list):
                error_list = []
            
            # 添加新的错误记录
            error_list.append(error_entry)
            
            # 保存更新后的错误列表
            with open(error_path, 'w', encoding='utf-8') as f:
                json.dump(error_list, f, ensure_ascii=False, indent=4)
            
            self.log_message(f"已将任务添加到错误列表: {self.chunk_info['url']}")
            
        
            
        except Exception as e:
            self.log_message(f"处理错误任务时出错: {str(e)}")
>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
