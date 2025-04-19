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

音频格式 = pyaudio.paInt16  # FORMAT = pyaudio.paInt16
声道数 = 1  # CHANNELS = 1
发送采样率 = 16000  # SEND_SAMPLE_RATE = 16000
接收采样率 = 24000  # RECEIVE_SAMPLE_RATE = 24000
块大小 = 1024  # CHUNK_SIZE = 1024

模型 = "models/gemini-2.0-flash-live-001"  # MODEL = "models/gemini-2.0-flash-live-001"

默认模式 = "screen"  # DEFAULT_MODE = "camera"

客户端 = genai.Client(  # client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=os.environ.get("GEMINI_API_KEY"),
)

# 虽然 Gemini 2.0 Flash 处于实验性预览模式，但此处只能传递 AUDIO 或 TEXT 中的一个。
配置 = types.LiveConnectConfig(  # CONFIG = types.LiveConnectConfig(
    response_modalities=[
        "audio",
    ],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Puck")
        )
    ),
)

音频对象 = pyaudio.PyAudio()  # pya = pyaudio.PyAudio()


class 音频循环:  # class AudioLoop:
    def __init__(self, 视频模式=默认模式):  # def __init__(self, video_mode=DEFAULT_MODE):
        self.视频模式 = 视频模式  # self.video_mode = video_mode

        self.音频输入队列 = None  # self.audio_in_queue = None
        self.输出队列 = None  # self.out_queue = None

        self.会话 = None  # self.session = None

        self.发送文本任务 = None  # self.send_text_task = None
        self.接收音频任务 = None  # self.receive_audio_task = None
        self.播放音频任务 = None  # self.play_audio_task = None

    async def 发送文本(self):  # async def send_text(self):
        while True:
            文本 = await asyncio.to_thread(  # text = await asyncio.to_thread(
                input,
                "消息 > ",  # "message > ",
            )
            if 文本.lower() == "q":  # if text.lower() == "q":
                break
            await self.会话.send(input=文本 or ".",
                                 end_of_turn=True)  # await self.session.send(input=text or ".", end_of_turn=True)

    def _获取帧(self, cap):  # def _get_frame(self, cap):
        # 读取帧 # Read the frameq
        ret, frame = cap.read()
        # 检查是否成功读取帧 # Check if the frame was read successfully
        if not ret:
            return None
        # 修复: 将 BGR 颜色空间转换为 RGB # Fix: Convert BGR to RGB color space
        # OpenCV 以 BGR 格式捕获，但 PIL 期望 RGB 格式 # OpenCV captures in BGR but PIL expects RGB format
        # 这可以防止视频馈送中的蓝色色调 # This prevents the blue tint in the video feed
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)  # 现在使用 RGB 帧 # Now using RGB frame
        img.thumbnail([1024, 1024])

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        mime_type = "image/jpeg"
        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    async def 获取帧(self):  # async def get_frames(self):
        # 这大约需要一秒钟，并且会阻塞整个程序
        # 如果你不 to_thread 它，会导致音频管道溢出。
        cap = await asyncio.to_thread(  # cap = await asyncio.to_thread(
            cv2.VideoCapture, 0
        )  # 0 代表默认摄像头 # 0 represents the default camera

        while True:
            帧 = await asyncio.to_thread(self._获取帧, cap)  # frame = await asyncio.to_thread(self._get_frame, cap)
            if 帧 is None:  # if frame is None:
                break

            await asyncio.sleep(1.0)

            await self.输出队列.put(帧)  # await self.out_queue.put(frame)

        # 释放 VideoCapture 对象 # Release the VideoCapture object
        cap.release()

    def _获取屏幕(self):  # def _get_screen(self):
        sct = mss.mss()
        monitor = sct.monitors[0]

        i = sct.grab(monitor)

        mime_type = "image/jpeg"
        image_bytes = mss.tools.to_png(i.rgb, i.size)
        img = PIL.Image.open(io.BytesIO(image_bytes))

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    async def 获取屏幕(self):  # async def get_screen(self):

        while True:
            帧 = await asyncio.to_thread(self._获取屏幕)  # frame = await asyncio.to_thread(self._get_screen)
            if 帧 is None:  # if frame is None:
                break

            await asyncio.sleep(1.0)

            await self.输出队列.put(帧)  # await self.out_queue.put(frame)

    async def 发送实时数据(self):  # async def send_realtime(self):
        while True:
            消息 = await self.输出队列.get()  # msg = await self.out_queue.get()
            await self.会话.send(input=消息)  # await self.session.send(input=msg)

    async def 监听音频(self):  # async def listen_audio(self):
        mic_info = 音频对象.get_default_input_device_info()  # mic_info = pya.get_default_input_device_info()
        self.音频流 = await asyncio.to_thread(  # self.audio_stream = await asyncio.to_thread(
            音频对象.open,  # pya.open,
            format=音频格式,  # format=FORMAT,
            channels=声道数,  # channels=CHANNELS,
            rate=发送采样率,  # rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=块大小,  # frames_per_buffer=CHUNK_SIZE,
        )
        if __debug__:
            kwargs = {"exception_on_overflow": False}
        else:
            kwargs = {}
        while True:
            数据 = await asyncio.to_thread(self.音频流.read, 块大小,
                                           **kwargs)  # data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
            await self.输出队列.put({"data": 数据,
                                     "mime_type": "audio/pcm"})  # await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})

    async def 接收音频(self):  # async def receive_audio(self):
        "后台任务，从 websocket 读取数据并将 pcm 块写入输出队列"  # "Background task to reads from the websocket and write pcm chunks to the output queue"
        while True:
            turn = self.会话.receive()  # turn = self.session.receive()
            async for response in turn:
                if 数据 := response.data:  # if data := response.data:
                    self.音频输入队列.put_nowait(数据)  # self.audio_in_queue.put_nowait(data)
                    continue
                if 文本 := response.text:  # if text := response.text:
                    print(文本, end="")  # print(text, end="")

            # 如果您中断模型，它会发送 turn_complete。
            # 为了使中断工作，我们需要停止播放。
            # 因此清空音频队列，因为它可能已加载
            # 比已经播放的音频多得多。
            while not self.音频输入队列.empty():  # while not self.audio_in_queue.empty():
                self.音频输入队列.get_nowait()  # self.audio_in_queue.get_nowait()

    async def 播放音频(self):  # async def play_audio(self):
        stream = await asyncio.to_thread(  # stream = await asyncio.to_thread(
            音频对象.open,  # pya.open,
            format=音频格式,  # format=FORMAT,
            channels=声道数,  # channels=CHANNELS,
            rate=接收采样率,  # rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        while True:
            bytestream = await self.音频输入队列.get()  # bytestream = await self.audio_in_queue.get()
            await asyncio.to_thread(stream.write, bytestream)  # await asyncio.to_thread(stream.write, bytestream)

    async def 运行(self):  # async def run(self):
        try:
            async with (
                客户端.aio.live.connect(model=模型,
                                        config=配置) as 会话,  # client.aio.live.connect(model=MODEL, config=CONFIG) as session,
                asyncio.TaskGroup() as 任务组,  # asyncio.TaskGroup() as tg,
            ):
                self.会话 = 会话  # self.session = session

                self.音频输入队列 = asyncio.Queue()  # self.audio_in_queue = asyncio.Queue()
                self.输出队列 = asyncio.Queue(maxsize=5)  # self.out_queue = asyncio.Queue(maxsize=5)

                发送文本任务 = 任务组.create_task(self.发送文本())  # send_text_task = tg.create_task(self.send_text())
                任务组.create_task(self.发送实时数据())  # tg.create_task(self.send_realtime())
                任务组.create_task(self.监听音频())  # tg.create_task(self.listen_audio())
                if self.视频模式 == "camera":  # if self.video_mode == "camera":
                    任务组.create_task(self.获取帧())  # tg.create_task(self.get_frames())
                elif self.视频模式 == "screen":  # elif self.video_mode == "screen":
                    任务组.create_task(self.获取屏幕())  # tg.create_task(self.get_screen())

                任务组.create_task(self.接收音频())  # tg.create_task(self.receive_audio())
                任务组.create_task(self.播放音频())  # tg.create_task(self.play_audio())

                await 发送文本任务  # await send_text_task
                raise asyncio.CancelledError("用户请求退出")  # raise asyncio.CancelledError("User requested exit")

        except asyncio.CancelledError:
            pass
        except ExceptionGroup as EG:
            self.音频流.close()  # self.audio_stream.close()
            traceback.print_exception(EG)


if __name__ == "__main__":
    解析器 = argparse.ArgumentParser()  # parser = argparse.ArgumentParser()
    解析器.add_argument(  # parser.add_argument(
        "--模式",  # "--mode",
        type=str,
        default=默认模式,  # default=DEFAULT_MODE,
        help="要流式传输的像素源",  # help="pixels to stream from",
        choices=["camera", "screen", "none"],
    )
    参数 = 解析器.parse_args()  # args = parser.parse_args()
    主程序 = 音频循环(视频模式=参数.模式)  # main = AudioLoop(video_mode=args.mode)
    asyncio.run(主程序.运行())  # asyncio.run(main.run())
