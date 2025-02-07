import os
import json

class QueueManagement:
    def __init__(self):
        self.base_path = os.path.join("data", "queuemanagement")
        self.queue_files = {
            "downloaded": "downloaded.json",
            "downloading": "downloading.json",
            "waiting": "waiting.json",
            "error": "error.json"
        }
    
    def initialize_queue_files(self):
        """初始化所有队列文件，并确保数据有效性"""
        # 确保目录存在
        os.makedirs(self.base_path, exist_ok=True)
        
        # 初始化每个队列文件
        for queue_name, file_name in self.queue_files.items():
            file_path = os.path.join(self.base_path, file_name)
            if not os.path.exists(file_path):
                # 创建文件并写入空列表
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=4)
                print(f"Created queue file: {file_name}")
            else:
                # 验证并清理现有文件的数据
                self._clean_queue_file(file_path)
    
    def _clean_queue_file(self, file_path):
        """清理队列文件中的无效数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 确保数据是列表类型
            if not isinstance(data, list):
                data = []
            
            # 移除所有 None 值和无效数据
            cleaned_data = [item for item in data if item is not None and isinstance(item, dict)]
            
            # 写回清理后的数据
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, ensure_ascii=False, indent=4)
                
        except Exception as e:
            print(f"Error cleaning queue file {file_path}: {str(e)}")
            # 如果文件损坏，重置为空列表
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=4)
