import math
import random

import os
import threading
import time

from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QWidget,
    QSlider, QLabel, QHBoxLayout
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

import os, sys

from 函数测试 import 模拟摆头动作


class 主窗口(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live2D 控制演示")

        self.浏览器 = QWebEngineView()
        本地文件 = os.path.abspath("web/index.html")
        self.浏览器.load(QUrl.fromLocalFile(本地文件))

        # 主布局
        主布局 = QVBoxLayout()
        主布局.addWidget(self.浏览器)

        # 控件区域布局
        控件布局 = QHBoxLayout()

        # 缩放滑动条
        self.缩放滑动条 = QSlider(Qt.Orientation.Horizontal)
        self.缩放滑动条.setRange(5, 100)  # 代表缩放 0.05 ~ 1.0
        self.缩放滑动条.setValue(20)  # 初始值 0.2
        self.缩放滑动条.valueChanged.connect(self.gengxsuof)
        控件布局.addWidget(QLabel("缩放"))
        控件布局.addWidget(self.缩放滑动条)

        # X 位置滑动条
        self.x滑动条 = QSlider(Qt.Orientation.Horizontal)
        self.x滑动条.setRange(0, 2000)
        self.x滑动条.setValue(960)  # 一般屏幕中间
        self.x滑动条.valueChanged.connect(self.gengxwz)
        控件布局.addWidget(QLabel("X"))
        控件布局.addWidget(self.x滑动条)

        # Y 位置滑动条
        self.y滑动条 = QSlider(Qt.Orientation.Horizontal)
        self.y滑动条.setRange(0, 1200)
        self.y滑动条.setValue(540)
        self.y滑动条.valueChanged.connect(self.gengxwz)
        控件布局.addWidget(QLabel("Y"))
        控件布局.addWidget(self.y滑动条)

        主布局.addLayout(控件布局)

        容器 = QWidget()
        容器.setLayout(主布局)
        self.setCentralWidget(容器)

    def 占位函数(self):
        self.缩放滑动条.valueChanged.connect(self.gengxsuof)
        self.x滑动条.valueChanged.connect(self.gengxwz)
        self.y滑动条.valueChanged.connect(self.gengxwz)

    def 设置嘴巴大小(self, 大小):
        self.浏览器.page().runJavaScript(
            f"""
            if (window.live2d模型) {{
                live2d模型.internalModel.coreModel.setParameterValueById('ParamMouthOpenY', {大小});
            }}
            """
        )

    def 停止动作(self):
        self.浏览器.page().runJavaScript(
            f"""
            if (window.live2d模型) {{
                live2d模型.internalModel.motionManager.update = (delta) => {{}};
            }}
            """
        )

    def 控制动作(self, 参数="", 值=None):
        self.浏览器.page().runJavaScript(
            f"""
            if (window.live2d模型) {{
                live2d模型.internalModel.coreModel.setParameterValueById('{参数}', {值});
            }}
            """
        )

    def 开始动作(self):
        概率 = random.random()  # 生成 0 到 1 之间的浮点数
        if 概率 < 0.5:
            self.浏览器.page().runJavaScript(
                """
                live2d模型.motion('Flick');
                """
            )
        else:
            self.浏览器.page().runJavaScript(
                """
                live2d模型.motion('Idle');
                """
            )

    def gengxsuof(self):
        缩放值 = self.缩放滑动条.value() / 100.0
        self.浏览器.page().runJavaScript(
            f"""
            if (window.live2d模型) {{
                live2d模型.scale.set({缩放值});
            }}
            """
        )

    def gengxwz(self):
        x = self.x滑动条.value()
        y = self.y滑动条.value()
        self.浏览器.page().runJavaScript(
            f"""
            if (window.live2d模型) {{
                live2d模型.x = {x};
                live2d模型.y = {y};
            }}
            """
        )


if __name__ == '__main__':
    应用 = QApplication(sys.argv)
    窗口 = 主窗口()
    窗口.resize(1000, 800)
    窗口.show()

    摆头角度X = [0.0]
    摆头角度Y = [0.0]
    摆头角度Z = [0.0]

    身体角度X = [0.0]
    身体角度Y = [0.0]
    身体角度Z = [0.0]

    动画线程 = threading.Thread(
        target=模拟摆头动作,
        args=(摆头角度X,)
    )
    动画线程.start()

    动画线程1 = threading.Thread(
        target=模拟摆头动作,
        args=(摆头角度Y, -10, 10, 120, 1, 0.5)
    )
    动画线程1.start()

    动画线程2 = threading.Thread(
        target=模拟摆头动作,
        args=(摆头角度Z, -30, 30, 120, 2, 0.2)
    )
    动画线程2.start()

    动画线程3 = threading.Thread(
        target=模拟摆头动作,
        args=(身体角度X, -5, 5, 120, 0.5, 0.2)
    )
    动画线程3.start()

    动画线程4 = threading.Thread(
        target=模拟摆头动作,
        args=(身体角度Y, -5, 5, 120, 0.5, 0.2)
    )
    动画线程4.start()

    动画线程5 = threading.Thread(
        target=模拟摆头动作,
        args=(身体角度Z, -20, 20, 120, 1, 0.2)
    )
    动画线程5.start()

    def 控制动作():
        窗口.控制动作("ParamAngleX", 摆头角度X[0])
        窗口.控制动作("ParamAngleY", 摆头角度Y[0])
        窗口.控制动作("ParamAngleZ", 摆头角度Z[0])
        窗口.控制动作("ParamBodyAngleZ", 身体角度X[0])
        窗口.控制动作("ParamBodyAngleX", 身体角度Y[0])


    定时器 = QTimer()
    定时器.timeout.connect(控制动作)
    定时器.start(8)  # 毫秒

    # 定时器1 = QTimer()
    # 定时器1.timeout.connect(控制动作1)
    # 定时器1.start(100000000)  # 毫秒

    sys.exit(应用.exec())
