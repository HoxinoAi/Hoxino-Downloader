import os
import json
import psutil
import speedtest
import time
from typing import Tuple

class ThreadOptimizer:
    def __init__(self):
        self.download_json_path = os.path.join("data", "queuemanagement", "downloading.json")
        self.network_test_interval = 300  # 5分钟测试一次网络
        self.last_network_test = 0
        self.last_network_speed = 0  # 上次测试的网络速度 (Mbps)

    def get_file_size(self, thread_id: int, url: str) -> int:
        """从downloading.json中获取文件大小"""
        try:
            print(f"尝试读取文件: {self.download_json_path}")
            print(f"查找任务 - thread_id: {thread_id}, url: {url}")  # 添加日志
            
            if not os.path.exists(self.download_json_path):
                print(f"文件不存在: {self.download_json_path}")
                raise FileNotFoundError(f"找不到文件: {self.download_json_path}")
            
            # 读取JSON文件
            with open(self.download_json_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                print(f"原始JSON内容: {content[:200]}...")
                
                # 清理JSON内容
                content = content.rstrip(': \t\n\r,')
                if content.endswith(']]'):
                    content = content[:-1]
                
                try:
                    data = json.loads(content)
                    print(f"JSON解析成功，数据类型: {type(data)}")
                    
                    if not isinstance(data, list):
                        data = [data]
                    
                    # 只查找完全匹配的任务
                    for task in data:
                        print(f"检查任务: thread_id={task.get('thread_id')}, url={task.get('url')}")
                        # 同时匹配thread_id和url
                        if (str(task.get('thread_id')) == str(thread_id) and 
                            task.get('url') == url):
                            size = int(task.get('size', 0))
                            print(f"找到完全匹配的任务，大小: {size}")
                            return size
                    
                    print(f"未找到匹配的任务 (thread_id={thread_id}, url={url})")
                    return 0
                    
                except json.JSONDecodeError as e:
                    print(f"JSON解析错误: {str(e)}")
                    raise
                
        except Exception as e:
            print(f"读取文件大小时出错: {str(e)}")
            return 0  # 发生错误时返回0，让调用方使用默认值

    def get_system_resources(self) -> Tuple[int, float, float]:
        """
        获取系统资源信息
        返回: (CPU核心数, 可用内存GB, CPU使用率)
        """
        cpu_count = psutil.cpu_count(logical=True)
        memory = psutil.virtual_memory()
        available_memory_gb = memory.available / (1024 * 1024 * 1024)
        cpu_usage = psutil.cpu_percent(interval=1) / 100.0
        
        return cpu_count, available_memory_gb, cpu_usage

    def get_network_speed(self) -> float:
        """
        获取网络下载速度（Mbps）
        """
        current_time = time.time()
        
        # 如果距离上次测试不到5分钟，返回缓存的结果
        if (current_time - self.last_network_test < self.network_test_interval and 
            self.last_network_speed > 0):
            return self.last_network_speed
        
        try:
            st = speedtest.Speedtest()
            speed_mbps = st.download() / 1_000_000  # 转换为Mbps
            
            self.last_network_test = current_time
            self.last_network_speed = speed_mbps
            
            return speed_mbps
        except:
            # 如果测速失败，返回一个保守的估计值
            return 50 if self.last_network_speed == 0 else self.last_network_speed

    def calculate_optimal_threads(self, file_size: int, 
                                cpu_count: int, 
                                available_memory_gb: float,
                                cpu_usage: float,
                                network_speed: float) -> int:
        """
        计算最优线程数
        """
        try:
            # 基于文件大小的基础线程数
            if file_size < 1024 * 1024:  # < 1MB
                base_threads = 1
            elif file_size < 10 * 1024 * 1024:  # < 10MB
                base_threads = 4
            elif file_size < 100 * 1024 * 1024:  # < 100MB
                base_threads = 8
            elif file_size < 1024 * 1024 * 1024:  # < 1GB
                base_threads = 16
            else:  # >= 1GB
                # 对于大文件，每GB增加8个线程，但不超过64
                gb_size = file_size / (1024 * 1024 * 1024)
                base_threads = min(64, int(16 + gb_size * 8))

            # CPU限制
            available_cpu = max(1, cpu_count * (1 - cpu_usage))
            cpu_limit = int(available_cpu * 4)  # 每个可用CPU核心分配4个线程

            # 内存限制 (更激进的配置)
            memory_limit = int(available_memory_gb * 8)  # 每GB内存8个线程

            # 网络限制 (更激进的配置)
            network_limit = int(network_speed / 5)  # 每5Mbps带宽1个线程
            
            # 综合考虑各种限制
            optimal_threads = min(
                base_threads,
                cpu_limit,
                memory_limit,
                network_limit,
                64  # 提高最大线程数限制
            )
            
            # 确保返回整数且不小于4
            return max(4, int(optimal_threads))
            
        except Exception as e:
            raise Exception(f"计算最优线程数失败: {str(e)}")

    def get_optimal_threads(self, thread_id: int, url: str) -> int:
        """获取最优线程数"""
        try:
            print(f"开始优化计算 - thread_id: {thread_id}")  # 添加日志
            # 获取文件大小
            file_size = self.get_file_size(thread_id, url)
            if file_size == 0:
                print(f"无法获取文件大小 (thread_id={thread_id})，使用默认值")
                return 4
            
            # 获取系统资源信息
            cpu_count, available_memory_gb, cpu_usage = self.get_system_resources()
            
            # 获取网络速度
            network_speed = self.get_network_speed()
            
            # 计算最优线程数
            optimal_threads = self.calculate_optimal_threads(
                file_size,
                cpu_count,
                available_memory_gb,
                cpu_usage,
                network_speed
            )
            
            # 打印决策报告
            print(f"""
线程优化决策报告:
- 文件大小: {file_size / 1024 / 1024:.2f} MB
- CPU核心数: {cpu_count}
- CPU使用率: {cpu_usage * 100:.1f}%
- 可用内存: {available_memory_gb:.2f} GB
- 网络速度: {network_speed:.1f} Mbps
- 最终线程数: {optimal_threads}
            """)
            
            return optimal_threads
            
        except Exception as e:
            print(f"线程优化失败: {str(e)}")
            return 4  # 发生错误时返回默认值

# 使用示例
if __name__ == "__main__":
    optimizer = ThreadOptimizer()
    threads = optimizer.get_optimal_threads(123, "http://example.com/file.zip")
    print(f"建议的线程数: {threads}")
