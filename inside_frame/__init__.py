from flask import Flask
from config import config_map
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
import redis, logging
from flask_wtf import CSRFProtect
from logging.handlers import RotatingFileHandler
from inside_frame.utils.commons import ReConverter

db = SQLAlchemy()
redis_store = None



def setup_log():
    # 设置日志的的登记  DEBUG调试级别
    logging.basicConfig(level=logging.DEBUG)
    # 创建日志记录器，设置日志的保存路径和每个日志的大小和日志的总大小 100M
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=100)
    # 创建日志记录格式，日志等级，输出日志的文件名 行数 日志信息
    formatter = logging.Formatter("%(levelname)s %(filename)s: %(lineno)d %(message)s")
    # 为日志记录器设置记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flaks app使用的）加载日志记录器
    logging.getLogger().addHandler(file_log_handler)


# 工厂模式
def create_app(config_name):
    setup_log()
    app = Flask(__name__)
    config_class = config_map.get(config_name)
    app.config.from_object(config_class)
    # 使用app初始化db
    db.init_app(app)
    global redis_store
    redis_store = redis.Redis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT)
    Session(app)
    CSRFProtect(app)

    # 为flask添加自定义的转换器
    app.url_map.converters['re'] = ReConverter
    # 注册蓝图
    from inside_frame import api_1_0
    app.register_blueprint(api_1_0.api)
    # 注册静态资源文件的蓝图
    from inside_frame import web_html
    app.register_blueprint(web_html.html)
    return app


'''session和post请求中的csrf验证'''
