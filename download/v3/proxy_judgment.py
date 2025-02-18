<<<<<<< HEAD
import os
from datetime import datetime
from download.util.Settings_util import SettingsUtil

class ProxyJudgment:
    def __init__(self, thread_id: int, file_name: str):
        self.thread_id = thread_id
        self.file_name = file_name
        self.settings = SettingsUtil()
        self.log_path = os.path.join("data", "log", "First_level_process", f"{thread_id}.txt")
        self.log_message(f"初始化 ProxyJudgment，线程ID: {thread_id}，文件名: {file_name}")

    def log_message(self, message: str):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    def judge(self, url: str):
        """代理判断函数"""
        self.log_message(f"开始代理判断，URL: {url}, 线程ID: {self.thread_id}, 文件名: {self.file_name}")
        
        proxy_enabled = self.settings.get_proxy_enabled()
        
        if proxy_enabled:
            self.log_message("代理已启用，调用 Proxy size retrieval 函数")
            self._call_proxy_size_retrieval(url)
        else:
            self.log_message("代理未启用，调用 Regular size retrieval 函数")
            self._call_regular_size_retrieval(url)

    def _call_proxy_size_retrieval(self, url: str):
        """调用代理尺寸获取函数"""
        self.log_message(f"调用代理尺寸获取函数，线程ID: {self.thread_id}, 文件名: {self.file_name}")
        from download.v4.proxy_size_retrieval import ProxySizeRetrieval
        proxy_retrieval = ProxySizeRetrieval(self.thread_id, self.file_name)
        proxy_retrieval.retrieve(url)

    def _call_regular_size_retrieval(self, url: str):
        """调用常规尺寸获取函数"""
        self.log_message(f"调用常规尺寸获取函数，线程ID: {self.thread_id}, 文件名: {self.file_name}")
        from download.v4.regular_size_retrieval import RegularSizeRetrieval
        regular_retrieval = RegularSizeRetrieval(self.thread_id, self.file_name)
        regular_retrieval.retrieve(url)
=======
import os
from datetime import datetime
from download.util.Settings_util import SettingsUtil

class ProxyJudgment:
    def __init__(self, thread_id: int):
        self.thread_id = thread_id
        self.settings = SettingsUtil()
        self.log_path = os.path.join("data", "log", "First_level_process", f"{thread_id}.txt")

    def log_message(self, message: str):
        """写入日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    def judge(self, url: str):
        """代理判断函数"""
        proxy_enabled = self.settings.get_proxy_enabled()
        
        if proxy_enabled:
            self.log_message("代理已启用，调用 Proxy size retrieval 函数")
            self._call_proxy_size_retrieval(url)
        else:
            self.log_message("代理未启用，调用 Regular size retrieval 函数")
            self._call_regular_size_retrieval(url)

    def _call_proxy_size_retrieval(self, url: str):
        """调用代理尺寸获取函数"""
        # TODO: 实现代理尺寸获取逻辑
        from download.v4.proxy_size_retrieval import ProxySizeRetrieval
        proxy_retrieval = ProxySizeRetrieval(self.thread_id)
        proxy_retrieval.retrieve(url)

    def _call_regular_size_retrieval(self, url: str):
        """调用常规尺寸获取函数"""
        # TODO: 实现常规尺寸获取逻辑
        from download.v4.regular_size_retrieval import RegularSizeRetrieval
        regular_retrieval = RegularSizeRetrieval(self.thread_id)
        regular_retrieval.retrieve(url)
>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
