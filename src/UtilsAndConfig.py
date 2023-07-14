import re
import os
import io
import json
import requests
from flask.json import JSONEncoder
from urllib.request import urlopen
from PIL import Image, ImageTk
import configparser
from urllib.parse import quote

# 自定义json编码类, 使用utf-8来编码返回 JSON 兼容的 Python 对象
class MyJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, str):  # 字符类型
            return str(obj, encoding='utf-8')
        if isinstance(obj, bytes):  # 字节类型
            return str(obj, encoding='utf-8')
        if isinstance(obj, object):
            return obj.get_json()
        return json.JSONEncoder.default(self, obj)


# HTTP和SOCKET 地址配置
class ServerConfig:
    def __init__(self):
        # 创建一个配置文件解释器
        cfg = configparser.ConfigParser()

        # os.path.join()函数用于路径拼接文件路径，可以传入多个路径
        # os.path.dirname(path)去掉文件名，返回目录
        # os.path.abspath(__file__)返回脚本的绝对路径
        # 这句话就是为了读取server.conf的文件路径, 就不用手敲了
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server.conf')

        # 读取一个名为file_path的配置文件
        cfg.read(file_path)

        # 得到不同分区下的配置信息
        self.SERVER_IP = str(cfg.get("server", "SERVER_IP"))  # IP信息
        self.HTTP_PORT = int(cfg.get("server", "HTTP_PORT"))  # http端口号
        self.SOCKET_PORT = int(cfg.get("server", "SOCKET_PORT"))  # socket端口号
        self.HTTP_SERVER_ADDRESS = 'http://' + self.SERVER_IP + ':' + str(self.HTTP_PORT)
        self.SOCKET_SERVER_ADDRESS = 'http://' + self.SERVER_IP + ':' + str(self.SOCKET_PORT)
        self.SQLALCHEMY_DATABASE_URI = str(cfg.get("server", "SQLALCHEMY_DATABASE_URI"))


serverConfig = ServerConfig()
# Socket通信常量 枚举
# 登录
USER_LOGIN = 'USER_LOGIN'
# 登录成功
USER_LOGIN_SUCCESS = 'USER_LOGIN_SUCCESS'
# 登录失败
USER_LOGIN_FAILED = 'USER_LOGIN_FAILED'
# 发送聊天消息
CHAT_SEND_MSG = 'FRIENDS_SEND_MSG'
# 发送聊天消息成功：对方在线
CHAT_SEND_MSG_SUCCESS = 'FRIENDS_SEND_MSG_SUCCESS'
# 发送聊天消息失败：对方离线
CHAT_SEND_MSG_ERR = 'FRIENDS_SEND_MSG_ERR'
# 新聊天消息
CHAT_HAS_NEW_MSG = 'FRIENDS_NEW_MSG'
# 好友状态改变
FRIENDS_ONLINE_CHANGED = 'FRIENDS_ONLINE_CHANGED'
# 好友/群数量改变
FRIENDS_GROUPS_COUNT_CHANGED = 'FRIENDS_GROUPS_COUNT_CHANGED'
# 发送消息验证
MESSAGE_SEND_MSG = 'MESSAGE_SEND_MSG'
# 新消息验证
MESSAGE_NEW_MSG = 'MESSAGE_NEW_MSG'
# 发送聊天文件
CHAT_SEND_FILE = 'CHAT_SEND_FILE'
# 发送聊天文件成功：对方在线
CHAT_SEND_FILE_SUCCESS = 'CHAT_SEND_FILE_SUCCESS'
# 发送聊天文件失败：对方离线
CHAT_SEND_FILE_ERR = 'CHAT_SEND_FILE_ERR'
# 新聊天文件
CHAT_HAS_NEW_FILE = 'CHAT_HAS_NEW_FILE'
# 强制退出
SYSTEM_LOGOUT = 'SYSTEM_LOGOUT'


# 登录名 字母开头 字母+数字组合 5-15位
def check_login_name(name):
    if name is None or len(name) < 5 or len(name) > 15:  # 空字符, 或者字符不在5-15之间
        return False
    if not name.encode('utf-8').isalnum():  # 检测字符串是否只由字母和数字组成
        return False
    if not re.match(r'[a-zA-Z][0-9a-zA-Z]', name):  # 正则表达式模式匹配, 第一个字符必须是字母，大小写不限。第二个字符必须是数字或字母，大小写不限。
        return False
    return True


# 处理换行符编码聊天信息   \n替换为/n
def encode_msg(msg):
    return str(msg).replace('\n', '/n')


# 解码 /n替换为\n
def decode_msg(msg):
    return msg.replace('/n', '\n')


# 得到本地聊天记录缓存路径
# 返回聊天缓存的路径
def get_local_cache_path(uid, is_friend, from_id, to_id, is_send):
    # 好友：/static/LocalCache/{uid}/friend/{toid}.crcd
    # 群：  /static/LocalCache/{uid}/group/{gid}.crcd
    # uid: 用户id
    # is_friend: 是不是朋友发的
    # from_id: 发送者id
    # to_id: 接收者id
    # 花括号 {} 可以用作占位符; \\表示单个的\
    path = '\\static\\LocalCache\\{uid}\\{type}\\{toid}.crcd'
    # 发送方
    if is_friend == 1:
        if is_send:
            path = path.replace('{uid}', str(from_id))
            path = path.replace('{toid}', str(to_id))
        else:
            path = path.replace('{uid}', str(to_id))
            path = path.replace('{toid}', str(from_id))
        path = path.replace('{type}', 'friends')
    else:
        path = path.replace('{uid}', str(uid))
        path = path.replace('{toid}', str(to_id))
        path = path.replace('{type}', 'groups')
    # os.path.abspath返回一个目录的绝对路径
    return os.path.abspath(os.path.dirname(__file__)) + path


# 从本地缓存文件中获取一条聊天记录，并将其解码成字符串。
def get_one_chat_record(is_friend, uid, to_id):
    path = get_local_cache_path(uid, is_friend, uid, to_id, True)
    check_path(path)
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # 取出最后一行作为聊天记录
        last_line = lines[-1]
    return decode_msg(last_line)


# 增加一条聊天记录到缓存中去
def add_one_chat_record(uid, is_friend, from_id, to_id, msg, is_send):
    record_path = get_local_cache_path(uid, is_friend, from_id, to_id, is_send)
    check_path(record_path)
    with open(record_path, 'a', encoding='utf-8') as f:
        f.write('\n' + encode_msg(msg))


# 检查是否存在文件, 如果不存在则创建, 并写入[[start]]
def check_path(path):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    if not os.path.exists(path):
        f = open(path, 'w', encoding='utf-8')
        f.write('[[start]]')


# 以下那些包含requests.get(url)的函数, 使用的接口都是在ChatServer中定义的接口
# @app.route('/getUsernameByUid', methods=['GET'])
# 通过用户id得到用户的姓名
def get_username_by_uid(uid):
    url = serverConfig.HTTP_SERVER_ADDRESS + '/getUsernameByUid?uid=' + str(uid)
    result_json = json.loads(requests.get(url).text)
    if result_json['code'] == 200:
        return result_json['data']
    return ''


# @app.route('/getGnameByGid', methods=['GET'])
# 在ChatHome.py和ChatWindow.py中使用
def get_group_name_by_gid(gid):
    url = serverConfig.HTTP_SERVER_ADDRESS + '/getGnameByGid?gid=' + str(gid)
    result_json = json.loads(requests.get(url).text)
    if result_json['code'] == 200:
        return result_json['data']
    return ''


# 按比例处理照片大小, 将图像缩放到给定的最大宽度和最大高度
def resize_image(is_http_img, path, max_w, max_h):
    if is_http_img:
        url = serverConfig.HTTP_SERVER_ADDRESS + path   # ip地址 + 路径
        file_name = url.split('/')[-1]
        quote_name = quote(file_name)
        url = url.replace(file_name, quote_name)
        image_bytes = urlopen(url).read()
        data_stream = io.BytesIO(image_bytes)
        img_open = Image.open(data_stream)
    else:
        img_open = Image.open(path)
    w, h = img_open.size
    if w <= max_w and h <= max_h:
        return ImageTk.PhotoImage(img_open)
    if (1.0 * w / max_w) > (1.0 * h / max_h):
        scale = 1.0 * w / max_w
    else:
        scale = 1.0 * h / max_h
    img_open = img_open.resize((int(w / scale), int(h / scale)), Image.ANTIALIAS)
    return ImageTk.PhotoImage(img_open)     # 使用 ImageTk.PhotoImage 将图像转换为 Tkinter 可用的图像格式
