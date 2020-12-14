from ronglian_sms_sdk import SmsSDK
import json

accId = '8aaf070875e449d70175f48b39ad06e9'
accToken = 'f2154c75234a44329bd680dcf6fe9ff5'
appId = '8aaf070875e449d70175f48b3a9d06f0'


class CCP(object):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super().__new__(cls, *args, **kwargs)  # 参数一定要传够，不然会报错
            cls._instance.sdk = SmsSDK(accId, accToken, appId)  # 参数一定要传够，不然会报错
        return cls._instance

    def send_message(self, mobile, datas):
        # sdk = SmsSDK(accId, accToken, appId)
        sdk = self._instance.sdk
        # sdk = self.sdk 不能这样写，这样相当于有直接创建了sdk违背单例模式的初衷了
        tid = '1'
        # mobile = '18329520409'
        # datas传入一个元组第一个为验证码，第二个为过期的时间单位是分钟
        # datas = ('1234', '5')
        result = json.loads(sdk.sendMessage(tid, mobile, datas))
        # print(resp)
        if result['statusCode'] == '000000':
            return 0
        else:
            return -1
# if __name__ == '__main__':
#     c = CCP()
#     c.send_message('18329520409',('1234', '5'))
