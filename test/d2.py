# 原生ANSI转义序列设置字体颜色
def print_colored_text():
    # 红色字体（加粗）
    print("\033[1;31m这是红色加粗的文字\033[0m")
    # 绿色字体 + 黄色背景
    print("\033[0;32m这是绿色字体、黄色背景的文字\033[0m")
    # 蓝色下划线字体
    print("\033[4;34m这是蓝色下划线的文字\033[0m")
    # 恢复默认颜色后输出普通文字
    print("这是恢复默认颜色后的普通文字")

if __name__ == "__main__":
    # Windows系统需先启用ANSI支持（Python 3.6+）
    import sys
    if sys.platform == "win32":
        import subprocess
        # 启用Windows终端的ANSI转义支持
        subprocess.call("", shell=True)
    print_colored_text()