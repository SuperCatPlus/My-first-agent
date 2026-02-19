import tornado.ioloop
import tornado.web
import tornado.websocket
import paramiko
import json
import logging
import asyncio
import sys
import signal
from utils.src.token_utils import (
    generate_terminal_token,
    validate_terminal_token,
    deactivate_terminal_token,
    get_active_terminal_count
)

# 配置日志
logging.basicConfig(level=logging.INFO)

# 解决 tornado 与 asyncio 兼容问题（Python 3.8+ 需配置）
if 'win' in sys.platform:
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# SSH 连接类（优化终端尺寸适配）
class SSHConnection:
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.ssh = None
        self.channel = None

    def connect(self, cols=80, rows=24):
        """建立SSH连接，支持指定终端尺寸"""
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=10,
            allow_agent=False,  # 禁用SSH代理（局域网简化）
            look_for_keys=False  # 不查找本地密钥
        )
        # 创建交互式终端通道，适配xterm.js尺寸
        self.channel = self.ssh.invoke_shell(term='xterm-256color', width=cols, height=rows)
        self.channel.settimeout(0.0)
        logging.info(f"成功连接到 {self.host}:{self.port} (终端尺寸: {cols}x{rows})")

    def resize_pty(self, cols, rows):
        """调整终端尺寸（适配xterm.js窗口缩放）"""
        if self.channel and self.channel.active:
            self.channel.resize_pty(width=cols, height=rows)

    def send(self, data):
        if self.channel and self.channel.active:
            self.channel.send(data)

    def recv(self):
        try:
            if self.channel and self.channel.recv_ready():
                # 二进制数据直接返回，前端xterm.js自行解码
                return self.channel.recv(4096)
            return b""
        except Exception as e:
            logging.error(f"读取SSH数据失败: {e}")
            # 修复：统一拼接逻辑，先拼接字符串再转字节串（避免类型问题）
            error_msg = "[ERROR] 读取数据失败: " + str(e)
            return error_msg.encode('utf-8')

    def close(self):
        if self.channel:
            self.channel.close()
        if self.ssh:
            self.ssh.close()
        logging.info("SSH连接已关闭")

# WebSocket处理类（适配xterm.js）
class SSHWebSocketHandler(tornado.websocket.WebSocketHandler):
    def initialize(self):
        self.ssh_conn = None
        self.loop = None  # 异步读取SSH返回数据的循环
        self.current_token = None  # 当前连接的token
        self.ws_id = None  # WebSocket连接ID

    def open(self):
        import secrets
        # 生成WebSocket连接ID
        self.ws_id = secrets.token_urlsafe(16)
        logging.info(f"前端WebSocket连接已建立 (ws_id: {self.ws_id})")

    def on_message(self, message):
        try:
            data = json.loads(message)
            # 1. 登录请求
            if data["type"] == "login":
                logging.info(f"收到登录请求: {data['host']}:{data['port']}@{data['username']}")
                
                try:
                    self.ssh_conn = SSHConnection(
                        host=data["host"],
                        port=int(data["port"]),
                        username=data["username"],
                        password=data["password"]
                    )
                    # 初始化终端尺寸（默认80x24，xterm.js会自动调整）
                    self.ssh_conn.connect(cols=data.get("cols", 80), rows=data.get("rows", 24))
                    
                    # 生成token（使用token_utils模块，包含WebSocket状态）
                    self.current_token = generate_terminal_token(
                        host=data["host"],
                        port=int(data["port"]),
                        username=data["username"],
                        ws_status="connected",  # WebSocket已连接
                        ws_id=self.ws_id  # WebSocket连接ID
                    )
                    
                    logging.info(f"Token生成成功: {self.current_token[:20]}...")
                    
                    # 启动异步读取SSH返回数据的循环
                    asyncio.ensure_future(self.start_ssh_read_loop())
                    
                    # 返回成功消息和token
                    response_data = {
                        "type": "success", 
                        "msg": "✅ 已成功连接到 " + data["host"],
                        "token": self.current_token
                    }
                    
                    logging.info(f"准备返回token给前端: {response_data['token'][:20]}...")
                    self.write_message(json.dumps(response_data))
                    logging.info("Token已成功发送给前端")
                    
                except Exception as e:
                    logging.error(f"登录过程中发生错误: {str(e)}", exc_info=True)
                    self.write_message(json.dumps({
                        "type": "error", 
                        "msg": f"❌ 登录失败: {str(e)}"
                    }))
            
            # 2. 发送终端命令
            elif data["type"] == "command":
                if self.ssh_conn:
                    self.ssh_conn.send(data["data"].encode('utf-8'))
            
            # 3. 调整终端尺寸
            elif data["type"] == "resize":
                if self.ssh_conn:
                    self.ssh_conn.resize_pty(cols=data["cols"], rows=data["rows"])

        except Exception as e:
            logging.error(f"处理消息失败: {e}")
            self.write_message(json.dumps({"type": "error", "msg": f"❌ 错误: {str(e)}"}))

    async def start_ssh_read_loop(self):
        """异步循环读取SSH数据并推送给前端"""
        while self.ssh_conn:
            try:
                # 检查通道是否存在且活跃
                if not self.ssh_conn.channel or not self.ssh_conn.channel.active:
                    logging.info("SSH通道已关闭，准备关闭WebSocket连接")
                    break
                
                recv_data = self.ssh_conn.recv()
                if recv_data:
                    # 二进制数据转base64传输（避免编码问题）
                    import base64
                    self.write_message(json.dumps({
                        "type": "output",
                        "data": base64.b64encode(recv_data).decode('utf-8')
                    }))
                else:
                    # 尝试读取退出状态，判断会话是否真正结束
                    try:
                        # 检查通道是否真的关闭
                        if self.ssh_conn.channel.exit_status_ready():
                            logging.info(f"SSH会话已退出，退出状态: {self.ssh_conn.channel.recv_exit_status()}")
                            break
                    except:
                        pass
                await asyncio.sleep(0.05)  # 降低循环频率，减少资源占用
            except Exception as e:
                logging.error(f"异步读取失败: {e}")
                break
        # 当循环结束时，关闭WebSocket连接
        if hasattr(self, 'ws_connection') and self.ws_connection:
            logging.info("SSH会话已结束，关闭WebSocket连接")
            self.close()

    def on_close(self):
        # 使token失效（使用token_utils模块）
        if self.current_token:
            deactivate_terminal_token(self.current_token)
        
        if self.ssh_conn:
            self.ssh_conn.close()
        logging.info("WebSocket连接已关闭")

    def check_origin(self, origin):
        """允许跨域（局域网内任意设备访问）"""
        return True



# Token状态查询处理器
class TokenStatusHandler(tornado.web.RequestHandler):
    """Token状态查询处理器"""
    
    def get(self):
        """获取所有token状态"""
        try:
            logging.info("收到GET请求：查询所有token状态")
            
            # 获取活跃token数量
            active_count = get_active_terminal_count()
            
            logging.info(f"当前活跃token数量: {active_count}")
            
            response_data = {
                "status": "success",
                "active_count": active_count,
                "message": f"当前有 {active_count} 个活跃的终端连接"
            }
            
            logging.info(f"返回token状态: {response_data}")
            self.write(response_data)
            
        except Exception as e:
            logging.error(f"查询token状态时发生错误: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write({
                "status": "error",
                "message": str(e)
            })
    
    def post(self):
        """检查指定token的状态"""
        try:
            data = json.loads(self.request.body)
            token = data.get("token", "")
            
            logging.info(f"收到POST请求：验证token: {token[:20] if token else 'empty'}...")
            
            if not token:
                logging.warning("Token验证请求缺少token参数")
                self.set_status(400)
                self.write({
                    "status": "error",
                    "message": "缺少token参数"
                })
                return
            
            # 验证token（使用token_utils模块）
            token_info = validate_terminal_token(token)
            
            if token_info:
                logging.info(f"Token验证成功: {token_info['token_id']}")
                self.write({
                    "status": "success",
                    "valid": True,
                    "active": token_info.get("active", False),
                    "token_info": {
                        "host": token_info["host"],
                        "port": token_info["port"],
                        "username": token_info["username"],
                        "issued_at": token_info["issued_at"],
                        "expires_at": token_info["expires_at"]
                    }
                })
            else:
                logging.warning(f"Token验证失败: {token[:20]}...")
                self.write({
                    "status": "success",
                    "valid": False,
                    "active": False,
                    "message": "Token无效或已过期"
                })
                
        except Exception as e:
            logging.error(f"验证token时发生错误: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write({
                "status": "error",
                "message": str(e)
            })

# 路由配置
def make_app():
    return tornado.web.Application([
        (r"/ws", SSHWebSocketHandler),
        (r"/api/token/status", TokenStatusHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    # 监听8080端口，允许局域网访问
    app.listen(28081, address='0.0.0.0')
    logging.info("=== Python WebSSH (Xterm.js 版) 启动成功 ===")
    logging.info(f"访问地址: http://{sys.argv[1] if len(sys.argv)>1 else '127.0.0.1'}:28081")
    
    # 获取当前事件循环
    loop = tornado.ioloop.IOLoop.current()
    
    # 添加信号处理（支持 Ctrl+C 优雅退出）
    def signal_handler(signum, frame):
        logging.info("\n接收到中断信号，正在关闭服务器...")
        loop.stop()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    if 'win' not in sys.platform:
        signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        loop.start()
    except KeyboardInterrupt:
        logging.info("\n接收到 Ctrl+C，正在关闭服务器...")
    finally:
        logging.info("服务器已关闭")