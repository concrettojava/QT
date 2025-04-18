"""
回溯软件Demo - 基于PyQt5的试验数据回放系统
包含主要功能:
1. 数据收集
2. 试验过程回放
3. 数据导出
"""

import sys
import os
import csv
import json
import datetime
import sqlite3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel, QFileDialog, QTableWidget,
                            QTableWidgetItem, QComboBox, QLineEdit, QSlider, QGridLayout,
                            QGroupBox, QTextEdit, QDateTimeEdit, QCheckBox, QMessageBox,
                            QListWidget, QListWidgetItem, QSplitter, QDialog, QRadioButton,
                            QProgressBar,QInputDialog)
from PyQt5.QtCore import Qt, QDateTime, QTimer, QUrl
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
import pyqtgraph as pg  # 用于绘制曲线图

# 创建数据库连接函数
def create_connection(db_file):
    """创建与SQLite数据库的连接"""
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)
    return conn

# 创建表格函数
def create_tables(conn):
    """创建所需的表格"""
    try:
        cursor = conn.cursor()

        # 创建试验信息表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                experiment_id TEXT NOT NULL,
                start_time TEXT,
                end_time TEXT,
                description TEXT
            )
        ''')

        # 创建视频数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS video_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER,
                camera_id TEXT,
                file_path TEXT,
                start_time TEXT,
                end_time TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments (id)
            )
        ''')

        # 创建实时数据表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS realtime_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER,
                timestamp TEXT,
                data_type TEXT,
                value REAL,
                FOREIGN KEY (experiment_id) REFERENCES experiments (id)
            )
        ''')

        # 创建日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER,
                timestamp TEXT,
                log_level TEXT,
                message TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments (id)
            )
        ''')

        # 创建标注表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER,
                timestamp TEXT,
                annotation_type TEXT,
                coordinates TEXT,
                description TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments (id)
            )
        ''')

        # 创建标签表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id INTEGER,
                start_time TEXT,
                end_time TEXT,
                name TEXT,
                description TEXT,
                FOREIGN KEY (experiment_id) REFERENCES experiments (id)
            )
        ''')

        conn.commit()
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")


class DataCollectionWidget(QWidget):
    """数据导入模块 - 一次性导入已有数据"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

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
        self.desc_input.setMaximumHeight(20)
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
            elif line_edit == self.log_data_path:
                self.log_selected_folder.setText(f"已选择: {folder}")
            elif line_edit == self.nvr_data_path:
                self.nvr_selected_folder.setText(f"已选择: {folder}")
            elif line_edit == self.camera_data_path:
                self.camera_selected_folder.setText(f"已选择: {folder}")

    def save_database(self):
        """保存数据库"""
        # 检查是否选择了所有必要的文件夹
        if not self.exp_id_input.text():
            QMessageBox.warning(self, "错误", "请输入试验编号")
            return

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

        # 设置进度条开始导入
        self.status_label.setText("正在导入数据...")
        self.progress_bar.setValue(0)

        # 模拟导入过程
        total_steps = 10  # 模拟总步骤数
        self.total_steps = total_steps
        self.current_step = 0

        # 启动模拟导入进度
        self.import_timer = QTimer()
        self.import_timer.timeout.connect(self._simulate_import_progress)
        self.import_timer.start(300)  # 每300毫秒更新一次

    def _simulate_import_progress(self):
        """模拟导入进度"""
        self.current_step += 1
        progress = int((self.current_step / self.total_steps) * 100)
        self.progress_bar.setValue(progress)
        self.status_label.setText(f"正在导入数据... {progress}%")

        if self.current_step >= self.total_steps:
            self.import_timer.stop()
            self.status_label.setText("数据导入完成")
            QMessageBox.information(self, "成功", "所有数据已成功导入到数据库中")

    def show_database_content(self):
        """显示数据库内容"""
        # 检查是否已经有导入的数据
        if self.progress_bar.value() < 100:
            QMessageBox.warning(self, "提示", "请先完成数据导入")
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
        exp_info = QTextEdit()
        exp_info.setReadOnly(True)
        exp_info.setText(f"""
        试验编号: {self.exp_id_input.text()}
        试验名称: {self.exp_name_input.text()}
        开始时间: {self.start_time_input.dateTime().toString("yyyy-MM-dd hh:mm:ss")}
        结束时间: {self.end_time_input.dateTime().toString("yyyy-MM-dd hh:mm:ss")}
        描述: {self.desc_input.toPlainText()}
        """)
        exp_layout.addWidget(exp_info)
        exp_tab.setLayout(exp_layout)
        tabs.addTab(exp_tab, "实验信息")

        # 上位机数据选项卡
        csv_tab = QWidget()
        csv_layout = QVBoxLayout()
        csv_info = QTableWidget()
        csv_info.setColumnCount(3)
        csv_info.setHorizontalHeaderLabels(["时间", "数据类型", "数值"])

        # 模拟生成一些数据
        start_time = self.start_time_input.dateTime().toPyDateTime()
        for i in range(20):
            row = csv_info.rowCount()
            csv_info.insertRow(row)
            time_str = (start_time + datetime.timedelta(minutes=i * 5)).strftime("%Y-%m-%d %H:%M:%S")
            csv_info.setItem(row, 0, QTableWidgetItem(time_str))
            csv_info.setItem(row, 1, QTableWidgetItem(f"传感器_{i % 5 + 1}"))
            csv_info.setItem(row, 2, QTableWidgetItem(f"{20 + i * 0.5:.2f}"))

        csv_layout.addWidget(csv_info)
        csv_tab.setLayout(csv_layout)
        tabs.addTab(csv_tab, "上位机数据")

        # 视频数据选项卡
        video_tab = QWidget()
        video_layout = QVBoxLayout()
        video_info = QTableWidget()
        video_info.setColumnCount(3)
        video_info.setHorizontalHeaderLabels(["设备ID", "文件路径", "时长(秒)"])

        # 从NVR和高速摄像机文件夹添加视频信息
        if self.nvr_data_path.text():
            row = video_info.rowCount()
            video_info.insertRow(row)
            video_info.setItem(row, 0, QTableWidgetItem("NVR_Main"))
            video_info.setItem(row, 1, QTableWidgetItem(f"{self.nvr_data_path.text()}/video_01.mp4"))
            video_info.setItem(row, 2, QTableWidgetItem("3600"))

        if self.camera_data_path.text():
            row = video_info.rowCount()
            video_info.insertRow(row)
            video_info.setItem(row, 0, QTableWidgetItem("Camera_1"))
            video_info.setItem(row, 1, QTableWidgetItem(f"{self.camera_data_path.text()}/highspeed_01.mp4"))
            video_info.setItem(row, 2, QTableWidgetItem("1800"))

        video_layout.addWidget(video_info)
        video_tab.setLayout(video_layout)
        tabs.addTab(video_tab, "视频数据")

        # 日志数据选项卡
        log_tab = QWidget()
        log_layout = QVBoxLayout()
        log_info = QTableWidget()
        log_info.setColumnCount(3)
        log_info.setHorizontalHeaderLabels(["时间", "级别", "消息"])

        # 模拟生成一些日志
        log_levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
        log_messages = [
            "系统初始化",
            "开始数据采集",
            "传感器连接成功",
            "数据异常，重试中",
            "恢复正常",
            "视频流中断",
            "重新连接设备",
            "数据采集完成"
        ]

        for i in range(10):
            row = log_info.rowCount()
            log_info.insertRow(row)
            time_str = (start_time + datetime.timedelta(minutes=i * 10)).strftime("%Y-%m-%d %H:%M:%S")
            log_info.setItem(row, 0, QTableWidgetItem(time_str))
            log_info.setItem(row, 1, QTableWidgetItem(log_levels[i % len(log_levels)]))
            log_info.setItem(row, 2, QTableWidgetItem(log_messages[i % len(log_messages)]))

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
class PlaybackWidget(QWidget):
    """试验过程回放模块"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_conn = None
        self.current_experiment_id = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # 添加数据库加载部分
        db_layout = QHBoxLayout()
        db_layout.addWidget(QLabel("数据库文件:"))
        self.db_path = QLineEdit()
        db_layout.addWidget(self.db_path)
        self.db_browse_btn = QPushButton("浏览...")
        self.db_browse_btn.clicked.connect(self.browse_database)
        db_layout.addWidget(self.db_browse_btn)
        self.load_db_btn = QPushButton("加载")
        self.load_db_btn.clicked.connect(self.load_database)
        db_layout.addWidget(self.load_db_btn)

        layout.addLayout(db_layout)

        # 试验选择下拉框
        exp_layout = QHBoxLayout()
        exp_layout.addWidget(QLabel("选择试验:"))
        self.exp_combo = QComboBox()
        self.exp_combo.currentIndexChanged.connect(self.experiment_selected)
        exp_layout.addWidget(self.exp_combo)

        layout.addLayout(exp_layout)

        # 主要显示区域分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧面板 - 视频回放
        left_panel = QWidget()
        left_layout = QVBoxLayout()

        # 视频播放组件
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(500)
        left_layout.addWidget(self.video_widget)

        # 媒体播放器
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)

        # 播放控制
        controls_layout = QHBoxLayout()

        self.play_btn = QPushButton("播放")
        self.play_btn.clicked.connect(self.play_video)
        controls_layout.addWidget(self.play_btn)

        self.pause_btn = QPushButton("暂停")
        self.pause_btn.clicked.connect(self.pause_video)
        controls_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_video)
        controls_layout.addWidget(self.stop_btn)

        left_layout.addLayout(controls_layout)

        # 进度滑块
        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.sliderMoved.connect(self.set_position)
        left_layout.addWidget(self.progress_slider)

        # 时间显示
        self.time_label = QLabel("00:00:00 / 00:00:00")
        left_layout.addWidget(self.time_label)
        left_layout.addStretch(1)
        left_panel.setLayout(left_layout)

        # 右侧面板 - 数据显示和标注
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        # 数据展示选项卡
        data_tabs = QTabWidget()

        # 实时数据选项卡
        self.realtime_tab = QWidget()
        realtime_layout = QVBoxLayout()

        # 数据曲线图
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', '数值')
        self.plot_widget.setLabel('bottom', '时间')
        self.plot_widget.showGrid(x=True, y=True)
        realtime_layout.addWidget(self.plot_widget)

        self.realtime_tab.setLayout(realtime_layout)

        # 日志选项卡
        self.log_tab = QWidget()
        log_layout = QVBoxLayout()

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(["时间", "级别", "消息"])
        self.log_table.horizontalHeader().setStretchLastSection(True)
        log_layout.addWidget(self.log_table)

        self.log_tab.setLayout(log_layout)

        # 标注选项卡
        self.annotation_tab = QWidget()
        annotation_layout = QVBoxLayout()

        annotation_form = QGridLayout()
        annotation_form.addWidget(QLabel("标注类型:"), 0, 0)
        self.annotation_type = QComboBox()
        self.annotation_type.addItems(["点", "线", "矩形", "椭圆", "多边形"])
        annotation_form.addWidget(self.annotation_type, 0, 1)

        annotation_form.addWidget(QLabel("描述:"), 1, 0)
        self.annotation_desc = QLineEdit()
        annotation_form.addWidget(self.annotation_desc, 1, 1)

        self.add_annotation_btn = QPushButton("添加标注")
        self.add_annotation_btn.clicked.connect(self.add_annotation)
        annotation_form.addWidget(self.add_annotation_btn, 2, 1)

        annotation_layout.addLayout(annotation_form)

        # 标注列表
        annotation_layout.addWidget(QLabel("标注列表:"))
        self.annotation_list = QListWidget()
        self.annotation_list.itemClicked.connect(self.annotation_selected)
        annotation_layout.addWidget(self.annotation_list)

        self.annotation_tab.setLayout(annotation_layout)

        # 标签选项卡
        self.tag_tab = QWidget()
        tag_layout = QVBoxLayout()

        tag_form = QGridLayout()
        tag_form.addWidget(QLabel("标签名称:"), 0, 0)
        self.tag_name = QLineEdit()
        tag_form.addWidget(self.tag_name, 0, 1)

        tag_form.addWidget(QLabel("开始时间:"), 1, 0)
        self.tag_start = QDateTimeEdit()
        self.tag_start.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        tag_form.addWidget(self.tag_start, 1, 1)

        tag_form.addWidget(QLabel("结束时间:"), 2, 0)
        self.tag_end = QDateTimeEdit()
        self.tag_end.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        tag_form.addWidget(self.tag_end, 2, 1)

        tag_form.addWidget(QLabel("描述:"), 3, 0)
        self.tag_desc = QLineEdit()
        tag_form.addWidget(self.tag_desc, 3, 1)

        self.add_tag_btn = QPushButton("添加标签")
        self.add_tag_btn.clicked.connect(self.add_tag)
        tag_form.addWidget(self.add_tag_btn, 4, 1)

        tag_layout.addLayout(tag_form)

        # 标签列表
        tag_layout.addWidget(QLabel("标签列表:"))
        self.tag_list = QListWidget()
        self.tag_list.itemClicked.connect(self.tag_selected)
        tag_layout.addWidget(self.tag_list)

        self.tag_tab.setLayout(tag_layout)

        # 添加选项卡
        data_tabs.addTab(self.realtime_tab, "实时数据")
        data_tabs.addTab(self.log_tab, "日志")
        data_tabs.addTab(self.annotation_tab, "标注")
        data_tabs.addTab(self.tag_tab, "标签")

        right_layout.addWidget(data_tabs)

        right_panel.setLayout(right_layout)

        # 添加面板到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)

        # 设置初始分割比例
        splitter.setSizes([400, 400])

        layout.addWidget(splitter)

        self.setLayout(layout)

    def browse_database(self):
        filename, _ = QFileDialog.getOpenFileName(self, "选择数据库文件", "", "数据库文件 (*.db)")
        if filename:
            self.db_path.setText(filename)

    def load_database(self):
        # 加载数据库
        db_file = self.db_path.text()
        if not db_file:
            QMessageBox.warning(self, "错误", "请选择数据库文件")
            return

        self.db_conn = create_connection(db_file)
        if self.db_conn is None:
            QMessageBox.critical(self, "错误", "无法连接到数据库")
            return

        # 加载试验列表
        self.load_experiments()

    def load_experiments(self):
        if self.db_conn is None:
            return

        cursor = self.db_conn.cursor()
        cursor.execute("SELECT id, experiment_id, name FROM experiments")
        experiments = cursor.fetchall()

        self.exp_combo.clear()
        for exp in experiments:
            self.exp_combo.addItem(f"{exp[1]} - {exp[2]}", exp[0])

        if experiments:
            self.exp_combo.setCurrentIndex(0)

    def experiment_selected(self, index):
        if index < 0 or self.db_conn is None:
            return

        self.current_experiment_id = self.exp_combo.currentData()

        # 加载视频数据
        self.load_video_data()

        # 加载实时数据
        self.load_realtime_data()

        # 加载日志数据
        self.load_log_data()

        # 加载标注
        self.load_annotations()

        # 加载标签
        self.load_tags()

    def load_video_data(self):
        if self.db_conn is None or self.current_experiment_id is None:
            return

        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT file_path FROM video_data WHERE experiment_id = ?",
            (self.current_experiment_id,)
        )

        video_data = cursor.fetchone()
        if video_data and os.path.exists(video_data[0]):
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(video_data[0])))
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
        else:
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            QMessageBox.warning(self, "警告", "未找到视频数据或文件不存在")

    def load_realtime_data(self):
        if self.db_conn is None or self.current_experiment_id is None:
            return

        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT timestamp, data_type, value FROM realtime_data WHERE experiment_id = ? ORDER BY timestamp",
            (self.current_experiment_id,)
        )

        data = cursor.fetchall()
        if data:
            # 解析时间和数值数据
            timestamps = []
            values = []

            for row in data:
                # 解析时间戳为 datetime 对象
                timestamp = datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
                # 将 datetime 转换为从开始时间的秒数
                if not timestamps:  # 第一个点
                    start_time = timestamp
                    timestamps.append(0)
                else:
                    delta = (timestamp - start_time).total_seconds()
                    timestamps.append(delta)

                values.append(row[2])

            # 绘制曲线
            self.plot_widget.clear()
            plot_pen = pg.mkPen(color=(255, 0, 0), width=2)
            self.plot_widget.plot(timestamps, values, pen=plot_pen, symbol='o', symbolSize=5, symbolBrush=(255, 0, 0))

    def load_log_data(self):
        if self.db_conn is None or self.current_experiment_id is None:
            return

        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT timestamp, log_level, message FROM logs WHERE experiment_id = ? ORDER BY timestamp",
            (self.current_experiment_id,)
        )

        logs = cursor.fetchall()

        # 清空表格
        self.log_table.setRowCount(0)

        # 添加日志数据
        for row_idx, log in enumerate(logs):
            self.log_table.insertRow(row_idx)
            self.log_table.setItem(row_idx, 0, QTableWidgetItem(log[0]))
            self.log_table.setItem(row_idx, 1, QTableWidgetItem(log[1]))
            self.log_table.setItem(row_idx, 2, QTableWidgetItem(log[2]))

        # 调整列宽
        self.log_table.resizeColumnsToContents()

    def load_annotations(self):
        if self.db_conn is None or self.current_experiment_id is None:
            return

        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT id, timestamp, annotation_type, description FROM annotations WHERE experiment_id = ? ORDER BY timestamp",
            (self.current_experiment_id,)
        )

        annotations = cursor.fetchall()

        # 清空列表
        self.annotation_list.clear()

        # 添加标注数据
        for annotation in annotations:
            item = QListWidgetItem(f"{annotation[1]} - {annotation[2]}: {annotation[3]}")
            item.setData(Qt.UserRole, annotation[0])  # 保存标注ID作为用户数据
            self.annotation_list.addItem(item)

    def load_tags(self):
        if self.db_conn is None or self.current_experiment_id is None:
            return

        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT id, start_time, end_time, name, description FROM tags WHERE experiment_id = ? ORDER BY start_time",
            (self.current_experiment_id,)
        )

        tags = cursor.fetchall()

        # 清空列表
        self.tag_list.clear()

        # 添加标签数据
        for tag in tags:
            item = QListWidgetItem(f"{tag[1]} - {tag[2]}: {tag[3]}")
            item.setData(Qt.UserRole, tag[0])  # 保存标签ID作为用户数据
            self.tag_list.addItem(item)

    def play_video(self):
        self.media_player.play()

    def pause_video(self):
        self.media_player.pause()

    def stop_video(self):
        self.media_player.stop()

    def set_position(self, position):
        self.media_player.setPosition(position)

    def add_annotation(self):
        if self.db_conn is None or self.current_experiment_id is None:
            QMessageBox.warning(self, "错误", "请先选择试验")
            return

        # 获取当前视频时间点
        current_time = QDateTime.currentDateTime()  # 实际项目中应该获取视频当前时间点
        timestamp = current_time.toString("yyyy-MM-dd hh:mm:ss")

        # 获取标注信息
        annotation_type = self.annotation_type.currentText()
        description = self.annotation_desc.text()

        if not description:
            QMessageBox.warning(self, "错误", "请输入标注描述")
            return

        # 保存标注信息到数据库
        # 这里简化了图形标注的坐标处理，实际项目中应该根据真实坐标保存
        cursor = self.db_conn.cursor()
        cursor.execute('''
            INSERT INTO annotations (experiment_id, timestamp, annotation_type, coordinates, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            self.current_experiment_id,
            timestamp,
            annotation_type,
            json.dumps({"x": 100, "y": 100}),  # 示例坐标
            description
        ))

        self.db_conn.commit()

        # 刷新标注列表
        self.load_annotations()

        # 清空输入
        self.annotation_desc.clear()

        QMessageBox.information(self, "成功", "已添加标注")

    def annotation_selected(self, item):
        # 获取选中的标注ID
        annotation_id = item.data(Qt.UserRole)

        # 查询标注详情
        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT timestamp, annotation_type, coordinates, description FROM annotations WHERE id = ?",
            (annotation_id,)
        )

        annotation = cursor.fetchone()
        if annotation:
            # 跳转到对应的视频时间点
            # 实际项目中应该根据时间戳定位视频
            QMessageBox.information(self, "标注详情",
                f"时间: {annotation[0]}\n类型: {annotation[1]}\n描述: {annotation[3]}")

    def add_tag(self):
        if self.db_conn is None or self.current_experiment_id is None:
            QMessageBox.warning(self, "错误", "请先选择试验")
            return

        # 获取标签信息
        name = self.tag_name.text()
        start_time = self.tag_start.dateTime().toString("yyyy-MM-dd hh:mm:ss")
        end_time = self.tag_end.dateTime().toString("yyyy-MM-dd hh:mm:ss")
        description = self.tag_desc.text()

        if not name:
            QMessageBox.warning(self, "错误", "请输入标签名称")
            return

        # 保存标签信息到数据库
        cursor = self.db_conn.cursor()
        cursor.execute('''
            INSERT INTO tags (experiment_id, start_time, end_time, name, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            self.current_experiment_id,
            start_time,
            end_time,
            name,
            description
        ))

        self.db_conn.commit()

        # 刷新标签列表
        self.load_tags()

        # 清空输入
        self.tag_name.clear()
        self.tag_desc.clear()

        QMessageBox.information(self, "成功", "已添加标签")

    def tag_selected(self, item):
        # 获取选中的标签ID
        tag_id = item.data(Qt.UserRole)

        # 查询标签详情
        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT start_time, end_time, name, description FROM tags WHERE id = ?",
            (tag_id,)
        )

        tag = cursor.fetchone()
        if tag:
            # 跳转到标签开始时间点
            # 实际项目中应该根据时间戳定位视频
            QMessageBox.information(self, "标签详情",
                f"开始时间: {tag[0]}\n结束时间: {tag[1]}\n名称: {tag[2]}\n描述: {tag[3]}")


class DataExportWidget(QWidget):
    """数据导出模块"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_conn = None
        self.current_experiment_id = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # 添加数据库加载部分
        db_layout = QHBoxLayout()
        db_layout.addWidget(QLabel("数据库文件:"))
        self.db_path = QLineEdit()
        db_layout.addWidget(self.db_path)
        self.db_browse_btn = QPushButton("浏览...")
        self.db_browse_btn.clicked.connect(self.browse_database)
        db_layout.addWidget(self.db_browse_btn)
        self.load_db_btn = QPushButton("加载")
        self.load_db_btn.clicked.connect(self.load_database)
        db_layout.addWidget(self.load_db_btn)

        layout.addLayout(db_layout)

        # 试验选择下拉框
        exp_layout = QHBoxLayout()
        exp_layout.addWidget(QLabel("选择试验:"))
        self.exp_combo = QComboBox()
        self.exp_combo.currentIndexChanged.connect(self.experiment_selected)
        exp_layout.addWidget(self.exp_combo)

        layout.addLayout(exp_layout)

        # 创建视频导出和数据导出的选项卡
        export_tabs = QTabWidget()

        # 视频导出选项卡
        self.video_export_tab = QWidget()
        video_layout = QVBoxLayout()

        # 相机选择
        video_layout.addWidget(QLabel("选择相机:"))
        self.camera_list = QListWidget()
        self.camera_list.setSelectionMode(QListWidget.MultiSelection)
        video_layout.addWidget(self.camera_list)

        # 时间范围
        time_range_group = QGroupBox("时间范围")
        time_range_layout = QGridLayout()

        time_range_layout.addWidget(QLabel("开始时间:"), 0, 0)
        self.video_start_time = QDateTimeEdit()
        self.video_start_time.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        time_range_layout.addWidget(self.video_start_time, 0, 1)

        time_range_layout.addWidget(QLabel("结束时间:"), 1, 0)
        self.video_end_time = QDateTimeEdit()
        self.video_end_time.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        time_range_layout.addWidget(self.video_end_time, 1, 1)

        time_range_group.setLayout(time_range_layout)
        video_layout.addWidget(time_range_group)

        # 导出格式
        format_group = QGroupBox("导出格式")
        format_layout = QVBoxLayout()

        self.mp4_format = QRadioButton("MP4")
        self.mp4_format.setChecked(True)
        format_layout.addWidget(self.mp4_format)

        self.avi_format = QRadioButton("AVI")
        format_layout.addWidget(self.avi_format)

        self.mov_format = QRadioButton("MOV")
        format_layout.addWidget(self.mov_format)

        format_group.setLayout(format_layout)
        video_layout.addWidget(format_group)

        # 导出按钮
        self.export_video_btn = QPushButton("导出视频")
        self.export_video_btn.clicked.connect(self.export_video)
        video_layout.addWidget(self.export_video_btn)

        # 状态标签
        self.video_export_status = QLabel("就绪")
        video_layout.addWidget(self.video_export_status)

        self.video_export_tab.setLayout(video_layout)

        # 数据导出选项卡
        self.data_export_tab = QWidget()
        data_layout = QVBoxLayout()

        # 数据类型选择
        data_layout.addWidget(QLabel("选择数据类型:"))
        self.data_type_list = QListWidget()
        self.data_type_list.setSelectionMode(QListWidget.MultiSelection)
        data_layout.addWidget(self.data_type_list)

        # 时间范围
        data_time_range_group = QGroupBox("时间范围")
        data_time_range_layout = QGridLayout()

        data_time_range_layout.addWidget(QLabel("开始时间:"), 0, 0)
        self.data_start_time = QDateTimeEdit()
        self.data_start_time.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        data_time_range_layout.addWidget(self.data_start_time, 0, 1)

        data_time_range_layout.addWidget(QLabel("结束时间:"), 1, 0)
        self.data_end_time = QDateTimeEdit()
        self.data_end_time.setDisplayFormat("yyyy-MM-dd hh:mm:ss")
        data_time_range_layout.addWidget(self.data_end_time, 1, 1)

        data_time_range_group.setLayout(data_time_range_layout)
        data_layout.addWidget(data_time_range_group)

        # 导出选项
        export_options_group = QGroupBox("导出选项")
        export_options_layout = QVBoxLayout()

        self.include_headers = QCheckBox("包含列头")
        self.include_headers.setChecked(True)
        export_options_layout.addWidget(self.include_headers)

        self.include_timestamp = QCheckBox("包含时间戳")
        self.include_timestamp.setChecked(True)
        export_options_layout.addWidget(self.include_timestamp)

        export_options_group.setLayout(export_options_layout)
        data_layout.addWidget(export_options_group)

        # 导出按钮
        self.export_data_btn = QPushButton("导出数据")
        self.export_data_btn.clicked.connect(self.export_data)
        data_layout.addWidget(self.export_data_btn)

        # 状态标签
        self.data_export_status = QLabel("就绪")
        data_layout.addWidget(self.data_export_status)

        self.data_export_tab.setLayout(data_layout)

        # 添加选项卡
        export_tabs.addTab(self.video_export_tab, "视频导出")
        export_tabs.addTab(self.data_export_tab, "数据导出")

        layout.addWidget(export_tabs)

        self.setLayout(layout)

    def browse_database(self):
        filename, _ = QFileDialog.getOpenFileName(self, "选择数据库文件", "", "数据库文件 (*.db)")
        if filename:
            self.db_path.setText(filename)

    def load_database(self):
        # 加载数据库
        db_file = self.db_path.text()
        if not db_file:
            QMessageBox.warning(self, "错误", "请选择数据库文件")
            return

        self.db_conn = create_connection(db_file)
        if self.db_conn is None:
            QMessageBox.critical(self, "错误", "无法连接到数据库")
            return

        # 加载试验列表
        self.load_experiments()

    def load_experiments(self):
        if self.db_conn is None:
            return

        cursor = self.db_conn.cursor()
        cursor.execute("SELECT id, experiment_id, name FROM experiments")
        experiments = cursor.fetchall()

        self.exp_combo.clear()
        for exp in experiments:
            self.exp_combo.addItem(f"{exp[1]} - {exp[2]}", exp[0])

        if experiments:
            self.exp_combo.setCurrentIndex(0)

    def experiment_selected(self, index):
        if index < 0 or self.db_conn is None:
            return

        self.current_experiment_id = self.exp_combo.currentData()

        # 加载相机列表
        self.load_cameras()

        # 加载数据类型列表
        self.load_data_types()

        # 加载时间范围
        self.load_time_range()

    def load_cameras(self):
        if self.db_conn is None or self.current_experiment_id is None:
            return

        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT DISTINCT camera_id FROM video_data WHERE experiment_id = ?",
            (self.current_experiment_id,)
        )

        cameras = cursor.fetchall()

        self.camera_list.clear()
        for camera in cameras:
            self.camera_list.addItem(camera[0])

    def load_data_types(self):
        if self.db_conn is None or self.current_experiment_id is None:
            return

        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT DISTINCT data_type FROM realtime_data WHERE experiment_id = ?",
            (self.current_experiment_id,)
        )

        data_types = cursor.fetchall()

        self.data_type_list.clear()
        for data_type in data_types:
            self.data_type_list.addItem(data_type[0])

    def load_time_range(self):
        if self.db_conn is None or self.current_experiment_id is None:
            return

        cursor = self.db_conn.cursor()
        cursor.execute(
            "SELECT start_time, end_time FROM experiments WHERE id = ?",
            (self.current_experiment_id,)
        )

        experiment = cursor.fetchone()
        if experiment:
            start_time = QDateTime.fromString(experiment[0], "yyyy-MM-dd hh:mm:ss")
            end_time = QDateTime.fromString(experiment[1], "yyyy-MM-dd hh:mm:ss")

            self.video_start_time.setDateTime(start_time)
            self.video_end_time.setDateTime(end_time)
            self.data_start_time.setDateTime(start_time)
            self.data_end_time.setDateTime(end_time)

    def export_video(self):
        if self.db_conn is None or self.current_experiment_id is None:
            QMessageBox.warning(self, "错误", "请先选择试验")
            return

        # 获取选中的相机
        selected_cameras = []
        for i in range(self.camera_list.count()):
            item = self.camera_list.item(i)
            if item.isSelected():
                selected_cameras.append(item.text())

        if not selected_cameras:
            QMessageBox.warning(self, "错误", "请至少选择一个相机")
            return

        # 获取时间范围
        start_time = self.video_start_time.dateTime().toString("yyyy-MM-dd hh:mm:ss")
        end_time = self.video_end_time.dateTime().toString("yyyy-MM-dd hh:mm:ss")

        # 获取导出格式
        export_format = "mp4"
        if self.avi_format.isChecked():
            export_format = "avi"
        elif self.mov_format.isChecked():
            export_format = "mov"

        # 选择导出目录
        export_dir = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if not export_dir:
            return

        # 模拟导出过程
        self.video_export_status.setText("正在导出视频...")

        # 实际项目中需要实现真实的视频导出逻辑
        # 这里仅模拟导出过程
        QTimer.singleShot(2000, lambda: self._complete_video_export(export_dir, selected_cameras, export_format))

    def _complete_video_export(self, export_dir, cameras, export_format):
        # 模拟导出完成
        for camera in cameras:
            export_path = os.path.join(export_dir, f"{camera}.{export_format}")
            # 实际项目中，这里应该实际创建视频文件

        self.video_export_status.setText(f"导出完成! 导出目录: {export_dir}")
        QMessageBox.information(self, "成功", f"已将{len(cameras)}个相机的视频导出到: {export_dir}")

    def export_data(self):
        if self.db_conn is None or self.current_experiment_id is None:
            QMessageBox.warning(self, "错误", "请先选择试验")
            return

        # 获取选中的数据类型
        selected_data_types = []
        for i in range(self.data_type_list.count()):
            item = self.data_type_list.item(i)
            if item.isSelected():
                selected_data_types.append(item.text())

        if not selected_data_types:
            QMessageBox.warning(self, "错误", "请至少选择一种数据类型")
            return

        # 获取时间范围
        start_time = self.data_start_time.dateTime().toString("yyyy-MM-dd hh:mm:ss")
        end_time = self.data_end_time.dateTime().toString("yyyy-MM-dd hh:mm:ss")

        # 获取导出选项
        include_headers = self.include_headers.isChecked()
        include_timestamp = self.include_timestamp.isChecked()

        # 选择导出文件
        export_file, _ = QFileDialog.getSaveFileName(self, "保存CSV文件", "", "CSV文件 (*.csv)")
        if not export_file:
            return

        # 导出CSV文件
        self.data_export_status.setText("正在导出数据...")

        try:
            with open(export_file, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)

                # 写入表头
                if include_headers:
                    headers = []
                    if include_timestamp:
                        headers.append("时间戳")
                    headers.extend(selected_data_types)
                    writer.writerow(headers)

                # 查询数据
                for data_type in selected_data_types:
                    cursor = self.db_conn.cursor()
                    cursor.execute(
                        """SELECT timestamp, value 
                        FROM realtime_data 
                        WHERE experiment_id = ? AND data_type = ? AND timestamp BETWEEN ? AND ?
                        ORDER BY timestamp""",
                        (self.current_experiment_id, data_type, start_time, end_time)
                    )

                    data = cursor.fetchall()

                    # 写入数据
                    for row in data:
                        if include_timestamp:
                            writer.writerow([row[0], row[1]])
                        else:
                            writer.writerow([row[1]])

            self.data_export_status.setText(f"导出完成! 文件: {export_file}")
            QMessageBox.information(self, "成功", f"数据已导出到: {export_file}")

        except Exception as e:
            self.data_export_status.setText(f"导出失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("回溯软件 Demo")
        self.setGeometry(100, 100, 1200, 800)
        # self.adjustSize()
        # 创建中心部件
        central_widget = QTabWidget()

        # 添加三个功能模块
        self.data_collection_widget = DataCollectionWidget()
        central_widget.addTab(self.data_collection_widget, "数据收集")

        self.playback_widget = PlaybackWidget()
        central_widget.addTab(self.playback_widget, "试验过程回放")

        self.data_export_widget = DataExportWidget()
        central_widget.addTab(self.data_export_widget, "数据导出")

        self.setCentralWidget(central_widget)


def main():
    app = QApplication(sys.argv)

    # 设置样式
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()