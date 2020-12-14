from flask import Blueprint

api = Blueprint('api_1_0', __name__, url_prefix='/api/v1.0')
# 虽然蓝图已经定义了，也已经注册了，可以定义蓝图文件但是必须要在这里引入蓝图文件才可以使用
from . import demo, verify_code, passport, profile, house, orders, pay
