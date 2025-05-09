from functools import wraps
from flask import request, jsonify
from ..Middleware import redis_client

def get_user_id_from_token(token):
    """从 Redis 验证令牌并获取用户 ID"""
    user_id = redis_client.get(f'login_token:{token}')
    if user_id:
        return user_id.decode()
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')  # 从请求头中获取令牌

        if not token:
            return jsonify({'msg': 'Missing Token', 'code':400})

        # 验证令牌是否存在于 Redis
        user_id = None
        for key in redis_client.scan_iter(match='login_token:*'):
            if redis_client.get(key).decode() == token:
                user_id = key.decode().split(':')[1]
                break

        if not user_id:
            return jsonify({'msg': 'Token is Invalid or Expired', 'code':400})

        # 将用户 ID 添加到 kwargs 中，供后续使用
        kwargs['user_id'] = user_id
        return f(*args, **kwargs)
    return decorated_function