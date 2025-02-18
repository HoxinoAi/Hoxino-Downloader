<<<<<<< HEAD
import os
import json
import math
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox
from download.util.Settings_util import SettingsUtil
from download.v6.Secondary_thread.DownloadConfig import DownloadConfig
from download.v6.DynamicOptimization.thread_optimizer import ThreadOptimizer
from PyQt6.QtCore import Q_ARG
from queuemanagement.queuemanagement import DatabaseManager

class ThreadDetermination:
    def __init__(self, thread_id: int, url: str, file_name: str, file_size: int):
        self.thread_id = thread_id
        self.url = url
        self.file_name = file_name
        self.file_size = file_size
        self.settings = SettingsUtil()
        self.log_path = os.path.join("data", "log", "First_level_process", f"{thread_id}.txt")
        self.temp_dir = os.path.join("data", "temp", f"task_{thread_id}")
        
        # 添加日志记录
        self.log_message(f"ThreadDetermination 初始化 - thread_id: {thread_id}, url: {url}, file_name: {file_name}")

    def log_message(self, message: str):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    def determine(self):
        """确定线程数量并进行文件分片"""
        try:
            self.log_message(f"开始确定线程数量 - thread_id: {self.thread_id}, file_name: {self.file_name}")
            db_manager = DatabaseManager()
            
            # 首先获取已存在的分片信息
            existing_chunks = db_manager.get_chunks_by_filename(self.file_name)
            
            # 获取设置的线程数
            threads = self.settings.get_threads()
            
            if existing_chunks:
                chunk_count = len(existing_chunks)
                expected_threads = 0
                
                # 确定预期的线程数
                if isinstance(threads, str) and threads.lower() == "动态优化":
                    try:
                        optimizer = ThreadOptimizer()
                        expected_threads = optimizer.get_optimal_threads(self.thread_id, self.url)
                    except Exception as e:
                        self.log_message(f"获取动态优化线程数失败: {str(e)}")
                        expected_threads = 4  # 使用默认值
                else:
                    try:
                        expected_threads = int(threads)
                    except ValueError:
                        expected_threads = 4  # 使用默认值

                # 如果分片数量与预期线程数相同，直接使用现有分片
                if chunk_count == expected_threads:
                    self.log_message(f"使用现有分片信息，分片数: {chunk_count}")
                    self._write_thread_count(chunk_count)
                    self._configure_download()
                    return
                    
            # 如果没有分片信息或分片数量不匹配，执行原有逻辑
            self.log_message("执行新的线程分配逻辑")
            try:
                if isinstance(threads, str) and threads.lower() == "动态优化":
                    self.log_message("使用动态优化模式")
                    try:
                        optimizer = ThreadOptimizer()
                        optimized_threads = optimizer.get_optimal_threads(self.thread_id, self.url)
                        
                        if not isinstance(optimized_threads, int) or optimized_threads < 1:
                            error_msg = f"无效的线程数: {optimized_threads}"
                            db_manager.add_error_task(self.url, self.file_name, error_msg, 'v5')
                            raise ValueError(error_msg)
                        
                        self.log_message(f"动态优化计算得到线程数: {optimized_threads}")
                        self._write_thread_count(optimized_threads)
                        self._split_file(optimized_threads)
                        
                    except Exception as e:
                        error_msg = f"动态优化失败: {str(e)}"
                        db_manager.add_error_task(self.url, self.file_name, error_msg, 'v5')
                        self.log_message(error_msg)
                        # 使用默认值
                        self._write_thread_count(4)
                        self._split_file(4)
                        
                else:
                    try:
                        thread_count = int(threads)
                        if thread_count < 1 or thread_count > 32:
                            error_msg = "线程数必须在1-32之间"
                            db_manager.add_error_task(self.url, self.file_name, error_msg, 'v5')
                            raise ValueError(error_msg)
                            
                        self._write_thread_count(thread_count)
                        self._split_file(thread_count)
                        
                    except ValueError as e:
                        error_msg = f"无效的线程设置: {threads}，使用默认值4"
                        db_manager.add_error_task(self.url, self.file_name, error_msg, 'v5')
                        self.log_message(error_msg)
                        self._write_thread_count(4)
                        self._split_file(4)
                        
            except Exception as e:
                error_msg = f"线程确定过程出错: {str(e)}"
                db_manager.add_error_task(self.url, self.file_name, error_msg, 'v5')
                self.log_message(error_msg)
                # 使用默认值继续执行
                self._write_thread_count(4)
                self._split_file(4)

        except Exception as e:
            error_msg = f"determine方法异常: {str(e)}"
            db_manager = DatabaseManager()
            db_manager.add_error_task(self.url, self.file_name, error_msg, 'v5')
            self.log_message(error_msg)
            raise

    def _write_thread_count(self, thread_count: int):
        """写入线程数到数据库"""
        try:
            db_manager = DatabaseManager()
            if db_manager.update_thread_count(self.url, thread_count):
                self.log_message(f"成功写入线程数 {thread_count} 到数据库")
            else:
                error_msg = "写入线程数到数据库失败"
                self.log_message(error_msg)
                raise Exception(error_msg)
            
        except Exception as e:
            self.log_message(f"写入线程数过程中发生错误: {str(e)}")
            raise

    def _split_file(self, thread_count: int):
        """将文件分割为指定数量的分片"""
        try:
            self.log_message(f"开始将文件分割为 {thread_count} 个分片")
            db_manager = DatabaseManager()

            # 直接使用实例的 file_name
            file_name = self.file_name
            self.log_message(f"使用文件名: {file_name}")

            # 计算分片信息
            base_chunk_size = self.file_size // thread_count
            chunks_info = []

            for i in range(thread_count):
                start = i * base_chunk_size
                end = self.file_size - 1 if i == thread_count - 1 else (i + 1) * base_chunk_size - 1
                actual_size = end - start + 1
                
                chunk_info = {
                    "chunk_id": i,
                    "file_name": file_name,
                    "url": self.url,
                    "start": start,
                    "end": end,
                    "size": actual_size,
                    "status": "pending"
                }
                chunks_info.append(chunk_info)
                self.log_message(f"生成分片 {i}: 起始={start}, 结束={end}, 大小={actual_size}")

            # 验证总大小
            total_chunks_size = sum(chunk["size"] for chunk in chunks_info)
            if total_chunks_size != self.file_size:
                error_msg = f"分片总大小({total_chunks_size})与文件大小({self.file_size})不匹配"
                db_manager.add_error_task(self.url, self.file_name, error_msg, 'v5')
                raise Exception(error_msg)

            # 保存分片信息到数据库
            if not db_manager.save_chunk_info(file_name, chunks_info):  # 使用 save_chunk_info
                error_msg = "保存分片信息到数据库失败"
                db_manager.add_error_task(self.url, self.file_name, error_msg, 'v5')
                raise Exception(error_msg)

            self.log_message("分片信息已保存到数据库")
            self._configure_download()
            
        except Exception as e:
            error_msg = f"文件分片过程出错: {str(e)}"
            db_manager.add_error_task(self.url, self.file_name, error_msg, 'v5')
            self.log_message(error_msg)
            raise

    def _configure_download(self):
        """配置下载方式并启动下载"""
        try:
            db_manager = DatabaseManager()
            task = db_manager.get_task_by_thread_id(self.thread_id)
            if not task:
                error_msg = "无法获取任务信息"
                db_manager.add_error_task(self.url, self.file_name, error_msg, 'v5')
                raise Exception(error_msg)
            
            file_name = task.get('file_name')
            if not file_name:
                error_msg = "任务信息中缺少文件名"
                db_manager.add_error_task(self.url, self.file_name, error_msg, 'v5')
                raise Exception(error_msg)
            
            # 获取分片信息
            chunks = db_manager.get_chunks_by_filename(file_name)  # 使用 get_chunks_by_filename
            if not chunks:
                error_msg = f"无法获取文件 {file_name} 的分片信息"
                db_manager.add_error_task(self.url, self.file_name, error_msg, 'v5')
                raise Exception(error_msg)
            
            download_config = DownloadConfig(
                primary_thread_id=self.thread_id,
                temp_dir=self.temp_dir,
                file_name=self.file_name
            )
            
            self.log_message(f"下载配置完成，临时目录: {self.temp_dir}")
            
        except Exception as e:
            error_msg = f"配置下载时发生错误: {str(e)}"
            db_manager = DatabaseManager()
            db_manager.add_error_task(self.url, self.file_name, error_msg, 'v5')
            self.log_message(error_msg)
            raise
=======
import os
import json
import math
from datetime import datetime
from PyQt6.QtWidgets import QMessageBox
from download.util.Settings_util import SettingsUtil
from download.v6.Secondary_thread.DownloadConfig import DownloadConfig
from download.v6.DynamicOptimization.thread_optimizer import ThreadOptimizer
from PyQt6.QtCore import Q_ARG

class ThreadDetermination:
    def __init__(self, thread_id: int, url: str, file_size: int):
        self.thread_id = thread_id
        self.url = url
        self.file_size = file_size
        self.settings = SettingsUtil()
        self.log_path = os.path.join("data", "log", "First_level_process", f"{thread_id}.txt")
        self.temp_dir = os.path.join("data", "temp", f"task_{thread_id}")
        
        # 添加日志记录
        self.log_message(f"ThreadDetermination 初始化 - thread_id: {thread_id}, url: {url}")

    def log_message(self, message: str):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    def determine(self):
        """确定线程数量并进行文件分片"""
        from download.Pausemonitoring.Pause_monitoring import pause_monitor
        from PyQt6.QtCore import QThread, QMetaObject, Qt, Q_ARG
        from PyQt6.QtWidgets import QApplication, QMessageBox
        
        print(f"开始确定线程数量，当前设置: {self.settings.get_threads()}")
        print(f"当前任务ID: {self.thread_id}")  # 添加日志
        
        pause_monitor.update_progress(
            url=self.url,
            thread_id=self.thread_id,
            stage="开始确定线程数量"
        )

        threads = self.settings.get_threads()
        self.log_message(f"获取到线程设置: {threads}")
        
        def show_error_dialog(message):
            """在主线程中显示错误弹窗"""
            def show_dialog():
                QMessageBox.warning(None, "错误", message)
            
            if QThread.currentThread() is QApplication.instance().thread():
                show_dialog()
            else:
                QMetaObject.invokeMethod(
                    QApplication.instance(),
                    "show_error_dialog",
                    Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, message)
                )

        try:
            self.log_message(f"开始确定线程数量 - thread_id: {self.thread_id}")
            if isinstance(threads, str) and threads.lower() == "动态优化":
                print("使用动态优化模式")
                self.log_message("使用动态优化模式")
                
                try:
                    optimizer = ThreadOptimizer()
                    print("ThreadOptimizer 实例创建成功")
                    optimized_threads = optimizer.get_optimal_threads(self.thread_id, self.url)
                    print(f"动态优化计算结果: {optimized_threads}")
                    
                    if not isinstance(optimized_threads, int) or optimized_threads < 1:
                        raise ValueError(f"无效的线程数: {optimized_threads}")
                    
                    self.log_message(f"动态优化计算得到线程数: {optimized_threads}")
                    self._split_file(optimized_threads)
                    
                except Exception as e:
                    error_msg = f"动态优化失败: {str(e)}"
                    print(f"动态优化异常: {error_msg}")
                    self.log_message(error_msg)
                    # 使用默认值
                    self._split_file(4)
                    
            else:
                try:
                    thread_count = int(threads)
                    if thread_count < 1 or thread_count > 32:
                        raise ValueError("线程数必须在1-32之间")
                        
                    print(f"使用固定线程数: {thread_count}")
                    self._split_file(thread_count)
                    
                except ValueError:
                    error_msg = f"无效的线程设置: {threads}，使用默认值4"
                    print(error_msg)
                    self.log_message(error_msg)
                    self._split_file(4)
                    
        except Exception as e:
            error_msg = f"线程确定过程出错: {str(e)}"
            print(f"整体异常: {error_msg}")
            self.log_message(error_msg)
            # 使用默认值继续执行
            self._split_file(4)

    def _split_file(self, thread_count: int):
        """将文件分割为指定数量的分片"""
        from download.Pausemonitoring.Pause_monitoring import pause_monitor
        
        # 通知开始文件分片
        pause_monitor.update_progress(
            url=self.url,
            thread_id=self.thread_id,
            stage=f"开始将文件分割为 {thread_count} 个分片"
        )
        
        self.log_message(f"开始将文件分割为 {thread_count} 个分片")

        try:
            # 创建临时目录
            os.makedirs(self.temp_dir, exist_ok=True)

            # 从downloading.json获取文件名
            downloading_path = os.path.join("data", "queuemanagement", "downloading.json")
            try:
                with open(downloading_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    self.log_message(f"读取到的原始JSON内容: {content[:100]}...")
                    
                    # 清理JSON内容
                    content = content.rstrip(': \t\n\r,')
                    if content.endswith(']]:'):
                        content = content[:-1]
                    
                    try:
                        downloading_tasks = json.loads(content)
                    except json.JSONDecodeError as e:
                        self.log_message(f"JSON解析错误: {str(e)}")
                        raise
                    
                    if not isinstance(downloading_tasks, list):
                        downloading_tasks = [downloading_tasks]
                    
                    # 查找匹配的任务获取文件名
                    file_name = None
                    for task in downloading_tasks:
                        if (task.get('url') == self.url and 
                            task.get('thread_id') == self.thread_id):
                            file_name = task.get('file_name')
                            if file_name:
                                self.log_message(f"找到匹配的任务: {task}")
                                break
                    
                    if not file_name:
                        self.log_message("未找到文件名，尝试从URL生成")
                        from urllib.parse import urlparse
                        parsed_url = urlparse(self.url)
                        file_name = os.path.basename(parsed_url.path)
                        if not file_name:
                            raise Exception(f"无法获取有效的文件名: {self.url}")
                    
                    self.log_message(f"最终使用的文件名: {file_name}")
                    
            except Exception as e:
                error_msg = f"获取文件名失败: {str(e)}"
                self.log_message(error_msg)
                raise Exception(error_msg)

            # 计算每个分片的基础大小
            base_chunk_size = self.file_size // thread_count  # 使用整除
            chunks_info = []

            # 生成分片信息
            for i in range(thread_count):
                start = i * base_chunk_size
                
                if i == thread_count - 1:
                    # 最后一个分片，直接使用文件总大小作为结束位置
                    end = self.file_size - 1  # 减1是因为字节计数从0开始
                else:
                    # 其他分片
                    end = (i + 1) * base_chunk_size - 1
                
                # 计算实际大小
                actual_size = end - start + 1
                
                chunk_info = {
                    "chunk_id": i,
                    "start": start,
                    "end": end,
                    "size": actual_size,
                    "url": self.url,
                    "file_name": file_name
                }
                chunks_info.append(chunk_info)
                
                self.log_message(f"生成分片 {i}: 起始={start}, 结束={end}, 大小={actual_size}")

            # 验证总大小
            total_chunks_size = sum(chunk["size"] for chunk in chunks_info)
            if total_chunks_size != self.file_size:
                raise Exception(f"分片总大小({total_chunks_size})与文件大小({self.file_size})不匹配")

            # 保存分片信息到临时目录
            info_file = os.path.join(self.temp_dir, "chunks_info.json")
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "url": self.url,
                    "file_name": file_name,  # 添加文件名到总信息
                    "total_size": self.file_size,
                    "chunks": chunks_info
                }, f, ensure_ascii=False, indent=4)

            self.log_message(f"文件分片信息已保存到: {info_file}")
            
            # 通知分片完成
            pause_monitor.update_progress(
                url=self.url,
                thread_id=self.thread_id,
                stage=f"文件分片完成，已生成 {thread_count} 个分片"
            )

            # 调用DownloadConfig类进行下载配置
            self._configure_download()
            
        except Exception as e:
            error_msg = f"文件分片过程出错: {str(e)}"
            self.log_message(error_msg)
            pause_monitor.update_progress(
                url=self.url,
                thread_id=self.thread_id,
                stage=f"文件分片失败: {error_msg}"
            )
            raise

    def _configure_download(self):
        """配置下载方式并启动下载"""
        from download.Pausemonitoring.Pause_monitoring import pause_monitor
        
        try:
            # 通知开始配置下载
            pause_monitor.update_progress(
                url=self.url,
                thread_id=self.thread_id,
                stage="开始配置下载参数"
            )
            
            # 读取分片信息
            info_file = os.path.join(self.temp_dir, "chunks_info.json")
            with open(info_file, 'r', encoding='utf-8') as f:
                chunks_info = json.load(f)
            
            # 启动下载配置
            download_config = DownloadConfig(
                primary_thread_id=self.thread_id,
                temp_dir=self.temp_dir
            )
            
            self.log_message(f"下载配置完成，临时目录: {self.temp_dir}")
            
            # 通知配置完成
            pause_monitor.update_progress(
                url=self.url,
                thread_id=self.thread_id,
                stage="下载参数配置完成，准备开始下载"
            )
            
        except Exception as e:
            error_msg = f"配置下载时发生错误: {str(e)}"
            self.log_message(error_msg)
            pause_monitor.update_progress(
                url=self.url,
                thread_id=self.thread_id,
                stage=f"下载配置失败: {error_msg}"
            )
            QMessageBox.warning(None, "错误", error_msg)
>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
