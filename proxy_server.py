import asyncio
import aiohttp
from aiohttp import web, ClientSession, ClientTimeout
import logging
import os
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===================== 核心配置（根据你的实际路径修改）=====================
# 1. 后端服务配置
BACKEND_CONFIG = {
    "flask_api": {  # Flask 智能体API服务
        "host": "127.0.0.1",
        "port": 28080,
        "prefix": "/api"  # API请求前缀
    },
    "webssh_ws": {  # WebSSH WebSocket服务
        "host": "127.0.0.1",
        "port": 28081,
        "prefix": "/shell/ws",
        "target_path": "/ws"  # 目标路径，对应nginx的proxy_pass http://127.0.0.1:28081/ws
    },
    "webssh_api": {  # WebSSH API服务
        "host": "127.0.0.1",
        "port": 28081,
        "prefix": "/shell/api/"
    }
}

# 2. 前端静态文件配置（关键！指定你的前端文件目录）
FRONTEND_CONFIGS = [
    {
        "prefix": "/",  # 根路径访问，指向 static/chat/
        "root": os.path.join(os.path.dirname(__file__), "static/chat/"),  # 前端文件本地目录
        "index_file": "index.html"  # 前端入口文件
    },
    {
        "prefix": "/shell/",  # WebSSH前端访问路径
        "root": os.path.join(os.path.dirname(__file__), "static/shell/"),  # WebSSH前端文件本地目录
        "index_file": "WebSHell.html"  # WebSSH前端入口文件
    }
]

# 3. 超时配置
CLIENT_TIMEOUT = ClientTimeout(total=60)

# ===================== 静态文件处理函数 =====================
async def serve_frontend_file(request):
    """处理前端静态文件请求，模拟Nginx的alias/root逻辑"""
    request_path = request.path
    
    # 按前缀长度排序，优先匹配更长的前缀（避免根路径"/"匹配所有路径）
    sorted_configs = sorted(FRONTEND_CONFIGS, key=lambda x: len(x["prefix"]), reverse=True)
    
    # 遍历所有前端配置，匹配请求路径
    for config in sorted_configs:
        prefix = config["prefix"]
        
        # 检查请求路径是否以该配置的前缀开头
        if request_path.startswith(prefix):
            # 提取文件路径（去掉前缀）
            file_path = request_path[len(prefix):]
            
            # 处理根路径（返回前端入口文件）
            if file_path == "" or file_path == "/":
                file_path = f"/{config['index_file']}"
            
            # 拼接本地文件路径
            local_file_path = Path(config["root"]) / file_path.lstrip("/")
            
            # 检查文件是否存在
            if not local_file_path.exists() or not local_file_path.is_file():
                logger.warning(f"前端文件不存在: {local_file_path}")
                return web.Response(status=404, text="404 Not Found", content_type="text/plain")
            
            # 根据文件后缀设置Content-Type（模拟Nginx的mime类型）
            content_type = get_content_type(local_file_path.suffix)
            
            # 读取并返回文件
            try:
                with open(local_file_path, "rb") as f:
                    file_data = f.read()
                logger.info(f"返回前端文件: {local_file_path}")
                return web.Response(body=file_data, content_type=content_type)
            except Exception as e:
                logger.error(f"读取前端文件失败: {e}")
                return web.Response(status=500, text="Internal Server Error", content_type="text/plain")
    
    # 未匹配到任何前端配置
    logger.warning(f"未匹配到前端配置: {request_path}")
    return web.Response(status=404, text="404 Not Found", content_type="text/plain")

def get_content_type(suffix):
    """映射文件后缀到Content-Type，覆盖前端常用类型"""
    mime_map = {
        ".html": "text/html",
        ".css": "text/css",
        ".js": "application/javascript",
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".ico": "image/x-icon",
        ".svg": "image/svg+xml",
        ".woff2": "font/woff2",
        ".woff": "font/woff",
        ".ttf": "font/ttf",
        ".txt": "text/plain"
    }
    return mime_map.get(suffix.lower(), "application/octet-stream")

# ===================== 反向代理核心函数 =====================
async def reverse_proxy(request):
    """反向代理核心处理：API/WebSocket转发"""
    path = request.path
    method = request.method
    headers = dict(request.headers)
    
    # 1. 移除Host头，避免后端识别错误
    if 'Host' in headers:
        del headers['Host']
    
    # 2. 匹配后端服务
    target_service = None
    target_path = path
    
    # 匹配WebSSH WebSocket服务
    if path.startswith(BACKEND_CONFIG["webssh_ws"]["prefix"]):
        target_service = BACKEND_CONFIG["webssh_ws"]
        # 使用固定的target_path，对应nginx的配置
        target_path = target_service.get("target_path", "/")
    # 匹配WebSSH API服务
    elif path.startswith(BACKEND_CONFIG["webssh_api"]["prefix"]):
        target_service = BACKEND_CONFIG["webssh_api"]
        target_path = path[len(BACKEND_CONFIG["webssh_api"]["prefix"]):]
        if not target_path:
            target_path = "/"
    # 匹配Flask API服务
    elif path.startswith(BACKEND_CONFIG["flask_api"]["prefix"]):
        target_service = BACKEND_CONFIG["flask_api"]
        target_path = path[len(BACKEND_CONFIG["flask_api"]["prefix"]):]
        if not target_path:
            target_path = "/"
    # 未匹配到代理路径（理论上不会走到这，因为路由已优先匹配前端）
    else:
        return web.Response(status=404, text="404 Not Found")
    
    # 构建目标URL
    target_host = f"http://{target_service['host']}:{target_service['port']}"
    target_url = f"{target_host}{target_path}"
    
    try:
        # 处理WebSocket请求（WebSSH的ws连接）
        if request.headers.get("Upgrade", "").lower() == "websocket":
            logger.info(f"代理WebSocket -> {target_url}")
            return await handle_websocket_proxy(request, target_host, target_path)
        
        # 处理普通API请求
        logger.info(f"代理 {method} {path} -> {target_url}")
        
        # 转发请求到后端
        async with ClientSession(timeout=CLIENT_TIMEOUT) as session:
            async with session.request(
                method=method,
                url=target_url,
                headers=headers,
                data=await request.read(),
                params=request.query,
                allow_redirects=False
            ) as response:
                # 构建响应（添加跨域头）
                proxy_response = web.Response(
                    status=response.status,
                    headers=dict(response.headers),
                    body=await response.read()
                )
                proxy_response.headers['Access-Control-Allow-Origin'] = '*'
                proxy_response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
                proxy_response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
                return proxy_response
    
    except Exception as e:
        logger.error(f"代理失败: {str(e)}", exc_info=True)
        return web.Response(
            status=500,
            text=f"代理服务器错误: {str(e)}",
            content_type="text/plain"
        )

async def handle_websocket_proxy(request, target_host, target_path):
    """WebSocket代理适配"""
    ws_target_url = target_host.replace("http://", "ws://") + target_path
    client_ws = web.WebSocketResponse()
    await client_ws.prepare(request)
    
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(ws_target_url) as server_ws:
            # 双向转发消息
            async def forward_from_client():
                async for msg in client_ws:
                    if msg.type == web.WSMsgType.TEXT:
                        await server_ws.send_str(msg.data)
                    elif msg.type == web.WSMsgType.BINARY:
                        await server_ws.send_bytes(msg.data)
                    elif msg.type == web.WSMsgType.CLOSE:
                        await server_ws.close()
                        break
            
            async def forward_from_server():
                async for msg in server_ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await client_ws.send_str(msg.data)
                    elif msg.type == aiohttp.WSMsgType.BINARY:
                        await client_ws.send_bytes(msg.data)
                    elif msg.type == aiohttp.WSMsgType.CLOSE:
                        await client_ws.close()
                        break
            
            await asyncio.gather(forward_from_client(), forward_from_server())
    
    return client_ws

# ===================== 初始化代理服务器 =====================
async def init_app():
    """初始化代理服务器：优先匹配前端，再匹配代理"""
    app = web.Application()
    
    # 1. 前端静态文件路由（优先级最高）
    # 为每个前端配置添加路由
    for config in FRONTEND_CONFIGS:
        prefix = config["prefix"]
        # 匹配所有路径，返回前端文件
        app.router.add_route('GET', f"{prefix}{{path:.*}}", serve_frontend_file)
        # 匹配前缀根路径，重定向到入口文件
        if prefix != "/":
            app.router.add_route('GET', prefix.rstrip('/'), lambda r, cfg=config: web.HTTPFound(f"{cfg['prefix']}{cfg['index_file']}"))
    
    # 2. API/WebSocket代理路由
    # 匹配 /api/* 所有请求
    app.router.add_route('*', f"{BACKEND_CONFIG['flask_api']['prefix']}/{{path:.*}}", reverse_proxy)
    # 匹配 /shell/ws/* WebSocket请求
    app.router.add_route('*', f"{BACKEND_CONFIG['webssh_ws']['prefix']}/{{path:.*}}", reverse_proxy)
    # 匹配 /shell/api/* WebSSH API请求
    app.router.add_route('*', f"{BACKEND_CONFIG['webssh_api']['prefix']}/{{path:.*}}", reverse_proxy)
    # 单独匹配WebSocket根路径
    app.router.add_route('*', BACKEND_CONFIG['webssh_ws']['prefix'].rstrip('/'), reverse_proxy)
    
    return app

if __name__ == "__main__":
    # 检查所有前端目录是否存在
    for config in FRONTEND_CONFIGS:
        if not os.path.exists(config["root"]):
            logger.error(f"前端目录不存在: {config['root']}")
            logger.info(f"请修改 FRONTEND_CONFIGS 中对应的 root 为实际目录！")
            exit(1)
    
    # 启动代理服务器（默认端口8080）
    proxy_port = 8080
    app = asyncio.run(init_app())
    logger.info("="*50)
    logger.info(f"✅ 代理服务器启动成功 (端口: {proxy_port})")
    
    # 显示所有前端配置
    for config in FRONTEND_CONFIGS:
        prefix = config['prefix']
        if prefix == "/":
            logger.info(f"🌐 根路径: http://127.0.0.1:{proxy_port}/ → {config['root']}")
        else:
            logger.info(f"🌐 前端访问: http://127.0.0.1:{proxy_port}{prefix}")
    
    logger.info(f"🔌 API代理: /api/* → Flask服务 (http://{BACKEND_CONFIG['flask_api']['host']}:{BACKEND_CONFIG['flask_api']['port']})")
    logger.info(f"🖥️ WebSSH WebSocket: /shell/ws/* → WebSSH服务 (http://{BACKEND_CONFIG['webssh_ws']['host']}:{BACKEND_CONFIG['webssh_ws']['port']})")
    logger.info(f"📡 WebSSH API: /shell/api/* → WebSSH服务 (http://{BACKEND_CONFIG['webssh_api']['host']}:{BACKEND_CONFIG['webssh_api']['port']})")
    logger.info("="*50)
    web.run_app(app, host='0.0.0.0', port=proxy_port)