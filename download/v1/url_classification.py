import os
import json
from urllib.parse import urlparse, unquote
from PyQt6.QtWidgets import QMessageBox
from download.util.Settings_util import SettingsUtil
import re
import time

class URLClassification:
    def __init__(self):
        self.settings = SettingsUtil()
        self.base_path = os.path.join("data", "queuemanagement")
        self.downloading_path = os.path.join(self.base_path, "downloading.json")
        self.waiting_path = os.path.join(self.base_path, "waiting.json")

    def get_filename_from_url(self, url: str) -> str:
        """从URL中提取文件名并处理重复"""
        try:
            # 解析URL
            parsed_url = urlparse(url)
            path = unquote(parsed_url.path)
            filename = os.path.basename(path)
            
            # 基本的文件名清理
            if not filename:
                filename = url.rstrip('/').split('/')[-1]
            if not filename:
                filename = "unnamed_file"
            
            filename = filename.split('?')[0]
            
            # 清理非法字符
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                filename = filename.replace(char, '_')
            
            # 处理文件名重复
            name, ext = os.path.splitext(filename)
            counter = 1
            original_name = name
            
            # 检查downloading.json和waiting.json中是否存在相同文件名
            while self._is_filename_exists(f"{name}{ext}"):
                name = f"{original_name}_{counter}"
                counter += 1
            
            filename = f"{name}{ext}"
            
            # 其他处理保持不变
            if filename.startswith('.'):
                filename = f"file_{filename}"
                
            max_length = 200
            if len(filename) > max_length:
                name, ext = os.path.splitext(filename)
                filename = name[:max_length-len(ext)] + ext
                
            return filename
            
        except Exception as e:
            print(f"处理文件名时出错: {str(e)}")
            return "download_file"
            
    def _is_filename_exists(self, filename: str) -> bool:
        """检查文件名是否已存在于任务列表中"""
        try:
            # 检查downloading.json
            if os.path.exists(self.downloading_path):
                with open(self.downloading_path, 'r', encoding='utf-8') as f:
                    downloading_tasks = json.load(f)
                    if any(task.get('file_name') == filename for task in downloading_tasks):
                        return True
                        
            # 检查waiting.json
            if os.path.exists(self.waiting_path):
                with open(self.waiting_path, 'r', encoding='utf-8') as f:
                    waiting_tasks = json.load(f)
                    if any(task.get('file_name') == filename for task in waiting_tasks):
                        return True
                        
            return False
            
        except Exception as e:
            print(f"检查文件名存在性时出错: {str(e)}")
            return False

    def validate_url(self, url: str) -> tuple[bool, str]:
        """
        验证并格式化URL
        Args:
            url: 输入的URL
        Returns:
            tuple: (是否有效, 格式化后的URL或错误信息)
        """
        try:
            # 去除首尾空白
            url = url.strip()
            
            # 检查是否为空
            if not url:
                return False, "URL不能为空"
                
            # 添加协议前缀（如果没有）
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
                
            # 使用正则表达式验证URL格式
            url_pattern = re.compile(
                r'^https?://'  # http:// 或 https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # 域名
                r'localhost|'  # localhost
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP地址
                r'(?::\d+)?'  # 可选端口
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
                
            if not url_pattern.match(url):
                return False, "无效的URL格式"
                
            # 尝试解析URL
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                return False, "URL缺少必要的组成部分"
                
            return True, url
            
        except Exception as e:
            return False, f"URL验证失败: {str(e)}"

    def classify_url(self, url: str):
        """对输入的URL进行分类并写入相应的JSON文件"""
        try:
            # 首先验证URL
            is_valid, result = self.validate_url(url)
            if not is_valid:
                QMessageBox.warning(None, "URL错误", result)
                return
                
            # 使用验证后的URL
            url = result
            
            # 获取最大任务数
            max_tasks = self.settings.get_max_tasks()
            
            # 获取文件名
            file_name = self.get_filename_from_url(url)
            
            # 获取当前时间并格式化
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            
            # 读取downloading.json，处理可能的格式问题
            try:
                with open(self.downloading_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    while content.endswith(']]'):
                        content = content[:-1]
                    if not content.endswith(']'):
                        content += ']'
                    downloading_tasks = json.loads(content)
            except (json.JSONDecodeError, FileNotFoundError):
                downloading_tasks = []
            
            # 准备任务数据
            task_data = {
                "url": url,
                "file_name": file_name,
                "status": "下载中",
                "time": current_time  # 添加时间字段
            }
            
            if len(downloading_tasks) < max_tasks:
                downloading_tasks.append(task_data)
                
                with open(self.downloading_path, 'w', encoding='utf-8') as f:
                    json.dump(downloading_tasks, f, ensure_ascii=False, indent=4)
                
                # 调用FirstLevelThread管理器，传递文件名
                from download.v2.first_level_thread import FirstLevelThread
                FirstLevelThread.manage_threads(
                    downloading_tasks=downloading_tasks, 
                    max_tasks=max_tasks
                )
                
            else:
                # 准备等待任务数据
                task_data = {
                    "url": url,
                    "file_name": file_name,
                    "status": "等待中",
                    "time": current_time  # 添加时间字段
                }
                
                # 读取waiting.json，处理可能的格式问题
                try:
                    with open(self.waiting_path, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        while content.endswith(']]'):
                            content = content[:-1]
                        if not content.endswith(']'):
                            content += ']'
                        waiting_tasks = json.loads(content)
                except (json.JSONDecodeError, FileNotFoundError):
                    waiting_tasks = []
                
                waiting_tasks.append(task_data)
                
                # 写入waiting.json
                with open(self.waiting_path, 'w', encoding='utf-8') as f:
                    json.dump(waiting_tasks, f, ensure_ascii=False, indent=4)
                
                QMessageBox.information(None, "任务分配", 
                    f"URL: {url}\n已添加到等待队列")
                
        except Exception as e:
            QMessageBox.warning(None, "错误", f"URL处理失败: {str(e)}")
