from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from ..models.models_user import User
from ..Middleware import db, redis_client
from ..utils.access_control import login_required, get_user_id_from_token
import datetime, uuid


user = Blueprint('user', __name__, url_prefix='/api')

# 用户注册
@user.route('/register', methods=['POST'])
def register():
    try:
        username = request.json.get('username')
        password = request.json.get('password')
        email = request.json.get('email')
        phone = request.json.get('phone')
        if not (username and password and email and phone):
            return jsonify({'msg': 'Missing Arguments','code': 400})

        # 检查是否已存在相同用户名、邮箱或手机号
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email) | (User.phone == phone)
        ).first()
        if existing_user:
            return jsonify({'msg': 'User Existed','code': 400})

        # 存储到数据库
        hashed_pw = generate_password_hash(password, salt_length=4)
        new_user = User(username=username, password=hashed_pw, email=email, phone=phone)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'msg': 'Sign Up Successful','code': 200})
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'Sign Up Fail', 'error': str(e),'code': 500})

# 用户登录
@user.route('/login', methods=['POST'])
def login():
    try:
        username = request.json.get('username')
        password = request.json.get('password')
        if not username or not password:
            return jsonify({'msg': 'Missing Arguments','code': 400})

        # 验证数据库用户
        user_obj = User.query.filter_by(username=username).first()
        if not user_obj or not check_password_hash(user_obj.password, password):
            return jsonify({'msg': 'Wrong Username or Password','code': 400})

        # 生成并缓存登录令牌
        token = str(uuid.uuid4())
        redis_client.setex('login_token:' + str(user_obj.id), 7 * 24 * 3600, token)
        return jsonify({'msg': 'Login Successful', 'token': token, 'username':username,'code': 200}), 200
    except Exception as e:
        return jsonify({'msg': 'Login Fail', 'error': str(e),'code': 500})

# 用户信息查询
@user.route('/profile', methods=['GET'])
@login_required
def profile(user_id):
    try:
        # 获取用户信息
        user_obj = User.query.get(user_id)
        if not user_obj:
            return jsonify({'msg': 'User not Existed','code': 400})

        # 返回用户信息
        return jsonify({
            'msg': 'Get UserInfo Successful',
            'id': user_obj.id,
            'username': user_obj.username,
            'email': user_obj.email,
            'phone': user_obj.phone,
            'created_at': user_obj.created_at,
            'updated_at': user_obj.updated_at,
            'code': 200
        })
    except Exception as e:
        return jsonify({'msg': 'Get UserInfo Fail', 'error': str(e),'code': 500})


# 用户信息更新
@user.route('/update', methods=['POST'])
@login_required
def update_profile(user_id):
    try:
        user_obj = User.query.get(user_id)

        username = request.json.get('username')
        email = request.json.get('email')
        phone = request.json.get('phone')

        if username:
            user_obj.username = username
        if email:
            user_obj.email = email
        if phone:
            user_obj.phone = phone

        # 更新更新时间
        user_obj.updated_at = datetime.datetime.now()

        db.session.commit()
        return jsonify({'msg': 'UserInfo Update Successful','code': 200})
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': 'UserInfo Update Fail', 'error': str(e),'code': 500})

# 验证token是否过期
@user.route('/verify/token', methods=['GET'])
def verify_token():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'msg': 'Missing Token','code': 400})

    # 验证令牌是否存在于 Redis
    for key in redis_client.scan_iter(match='login_token:*'):
        if redis_client.get(key).decode() == token:
            return jsonify({'msg': 'Token Valid','code': 200})

    return jsonify({'msg': 'Token is Invalid or Expired', 'code': 400})

