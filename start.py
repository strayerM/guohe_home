import base64
import os
from flask import render_template
from flask import Flask, jsonify, request, make_response, send_from_directory
from werkzeug.utils import secure_filename
from functools import wraps
from util import response_info, db_util
app = Flask(__name__)
UPLOAD_FOLDER='/var/www/apk'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = set(['apk'])
# 用于判断文件后缀
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1] in ALLOWED_EXTENSIONS
def allow_cross_domain(fun):
    @wraps(fun)
    def wrapper_fun(*args, **kwargs):
        rst = make_response(fun(*args, **kwargs))
        rst.headers['Access-Control-Allow-Origin'] = '*'
        rst.headers['Access-Control-Allow-Methods'] = 'PUT,GET,POST,DELETE'
        allow_headers = "Referer,Accept,Origin,User-Agent"
        rst.headers['Access-Control-Allow-Headers'] = allow_headers
        return rst

    return wrapper_fun

#r = redis.Redis(host='127.0.0.1', port=6379, db=0)

@app.errorhandler(500)
def internal_server_error(e):
    app.logger.exception('error 500: %s', e)
    response = response_info.error(500,'internal server error',e)
    response.status_code = 500
    return response

@app.route("/apk/getApkInfo", methods=['GET'])
@allow_cross_domain
def download_apk_info():
    data=db_util.get_download_apk_info()
    return jsonify(data)

@app.route("/apk/download/<filename>", methods=['GET'])
@allow_cross_domain
def download_file(filename):
    # 需要知道2个参数, 第1个参数是本地目录的path, 第2个参数是文件名(带扩展名)
    directory = r'/var/www/apk'
    data = db_util.get_download_apk_info()
    serverVersion=data['info']['serverVersion']
    new_fileName=filename+serverVersion+r'.apk'
    #新增下载次数
    web_data=db_util.get_data()
    nowDownloads=web_data['downloads']
    db_util.set_downloads(nowDownloads+1)

    return send_from_directory(directory, new_fileName, as_attachment=True)
@app.route('/apk/upload',methods=['POST'],strict_slashes=False)
@allow_cross_domain
def upload():
    f = request.files['file']
    fname=secure_filename(f.filename)
    if allowed_file(fname):
        upload_path = os.path.join(r'/var/www/apk',secure_filename(f.filename))  #注意：没有的文件夹一定要先创建，不然会提示没有该路径
        f.save(upload_path)
        print(secure_filename(f.filename))
        token = base64.b64encode(secure_filename(f.filename).encode('utf-8'))
        return jsonify(response_info.success('上传成功',str(token)))
    else:
        return jsonify(response_info.error('801','文件类型不符合要求',''))
@app.route('/apk/updateInfo',methods=['POST'])
@allow_cross_domain
def app_download_info_update():
    download_info = request.get_json()
    data=db_util.update_download_apk_info(download_info)
    return jsonify(data)



@app.route("/getData")
@allow_cross_domain
def get_data():
    now_users=db_util.get_pxc_users()
    db_util.set_users(now_users)
    return jsonify(db_util.get_data())


@app.route("/")
@allow_cross_domain
def hello():
    web_datas=db_util.get_data()
    nowClicks_web=web_datas['clicks_web']
    print(nowClicks_web)
    afterClicks_web=int(nowClicks_web)+1
    db_util.set_clicks_web(str(afterClicks_web))
    return  render_template('index.html')


if __name__ == '__main__':
    from werkzeug.contrib.fixers import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app)
    app.run()
