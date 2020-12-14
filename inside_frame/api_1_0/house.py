from . import api
from datetime import datetime
from flask import request, jsonify, g, session
from inside_frame.response_code import RET
from inside_frame import redis_store, db, constants
from inside_frame.models import Area, House, Facility, HouseImage, User, Order
from inside_frame.utils.commons import login_required
from inside_frame.libs.image_storage import storage
import json, logging


@api.route('/areas')
def get_area_info():
    # 查询redis
    try:
        response_json = redis_store.get('area_info')
    except Exception as e:
        logging.error(e)
    else:
        if response_json is not None:
            response_json = json.loads(response_json)
            return jsonify(errno=RET.OK, errmsg='ok', data=response_json['data'])
            # return response_json,200,{'Content-Type': 'application/json'}
    try:
        area_li = Area.query.all()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')
    area_dict_li = []
    for area in area_li:
        area_dict_li.append(area.to_dict())
    # 保存列表数据到redis中,将数据转成字符串
    response_dict = dict(data=area_dict_li)
    # response_dict = dict(data=area_dict_li,errno=RET.OK, errmsg='ok')
    response_json = json.dumps(response_dict)
    try:
        redis_store.setex('area_info', constants.AREA_INFO_REDIS_CACHE_EXPIRES, response_json)
    except Exception as e:
        logging.error(e)
    return jsonify(errno=RET.OK, errmsg='ok', data=area_dict_li)
    # return response_json,200,{'Content-Type': 'application/json'} # 自己构建返回数据节省转化的代码


@api.route('/houses/info', methods=['POST'])
@login_required
def save_house_info():
    # 发布房源的用户
    user_id = g.user_id
    house_data = request.get_json()
    title = house_data.get("title")  # 房屋名称标题
    price = house_data.get("price")  # 房屋单价
    area_id = house_data.get("area_id")  # 房屋所属城区的编号
    address = house_data.get("address")  # 房屋地址
    room_count = house_data.get("room_count")  # 房屋包含的房间数目
    acreage = house_data.get("acreage")  # 房屋面积
    unit = house_data.get("unit")  # 房屋布局（几室几厅)
    capacity = house_data.get("capacity")  # 房屋容纳人数
    beds = house_data.get("beds")  # 房屋卧床数目
    deposit = house_data.get("deposit")  # 押金
    min_days = house_data.get("min_days")  # 最小入住天数 2
    max_days = house_data.get("max_days")  # 最大入住天数 1
    # 校验参数是否存在
    if not all(
            [title, price, area_id, address, room_count, acreage, unit, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    # 判断价格和押金是否输入的是数字校验
    try:
        price = int(float(price) * 100)  # 分
        deposit = int(float(deposit) * 100)  # 分
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='金额设置有误')
    # 判断区域id是否存在
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')
    if area is None:
        return jsonify(errno=RET.PARAMERR, errmsg='城区信息有误')
    # 保存房屋信息

    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        acreage=acreage,
        unit=unit,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days
    )
    # 关联设施信息和house表存入数据库
    facility_ids = house_data.get("facility")  # 设备信息，它是一个列表需要单独处理
    if facility_ids:
        # 查看数据库中设备是否存在防止别人用postman模拟恶意请求
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            logging.error(e)
            return jsonify(errno=RET.DBERR, errmsg='数据库异常')
        if facilities:
            # 关联合法的数据再后端应用多对多的模型,
            house.facilities = facilities
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='保存数据失败')
    # 返回结果
    return jsonify(errno=RET.OK, errmsg='ok', data=house.to_basic_dict())


@api.route('/houses/image', methods=['POST'])
@login_required
def save_house_img():
    """
    保存房屋的图片
    :return: 返回图片的url地址
    """
    # 接受参数
    image_file = request.files.get('house_image')
    house_id = request.form.get('house_id')
    # 校验参数
    if not all([image_file, house_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数不完整')
    try:
        house = House.query.get(house_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')
    if house is None:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')
    # 图片上传到七牛云
    image_data = image_file.read()
    try:
        filename = storage(image_data)
    except Exception as e:
        logging.error(e)
        return jsonify(RET.THIRDERR, errmsg='保存图片失败')
    # 保存图片hush名字到数据库
    house_image = HouseImage(house_id=house_id, url=filename)
    db.session.add(house_image)
    # 处理房屋的主图
    if not house.index_image_url:
        house.index_image_url = filename
        db.session.add(house)
    try:
        db.session.commit()
    except Exception as e:
        logging.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')
    image_url = constants.QINIU_URL_DOMAIN + filename
    return jsonify(errno=RET.OK, errmsg='ok', data={'image_url': image_url})


@api.route('/user/houses', methods=['GET'])
@login_required
def get_user_houses():
    """
    获取用户发布的房源
    :return: 发布的房源信息
    """
    # 获取当前用户
    user_id = g.user_id
    try:
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='获取数据失败')

    # 转成字典存在列表中
    house_li = []
    if houses:
        for house in houses:
            house_li.append(house.to_basic_dict())
    return jsonify(errno=RET.OK, errmsg='ok', data={'houses': house_li})


@api.route('/houses/index', methods=['GET'])
def get_house_index():
    '''
    获取首页房屋信息
    :return: 排序后的房屋信息
    '''
    # 查询数据库之前先查询缓存
    try:
        result = redis_store.get('house_page_data')
    except Exception as e:
        logging.error(e)
        result = None
    if result:
        return result.decode(), 200, {'Content-Type': 'application/json'}
    else:
        # 查询数据库，返回房屋信息最多的5条数据
        try:
            houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_NUMS).all()
        except Exception as e:
            logging.error(e)
            return jsonify(errno=RET.DBERR, errmsg='获取数据失败')
        if not houses:
            return jsonify(errno=RET.NODATA, errmsg='没有数据')
        houses_li = []
        for house in houses:
            houses_li.append(house.to_basic_dict())
        # 如果缓存中没有数据先加载缓存中去
        house_dict = dict(errno=RET.OK, errmsg='ok', data=houses_li)
        json_houses = json.dumps(house_dict)
        try:
            redis_store.setex('house_page_data', constants.HOME_PAGE_DATA_REDIS_EXPIRES, json_houses)
        except Exception as e:
            logging.error(e)
        return json_houses, 200, {'Content-Type': 'application/json'}
        # return jsonify(errno=RET.OK,errmsg='ok',data=houses_li)


@api.route('/houses/<int:house_id>', methods=['GET'])
def get_house_detail(house_id):
    """
    获取房屋信息
    :param house_id: ，房屋的id
    :return: 房屋的详细信息
    """
    # 当前用户的id防止自己刷单
    user_id = session.get('user_id', '-1')
    # 校验参数
    if not house_id:
        return jsonify(errno=RET.PARAMERR, errmsg='参数错误')
    # 从缓存中查询数据，首页的轮播图要优化,不能让用户频繁访问数据库
    try:
        result = redis_store.get('house_info_%s' % house_id)
    except Exception as e:
        logging.error(e)
        result = None
    if result:
        #     print('"errno":%s,"errmsg":"ok","data":{"house":%s,"user_id":%s}' % (RET.OK, result.decode(), user_id), 200, {
        #         'Content-Type': 'application/json'})
        return '{"errno":%s,"errmsg":"ok","data":{"house":%s,"user_id":%s}}' % (
            RET.OK, result.decode(), user_id), 200, {'Content-Type': 'application/json'}
    #     #     print(result.decode(),200, {'Content-Type': 'application/json'})
    #     #     return result.decode(),200, {'Content-Type': 'application/json'}
    # 查询数据库
    try:
        house = House.query.get(house_id)
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询数据库失败')
    # print(house) # <House 5>不用循环了，因为直接返回的是对象
    if not house:
        return jsonify(errno=RET.NODATA, errmsg='房屋不存在')
    house_data = house.to_full_dict()
    # house_data.update(errno=RET.OK, errmsg='ok', user_id=user_id)
    # 存入redis中
    json_house = json.dumps(house_data)
    try:
        redis_store.setex('house_info_%s' % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE, json_house)
    except Exception as e:
        logging.error(e)
    # print('*' * 20)
    # print(user_id, house_data)
    # print('%' * 20)
    return jsonify(errno=RET.OK, errmsg='ok', data={'house': house_data, 'user_id': user_id})


# http://127.0.0.1:5000/api/v1.0/houses?aid=2&sd=2020-12-08&ed=2020-12-25&sk=new&p=1
# aid 区域的id
# sd 开始入住的时间
# ed 结束的时间
# sk 排序
# p 页码
@api.route('/houses', methods=['GET'])
def get_house_list():
    # 接收参数
    area_id = request.args.get('aid')
    start_date = request.args.get('sd')
    end_date = request.args.get('ed')
    sort_key = request.args.get('sk')
    page = request.args.get('p')
    # 校验参数
    try:
        # print(start_date) # 2020-12-04 type ：str
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')  # 将str转成时间类型
        # print(start_date) # 2020-12-04 00:00:00  type ：<class 'datetime.datetime'>
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        if start_date and end_date:
            assert start_date <= end_date  # 断言，当条件不满足的时候触发一异常
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='日期参数有误')

    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            logging.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg='区域参数有误')
    if sort_key not in ('new', 'booking', 'price-inc', 'price-des'):
        return jsonify(errno=RET.PARAMERR, errmsg='排序参数有误')
    try:
        page = int(page)
    except Exception as e:
        logging.error(e)
        page = 1
    # 先查缓存数据
    redis_key = 'house_%s_%s_%s_%s' % (start_date, end_date, area_id, sort_key)
    try:
        resp_json = redis_store.hget(redis_key, page)
    except Exception as e:
        logging.error(e)
    else:
        if resp_json:
            return resp_json.decode(), 200, {'Content-Type': 'application/json'}

    # 查询数据库
    conflict_order = None
    # 将所有的过滤条件都放在列表中，通过解包去查询
    filter_params = []
    try:
        if start_date and end_date:
            # 查询冲突的订单房屋以及被预定
            conflict_order = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()
        elif start_date:
            conflict_order = Order.query.filter(Order.end_date >= start_date).all()
        elif end_date:
            conflict_order = Order.query.filter(Order.begin_date <= end_date).all()
    except Exception as e:
        logging.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库异常')
    if conflict_order:
        # 从订单中获取冲突的房屋订单
        conflict_house_id = [order.house_id for order in conflict_order]
        if conflict_house_id:
            # house = House.query.filter(House.id.notin_(conflict_house_id))
            # print(House.id.notin_(conflict_house_id),'1'*20)
            filter_params.append(House.id.notin_(conflict_house_id))
    if area_id:
        # 查询的条件
        filter_params.append(House.area_id == area_id)
        # filter_params.append("%s == %s" % (House.area_id,area_id))
    # print(type(House.area_id),House.area_id,area_id,'*'*20)
    # print(House.area_id == area_id)
    # print(*filter_params,'2'*20)
    # 排序
    if sort_key == 'booking':
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_key == 'price-inc':
        house_query = House.query.filter(*filter_params).order_by(House.price.asc())
    elif sort_key == 'price-des':
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else:
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())
    # 处理分页
    # house = House.query.filter(*filter_params)
    # paginate()page:当前页 per_page:每页显示多少个数据,error_out:自动输出错误
    page_obj = house_query.paginate(page=page, per_page=constants.HOUSE_LIST_PAGE_NUMS, error_out=False)
    # 总页数
    total_page = page_obj.pages
    # print(page_obj) # <flask_sqlalchemy.Pagination object at 0x000001BBBB36D408>
    house_li = page_obj.items
    # print(house_li) # [<House 7>, <House 6>]
    houses = []
    for house in house_li:
        houses.append(house.to_basic_dict())
    resp_dict = dict(errno=RET.OK, errmsg='ok', data={'total_page': total_page, 'houses': houses})
    resp_json = json.dumps(resp_dict)
    # 将数据保存到redis中通过hash类型来保存
    '''{
        '1':{1,2}, 第一页的房屋信息
        '2':{3,4}  第二页的房屋信息
    }'''
    try:
        # redis_key = 'house_%s_%s_%s_%s' % (start_date, end_date, area_id, sort_key)
        # 如果用户信息更改则可以手动删除缓存的数据redis_store.delete(key)
        pl = redis_store.pipeline()
        pl.hset(redis_key, page, resp_json)
        pl.expire(redis_key, constants.HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES)
        pl.execute()
    except Exception as e:
        logging.error(e)

    return jsonify(errno=RET.OK, errmsg='ok', data={'total_page': total_page, 'houses': houses})
# 搜索的数据放入redis中house_开始_区域ID_排序_页数
