from inside_frame.tasks.main import celery_app
from inside_frame.libs.message.ccp_sms import CCP


@celery_app.task
def send_sms(mobile, datas):
    '''发动短信的异步任务'''
    ccp = CCP()
    ccp.send_message(mobile, datas)
