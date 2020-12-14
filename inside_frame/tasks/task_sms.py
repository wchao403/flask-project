from celery import Celery
from inside_frame.libs.message.ccp_sms import CCP

# 创建celery对象 redis 16个数据库0-15 使用的第一个数据库
celery_app = Celery('home',broker='redis://127.0.0.1:6379/1')
@celery_app.task
def send_sms(mobile, datas):
    '''发动短信的异步任务'''
    ccp = CCP()
    ccp.send_message(mobile, datas)
