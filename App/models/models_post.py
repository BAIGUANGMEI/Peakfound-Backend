from ..Middleware import db
from datetime import datetime

class Post(db.Model):
    __tablename__ = 'post'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(128), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tags = db.Column(db.String(255), nullable=True)
    server = db.Column(db.String(255), nullable=True)
    game_id = db.Column(db.String(256), nullable=False)
    game_name = db.Column(db.String(256), nullable=False)
    view_number = db.Column(db.Integer, default=0, nullable=False)
    like_number = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # 关联用户
    user = db.relationship('User', backref='posts')

    # 检查用户是否已点赞
    def has_liked(self, user_id):
        like = PostLike.query.filter_by(post_id=self.id, user_id=user_id).first()
        return like is not None

    # 添加点赞
    def add_like(self, user_id):
        if not self.has_liked(user_id):
            like = PostLike(post_id=self.id, user_id=user_id)
            db.session.add(like)
            self.like_number += 1

    # 取消点赞
    def remove_like(self, user_id):
        like = PostLike.query.filter_by(post_id=self.id, user_id=user_id).first()
        if like:
            db.session.delete(like)
            self.like_number -= 1

class PostImage(db.Model):
    __tablename__ = 'post_image'

    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    image_url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now())

    # 关联文章
    post = db.relationship('Post', backref=db.backref('images', lazy=True))

class PostLike(db.Model):
    __tablename__ = 'post_like'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now())

    # 关联文章和用户
    post = db.relationship('Post', backref=db.backref('likes', lazy=True))
    user = db.relationship('User', backref=db.backref('liked_posts', lazy=True))