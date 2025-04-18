from playback_system import PlaybackWidget,DataExportWidget
from DataCollection import DataCollectionWidget
from videoplayer import VideoPlayerWidget
from PyQt5.QtWidgets import QMainWindow,QTabWidget,QApplication
import sys

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

        self.playback_widget = VideoPlayerWidget()
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
