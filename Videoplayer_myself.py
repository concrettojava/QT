import sqlite3, sys, os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QPushButton, QHBoxLayout, QFileDialog, QSlider,
                             QLabel, QMessageBox, QStyle, QFrame, QScrollArea, QGroupBox, QSizePolicy)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl, QSize, QTime, QTimer
from PyQt5.QtGui import QIcon, QCursor


class CustomVideoWidget(QWidget):
    """自定义视频控件，带有悬停显示的控制条"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # 创建布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # 创建视频显示区域
        self.videoWidget = QVideoWidget()
        self.layout.addWidget(self.videoWidget)

        # 创建控制层
        self.controlBar = QWidget(self)
        self.controlBar.setStyleSheet("background-color: rgba(0, 0, 0, 150); border-radius: 5px;")
        self.controlBar.setFixedHeight(50)

        # 控制层布局
        controlLayout = QHBoxLayout(self.controlBar)
        controlLayout.setContentsMargins(10, 5, 10, 5)

        # 播放/暂停按钮
        self.playButton = QPushButton()
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.setIconSize(QSize(24, 24))
        self.playButton.setFixedSize(30, 30)
        self.playButton.setStyleSheet("background: transparent; border: none;")

        # 时间标签
        self.timeLabel = QLabel("00:00 / 00:00")
        self.timeLabel.setStyleSheet("color: white;")
        self.timeLabel.setFixedWidth(100)

        # 进度条
        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.setStyleSheet("QSlider::groove:horizontal { height: 5px; background: #555; }"
                                          "QSlider::handle:horizontal { background: #2196F3; width: 12px; margin: -4px 0; border-radius: 6px; }")

        # 音量按钮
        self.volumeButton = QPushButton()
        self.volumeButton.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        self.volumeButton.setIconSize(QSize(20, 20))
        self.volumeButton.setFixedSize(30, 30)
        self.volumeButton.setStyleSheet("background: transparent; border: none;")

        # 音量滑块
        self.volumeSlider = QSlider(Qt.Horizontal)
        self.volumeSlider.setRange(0, 100)
        self.volumeSlider.setValue(100)  # 默认最大音量
        self.volumeSlider.setFixedWidth(70)
        self.volumeSlider.setStyleSheet("QSlider::groove:horizontal { height: 5px; background: #555; }"
                                        "QSlider::handle:horizontal { background: #2196F3; width: 12px; margin: -4px 0; border-radius: 6px; }")

        # 全屏按钮
        self.fullScreenButton = QPushButton()
        self.fullScreenButton.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
        self.fullScreenButton.setIconSize(QSize(20, 20))
        self.fullScreenButton.setFixedSize(30, 30)
        self.fullScreenButton.setStyleSheet("background: transparent; border: none;")

        # 添加控件到控制层
        controlLayout.addWidget(self.playButton)
        controlLayout.addSpacing(5)
        controlLayout.addWidget(self.positionSlider)
        controlLayout.addSpacing(5)
        controlLayout.addWidget(self.timeLabel)
        controlLayout.addSpacing(10)
        controlLayout.addWidget(self.volumeButton)
        controlLayout.addWidget(self.volumeSlider)
        controlLayout.addSpacing(10)
        controlLayout.addWidget(self.fullScreenButton)

        # 初始状态隐藏控制层
        self.controlBar.setVisible(False)

        # 设置鼠标跟踪
        self.setMouseTracking(True)
        self.videoWidget.setMouseTracking(True)

        # 创建计时器用于自动隐藏控制层
        self.hideTimer = QTimer(self)
        self.hideTimer.setSingleShot(True)
        self.hideTimer.timeout.connect(self.hideControls)

    def resizeEvent(self, event):
        """重新定位控制层"""
        self.controlBar.setGeometry(10, self.height() - 60, self.width() - 20, 50)
        super().resizeEvent(event)

    def enterEvent(self, event):
        """鼠标进入时显示控制层"""
        self.controlBar.setVisible(True)
        self.hideTimer.start(3000)  # 3秒后自动隐藏
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开时隐藏控制层"""
        self.hideTimer.stop()
        self.controlBar.setVisible(False)
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        """鼠标移动时显示控制层并重置计时器"""
        self.controlBar.setVisible(True)
        self.hideTimer.start(3000)  # 重置计时器
        super().mouseMoveEvent(event)

    def hideControls(self):
        """隐藏控制层"""
        # 只有当鼠标不在控制层上时才隐藏
        if not self.controlBar.underMouse():
            self.controlBar.setVisible(False)

    def mousePressEvent(self, event):
        """点击视频区域播放/暂停"""
        if event.button() == Qt.LeftButton:
            # 安全检查：确保控制层和父窗口存在
            if (self.controlBar and not self.controlBar.geometry().contains(event.pos()) and
                    self.parent() and hasattr(self.parent(), 'togglePlayPause')):
                # 通知父窗口播放/暂停
                self.parent().togglePlayPause()
                # 显示控制条并重置计时器
                self.controlBar.setVisible(True)
                self.hideTimer.start(3000)
        super().mousePressEvent(event)


class VideoThumbnail(QLabel):
    """视频缩略图控件"""

    def __init__(self, video_path, index, parent=None):
        super().__init__(parent)
        self.video_path = video_path
        self.index = index
        self.selected = False

        # 设置缩略图大小和样式
        self.setFixedSize(120, 80)
        self.setAlignment(Qt.AlignCenter)
        self.setFrameShape(QFrame.Box)
        self.setStyleSheet("border: 2px solid gray; background-color: #2c3e50; color: white;")

        # 设置视频名称
        video_name = os.path.basename(video_path)
        if len(video_name) > 15:
            video_name = video_name[:12] + "..."
        self.setText(video_name)

        # 设置鼠标悬停跟踪
        self.setMouseTracking(True)

    def enterEvent(self, event):
        """鼠标进入时高亮显示"""
        if not self.selected:
            self.setStyleSheet("border: 2px solid #3498db; background-color: #34495e; color: white;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开时恢复样式"""
        if not self.selected:
            self.setStyleSheet("border: 2px solid gray; background-color: #2c3e50; color: white;")
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """点击时选择视频但不播放"""
        if event.button() == Qt.LeftButton:
            # 安全检查：确保窗口存在并有selectVideo方法
            window = self.window()
            if window and hasattr(window, 'selectVideo'):
                window.selectVideo(self.index)
        super().mousePressEvent(event)


class VideoPlayer(QMainWindow):
    def __init__(self,parent=None):
        super().__init__(parent)

        # 初始化变量
        self.conn = None
        self.cursor = None
        self.videoList = []
        self.current_video_index = -1  # 表示没有选择任何视频
        self.isFullScreen = False
        self.preMuteVolume = 50  # 默认音量

        # 窗口设置
        self.setWindowTitle("视频播放器")
        self.setGeometry(100, 100, 800, 600)

        # 创建媒体播放器
        self.mediaPlayer = QMediaPlayer(None, QMediaPlayer.VideoSurface)

        # 创建自定义视频控件
        self.videoContainer = CustomVideoWidget(self)
        self.videoWidget = self.videoContainer.videoWidget

        # 设置媒体播放器的视频输出
        self.mediaPlayer.setVideoOutput(self.videoWidget)

        # 数据库加载区域
        db_group = QGroupBox("数据库加载")
        db_layout = QHBoxLayout()

        self.db_path_label = QLabel("未选择数据库")
        db_layout.addWidget(self.db_path_label)

        self.load_db_btn = (QPushButton("加载数据库"))
        self.load_db_btn.clicked.connect(self.loadData)
        db_layout.addWidget(self.load_db_btn)
        db_group.setLayout(db_layout)
        db_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)


        # 创建视频缩略图区域
        self.thumbnailScrollArea = QScrollArea()
        self.thumbnailScrollArea.setWidgetResizable(True)
        self.thumbnailScrollArea.setFixedHeight(100)
        self.thumbnailScrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.thumbnailScrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.thumbnailScrollArea.setStyleSheet("background-color: #1e272e;")

        # 创建缩略图容器
        self.thumbnailContainer = QWidget()
        self.thumbnailLayout = QHBoxLayout(self.thumbnailContainer)
        self.thumbnailLayout.setSpacing(10)
        self.thumbnailLayout.setContentsMargins(10, 5, 10, 5)
        self.thumbnailScrollArea.setWidget(self.thumbnailContainer)

        # 初始不显示缩略图区域
        self.thumbnailScrollArea.setVisible(False)

        # 创建主布局
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QVBoxLayout(centralWidget)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # 添加视频控件和缩略图区域
        mainLayout.addWidget(db_group)
        mainLayout.addWidget(self.videoContainer)
        mainLayout.addWidget(self.thumbnailScrollArea)

        try:
            # 连接控制信号
            self.videoContainer.playButton.clicked.connect(self.togglePlayPause)
            self.videoContainer.positionSlider.sliderMoved.connect(self.setPosition)
            self.videoContainer.volumeButton.clicked.connect(self.muteToggle)
            self.videoContainer.volumeSlider.valueChanged.connect(self.setVolume)
            self.videoContainer.fullScreenButton.clicked.connect(self.toggleFullScreen)

            # 连接媒体播放器信号
            self.mediaPlayer.stateChanged.connect(self.mediaStateChanged)
            self.mediaPlayer.positionChanged.connect(self.positionChanged)
            self.mediaPlayer.durationChanged.connect(self.durationChanged)
            self.mediaPlayer.volumeChanged.connect(self.volumeChanged)
            self.mediaPlayer.error.connect(self.handleError)
        except Exception as e:
            print(f"初始化过程中出错: {str(e)}")

        # 设置初始音量
        self.mediaPlayer.setVolume(self.preMuteVolume)

    def resizeEvent(self, event):
        """窗口大小改变时调整覆盖层大小"""
        if hasattr(self, 'videoOverlay') and self.videoOverlay:
            self.videoOverlay.setGeometry(0, 0, self.videoContainer.width(), self.videoContainer.height())
        super().resizeEvent(event)

    def closeEvent(self, event):
        """窗口关闭时释放资源"""
        try:
            # 释放媒体播放器
            if self.mediaPlayer:
                self.mediaPlayer.stop()

            # 关闭数据库连接
            if self.conn:
                self.conn.close()
        except Exception as e:
            print(f"关闭时出错: {str(e)}")
        super().closeEvent(event)

    def selectVideo(self, index):
        """选择视频但不播放"""
        try:
            if 0 <= index < len(self.videoList):
                self.current_video_index = index
                video_path = self.videoList[index][0]

                if os.path.exists(video_path):
                    # 停止当前播放
                    self.mediaPlayer.stop()

                    # 隐藏导入按钮覆盖层
                    if hasattr(self, 'videoOverlay') and self.videoOverlay:
                        self.videoOverlay.setVisible(False)

                    # 加载视频但不播放
                    self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))

                    # 更新缩略图选中状态
                    for i in range(self.thumbnailLayout.count()):
                        item = self.thumbnailLayout.itemAt(i)
                        if item and item.widget():
                            widget = item.widget()
                            if isinstance(widget, VideoThumbnail):
                                if widget.index == index:
                                    widget.setStyleSheet(
                                        "border: 2px solid #e74c3c; background-color: #34495e; color: white;")
                                    widget.selected = True
                                else:
                                    widget.setStyleSheet(
                                        "border: 2px solid gray; background-color: #2c3e50; color: white;")
                                    widget.selected = False
                else:
                    QMessageBox.warning(self, "警告", f"视频文件不存在: {video_path}")
        except Exception as e:
            print(f"选择视频时出错: {str(e)}")

    def togglePlayPause(self):
        """切换播放/暂停状态"""
        try:
            if self.mediaPlayer.media().isNull():
                if self.current_video_index >= 0 and self.current_video_index < len(self.videoList):
                    # 有选择视频但尚未加载，先加载视频
                    video_path = self.videoList[self.current_video_index][0]
                    if os.path.exists(video_path):
                        self.mediaPlayer.setMedia(QMediaContent(QUrl.fromLocalFile(video_path)))
                else:
                    QMessageBox.warning(self, "警告", "请先选择一个视频")
                    return

            if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
                self.mediaPlayer.pause()
            else:
                self.mediaPlayer.play()
        except Exception as e:
            print(f"播放/暂停时出错: {str(e)}")

    def mediaStateChanged(self, state):
        """媒体状态改变时更新按钮图标"""
        try:
            if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
                self.videoContainer.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            else:
                self.videoContainer.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        except Exception as e:
            print(f"更新播放状态时出错: {str(e)}")

    def positionChanged(self, position):
        """更新进度条位置和时间显示"""
        try:
            self.videoContainer.positionSlider.setValue(position)

            # 更新时间显示
            duration = self.mediaPlayer.duration()
            if duration > 0:
                current_time = QTime(0, 0)
                current_time = current_time.addMSecs(position)
                total_time = QTime(0, 0)
                total_time = total_time.addMSecs(duration)
                time_format = "mm:ss"
                self.videoContainer.timeLabel.setText(
                    f"{current_time.toString(time_format)} / {total_time.toString(time_format)}")
        except Exception as e:
            print(f"更新位置时出错: {str(e)}")

    def durationChanged(self, duration):
        """媒体时长改变时更新进度条范围"""
        try:
            self.videoContainer.positionSlider.setRange(0, duration)
        except Exception as e:
            print(f"更新时长时出错: {str(e)}")

    def setPosition(self, position):
        """设置播放位置"""
        try:
            self.mediaPlayer.setPosition(position)
        except Exception as e:
            print(f"设置位置时出错: {str(e)}")

    def volumeChanged(self, volume):
        """音量改变时更新滑块和图标"""
        try:
            self.videoContainer.volumeSlider.setValue(volume)
            if volume == 0:
                self.videoContainer.volumeButton.setIcon(self.style().standardIcon(QStyle.SP_MediaVolumeMuted))
            else:
                self.videoContainer.volumeButton.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        except Exception as e:
            print(f"更新音量显示时出错: {str(e)}")

    def setVolume(self, volume):
        """设置音量"""
        try:
            self.mediaPlayer.setVolume(volume)
        except Exception as e:
            print(f"设置音量时出错: {str(e)}")

    def muteToggle(self):
        """切换静音状态"""
        try:
            if self.mediaPlayer.volume() > 0:
                self.preMuteVolume = self.mediaPlayer.volume()
                self.mediaPlayer.setVolume(0)
                self.videoContainer.volumeButton.setIcon(self.style().standardIcon(QStyle.SP_MediaVolumeMuted))
            else:
                # 恢复之前的音量，如果没有记录则设为50%
                self.mediaPlayer.setVolume(getattr(self, 'preMuteVolume', 50))
                self.videoContainer.volumeButton.setIcon(self.style().standardIcon(QStyle.SP_MediaVolume))
        except Exception as e:
            print(f"切换静音时出错: {str(e)}")

    def toggleFullScreen(self):
        """切换全屏状态"""
        try:
            if self.isFullScreen:
                self.showNormal()
                self.thumbnailScrollArea.setVisible(True)
                self.videoContainer.fullScreenButton.setIcon(self.style().standardIcon(QStyle.SP_TitleBarMaxButton))
            else:
                self.showFullScreen()
                self.thumbnailScrollArea.setVisible(False)
                self.videoContainer.fullScreenButton.setIcon(self.style().standardIcon(QStyle.SP_TitleBarNormalButton))
            self.isFullScreen = not self.isFullScreen
        except Exception as e:
            print(f"切换全屏时出错: {str(e)}")

    def keyPressEvent(self, event):
        """按键事件处理"""
        try:
            if event.key() == Qt.Key_Escape and self.isFullScreen:
                self.toggleFullScreen()
            elif event.key() == Qt.Key_Space:
                self.togglePlayPause()
            else:
                super().keyPressEvent(event)
        except Exception as e:
            print(f"按键事件处理时出错: {str(e)}")

    def createThumbnails(self):
        """创建视频缩略图"""
        try:
            # 清空现有缩略图
            while self.thumbnailLayout.count():
                item = self.thumbnailLayout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            # 为每个视频创建缩略图
            for i, (video_path, _) in enumerate(self.videoList):
                thumbnail = VideoThumbnail(video_path, i, self.thumbnailContainer)
                self.thumbnailLayout.addWidget(thumbnail)

            # 添加弹簧确保缩略图靠左对齐
            self.thumbnailLayout.addStretch()

            # 显示视频选择栏
            self.thumbnailScrollArea.setVisible(True)
        except Exception as e:
            print(f"创建缩略图时出错: {str(e)}")

    def loadData(self):
        """加载数据库中的视频信息"""
        try:
            db_path, _ = QFileDialog.getOpenFileName(self, "选择数据库文件", "", "数据库文件(*.db)")
            if not db_path:
                return

            # 关闭之前的连接
            if self.conn:
                self.conn.close()

            # 连接到数据库
            self.conn = sqlite3.connect(db_path)
            self.cursor = self.conn.cursor()

            # 检查表是否存在
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='video_data'")
            if not self.cursor.fetchone():
                QMessageBox.warning(self, "警告", "数据库中不存在video_data表")
                return

            # 查询视频数据
            self.cursor.execute("SELECT file_path, duration FROM video_data")
            self.videoList = list(self.cursor.fetchall())

            if not self.videoList:
                QMessageBox.warning(self, "警告", "未找到视频数据")
                return

            # 更新数据库路径标签
            self.db_path_label.setText(f"已加载: {os.path.basename(db_path)}")

            # 更新加载按钮样式
            self.load_db_btn.setText("重新加载")
            self.load_db_btn.setStyleSheet("background-color: #27ae60; color: white;")

            # 创建视频缩略图
            self.createThumbnails()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "数据库错误", f"读取数据库失败: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载数据时发生错误: {str(e)}")

    def handleError(self):
        """处理媒体播放器错误"""
        try:
            errorMsg = self.mediaPlayer.errorString()
            QMessageBox.warning(self, "媒体播放器错误",
                                f"发生错误: {errorMsg}")
        except Exception as e:
            print(f"处理媒体播放器错误时出错: {str(e)}")


if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        player = VideoPlayer()
        player.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"应用启动时发生错误: {str(e)}")