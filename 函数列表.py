def do_action_by_emotion(emotion: str) -> dict:
    """
    此函数控制对话模型的动作,根据与用户的对话的情绪调用不同动作

    接收一个表示心情的字符串，并返回相同的内容。

    参数:
        emotion: 表示情绪的字符串，只能是 "开心", "吃惊", "失望", "害羞" 其中之一

    返回:
        一个包含原始情绪的字典。
    """

    return {"response": emotion}
