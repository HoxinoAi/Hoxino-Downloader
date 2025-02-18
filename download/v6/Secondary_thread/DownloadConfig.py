<<<<<<< HEAD
import os
import json
import threading
from typing import Dict, List
from download.util.Settings_util import SettingsUtil
from queuemanagement.queuemanagement import DatabaseManager

class DownloadConfig:
    merge_instances = {}  # 存储每个一级线程ID对应的Merge实例
    progress_instances = {}  # 存储每个文件名对应的Progress实例
    
    def __init__(self, primary_thread_id: int, temp_dir: str, file_name: str):
        """
        初始化下载配置
        Args:
            primary_thread_id: 一级线程ID
            temp_dir: 临时目录位置
            file_name: 文件名
        """
        self.primary_thread_id = primary_thread_id
        self.temp_dir = temp_dir
        self.file_name = file_name  # 新增文件名字段
        self.settings = SettingsUtil()
        self.db_manager = DatabaseManager()
        
        # 确定下载模式
        self.download_mode = "proxy" if self.settings.get_proxy_enabled() else "regular"
        
        # 设置日志路径
        self.log_path = os.path.join("data", "log", "First_level_process", f"{primary_thread_id}.txt")
        
        # 记录初始化信息
        self.log_message(f"一级线程 {primary_thread_id} 初始化下载配置")
        self.log_message(f"文件名: {file_name}")  # 新增日志
        self.log_message(f"临时目录: {temp_dir}")
        self.log_message(f"下载模式: {self.download_mode}")
        
        # 启动二级线程管理
        self.secondary_thread_manager()
        
        # 启动进度管理和合并监控
        self._start_monitors()
        
    def log_message(self, message: str):
        """写入日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
            
    def secondary_thread_manager(self):
        """二级线程管理函数"""
        try:
            # 直接使用实例的 file_name
            chunks = self.db_manager.get_chunks_by_filename(self.file_name)
            if not chunks:
                raise ValueError(f"找不到文件 {self.file_name} 的分片信息")
            
            self.log_message(f"读取到 {len(chunks)} 个分片信息")
            
            # 按照chunk_id排序分片信息
            chunks.sort(key=lambda x: x['chunk_id'])
            
            # 创建并启动二级线程
            for chunk in chunks:
                thread = threading.Thread(
                    target=self._start_request,
                    args=(chunk,),
                    name=f"SecondaryThread-{chunk['chunk_id']}"
                )
                thread.daemon = True
                thread.start()
                self.log_message(f"启动二级线程 {chunk['chunk_id']}")
                
        except Exception as e:
            self.log_message(f"二级线程管理出错: {str(e)}")
            
    def _start_request(self, chunk: Dict):
        """启动单个二级线程的请求"""
        try:
            # 在chunk信息中添加文件名
            chunk['file_name'] = self.file_name
            
            from download.v6.install.Secondary_thread_request import SecondaryThreadRequest
            request = SecondaryThreadRequest(
                primary_thread_id=self.primary_thread_id,
                secondary_thread_id=chunk["chunk_id"],
                chunk_info=chunk,
                temp_dir=self.temp_dir,
                download_mode=self.download_mode,
                file_name=self.file_name  # 添加文件名参数
            )
            request.start()
            
        except Exception as e:
            self.log_message(f"二级线程 {chunk['chunk_id']} 请求启动失败: {str(e)}")
            
    def _start_monitors(self):
        """启动进度管理和合并监控"""
        try:
            # 直接使用实例的 file_name
            chunks = self.db_manager.get_chunks_by_filename(self.file_name)
            if not chunks:
                raise ValueError(f"找不到文件 {self.file_name} 的分片信息")
            
            # 初始化进度管理，传入文件名
            from download.v6.progress.progress import Progress
            self.progress = Progress(file_name=self.file_name)
            DownloadConfig.progress_instances[self.file_name] = self.progress  # 保存实例
            self.log_message(f"启动进度管理 (文件名: {self.file_name})")
            
            # 启动合并监控线程
            from download.v6.merge.merge import Merge
            self.merge = Merge(
                primary_thread_id=self.primary_thread_id,
                file_name=self.file_name  # 如果 Merge 类也需要文件名，也要传入
            )
            DownloadConfig.merge_instances[self.primary_thread_id] = self.merge
            
            merge_thread = threading.Thread(
                target=self.merge.start,
                name=f"MergeThread-{self.primary_thread_id}"
            )
            merge_thread.daemon = False
            merge_thread.start()
            self.log_message("启动合并监控")
            
        except Exception as e:
            self.log_message(f"启动监控失败: {str(e)}")
=======
import os
import json
import threading
from typing import Dict, List
from download.util.Settings_util import SettingsUtil

class DownloadConfig:
    merge_instances = {}  # 存储每个一级线程ID对应的Merge实例
    
    def __init__(self, primary_thread_id: int, temp_dir: str):
        """
        初始化下载配置
        Args:
            primary_thread_id: 一级线程ID
            temp_dir: 临时目录位置
        """
        self.primary_thread_id = primary_thread_id
        self.temp_dir = temp_dir
        self.settings = SettingsUtil()
        
        # 确定下载模式
        self.download_mode = "proxy" if self.settings.get_proxy_enabled() else "regular"
        
        # 设置日志路径
        self.log_path = os.path.join("data", "log", "First_level_process", f"{primary_thread_id}.txt")
        
        # 记录初始化信息
        self.log_message(f"一级线程 {primary_thread_id} 初始化下载配置")
        self.log_message(f"临时目录: {temp_dir}")
        self.log_message(f"下载模式: {self.download_mode}")
        
        # 启动二级线程管理
        self.secondary_thread_manager()
        
        # 启动进度管理和合并监控
        self._start_monitors()
        
    def log_message(self, message: str):
        """写入日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
            
    def secondary_thread_manager(self):
        """二级线程管理函数"""
        try:
            # 读取分片信息
            chunks_info_path = os.path.join(self.temp_dir, "chunks_info.json")
            with open(chunks_info_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                chunks = data["chunks"]
            
            self.log_message(f"读取到 {len(chunks)} 个分片信息")
            
            # 创建并启动二级线程
            for chunk in chunks:
                thread = threading.Thread(
                    target=self._start_request,
                    args=(chunk,),
                    name=f"SecondaryThread-{chunk['chunk_id']}"
                )
                thread.start()
                self.log_message(f"启动二级线程 {chunk['chunk_id']}")
                
        except Exception as e:
            self.log_message(f"二级线程管理出错: {str(e)}")
            
    def _start_request(self, chunk: Dict):
        """启动单个二级线程的请求"""
        try:
            from download.v6.install.Secondary_thread_request import SecondaryThreadRequest
            request = SecondaryThreadRequest(
                primary_thread_id=self.primary_thread_id,
                secondary_thread_id=chunk["chunk_id"],
                chunk_info=chunk,
                temp_dir=self.temp_dir,
                download_mode=self.download_mode
            )
            request.start()
            
        except Exception as e:
            self.log_message(f"二级线程 {chunk['chunk_id']} 请求启动失败: {str(e)}")
            
    def _start_monitors(self):
        """启动进度管理和合并监控"""
        try:
            # 初始化进度管理
            from download.v6.progress.progress import Progress
            self.progress = Progress(self.primary_thread_id)
            self.log_message("启动进度管理")
            
            # 启动合并监控线程
            from download.v6.merge.merge import Merge
            self.merge = Merge(self.primary_thread_id)
            DownloadConfig.merge_instances[self.primary_thread_id] = self.merge  # 保存实例
            
            merge_thread = threading.Thread(
                target=self.merge.start,
                name=f"MergeThread-{self.primary_thread_id}"
            )
            merge_thread.daemon = False
            merge_thread.start()
            self.log_message("启动合并监控")
            
        except Exception as e:
            self.log_message(f"启动失败: {str(e)}")
>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
