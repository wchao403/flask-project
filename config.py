import redis


class Config():
    """mysq的配置信息"""
    USERNAME = 'root'
    PASSWORD = 'root'
    HOST = '127.0.0.1'
    PORT = '3306'
    DATABASE = 'home'
    DB_URL = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8'.format(USERNAME, PASSWORD, HOST, PORT, DATABASE)
    SQLALCHEMY_DATABASE_URI = DB_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    """redis的配置信息"""
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379

    """flask-session,保存在不同的服务器中,是否签名，是否可以被别人知晓"""
    SESSION_TYPE = 'redis'
    SESSION_REDIS = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    SECRET_KEY = 'ASDFFSASEFEOFIGN'
    PERMANENT_SESSION_LIFETIOME = 8640  # 有效时间为一天单位是秒，不设置即为永久登录


class DevConfig(Config):
    """开发环境：用于编写和调试项目代码"""
    DEBUG = True


class ProConfig(Config):
    """生产环境：用于项目线上部署运行"""


config_map = {
    'dev': DevConfig,
    'pro': ProConfig
}
