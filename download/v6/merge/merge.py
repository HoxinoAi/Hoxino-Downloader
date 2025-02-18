<<<<<<< HEAD
import os
import json
from typing import Set
from datetime import datetime
from download.util.Settings_util import SettingsUtil
import threading
import queue
from urllib.parse import urlparse, unquote
import traceback
from queuemanagement.queuemanagement import DatabaseManager

class Merge:
    def __init__(self, primary_thread_id: int, file_name: str):
        """
        初始化合并监控
        Args:
            primary_thread_id: 一级线程ID
            file_name: 文件名
        """
        self.primary_thread_id = primary_thread_id
        self.file_name = file_name  # 直接使用传入的文件名
        self.db_manager = DatabaseManager()
        
        # 设置独立的合并监控日志路径
        self.log_dir = os.path.join("data", "log", "merge")
        self.log_path = os.path.join(self.log_dir, f"{primary_thread_id}.txt")
        
        # 确保日志目录存在并清理旧日志
        self._ensure_log_directory()
        self._clean_old_log()
        
        # 获取分片信息
        self.chunks = self.db_manager.get_chunks_by_filename(self.file_name)
        if not self.chunks:
            raise ValueError(f"找不到文件 {self.file_name} 的分片信息")
        
        # 设置临时目录
        self.temp_dir = os.path.join("data", "installtemp", f"{self.file_name}")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # 记录完成的分片
        self.completed_chunks = set()
        self.total_chunks = len(self.chunks)
        
        # 初始化信号队列
        self.signal_queue = queue.Queue()
        
        self.log_message(f"初始化合并监控，文件名：{self.file_name}，总分片数：{self.total_chunks}")
        
    def _ensure_log_directory(self):
        """确保日志目录存在"""
        os.makedirs(self.log_dir, exist_ok=True)

    def _clean_old_log(self):
        """清理旧的日志文件"""
        if os.path.exists(self.log_path):
                os.remove(self.log_path)

    def log_message(self, message: str):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
            
    def start(self):
        """启动合并监控"""
        try:
            self.log_message("合并监控开始运行")
            while True:
                try:
                    # 等待二级线程的完成信号
                    self.log_message("等待二级线程完成信号...")
                    secondary_thread_id = self.signal_queue.get()
                    self.log_message(f"收到二级线程 {secondary_thread_id} 的完成信号")
                    self.notify_chunk_complete(secondary_thread_id)
                    
                    # 如果所有分片都完成了，就退出监听
                    if len(self.completed_chunks) == self.total_chunks:
                        self.log_message("所有分片信号已收到，退出监听")
                        break
                        
                except Exception as e:
                    self.log_message(f"监听过程出错: {str(e)}")
                    break  # 出错时退出循环
                
            self.log_message("合并监控结束")
            
        except Exception as e:
            self.log_message(f"合并监控启动失败: {str(e)}")
        
    def notify_chunk_complete(self, secondary_thread_id: int):
        """接收二级线程完成信号"""
        self.completed_chunks.add(secondary_thread_id)
        self.log_message(f"二级线程 {secondary_thread_id} 下载完成")
        
        # 检查是否所有分片都完成
        if len(self.completed_chunks) == self.total_chunks:
            self.log_message("所有分片下载完成，更新状态为合并中")
            
            # 更新数据库中的任务状态为合并中
            if self.db_manager.update_task_status_by_filename(self.file_name, "合并中"):
                self.log_message("已更新任务状态为合并中")
            else:
                self.log_message("更新任务状态失败")
                
            # 更新进度为100%
            if self.db_manager.update_progress_by_filename(self.file_name, 100):
                self.log_message("已更新进度为100%")
            else:
                self.log_message("更新进度失败")
                
            self.log_message("开始合并文件")
            self._merge_files()
            
    def _merge_files(self):
        """合并所有分片文件"""
        try:
            # 获取下载路径（包含自动重命名功能）
            self.download_path = self.get_download_path()
            self.log_message(f"合并文件将保存到: {self.download_path}")
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(self.download_path), exist_ok=True)
            
            # 按顺序合并分片
            with open(self.download_path, 'wb') as outfile:
                for chunk in sorted(self.chunks, key=lambda x: x['chunk_id']):
                    chunk_path = os.path.join(self.temp_dir, f"chunk_{chunk['chunk_id']}")
                    if os.path.exists(chunk_path):
                        with open(chunk_path, 'rb') as infile:
                            outfile.write(infile.read())
                        self.log_message(f"成功合并分片: {chunk_path}")
                    else:
                        self.log_message(f"警告：分片文件不存在: {chunk_path}")
            
            self.log_message("文件合并完成")
            
            # 删除数据库中的分片记录
            if self.db_manager.delete_chunks_by_filename(self.file_name):
                self.log_message("成功删除分片数据")
            else:
                self.log_message("删除分片数据失败")
            
            # 清理临时文件
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
                self.log_message(f"清理临时文件目录: {self.temp_dir}")
            except Exception as e:
                self.log_message(f"清理临时文件失败: {str(e)}")
            
            # 调用结论处理，传入文件名和下载路径
            from download.v6.conclusion.conclusion import Conclusion
            conclusion = Conclusion(self.primary_thread_id)
            conclusion.process(file_name=self.file_name, download_path=self.download_path)
            
        except Exception as e:
            self.log_message(f"合并文件失败: {str(e)}")
            traceback.print_exc()
            

            
    def get_download_path(self) -> str:
        """获取下载文件保存路径，如果目标位置已存在文件则重命名"""
        try:
            settings = SettingsUtil()
            download_dir = settings.get_download_path()
            os.makedirs(download_dir, exist_ok=True)
            
            # 从chunks_info中获取基础文件名
            filename = self.file_name
            if not filename:
                # 如果没有预设的文件名，则从URL生成
                url = self.file_name
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                filename = filename.split('?')[0]
                
                # 清理非法字符
                invalid_chars = '<>:"|?*'
                for char in invalid_chars:
                    filename = filename.replace(char, '_')
                    
                if not filename:
                    filename = "downloaded_file"
            
            # 处理文件名重复
            name, ext = os.path.splitext(filename)
            counter = 1
            original_name = name
            
            # 检查文件是否已存在，如果存在则重命名
            while True:
                full_path = os.path.join(download_dir, f"{name}{ext}")
                if not os.path.exists(full_path):
                    break
                name = f"{original_name}_{counter}"
                counter += 1
                self.log_message(f"文件已存在，尝试新文件名: {name}{ext}")
            
            # 最终的完整路径
            final_path = os.path.normpath(full_path)
            
            self.log_message(f"原始URL: {self.file_name}")
            self.log_message(f"原始文件名: {filename}")
            self.log_message(f"最终保存路径: {final_path}")
            
            return final_path
            
        except Exception as e:
            self.log_message(f"生成下载路径失败: {str(e)}")
            # 生成一个带时间戳的默认文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return os.path.join(download_dir, f"downloaded_file_{timestamp}")

class FileMerger:
    def __init__(self, primary_thread_id: int, chunks_info: dict):
        self.primary_thread_id = primary_thread_id
        self.chunks_info = chunks_info
        self.download_path = None  # 添加成员变量存储下载路径
        
        # 设置日志路径
        self.log_dir = os.path.join("data", "log", "merge")
        self.log_path = os.path.join(self.log_dir, f"merge_{self.primary_thread_id}.log")
        
        # 确保日志目录存在并清理旧日志
        self._ensure_log_directory()
        self._clean_old_log()

    def _ensure_log_directory(self):
        """确保日志目录存在"""
        os.makedirs(self.log_dir, exist_ok=True)

    def _clean_old_log(self):
        """清理旧的日志文件"""

        if os.path.exists(self.log_path):
                os.remove(self.log_path)


    def log_message(self, message: str):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    def get_clean_filename(self, file_path: str) -> str:
        """
        获取清理过的文件路径
        Args:
            file_path: 原始文件路径（可能包含URL参数）
        Returns:
            str: 清理后的文件路径
        """
        try:
            # 分离目录和文件名
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            
            # 清理文件名（移除URL参数和非法字符）
            filename = filename.split('?')[0]  # 移除URL参数
            
            # 清理非法字符
            invalid_chars = '<>:"|?*'  # 移除 \ / 因为它们是路径分隔符
            for char in invalid_chars:
                filename = filename.replace(char, '_')
                
            # 重新组合目录和清理后的文件名
            clean_path = os.path.join(directory, filename)
            
            # 规范化路径分隔符
            clean_path = os.path.normpath(clean_path)
            
            self.log_message(f"原始路径: {file_path}")
            self.log_message(f"清理后路径: {clean_path}")
            
            return clean_path
            
        except Exception as e:
            self.log_message(f"清理文件名失败: {str(e)}")
            # 返回一个默认的安全路径
            return os.path.join(os.path.dirname(file_path), "merged_file")
            
    def merge_files(self, file_parts: list, output_path: str):
        """
        合并文件分片
        Args:
            file_parts: 分片文件路径列表
            output_path: 输出文件路径
        """
        try:
            # 获取清理后的输出路径
            clean_output_path = self.get_clean_filename(output_path)
            self.log_message(f"开始合并文件")
            self.log_message(f"合并文件将保存到: {clean_output_path}")
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(clean_output_path), exist_ok=True)
            
            # 合并文件
            with open(clean_output_path, 'wb') as outfile:
                for part in sorted(file_parts):
                    if os.path.exists(part):
                        with open(part, 'rb') as infile:
                            outfile.write(infile.read())
                        self.log_message(f"成功合并分片: {part}")
                    else:
                        self.log_message(f"警告：分片文件不存在: {part}")
                        
            # 删除分片文件
            for part in file_parts:
                try:
                    if os.path.exists(part):
                        os.remove(part)
                        self.log_message(f"成功删除分片: {part}")
                except Exception as e:
                    self.log_message(f"删除分片文件失败 {part}: {str(e)}")
                    
            self.log_message("文件合并完成")
            
        except Exception as e:
            self.log_message(f"文件合并失败: {str(e)}")
            raise
=======
import os
import json
from typing import Set
from datetime import datetime
from download.util.Settings_util import SettingsUtil
import threading
import queue
from urllib.parse import urlparse, unquote
import traceback

class Merge:
    def __init__(self, primary_thread_id: int):
        """
        初始化合并监控
        Args:
            primary_thread_id: 一级线程ID
        """
        self.primary_thread_id = primary_thread_id
        
        # 设置独立的合并监控日志路径
        self.log_dir = os.path.join("data", "log", "merge")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_path = os.path.join(self.log_dir, f"{primary_thread_id}.txt")
        
        # 读取分片信息
        self.temp_dir = os.path.join("data", "temp", f"task_{primary_thread_id}")
        self.chunks_info = self._load_chunks_info()
        self.total_chunks = len(self.chunks_info["chunks"])
        
        # 记录完成的分片
        self.completed_chunks: Set[int] = set()
        
        self.signal_queue = queue.Queue()  # 用于接收信号的队列
        
    def _load_chunks_info(self) -> dict:
        """加载分片信息"""
        info_file = os.path.join(self.temp_dir, "chunks_info.json")
        with open(info_file, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def log_message(self, message: str):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
            
    def start(self):
        """启动合并监控"""
        try:
            self.log_message("合并监控开始运行")
            while True:
                try:
                    # 等待二级线程的完成信号
                    self.log_message("等待二级线程完成信号...")
                    secondary_thread_id = self.signal_queue.get()
                    self.log_message(f"收到二级线程 {secondary_thread_id} 的完成信号")
                    self.notify_chunk_complete(secondary_thread_id)
                    
                    # 如果所有分片都完成了，就退出监听
                    if len(self.completed_chunks) == self.total_chunks:
                        self.log_message("所有分片信号已收到，退出监听")
                        break
                        
                except Exception as e:
                    self.log_message(f"监听过程出错: {str(e)}")
                    break  # 出错时退出循环
                
            self.log_message("合并监控结束")
            
        except Exception as e:
            self.log_message(f"合并监控启动失败: {str(e)}")
        
    def notify_chunk_complete(self, secondary_thread_id: int):
        """接收二级线程完成信号"""
        self.completed_chunks.add(secondary_thread_id)
        self.log_message(f"二级线程 {secondary_thread_id} 下载完成")
        
        # 检查是否所有分片都完成
        if len(self.completed_chunks) == self.total_chunks:
            self.log_message("所有分片下载完成，开始合并文件")
            self._merge_files()
            
    def _merge_files(self):
        """合并所有分片文件"""
        try:
            # 获取下载路径（包含自动重命名功能）
            self.download_path = self.get_download_path()  # 保存路径到成员变量
            self.log_message(f"合并文件将保存到: {self.download_path}")
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(self.download_path), exist_ok=True)
            
            # 按顺序合并分片
            with open(self.download_path, 'wb') as outfile:
                for chunk in self.chunks_info["chunks"]:
                    chunk_path = os.path.join("data", "installtemp", 
                        str(self.primary_thread_id), f"chunk_{chunk['chunk_id']}")
                    if os.path.exists(chunk_path):
                        with open(chunk_path, 'rb') as infile:
                            outfile.write(infile.read())
                        self.log_message(f"成功合并分片: {chunk_path}")
                    else:
                        self.log_message(f"警告：分片文件不存在: {chunk_path}")
            
            self.log_message("文件合并完成")
            
            # 更新downloaded.json
            self._update_downloaded_info()
            
            # 清理临时文件
            temp_dir = os.path.join("data", "installtemp", str(self.primary_thread_id))
            try:
                import shutil
                shutil.rmtree(temp_dir)
                self.log_message(f"清理临时文件目录: {temp_dir}")
            except Exception as e:
                self.log_message(f"清理临时文件失败: {str(e)}")
            
            # 调用结论处理
            from download.v6.conclusion.conclusion import Conclusion
            conclusion = Conclusion(self.primary_thread_id)
            conclusion.process(self.chunks_info["url"])
            
        except Exception as e:
            self.log_message(f"文件合并失败: {str(e)}")
            self.log_message(traceback.format_exc())  # 添加详细错误信息
            
    def _update_downloaded_info(self):
        """更新downloaded.json文件"""
        try:
            if not self.download_path:  # 检查下载路径是否存在
                self.log_message("错误：下载路径未设置")
                return
                
            downloaded_path = os.path.join("data", "queuemanagement", "downloaded.json")
            os.makedirs(os.path.dirname(downloaded_path), exist_ok=True)
            
            # 读取现有数据
            downloaded_list = []
            if os.path.exists(downloaded_path):
                try:
                    with open(downloaded_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        # 清理可能的多余数据
                        if content.endswith(']]]'):
                            content = content[:-1]
                        if content.endswith(']]'):
                            content = content[:-1]
                        downloaded_list = json.loads(content)
                        if not isinstance(downloaded_list, list):
                            downloaded_list = [downloaded_list]
                except json.JSONDecodeError:
                    self.log_message("警告：downloaded.json格式错误，将重新创建")
                    downloaded_list = []
            
            # 创建新的下载记录
            new_record = {
                'url': self.chunks_info["url"],
                'file_name': os.path.basename(self.download_path),
                'save_path': os.path.abspath(self.download_path),  # 使用绝对路径
                'status': "已完成",
                'thread_id': self.primary_thread_id,
                'size': os.path.getsize(self.download_path),
                'progress': 100.0,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 检查是否已存在相同记录
            exists = False
            for i, item in enumerate(downloaded_list):
                if item.get('file_name') == new_record['file_name']:
                    downloaded_list[i] = new_record  # 更新现有记录
                    exists = True
                    break
            
            if not exists:
                downloaded_list.append(new_record)
            
            # 保存更新后的数据
            with open(downloaded_path, 'w', encoding='utf-8') as f:
                json.dump(downloaded_list, f, ensure_ascii=False, indent=4)
                
            self.log_message(f"已更新downloaded.json，文件保存在: {self.download_path}")
            
        except Exception as e:
            self.log_message(f"更新downloaded.json失败: {str(e)}")
            self.log_message(traceback.format_exc())
            
    def get_download_path(self) -> str:
        """获取下载文件保存路径，如果目标位置已存在文件则重命名"""
        try:
            settings = SettingsUtil()
            download_dir = settings.get_download_path()
            os.makedirs(download_dir, exist_ok=True)
            
            # 从chunks_info中获取基础文件名
            filename = self.chunks_info.get("file_name", "")
            if not filename:
                # 如果没有预设的文件名，则从URL生成
                url = self.chunks_info["url"]
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                filename = filename.split('?')[0]
                
                # 清理非法字符
                invalid_chars = '<>:"|?*'
                for char in invalid_chars:
                    filename = filename.replace(char, '_')
                    
                if not filename:
                    filename = "downloaded_file"
            
            # 处理文件名重复
            name, ext = os.path.splitext(filename)
            counter = 1
            original_name = name
            
            # 检查文件是否已存在，如果存在则重命名
            while True:
                full_path = os.path.join(download_dir, f"{name}{ext}")
                if not os.path.exists(full_path):
                    break
                name = f"{original_name}_{counter}"
                counter += 1
                self.log_message(f"文件已存在，尝试新文件名: {name}{ext}")
            
            # 最终的完整路径
            final_path = os.path.normpath(full_path)
            
            self.log_message(f"原始URL: {self.chunks_info['url']}")
            self.log_message(f"原始文件名: {filename}")
            self.log_message(f"最终保存路径: {final_path}")
            
            return final_path
            
        except Exception as e:
            self.log_message(f"生成下载路径失败: {str(e)}")
            # 生成一个带时间戳的默认文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return os.path.join(download_dir, f"downloaded_file_{timestamp}")

class FileMerger:
    def __init__(self, primary_thread_id: int, chunks_info: dict):
        self.primary_thread_id = primary_thread_id
        self.chunks_info = chunks_info
        self.download_path = None  # 添加成员变量存储下载路径

    def get_clean_filename(self, file_path: str) -> str:
        """
        获取清理过的文件路径
        Args:
            file_path: 原始文件路径（可能包含URL参数）
        Returns:
            str: 清理后的文件路径
        """
        try:
            # 分离目录和文件名
            directory = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            
            # 清理文件名（移除URL参数和非法字符）
            filename = filename.split('?')[0]  # 移除URL参数
            
            # 清理非法字符
            invalid_chars = '<>:"|?*'  # 移除 \ / 因为它们是路径分隔符
            for char in invalid_chars:
                filename = filename.replace(char, '_')
                
            # 重新组合目录和清理后的文件名
            clean_path = os.path.join(directory, filename)
            
            # 规范化路径分隔符
            clean_path = os.path.normpath(clean_path)
            
            self.log_message(f"原始路径: {file_path}")
            self.log_message(f"清理后路径: {clean_path}")
            
            return clean_path
            
        except Exception as e:
            self.log_message(f"清理文件名失败: {str(e)}")
            # 返回一个默认的安全路径
            return os.path.join(os.path.dirname(file_path), "merged_file")
            
    def merge_files(self, file_parts: list, output_path: str):
        """
        合并文件分片
        Args:
            file_parts: 分片文件路径列表
            output_path: 输出文件路径
        """
        try:
            # 获取清理后的输出路径
            clean_output_path = self.get_clean_filename(output_path)
            self.log_message(f"开始合并文件")
            self.log_message(f"合并文件将保存到: {clean_output_path}")
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(clean_output_path), exist_ok=True)
            
            # 合并文件
            with open(clean_output_path, 'wb') as outfile:
                for part in sorted(file_parts):
                    if os.path.exists(part):
                        with open(part, 'rb') as infile:
                            outfile.write(infile.read())
                        self.log_message(f"成功合并分片: {part}")
                    else:
                        self.log_message(f"警告：分片文件不存在: {part}")
                        
            # 删除分片文件
            for part in file_parts:
                try:
                    if os.path.exists(part):
                        os.remove(part)
                        self.log_message(f"成功删除分片: {part}")
                except Exception as e:
                    self.log_message(f"删除分片文件失败 {part}: {str(e)}")
                    
            self.log_message("文件合并完成")
            
        except Exception as e:
            self.log_message(f"文件合并失败: {str(e)}")
            raise
            
    def log_message(self, message: str):
        """写入日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_dir = os.path.join("data", "log", "merge")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"merge_{self.primary_thread_id}.log")
        
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
