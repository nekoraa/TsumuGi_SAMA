import sys
import sys
import threading
import warnings
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication
from google模型流处理 import 音频循环
from live2d测试 import 主窗口
from 函数测试 import 模拟摆头动作
warnings.filterwarnings("ignore", category=DeprecationWarning)
import asyncio
import argparse
import time


if __name__ == "__main__":
    参数解析器 = argparse.ArgumentParser()
    参数 = 参数解析器.parse_args()
    主程序 = 音频循环(视频模式=False)  # 移除 视频模式 参数


    # asyncio.run(主程序.运行())
    def 启动异步任务():
        asyncio.run(主程序.运行())


    # 创建并启动线程
    线程 = threading.Thread(target=启动异步任务)
    线程.start()

    从变量 = 100
    从变量1 = 100


    def 非线性插值(开始, 结束, 因子):
        return 开始 + (结束 - 开始) * (1 - (1 - 因子) ** 3)  # 指数衰减函数


    def 主变量线程():
        global 从变量1
        while True:
            从变量1 = 非线性插值(从变量1, int(主程序.平均值2), 0.1)
            time.sleep(0.0016)  # 每次暂停 0.1 秒，模拟动画的更新过程


    线程1 = threading.Thread(target=主变量线程)
    线程1.start()

    应用 = QApplication(sys.argv)
    窗口 = 主窗口()
    窗口.resize(1000, 800)
    窗口.show()


    def 设置嘴巴大小():

        if 主程序.字节流:
            窗口.设置嘴巴大小(从变量1 * 0.005)

        if not 主程序.字节流:
            窗口.设置嘴巴大小(0)


    摆头角度X = [0.0]
    摆头角度Y = [0.0]
    摆头角度Z = [0.0]

    身体角度X = [0.0]
    身体角度Y = [0.0]
    身体角度Z = [0.0]


    # 按顺序组合各角度变量及其对应参数
    线程参数列表 = [
        (摆头角度X,),  # 只传一个参数
        (摆头角度Y, -10, 10, 120, 1, 0.5),
        (摆头角度Z, -30, 30, 120, 2, 0.2),
        (身体角度X, -5, 5, 120, 0.5, 0.2),
        (身体角度Y, -5, 5, 120, 0.5, 0.2),
        (身体角度Z, -20, 20, 120, 1, 0.2),
    ]

    # 创建并启动线程
    for 参数 in 线程参数列表:
        threading.Thread(target=模拟摆头动作, args=参数).start()



    def 控制动作():
        窗口.控制动作("ParamAngleX", 摆头角度X[0])
        窗口.控制动作("ParamAngleY", 摆头角度Y[0])
        窗口.控制动作("ParamAngleZ", 摆头角度Z[0])
        窗口.控制动作("ParamBodyAngleZ", 身体角度X[0])
        窗口.控制动作("ParamBodyAngleX", 身体角度Y[0])


    定时器3 = QTimer()
    定时器3.timeout.connect(控制动作)
    定时器3.start(8)  # 毫秒

    定时器4 = QTimer()
    定时器4.timeout.connect(lambda: 窗口.检测动作(主程序.说话参数))
    定时器4.start(100)  # 毫秒

    窗口.停止动作()

    定时器 = QTimer()
    定时器.timeout.connect(设置嘴巴大小)
    定时器.start(8)  # 毫秒
    print("加载成功!")
    sys.exit(应用.exec())
