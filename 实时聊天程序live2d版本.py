import os

import random
import sys
import threading

import warnings

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from live2d测试 import 主窗口
from 函数 import 数值转颜色
from 函数测试 import 模拟摆头动作
from 图形进程 import 圆形窗口

warnings.filterwarnings("ignore", category=DeprecationWarning)


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
    api_key=os.environ.get("GEMINI_API_KEY"),  # 替换为你的 API 密钥
)

#提示词 = """あなたは日本語の会話練習AIで、名前はつむぎ。若者っぽいカジュアルな話し方で答えて。敬語は使わず、全部タメ口で。話すスピードはゆっくりめに。"""
提示词 = """あなたは日本語の会話練習AIで、名前はつむぎ。若者っぽいカジュアルな話し方で答えて。敬語は使わず、全部タメ口で。話すスピードはゆっくりめに。。"""


tools = [
    types.Tool(google_search=types.GoogleSearch()),
]

# 虽然 Gemini 2.0 Flash 处于实验性预览模式，但此处只能传递 AUDIO 或
# TEXT 中的一个。
配置 = types.LiveConnectConfig(
    response_modalities=[
        # "text",
        "audio",
    ],
    system_instruction=提示词,
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Leda")
        )
    ),
    tools=tools,
)

音频库 = pyaudio.PyAudio()


class 音频循环:
    def __init__(self, 视频模式="screen"):  # 重新添加 视频模式 参数，并默认设置为 "screen"
        self.视频模式 = 视频模式  # 重新添加 视频模式 相关

        self.音频输入队列 = None
        self.输出队列 = asyncio.Queue(maxsize=5)  # 重新添加 输出队列，虽然可能不再直接使用，但为了保守修改，先保留

        self.会话 = None

        self.发送文本任务 = None
        self.接收音频任务 = None
        self.播放音频任务 = None
        self.发送实时任务 = None # 添加 发送实时 任务
        self.获取屏幕任务 = None # 添加 获取屏幕 任务

    async def 发送文本(self):
        while True:
            文本 = await asyncio.to_thread(
                input,
                "",
            )
            if 文本.lower() == "q":
                break
            await self.会话.send(input=文本 or ".", end_of_turn=True)

    def _获取屏幕(self): # def _get_screen(self):
        sct = mss.mss()
        monitor = sct.monitors[0]

        i = sct.grab(monitor)

        mime_type = "image/jpeg"
        image_bytes = mss.tools.to_png(i.rgb, i.size) # Changed to png as jpeg might have issues and png is lossless and faster to encode/decode usually.
        img = PIL.Image.open(io.BytesIO(image_bytes))

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg") # Keep saving as jpeg as requested. But consider png for better performance.
        image_io.seek(0)

        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    async def 获取屏幕(self): # async def get_screen(self):

        while True:
            帧 = await asyncio.to_thread(self._获取屏幕) # frame = await asyncio.to_thread(self._get_screen)
            if 帧 is None: # if frame is None:
                break

            await asyncio.sleep(1.0) # Reduced to 0.1 or lower for smoother video, 1.0 is very slow for video

            await self.输出队列.put(帧) # await self.out_queue.put(frame)      模仿这个方法写入

    async def 发送实时(self):
        while True:
            数据包 = await self.输出队列.get()
            await self.会话.send(input=数据包)

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

            # if not 字节流:
            #     字节数值 = [byte for byte in 数据]
            #     # 计算平均值
            #     中间值 = sum(字节数值) / len(字节数值)
            #     if 中间值 < 80:
            #         平均值1 = 中间值
            #     else:
            #         平均值1 = 80

            await self.输出队列.put({"data": 数据, "mime_type": "audio/pcm"}) # 重新使用 输出队列，音频数据也放入输出队列

    async def 接收音频(self):
        "后台任务，用于从 websocket 读取数据并将 pcm 数据块写入音频输入队列"
        CHUNK_SIZE = 4032  # 每次向队列投入的最小数据块，单位：字节

        while True:
            turn = self.会话.receive()
            async for response in turn:
                if 数据 := response.data:
                    for i in range(0, len(数据), CHUNK_SIZE):
                        小块 = 数据[i:i + CHUNK_SIZE]
                        self.音频输入队列.put_nowait(小块)
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
            # print(平均值1)
            if 字节流:
                字节数值 = [byte for byte in 字节流]
                # 计算平均值
                平均值1 = sum(字节数值) / len(字节数值)
            else:
                平均值1 = 0

            await asyncio.sleep(0.01)

    async def 运行(self):
        try:
            async with (
                客户端.aio.live.connect(model=模型, config=配置) as 会话,
                asyncio.TaskGroup() as 任务组,
            ):
                self.会话 = 会话

                self.音频输入队列 = asyncio.Queue()
                self.输出队列 = asyncio.Queue(maxsize=5) # 重新添加 输出队列

                发送文本任务 = 任务组.create_task(self.发送文本())
                任务组.create_task(self.监听音频())
                任务组.create_task(self.发送实时()) # 重新添加 发送实时 任务

                # 重新添加 视频模式 相关任务, 默认启动屏幕捕获
                if self.视频模式 == "camera":
                    # 假设有 获取帧 方法，如果不需要相机，可以移除这部分
                    # 任务组.create_task(self.获取帧())
                    pass #  如果不需要相机，则pass
                elif self.视频模式 == "screen" or True: # 默认启动屏幕捕获，或者始终启动
                    self.获取屏幕任务 = 任务组.create_task(self.获取屏幕()) # 启动屏幕捕获任务

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
            从变量1 = 非线性插值(从变量1, int(平均值1), 0.1)
            time.sleep(0.0016)  # 每次暂停 0.1 秒，模拟动画的更新过程


    线程1 = threading.Thread(target=主变量线程)
    线程1.start()

    应用 = QApplication(sys.argv)
    窗口 = 主窗口()
    窗口.resize(1000, 800)
    窗口.show()


    def 设置嘴巴大小():

        if 字节流:
            窗口.设置嘴巴大小(从变量1 * 0.005)

        if not 字节流:
            窗口.开始动作()
            窗口.设置嘴巴大小(0)


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


    定时器3 = QTimer()
    定时器3.timeout.connect(控制动作)
    定时器3.start(8)  # 毫秒

    窗口.停止动作()

    定时器 = QTimer()
    定时器.timeout.connect(设置嘴巴大小)
    定时器.start(8)  # 毫秒
    print("加载成功!")
    sys.exit(应用.exec())
