# 提供静态资源文件的蓝图
from flask import Blueprint, current_app, make_response, session
from flask_wtf import csrf

html = Blueprint('web_html', __name__)


# 127.0.0.1:5000/  访问首页
# 127.0.0.1:5000/index.html 访问首页
# 127.0.0.1:5000/register.html 访问注册页面
# 路由转换,主要解决没有传的情况/不报错
@html.route('/<re(".*"):html_file_name>')
def get_html(html_file_name):
    # 访问首页
    if not html_file_name:
        html_file_name = 'index.html'
    # 加载图标，如果访问的不是favicon，再去拼接
    if html_file_name != 'favicon.ico':
        html_file_name = 'html/' + html_file_name
    response = make_response(current_app.send_static_file(html_file_name))
    # 当访问静态资源文件的时候给他们加上csrf验证，需要引入response，加在cookie中body还没有加
    csrf_token = csrf.generate_csrf()
    response.set_cookie('csrf_token', csrf_token)
    # return current_app.send_static_file(html_file_name)
    return response
