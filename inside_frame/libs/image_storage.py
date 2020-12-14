from qiniu import Auth,put_data

# 需要填写你的 Access Key 和 Secret Key
access_key = 'RhkClBw2Kf7P1hwtsyyv3LGM-unTDSfTi5ZuGGOh'
secret_key = 'IJLrqbXS6XeBxQRNZWK-T1gpe4MHpv_oYzJ-v47S'


def storage(file_data):
    # 构建鉴权对象
    q = Auth(access_key, secret_key)
    # 要上传的空间
    bucket_name = 'flask-image-store'
    # 上传后保存的文件名
    key = 'my-python-logo.png'
    # 生成上传 Token，可以指定过期时间等
    token = q.upload_token(bucket_name, None, 3600)
    # 要上传文件的本地路径

    ret, info = put_data(token, None, file_data)
    if info.status_code == 200:
        return ret.get('key')
    else:
        raise Exception('上传图片失败')

# if __name__ == '__main__':
#     with open('./03.jpg','rb') as f:
#         res = storage(f.read())
#         print(res)
