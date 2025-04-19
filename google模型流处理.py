import os
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import asyncio
import base64
import io
import traceback
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
音频库 = pyaudio.PyAudio()

模型 = "models/gemini-2.0-flash-live-001"
提示词 = """あなたは日本語の会話練習AIで、名前はつむぎ。若者っぽいカジュアルな話し方で答えて。敬語は使わず、全部タメ口で。話すスピードはゆっくりめに。"""

客户端 = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=os.environ.get("GEMINI_API_KEY"),
)

配置 = types.LiveConnectConfig(
    response_modalities=["audio"],
    system_instruction=提示词,
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Leda")
        )
    ),
    tools=[types.Tool(google_search=types.GoogleSearch())],
)


class 音频循环:
    def __init__(self, 视频模式=False):
        self.视频模式 = 视频模式
        self.输出队列 = asyncio.Queue(maxsize=5)
        self.平均值2 = 0
        self.字节流 = None
        self.会话 = None
        self.音频输入队列 = None

    async def 发送文本(self):
        while True:
            文本 = await asyncio.to_thread(input, "")
            if 文本.lower() == "q":
                break
            await self.会话.send(input=文本 or ".", end_of_turn=True)

    def _获取屏幕(self):
        sct = mss.mss()
        monitor = sct.monitors[0]
        i = sct.grab(monitor)

        img = PIL.Image.open(io.BytesIO(mss.tools.to_png(i.rgb, i.size)))
        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        return {
            "mime_type": "image/jpeg",
            "data": base64.b64encode(image_io.read()).decode()
        }

    async def 获取屏幕(self):
        while True:
            帧 = await asyncio.to_thread(self._获取屏幕)
            if 帧 is None:
                break
            await asyncio.sleep(1.0)
            await self.输出队列.put(帧)

    async def 发送实时(self):
        while True:
            数据包 = await self.输出队列.get()
            await self.会话.send(input=数据包)

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
        while True:
            数据 = await asyncio.to_thread(
                self.音频流.read,
                数据块大小,
                exception_on_overflow=False
            )
            await self.输出队列.put({"data": 数据, "mime_type": "audio/pcm"})

    async def 接收音频(self):
        CHUNK_SIZE = 3048
        while True:
            turn = self.会话.receive()
            async for response in turn:
                if 数据 := response.data:
                    for i in range(0, len(数据), CHUNK_SIZE):
                        小块 = 数据[i:i + CHUNK_SIZE]
                        self.音频输入队列.put_nowait(小块)
                if 文本 := response.text:
                    print(文本, end="")

            while not self.音频输入队列.empty():
                self.音频输入队列.get_nowait()

    async def 播放音频(self):
        播放流 = await asyncio.to_thread(
            音频库.open,
            format=音频格式,
            channels=声道数,
            rate=接收采样率,
            output=True,
        )
        while True:
            self.字节流 = await self.音频输入队列.get()
            await asyncio.to_thread(播放流.write, self.字节流)
            self.字节流 = None

    async def 字节流检测(self):
        while True:
            if self.字节流:
                数值 = [byte for byte in self.字节流]
                self.平均值2 = sum(数值) / len(数值)
            else:
                self.平均值2 = 0
            await asyncio.sleep(0.01)

    async def 运行(self):
        try:
            async with (
                客户端.aio.live.connect(model=模型, config=配置) as 会话,
                asyncio.TaskGroup() as 任务组,
            ):
                self.会话 = 会话
                self.音频输入队列 = asyncio.Queue()

                发送文本任务 = 任务组.create_task(self.发送文本())
                任务组.create_task(self.监听音频())
                任务组.create_task(self.发送实时())
                if self.视频模式 == "screen":
                    print("开启屏幕捕获")
                    任务组.create_task(self.获取屏幕())

                任务组.create_task(self.接收音频())
                任务组.create_task(self.播放音频())
                任务组.create_task(self.字节流检测())

                await 发送文本任务
                raise asyncio.CancelledError("用户请求退出")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            try:
                self.音频流.close()
            except Exception:
                pass
            traceback.print_exception(e)


if __name__ == "__main__":
    参数解析器 = argparse.ArgumentParser()
    参数 = 参数解析器.parse_args()
    主程序 = 音频循环(视频模式=False)
    asyncio.run(主程序.运行())
