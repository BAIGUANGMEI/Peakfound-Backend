import os
import uuid
from werkzeug.utils import secure_filename
from minio import Minio
from minio.error import S3Error
import datetime

# 配置上传文件夹和允许的文件类型
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 获取 personnel_web 目录
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    """检查文件是否是允许的类型"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_multiple_images(files):

    # 设置 MinIO 客户端
    client = Minio("47.117.167.215:9000",
                   access_key="31911DvbVhPJfhu4l3De",
                   secret_key="5lwcyVjnuvweK36l9JunEwYdPSYwD4jKas5LU1hN",
                   secure=False
                   )

    """处理多图片上传"""
    image_urls = []
    for file in files:
        if file and allowed_file(file.filename):
            # 检查文件类型
            # 生成唯一文件名
            unique_id = uuid.uuid4().hex
            filename = f'PeakFound_{unique_id}_{datetime.datetime.now().strftime('%Y_%H_%M_%S')}.{file.filename.rsplit(".", 1)[1].lower()}'

            # 上传到 MinIO
            try:
                bucket_name = "webserver"
                minio_filename = filename

                found = client.bucket_exists(bucket_name)
                if not found:
                    client.make_bucket(bucket_name)
                    print("Created bucket", bucket_name)
                else:
                    print("Bucket", bucket_name, "already exists")

                # Upload the file, renaming it in the process
                client.put_object(bucket_name, minio_filename, file, -1, part_size=10*1024*1024)

                url = f'http://47.117.167.215:9000/webserver/{minio_filename}'

                image_urls.append(url)

            except S3Error as e:
                raise ValueError(f"MinIO 上传失败: {e}")
        else:
            raise ValueError("文件类型不被支持")
    return image_urls