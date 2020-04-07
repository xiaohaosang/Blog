import os
import sys

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# SQLite URI compatible
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'


class Operations:
    CONFIRM = 'confirm'
    RESET_PASSWORD = 'reset-password'
    CHANGE_EMAIL = 'change-email'


class BaseConfig:
    BLOG_SEARCH_RESULT_PER_PAGE = 10
    BLOG_NOTIFICATION_PER_PAGE =20
    BLOG_ARTICLE_PER_PAGE = 10
    BLOG_MANAGE_ARTICLE_PER_PAGE = 15
    BlOG_MANAGE_USER_PER_PAGE = 15
    BLOG_COMMENT_PER_PAGE = 15
    BLOG_USER_PER_PAGE = 20
    BLOG_UPLOAD_PATH = os.path.join(basedir, 'uploads')
    BLOG_MAIL_SUBJECT_PREFIX = '[BLOG]'
    BlOG_ALLOWED_IMAGE_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
    BLOG_ADMIN_EMAIL = "xiaohaosang@163.com"


    #BLOG_PHOTO_SIZE = {'small': 400,
    #                    'medium': 800}
    #BLOG_PHOTO_SUFFIX = {
    #    BLOG_PHOTO_SIZE['small']: '_s',  # thumbnail
    #    BLOG_PHOTO_SIZE['medium']: '_m',  # display
    #}

    SECRET_KEY = os.getenv('SECRET_KEY', 'secret string')
    # MAX_CONTENT_LENGTH = 3 * 1024 * 1024  # file size exceed to 3 Mb will return a 413 error response.

    BOOTSTRAP_SERVE_LOCAL = True

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    CKEDITOR_ENABLE_CSRF = True
    CKEDITOR_FILE_UPLOADER = 'user.upload_image'

    AVATARS_SAVE_PATH = os.path.join(BLOG_UPLOAD_PATH, 'avatars')
    AVATARS_SIZE_TUPLE = (30, 100, 200)

    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('BLOG Admin', MAIL_USERNAME)

    '''
    DROPZONE_ALLOWED_FILE_TYPE = 'image'
    DROPZONE_MAX_FILE_SIZE = 3
    DROPZONE_MAX_FILES = 30
    DROPZONE_ENABLE_CSRF = True
    '''
    WHOOSHEE_MIN_STRING_LEN = 1


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = \
        prefix + os.path.join(basedir, 'data-dev.db')
    REDIS_URL = "redis://localhost"


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'  # in-memory database


class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',
                                        prefix + os.path.join(basedir, 'data.db'))


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}