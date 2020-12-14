from . import api
from datetime import datetime
from flask import request, jsonify, g
from inside_frame.response_code import RET
from inside_frame import db
from inside_frame.models import House, Order
from inside_frame.utils.commons import login_required
import logging


@api.route('/orders', methods=['POST'])
@login_required
def save_order():
    '''
    保存订单
    end_date: 结束时间
    house_id: 房屋id
    start_date: 开始时间
    :return:
    '''
    # 接收参数
    user_id = g.user_id
    order_date = request.get_json()
    if not order_date:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    start_date = order_date.get('start_date')
    house_id = order_date.get('house_id')
    end_date = order_date.get('end_date')
    if not all([start_date, house_id, end_date]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        assert start_date <= end_date
        # datetime自带的获得天数的方法，获得天数
        days = (end_date - start_date).days + 1
        print(days)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='日期格式错误')
    try:
        house = House.query.get(house_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取房屋信息失败')
    if not house:
        return jsonify(errno=RET.NODATA, errmsg='房屋信息不存在')
    # 判断预定的房屋是不是自己，不能让房东自己刷单
    if user_id == house.user_id:
        return jsonify(errno=RET.ROLEERR, errmsg='不能预定自己的房屋')
    # 查询冲突时间的订单数量
    try:
        count = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date,
                                   Order.house_id == house_id).count()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='订单数据有误')
    if count > 0:
        return jsonify(errno=RET.DATAERR, errmsg='房屋已经被预定')
    # 保存订单数据
    amount = days * house.price
    order = Order(user_id=user_id, house_id=house_id, begin_date=start_date, end_date=end_date, days=days,
                  house_price=house.price, amount=amount)
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存订单失败')
    return jsonify(errno=RET.OK, errmsg='ok')


@api.route('/user/orders', methods=['GET'])
@login_required
def get_user_order():
    '''
    查询用户信息
    :param: role custom landlord
    :return:订单信息
    '''
    user_id = g.user_id
    role = request.args.get('role', '')
    try:
        if role == 'landlord':
            # 客户订单查询，查询谁定了我的房间
            # 先查询属于自己的房间
            houses = House.query.filter(House.user_id == user_id).all()
            house_id = [house.id for house in houses]
            # 根据房间的id查询预定房间的id
            orders = Order.query.filter(Order.house_id.in_(house_id)).order_by(Order.create_time.desc()).all()
        else:
            # 我的订单的查询
            orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc()).all()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询订单失败')
    orders_dict_list = []
    if orders:
        for order in orders:
            orders_dict_list.append(order.to_dict())
    return jsonify(errno=RET.OK, errmsg='ok', data={'orders': orders_dict_list})


@api.route('/orders/<int:order_id>/status', methods=['PUT'])
@login_required
def accept_reject_order(order_id):
    '''
    接单 拒单
    :param order_id: 订单id
    :return: json
    '''
    user_id = g.user_id
    # 接受参数
    request_data = request.get_json()
    if not request_data:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    action = request_data.get('action')
    if action not in ("reject", "accept"):
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    try:
        # 根据订单号查询数据库
        order = Order.query.filter(Order.id == order_id, Order.status == 'WAIT_ACCEPT').first()
        house = order.house
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='无法获得该订单')
    # 保证房东只能修改自己的房子的订单，不能修改别人的房子的订单,也就是说只有房东才能接单和拒单
    if house.user_id != user_id:
        return jsonify(errno=RET.REQERR, errmsg='操作无效')

    if action == 'accept':
        order.status = 'WAIT_PAYMENT'
    elif action == 'reject':
        order.status = 'REJECTED'
        reason = request_data.get('reason')
        if not reason:
            return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
        order.comment = reason
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='操作失败')
    return jsonify(errno=RET.OK, errmsg='ok')


@api.route('/orders/<int:order_id>/comment', methods=['PUT'])
@login_required
def save_order_comment(order_id):
    '''
    保存订单评论信息
    :param order_id: 订单id
    :return: json
    '''
    user_id = g.user_id
    # 接受参数
    request_data = request.get_json()
    comment = request_data.get('comment')
    if not comment:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    try:
        order = Order.query.filter(Order.id == order_id, Order.status == 'WAIT_COMMENT',
                                   Order.user_id == user_id).first()
        # 将房屋订单数量加1
        house = order.house
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='无法获取订单数据')
    if not order:
        return jsonify(errno=RET.DBERR, errmsg='没有订单数据操作无效')
    try:
        order.status = 'COMPLETE'
        order.comment = comment
        house.order_count += 1
        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='操作失败')
    return jsonify(errno=RET.OK, errmsg='OK')
