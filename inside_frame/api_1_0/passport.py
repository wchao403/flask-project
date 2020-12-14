from . import api
import re, logging
from flask import request, jsonify, session
from inside_frame.response_code import RET
from inside_frame import redis_store, db, constants
from inside_frame.models import User
from sqlalchemy.exc import IntegrityError  # 数据库手机号重复插入时，捕获的异常


@api.route('/users', methods=['POST'])
def register():
    """
    注册
    :param 手机号 短信验证码 密码 确认密码
    :return:
    """
    request_dict = request.get_json()
    mobile = request_dict.get('mobile')
    sms_code = request_dict.get('sms_code')
    password = request_dict.get('password')
    password2 = request_dict.get('password2')
    # 验证
    if not all([mobile, sms_code, password, password2]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    # 判断手机号的格式
    if not re.match(r'1[345678]\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')
    if password != password2:
        return jsonify(errno=RET.PARAMERR, errmsg='两次密码不一致')
    # 业务逻辑
    # 从redis中取出短信验证码
    try:
        real_sms_code = redis_store.get('sms_code_%s' % mobile)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取短信验证码异常')
    # 判断短信验证是否过期
    if real_sms_code is None:
        return jsonify(errno=RET.NODATA, errmsg='短信验证码失效')
    # 删除redis中的短信验证码
    try:
        redis_store.delete('sms_code_%s' % mobile)
    except Exception as e:
        logging.error(e)
    # 判断用户填写的短信验证码的正确性
    real_sms_code = real_sms_code.decode()
    if real_sms_code != sms_code:
        return jsonify(errno=RET.DATAERR, errmsg='短信验证码错误')
    # 手机号是否被注册过 ，为了节省数据库的开销把手机号设置成唯一值，当手机号重复时，无法插入数据库
    # try:
    #     user = User.query.filter_by(mobile=mobile).first()
    # except Exception as e:
    #     logging.error(e)
    # else:
    #     if user is not None:
    #         # 表示手机号已经被注册了，已经存在在数据库当中了
    #         return jsonify(errno=RET.DATAEXIST, errmsg='手机号已经存在')
    # 保存数据
    user = User(name=mobile, mobile=mobile)
    # user.pwd_hash(password) 改变它为装饰器
    user.password = password
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error(e)
        return jsonify(errno=RET.DATAEXIST, errmsg='手机号已经存在')
    except Exception as e:
        db.session.rollback()  # 为了防止数据库中存在垃圾数据所以要回滚
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='插入数据库异常')
    # 保存登录状态到session中
    session['name'] = mobile
    session['mobile'] = mobile
    session['user_id'] = user.id
    # 返回结果
    return jsonify(errno=RET.OK, errmsg='注册成功')


@api.route('/sessions', methods=['POST'])
def login():
    # 登录接受参数
    request_dict = request.get_json()
    mobile = request_dict.get('mobile')
    password = request_dict.get('password')
    # 校验参数
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    if not re.match(r'1[345678]\d{9}', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机格式错误')
    # 业务逻辑处理
    # 判断错误次数是否超过限制，如果超过限制则直接返回通过ip查
    # redis 用户ip
    user_ip = request.remote_addr
    try:
        access_nums = redis_store.get('access_nums_%s' % user_ip)
    except Exception as e:
        logging.error(e)
    else:
        if access_nums is not None and int(access_nums) >= constants.LOGIN_ERROR_MAX_TIMES:
            return jsonify(RET.REQERR, errmsg='错误次数太多请稍后重试')
    # 从数据库中查询手机号是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取用户信息失败')
    # 验证密码
    if user is None or not user.check_pwd_hash(password):
        try:
            pl = redis_store.pipeline()
            pl.incr('access_nums_%s' % user_ip)
            pl.expire('access_nums_%s' % user_ip, constants.LOGIN_ERROR_FORBID_TIME)
            pl.execute()
        except Exception as e:
            logging.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='账号密码不匹配')
    # 保存登录状态
    session['name'] = user.name
    session['mobile'] = user.mobile
    session['user_id'] = user.id
    # 返回
    return jsonify(errno=RET.OK, errmsg='登录成功')


@api.route('/session', methods=['GET'])
def check_login():
    # 检验登录状态
    name = session.get('name')
    if name is not None:
        return jsonify(errno=RET.OK, errmsg='true', data={'name': name})
    else:
        return jsonify(errno=RET.SESSIONERR, errmsg='false')


@api.route('/session', methods=['DELETE'])
def login_out():
    # 退出登录清空session数据
    session.clear()
    return jsonify(errno=RET.OK, errmsg='ok')
