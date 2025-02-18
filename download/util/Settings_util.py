<<<<<<< HEAD
import os
import json

class SettingsUtil:
    def __init__(self):
        self.settings_path = os.path.join("setting","setting.json")
        self.settings = self._load_settings()
    
    def _load_settings(self):
        """加载设置文件"""
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            
            return {}

    def get_max_tasks(self) -> int:
        """获取最大任务数量
        Returns:
            int: 最大任务数量，默认为4
        """
        return self.settings.get('max_tasks', 4)

    def get_threads(self) -> int:
        """获取线程数量
        Returns:
            int: 线程数量，默认为6
        """
        return self.settings.get('threads', 6)

    def get_download_path(self) -> str:
        """获取下载路径
        Returns:
            str: 下载路径，默认为桌面路径
        """
        default_path = os.path.join(os.path.expanduser("~"), "Desktop")
        return self.settings.get('download_path', default_path)

    def get_proxy_config(self):
        """获取代理配置信息"""
        try:
            with open("setting/setting.json", 'r', encoding='utf-8') as f:
                settings = json.load(f)
                proxy_address = settings.get("proxy_address", "127.0.0.1:7890")
                host, port = proxy_address.split(":")
                return {
                    "host": host,
                    "port": int(port)
                }
        except Exception as e:
            # 如果出现任何错误，返回默认配置
            return {
                "host": "127.0.0.1",
                "port": 7890
            }

    def get_proxy_enabled(self):
        """获取代理是否启用的状态"""
        try:
            with open("setting/setting.json", 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return settings.get("proxy", False)
        except Exception as e:
            return False
=======
import os
import json

class SettingsUtil:
    def __init__(self):
        self.settings_path = os.path.join("setting","setting.json")
        self.settings = self._load_settings()
    
    def _load_settings(self):
        """加载设置文件"""
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载设置文件失败: {e}")
            return {}

    def get_max_tasks(self) -> int:
        """获取最大任务数量
        Returns:
            int: 最大任务数量，默认为4
        """
        return self.settings.get('max_tasks', 4)

    def get_threads(self) -> int:
        """获取线程数量
        Returns:
            int: 线程数量，默认为6
        """
        return self.settings.get('threads', 6)

    def get_download_path(self) -> str:
        """获取下载路径
        Returns:
            str: 下载路径，默认为桌面路径
        """
        default_path = os.path.join(os.path.expanduser("~"), "Desktop")
        return self.settings.get('download_path', default_path)

    def get_proxy_config(self):
        """获取代理配置信息"""
        try:
            with open("setting/setting.json", 'r', encoding='utf-8') as f:
                settings = json.load(f)
                proxy_address = settings.get("proxy_address", "127.0.0.1:7890")
                host, port = proxy_address.split(":")
                return {
                    "host": host,
                    "port": int(port)
                }
        except Exception as e:
            # 如果出现任何错误，返回默认配置
            return {
                "host": "127.0.0.1",
                "port": 7890
            }

    def get_proxy_enabled(self):
        """获取代理是否启用的状态"""
        try:
            with open("setting/setting.json", 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return settings.get("proxy", False)
        except Exception as e:
            return False
>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
