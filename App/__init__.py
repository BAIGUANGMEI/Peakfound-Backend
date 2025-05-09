from flask import Flask
from .route.route_user import user
from .route.route_post import post
from .Middleware import init_middleware


def create_app():
    app = Flask(__name__)

    #注册蓝图
    app.register_blueprint(blueprint=user)#用户
    app.register_blueprint(blueprint=post)#文章

    app.config.from_object('config.DevelopmentConfig')


    init_middleware(app)

    return app