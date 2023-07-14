from flask import Flask
from flask import request
from flask_sqlalchemy import SQLAlchemy
import json
import UtilsAndConfig
import os
import datetime
import uuid
import hashlib
import socket
import threading
from UtilsAndConfig import ServerConfig
from wsgiref.simple_server import make_server
import sys

import MyDES
import utils
import des_setting

# 初始化flask实例
app = Flask(__name__)

# 配置
serverConfig = ServerConfig()
FILES_PATH = os.path.abspath(os.path.dirname(__file__)) + '/static'
if not os.path.exists(FILES_PATH):
    os.mkdir(FILES_PATH)
# 数据库配置
# 设置连接数据库的URL
app.config['SQLALCHEMY_DATABASE_URI'] = serverConfig.SQLALCHEMY_DATABASE_URI
# 设置每次请求结束后会自动提交数据库的改动
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# 查询时显示原始SQL语句
app.config['SQLALCHEMY_ECHO'] = False

# 连接数据库
db = SQLAlchemy(app)
online_users = dict()

# socket监听
mySocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # IPv4 协议，TCP 协议传输数据。
mySocket.bind((serverConfig.SERVER_IP, serverConfig.SOCKET_PORT))  # 将套接字对象绑定到一个指定的 IP 地址和端口号
mySocket.listen(10)  # 最多可以接受的连接数，这里是 10


# 对象转json时编码

# 结果集定义: 以'codes'为200或者400区分请求成功与否
class Result:
    @staticmethod
    def success(data):
        return json.dumps({'code': 200, 'data': data, 'message': ''},
                          cls=UtilsAndConfig.MyJSONEncoder, ensure_ascii=False)

    @staticmethod
    def fail(message):
        return json.dumps({'code': 400, 'data': '', 'message': message},
                          cls=UtilsAndConfig.MyJSONEncoder, ensure_ascii=False)


# 数据库实体类定义
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pwd = db.Column(db.String(36), nullable=False)
    loginName = db.Column(db.String(50), nullable=False, unique=True)
    username = db.Column(db.String(50), nullable=False)
    sex = db.Column(db.Integer, nullable=False)
    picUrl = db.Column(db.String(200), nullable=False)
    updateTime = db.Column(db.DateTime(), nullable=False)

    def get_json(self):
        return {
            'id': self.id,
            'pwd': '',
            'loginName': self.loginName,
            'username': self.username,
            'sex': self.sex,
            'picUrl': self.picUrl,
            'updateTime': self.updateTime.strftime('%Y-%m-%d %H:%M:%S')
        }


class Friends(db.Model):
    __tablename__ = 'friends'  # 表的名称
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uid = db.Column(db.Integer, nullable=False)
    friendId = db.Column(db.Integer, nullable=False)
    updateTime = db.Column(db.DateTime(), nullable=False)

    def get_json(self):
        return {
            'id': self.id,
            'uid': self.uid,
            'friendId': self.friendId,
            'gname': self.gname,
            'updateTime': self.updateTime.strftime('%Y-%m-%d %H:%M:%S')
        }


class GroupChat(db.Model):
    __tablename__ = 'groupChat'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    createUid = db.Column(db.Integer, nullable=False)
    gname = db.Column(db.String(50), nullable=False)
    updateTime = db.Column(db.DateTime(), nullable=False)

    def get_json(self):
        return {
            'id': self.id,
            'createUid': self.createUid,
            'gname': self.gname,
            'updateTime': self.updateTime.strftime('%Y-%m-%d %H:%M:%S')
        }


class GroupMembers(db.Model):
    __tablename__ = 'groupMembers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gId = db.Column(db.Integer, nullable=False)
    uId = db.Column(db.Integer, nullable=False)
    joinTime = db.Column(db.DateTime(), nullable=False)

    def get_json(self):
        return {
            'id': self.id,
            'gId': self.gId,
            'uId': self.uId,
            'joinTime': self.joinTime.strftime('%Y-%m-%d %H:%M:%S')
        }


# -- //验证消息
# -- //type: 1:添加好友  2:申请入群  3:邀请入群
# -- //handle: 0:未处理 1:同意  2:拒绝
# -- //gId：当type为2、3时有效
# -- message(id, fromUid, toUid, type, gId, sendTime, handle, handleTime)
class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fromUid = db.Column(db.Integer, nullable=False)
    toUid = db.Column(db.Integer, nullable=False)
    type = db.Column(db.Integer, nullable=False)
    gId = db.Column(db.Integer, nullable=False)
    handle = db.Column(db.Integer, nullable=False)
    sendTime = db.Column(db.DateTime(), nullable=False)
    handleTime = db.Column(db.DateTime(), nullable=True)

    def get_json(self):
        handel_time_text = ''
        if self.handleTime is not None:
            handel_time_text = self.handleTime.strftime('%Y-%m-%d %H:%M:%S')
        return {
            'id': self.id,
            'fromUid': self.fromUid,
            'toUid': self.toUid,
            'type': self.type,
            'gId': self.gId,
            'handle': self.handle,
            'sendTime': self.sendTime.strftime('%Y-%m-%d %H:%M:%S'),
            'handleTime': handel_time_text
        }


# controller定义
# 这段代码是一个 Python Flask 网络应用程序的后端代码，
# 用于处理客户端通过 GET 方法请求的名为 checkLoginName 的接口。
# 当客户端请求该接口时，将会执行 check_login_name() 函数。
@app.route('/checkLoginName', methods=['GET'])
def check_login_name():
    try:
        name = request.args.get("name")
        if not UtilsAndConfig.check_login_name(name):
            # Result.fail是自定义的
            return Result.fail('用户名不合法！')
        # 查询数据库是否已存在
        users = Users.query.filter_by(loginName=name).all()
        if len(users) == 0:
            return Result.success('OK')
        else:
            return Result.fail('登录名已存在！')
    except Exception as e:
        print(e.message)
        return Result.fail('参数异常')


@app.route('/register', methods=['POST'])
def register():
    try:
        files = request.files['file']
        head_pic_path = FILES_PATH + '/' + 'headPic/'
        if not os.path.exists(head_pic_path):
            os.mkdir(head_pic_path)
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        head_pic_path = head_pic_path + today + '/'
        if not os.path.exists(head_pic_path):
            os.mkdir(head_pic_path)
        # uuid.uuid1()用于生成一个唯一的字符
        filename = str(uuid.uuid1()) + '.jpg'
        files.save(head_pic_path + filename)

        params = request.values
        pic_url = '/static/headPic/' + today + "/" + filename
        login_name = params['loginName']
        name = params['name']
        sex = params['sex']
        pwd1 = params['pwd1']
        pwd2 = params['pwd2']

        users = Users.query.filter_by(loginName=login_name).all()
        if len(users) > 0:
            return Result.fail('登录名已存在！')
        if pwd2 != pwd1:
            return Result.fail('重复密码不正确！')

        # 密码md5加密
        md5 = hashlib.md5()
        md5.update(pwd1.encode(encoding='utf-8'))
        password = md5.hexdigest()

        users = Users(pwd=password, loginName=login_name, username=name, sex=sex,
                      picUrl=pic_url, updateTime=datetime.datetime.now())
        db.session.add(users)
        db.session.commit()
        return Result.success('OK')
        pass
    except Exception as e:
        db.session.rollback()
        return Result.fail('参数异常')


@app.route('/getUserById', methods=['GET'])
def get_user_by_id():
    try:
        uid = request.args.get("uid")
        # 查询数据库是否已存在
        user = Users.query.filter_by(id=uid).first()
        if user is None:
            return Result.fail('用户不存在！')
        else:
            return Result.success(user)
    except Exception as e:
        print(e.message)
        return Result.fail('参数异常')


@app.route('/getFriendsById', methods=['GET'])
def get_friends():
    try:
        uid = str(request.args.get("uid"))
        if uid.isdigit():
            friends = get_friends_by_uid(uid)
            dict_friends = list()
            for f in friends:
                is_online = 0
                if f.id in online_users.keys():
                    is_online = 1
                dic_f = {'online': is_online, 'user': f}
                dict_friends.append(dic_f)
            return Result.success(dict_friends)
        return Result.fail('参数异常')
    except Exception as e:
        print(e.message)
        return Result.fail('参数异常')


# 根据群id
@app.route('/getGroupsDetails', methods=['GET'])
def get_groups_details():
    try:
        gid = str(request.args.get("gid"))
        if gid.isdigit():
            group = GroupChat.query.filter(GroupChat.id == int(gid)).first()

            create = Users.query.filter(Users.id == group.createUid).first()
            create_name = create.username

            group_members = GroupMembers.query.filter(GroupMembers.gId == group.id).all()
            members = list()
            for m in group_members:
                di = dict()
                u = Users.query.filter(Users.id == m.uId).first()
                name = u.username
                di['uid'] = u.id
                di['name'] = name
                if u.id in online_users.keys():
                    di['online'] = 1
                else:
                    di['online'] = 0
                members.append(di)

            result = {'group': group, 'createName': create_name, 'members': members}
            return Result.success(result)
        return Result.fail('参数异常')
    except Exception as e:
        print(e.message)
        return Result.fail('参数异常')


# 根据群id
@app.route('/getGroupMembers', methods=['GET'])
def get_group_members():
    try:
        gid = str(request.args.get("gid"))
        if gid.isdigit():
            group = GroupChat.query.filter(GroupChat.id == int(gid)).first()
            group_members = GroupMembers.query.filter(GroupMembers.gId == group.id).all()
            user_ids = list()
            for m in group_members:
                user_ids.append(m.uId)
            users = Users.query.filter(Users.id.in_(user_ids)).all()
            return Result.success(users)
        return Result.fail('参数异常')
    except Exception as e:
        print(e.message)
        return Result.fail('参数异常')


# 根据用户uid
@app.route('/getGroupsById', methods=['GET'])
def get_groups():
    try:
        uid = str(request.args.get("uid"))
        if uid.isdigit():
            groups = get_groups_by_uid(int(uid))
            return Result.success(groups)
        return Result.fail('参数异常')
    except Exception as e:
        print(e.message)
        return Result.fail('参数异常')


@app.route('/hasNewMessage', methods=['GET'])
def has_new_message():
    try:
        uid = int(request.args.get("uid"))
        msgs = Message.query.filter(Message.toUid == uid) \
            .filter(Message.handle == 0).all()
        return Result.success(len(msgs))
    except Exception as e:
        print(e.message)
        return Result.fail('参数异常')


@app.route('/searchFriendsGroups', methods=['GET'])
def search_friends_groups():
    try:
        search_text = request.args.get("searchText")
        # 根据登录名或群号进行查询 精准查询，不允许模糊
        user = Users.query.filter(Users.loginName == search_text).first()
        if user is not None:
            return Result.success({'type': 'user', 'data': user})
        if str(search_text).isdigit():
            group = GroupChat.query.filter(GroupChat.id == int(search_text)).first()
            if group is not None:
                return Result.success({'type': 'group', 'data': group})
        return Result.success({'type': 'none', 'data': {}})
    except Exception as e:
        print(e.message)
        return Result.fail('参数异常')


@app.route('/searchUserByLoginname', methods=['GET'])
def search_user_by_loginname():
    try:
        search_text = request.args.get("searchText")
        # 根据登录名或群号进行查询 精准查询，不允许模糊
        user = Users.query.filter(Users.loginName == search_text).first()
        if user is not None:
            return Result.success(user)
        return Result.fail('不存在此用户')
    except Exception as e:
        print(e.message)
        return Result.fail('参数异常')


@app.route('/addGroupMember', methods=['GET'])
def add_gourp_member():
    try:
        gid = str(request.args.get("gid"))
        uid = str(request.args.get("uid"))
        from_id = str(request.args.get("fromId"))
        if gid.isdigit() and uid.isdigit() and from_id.isdigit():
            if check_can_add_gourp_member(gid, uid):
                message = Message(fromUid=int(from_id), toUid=int(uid), type=3, gId=int(gid),
                                  handle=0, sendTime=datetime.datetime.now())
                db.session.add(message)
                db.session.commit()
                if int(uid) in online_users.keys():
                    connection = online_users[int(uid)]
                    send_msg = {'type': UtilsAndConfig.MESSAGE_NEW_MSG}
                    connection.send(json.dumps(send_msg).encode())
                return Result.success('ok')
        return Result.fail('参数异常')
    except Exception as e:
        db.session.rollback()
        print(e.message)
        return Result.fail('参数异常')


@app.route('/canAddGroupMember', methods=['GET'])
def can_add_gourp_member():
    try:
        gid = str(request.args.get("gid"))
        uid = str(request.args.get("uid"))
        if gid.isdigit() and uid.isdigit():
            if check_can_add_gourp_member(gid, uid):
                return Result.success(1)
            else:
                return Result.success(0)
        return Result.fail('参数异常')
    except Exception as e:
        print(e.message)
        return Result.fail('参数异常')


def check_can_add_gourp_member(gid, uid):
    group = GroupChat.query.filter(GroupChat.id == int(gid)).first()
    if group is not None:
        members = GroupMembers.query.filter(GroupMembers.gId == int(gid)). \
            filter(GroupMembers.uId == int(uid)).all()
        if len(members) > 0:
            return False
        messages = Message.query.filter(Message.fromUid == group.createUid).filter(Message.toUid == int(uid)) \
            .filter(Message.type == 3).filter(Message.gId == int(gid)).filter(Message.handle == 0).all()
        if len(messages) > 0:
            return False
        return True
    return False


@app.route('/getUsernameByUid', methods=['GET'])
def get_username_by_uid():
    try:
        uid = int(request.args.get("uid"))
        user = Users.query.filter(Users.id == uid).first()
        if user is not None:
            return Result.success(user.username)
        else:
            return Result.fail('用户不存在')

    except Exception as e:
        print(e.message)
        return Result.fail('参数异常')


@app.route('/getGnameByGid', methods=['GET'])
def get_gname_by_gid():
    try:
        gid = int(request.args.get("gid"))
        group = GroupChat.query.filter(GroupChat.id == gid).first()
        if group is not None:
            return Result.success(group.gname)
        else:
            return Result.fail('群不存在')
    except Exception as e:
        print(e.message)
        return Result.fail('参数异常')


@app.route('/canAddFriends', methods=['GET'])
def can_add_friends():
    try:
        type = request.args.get("type")
        uid = request.args.get("uid")
        id = request.args.get("id")
        if type in ['user', 'group']:
            return Result.success(can_add(type, uid, id))
        return Result.fail('参数异常')

    except Exception as e:
        print(e.message)
        return Result.fail('参数异常')


@app.route('/addFriendsOrGroup', methods=['GET'])
def add_friends_or_group():
    try:
        friend_type = request.args.get("type")
        uid = request.args.get("uid")
        friend_id = request.args.get("id")
        if friend_type in ['user', 'group'] and can_add(friend_type, uid, friend_id) == 0:
            if friend_type == 'user':
                message = Message(fromUid=int(uid), toUid=int(friend_id), type=1,
                                  handle=0, sendTime=datetime.datetime.now())
                db.session.add(message)
                db.session.commit()
                if int(friend_id) in online_users.keys():
                    connection = online_users[int(friend_id)]
                    send_msg = {'type': UtilsAndConfig.MESSAGE_NEW_MSG}
                    connection.send(json.dumps(send_msg).encode())
            else:
                group = GroupChat.query.filter(GroupChat.id == int(friend_id)).first()
                message = Message(fromUid=int(uid), toUid=group.createUid, type=2, handle=0,
                                  gId=int(friend_id), sendTime=datetime.datetime.now())
                db.session.add(message)
                db.session.commit()
                if group.createUid in online_users.keys():
                    connection = online_users[group.createUid]
                    send_msg = {'type': UtilsAndConfig.MESSAGE_NEW_MSG}
                    connection.send(json.dumps(send_msg).encode())

            return Result.success('OK')

        return Result.fail('参数异常')

    except Exception as e:
        db.session.rollback()
        print(e.message)
        return Result.fail('参数异常')


@app.route('/getNoHandleMessages', methods=['GET'])
def get_no_handle_message():
    try:
        uid = str(request.args.get("uid"))
        if uid.isdigit():
            msgs = Message.query.filter(Message.handle == 0).filter(Message.toUid == int(uid)).all()
            return Result.success(msgs)
        return Result.fail('参数异常')
    except Exception as e:
        db.session.rollback()
        print(e.message)
        return Result.fail('参数异常')


@app.route('/messageHandle', methods=['GET'])
def message_handle():
    try:
        msg_id = str(request.args.get("msgId"))
        msg_handle = str(request.args.get("msgHandle"))
        if msg_id.isdigit() and msg_handle.isdigit():
            msg = Message.query.filter(Message.handle == 0).filter(Message.id == int(msg_id)).first()
            if msg is not None:
                # 1:添加好友  2:申请入群  3:邀请入群
                # 0:未处理 1:同意  2:拒绝
                if msg.type == 1:
                    if int(msg_handle) == 1:
                        f = Friends(uid=msg.fromUid, friendId=msg.toUid, updateTime=datetime.datetime.now())
                        db.session.add(f)
                        db.session.commit()
                        # 已同意，清除相互的申请
                        Message.query.filter(Message.type == 1).filter(Message.fromUid == msg.toUid) \
                            .filter(Message.toUid == msg.fromUid).filter(Message.handle == 0) \
                            .update({'handle': 1, 'handleTime': datetime.datetime.now()})
                    Message.query.filter(Message.handle == 0).filter(Message.id == int(msg_id)) \
                        .update({'handle': int(msg_handle), 'handleTime': datetime.datetime.now()})

                if msg.type == 2:
                    if int(msg_handle) == 1:
                        g = GroupMembers(gId=msg.gId, uId=msg.fromUid, joinTime=datetime.datetime.now())
                        db.session.add(g)
                        db.session.commit()
                        # 已同意，清除 被邀请
                        Message.query.filter(Message.type == 3).filter(Message.fromUid == msg.toUid) \
                            .filter(Message.toUid == msg.fromUid).filter(Message.gId == msg.gId) \
                            .filter(Message.handle == 0) \
                            .update({'handle': 1, 'handleTime': datetime.datetime.now()})
                    Message.query.filter(Message.handle == 0).filter(Message.id == int(msg_id)) \
                        .update({'handle': int(msg_handle), 'handleTime': datetime.datetime.now()})
                if msg.type == 3:
                    if int(msg_handle) == 1:
                        g = GroupMembers(gId=msg.gId, uId=msg.toUid, joinTime=datetime.datetime.now())
                        db.session.add(g)
                        db.session.commit()
                        # 已同意，清除主动申请
                        Message.query.filter(Message.type == 2).filter(Message.fromUid == msg.toUid) \
                            .filter(Message.handle == 0) \
                            .filter(Message.toUid == msg.fromUid).filter(Message.gId == msg.gId) \
                            .update({'handle': 1, 'handleTime': datetime.datetime.now()})
                    Message.query.filter(Message.handle == 0).filter(Message.id == int(msg_id)) \
                        .update({'handle': int(msg_handle), 'handleTime': datetime.datetime.now()})

                # 通知刷新好友列表
                if int(msg_handle) == 1:
                    if msg.type == 1:
                        if msg.fromUid in online_users.keys():
                            connection = online_users[msg.fromUid]
                            send_msg = {'type': UtilsAndConfig.FRIENDS_GROUPS_COUNT_CHANGED}
                            connection.send(json.dumps(send_msg).encode())
                        if msg.toUid in online_users.keys():
                            connection = online_users[msg.toUid]
                            send_msg = {'type': UtilsAndConfig.FRIENDS_GROUPS_COUNT_CHANGED}
                            connection.send(json.dumps(send_msg).encode())
                    else:
                        members = GroupMembers.query.filter(GroupMembers.gId == msg.gId).all()
                        for m in members:
                            if m.uId in online_users.keys():
                                connection = online_users[m.uId]
                                send_msg = {'type': UtilsAndConfig.FRIENDS_GROUPS_COUNT_CHANGED}
                                connection.send(json.dumps(send_msg).encode())

            return Result.success('Ok')
        return Result.fail('参数异常')
    except Exception as e:
        db.session.rollback()
        print(e.message)
        return Result.fail('参数异常')


@app.route('/getGroupMemberCount', methods=['GET'])
def get_group_member_count():
    try:
        gId = str(request.args.get("gId"))
        if gId.isdigit():
            members = GroupMembers.query.filter(GroupMembers.gId == int(gId)).all()
            count = len(members)
            return Result.success(count)
        return Result.fail('参数异常')
    except Exception as e:
        db.session.rollback()
        print(e.message)
        return Result.fail('参数异常')


@app.route('/downloadFileSuccess', methods=['GET'])
def download_file_success():
    try:
        path = str(request.args.get("path"))
        # 只能删除 /static/tmp/ 的文件
        file_name = path.split('/')[-1]
        if path.replace(file_name, '') == '/static/tmp/':
            file_path = os.path.abspath(os.path.dirname(__file__)) + path
            if os.path.isfile(file_path) and os.path.exists(file_path):
                os.remove(file_path)
        return ''
    except Exception as e:
        print(e.message)
        return Result.fail('参数异常')


@app.route('/getGroupSize', methods=['GET'])
def get_group_size():
    try:
        # 获取HTTP请求中的参数
        gid = int(request.args.get("gid"))
        members = get_group_members(gid)
        if members is None:
            return Result.fail('群不存在')
        else:
            return Result.success(len(members))

    except Exception as e:
        print(e.message)
        return Result.fail('参数异常')


@app.route('/createGroup', methods=['GET'])
def create_group():
    try:
        uid = str(request.args.get("uid"))
        gName = str(request.args.get("gName"))
        if uid.isdigit():
            if not gName.isdigit():
                alredy = GroupChat.query.filter(GroupChat.gname == gName).first()
                if alredy is not None:
                    return Result.fail('已存在此群名')
                g = GroupChat(createUid=int(uid), gname=gName, updateTime=datetime.datetime.now())
                db.session.add(g)
                db.session.commit()
                alredy = GroupChat.query.filter(GroupChat.gname == gName).first()
                gm = GroupMembers(gId=alredy.id, uId=int(uid), joinTime=datetime.datetime.now())
                db.session.add(gm)
                db.session.commit()

                connection = online_users[int(uid)]
                send_msg = {'type': UtilsAndConfig.FRIENDS_GROUPS_COUNT_CHANGED}
                connection.send(json.dumps(send_msg).encode())

                return Result.success('OK')
        return Result.fail('参数异常')
    except Exception as e:
        db.session.rollback()
        print(e.message)
        return Result.fail('参数异常')


@app.route('/delete_friend', methods=['GET'])
def delete_friend():
    try:
        uid = str(request.args.get("uid"))
        friend_id = str(request.args.get("friendId"))
        if uid.isdigit() and friend_id.isdigit():
            Friends.query.filter(Friends.uid == int(uid)).filter(Friends.friendId == int(friend_id)).delete()
            Friends.query.filter(Friends.uid == int(friend_id)).filter(Friends.friendId == int(uid)).delete()
            if int(uid) in online_users.keys():
                connection = online_users[int(uid)]
                send_msg = {'type': UtilsAndConfig.FRIENDS_GROUPS_COUNT_CHANGED}
                connection.send(json.dumps(send_msg).encode())
            if int(friend_id) in online_users.keys():
                connection = online_users[int(friend_id)]
                send_msg = {'type': UtilsAndConfig.FRIENDS_GROUPS_COUNT_CHANGED}
                connection.send(json.dumps(send_msg).encode())
            return Result.success('ok')
        return Result.fail('参数异常')
    except Exception as e:
        db.session.rollback()
        print(e.message)
        return Result.fail('参数异常')


@app.route('/quitGroup', methods=['GET'])
def quit_group():
    try:
        uid = str(request.args.get("uid"))
        group_id = str(request.args.get("groupId"))
        if uid.isdigit() and group_id.isdigit():
            GroupMembers.query.filter(GroupMembers.gId == int(group_id)).filter(GroupMembers.uId == int(uid)).delete()
            members = GroupMembers.query.filter(GroupMembers.gId == int(group_id)).all()
            for m in members:
                if m.uId in online_users.keys():
                    connection = online_users[m.uId]
                    send_msg = {'type': UtilsAndConfig.FRIENDS_GROUPS_COUNT_CHANGED}
                    connection.send(json.dumps(send_msg).encode())
            return Result.success('ok')
        return Result.fail('参数异常')
    except Exception as e:
        db.session.rollback()
        print(e.message)
        return Result.fail('参数异常')


@app.route('/deleteGroup', methods=['GET'])
def delete_group():
    try:
        uid = str(request.args.get("uid"))
        group_id = str(request.args.get("groupId"))
        if uid.isdigit() and group_id.isdigit():
            member_ids = list()
            members = GroupMembers.query.filter(GroupMembers.gId == int(group_id)).all()
            for m in members:
                member_ids.append(m.uId)
            Message.query.filter(Message.gId == int(group_id)).delete()
            GroupMembers.query.filter(GroupMembers.gId == int(group_id)).delete()
            GroupChat.query.filter(GroupChat.id == int(group_id)).filter(GroupChat.createUid == int(uid)).delete()
            for m_uid in member_ids:
                if m_uid in online_users.keys():
                    connection = online_users[m_uid]
                    send_msg = {'type': UtilsAndConfig.FRIENDS_GROUPS_COUNT_CHANGED}
                    connection.send(json.dumps(send_msg).encode())
            return Result.success('ok')
        return Result.fail('参数异常')
    except Exception as e:
        db.session.rollback()
        print(e.message)
        return Result.fail('参数异常')


@app.route('/removeMember', methods=['GET'])
def remove_member():
    try:
        create_id = str(request.args.get("createId"))
        gid = str(request.args.get("gid"))
        uid = str(request.args.get("uid"))
        if create_id.isdigit() and gid.isdigit() and uid.isdigit():
            groups = GroupChat.query.filter(GroupChat.id == int(gid)) \
                .filter(GroupChat.createUid == int(create_id)).all()
            if groups is not None and len(groups) == 1:
                GroupMembers.query.filter(GroupMembers.gId == int(gid)).filter(GroupMembers.uId == int(uid)).delete()

                if int(uid) in online_users.keys():
                    connection = online_users[int(uid)]
                    send_msg = {'type': UtilsAndConfig.FRIENDS_GROUPS_COUNT_CHANGED}
                    connection.send(json.dumps(send_msg).encode())
                return Result.success('ok')
        return Result.fail('参数异常')
    except Exception as e:
        db.session.rollback()
        print(e.message)
        return Result.fail('参数异常')


@app.route('/modifyGroupName', methods=['GET'])
def modify_group_name():
    try:
        gid = str(request.args.get("gid"))
        new_name = str(request.args.get("newName"))
        uid = str(request.args.get("uid"))
        if gid.isdigit() and uid.isdigit():
            if len(new_name) > 6 or len(new_name) < 1:
                return Result.fail('群名有误请重新输入')
            group = GroupChat.query.filter(GroupChat.id == int(gid)).filter(GroupChat.createUid == int(uid)).first()
            if group is None:
                return Result.fail('不存在此群号')
            GroupChat.query.filter(GroupChat.id == int(gid)).filter(GroupChat.createUid == int(uid)) \
                .update({'gname': new_name})
            return Result.success('ok')
        return Result.fail('参数异常')
    except Exception as e:
        db.session.rollback()
        print(e.message)
        return Result.fail('参数异常')


@app.route('/modifyUser', methods=['POST'])
def modify_user():
    try:
        params = request.values
        username = params['username']
        sex = params['sex']
        pwd1 = params['pwd1']
        pwd2 = params['pwd2']
        pic_path = params['pic_path']
        uid = params['uid']

        user = Users.query.filter(Users.id == int(uid)).first()
        if user is not None:
            # 昵称和性别
            Users.query.filter(Users.id == int(uid)) \
                .update({'username': username, 'sex': sex, 'updateTime': datetime.datetime.now()})

            # 修改了头像
            if len(str(pic_path).strip()) > 0:
                files = request.files['file']
                head_pic_path = FILES_PATH + '/' + 'headPic/'
                today = datetime.datetime.now().strftime('%Y-%m-%d')
                head_pic_path = head_pic_path + today + '/'
                if not os.path.exists(head_pic_path):
                    os.makedirs(head_pic_path)
                filename = str(uuid.uuid1()) + '.jpg'
                files.save(head_pic_path + filename)
                pic_url = '/static/headPic/' + today + "/" + filename
                Users.query.filter(Users.id == int(uid)) \
                    .update({'picUrl': pic_url, 'updateTime': datetime.datetime.now()})
            # 修改了密码
            if len(pwd1) > 0 and pwd2 == pwd1:
                md5 = hashlib.md5()
                md5.update(pwd1.encode(encoding='utf-8'))
                password = md5.hexdigest()

                Users.query.filter(Users.id == int(uid)) \
                    .update({'pwd': password, 'updateTime': datetime.datetime.now()})
            friends = get_friends_by_uid(uid)
            for f in friends:
                if f.id in online_users.keys():
                    connection = online_users[f.id]
                    send_msg = {'type': UtilsAndConfig.FRIENDS_GROUPS_COUNT_CHANGED}
                    connection.send(json.dumps(send_msg).encode())
            return Result.success('OK')
        return Result.fail('参数异常')
    except Exception as e:
        db.session.rollback()
        print(e.message)
        return Result.fail('参数异常')


# 辅助函数获取数据库查找的内容, 非定义接口
# 获取好友
def can_add(add_type, uid, id):
    if add_type == 'user':
        if uid == id:
            return 1
        # 在friend数据库中查找
        f = Friends.query.filter(Friends.uid == int(uid)).filter(Friends.friendId == int(id)).first()
        if f is not None:
            return 1
        f = Friends.query.filter(Friends.uid == int(id)).filter(Friends.friendId == int(uid)).first()
        if f is not None:
            return 1
        m = Message.query.filter(Message.fromUid == int(uid)).filter(Message.toUid == int(id)) \
            .filter(Message.type == 1).filter(Message.handle == 0).first()
        if m is not None:
            return 1
        return 0
    if add_type == 'group' and str(id).isdigit():
        g = GroupMembers.query.filter(GroupMembers.gId == int(id)).filter(GroupMembers.uId == int(uid)).first()
        if g is not None:
            return 1

        m = Message.query.filter(Message.fromUid == int(uid)).filter(Message.gId == int(id)) \
            .filter(Message.type == 2).filter(Message.handle == 0).first()
        if m is not None:
            return 1
        return 0


def get_friends_by_uid(uid):
    # 查询数据库是否已存在
    friends1 = Friends.query.filter_by(uid=uid).all()
    friends2 = Friends.query.filter_by(friendId=uid).all()
    list_ids = list()
    for f in friends1:
        list_ids.append(f.friendId)
    for f in friends2:
        list_ids.append(f.uid)
    friends = Users.query.filter(Users.id.in_(list_ids)).all()
    return friends


def get_groups_by_uid(uid):
    group_members = GroupMembers.query.filter(GroupMembers.uId == uid).all()
    group_ids = list()
    for m in group_members:
        group_ids.append(m.gId)
    groups = GroupChat.query.filter(GroupChat.id.in_(group_ids)).all()
    return groups


def get_group_members(gid):
    group = GroupChat.query.filter(GroupChat.id == gid).first()
    if group is not None:
        members = GroupMembers.query.filter(GroupMembers.gId == gid).all()
        return members
    return None


# 断开连接，提示好友下线
def connection_close(connection):
    if connection in online_users.values():
        uid = list(online_users.keys())[list(online_users.values()).index(connection)]
        online_users.pop(uid)
        friends = get_friends_by_uid(uid)
        for f in friends:
            if f.id in online_users.keys():
                friend_connection = online_users[f.id]
                send_msg = {'type': UtilsAndConfig.FRIENDS_ONLINE_CHANGED, 'uid': uid, 'online': 0}
                friend_connection.send(json.dumps(send_msg).encode())
        connection.close()

# my_socket.connect uuid
# 其他函数
# 监听socket
def socket_listen_thread():
    while True:
        # 获取
        connection, address = mySocket.accept()
        # print(f"一个新的客户端到来, connection信息是: {str(connection)};  address信息是: {str(address)}")
        # 用户连接携带的uid，判断是否和服务器相同
        data_dic = json.loads(connection.recv(1024).decode())
        # print(f"当前connection的recv函数内容是: {str(data_dic)}")
        # 客户端登录socket请求
        if data_dic['type'] == UtilsAndConfig.USER_LOGIN:  # 如果解析出类型是登录字段
            login_name = str(data_dic['login_name'])
            pwd = str(data_dic['pwd'])
            # 密码加解密
            md5 = hashlib.md5()
            md5.update(pwd.encode(encoding='utf-8'))
            password = md5.hexdigest()
            # 清空下数据库查询缓存，不清空短时间内注册的用户可能无法登录
            db.session.expire_all()
            db.session.commit()
            # 得到满足user表中满足条件的信息
            users = Users.query.filter(Users.loginName == login_name) \
                .filter(Users.pwd == password).all()
            print(f"当前新的客户端到来后查找的user表中信息是: {str(users)}")
            if len(users) == 0:
                send_msg = {'type': UtilsAndConfig.USER_LOGIN_FAILED}
                connection.send(json.dumps(send_msg).encode())
            else:
                # 服务返回uid，客户端打开好友界面后，
                # 凭借此uid与服务器进行socket连接
                uid = users[0].id

                # 已存在uid已登录，重新登录
                # 原登录退出连接，退出程序
                print(f"当前online_users中的内容是:  {str(online_users)}")
                if uid in online_users.keys():
                    # logout
                    login_connection = online_users[int(uid)]
                    send_msg = {'type': UtilsAndConfig.SYSTEM_LOGOUT}
                    login_connection.send(json.dumps(send_msg).encode())

                online_users[uid] = connection
                send_msg = {'type': UtilsAndConfig.USER_LOGIN_SUCCESS, 'uid': uid}
                connection.send(json.dumps(send_msg).encode())

                print(f"加入当前客户端后online_users中的内容是:  {str(online_users)}")
                print("当前online_users内容是: ")
                print(online_users)
                # 通知好友们，我上线了
                friends = get_friends_by_uid(uid)
                for f in friends:
                    if f.id in online_users.keys():
                        friend_connection = online_users[f.id]
                        print(f"当前friend_connection中的内容是: {str(friend_connection)}")
                        send_msg = {'type': UtilsAndConfig.FRIENDS_ONLINE_CHANGED, 'uid': uid, 'online': 1}
                        friend_connection.send(json.dumps(send_msg).encode())

                # 创建子线程，保持通信
                keep_link_thread = threading.Thread(target=socket_keep_link_thread, args=(connection,))
                keep_link_thread.setDaemon(True)
                keep_link_thread.start()


# 登录后保持socket连接，处理各种消息的通信
def socket_keep_link_thread(connection):
    while True:
        try:
            # 先进行解密
            # key = "hfut"
            # des = MyDES.MyDes()
            msg = connection.recv(1024).decode()
            # msg = des.decode(msg, key)
            # print(f"当前msg内容是: {str(msg)}")
            if not msg:
                connection_close(connection)
                return
            else:
                msg_json = json.loads(str(msg))
                # print(f"当前msg_json内容是: {str(msg_json)}")
                # 发消息
                if msg_json['type'] == UtilsAndConfig.CHAT_SEND_MSG:
                    to_id = msg_json['toId']
                    is_friend = msg_json['isFriend']
                    from_uid = msg_json['fromId']
                    send_time = msg_json['sendTime']
                    msg_text = msg_json['msgText']

                    data = {'from_uid': from_uid, 'to_id': to_id, 'send_time': send_time, 'msg_text': msg_text,
                            'is_friend': is_friend, 'type': '', 'msg_type': 'train'}
                    # 通知接收方，收到新消息
                    if is_friend == 1:
                        # 好友私聊消息
                        if to_id in online_users.keys():
                            friend_connection = online_users[to_id]
                            data['type'] = UtilsAndConfig.CHAT_HAS_NEW_MSG
                            friend_connection.send(json.dumps(data).encode())
                            print(f"好友私聊后的消息是:  {str(data)}")
                            # 通知发送方，发送成功
                            data['type'] = UtilsAndConfig.CHAT_SEND_MSG_SUCCESS
                            connection.send(json.dumps(data).encode())
                        else:
                            # 通知发送方，发送失败，对方不在线
                            data['type'] = UtilsAndConfig.CHAT_SEND_MSG_ERR
                            connection.send(json.dumps(data).encode())
                    else:
                        # 群消息，通知在线的群成员
                        members = get_group_members(to_id)
                        members_online = False
                        for m in members:
                            if m.uId in online_users.keys() and m.uId != from_uid:
                                members_online = True
                                member_connection = online_users[m.uId]
                                data['type'] = UtilsAndConfig.CHAT_HAS_NEW_MSG
                                member_connection.send(json.dumps(data).encode())
                        if members_online:
                            # 通知发送方，发送成功
                            data['type'] = UtilsAndConfig.CHAT_SEND_MSG_SUCCESS
                            connection.send(json.dumps(data).encode())
                        else:
                            # 通知发送方，发送失败，对方不在线
                            data['type'] = UtilsAndConfig.CHAT_SEND_MSG_ERR
                            connection.send(json.dumps(data).encode())
                # 发文件
                if msg_json['type'] == UtilsAndConfig.CHAT_SEND_FILE:
                    from_id = msg_json['from_id']
                    to_id = msg_json['to_id']
                    is_friend = msg_json['is_friend']
                    send_date = msg_json['send_date']
                    file_length = msg_json['file_length']
                    file_suffix = msg_json['file_suffix']
                    file_name = msg_json['file_name']

                    file_save_name = str(uuid.uuid1()) + '.' + file_suffix
                    return_file_path = '/static/tmp/' + file_save_name
                    file_path = os.path.abspath(os.path.dirname(__file__)) + return_file_path
                    if not os.path.exists(os.path.dirname(file_path)):
                        os.makedirs(os.path.dirname(file_path))

                    data = {'from_uid': from_id, 'to_id': to_id, 'send_time': send_date, 'file_name': file_name,
                            'is_friend': is_friend, 'type': UtilsAndConfig.CHAT_SEND_FILE_SUCCESS,
                            'file_path': return_file_path}

                    if is_friend == 1:
                        if to_id not in online_users.keys():
                            # 通知发送方，发送失败，对方不在线
                            data['type'] = UtilsAndConfig.CHAT_SEND_MSG_ERR
                            connection.send(json.dumps(data).encode())
                            continue
                    else:
                        members = get_group_members(to_id)
                        flag = True
                        for m in members:
                            if m.uId in online_users.keys() and m.uId != from_id:
                                flag = False
                                break
                        if flag:
                            # 通知发送方，发送失败，对方不在线
                            data['type'] = UtilsAndConfig.CHAT_SEND_MSG_ERR
                            connection.send(json.dumps(data).encode())
                            continue

                    # 接收文件
                    total_data = b''
                    file_data = connection.recv(1024)
                    total_data += file_data
                    num = len(file_data)
                    while num < file_length:
                        file_data = connection.recv(1024)
                        num += len(file_data)
                        total_data += file_data

                    with open(file_path, "wb") as f:
                        f.write(total_data)

                    connection.send(json.dumps(data).encode())

                    # 通知接收方，收到新文件消息
                    if is_friend == 1:
                        friend_connection = online_users[to_id]
                        data['type'] = UtilsAndConfig.CHAT_HAS_NEW_FILE
                        friend_connection.send(json.dumps(data).encode())
                    else:
                        members = get_group_members(to_id)
                        for m in members:
                            if m.uId in online_users.keys() and m.uId != from_id:
                                member_connection = online_users[m.uId]
                                data['type'] = UtilsAndConfig.CHAT_HAS_NEW_FILE
                                member_connection.send(json.dumps(data).encode())
        # 断开连接，提示好友下线
        except ConnectionAbortedError:
            connection_close(connection)
            return
        except ConnectionResetError:
            connection_close(connection)
            return


# 主线程
if __name__ == '__main__':
    try:
        result = db.session.execute("select 1 as alive")
        print("\033[1;32m", "数据库连接：正常", "\033[0m")
    except Exception as e:
        print("\033[0;31;40m", "数据库连接：失败", "\033[0m")
        print("\033[0;31;40m", "请检查数据库是否运行，或数据库配置是否正确，或chatdb.sql脚本是否执行过", "\033[0m")
        sys.exit()

    # 启动socket线程
    socketThread = threading.Thread(target=socket_listen_thread)
    socketThread.setDaemon(True)  # 守护线程，这意味着该线程不会阻止程序退出，而是在程序退出时自动结束
    socketThread.start()

    msg = "服务器已启动：" + serverConfig.SERVER_IP + ":" + str(serverConfig.HTTP_PORT)
    print("\033[1;32m", msg, "\033[0m")
    # md5
    # 启动Flask服务器
    app.debug = False
    server = make_server(serverConfig.SERVER_IP, serverConfig.HTTP_PORT, app)
    try:
        server.serve_forever()  # 启动一个服务器并一直运行，直到程序退出或手动停止服务器
    # 停止运行时，释放flask与socket资源
    except KeyboardInterrupt:
        server.server_close()
        mySocket.close()
        sys.exit()
