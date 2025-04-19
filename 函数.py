def 数值转颜色(value, 最小值=0, 最大值=250):
    """
    将数值映射为颜色（从#00FFFF到#FFFFFF），越大越白，越小越蓝。
    value: 输入数值
    最小值、最大值：用于归一化 value 到 0~1
    返回: RGB颜色字符串，例如 "#80FFFF"
    """
    # 防止除零，确保 value 在[min, max]之间
    value = max(最小值, min(value, 最大值))
    t = (value - 最小值) / (最大值 - 最小值)

    # 起始色: #00FFFF → R=0, G=255, B=255
    # 目标色: #FFFFFF → R=255, G=255, B=255
    R = int(0 + (255 - 0) * t)
    G = 255
    B = 255

    return f"#{R:02X}{G:02X}{B:02X}"
