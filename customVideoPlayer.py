from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer, QSize, Qt
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QStyle, QSlider, QLabel


class CustomVideoWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # 创建布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)#满填充
        self.layout.setSpacing(0)

        # 创建视频显示区域
        self.videoWidget = QVideoWidget()
        self.layout.addWidget(self.videoWidget)

        # 创建控制层
        self.controlBar = QWidget(self)
        self.controlBar.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        self.controlBar.setFixedHeight(40)

        # 控制层布局
        controlLayout = QHBoxLayout(self.controlBar)
        controlLayout.setContentsMargins(5, 0, 5, 0)

        # 播放/暂停按钮
        self.playButton = QPushButton()
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.setIconSize(QSize(24, 24))
        self.playButton.setFixedSize(30, 30)
        self.playButton.setStyleSheet("background: transparent; border: none;")

        # 进度条
        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.setStyleSheet("QSlider::groove:horizontal { height: 5px; background: #555; }"
                                          "QSlider::handle:horizontal { background: #2196F3; width: 12px; margin: -4px 0; border-radius: 6px; }")

        # 时间标签
        self.timeLabel = QLabel("00:00 / 00:00")
        self.timeLabel.setStyleSheet("color: white;")
        self.timeLabel.setFixedWidth(100)

        # 添加控件到控制层
        controlLayout.addWidget(self.playButton)
        controlLayout.addWidget(self.positionSlider)
        controlLayout.addWidget(self.timeLabel)

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
        self.controlBar.setGeometry(0, self.height() - 40, self.width(), 40)
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
        self.controlBar.setVisible(False)

    def mousePressEvent(self, event):
        """点击视频区域播放/暂停"""
        if event.button() == Qt.LeftButton:
            if not self.controlBar.geometry().contains(event.pos()):
                # 通知父窗口播放/暂停
                self.parent().togglePlayPause()
        super().mousePressEvent(event)


