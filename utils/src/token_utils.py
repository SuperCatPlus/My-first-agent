"""
Token工具模块 - 统一管理终端连接token
使用JWT实现无状态token，内存中维护活跃token集合用于快速查询
"""

import jwt
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from threading import Lock

# 配置日志
logger = logging.getLogger(__name__)

class TokenConfig:
    """Token配置类"""
    
    # JWT密钥（生产环境应从环境变量读取）
    SECRET_KEY = 'your-secret-key-change-this-in-production-12345678'
    
    # Token算法
    ALGORITHM = "HS256"
    
    # Token有效期（小时）
    TOKEN_EXPIRY_HOURS = 24
    
    # Token前缀
    TOKEN_PREFIX = "Bearer"


class TokenManager:
    """Token管理器 - 使用JWT实现无状态token"""
    
    def __init__(self):
        """初始化Token管理器"""
        # 活跃token集合（仅用于快速查询，不存储完整token信息）
        self.active_tokens: set = set()
        # 线程锁，保证线程安全
        self.lock = Lock()
        
        logger.info("Token管理器初始化完成")
    
    def generate_token(self, host: str, port: int, username: str, ws_status: str = "disconnected", ws_id: str = None) -> str:
        """
        生成新的JWT token
        
        Args:
            host: SSH主机地址
            port: SSH端口
            username: SSH用户名
            ws_status: WebSocket状态（connected/disconnected）
            ws_id: WebSocket连接ID
            
        Returns:
            JWT token字符串
        """
        # 生成token ID（用于标识和撤销）
        token_id = secrets.token_urlsafe(16)
        
        # 计算过期时间
        issued_at = datetime.utcnow()
        expires_at = issued_at + timedelta(hours=TokenConfig.TOKEN_EXPIRY_HOURS)
        
        # 构建JWT payload
        payload = {
            "jti": token_id,  # JWT ID
            "host": host,
            "port": port,
            "username": username,
            "ws_status": ws_status,  # WebSocket状态
            "ws_id": ws_id,  # WebSocket连接ID
            "iat": int(issued_at.timestamp()),  # issued at
            "exp": int(expires_at.timestamp())  # expiration
        }
        
        # 生成JWT token
        token = jwt.encode(payload, TokenConfig.SECRET_KEY, algorithm=TokenConfig.ALGORITHM)
        
        # 添加到活跃token集合
        with self.lock:
            self.active_tokens.add(token_id)
        
        logger.info(f"生成新token: {token_id} (主机: {host}:{port}, 用户: {username}, ws_status: {ws_status})")
        return token
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证token并返回token信息
        
        Args:
            token: JWT token字符串
            
        Returns:
            token信息字典，验证失败返回None
        """
        try:
            # 解析JWT token
            payload = jwt.decode(
                token,
                TokenConfig.SECRET_KEY,
                algorithms=[TokenConfig.ALGORITHM]
            )
            
            # 检查token是否在活跃集合中
            token_id = payload.get("jti")
            if token_id not in self.active_tokens:
                logger.warning(f"Token已被撤销: {token_id}")
                return None
            
            # 返回token信息
            return {
                "token_id": token_id,
                "host": payload.get("host"),
                "port": payload.get("port"),
                "username": payload.get("username"),
                "ws_status": payload.get("ws_status", "disconnected"),
                "ws_id": payload.get("ws_id"),
                "issued_at": payload.get("iat"),
                "expires_at": payload.get("exp"),
                "active": True
            }
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token已过期")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token无效: {str(e)}")
            return None
    
    def deactivate_token(self, token: str) -> bool:
        """
        使token失效（撤销）
        
        Args:
            token: JWT token字符串
            
        Returns:
            是否成功使token失效
        """
        try:
            # 解析token获取token_id
            payload = jwt.decode(
                token,
                TokenConfig.SECRET_KEY,
                algorithms=[TokenConfig.ALGORITHM],
                options={"verify_exp": False}  # 不验证过期时间
            )
            
            token_id = payload.get("jti")
            
            # 从活跃集合中移除
            with self.lock:
                if token_id in self.active_tokens:
                    self.active_tokens.remove(token_id)
                    logger.info(f"Token已失效: {token_id}")
                    return True
            
            return False
            
        except jwt.InvalidTokenError as e:
            logger.warning(f"使token失效失败: {str(e)}")
            return False
    
    def is_token_active(self, token: str) -> bool:
        """
        检查token是否有效且活跃
        
        Args:
            token: JWT token字符串
            
        Returns:
            token是否有效且活跃
        """
        token_info = self.validate_token(token)
        if not token_info:
            return False
        return token_info.get("active", False)
    
    def get_active_count(self) -> int:
        """
        获取活跃token数量
        
        Returns:
            活跃token数量
        """
        with self.lock:
            return len(self.active_tokens)
    
    def get_all_active_tokens_info(self) -> List[Dict[str, Any]]:
        """
        获取所有活跃token的信息（注意：此方法需要遍历所有token，性能较低）
        
        Returns:
            活跃token信息列表
        """
        # 由于我们只存储token_id，无法直接获取所有token信息
        # 这个方法主要用于调试，实际使用时建议使用其他方式
        return [
            {
                "token_id": token_id,
                "active": True
            }
            for token_id in self.active_tokens
        ]
    
    def cleanup_expired_tokens(self):
        """
        清理过期的token（从活跃集合中移除）
        注意：由于JWT是无状态的，过期token会自动验证失败
        这个方法主要用于清理内存中的活跃集合
        """
        # 由于我们只存储token_id，无法直接判断是否过期
        # 实际使用中，过期token会自动验证失败，无需手动清理
        pass


# 全局Token管理器实例
token_manager = TokenManager()


# 便捷函数
def generate_terminal_token(host: str, port: int, username: str, ws_status: str = "disconnected", ws_id: str = None) -> str:
    """
    生成终端连接token（便捷函数）
    
    Args:
        host: SSH主机地址
        port: SSH端口
        username: SSH用户名
        ws_status: WebSocket状态（connected/disconnected）
        ws_id: WebSocket连接ID
        
    Returns:
        JWT token字符串
    """
    return token_manager.generate_token(host, port, username, ws_status, ws_id)


def validate_terminal_token(token: str) -> Optional[Dict[str, Any]]:
    """
    验证终端连接token（便捷函数）
    
    Args:
        token: JWT token字符串
        
    Returns:
        token信息字典，验证失败返回None
    """
    return token_manager.validate_token(token)


def is_terminal_connected(token: str) -> bool:
    """
    检查终端是否已连接（便捷函数）
    
    Args:
        token: JWT token字符串
        
    Returns:
        终端是否已连接
    """
    return token_manager.is_token_active(token)


def deactivate_terminal_token(token: str) -> bool:
    """
    使终端连接token失效（便捷函数）
    
    Args:
        token: JWT token字符串
        
    Returns:
        是否成功使token失效
    """
    return token_manager.deactivate_token(token)


def get_active_terminal_count() -> int:
    """
    获取活跃终端连接数量（便捷函数）
    
    Returns:
        活跃终端连接数量
    """
    return token_manager.get_active_count()