from PyQt6.QtWidgets import QMenu, QMessageBox
from PyQt6.QtCore import pyqtSignal, QObject
import os
import subprocess
import json  # 添加json导入

class CompletedMenu(QObject):
    # 定义信号
    open_file_location = pyqtSignal(str)  # 发送文件路径
    delete_local_file = pyqtSignal(str)   # 发送文件路径
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.menu = QMenu(parent)
        self.setup_menu()
        
    def setup_menu(self):
        """设置菜单项"""
        # 打开文件位置
        open_action = self.menu.addAction("打开文件位置")
        open_action.triggered.connect(lambda: self._open_file_location(self._current_file_path))
        
        # 添加分隔线
        self.menu.addSeparator()
        
        # 删除本地文件
        delete_action = self.menu.addAction("删除本地文件")
        delete_action.triggered.connect(lambda: self._delete_local_file(self._current_file_path))
        
        # 设置菜单样式
        self.menu.setStyleSheet("""
            QMenu {
                background-color: #2b2b2b;
                color: #ecf0f1;
                border: 1px solid #3498db;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 2px;
                margin: 2px 5px;
            }
            QMenu::item:selected {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
                color: white;
            }
            QMenu::separator {
                height: 1px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2ecc71,
                    stop:1 #3498db
                );
                margin: 5px 15px;
            }
            QMenu::icon {
                padding-left: 10px;
            }
        """)
    
    def show_menu(self, pos, file_path: str):
        """显示菜单"""
        self._current_file_path = file_path
        self.menu.popup(pos)
    
    def _open_file_location(self, file_path: str):
        """打开文件所在位置"""
        try:
            if os.path.exists(file_path):
                # 在Windows中打开文件夹并选中文件
                subprocess.run(['explorer', '/select,', os.path.normpath(file_path)])
            else:
                QMessageBox.warning(
                    self.menu,
                    "错误",
                    "文件不存在！",
                    QMessageBox.StandardButton.Ok
                )
        except Exception as e:
            QMessageBox.critical(
                self.menu,
                "错误",
                f"打开文件位置失败: {str(e)}",
                QMessageBox.StandardButton.Ok
            )
    
    def _delete_local_file(self, file_path: str):
        """删除本地文件和相关记录"""
        try:
            if os.path.exists(file_path):
                reply = QMessageBox.question(
                    self.menu,
                    "确认删除",
                    "确定要删除此文件吗？此操作不可恢复！",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # 删除本地文件
                    os.remove(file_path)
                    
                    # 删除downloaded.json中的记录
                    self._remove_downloaded_record(file_path)
                    
                    QMessageBox.information(
                        self.menu,
                        "成功",
                        "文件已删除！",
                        QMessageBox.StandardButton.Ok
                    )
                    # 发送信号通知更新UI
                    self.delete_local_file.emit(file_path)
            else:
                QMessageBox.warning(
                    self.menu,
                    "错误",
                    "文件不存在！",
                    QMessageBox.StandardButton.Ok
                )
        except Exception as e:
            QMessageBox.critical(
                self.menu,
                "错误",
                f"删除文件失败: {str(e)}",
                QMessageBox.StandardButton.Ok
            )

    def _remove_downloaded_record(self, file_path: str):
        """从downloaded.json中删除对应记录"""
        try:
            downloaded_path = os.path.join("data", "queuemanagement", "downloaded.json")
            if not os.path.exists(downloaded_path):
                return
            
            # 规范化要删除的文件路径
            normalized_file_path = os.path.normpath(file_path)
            print(f"准备删除路径: {normalized_file_path}")  # 调试信息
            
            # 读取现有数据
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
                
                # 打印当前记录，用于调试
                print("当前记录:")
                for item in downloaded_list:
                    print(f"记录路径: {item.get('save_path')}")
                
                # 过滤掉要删除的记录，使用规范化路径进行比较
                new_list = []
                for item in downloaded_list:
                    item_path = os.path.normpath(item.get('save_path', ''))
                    if item_path != normalized_file_path:
                        new_list.append(item)
                    else:
                        print(f"找到并删除记录: {item_path}")  # 调试信息
                
                # 检查是否有记录被删除
                if len(new_list) == len(downloaded_list):
                    print("警告：未找到匹配的记录")
                else:
                    print(f"成功删除记录，剩余记录数: {len(new_list)}")
                
                # 保存更新后的数据
                with open(downloaded_path, 'w', encoding='utf-8') as f:
                    json.dump(new_list, f, ensure_ascii=False, indent=4)
                
            except json.JSONDecodeError as e:
                print(f"读取downloaded.json失败: {str(e)}")
            
        except Exception as e:
            print(f"删除下载记录失败: {str(e)}")
            import traceback
            print(traceback.format_exc())  # 打印完整错误堆栈
