from . import api
from flask import g, request, jsonify, session
from inside_frame.utils.commons import login_required
from inside_frame.response_code import RET
from inside_frame.libs.image_storage import storage
import logging
from inside_frame.models import User
from inside_frame import db, constants
from sqlalchemy.exc import IntegrityError


@api.route('/users/avatar', methods=['POST'])
@login_required
def set_user_avatar():
    """设置用户头像"""
    user_id = g.user_id
    # 获取图片
    image_file = request.files.get('avatar')  # 这是一个类
    if image_file is None:
        return jsonify(errno=RET.PARAMERR, errmsg='未上传图片')
    image_data = image_file.read()  # 获得图片的二进制数据
    # 上传图片到七牛云，调用第三方的东西一定要做异常处理
    try:
        file_name = storage(image_data)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='上传图片失败')
    # 保存地址到数据库中，只保存hash值取的时候再加上域名，未数据库减少压力，节省空间
    try:
        User.query.filter_by(id=user_id).update({'avatar_url': file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='保存图片信息上传失败')
    avatar_url = constants.QINIU_URL_DOMAIN + file_name
    print(avatar_url)
    return jsonify(errno=RET.OK, errmsg='保存成功', data={'avatar_url': avatar_url})


@api.route('/users/name', methods=['PUT'])
@login_required
def change_user_name():
    user_id = g.get('user_id')
    request_data = request.get_json()
    if not request_data:
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    name = request_data.get('name')
    try:
        user = User.query.filter_by(name=name).first()
    except Exception as e:
        logging.error(e)
    else:
        if user:
            return jsonify(errno=RET.DBERR, errmsg='用户名已存在')
    try:
        User.query.filter_by(id=user_id).update({'name': name})
        db.session.commit()
    # except IntegrityError as e:
    #     db.session.rollback()
    #     logging.error(e)
    #     return jsonify(errno=RET.DBERR, errmsg='用户名已存在')
    # 这个捕获不到重名异常，万能捕获也捕获不到这个错误所以再查询数据库之前自己定义一个方法去查询
    except Exception as e:
        db.session.rollback()
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='设置用户名错误')
    # 更新session数据
    session['name'] = name
    return jsonify(errno=RET.OK, errmsg='OK')


@api.route('/user', methods=['GET'])
@login_required
def get_user_profile():
    user_id = g.user_id
    try:
        user = User.query.get(user_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取用户信息失败')
    if user is None:
        return jsonify(errno=RET.NODATA, errmsg='获取用户信息失败')
    return jsonify(errno=RET.OK, errmsg='ok', data=user.to_dict())


@api.route('/users/auth', methods=['POST'])
@login_required
def set_user_auth():
    user_id = g.user_id
    response = request.get_json()
    id_card = response.get('id_card')
    real_name = response.get('real_name')
    if not all([id_card, real_name]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    try:
        # 实名认证的信息只能让他修改一次，如果里面有数据就不能让他继续修改
        User.query.filter_by(id=user_id, real_name=None, id_card=None).update(
            {'real_name': real_name, 'id_card': id_card})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据保存异常')
    return jsonify(errno=RET.OK, errmsg='ok')


@api.route('/users/auth', methods=['GET'])
@login_required
def get_user_auth():
    user_id = g.user_id
    try:
        user = User.query.get(user_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取用户信息失败')
    if user is None:
        return jsonify(errno=RET.NODATA, errmsg='获取用户信息失败')
    return jsonify(errno=RET.OK, errmsg='ok', data=user.auth_to_dict())
