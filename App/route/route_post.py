from flask import Blueprint, request, jsonify
from ..models.models_user import User
from ..models.models_post import Post, PostImage
from ..Middleware import db, redis_client
from ..utils.access_control import login_required
from ..utils.upload_img import upload_multiple_images

post = Blueprint('post', __name__, url_prefix='/api')


# 新建文章
@post.route('/add/post', methods=['POST'])
@login_required
def add_post(user_id):
    try:
        title = request.form.get('title')
        content = request.form.get('content')
        tags = request.form.get('tags')
        server = request.form.get('server')
        game_id = request.form.get('game_id')
        game_name = request.form.get('game_name')

        if not title or not content:
            return jsonify({'msg': '缺少参数', 'code': 400})

        # 创建文章
        new_post = Post(title=title, content=content, author=user_id, tags=tags, server=server, game_id=game_id,
                        game_name=game_name)
        db.session.add(new_post)
        db.session.commit()

        # 处理图片上传
        if 'images' in request.files:
            files = request.files.getlist('images')
            try:
                image_urls = upload_multiple_images(files)
                for url in image_urls:
                    post_image = PostImage(post_id=new_post.id, image_url=url)
                    db.session.add(post_image)
            except ValueError as ve:
                # 删除已创建的文章
                db.session.delete(new_post)
                db.session.commit()
                return jsonify({'msg': '图片上传失败', 'error': str(ve), 'code': 400})

        db.session.commit()
        return jsonify({'msg': '文章发布成功', 'post_id': new_post.id, 'code': 200})

    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': '文章发布失败', 'error': str(e), 'code': 500})


# 获取文章信息
@post.route('/post/<int:post_id>', methods=['GET'])
@login_required
def get_post(user_id, post_id):
    try:
        post_obj = Post.query.get(post_id)
        if not post_obj:
            return jsonify({'msg': '文章不存在', 'code': 400})

        # 增加浏览量
        post_obj.view_number += 1
        db.session.commit()

        # 获取文章信息
        post_info = {
            'id': post_obj.id,
            'title': post_obj.title,
            'content': post_obj.content,
            'author': post_obj.author,
            'tags': post_obj.tags,
            'server': post_obj.server,
            'game_id': post_obj.game_id,
            'game_name': post_obj.game_name,
            'view_number': post_obj.view_number,
            'like_number': post_obj.like_number,
            'created_at': post_obj.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': post_obj.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'images': [image.image_url for image in post_obj.images]
        }

        return jsonify({'msg': '获取文章成功', 'post_info': post_info, 'code': 200})

    except Exception as e:
        return jsonify({'msg': '获取文章失败', 'error': str(e), 'code': 500})

# 获取所有文章列表
@post.route('/posts', methods=['GET'])
@login_required
def get_all_posts(user_id):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 30, type=int)

        # 使用分页查询
        posts = Post.query.paginate(page = page, per_page = per_page, error_out=False)

        post_list = []
        for post in posts.items:
            post_list.append({
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'images': [image.image_url for image in post.images],
                'author': post.author,
                'tags': post.tags,
                'server': post.server,
                'game_id': post.game_id,
                'game_name': post.game_name,
                'view_number': post.view_number,
                'like_number': post.like_number,
                'created_at': post.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'updated_at': post.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            })

        return jsonify({'msg': '获取文章列表成功', 'posts': post_list, 'total': posts.total, 'code': 200})

    except Exception as e:
        return jsonify({'msg': '获取文章列表失败', 'error': str(e), 'code': 500})

# 文章点赞
@post.route('/post/like', methods=['POST'])
@login_required
def like_post(user_id):
    try:
        post_id = request.json.get('post_id')
        post_obj = Post.query.get(post_id)
        if not post_obj:
            return jsonify({'msg': '文章不存在', 'code': 400})

        # 检查用户是否已点赞
        if post_obj.has_liked(user_id):
            return jsonify({'msg': '已点赞', 'code': 400})

        # 添加点赞记录
        post_obj.add_like(user_id)
        db.session.commit()
        return jsonify({'msg': '点赞成功', 'code': 200})

    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': '点赞失败', 'error': str(e), 'code': 500})


@post.route('/rank/game_id', methods=['GET'])
def get_top_10_game_id():
    # 从mysql数据库中获取被帖子使用最多的游戏ID和游戏名
    try:

        game_id_list = db.session.query(Post.game_id, db.func.count(Post.game_id).label('count')) \
            .group_by(Post.game_id) \
            .order_by(db.desc('count')).limit(10).all()

        game_name_list = [
            db.session.query(Post.game_name).filter(Post.game_id == game_id).first()
            for game_id, _ in game_id_list
        ]

        result = []
        for i in range(len(game_id_list)):
            result.append({
                'game_id': game_id_list[i][0],
                'game_name': game_name_list[i][0],
                'count': game_id_list[i][1]
            })

        return jsonify({'msg': '获取成功', 'game_ids': result, 'code': 200})
    except Exception as e:
        return jsonify({'msg': '获取失败', 'error': str(e), 'code': 500})

