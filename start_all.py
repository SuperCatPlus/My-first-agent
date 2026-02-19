"""
一键启动脚本
自动启动所有服务：web_server.py、WebSHell.py、proxy_server.py
"""

import subprocess
import sys
import os
import time
import signal
import atexit
from pathlib import Path

# 获取当前脚本所在目录
BASE_DIR = Path(__file__).parent.absolute()

# 服务配置
SERVICES = [
    {
        'name': '聊天服务',
        'script': 'web_server.py',
        'port': 28080,
        'description': 'Flask聊天API服务'
    },
    {
        'name': 'SSH终端服务',
        'script': 'WebSHell.py',
        'port': 28081,
        'description': 'Tornado WebSocket SSH终端'
    },
    {
        'name': '反向代理服务',
        'script': 'proxy_server.py',
        'port': 28087,
        'description': 'Flask反向代理服务器'
    }
]

# 存储子进程
processes = []

def check_port_in_use(port):
    """
    检查端口是否被占用
    
    Args:
        port (int): 端口号
    
    Returns:
        bool: 端口是否被占用
    """
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result == 0
    except:
        return False

def start_service(service_config):
    """
    启动单个服务
    
    Args:
        service_config (dict): 服务配置
    
    Returns:
        subprocess.Popen: 子进程对象
    """
    script_path = BASE_DIR / service_config['script']
    
    if not script_path.exists():
        print(f"❌ 脚本不存在: {script_path}")
        return None
    
    # 检查端口是否被占用
    if check_port_in_use(service_config['port']):
        print(f"⚠️  端口 {service_config['port']} 已被占用，跳过启动 {service_config['name']}")
        return None
    
    print(f"🚀 启动 {service_config['name']} (端口: {service_config['port']})...")
    
    try:
        # 创建子进程
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=str(BASE_DIR),
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
        )
        return process
    except Exception as e:
        print(f"❌ 启动 {service_config['name']} 失败: {e}")
        return None

def stop_all_services():
    """
    停止所有服务
    """
    print("\n" + "=" * 60)
    print("🛑 正在停止所有服务...")
    print("=" * 60)
    
    for i, process in enumerate(processes):
        if process and process.poll() is None:
            service_name = SERVICES[i]['name']
            try:
                print(f"🛑 停止 {service_name}...")
                if sys.platform == 'win32':
                    process.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    process.terminate()
                
                # 等待进程结束
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"⚠️  {service_name} 未在5秒内结束，强制终止...")
                    process.kill()
                    process.wait()
                
                print(f"✅ {service_name} 已停止")
            except Exception as e:
                print(f"❌ 停止 {service_name} 失败: {e}")
    
    print("=" * 60)
    print("✅ 所有服务已停止")
    print("=" * 60)

def wait_for_service(port, service_name, timeout=30):
    """
    等待服务启动
    
    Args:
        port (int): 服务端口
        service_name (str): 服务名称
        timeout (int): 超时时间（秒）
    
    Returns:
        bool: 服务是否成功启动
    """
    print(f"⏳ 等待 {service_name} 启动...")
    
    for i in range(timeout):
        if check_port_in_use(port):
            print(f"✅ {service_name} 启动成功 (耗时 {i+1}秒)")
            return True
        time.sleep(1)
    
    print(f"❌ {service_name} 启动超时")
    return False

def main():
    """
    主函数
    """
    print("=" * 60)
    print("🚀 一键启动所有服务")
    print("=" * 60)
    print(f"📁 工作目录: {BASE_DIR}")
    print(f"🐍 Python版本: {sys.version}")
    print("=" * 60)
    
    # 注册退出处理函数
    atexit.register(stop_all_services)
    
    # 检查依赖
    print("\n📦 检查依赖包...")
    required_packages = ['flask', 'tornado', 'paramiko', 'requests']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (未安装)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ 缺少依赖包，请运行: pip install {' '.join(missing_packages)}")
        return
    
    # 启动服务
    print("\n" + "=" * 60)
    print("🚀 开始启动服务")
    print("=" * 60)
    
    for service_config in SERVICES:
        process = start_service(service_config)
        if process:
            processes.append(process)
            
            # 等待服务启动
            if not wait_for_service(service_config['port'], service_config['name']):
                print(f"⚠️  {service_config['name']} 启动失败，继续启动其他服务...")
        else:
            processes.append(None)
    
    # 显示启动结果
    print("\n" + "=" * 60)
    print("📊 服务启动结果")
    print("=" * 60)
    
    for i, (service_config, process) in enumerate(zip(SERVICES, processes)):
        if process and process.poll() is None:
            print(f"✅ {service_config['name']}: http://localhost:{service_config['port']}")
        else:
            print(f"❌ {service_config['name']}: 启动失败")
    
    # 显示访问信息
    print("\n" + "=" * 60)
    print("🌐 访问地址")
    print("=" * 60)
    print(f"🏠 主界面: http://localhost:28087")
    print(f"💬 聊天界面: http://localhost:28087/")
    print(f"🖥️  SSH终端: http://localhost:28087/shell/")
    print(f"📊 健康检查: http://localhost:28087/api/health")
    print("=" * 60)
    print("💡 提示: 按 Ctrl+C 停止所有服务")
    print("=" * 60)
    
    # 保持运行
    try:
        while True:
            # 检查进程状态
            for i, (service_config, process) in enumerate(zip(SERVICES, processes)):
                if process and process.poll() is not None:
                    print(f"⚠️  {service_config['name']} 已停止 (退出码: {process.poll()})")
            
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n\n接收到中断信号...")
        stop_all_services()

if __name__ == '__main__':
    main()