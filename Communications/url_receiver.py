<<<<<<< HEAD
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
from pathlib import Path
import os
import sys
from PyQt6.QtCore import (
    QObject, 
    pyqtSignal, 
    QThread, 
    QMetaObject, 
    Q_ARG, 
    Qt,
    QTimer
)
from collections import deque
from time import time
import threading

class URLReceiver(QObject):
    url_received = pyqtSignal(str)  # 定义信号
    
    def __init__(self, port=8888):
        super().__init__()
        self.port = port
        self.server = None
        self.setup_logging()
        # 修改请求记录队列的大小和时间限制
        self.request_times = deque(maxlen=3)  # 减小队列大小
        self.min_interval = 0.5  # 设置最小间隔时间（秒）
        self.processing_lock = threading.Lock()  # 添加处理锁
        
    def setup_logging(self):
        """设置日志"""
        log_dir = Path(os.path.expanduser("~")) / "AppData" / "Local" / "Hoxino" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "url_receiver.log"
        

    
    def emit_url_signal(self, url: str):
        """在主线程中发送URL信号"""
        # 直接发送信号
        self.url_received.emit(url)
    class RequestHandler(BaseHTTPRequestHandler):
        def do_HEAD(self):
            """处理HEAD请求（用于检查服务器状态）"""
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
        
        def do_OPTIONS(self):
            """处理OPTIONS请求（用于CORS）"""
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, HEAD, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

        def do_POST(self):
            """处理POST请求"""
            try:
                # 获取请求内容长度
                content_length = int(self.headers['Content-Length'])
                # 读取请求内容
                post_data = self.rfile.read(content_length)
                # 解析JSON数据
                data = json.loads(post_data.decode('utf-8'))
                
                url = data.get('url', '')
                
                # 使用锁确保线程安全
                with self.server.url_receiver.processing_lock:
                    current_time = time()
                    
                    # 检查时间间隔
                    if self.server.url_receiver.request_times:
                        last_request_time = self.server.url_receiver.request_times[-1]
                        if current_time - last_request_time < self.server.url_receiver.min_interval:
                            self.send_response(429)
                            self.send_header('Content-type', 'application/json')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            
                            response = {
                                'status': 'error',
                                'message': '请求过于频繁，请稍后再试'
                            }
                            self.wfile.write(json.dumps(response).encode('utf-8'))
                            return
                    
                    # 更新请求时间
                    self.server.url_receiver.request_times.append(current_time)
                    
                    # 处理URL
                    try:
                        self._process_url(url)
                    except Exception as e:
                        raise
                
            except Exception as e:
                logging.error(f"处理请求时出错: {str(e)}", exc_info=True)
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {'status': 'error', 'message': str(e)}
                self.wfile.write(json.dumps(response).encode('utf-8'))

        def _process_url(self, url: str):
            """处理URL请求"""
            try:
                if not url or not url.strip():
                    raise ValueError("无效的URL")
                
                # 使用 QTimer 发送信号
                self.server.url_receiver.emit_url_signal(url)
                
                # 返回成功响应
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {'status': 'success', 'message': 'URL received'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            except Exception as e:
                logging.error(f"处理URL时出错: {str(e)}", exc_info=True)
                raise

    def start(self):
        """启动服务器"""
        try:
            # 创建自定义的HTTPServer类bug
            class CustomHTTPServer(HTTPServer):
                def __init__(self, server_address, RequestHandlerClass, url_receiver):
                    super().__init__(server_address, RequestHandlerClass)
                    self.url_receiver = url_receiver
            
            # 创建服务器实例
            self.server = CustomHTTPServer(
                ('', self.port), 
                self.RequestHandler,
                self
            )
            
            
            
            # 使用线程运行服务器
            server_thread = threading.Thread(target=self.server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
        except Exception as e:
            logging.error(f"启动服务器时出错: {str(e)}", exc_info=True)
            raise
    
    def stop(self):
        """停止服务器"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()

# 测试代码
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    receiver = URLReceiver()
    

    
    try:
        receiver.start()
    except KeyboardInterrupt:
        receiver.stop()
        
=======
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
from pathlib import Path
import os
import sys
from PyQt6.QtCore import (
    QObject, 
    pyqtSignal, 
    QThread, 
    QMetaObject, 
    Q_ARG, 
    Qt,
    QTimer
)
from collections import deque
from time import time
import threading

class URLReceiver(QObject):
    url_received = pyqtSignal(str)  # 定义信号
    
    def __init__(self, port=8888):
        super().__init__()
        self.port = port
        self.server = None
        self.setup_logging()
        # 修改请求记录队列的大小和时间限制
        self.request_times = deque(maxlen=3)  # 减小队列大小
        self.min_interval = 0.5  # 设置最小间隔时间（秒）
        self.processing_lock = threading.Lock()  # 添加处理锁
        
    def setup_logging(self):
        """设置日志"""
        log_dir = Path(os.path.expanduser("~")) / "AppData" / "Local" / "Hoxino" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "url_receiver.log"
        
        # 同时输出到控制台和文件
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(str(log_file)),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def emit_url_signal(self, url: str):
        """在主线程中发送URL信号"""
        logging.info(f"发送URL信号: {url}")
        try:
            # 直接发送信号
            self.url_received.emit(url)
            logging.info("URL信号发送成功")
        except Exception as e:
            logging.error(f"发送URL信号时出错: {str(e)}", exc_info=True)
    
    class RequestHandler(BaseHTTPRequestHandler):
        def do_HEAD(self):
            """处理HEAD请求（用于检查服务器状态）"""
            logging.info("收到HEAD请求")
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
        
        def do_OPTIONS(self):
            """处理OPTIONS请求（用于CORS）"""
            logging.info("收到OPTIONS请求")
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, HEAD, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

        def do_POST(self):
            """处理POST请求"""
            try:
                # 获取请求内容长度
                content_length = int(self.headers['Content-Length'])
                # 读取请求内容
                post_data = self.rfile.read(content_length)
                # 解析JSON数据
                data = json.loads(post_data.decode('utf-8'))
                
                url = data.get('url', '')
                logging.info(f"收到下载请求: {url}")
                
                # 使用锁确保线程安全
                with self.server.url_receiver.processing_lock:
                    current_time = time()
                    
                    # 检查时间间隔
                    if self.server.url_receiver.request_times:
                        last_request_time = self.server.url_receiver.request_times[-1]
                        if current_time - last_request_time < self.server.url_receiver.min_interval:
                            logging.warning("请求过于频繁，已拦截")
                            self.send_response(429)
                            self.send_header('Content-type', 'application/json')
                            self.send_header('Access-Control-Allow-Origin', '*')
                            self.end_headers()
                            
                            response = {
                                'status': 'error',
                                'message': '请求过于频繁，请稍后再试'
                            }
                            self.wfile.write(json.dumps(response).encode('utf-8'))
                            return
                    
                    # 更新请求时间
                    self.server.url_receiver.request_times.append(current_time)
                    
                    # 处理URL
                    try:
                        self._process_url(url)
                    except Exception as e:
                        logging.error(f"处理URL时出错: {str(e)}", exc_info=True)
                        raise
                
            except Exception as e:
                logging.error(f"处理请求时出错: {str(e)}", exc_info=True)
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {'status': 'error', 'message': str(e)}
                self.wfile.write(json.dumps(response).encode('utf-8'))

        def _process_url(self, url: str):
            """处理URL请求"""
            try:
                if not url or not url.strip():
                    raise ValueError("无效的URL")
                
                # 使用 QTimer 发送信号
                self.server.url_receiver.emit_url_signal(url)
                
                # 返回成功响应
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {'status': 'success', 'message': 'URL received'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                logging.info("URL信号发送成功")
                
            except Exception as e:
                logging.error(f"处理URL时出错: {str(e)}", exc_info=True)
                raise

    def start(self):
        """启动服务器"""
        try:
            # 创建自定义的HTTPServer类
            class CustomHTTPServer(HTTPServer):
                def __init__(self, server_address, RequestHandlerClass, url_receiver):
                    super().__init__(server_address, RequestHandlerClass)
                    self.url_receiver = url_receiver
            
            # 创建服务器实例
            self.server = CustomHTTPServer(
                ('', self.port), 
                self.RequestHandler,
                self
            )
            
            logging.info(f"URL接收服务器启动在端口 {self.port}")
            print(f"服务器正在运行，按 Ctrl+C 停止...")
            
            # 使用线程运行服务器
            server_thread = threading.Thread(target=self.server.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
        except Exception as e:
            logging.error(f"启动服务器时出错: {str(e)}", exc_info=True)
            raise
    
    def stop(self):
        """停止服务器"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logging.info("URL接收服务器已停止")

# 测试代码
if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    receiver = URLReceiver()
    
    # 测试信号处理
    def handle_url(url):
        print(f"收到URL: {url}")
    
    receiver.url_received.connect(handle_url)
    
    try:
        logging.info("正在启动服务器...")
        receiver.start()
    except KeyboardInterrupt:
        receiver.stop()
        print("\n服务器已停止")
    except Exception as e:
        logging.error(f"服务器异常退出: {str(e)}", exc_info=True)
>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
