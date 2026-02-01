
import sys
import time

def loading_animation(text="加载中", duration=3):
    """
    可控制时长的旋转加载动画
    :param text: 加载提示文字
    :param duration: 加载动画运行时长（秒，默认3秒）
    """
    chars = ['|', '/', '-', '\\']  # 旋转字符
    idx = 0
    start_time = time.time()  # 记录动画开始时间
    
    # 循环直到达到指定时长
    while time.time() - start_time < duration:
        sys.stdout.write(f"\r{text} {chars[idx % len(chars)]}")
        sys.stdout.flush()
        idx += 1
        time.sleep(0.2)  # 动画速度
    
    # 时长结束后，清空加载行并输出完成提示
    sys.stdout.write(f"\r{text} ✅ 完成\n")

loading_animation()