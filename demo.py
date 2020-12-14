'''融联云短信平台测试脚本'''
# from ronglian_sms_sdk import SmsSDK
# accId = '8aaf070875e449d70175f48b39ad06e9'
# accToken = 'f2154c75234a44329bd680dcf6fe9ff5'
# appId = '8aaf070875e449d70175f48b3a9d06f0'
# def send_message():
#     sdk = SmsSDK(accId, accToken, appId)
#     tid = '1'
#     mobile = '18329520409'
#     # datas传入一个元组第一个为验证码，第二个为过期的时间单位是分钟
#     datas = ('1234', '5')
#     resp = sdk.sendMessage(tid, mobile, datas)
#     print(resp)
# send_message()
'''七牛云图片平台保存'''
# from qiniu import Auth, put_file, etag
# import qiniu.config
# #需要填写你的 Access Key 和 Secret Key
# access_key = 'RhkClBw2Kf7P1hwtsyyv3LGM-unTDSfTi5ZuGGOh'
# secret_key = 'IJLrqbXS6XeBxQRNZWK-T1gpe4MHpv_oYzJ-v47S'
# #构建鉴权对象
# q = Auth(access_key, secret_key)
# #要上传的空间
# bucket_name = 'flask-image-store'
# #上传后保存的文件名
# key = 'my-python-logo.png'
# #生成上传 Token，可以指定过期时间等
# token = q.upload_token(bucket_name, None, 3600)
# #要上传文件的本地路径
# localfile = './01.png'
# ret, info = put_file(token, None, localfile)
# print(info)
# print('*'*50)
# print(ret)
# assert ret['key'] == key
# assert ret['hash'] == etag(localfile)

'''
<option value="1">东城区</option>
<option value="2">西城区</option>
<option value="3">朝阳区</option>
<option value="4">海淀区</option>
<option value="5">昌平区</option>
<option value="6">丰台区</option>
<option value="7">房山区</option>
<option value="8">通州区</option>
<option value="9">顺义区</option>
<option value="10">大兴区</option>
<option value="11">怀柔区</option>
<option value="12">平谷区</option>
<option value="13">密云区</option>
<option value="14">延庆区</option>
<option value="15">石景山区</option>
<option value="16">门头沟区</option>
                              '''
