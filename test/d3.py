# 示例：任务完成后停止动画
import threading
import time, sys
# 示例：任务完成后停止动画
import threading
stop = False

def task():
    global stop
    time.sleep(3)  # 模拟耗时任务
    stop = True

threading.Thread(target=task).start()

# 带停止逻辑的加载
chars = ['|', '/', '-', '\\']
idx = 0
while not stop:
    sys.stdout.write(f"\r初始化智能体 {chars[idx % 4]}")
    sys.stdout.flush()
    idx += 1
    time.sleep(0.1)
sys.stdout.write("\r初始化智能体 ✅ 完成\n")  # 任务完成提示