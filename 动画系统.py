import threading
import time
import random


# 非线性插值函数，用来平滑过渡
def 非线性插值(开始, 结束, 因子):
    return 开始 + (结束 - 开始) * (1 - (1 - 因子) ** 3)  # 指数衰减函数


# 主线程任务：控制主变量随机变化
def 主变量线程():
    global 主变量, 从变量
    while True:

        # 让从变量逐渐接近新的主变量
        起始值 = 从变量
        目标值 = 主变量
        因子 = 0.0  # 从 0 到 1 的过渡因子
        while 因子 < 1.0:
            因子 += 0.05  # 每次更新 5%
            从变量 = 非线性插值(起始值, 目标值, 因子)
            print(f"从变量: {从变量:.2f}")
            time.sleep(0.1)  # 每次暂停 0.1 秒，模拟动画的更新过程

def 主变量更新():
    while True:
        global 主变量
        # 每5秒钟改变一次主变量的值
        主变量 = random.randint(60, 100)
        print(f"主变量变化为: {主变量}")
        time.sleep(10)



# 创建主变量和从变量
主变量 = 100
从变量 = 100

# 启动主线程
线程 = threading.Thread(target=主变量线程)
线程.daemon = True  # 使线程在主程序退出时自动结束
线程.start()

线程1 = threading.Thread(target=主变量更新)
线程1.daemon = True  # 使线程在主程序退出时自动结束
线程1.start()


# 主程序持续运行，打印从变量的值
while True:
    print(f"当前从变量的值是: {从变量:.2f}")
    time.sleep(1)  # 每秒打印一次当前从变量的值
