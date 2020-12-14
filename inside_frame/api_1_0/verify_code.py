from . import api
from inside_frame.utils.captcha.captcha import captcha
import logging
import random
from flask import jsonify, make_response, request
from inside_frame import constants, redis_store
from inside_frame.response_code import RET
from inside_frame.models import User

"""
REST风格                         goods根据请求方式的不同，有不同的内容
/add_goods                       GET 查询
/update_goods                    POST 保存
/delete_goods                    PUT 修改
/get_goods                       DELETE 删除
"""


# UUID image_code_id :前端返回，将它作为参数传递给后端这个uuid作为标识符
# 用时间戳+随机数也可以作为唯一的标识符
# UUID: 验证码(string)
# GET 127.0.0.1/api/v1.0/image_codes/<image_code_id>
@api.route('/image_codes/<image_code_id>')
def get(image_code_id):
    # 验证参数image_code_id: 图片的编号
    # 业务逻辑处理，生成图片验证码
    text, image_data = captcha.generate_captcha()
    # 保存验证码
    try:
        redis_store.setex('image_code_%s' % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmag='保存图片验证码失败')
    response = make_response(image_data)
    response.headers['Content-Type'] = 'image/jpg'
    return response


@api.route('/sms_codes/<re(r"1[34578]\d{9}"):mobile>')
def get_sms_code(mobile):
    '''获取短信验证码'''
    # 获取图片验证码参数
    image_code = request.args.get('image_code')  # 图片验证码
    image_code_id = request.args.get('image_code_id')  # uuid
    # 校验图片验证码参数
    if not all([image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    # 业务逻辑，从redis取出图片验证码
    try:
        real_image_code = redis_store.get('image_code_%s' % image_code_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='redis数据库异常')
    # 判断图片验证码是否过期
    if real_image_code is None:
        return jsonify(errno=RET.NODATA, errmsg='图片验证码失效')
    # 没有过期删除redis中的图片验证码
    try:
        redis_store.delete('image_code_%s' % image_code_id)
    except Exception as e:
        logging.error(e)
    # print(real_image_code)  b'TKNE'
    # 与用户填写的图片验证码做对比
    real_image_code = real_image_code.decode()
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, errmsg='图片验证码错误')
    # 判断手机号是否是重复发送的代码，优化
    try:
        send_flag = redis_store.get('send_sms_code%s' % mobile)
    except Exception as e:
        logging.error(e)
    else:
        if send_flag is not None:
            return jsonify(errno=RET.REQERR, errmsg='请求过于频繁')
    # 判断手机号是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        logging.error(e)
    else:
        if user is not None:
            # 表示手机号已经被注册了，已经存在在数据库当中了
            return jsonify(errno=RET.DATAEXIST, errmsg='手机号已经存在')
    # 生成短信验证码
    sms_code = '%06d' % random.randint(0, 999999)
    # 保存真实的短息验证码到redis中
    try:
        pl = redis_store.pipeline()
        # redis_store.setex('sms_code_%s' % mobile, constants.SMS_CODE_REDIS_WXPIRES, sms_code)
        pl.setex('sms_code_%s' % mobile, constants.SMS_CODE_REDIS_WXPIRES, sms_code)
        # 保存发送给这个手机号的记录
        # redis_store.setex('send_sms_code%s' % mobile, constants.SEND_SMS_CODE_EXPIRES, 1)
        pl.setex('send_sms_code%s' % mobile, constants.SEND_SMS_CODE_EXPIRES, 1)
        pl.execute()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DATAERR, errmsg='保存短信验证码异常')
    # 发短信，返回值将它优化为celery分布式系统，避免前端反应延迟
    # try:
    #     ccp = CCP()
    #     result = ccp.send_message(mobile, (sms_code, int(constants.SMS_CODE_REDIS_WXPIRES / 60)))
    # except Exception as e:
    #     logging.error(e)
    #     return jsonify(errno=RET.THIRDERR, errmsg='发送异常')
    # from inside_frame.tasks.task_sms import send_sms # 异步发送的时候不能直接调用写的方法，一定要加上delay
    from inside_frame.tasks.sms.tasks import send_sms
    send_sms.delay(mobile, (sms_code, int(constants.SMS_CODE_REDIS_WXPIRES / 60)))

    # if result == 0:
    return jsonify(errno=RET.OK, errmsg='发送成功')
    # else:
    #     return jsonify(errno=RET.THIRDERR, errmsg='发送失败')
