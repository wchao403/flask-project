# 设置图片验证码的redis保存过期时间 单位：秒
IMAGE_CODE_REDIS_EXPIRES = 180
# 设置短信验证码redis有效期 单位：秒
SMS_CODE_REDIS_WXPIRES = 300
# 设置获取短信验证码的过期间隔时间 单位秒
SEND_SMS_CODE_EXPIRES = 60
# 登录次数的最大值
LOGIN_ERROR_MAX_TIMES = 500
# 登录次数验证时间间隔 600秒
LOGIN_ERROR_FORBID_TIME = 600
# 七牛云图片前面的域名
QINIU_URL_DOMAIN = 'http://qkjx4jzqb.hd-bkt.clouddn.com/'
# 地区有效期的过期时间7200秒
AREA_INFO_REDIS_CACHE_EXPIRES = 7200
# 首页返回的房屋数量，最多展示5个
HOME_PAGE_MAX_NUMS = 5
# 首页房屋轮播图的过期时间设置 7200秒
HOME_PAGE_DATA_REDIS_EXPIRES = 7200
# 详情房屋的过期时间
HOUSE_DETAIL_REDIS_EXPIRE = 7200
# 查询的时候每页显示的数据量
HOUSE_LIST_PAGE_NUMS = 2
# 搜索页面缓存的过期时间
HOUSE_LIST_PAGE_REDIS_CACHE_EXPIRES = 7200
# 详情页面的评论数量的展示
HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 2
