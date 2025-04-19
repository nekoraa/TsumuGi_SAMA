"""
## 文档
快速入门: https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_LiveAPI.py

## 设置

要安装此脚本的依赖项，请运行:
"""
import random
import sys
import threading

import warnings

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from 函数 import 数值转颜色
from 图形进程 import 圆形窗口

warnings.filterwarnings("ignore", category=DeprecationWarning)

import os
import asyncio
import base64
import io
import traceback

import cv2  # 保持导入，即使当前未使用，因为原始脚本依赖它，移除可能引入其他问题，如果确定完全不需要可以移除
import pyaudio
import PIL.Image  # 保持导入，理由同上
import mss  # 保持导入，理由同上

import argparse
import time

from google import genai
from google.genai import types

音频格式 = pyaudio.paInt16
声道数 = 1
发送采样率 = 16000
接收采样率 = 24000
数据块大小 = 1024
字节流 = None

平均值 = 0
平均值1 = 0

模型 = "models/gemini-2.0-flash-live-001"

默认模式 = "none"  # 默认模式不再使用，但保留定义

客户端 = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key="AIzaSyCAIRhl-xcBQ02t_IVP1LQZdwlpIQCJZKc",  # 替换为你的 API 密钥
)

提示词 = """あなたは日本語の会話練習AIで、名前はネコミミ。若者っぽいカジュアルな話し方で答えて。文は短くていい。敬語は使わず、全部タメ口で。話すスピードはゆっくりめに。"""

# 虽然 Gemini 2.0 Flash 处于实验性预览模式，但此处只能传递 AUDIO 或
# TEXT 中的一个。
配置 = types.LiveConnectConfig(
    response_modalities=[
        "audio",
    ],
    system_instruction=提示词,
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Zephyr")
        )
    ),
)

音频库 = pyaudio.PyAudio()


class 音频循环:
    def __init__(self):  # 移除 视频模式 参数
        # self.视频模式 = 视频模式  # 移除 视频模式 相关

        self.音频输入队列 = None
        self.输出队列 = None  # 不再需要输出队列，因为没有实时发送图像等

        self.会话 = None

        self.发送文本任务 = None
        self.接收音频任务 = None
        self.播放音频任务 = None

    async def 发送文本(self):
        while True:
            文本 = await asyncio.to_thread(
                input,
                "",
            )
            if 文本.lower() == "q":
                break
            await self.会话.send(input=文本 or ".", end_of_turn=True)

    # 移除 _获取帧, 获取帧, _获取屏幕, 获取屏幕, 发送实时 方法

    async def 监听音频(self):
        global 平均值1
        麦克风信息 = 音频库.get_default_input_device_info()
        self.音频流 = await asyncio.to_thread(
            音频库.open,
            format=音频格式,
            channels=声道数,
            rate=发送采样率,
            input=True,
            input_device_index=麦克风信息["index"],
            frames_per_buffer=数据块大小,
        )
        if __debug__:
            kwargs = {"exception_on_overflow": False}
        else:
            kwargs = {}
        while True:
            数据 = await asyncio.to_thread(self.音频流.read, 数据块大小, **kwargs)

            if not 字节流:
                字节数值 = [byte for byte in 数据]
                # 计算平均值
                中间值 = sum(字节数值) / len(字节数值)
                if 中间值 < 80:
                    平均值1 = 中间值
                else:
                    平均值1 = 80



            #  不再需要输出队列
            # await self.输出队列.put({"data": 数据, "mime_type": "audio/pcm"})
            await self.会话.send(input={"data": 数据, "mime_type": "audio/pcm"})  # 直接发送音频数据

    async def 接收音频(self):
        "后台任务，用于从 websocket 读取数据并将 pcm 数据块写入音频输入队列"
        while True:
            turn = self.会话.receive()
            async for response in turn:
                if 数据 := response.data:
                    self.音频输入队列.put_nowait(数据)
                    continue
                if 文本 := response.text:
                    print(文本, end="")

            # 如果您中断模型，它会发送 turn_complete。
            # 为了使中断工作，我们需要停止播放。
            # 因此清空音频队列，因为它可能已加载
            # 比已播放的音频多得多。
            while not self.音频输入队列.empty():
                self.音频输入队列.get_nowait()

    async def 播放音频(self):
        global 字节流, 平均值1
        音频播放流 = await asyncio.to_thread(
            音频库.open,
            format=音频格式,
            channels=声道数,
            rate=接收采样率,
            output=True,
        )
        while True:
            字节流 = await self.音频输入队列.get()
            await asyncio.to_thread(音频播放流.write, 字节流)
            字节流 = None

    async def 字节流检测(self):
        global 字节流, 平均值1
        while True:
            print(平均值1)
            if 字节流:
                字节数值 = [byte for byte in 字节流]
                # 计算平均值
                平均值1 = sum(字节数值) / len(字节数值)
            else:
                pass

            await asyncio.sleep(0.01)

    async def 运行(self):
        try:
            async with (
                客户端.aio.live.connect(model=模型, config=配置) as 会话,
                asyncio.TaskGroup() as 任务组,
            ):
                self.会话 = 会话

                self.音频输入队列 = asyncio.Queue()
                # self.输出队列 = asyncio.Queue(maxsize=5) # 不再需要输出队列

                发送文本任务 = 任务组.create_task(self.发送文本())
                # 移除 任务组.create_task(self.发送实时()) # 不再需要发送实时
                任务组.create_task(self.监听音频())
                # 移除 视频模式 相关任务
                # if self.视频模式 == "camera":
                #     任务组.create_task(self.获取帧())
                # elif self.视频模式 == "screen":
                #     任务组.create_task(self.获取屏幕())

                任务组.create_task(self.接收音频())
                任务组.create_task(self.播放音频())
                任务组.create_task(self.字节流检测())

                await 发送文本任务
                raise asyncio.CancelledError("用户请求退出")

        except asyncio.CancelledError:
            pass
        except ExceptionGroup as 异常组:
            self.音频流.close()
            traceback.print_exception(异常组)


if __name__ == "__main__":
    参数解析器 = argparse.ArgumentParser()
    参数 = 参数解析器.parse_args()
    主程序 = 音频循环()  # 移除 视频模式 参数


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
            从变量1 = 非线性插值(从变量1, int(平均值1), 0.01)
            time.sleep(0.0016)  # 每次暂停 0.1 秒，模拟动画的更新过程


    线程1 = threading.Thread(target=主变量线程)
    线程1.start()

    应用 = QApplication(sys.argv)

    半径 = 80
    颜色 = "#33CC99"
    窗口大小 = (400, 400)


    def 定时换颜色():
        窗口.设置新参数(int(从变量1), 数值转颜色(int(从变量1)))


    窗口 = 圆形窗口(半径=半径, 颜色=颜色, 窗口大小=窗口大小)
    窗口.show()

    定时器 = QTimer()
    定时器.timeout.connect(定时换颜色)
    定时器.start(16)  # 毫秒

    sys.exit(应用.exec())
