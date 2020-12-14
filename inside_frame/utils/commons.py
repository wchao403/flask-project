from werkzeug.routing import BaseConverter
from flask import session, jsonify, g
from inside_frame.response_code import RET
import functools


class ReConverter(BaseConverter):
    def __init__(self, map, regex):
        # super(ReConverter, self).__init__() # python2的写法
        super().__init__(map)
        self.regex = regex


# 定义一个验证是否登录的装饰器, view_func是装饰的函数
def login_required(view_func):
    @functools.wraps(view_func)  # 保证原函数的属性
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        if user_id is not None:  # 已登录
            g.user_id = user_id  # 将user_id定义在全局里面方便以后调用
            return view_func(*args, **kwargs)
        else:
            return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')

    return wrapper
