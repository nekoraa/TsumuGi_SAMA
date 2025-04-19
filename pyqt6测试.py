from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QSlider, QLabel
from PyQt6.QtCore import Qt
import sys

class 主窗口(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("滑动条测试")

        布局 = QVBoxLayout()
        self.滑动条 = QSlider(Qt.Orientation.Horizontal)
        self.滑动条.valueChanged.connect(self.ces)

        布局.addWidget(QLabel("测试"))
        布局.addWidget(self.滑动条)

        容器 = QWidget()
        容器.setLayout(布局)
        self.setCentralWidget(容器)

    def ces(self):
        print("滑动条值变化")

应用 = QApplication(sys.argv)
窗口 = 主窗口()
窗口.show()
sys.exit(应用.exec())


