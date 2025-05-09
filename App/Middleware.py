from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_redis import FlaskRedis
from flask_cors import CORS


db=SQLAlchemy()
migrate=Migrate()
redis_client = FlaskRedis()

def init_middleware(app):
    db.init_app(app=app)
    migrate.init_app(app=app,db=db)
    redis_client.init_app(app)

    # 配置 CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

