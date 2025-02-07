import os
import json
import threading
import time
from datetime import datetime
from typing import Optional

class FirstLevelThread(threading.Thread):
    _thread_count = 0  # 类变量，用于跟踪线程编号
    _active_threads = {}  # 存储活跃的线程 {thread_id: thread_instance}
    _lock = threading.Lock()  # 用于线程安全操作

    def __init__(self, thread_id: int):
        super().__init__()
        self.thread_id = thread_id
        self.url: Optional[str] = None
        self.file_name: Optional[str] = None
        self.is_running = False
        self.log_path = os.path.join("data", "log", "First_level_process", f"{thread_id}.txt")
        self._ensure_log_directory()
        # 设置为守护线程
        self.daemon = True
        print(f"线程 {thread_id} 初始化完成")  # 添加初始化日志

    def _ensure_log_directory(self):
        """确保日志目录存在"""
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log_message(self, message: str):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    def run(self):
        """线程运行主函数"""
        try:
            self.is_running = True
            self.log_message(f"线程 {self.thread_id} 已创建")
            
            if self.url:  # 确保有URL时才继续
                self.log_message(f"开始处理URL: {self.url}")
                
                # 检查是否有保存的下载进度
                downloading_path = os.path.join("data", "queuemanagement", "downloading.json")
                with open(downloading_path, 'r', encoding='utf-8') as f:
                    downloading_tasks = json.load(f)
                
                has_progress = False
                for task in downloading_tasks:
                    if task['url'] == self.url and task.get('has_progress', False):
                        has_progress = True
                        break
                
                if has_progress:
                    self.log_message("检测到保存的下载进度，继续下载")
                    self.resume_download()
                else:
                    self.log_message("没有保存的下载进度，开始新下载")
                    self.proxy_judgment()
                
        finally:
            self.is_running = False
            self.url = None  # 清除URL，表示任务完成
            self.file_name = None
            self.log_message(f"线程 {self.thread_id} 任务完成")

    def proxy_judgment(self):
        """代理判断函数"""
        self.log_message("调用 Proxy judgment 函数")
        from download.v3.proxy_judgment import ProxyJudgment
        proxy_judgment = ProxyJudgment(self.thread_id)
        proxy_judgment.judge(self.url)

    def resume_download(self):
        """继续下载"""
        try:
            # 获取保存的下载状态
            state_dir = os.path.join("data", "download_state", str(self.thread_id))
            if not os.path.exists(state_dir):
                self.log_message("未找到下载状态，切换到新下载")
                self.proxy_judgment()
                return
            
            # 创建临时目录
            temp_dir = os.path.join("data", "temp", str(self.thread_id))
            os.makedirs(temp_dir, exist_ok=True)
            
            # 读取所有分块的状态
            chunk_states = {}
            for file_name in os.listdir(state_dir):
                if file_name.startswith("chunk_") and file_name.endswith(".json"):
                    with open(os.path.join(state_dir, file_name), 'r', encoding='utf-8') as f:
                        state = json.load(f)
                        chunk_id = int(file_name[6:-5])
                        chunk_states[chunk_id] = state
            
            if not chunk_states:
                self.log_message("未找到有效的下载状态，切换到新下载")
                self.proxy_judgment()
                return
            
            # 准备chunks_info.json
            chunks_info = {
                "url": self.url,
                "file_name": self.file_name,
                "chunks": []
            }
            
            # 将所有分块信息添加到chunks_info中
            for chunk_id, state in chunk_states.items():
                chunk_info = {
                    "chunk_id": chunk_id,
                    "url": state['url'],
                    "start": state['chunk_start'],
                    "end": state['chunk_end'],
                    "size": state['chunk_end'] - state['chunk_start'] + 1,
                    "downloaded_size": state['downloaded_size']
                }
                chunks_info["chunks"].append(chunk_info)
            
            # 保存chunks_info.json
            chunks_info_path = os.path.join(temp_dir, "chunks_info.json")
            with open(chunks_info_path, 'w', encoding='utf-8') as f:
                json.dump(chunks_info, f, ensure_ascii=False, indent=4)
            
            # 初始化DownloadConfig
            from download.v6.Secondary_thread.DownloadConfig import DownloadConfig
            download_config = DownloadConfig(
                primary_thread_id=self.thread_id,
                temp_dir=temp_dir
            )
            
            self.log_message("已通过DownloadConfig初始化所有二级线程")
            
        except Exception as e:
            self.log_message(f"继续下载失败: {str(e)}")
            # 如果继续下载失败，切换到新下载
            self.proxy_judgment()

    @classmethod
    def manage_threads(cls, downloading_tasks: list, max_tasks: int):
        """管理线程的创建、分配和销毁"""
        with cls._lock:
            try:
                print("开始管理线程...")
                
                # 找出需要新线程的任务（没有thread_id的任务）
                new_tasks = [
                    task for task in downloading_tasks
                    if task.get('status') == '下载中' and 'thread_id' not in task
                ]
                
                # 计算需要创建的新线程数
                new_threads_needed = min(
                    len(new_tasks),
                    max_tasks - len(cls._active_threads)
                )
                print(f"需要创建的新线程数: {new_threads_needed}")

                # 创建并启动新线程
                for task in new_tasks[:new_threads_needed]:
                    try:
                        thread_id = len(cls._active_threads)
                        print(f"准备创建线程: thread_id={thread_id}")
                        
                        # 创建线程实例
                        thread = FirstLevelThread(thread_id)
                        cls._active_threads[thread_id] = thread
                        
                        # 先分配任务
                        thread.url = task['url']
                        thread.file_name = task['file_name']
                        print(f"已分配任务到线程 {thread_id}")
                        
                        # 更新downloading.json
                        downloading_path = os.path.join("data", "queuemanagement", "downloading.json")
                        try:
                            with open(downloading_path, 'r', encoding='utf-8') as f:
                                tasks = json.load(f)
                            
                            # 更新对应任务的thread_id
                            for t in tasks:
                                if (t.get('url') == task['url'] and 
                                    t.get('file_name') == task['file_name'] and 
                                    t.get('status') == '下载中' and
                                    'thread_id' not in t):  # 确保只更新没有thread_id的任务
                                    t['thread_id'] = thread_id
                                    print(f"更新任务thread_id: {thread_id}")
                                    break
                            
                            # 写回文件
                            with open(downloading_path, 'w', encoding='utf-8') as f:
                                json.dump(tasks, f, ensure_ascii=False, indent=4)
                            
                        except Exception as e:
                            print(f"更新downloading.json失败: {str(e)}")
                        
                        # 启动线程
                        print(f"准备启动线程 {thread_id}")
                        thread.start()
                        print(f"线程 {thread_id} 已启动")
                        
                        # 等待线程确实开始运行
                        time.sleep(0.1)
                        if thread.is_alive():
                            print(f"线程 {thread_id} 成功运行")
                        else:
                            print(f"警告：线程 {thread_id} 可能未正常启动")

                    except Exception as e:
                        print(f"创建和启动线程 {thread_id} 时出错: {str(e)}")
                        raise

            except Exception as e:
                print(f"线程管理过程出错: {str(e)}")
                raise

    def assign_url(self, url: str, file_name: str):
        """分配URL和文件名到线程"""
        try:
            self.url = url
            self.file_name = file_name
            self.log_message(f"已分配URL: {url}")
            self.log_message(f"文件将保存为: {file_name}")
            
            # 更新downloading.json中的thread_id
            self._update_downloading_json(url, file_name)
            
        except Exception as e:
            self.log_message(f"分配URL时出错: {str(e)}")
            raise

    def _update_downloading_json(self, url: str, file_name: str):
        """更新downloading.json中的thread_id"""
        downloading_path = os.path.join("data", "queuemanagement", "downloading.json")
        try:
            with self._lock:  # 使用类的锁来确保线程安全
                # 读取当前的downloading.json
                with open(downloading_path, 'r', encoding='utf-8') as f:
                    tasks = json.load(f)
                
                # 更新对应任务的thread_id
                updated = False
                for task in tasks:
                    if (task.get('url') == url and 
                        task.get('file_name') == file_name and 
                        task.get('status') == '下载中'):
                        task['thread_id'] = self.thread_id
                        updated = True
                        self.log_message(f"更新任务thread_id: {self.thread_id}")
                        break
                
                if not updated:
                    self.log_message(f"警告: 未找到匹配的任务进行更新 (URL: {url}, 文件名: {file_name})")
                    return
                
                # 写回文件
                with open(downloading_path, 'w', encoding='utf-8') as f:
                    json.dump(tasks, f, ensure_ascii=False, indent=4)
                
                self.log_message(f"成功更新downloading.json中的thread_id: {self.thread_id}")
                
        except Exception as e:
            self.log_message(f"更新downloading.json失败: {str(e)}")
            raise

    def update_progress_in_ui(self, thread_id: int, progress: float):
        """更新UI中的进度"""
        print(f"FirstLevelThread - 收到进度更新: thread_id={thread_id}, progress={progress}")
        # 确保信号正确传递给UI
        if hasattr(self, 'progress_updated'):
            self.progress_updated.emit(thread_id, progress)