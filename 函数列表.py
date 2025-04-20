
def get_current_temperature(位置: str) -> dict:
    """获取指定位置的当前温度。

    参数:
        位置: 城市和州，例如 "San Francisco, CA"

    返回:
        一个包含温度和单位的字典。
    """
    import web程序端语音程序
    web程序端语音程序.动作变量 = [1,1]

    # 实际实现可以调用天气API，这里先用模拟数据
    return {"温度": 25, "单位": "摄氏度"}


def do_action_by_emotion(emotion: str) -> dict:
    """
    此函数控制对话模型的动作,当你认为有必要进行下面动作时调用

    "开心", "失望", "恐惧"

    接收一个表示心情的字符串，并返回相同的内容。

    参数:
        emotion: 表示情绪的字符串，只能是 "开心", "失望", "恐惧" 其中之一

    返回:
        一个包含原始情绪的字典。
    """
    import web程序端语音程序
    web程序端语音程序.动作变量 = [1,1]

    return {"response": emotion}
