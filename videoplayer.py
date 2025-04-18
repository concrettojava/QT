import os
import sqlite3
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QGroupBox, QLabel, QPushButton, QFileDialog,
                             QProgressBar, QSizePolicy,QSlider, QMessageBox, QGridLayout)
from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget


class VideoPlayerWidget(QWidget):
    """视频播放模块 - 从数据库加载和播放视频文件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.conn = None  # 数据库连接
        self.cursor = None  # 数据库游标
        self.videos = []  # 视频信息列表
        self.players = []  # 视频播放器列表
        self.video_widgets = []  # 视频显示组件列表
        self.current_position = 0  # 当前播放位置（毫秒）
        self.max_duration = 0  # 最长视频时长（毫秒）
        self.timer = QTimer()  # 定时器，用于更新进度
        self.timer.timeout.connect(self.update_progress)
        self.timer.setInterval(500)  # 每500毫秒更新一次进度
        self.playing = False  # 播放状态

    def initUI(self):
        main_layout = QVBoxLayout()

        # 数据库加载区域
        db_group = QGroupBox("数据库加载")
        db_layout = QHBoxLayout()

        self.db_path_label = QLabel("未选择数据库")
        db_layout.addWidget(self.db_path_label)

        load_db_btn = QPushButton("加载数据库")
        load_db_btn.clicked.connect(self.load_database)
        db_layout.addWidget(load_db_btn)

        db_group.setLayout(db_layout)
        main_layout.addWidget(db_group)
        # main_layout.addStretch()

        # 视频区域容器
        self.videos_container = QGroupBox("视频播放")
        self.videos_layout = QGridLayout()
        self.videos_container.setLayout(self.videos_layout)
        self.videos_container.setSizePolicy(QSizePolicy.Preferred,QSizePolicy.Expanding)
        main_layout.addWidget(self.videos_container)

        # 播放控制
        control_group = QGroupBox("播放控制")
        control_layout = QVBoxLayout()

        # 进度条
        progress_layout = QHBoxLayout()
        self.position_label = QLabel("00:00")
        progress_layout.addWidget(self.position_label)

        self.progress_slider = QSlider(Qt.Horizontal)
        self.progress_slider.setRange(0, 100)
        self.progress_slider.sliderMoved.connect(self.set_position)
        progress_layout.addWidget(self.progress_slider)

        self.duration_label = QLabel("00:00")
        progress_layout.addWidget(self.duration_label)

        control_layout.addLayout(progress_layout)

        # 播放按钮
        buttons_layout = QHBoxLayout()

        self.play_btn = QPushButton("播放")
        self.play_btn.clicked.connect(self.play_videos)
        buttons_layout.addWidget(self.play_btn)

        self.pause_btn = QPushButton("暂停")
        self.pause_btn.clicked.connect(self.pause_videos)
        buttons_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_videos)
        buttons_layout.addWidget(self.stop_btn)

        control_layout.addLayout(buttons_layout)
        control_group.setLayout(control_layout)
        # control_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        main_layout.addWidget(control_group)

        # 设置主布局
        self.setLayout(main_layout)
        self.setWindowTitle("实验视频播放器")
        self.resize(800, 600)

    def load_database(self):
        """加载数据库文件并提取视频信息"""
        # 选择数据库文件
        db_path, _ = QFileDialog.getOpenFileName(self, "选择数据库文件", "", "数据库文件 (*.db)")
        if not db_path:
            return

        # 更新UI
        self.db_path_label.setText(f"已加载: {os.path.basename(db_path)}")

        # 关闭之前的连接
        if self.conn:
            self.conn.close()

        # 连接到数据库
        try:
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()

            # 查询视频数据
            self.cursor.execute('''
            SELECT id, experiment_id, device_id, file_path, duration 
            FROM video_data 
            ORDER BY device_id
            ''')
            self.videos = self.cursor.fetchall()

            if not self.videos:
                QMessageBox.warning(self, "警告", "未找到视频数据")
                return

            # 清除之前的视频播放器
            self.clear_players()

            # 计算最大时长（秒）
            self.max_duration = max(video[4] for video in self.videos) * 1000  # 转换为毫秒
            self.progress_slider.setRange(0, self.max_duration)
            self.duration_label.setText(self.format_time(self.max_duration))

            # 创建视频播放器
            self.create_players()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "数据库错误", f"读取数据库失败: {str(e)}")

    def clear_players(self):
        """清除当前所有播放器"""
        # 停止计时器
        self.timer.stop()
        self.playing = False

        # 清理播放器和视频窗口
        for player in self.players:
            player.stop()

        self.players = []
        self.video_widgets = []

        # 清理视频布局中的所有组件
        while self.videos_layout.count():
            item = self.videos_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def create_players(self):
        """为每个视频创建播放器"""
        # 获取有多少个不同设备的视频
        devices = set(video[2] for video in self.videos)

        # 创建视频播放器网格
        row, col = 0, 0
        max_cols = 2  # 每行最多2个视频

        for device in devices:
            # 找出该设备的所有视频
            device_videos = [v for v in self.videos if v[2] == device]

            for video in device_videos:
                video_id, exp_id, device_id, file_path, duration = video

                # 检查文件是否存在
                if not os.path.exists(file_path):
                    # 显示错误，但继续处理其他视频
                    self.videos_layout.addWidget(QLabel(f"文件不存在: {file_path}"), row, col)
                    continue

                # 创建视频标签
                label = QLabel(f"{device_id} - {os.path.basename(file_path)}")
                self.videos_layout.addWidget(label, row, col, 1, 1)

                # 创建视频组件
                video_widget = QVideoWidget()
                self.videos_layout.addWidget(video_widget, row + 1, col, 1, 1)
                self.video_widgets.append(video_widget)

                # 创建播放器
                player = QMediaPlayer()
                player.setVideoOutput(video_widget)
                player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
                self.players.append(player)

                # 创建视频结束标识
                finished_label = QLabel("播放中")
                self.videos_layout.addWidget(finished_label, row + 2, col, 1, 1)

                # 记录标签，用于后续更新状态
                player.finished_label = finished_label
                player.duration = duration * 1000  # 转换为毫秒

                # 更新网格位置
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 10  # 每个视频占3行

    def play_videos(self):
        """播放所有视频"""
        if not self.players:
            return

        for player in self.players:
            player.play()
            player.finished_label.setText("播放中")

        self.playing = True
        self.timer.start()

    def pause_videos(self):
        """暂停所有视频"""
        if not self.players:
            return

        for player in self.players:
            player.pause()

        self.playing = False
        self.timer.stop()

    def stop_videos(self):
        """停止所有视频"""
        if not self.players:
            return

        for player in self.players:
            player.stop()
            player.finished_label.setText("已停止")

        self.playing = False
        self.timer.stop()
        self.current_position = 0
        self.progress_slider.setValue(0)
        self.position_label.setText("00:00")

    def update_progress(self):
        """更新播放进度"""
        if not self.playing or not self.players:
            return

        # 获取当前位置（使用第一个播放器作为参考）
        self.current_position = self.players[0].position()

        # 更新进度条和时间显示
        self.progress_slider.setValue(self.current_position)
        self.position_label.setText(self.format_time(self.current_position))

        # 检查每个视频是否已经播放结束
        for player in self.players:
            if player.position() >= player.duration:
                player.finished_label.setText("已播放完成")

        # 检查是否所有视频都播放完成
        if all(player.position() >= player.duration for player in self.players):
            self.timer.stop()
            self.playing = False

    def set_position(self, position):
        """设置播放位置"""
        if not self.players:
            return

        for player in self.players:
            player.setPosition(position)
            # 重置"已播放完成"标签
            if position < player.duration:
                player.finished_label.setText("播放中")
            else:
                player.finished_label.setText("已播放完成")

    def format_time(self, milliseconds):
        """格式化时间显示"""
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds %= 60
        return f"{minutes:02d}:{seconds:02d}"

    def closeEvent(self, event):
        """关闭窗口时的处理"""
        # 停止视频播放
        self.stop_videos()

        # 关闭数据库连接
        if self.conn:
            self.conn.close()

        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoPlayerWidget()
    window.show()
    sys.exit(app.exec_())