<<<<<<< HEAD
import os
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Tuple
import traceback
import time

class DatabaseManager:
    # 使用单例模式确保只有一个数据库实例
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化数据库管理器"""
        if self._initialized:
            return
            
        # 创建数据目录
        self.data_dir = os.path.join("data", "db")
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 数据库文件路径
        self.db_path = os.path.join(self.data_dir, "downloader.db")
        
        # 初始化数据库表
        self._init_database()
        self._initialized = True
    
    def _init_database(self):
        """初始化数据库表结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 下载中的任务表，预先创建32个线程进度字段
                create_downloading_table = """
                    CREATE TABLE IF NOT EXISTS downloading (
                        file_name TEXT PRIMARY KEY,
                        url TEXT,
                        status TEXT,
                        time TIMESTAMP,
                        size INTEGER,
                        threads INTEGER,
                        progress REAL,
                        thread_id INTEGER,
                        """
                
                # 动态添加32个进度字段
                progress_columns = ",\n                        ".join([f"progress_{i} REAL DEFAULT 0" for i in range(32)])
                create_downloading_table += progress_columns + "\n                    )"
                
                conn.execute(create_downloading_table)
                
                # 已完成的任务表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS downloaded (
                        file_name TEXT PRIMARY KEY,
                        url TEXT,
                        status TEXT,
                        time TIMESTAMP,
                        size INTEGER,
                        threads INTEGER,
                        progress REAL,
                        thread_id INTEGER,
                        save_path TEXT
                    )
                """)
                
                # 等待中的任务表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS waiting (
                        file_name TEXT PRIMARY KEY,
                        url TEXT,
                        status TEXT,
                        time TIMESTAMP,
                        size INTEGER,
                        threads INTEGER,
                        progress REAL,
                        thread_id INTEGER
                    )
                """)
                
                # 错误任务表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS error (
                        file_name TEXT PRIMARY KEY,
                        url TEXT,
                        status TEXT,
                        sign TEXT,
                        time TIMESTAMP,
                        error TEXT
                    )
                """)
                
                # 添加分片信息表
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS chunks (
                        chunk_id INTEGER,
                        file_name TEXT,
                        url TEXT,
                        start INTEGER,
                        end INTEGER,
                        size INTEGER,
                        status TEXT,
                        PRIMARY KEY (file_name, chunk_id)
                    )
                """)
                
                # 创建索引
                conn.execute("CREATE INDEX IF NOT EXISTS idx_downloading_status ON downloading(status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_downloaded_time ON downloaded(time)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_waiting_time ON waiting(time)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_error_time ON error(time)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_filename ON chunks(file_name)")
                
                # 创建下载状态表

            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_downloading_status ON downloading(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_downloaded_time ON downloaded(time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_waiting_time ON waiting(time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_error_time ON error(time)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_filename ON chunks(file_name)")
            
            # 创建下载状态表

        except Exception as e:
            print(f"数据库初始化失败: {str(e)}")

    def is_filename_exists(self, filename: str) -> bool:
        """检查文件名是否已存在"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 1 FROM downloading WHERE file_name = ?
                    UNION ALL
                    SELECT 1 FROM waiting WHERE file_name = ?
                """, (filename, filename))
                return cursor.fetchone() is not None
        except Exception as e:
            return False

    def add_error_task(self, url: str, file_name: str, error_msg: str, sign: str) -> bool:
        """添加错误任务记录
        Args:
            url: 任务URL
            file_name: 文件名
            error_msg: 错误信息
            sign: 错误标识
        Returns:
            bool: 是否添加成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 使用 INSERT OR REPLACE 而不是简单的 INSERT
                conn.execute("""
                    INSERT OR REPLACE INTO error 
                    (file_name, url, status, sign, time, error)
                    VALUES (?, ?, '错误', ?, ?, ?)
                """, (
                    file_name,
                    url,
                    sign,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    error_msg
                ))
                conn.commit()
                return True
        except Exception as e:
            # 如果是主键冲突错误，我们认为这是正常的情况
            if "UNIQUE constraint failed" in str(e):
                return True
            return False

    def get_downloading_count(self) -> int:
        """获取正在下载的任务数量"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM downloading")
                return cursor.fetchone()[0]
        except Exception as e:
            return 0

    def add_downloading_task(self, task_data: Dict[str, Any]) -> bool:
        """添加下载任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO downloading 
                    (file_name, url, status, time)
                    VALUES (?, ?, ?, ?)
                """, (
                    task_data['file_name'],
                    task_data['url'],
                    task_data.get('status', '下载中'),
                    task_data.get('time', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                ))
                conn.commit()
                return True
        except Exception as e:
            return False

    def add_waiting_task(self, task_data: Dict[str, Any]) -> bool:
        """添加等待任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO waiting 
                    (file_name, url, status, time)
                    VALUES (?, ?, ?, ?)
                """, (
                    task_data['file_name'],
                    task_data['url'],
                    task_data.get('status', '等待中'),
                    task_data.get('time', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                ))
                conn.commit()
                return True
        except Exception as e:
            return False

    def add_thread_progress_column(self, thread_id: int, thread_count: int):
        """
        为指定的下载任务添加二级线程进度字段
        Args:
            thread_id: 主线程ID
            thread_count: 二级线程数量
        """
       
        with sqlite3.connect(self.db_path) as conn:
            # 获取现有列信息
            cursor = conn.execute(f"PRAGMA table_info(downloading)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            # 添加缺失的进度列
            for i in range(thread_count):
                column_name = f"progress_{i}"
                if column_name not in existing_columns:
                    conn.execute(f"ALTER TABLE downloading ADD COLUMN {column_name} REAL DEFAULT 0")
                
            conn.commit()
                

    
    def get_connection(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def close(self):
        """关闭数据库连接"""
        if hasattr(self, '_conn'):
            self._conn.close()

    def get_downloading_tasks(self) -> List[Dict[str, Any]]:
        """获取所有下载中的任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM downloading")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            return []

    def update_thread_id(self, file_name: str, thread_id: int) -> bool:
        """更新任务的线程ID
        Args:
            file_name: 文件名（主键）
            thread_id: 分配的线程ID
        Returns:
            bool: 是否更新成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE downloading 
                    SET thread_id = ? 
                    WHERE file_name = ?
                """, (thread_id, file_name))
                conn.commit()
                return True
        except Exception as e:
            return False

    def get_task_by_url(self, url: str) -> Dict[str, Any]:
        """根据URL获取任务信息
        Args:
            url: 任务URL
        Returns:
            Dict: 任务信息，包含file_name等
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM downloading 
                    WHERE url = ?
                """, (url,))
                result = cursor.fetchone()
                return dict(result) if result else {}
        except Exception as e:
            return {}

    def assign_thread_id(self, url: str, thread_id: int, file_name: str) -> bool:
        """分配线程ID给任务
        Args:
            url: 任务URL
            thread_id: 要分配的线程ID
            file_name: 文件名
        Returns:
            bool: 是否分配成功
        """
        try:
            
            with sqlite3.connect(self.db_path) as conn:
                # 先检查任务是否存在
                cursor = conn.execute("""
                    SELECT file_name, thread_id, status 
                    FROM downloading 
                    WHERE url = ? AND file_name = ?
                """, (url, file_name))
                
                result = cursor.fetchone()
                
                if result:
                    current_file_name, current_thread_id, current_status = result
                
                # 更新线程ID
                cursor = conn.execute("""
                    UPDATE downloading 
                    SET thread_id = ?,
                        time = ?
                    WHERE url = ? AND file_name = ?
                """, (
                    thread_id,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    url,
                    file_name
                ))
                conn.commit()
                
                rows_affected = cursor.rowcount
                
                if rows_affected > 0:
                    
                    # 验证更新结果
                    cursor = conn.execute("""
                        SELECT thread_id 
                        FROM downloading 
                        WHERE url = ? AND file_name = ?
                    """, (url, file_name))
                    verify_result = cursor.fetchone()
                    
                    return True
                else:
                    return False
                
        except Exception as e:
            traceback.print_exc()
            return False

    def update_file_size(self, url: str, thread_id: int, file_size: int) -> bool:
        """更新文件大小到downloading表
        Args:
            url: 任务URL
            thread_id: 线程ID
            file_size: 文件大小
        Returns:
            bool: 是否更新成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE downloading 
                    SET size = ? 
                    WHERE url = ? AND thread_id = ?
                """, (file_size, url, thread_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            return False

    def remove_downloading_task(self, url: str) -> bool:
        """从downloading表中移除任务
        Args:
            url: 任务URL
        Returns:
            bool: 是否移除成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM downloading WHERE url = ?", (url,))
                conn.commit()
                return True
        except Exception as e:
            return False

    def move_next_waiting_to_downloading(self) -> bool:
        """将等待队列中的第一个任务移动到下载队列"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 获取第一个等待任务
                cursor = conn.execute("SELECT * FROM waiting ORDER BY time ASC LIMIT 1")
                task = cursor.fetchone()
                
                if task:
                    # 删除等待任务
                    conn.execute("DELETE FROM waiting WHERE file_name = ?", (task[0],))
                    
                    # 添加到下载队列
                    conn.execute("""
                        INSERT INTO downloading 
                        (file_name, url, status, time)
                        VALUES (?, ?, '下载中', ?)
                    """, (task[0], task[1], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    
                    conn.commit()
                    return True
                return False
        except Exception as e:
            return False

    def get_task_progress(self, url: str) -> float:
        """获取任务的下载进度
        Args:
            url: 任务URL
        Returns:
            float: 下载进度（0-100）
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT progress 
                    FROM downloading 
                    WHERE url = ?
                """, (url,))
                result = cursor.fetchone()
                return float(result[0]) if result and result[0] is not None else 0
        except Exception as e:
            return 0

    def update_thread_count(self, url: str, thread_count: int) -> bool:
        """更新任务的线程数
        Args:
            url: 任务URL
            thread_count: 线程数量
        Returns:
            bool: 是否更新成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE downloading 
                    SET threads = ? 
                    WHERE url = ?
                """, (thread_count, url))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            return False

    def get_thread_count(self, url: str) -> int:
        """获取任务的线程数
        Args:
            url: 任务URL
        Returns:
            int: 线程数量，如果未找到则返回0
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT threads 
                    FROM downloading 
                    WHERE url = ?
                """, (url,))
                result = cursor.fetchone()
                return int(result[0]) if result and result[0] is not None else 0
        except Exception as e:
            return 0

    def get_task_size(self, url: str, thread_id: int) -> int:
        """获取任务的文件大小
        Args:
            url: 任务URL
            thread_id: 线程ID
        Returns:
            int: 文件大小（字节）
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT size 
                    FROM downloading 
                    WHERE url = ? AND thread_id = ?
                """, (url, thread_id))
                result = cursor.fetchone()
                return int(result[0]) if result and result[0] is not None else 0
        except Exception as e:
            return 0

    def save_chunk_info(self, url: str, chunks_info: List[Dict[str, Any]]) -> bool:
        """保存分片信息到数据库
        Args:
            url: 任务URL
            chunks_info: 分片信息列表
        Returns:
            bool: 是否保存成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 先删除旧的分片信息
                file_name = chunks_info[0].get('file_name') if chunks_info else None
                if file_name:
                    conn.execute("DELETE FROM chunks WHERE file_name = ?", (file_name,))
                
                # 插入新的分片信息
                conn.executemany("""
                    INSERT OR REPLACE INTO chunks 
                    (chunk_id, file_name, url, start, end, size, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, [(
                    chunk["chunk_id"],
                    chunk["file_name"],
                    chunk["url"],
                    chunk["start"],
                    chunk["end"],
                    chunk["size"],
                    chunk.get("status", "pending")
                ) for chunk in chunks_info])
                
                conn.commit()
                return True
        except Exception as e:
            # 如果是主键冲突错误，我们认为这是正常的情况
            if "UNIQUE constraint failed" in str(e):
                return True
            return False

    def get_chunks_by_filename(self, file_name: str) -> List[Dict[str, Any]]:
        """获取指定文件名的所有分片信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM chunks 
                    WHERE file_name = ?
                    ORDER BY chunk_id
                """, (file_name,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            return []

    def move_task_to_downloaded(self, file_name: str, save_path: str = "") -> bool:
        """将任务从downloading移动到downloaded表
        Args:
            file_name: 文件名（主键）
            save_path: 文件保存路径
        Returns:
            bool: 是否移动成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 获取任务信息
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM downloading WHERE file_name = ?", (file_name,))
                task = cursor.fetchone()
                
                if task:
                    # 插入到downloaded表
                    task_dict = dict(task)
                    task_dict['status'] = '已完成'
                    task_dict['time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    task_dict['save_path'] = save_path
                    
                    
                    conn.execute("""
                        INSERT INTO downloaded 
                        (file_name, url, status, time, size, threads, progress, thread_id, save_path)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        task_dict['file_name'],
                        task_dict['url'],
                        task_dict['status'],
                        task_dict['time'],
                        task_dict.get('size'),
                        task_dict.get('threads'),
                        task_dict.get('progress'),
                        task_dict.get('thread_id'),
                        save_path
                    ))
                    
                    # 从downloading表删除
                    conn.execute("DELETE FROM downloading WHERE file_name = ?", (file_name,))
                    conn.commit()
                    return True
                
            return False
            
        except Exception as e:
            traceback.print_exc() 
            return False

    def update_task_status(self, file_name: str, status: str) -> bool:
        """
        更新任务状态
        
        Args:
            file_name: 文件名
            status: 新状态
            
        Returns:
            bool: 是否更新成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE downloading 
                    SET status = ? 
                    WHERE file_name = ?
                """, (status, file_name))
                
                conn.commit()
                
                success = cursor.rowcount > 0
                return success
                
        except Exception as e:
            import traceback
            return False

    def get_downloading_task_details(self, url: str = None) -> List[Dict[str, Any]]:
        """获取下载中任务的详细信息，包括二级线程进度
        Args:
            url: 可选，指定任务的URL
        Returns:
            List[Dict]: 任务详细信息列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # 获取所有列名，包括二级线程进度列
                cursor = conn.execute("PRAGMA table_info(downloading)")
                columns = [row[1] for row in cursor.fetchall()]
                progress_columns = [col for col in columns if col.startswith('progress_')]
                
                # 构建查询语句
                query = f"""
                    SELECT *, 
                    {', '.join(progress_columns)} 
                    FROM downloading
                    {' WHERE url = ?' if url else ''}
                    ORDER BY time DESC
                """
                
                # 执行查询
                cursor = conn.execute(query, (url,) if url else ())
                tasks = []
                
                for row in cursor:
                    task_dict = dict(row)
                    # 添加二级线程进度信息
                    task_dict['thread_progress'] = {
                        col: task_dict[col]
                        for col in progress_columns
                        if task_dict[col] is not None
                    }
                    tasks.append(task_dict)
                    
                return tasks
                
        except Exception as e:
            return []

    def get_task_thread_progress(self, url: str) -> Dict[str, float]:
        """获取指定任务的所有二级线程进度
        Args:
            url: 任务URL
        Returns:
            Dict[str, float]: 二级线程进度字典 {thread_id: progress}
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 获取所有进度列
                cursor = conn.execute("PRAGMA table_info(downloading)")
                progress_columns = [
                    row[1] for row in cursor.fetchall() 
                    if row[1].startswith('progress_')
                ]
                
                if not progress_columns:
                    return {}
                    
                # 构建查询
                query = f"""
                    SELECT {', '.join(progress_columns)}
                    FROM downloading
                    WHERE url = ?
                """
                
                cursor = conn.execute(query, (url,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        col: row[i] 
                        for i, col in enumerate(progress_columns)
                        if row[i] is not None
                    }
                return {}
                
        except Exception as e:
            return {}

    def get_task_by_filename(self, file_name: str) -> Dict[str, Any]:
        """根据文件名获取任务信息
        Args:
            file_name: 文件名
        Returns:
            Dict: 任务信息字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM downloading 
                    WHERE file_name = ?
                """, (file_name,))
                row = cursor.fetchone()
                return dict(row) if row else {}
        except Exception as e:
            return {}

    def get_downloaded_file_path(self, file_name: str) -> str:
        """获取已下载文件的保存路径
        Args:
            file_name: 文件名
        Returns:
            str: 文件保存路径，如果未找到返回空字符串
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT save_path FROM downloaded 
                    WHERE file_name = ? AND status = '已完成'
                """, (file_name,))
                row = cursor.fetchone()
                if row and row[0] and os.path.exists(row[0]):
                    return row[0]
                return ""
        except Exception as e:
            return ""

    def remove_downloaded_task(self, file_name: str) -> bool:
        """从downloaded表中移除任务
        Args:
            file_name: 文件名
        Returns:
            bool: 是否移除成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM downloaded 
                    WHERE file_name = ?
                """, (file_name,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            return False

    def get_tasks_by_type(self, task_type: str) -> List[Dict[str, Any]]:
        """获取指定类型的任务列表
        Args:
            task_type: 任务类型（'downloading', 'waiting', 'downloaded', 'error'）
        Returns:
            List[Dict]: 任务列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                if task_type == "error":
                    cursor = conn.execute("""
                        SELECT url, error as error_msg, file_name, time 
                        FROM error 
                        ORDER BY time DESC
                    """)
                else:
                    # 获取表的所有列名
                    cursor = conn.execute(f"PRAGMA table_info({task_type})")
                    columns = [row[1] for row in cursor.fetchall()]
                    
                    # 构建查询语句，包含所有列
                    query = f"""
                        SELECT {', '.join(columns)}
                        FROM {task_type}
                        ORDER BY time DESC
                    """
                    cursor = conn.execute(query)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            return []

    def get_task_by_type_and_url(self, task_type: str, url: str) -> Dict[str, Any]:
        """获取指定类型和URL的任务信息
        Args:
            task_type: 任务类型（'downloading', 'waiting', 'downloaded', 'error'）
            url: 任务URL
        Returns:
            Dict: 任务信息字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(f"""
                    SELECT * FROM {task_type}
                    WHERE url = ?
                """, (url,))
                row = cursor.fetchone()
                return dict(row) if row else {}
        except Exception as e:
            return {}

    def remove_task_by_type(self, task_type: str, file_name: str) -> bool:
        """从指定类型的表中删除任务
        Args:
            task_type: 任务类型（'downloading', 'waiting', 'downloaded', 'error'）
            file_name: 文件名（主键）
        Returns:
            bool: 是否删除成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(f"""
                    DELETE FROM {task_type}
                    WHERE file_name = ?
                """, (file_name,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            return False

    def get_task_by_type_and_filename(self, task_type: str, file_name: str) -> Dict[str, Any]:
        """获取指定类型和文件名的任务信息
        Args:
            task_type: 任务类型（'downloading', 'waiting', 'downloaded', 'error'）
            file_name: 文件名
        Returns:
            Dict: 任务信息字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(f"""
                    SELECT * FROM {task_type}
                    WHERE file_name = ?
                """, (file_name,))
                row = cursor.fetchone()
                return dict(row) if row else {}
        except Exception as e:
            return {}

    def get_task_by_thread_id(self, thread_id: int) -> Dict[str, Any]:
        """根据线程ID获取任务信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM downloading
                    WHERE thread_id = ?
                """, (thread_id,))
                row = cursor.fetchone()
                return dict(row) if row else {}
        except Exception as e:
            return {}

    def get_task_progress_by_filename(self, file_name: str) -> float:
        """
        根据文件名获取任务进度
        Args:
            file_name: 文件名
        Returns:
            float: 进度值（0-100）
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT progress 
                    FROM downloading 
                    WHERE file_name = ?
                """, (file_name,))
                result = cursor.fetchone()
                if result and result[0] is not None:
                    return float(result[0])
                return 0.0
        except Exception as e:
            return 0.0

    def get_thread_count_by_filename(self, file_name: str) -> int:
        """
        根据文件名获取任务的线程数
        Args:
            file_name: 文件名
        Returns:
            int: 线程数量，如果未找到则返回0
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 检查数据库中的所有任务
                cursor = conn.execute("SELECT file_name, threads, status FROM downloading")
                all_tasks = cursor.fetchall()
                
                # 检查文件名是否存在
                cursor = conn.execute("""
                    SELECT EXISTS(
                        SELECT 1 
                        FROM downloading 
                        WHERE file_name = ?
                    )
                """, (file_name,))
                exists = cursor.fetchone()[0]
                
                if not exists:
                    return 0

                # 获取线程数
                cursor = conn.execute("""
                    SELECT threads, status
                    FROM downloading 
                    WHERE file_name = ?
                """, (file_name,))
                result = cursor.fetchone()
                
                if result:
                    threads, status = result
                    if threads is not None:
                        return int(threads)
                    else:
                        return 0
                else:
                    return 0
                
        except Exception as e:
            return 0

    def update_task_status_by_filename(self, file_name: str, status: str) -> bool:
        """根据文件名更新任务状态
        Args:
            file_name: 文件名
            status: 新状态
        Returns:
            bool: 是否更新成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE downloading 
                    SET status = ? 
                    WHERE file_name = ?
                """, (status, file_name))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            return False

    def delete_chunks_by_filename(self, file_name: str) -> bool:
        """删除指定文件名的所有分片数据
        Args:
            file_name: 文件名
        Returns:
            bool: 是否删除成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM chunks 
                    WHERE file_name = ?
                """, (file_name,))
                conn.commit()
                
                # 返回是否有记录被删除
                deleted_count = cursor.rowcount
                if deleted_count > 0:
                    return True
                else:
                    return False
                
        except Exception as e:
            traceback.print_exc()
            return False

    def update_progress_by_filename(self, file_name: str, progress: float) -> bool:
        """根据文件名更新downloading表中的进度值
        Args:
            file_name: 文件名
            progress: 进度值（0-100）
        Returns:
            bool: 是否更新成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 确保进度值在0-100范围内
                progress = max(0, min(100, float(progress)))
                
                cursor = conn.execute("""
                    UPDATE downloading 
                    SET progress = ?,
                        time = ?
                    WHERE file_name = ?
                """, (
                    progress,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    file_name
                ))
                conn.commit()
                
                # 检查是否有记录被更新
                if cursor.rowcount > 0:
                    return True
                else:
                    return False
                
        except Exception as e:
            traceback.print_exc()  # 打印详细错误信息
            return False

    def check_download_status(self, file_name: str) -> Tuple[int, bool]:
        """
        根据文件名查询downloading表中的progress和thread_id字段
        
        Args:
            file_name: 文件名
            
        Returns:
            Tuple[int, bool]: (thread_id, status)
            - thread_id: 线程ID，如果未找到返回0
            - status: True表示需要重新下载（progress为0或不存在），False表示已有下载进度
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT thread_id, progress 
                    FROM downloading 
                    WHERE file_name = ?
                """, (file_name,))
                
                result = cursor.fetchone()
                
                if result is None:
                    # 记录不存在
                    return 0, True
                    
                thread_id, progress = result
                
                # 如果thread_id为None，设为0
                thread_id = thread_id if thread_id is not None else 0
                
                # 如果progress为None或0，返回True表示需要重新下载
                need_redownload = progress is None or progress == 0
                
                return thread_id, need_redownload
                
        except Exception as e:
            return 0, True

    def clear_thread_id(self, file_name: str) -> bool:
        """
        根据文件名清除downloading表中的thread_id字段数据
        
        Args:
            file_name: 文件名
            
        Returns:
            bool: 是否清除成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    UPDATE downloading 
                    SET thread_id = NULL 
                    WHERE file_name = ?
                """, (file_name,))
                
                conn.commit()
                
                # 检查是否有记录被更新
                if cursor.rowcount > 0:
                    return True
                else:
                    return False
                
        except Exception as e:
            traceback.print_exc()  # 打印详细错误信息
            return False

    def get_threads_by_filename(self, file_name: str) -> int:
        """
        根据文件名查询downloading表中的threads字段
        
        Args:
            file_name: 文件名
            
        Returns:
            int: 线程数量，如果未找到或出错则返回0
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT threads 
                    FROM downloading 
                    WHERE file_name = ?
                """, (file_name,))
                
                result = cursor.fetchone()
                
                if result and result[0] is not None:
                    return int(result[0])
                else:
                    return 0
                
        except Exception as e:
            import traceback
            return 0

    

    def check_downloading_status(self, file_name: str) -> bool:
        """
        检查文件是否处于暂停状态
        
        Args:
            file_name: 文件名
            
        Returns:
            bool: True表示处于暂停状态，False表示非暂停状态
        """
        try:
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT status 
                    FROM downloading 
                    WHERE file_name = ? AND status = '暂停中'
                """, (file_name,))
                
                result = cursor.fetchone()
                is_paused = result is not None
                return is_paused
                
        except Exception as e:
            traceback.print_exc()
            return False

    def check_file_exists_in_all_tables(self, filename: str) -> bool:
        """
        检查文件名是否在downloading/downloaded/waiting表中存在
        
        Args:
            filename: 文件名
            
        Returns:
            bool: True表示文件名不存在，False表示文件名已存在
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT 1 
                    FROM (
                        SELECT file_name FROM downloading
                        UNION ALL
                        SELECT file_name FROM downloaded
                        UNION ALL
                        SELECT file_name FROM waiting
                    ) 
                    WHERE file_name = ?
                """, (filename,))
                
                result = cursor.fetchone()
                return result is None  # 如果没有找到记录返回True，找到了返回False
                
        except Exception as e:
            traceback.print_exc()
            return False  # 发生错误时返回False，认为文件可能存在

    def remove_downloading_by_filename(self, file_name: str) -> bool:
        """根据文件名从downloading表中删除任务
        
        Args:
            file_name: 文件名
            
        Returns:
            bool: 是否删除成功
        """
        try:
            
            with sqlite3.connect(self.db_path) as conn:
                # 先检查任务是否存在
                cursor = conn.execute("""
                    SELECT file_name, url, status 
                    FROM downloading 
                    WHERE file_name = ?
                """, (file_name,))
                
                result = cursor.fetchone()
                if result:
                    current_file_name, url, status = result

                    # 执行删除操作
                    cursor = conn.execute("""
                        DELETE FROM downloading 
                        WHERE file_name = ?
                    """, (file_name,))
                    conn.commit()
                    
                    rows_affected = cursor.rowcount
                    
                    if rows_affected > 0:
                        return True
                    else:
                        return False
                else:
                    return False
            
        except Exception as e:
            traceback.print_exc()
            return False

    def remove_waiting_task(self, file_name: str) -> bool:
        """从waiting表中删除任务
        
        Args:
            file_name: 文件名
            
        Returns:
            bool: 是否删除成功
        """
        try:
            
            with sqlite3.connect(self.db_path) as conn:
                # 先检查任务是否存在
                cursor = conn.execute("""
                    SELECT file_name, url 
                    FROM waiting 
                    WHERE file_name = ?
                """, (file_name,))
                
                result = cursor.fetchone()
                if result:
                    current_file_name, url = result
                    
                    # 执行删除操作
                    cursor = conn.execute("""
                        DELETE FROM waiting 
                        WHERE file_name = ?
                    """, (file_name,))
                    conn.commit()
                    
                    rows_affected = cursor.rowcount
                    
                    if rows_affected > 0:
                        return True
                    else:
                        return False
                else:
                    return False
            
        except Exception as e:
            traceback.print_exc()
            return False

    def clear_all_tables(self) -> bool:
        """删除所有表中的数据
        Returns:
            bool: 是否成功删除所有数据
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                # 删除所有表中的数据
                tables = ['downloading', 'downloaded', 'waiting', 'error', 'chunks']
                
                for table in tables:
                    conn.execute(f"DELETE FROM {table}")
                
                # 提交事务
                conn.commit()
                
                # 执行VACUUM来回收空间
                conn.execute("VACUUM")
                
                return True
                
        except Exception as e:
            traceback.print_exc()
            return False

    
=======
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
>>>>>>> 2d5d9d9cf12d707f2c5354c07328162bc648e520
