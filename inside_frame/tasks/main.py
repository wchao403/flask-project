from celery import Celery

celery_app = Celery('home')
# 加载配置文件
celery_app.config_from_object('inside_frame.tasks.config')
# 注册任务
celery_app.autodiscover_tasks(['inside_frame.tasks.sms'])
# 启动命令
# celery -A inside_frame.tasks.main -l info -P eventl