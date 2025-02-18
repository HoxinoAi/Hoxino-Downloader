<<<<<<< HEAD
import psutil
import platform
from typing import Tuple, Dict
from PyQt6.QtWidgets import QMessageBox

class PerformanceEvaluator:
    def __init__(self):
        self.cpu_count = psutil.cpu_count(logical=True)
        self.memory = psutil.virtual_memory()
        self.cpu_freq = psutil.cpu_freq() if hasattr(psutil.cpu_freq(), 'max') else None
        self.system = platform.system()
        
    def evaluate_settings(self, max_tasks: int, threads_per_task: int) -> Dict:
        """
        评估用户的设置是否适合当前设备
        
        Args:
            max_tasks: 最大任务数
            threads_per_task: 每个任务的线程数
            
        Returns:
            Dict: 包含评估结果的字典
        """
        total_threads = max_tasks * threads_per_task
        available_memory_gb = self.memory.available / (1024 * 1024 * 1024)
        
        # 计算建议的最大线程数
        recommended_threads = self._calculate_recommended_threads()
        
        # 评估结果
        result = {
            "is_suitable": True,
            "warning_level": 0,  # 0: 适合, 1: 轻微警告, 2: 严重警告
            "messages": [],
            "recommendations": [],
            "system_info": {
                "cpu_cores": self.cpu_count,
                "available_memory_gb": round(available_memory_gb, 2),
                "system": self.system,
                "cpu_freq": round(self.cpu_freq.max, 2) if self.cpu_freq else "Unknown"
            }
        }
        
        # CPU 负载评估
        cpu_load_factor = total_threads / self.cpu_count
        if cpu_load_factor > 4:
            result["is_suitable"] = False
            result["warning_level"] = 2
            result["messages"].append(
                f"警告：设置的总线程数({total_threads})远超CPU核心数({self.cpu_count})，"
                "可能导致系统严重过载！"
            )
        elif cpu_load_factor > 2:
            result["warning_level"] = 1
            result["messages"].append(
                f"注意：设置的总线程数({total_threads})较多，"
                f"可能导致CPU负载较高。"
            )
            
        # 内存评估 (假设每个线程大约需要10MB内存)
        estimated_memory_usage = total_threads * 10 / 1024  # GB
        if estimated_memory_usage > available_memory_gb * 0.7:
            result["is_suitable"] = False
            result["warning_level"] = 2
            result["messages"].append(
                f"警告：预计内存使用({estimated_memory_usage:.1f}GB)接近系统可用内存"
                f"({available_memory_gb:.1f}GB)，可能导致系统不稳定！"
            )
        elif estimated_memory_usage > available_memory_gb * 0.5:
            result["warning_level"] = max(result["warning_level"], 1)
            result["messages"].append(
                f"注意：预计内存使用({estimated_memory_usage:.1f}GB)较高。"
            )
            
        # 提供建议
        if not result["is_suitable"]:
            recommended_tasks = min(max_tasks, recommended_threads // threads_per_task)
            recommended_threads_per_task = min(threads_per_task, 
                                            recommended_threads // max_tasks)
            
            result["recommendations"].extend([
                f"建议的最大任务数：{recommended_tasks}",
                f"建议的每任务线程数：{recommended_threads_per_task}",
                f"建议的总线程数：{recommended_threads}"
            ])
            
        return result

    def _calculate_recommended_threads(self) -> int:
        """计算建议的最大线程数"""
        available_memory_gb = self.memory.available / (1024 * 1024 * 1024)
        
        # 基于CPU核心数的建议
        cpu_based = self.cpu_count * 2
        
        # 基于可用内存的建议 (假设每个线程需要10MB内存)
        memory_based = int((available_memory_gb * 1024) / 10)
        
        # 取较小值作为建议值
        recommended = min(cpu_based, memory_based)
        
        # 设置上限
        return min(recommended, 32)

    def show_evaluation_dialog(self, max_tasks: int, threads_per_task: int):
        """显示评估结果对话框"""
        result = self.evaluate_settings(max_tasks, threads_per_task)
        
        # 构建消息内容
        message = "性能评估结果：\n\n"
        
        # 系统信息
        message += "系统信息：\n"
        message += f"- CPU核心数：{result['system_info']['cpu_cores']}\n"
        message += f"- 可用内存：{result['system_info']['available_memory_gb']}GB\n"
        message += f"- 操作系统：{result['system_info']['system']}\n"
        if result['system_info']['cpu_freq'] != "Unknown":
            message += f"- CPU频率：{result['system_info']['cpu_freq']}MHz\n"
        message += "\n"
        
        # 评估结果
        message += "评估结果：\n"
        total_threads = max_tasks * threads_per_task
        message += f"- 设置的最大任务数：{max_tasks}\n"
        message += f"- 每个任务的线程数：{threads_per_task}\n"
        message += f"- 总线程数：{total_threads}\n\n"
        
        # 警告和建议
        if result["messages"]:
            message += "警告：\n"
            for msg in result["messages"]:
                message += f"- {msg}\n"
            message += "\n"
            
        if result["recommendations"]:
            message += "建议：\n"
            for rec in result["recommendations"]:
                message += f"- {rec}\n"
        
        # 显示对话框
        icon = (QMessageBox.Icon.Warning if result["warning_level"] > 0 
                else QMessageBox.Icon.Information)
        title = "性能评估" if result["is_suitable"] else "性能警告"
        
        QMessageBox.information(None, title, message, icon)
        
        return result["is_suitable"]
=======
import psutil
import platform
from typing import Tuple, Dict
from PyQt6.QtWidgets import QMessageBox

class PerformanceEvaluator:
    def __init__(self):
        self.cpu_count = psutil.cpu_count(logical=True)
        self.memory = psutil.virtual_memory()
        self.cpu_freq = psutil.cpu_freq() if hasattr(psutil.cpu_freq(), 'max') else None
        self.system = platform.system()
        
    def evaluate_settings(self, max_tasks: int, threads_per_task: int) -> Dict:
        """
        评估用户的设置是否适合当前设备
        
        Args:
            max_tasks: 最大任务数
            threads_per_task: 每个任务的线程数
            
        Returns:
            Dict: 包含评估结果的字典
        """
        total_threads = max_tasks * threads_per_task
        available_memory_gb = self.memory.available / (1024 * 1024 * 1024)
        
        # 计算建议的最大线程数
        recommended_threads = self._calculate_recommended_threads()
        
        # 评估结果
        result = {
            "is_suitable": True,
            "warning_level": 0,  # 0: 适合, 1: 轻微警告, 2: 严重警告
            "messages": [],
            "recommendations": [],
            "system_info": {
                "cpu_cores": self.cpu_count,
                "available_memory_gb": round(available_memory_gb, 2),
                "system": self.system,
                "cpu_freq": round(self.cpu_freq.max, 2) if self.cpu_freq else "Unknown"
            }
        }
        
        # CPU 负载评估
        cpu_load_factor = total_threads / self.cpu_count
        if cpu_load_factor > 4:
            result["is_suitable"] = False
            result["warning_level"] = 2
            result["messages"].append(
                f"警告：设置的总线程数({total_threads})远超CPU核心数({self.cpu_count})，"
                "可能导致系统严重过载！"
            )
        elif cpu_load_factor > 2:
            result["warning_level"] = 1
            result["messages"].append(
                f"注意：设置的总线程数({total_threads})较多，"
                f"可能导致CPU负载较高。"
            )
            
        # 内存评估 (假设每个线程大约需要10MB内存)
        estimated_memory_usage = total_threads * 10 / 1024  # GB
        if estimated_memory_usage > available_memory_gb * 0.7:
            result["is_suitable"] = False
            result["warning_level"] = 2
            result["messages"].append(
                f"警告：预计内存使用({estimated_memory_usage:.1f}GB)接近系统可用内存"
                f"({available_memory_gb:.1f}GB)，可能导致系统不稳定！"
            )
        elif estimated_memory_usage > available_memory_gb * 0.5:
            result["warning_level"] = max(result["warning_level"], 1)
            result["messages"].append(
                f"注意：预计内存使用({estimated_memory_usage:.1f}GB)较高。"
            )
            
        # 提供建议
        if not result["is_suitable"]:
            recommended_tasks = min(max_tasks, recommended_threads // threads_per_task)
            recommended_threads_per_task = min(threads_per_task, 
                                            recommended_threads // max_tasks)
            
            result["recommendations"].extend([
                f"建议的最大任务数：{recommended_tasks}",
                f"建议的每任务线程数：{recommended_threads_per_task}",
                f"建议的总线程数：{recommended_threads}"
            ])
            
        return result

    def _calculate_recommended_threads(self) -> int:
        """计算建议的最大线程数"""
        available_memory_gb = self.memory.available / (1024 * 1024 * 1024)
        
        # 基于CPU核心数的建议
        cpu_based = self.cpu_count * 2
        
        # 基于可用内存的建议 (假设每个线程需要10MB内存)
        memory_based = int((available_memory_gb * 1024) / 10)
        
        # 取较小值作为建议值
        recommended = min(cpu_based, memory_based)
        
        # 设置上限
        return min(recommended, 32)

    def show_evaluation_dialog(self, max_tasks: int, threads_per_task: int):
        """显示评估结果对话框"""
        result = self.evaluate_settings(max_tasks, threads_per_task)
        
        # 构建消息内容
        message = "性能评估结果：\n\n"
        
        # 系统信息
        message += "系统信息：\n"
        message += f"- CPU核心数：{result['system_info']['cpu_cores']}\n"
        message += f"- 可用内存：{result['system_info']['available_memory_gb']}GB\n"
        message += f"- 操作系统：{result['system_info']['system']}\n"
        if result['system_info']['cpu_freq'] != "Unknown":
            message += f"- CPU频率：{result['system_info']['cpu_freq']}MHz\n"
        message += "\n"
        
        # 评估结果
        message += "评估结果：\n"
        total_threads = max_tasks * threads_per_task
        message += f"- 设置的最大任务数：{max_tasks}\n"
        message += f"- 每个任务的线程数：{threads_per_task}\n"
        message += f"- 总线程数：{total_threads}\n\n"
        
        # 警告和建议
        if result["messages"]:
            message += "警告：\n"
            for msg in result["messages"]:
                message += f"- {msg}\n"
            message += "\n"
            
        if result["recommendations"]:
            message += "建议：\n"
            for rec in result["recommendations"]:
                message += f"- {rec}\n"
        
        # 显示对话框
        icon = (QMessageBox.Icon.Warning if result["warning_level"] > 0 
                else QMessageBox.Icon.Information)
        title = "性能评估" if result["is_suitable"] else "性能警告"
        
        QMessageBox.information(None, title, message, icon)
        
        return result["is_suitable"]
>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
