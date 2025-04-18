import os
import sqlite3
import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
                             QLineEdit, QDateTimeEdit, QTextEdit, QPushButton, QFileDialog,
                             QMessageBox, QProgressBar, QGridLayout, QDialog, QTabWidget,
                             QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import QDateTime, QTimer


class DataCollectionWidget(QWidget):
    """数据导入模块 - 一次性导入已有数据"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.conn = None  # 数据库连接
        self.cursor = None  # 数据库游标

    def initUI(self):
        layout = QVBoxLayout()

        # 添加实验信息组
        self.experiment_group = QGroupBox("试验信息")
        exp_layout = QGridLayout()

        exp_layout.addWidget(QLabel("试验编号:"), 0, 0)
        self.exp_id_input = QLineEdit()
        exp_layout.addWidget(self.exp_id_input, 0, 1)

        exp_layout.addWidget(QLabel("试验名称:"), 1, 0)
        self.exp_name_input = QLineEdit()
        exp_layout.addWidget(self.exp_name_input, 1, 1)

        exp_layout.addWidget(QLabel("开始时间:"), 2, 0)
        self.start_time_input = QDateTimeEdit(QDateTime.currentDateTime())
        self.start_time_input.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        exp_layout.addWidget(self.start_time_input, 2, 1)

        exp_layout.addWidget(QLabel("结束时间:"), 3, 0)
        self.end_time_input = QDateTimeEdit(QDateTime.currentDateTime())
        self.end_time_input.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        exp_layout.addWidget(self.end_time_input, 3, 1)

        exp_layout.addWidget(QLabel("描述:"), 4, 0)
        self.desc_input = QTextEdit()
        self.desc_input.setMaximumHeight(60)
        exp_layout.addWidget(self.desc_input, 4, 1)

        self.experiment_group.setLayout(exp_layout)
        layout.addWidget(self.experiment_group)

        # 添加数据源选择组
        self.data_source_group = QGroupBox("数据源导入")
        data_source_layout = QGridLayout()

        # 上位机数据 - 左上角(0,0)
        csv_group = QGroupBox("上位机数据")
        csv_layout = QGridLayout()

        csv_layout.addWidget(QLabel("数据文件夹:"), 0, 0)
        self.csv_data_path = QLineEdit()
        csv_layout.addWidget(self.csv_data_path, 0, 1)
        self.csv_browse_btn = QPushButton("浏览...")
        self.csv_browse_btn.clicked.connect(lambda: self.browse_folder(self.csv_data_path))
        csv_layout.addWidget(self.csv_browse_btn, 0, 2)

        # 显示所选文件夹路径
        self.csv_selected_folder = QLabel("未选择文件夹")
        csv_layout.addWidget(self.csv_selected_folder, 1, 0, 1, 3)

        csv_group.setLayout(csv_layout)
        data_source_layout.addWidget(csv_group, 0, 0)

        # 日志数据 - 右上角(0,1)
        log_group = QGroupBox("实验日志")
        log_layout = QGridLayout()

        log_layout.addWidget(QLabel("日志文件夹:"), 0, 0)
        self.log_data_path = QLineEdit()
        log_layout.addWidget(self.log_data_path, 0, 1)
        self.log_browse_btn = QPushButton("浏览...")
        self.log_browse_btn.clicked.connect(lambda: self.browse_folder(self.log_data_path))
        log_layout.addWidget(self.log_browse_btn, 0, 2)

        # 显示所选文件夹路径
        self.log_selected_folder = QLabel("未选择文件夹")
        log_layout.addWidget(self.log_selected_folder, 1, 0, 1, 3)

        log_group.setLayout(log_layout)
        data_source_layout.addWidget(log_group, 0, 1)

        # NVR设备数据 - 左下角(1,0)
        nvr_group = QGroupBox("NVR设备数据")
        nvr_layout = QGridLayout()

        nvr_layout.addWidget(QLabel("NVR数据文件夹:"), 0, 0)
        self.nvr_data_path = QLineEdit()
        nvr_layout.addWidget(self.nvr_data_path, 0, 1)
        self.nvr_browse_btn = QPushButton("浏览...")
        self.nvr_browse_btn.clicked.connect(lambda: self.browse_folder(self.nvr_data_path))
        nvr_layout.addWidget(self.nvr_browse_btn, 0, 2)

        # 显示所选文件夹路径
        self.nvr_selected_folder = QLabel("未选择文件夹")
        nvr_layout.addWidget(self.nvr_selected_folder, 1, 0, 1, 3)

        nvr_group.setLayout(nvr_layout)
        data_source_layout.addWidget(nvr_group, 1, 0)

        # 高速摄像机数据 - 右下角(1,1)
        camera_group = QGroupBox("高速摄像机数据")
        camera_layout = QGridLayout()

        camera_layout.addWidget(QLabel("摄像机数据文件夹:"), 0, 0)
        self.camera_data_path = QLineEdit()
        camera_layout.addWidget(self.camera_data_path, 0, 1)
        self.camera_browse_btn = QPushButton("浏览...")
        self.camera_browse_btn.clicked.connect(lambda: self.browse_folder(self.camera_data_path))
        camera_layout.addWidget(self.camera_browse_btn, 0, 2)

        # 显示所选文件夹路径
        self.camera_selected_folder = QLabel("未选择文件夹")
        camera_layout.addWidget(self.camera_selected_folder, 1, 0, 1, 3)

        camera_group.setLayout(camera_layout)
        data_source_layout.addWidget(camera_group, 1, 1)

        self.data_source_group.setLayout(data_source_layout)
        layout.addWidget(self.data_source_group)

        # 添加操作按钮（并排放置）
        btn_layout = QHBoxLayout()
        self.save_db_btn = QPushButton("保存数据")
        self.save_db_btn.clicked.connect(self.save_database)
        btn_layout.addWidget(self.save_db_btn)

        self.show_db_btn = QPushButton("显示数据库内容")
        self.show_db_btn.clicked.connect(self.show_database_content)
        btn_layout.addWidget(self.show_db_btn)

        layout.addLayout(btn_layout)

        # 进度条
        self.progress_group = QGroupBox("导入进度")
        progress_layout = QVBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪")
        progress_layout.addWidget(self.status_label)

        self.progress_group.setLayout(progress_layout)
        layout.addWidget(self.progress_group)

        # 放置弹性空间，把内容置顶
        layout.addStretch(1)
        self.setLayout(layout)

    def browse_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, "选择文件夹")
        if folder:
            line_edit.setText(folder)
            # 更新对应的文件夹显示标签
            if line_edit == self.csv_data_path:
                self.csv_selected_folder.setText(f"已选择: {folder}")
                self.scan_folder(folder, "csv")
            elif line_edit == self.log_data_path:
                self.log_selected_folder.setText(f"已选择: {folder}")
                self.scan_folder(folder, "log")
            elif line_edit == self.nvr_data_path:
                self.nvr_selected_folder.setText(f"已选择: {folder}")
                self.scan_folder(folder, "video")
            elif line_edit == self.camera_data_path:
                self.camera_selected_folder.setText(f"已选择: {folder}")
                self.scan_folder(folder, "video")

    def scan_folder(self, folder_path, data_type):
        """扫描文件夹并报告发现的文件"""
        if not os.path.exists(folder_path):
            return

        file_extensions = {
            "csv": [".csv", ".txt", ".dat"],
            "log": [".log", ".txt"],
            "video": [".mp4", ".avi", ".mov", ".mkv"]
        }

        extensions = file_extensions.get(data_type, [])
        found_files = []

        for root, _, files in os.walk(folder_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    found_files.append(os.path.join(root, file))

        # 显示找到的文件数量
        if data_type == "csv":
            self.csv_selected_folder.setText(f"已选择: {folder_path} (发现 {len(found_files)} 个数据文件)")
        elif data_type == "log":
            self.log_selected_folder.setText(f"已选择: {folder_path} (发现 {len(found_files)} 个日志文件)")
        elif data_type == "video" and self.nvr_data_path.text() == folder_path:
            self.nvr_selected_folder.setText(f"已选择: {folder_path} (发现 {len(found_files)} 个视频文件)")
        elif data_type == "video" and self.camera_data_path.text() == folder_path:
            self.camera_selected_folder.setText(f"已选择: {folder_path} (发现 {len(found_files)} 个视频文件)")

    def create_database_tables(self, db_path):
        """创建数据库表结构"""
        try:
            # 连接到SQLite数据库（如果不存在则创建）
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()

            # 创建实验信息表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY,
                name TEXT,
                start_time TEXT,
                end_time TEXT,
                description TEXT
            )
            ''')

            # 创建上位机数据表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT,
                timestamp TEXT,
                sensor_type TEXT,
                value REAL,
                file_source TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            )
            ''')

            # 创建视频数据表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT,
                device_id TEXT,
                file_path TEXT,
                duration INTEGER,
                file_size INTEGER,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            )
            ''')

            # 创建日志数据表
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT,
                timestamp TEXT,
                level TEXT,
                message TEXT,
                file_source TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            )
            ''')

            self.conn.commit()
            return True

        except sqlite3.Error as e:
            QMessageBox.critical(self, "数据库错误", f"创建数据库表失败: {str(e)}")
            if self.conn:
                self.conn.close()
                self.conn = None
            return False

    def save_experiment_info(self, experiment_id):
        """保存实验基本信息"""
        try:
            exp_name = self.exp_name_input.text()
            start_time = self.start_time_input.dateTime().toString("yyyy-MM-dd hh:mm:ss")
            end_time = self.end_time_input.dateTime().toString("yyyy-MM-dd hh:mm:ss")
            description = self.desc_input.toPlainText()

            self.cursor.execute('''
            INSERT INTO experiments (id, name, start_time, end_time, description)
            VALUES (?, ?, ?, ?, ?)
            ''', (experiment_id, exp_name, start_time, end_time, description))

            self.conn.commit()
            return True

        except sqlite3.Error as e:
            QMessageBox.critical(self, "数据库错误", f"保存实验信息失败: {str(e)}")
            return False

    def process_csv_data(self, experiment_id):
        """处理并保存上位机CSV数据"""
        folder_path = self.csv_data_path.text()
        if not folder_path or not os.path.exists(folder_path):
            return 0

        try:
            # 查找CSV文件
            csv_files = []
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(('.csv', '.txt', '.dat')):
                        csv_files.append(os.path.join(root, file))

            file_count = 0
            for file_path in csv_files:
                try:
                    with open(file_path, 'r') as f:
                        # 简单处理CSV文件，假设格式为: 时间,传感器类型,数值
                        lines = f.readlines()
                        for i, line in enumerate(lines):
                            if i == 0 and ',' in line:  # 跳过可能的标题行
                                continue

                            parts = line.strip().split(',')
                            if len(parts) >= 3:
                                try:
                                    timestamp = parts[0].strip()
                                    sensor_type = parts[1].strip()
                                    value = float(parts[2].strip())

                                    self.cursor.execute('''
                                    INSERT INTO sensor_data (experiment_id, timestamp, sensor_type, value, file_source)
                                    VALUES (?, ?, ?, ?, ?)
                                    ''', (experiment_id, timestamp, sensor_type, value, file_path))
                                except (ValueError, IndexError):
                                    continue  # 跳过不符合格式的行

                    file_count += 1
                    self.conn.commit()

                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {str(e)}")
                    continue

            return file_count

        except Exception as e:
            QMessageBox.warning(self, "数据处理警告", f"处理上位机数据时出现问题: {str(e)}")
            return 0

    def process_log_data(self, experiment_id):
        """处理并保存日志数据"""
        folder_path = self.log_data_path.text()
        if not folder_path or not os.path.exists(folder_path):
            return 0

        try:
            # 查找日志文件
            log_files = []
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(('.log', '.txt')):
                        log_files.append(os.path.join(root, file))

            file_count = 0
            for file_path in log_files:
                try:
                    with open(file_path, 'r') as f:
                        lines = f.readlines()
                        for line in lines:
                            # 尝试解析日志行，假设格式为: [时间] [级别] 消息
                            # 或者简单的格式如: 时间 级别 消息
                            parts = line.strip().split(' ', 2)
                            if len(parts) >= 3:
                                timestamp = parts[0].strip()
                                level = parts[1].strip()
                                message = parts[2].strip()

                                self.cursor.execute('''
                                INSERT INTO log_data (experiment_id, timestamp, level, message, file_source)
                                VALUES (?, ?, ?, ?, ?)
                                ''', (experiment_id, timestamp, level, message, file_path))

                    file_count += 1
                    self.conn.commit()

                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {str(e)}")
                    continue

            return file_count

        except Exception as e:
            QMessageBox.warning(self, "数据处理警告", f"处理日志数据时出现问题: {str(e)}")
            return 0

    def process_video_data(self, experiment_id):
        """处理并保存视频数据(NVR和高速摄像机)"""
        nvr_path = self.nvr_data_path.text()
        camera_path = self.camera_data_path.text()

        total_videos = 0

        # 处理NVR视频
        if nvr_path and os.path.exists(nvr_path):
            video_files = []
            for root, _, files in os.walk(nvr_path):
                for file in files:
                    if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                        video_files.append(os.path.join(root, file))

            for file_path in video_files:
                file_size = os.path.getsize(file_path)  # 获取文件大小（字节）
                # 这里简单假设视频时长（秒），实际应该使用视频库获取
                duration = file_size // 1000000  # 简单估算，每MB约1秒

                self.cursor.execute('''
                INSERT INTO video_data (experiment_id, device_id, file_path, duration, file_size)
                VALUES (?, ?, ?, ?, ?)
                ''', (experiment_id, "NVR", file_path, duration, file_size))

                total_videos += 1

        # 处理高速摄像机视频
        if camera_path and os.path.exists(camera_path):
            video_files = []
            for root, _, files in os.walk(camera_path):
                for file in files:
                    if file.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                        video_files.append(os.path.join(root, file))

            for file_path in video_files:
                file_size = os.path.getsize(file_path)
                duration = file_size // 2000000  # 高速摄像机文件通常更大，调整估算

                self.cursor.execute('''
                INSERT INTO video_data (experiment_id, device_id, file_path, duration, file_size)
                VALUES (?, ?, ?, ?, ?)
                ''', (experiment_id, "HighSpeedCamera", file_path, duration, file_size))

                total_videos += 1

        self.conn.commit()
        return total_videos

    def save_database(self):
        """保存数据库"""
        # 检查是否输入了试验编号
        if not self.exp_id_input.text():
            QMessageBox.warning(self, "错误", "请输入试验编号")
            return

        # 确认是否要继续，如果有空数据源
        if not all([self.csv_data_path.text(), self.log_data_path.text(),
                    self.nvr_data_path.text(), self.camera_data_path.text()]):
            reply = QMessageBox.question(self, "确认", "部分数据源文件夹未选择，是否继续?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return

        # 选择保存文件
        filename, _ = QFileDialog.getSaveFileName(self, "保存数据库", "", "数据库文件 (*.db)")
        if not filename:
            return

        # 确保文件名以.db结尾
        if not filename.lower().endswith('.db'):
            filename += '.db'

        # 设置进度条开始导入
        self.status_label.setText("正在创建数据库...")
        self.progress_bar.setValue(5)

        # 创建数据库和表结构
        if not self.create_database_tables(filename):
            self.status_label.setText("数据库创建失败")
            return

        # 获取实验ID
        experiment_id = self.exp_id_input.text()

        # 保存实验信息
        self.status_label.setText("正在保存实验信息...")
        self.progress_bar.setValue(10)
        if not self.save_experiment_info(experiment_id):
            self.close_database()
            self.status_label.setText("保存实验信息失败")
            return

        # 处理上位机数据
        self.status_label.setText("正在处理上位机数据...")
        self.progress_bar.setValue(30)
        csv_count = self.process_csv_data(experiment_id)

        # 处理日志数据
        self.status_label.setText("正在处理日志数据...")
        self.progress_bar.setValue(60)
        log_count = self.process_log_data(experiment_id)

        # 处理视频数据
        self.status_label.setText("正在处理视频数据...")
        self.progress_bar.setValue(80)
        video_count = self.process_video_data(experiment_id)

        # 完成并关闭数据库
        self.progress_bar.setValue(100)
        self.status_label.setText("数据导入完成")

        # 显示导入结果信息
        QMessageBox.information(self, "导入成功",
                                f"数据库创建成功!\n\n"
                                f"导入实验信息: 1条\n"
                                f"处理上位机数据文件: {csv_count}个\n"
                                f"处理日志文件: {log_count}个\n"
                                f"处理视频文件: {video_count}个\n\n"
                                f"数据库保存路径: {filename}")

        # 保持数据库连接打开，以便显示数据库内容

    def close_database(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def show_database_content(self):
        """显示数据库内容"""
        # 检查是否已经有导入的数据
        if not self.conn:
            QMessageBox.warning(self, "提示", "请先完成数据导入或打开现有数据库")
            return

        # 创建一个新窗口显示数据库内容
        self.db_viewer = QDialog(self)
        self.db_viewer.setWindowTitle("数据库内容")
        self.db_viewer.resize(800, 600)

        layout = QVBoxLayout()

        # 创建选项卡组件来展示不同类型的数据
        tabs = QTabWidget()

        # 实验信息选项卡
        exp_tab = QWidget()
        exp_layout = QVBoxLayout()
        exp_info = QTableWidget()
        exp_info.setColumnCount(5)
        exp_info.setHorizontalHeaderLabels(["试验编号", "试验名称", "开始时间", "结束时间", "描述"])

        # 查询实验信息
        try:
            self.cursor.execute("SELECT id, name, start_time, end_time, description FROM experiments")
            experiments = self.cursor.fetchall()

            for row_num, row_data in enumerate(experiments):
                exp_info.insertRow(row_num)
                for col_num, col_data in enumerate(row_data):
                    exp_info.setItem(row_num, col_num, QTableWidgetItem(str(col_data)))

        except sqlite3.Error:
            exp_info.setRowCount(0)

        exp_layout.addWidget(exp_info)
        exp_tab.setLayout(exp_layout)
        tabs.addTab(exp_tab, "实验信息")

        # 上位机数据选项卡
        csv_tab = QWidget()
        csv_layout = QVBoxLayout()
        csv_info = QTableWidget()
        csv_info.setColumnCount(5)
        csv_info.setHorizontalHeaderLabels(["ID", "实验编号", "时间", "数据类型", "数值"])

        # 查询上位机数据
        try:
            self.cursor.execute("SELECT id, experiment_id, timestamp, sensor_type, value FROM sensor_data LIMIT 200")
            sensor_data = self.cursor.fetchall()

            for row_num, row_data in enumerate(sensor_data):
                csv_info.insertRow(row_num)
                for col_num, col_data in enumerate(row_data):
                    csv_info.setItem(row_num, col_num, QTableWidgetItem(str(col_data)))

        except sqlite3.Error:
            csv_info.setRowCount(0)

        csv_layout.addWidget(csv_info)
        csv_tab.setLayout(csv_layout)
        tabs.addTab(csv_tab, "上位机数据")

        # 视频数据选项卡
        video_tab = QWidget()
        video_layout = QVBoxLayout()
        video_info = QTableWidget()
        video_info.setColumnCount(6)
        video_info.setHorizontalHeaderLabels(["ID", "实验编号", "设备ID", "文件路径", "时长(秒)", "文件大小(字节)"])

        # 查询视频数据
        try:
            self.cursor.execute("SELECT id, experiment_id, device_id, file_path, duration, file_size FROM video_data")
            video_data = self.cursor.fetchall()

            for row_num, row_data in enumerate(video_data):
                video_info.insertRow(row_num)
                for col_num, col_data in enumerate(row_data):
                    video_info.setItem(row_num, col_num, QTableWidgetItem(str(col_data)))

        except sqlite3.Error:
            video_info.setRowCount(0)

        video_layout.addWidget(video_info)
        video_tab.setLayout(video_layout)
        tabs.addTab(video_tab, "视频数据")

        # 日志数据选项卡
        log_tab = QWidget()
        log_layout = QVBoxLayout()
        log_info = QTableWidget()
        log_info.setColumnCount(5)
        log_info.setHorizontalHeaderLabels(["ID", "实验编号", "时间", "级别", "消息"])

        # 查询日志数据
        try:
            self.cursor.execute("SELECT id, experiment_id, timestamp, level, message FROM log_data LIMIT 200")
            log_data = self.cursor.fetchall()

            for row_num, row_data in enumerate(log_data):
                log_info.insertRow(row_num)
                for col_num, col_data in enumerate(row_data):
                    log_info.setItem(row_num, col_num, QTableWidgetItem(str(col_data)))

        except sqlite3.Error:
            log_info.setRowCount(0)

        log_layout.addWidget(log_info)
        log_tab.setLayout(log_layout)
        tabs.addTab(log_tab, "日志数据")

        layout.addWidget(tabs)

        # 添加关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.db_viewer.close)
        layout.addWidget(close_btn)

        self.db_viewer.setLayout(layout)
        self.db_viewer.exec_()

    def __del__(self):
        """析构函数，确保关闭数据库连接"""
        self.close_database()