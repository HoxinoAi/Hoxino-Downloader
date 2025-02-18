import sys
import json
import struct
import multiprocessing
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

class NativeMessagingHost(QObject):
    message_received = pyqtSignal(str)  # 用于发送接收到的URL信号
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.process = None
        self.message_queue = multiprocessing.Queue()
        self.output_queue = multiprocessing.Queue()
        
        # 创建定时器来检查消息队列
        self.timer = QTimer()
        self.timer.timeout.connect(self._check_message_queue)
        self.timer.start(100)  # 每100ms检查一次
    
    def start(self):
        """启动本地消息主机"""
        if self.running:
            return
            
        self.running = True
        self.process = multiprocessing.Process(
            target=self._message_loop,
            args=(self.message_queue, self.output_queue)
        )
        self.process.daemon = True
        self.process.start()
    
    def stop(self):
        """停止本地消息主机"""
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.join(timeout=1)
            self.process = None
    
    def _check_message_queue(self):
        """检查消息队列中是否有新消息"""

        while not self.message_queue.empty():
                message = self.message_queue.get_nowait()
                if 'url' in message:
                    self.message_received.emit(message['url'])
       
    
    @staticmethod
    def _message_loop(message_queue, output_queue):
        """在单独的进程中运行的消息循环"""
        while True:
            try:
                # 读取消息长度（4字节）
                length_bytes = sys.stdin.buffer.read(4)
                if not length_bytes:
                    continue
                
                # 解析消息长度
                message_length = struct.unpack('i', length_bytes)[0]
                
                # 读取消息内容
                message_bytes = sys.stdin.buffer.read(message_length)
                message = json.loads(message_bytes.decode('utf-8'))
                
                # 将消息放入队列
                message_queue.put(message)
                
            except Exception as e:
                
                continue
    
    def send_message(self, message):
        """发送消息到浏览器"""
       
        message_json = json.dumps(message)
        message_bytes = message_json.encode('utf-8')
        # 写入消息长度（4字节）
        sys.stdout.buffer.write(struct.pack('i', len(message_bytes)))
        # 写入消息内容
        sys.stdout.buffer.write(message_bytes)
        sys.stdout.buffer.flush()
            
