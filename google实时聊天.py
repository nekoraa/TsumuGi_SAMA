"""
## 文档
快速入门: https://github.com/google-gemini/cookbook/blob/main/quickstarts/Get_started_LiveAPI.py

## 设置

要安装此脚本的依赖项，请运行:
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)



import os
import asyncio
import base64
import io
import traceback

import cv2
import pyaudio
import PIL.Image
import mss

import argparse

from google import genai
from google.genai import types

音频格式 = pyaudio.paInt16
声道数 = 1
发送采样率 = 16000
接收采样率 = 24000
数据块大小 = 1024

模型 = "models/gemini-2.0-flash-live-001"

默认模式 = "none"

客户端 = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=os.environ.get("GEMINI_API_KEY"),
)

提示词 = """你是一个口语练习对话ai名字是ネコミミ,你应该回答日语"""


# 虽然 Gemini 2.0 Flash 处于实验性预览模式，但此处只能传递 AUDIO 或
# TEXT 中的一个。
配置 = types.LiveConnectConfig(
    response_modalities=[
        "audio",
    ],
    system_instruction=提示词,
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
        )
    ),
)

音频库 = pyaudio.PyAudio()


class 音频循环:
    def __init__(self, 视频模式=默认模式):
        self.视频模式 = 视频模式

        self.音频输入队列 = None
        self.输出队列 = None

        self.会话 = None

        self.发送文本任务 = None
        self.接收音频任务 = None
        self.播放音频任务 = None

    async def 发送文本(self):
        while True:
            文本 = await asyncio.to_thread(
                input,
                "消息 > ",
            )
            if 文本.lower() == "q":
                break
            await self.会话.send(input=文本 or ".", end_of_turn=True)

    def _获取帧(self, 摄像头):
        # 读取帧
        返回, 帧 = 摄像头.read()
        # 检查是否成功读取帧
        if not 返回:
            return None
        # 修复: 将 BGR 颜色空间转换为 RGB
        # OpenCV 以 BGR 捕获，但 PIL 期望 RGB 格式
        # 这可以防止视频源中的蓝色色调
        彩色帧 = cv2.cvtColor(帧, cv2.COLOR_BGR2RGB)
        图像 = PIL.Image.fromarray(彩色帧)  # 现在使用 RGB 帧
        图像.thumbnail([1024, 1024])

        图像IO = io.BytesIO()
        图像.save(图像IO, format="jpeg")
        图像IO.seek(0)

        MIME类型 = "image/jpeg"
        图像字节 = 图像IO.read()
        return {"mime_type": MIME类型, "data": base64.b64encode(图像字节).decode()}

    async def 获取帧(self):
        # 这大约需要一秒钟，并且会阻塞整个程序
        # 如果您不对其进行 to_thread 处理，则会导致音频管道溢出。
        摄像头 = await asyncio.to_thread(
            cv2.VideoCapture, 0
        )  # 0 代表默认摄像头

        while True:
            帧 = await asyncio.to_thread(self._获取帧, 摄像头)
            if 帧 is None:
                break

            await asyncio.sleep(1.0)

            await self.输出队列.put(帧)

        # 释放 VideoCapture 对象
        摄像头.release()

    def _获取屏幕(self):
        屏幕捕获 = mss.mss()
        显示器 = 屏幕捕获.monitors[0]

        图像数据 = 屏幕捕获.grab(显示器)

        MIME类型 = "image/jpeg"
        图像字节 = mss.tools.to_png(图像数据.rgb, 图像数据.size)
        图像 = PIL.Image.open(io.BytesIO(图像字节))

        图像IO = io.BytesIO()
        图像.save(图像IO, format="jpeg")
        图像IO.seek(0)

        图像字节 = 图像IO.read()
        return {"mime_type": MIME类型, "data": base64.b64encode(图像字节).decode()}

    async def 获取屏幕(self):

        while True:
            帧 = await asyncio.to_thread(self._获取屏幕)
            if 帧 is None:
                break

            await asyncio.sleep(1.0)

            await self.输出队列.put(帧)

    async def 发送实时(self):
        while True:
            消息 = await self.输出队列.get()
            await self.会话.send(input=消息)

    async def 监听音频(self):
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
            await self.输出队列.put({"data": 数据, "mime_type": "audio/pcm"})

    async def 接收音频(self):
        "后台任务，用于从 websocket 读取数据并将 pcm 数据块写入输出队列"
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

    async def 运行(self):
        try:
            async with (
                客户端.aio.live.connect(model=模型, config=配置) as 会话,
                asyncio.TaskGroup() as 任务组,
            ):
                self.会话 = 会话

                self.音频输入队列 = asyncio.Queue()
                self.输出队列 = asyncio.Queue(maxsize=5)

                发送文本任务 = 任务组.create_task(self.发送文本())
                任务组.create_task(self.发送实时())
                任务组.create_task(self.监听音频())
                if self.视频模式 == "camera":
                    任务组.create_task(self.获取帧())
                elif self.视频模式 == "screen":
                    任务组.create_task(self.获取屏幕())

                任务组.create_task(self.接收音频())
                任务组.create_task(self.播放音频())

                await 发送文本任务
                raise asyncio.CancelledError("用户请求退出")

        except asyncio.CancelledError:
            pass
        except ExceptionGroup as 异常组:
            self.音频流.close()
            traceback.print_exception(异常组)


if __name__ == "__main__":
    参数解析器 = argparse.ArgumentParser()
    参数解析器.add_argument(
        "--mode",
        type=str,
        default=默认模式,
        help="要从中流式传输像素的模式",
        choices=["camera", "screen", "none"],
    )
    参数 = 参数解析器.parse_args()
    主程序 = 音频循环(视频模式=参数.mode)
    asyncio.run(主程序.运行())