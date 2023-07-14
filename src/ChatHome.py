import tkinter as tk
import tkinter.messagebox
import tkinter.filedialog
import requests
import json
import threading
import os
from FriendView import *
from FriendView import FriendView
from GroupsView import GroupsView
from ChatWindow import ChatWindow
import datetime
import sys
import MyDES
import utils
import des_setting
from UtilsAndConfig import ServerConfig


class ChatHome:

    def __init__(self, uid, my_socket):
        self.server_config = ServerConfig()
        self.uid = uid
        self.User = None
        self.frames_friend_view = dict()
        self.frames_group_view = dict()
        self.canvas_frame = None
        self.socket = my_socket
        self.root = None
        self.canvas = None
        self.label_message_tip = None
        self.canvas_frame = None
        self.window_chat_context = None
        self.window_chat = None
        self.frame_user_info = None
        self.img_jpg = None
        self.frame_mid = None
        self.scrollbar = None
        self.emoji_cache = dict()
        self.run()

    # 加载表情包图片
    def load_emoji(self):
        files_dir = os.path.abspath(os.path.dirname(__file__)) + '/static/emoji/'   # 文件路径
        files = os.listdir(files_dir)   # 所有头像
        for file in files:
            if file.split('.')[-1] == 'png':    # 获取并检查文件名的扩展名
                emoji_path = files_dir + file   # 表情包文件路径拼接
                img_jpg = UtilsAndConfig.resize_image(False, emoji_path, 25, 25)    # 获取用于Tkinter适用的图片
                all_file_name = emoji_path.split('/')[-1]   # 得到文件名
                name = str(all_file_name).replace('.png', '')
                self.emoji_cache[name] = img_jpg    # 键值对存储表情文件, 后面'表情名'就可以访问图片

    def run(self):
        # 创建子线程保持socket通信
        keep_link_thread = threading.Thread(target=self.socket_keep_link_thread)
        keep_link_thread.setDaemon(True)
        keep_link_thread.start()

        # 基本信息
        self.root = tk.Tk()
        self.root.title('主界面')
        self.root.geometry('350x510+600+300')
        self.root.minsize(350, 510)
        self.root.maxsize(350, 510)

        # 用户名
        self.frame_user_info = Frame(self.root, relief=RAISED, width=350, borderwidth=0, height=70, bg='#B5D5D0')
        self.frame_user_info.place(x=0, y=0)
        self.init_user_info()

        # 下方按钮
        frame_bottom_button = Frame(self.root, relief=RAISED, borderwidth=0, width=350, height=50)
        frame_bottom_button.place(x=0, y=70)
        button_bottom_add_friends = Button(frame_bottom_button, width=20, bg='#ABDAD9',
                                           text='添加好友', command=self.open_add_friends)
        button_bottom_add_friends.place(x=0, y=0)
        button_bottom_create_groups = Button(frame_bottom_button, width=20, bg='#ABDAD9',
                                             text='创建群聊', command=self.open_create_groups)
        button_bottom_create_groups.place(x=165, y=0)

        # 中间画布canvas
        self.frame_mid = Frame(self.root, width=350, height=340)
        self.frame_mid.place(x=0, y=110)
        # # 画布中的frame
        self.init_friends_and_group_view()


        # 新消息
        frame_message = Frame(self.root, relief=RAISED, borderwidth=0, width=350, height=50)
        frame_message.place(x=0, y=460)
        self.label_message_tip = Label(frame_message)
        self.label_message_tip.place(x=55, y=12)
        self.refresh_message_count()
        button_message_open = Button(frame_message, width=7, bg='#ABDAD9',
                                     text='点击查看', command=self.open_message_window)
        button_message_open.place(x=250, y=7)
        self.load_emoji()
        self.root.mainloop()

    # 其他函数

    # 初始化聊天主界面的头像、昵称和修改信息模块
    def init_user_info(self):
        for widget in self.frame_user_info.winfo_children():
            widget.destroy()

        # 用户信息
        url = self.server_config.HTTP_SERVER_ADDRESS + '/getUserById?uid=' + str(self.uid)  # 通过接口请求uid对应的用户信息
        result_user_info = requests.get(url)  # 使用requests库中的get方法来获取指定url的内容，并返回该内容的文本形式
        result_user_info = json.loads(result_user_info.text)  # 从json文件中读取数据, 得到
        if result_user_info['code'] != 200:  # ChatServer中class类:Result:
            tkinter.messagebox.showwarning('提示', '参数出错，请正确运行程序!')
            sys.exit()
        else:
            self.User = result_user_info['data']  # data字段中有详细的信息
        self.img_jpg = UtilsAndConfig.resize_image(True, self.User['picUrl'], 50, 50)  # 修改图像得到 Tkinter 可用的图像格式

        # 主界面显示
        Label(self.frame_user_info, image=self.img_jpg).place(x=7, y=7)  # 头像
        # 昵称
        Label(self.frame_user_info, bg='#E1EFF5',text=self.User['username'], fg='green',
              font=('宋体', 15)).place(x=70, y=19)

        # 修改信息按钮, 槽函数设置为self.modify_user
        Button(self.frame_user_info, bg='#ABDAD9', text='修改信息', command=self.modify_user).place(x=250, y=19)

    # 主界面修改信息按钮
    def modify_user(self):
        var_pic_path = StringVar()  # 头像的路径
        var_username = StringVar()  # 昵称
        var_sex_val = IntVar()      # 性别
        var_pwd1 = StringVar()      # 密码
        var_pwd2 = StringVar()      # 重复密码

        var_pic_path.set('')
        var_username.set(self.User['username'])
        var_sex_val.set(self.User['sex'])
        var_pwd1.set('')
        var_pwd1.set('')

        # 选择头像图片的路径
        def show_openfile_dialog():
            file_types = [('头像图片', '*.jpg')]
            file_path = tkinter.filedialog.askopenfilename(title=u'选择文件', filetypes=file_types)
            var_pic_path.set(file_path)

        # 修改信息按钮函数
        def confirm_modify():
            pic_path = var_pic_path.get()
            username = var_username.get()
            sex = var_sex_val.get()
            pwd1 = var_pwd1.get()
            pwd2 = var_pwd2.get()

            if username == '' or len(username) == 0:
                tkinter.messagebox.showwarning('提示', '昵称不能为空!')
                return
            if len(username) > 6:
                tkinter.messagebox.showwarning('提示', '昵称长度不能大于6!')
                return

            if pwd1 != '' or len(pwd1) != 0:
                if pwd2 == '' or len(pwd2) == 0:
                    tkinter.messagebox.showwarning('提示', '若需要修改密码，则需填写重复填写密码!')
                    return
            if pwd2 != '' or len(pwd2) != 0:
                if pwd1 == '' or len(pwd1) == 0:
                    tkinter.messagebox.showwarning('提示', '若需要修改密码，则需填写重复填写密码!')
                    return
            if pwd1 != pwd2:
                tkinter.messagebox.showwarning('提示', '密码不一致!')
                return

            url = self.server_config.HTTP_SERVER_ADDRESS + '/modifyUser'

            params = {
                'username': username,
                'sex': sex,
                'pwd1': pwd1,
                'pwd2': pwd2,
                'pic_path': pic_path,
                'uid': self.uid
            }
            button_confirm['state'] = DISABLED
            # 未修改头像

            if len(pic_path.strip()) == 0:
                r = requests.post(url, data=params)
            else:
                files = {'file': open(pic_path, 'rb')}
                r = requests.post(url, data=params, files=files)
            button_confirm['state'] = NORMAL
            result = json.loads(r.text)
            if result['code'] == 200:
                window_modify.destroy()
                tkinter.messagebox.showwarning('提示', '修改成功')
                self.init_user_info()
                return
            else:
                tkinter.messagebox.showwarning('提示', result['message'])

        global window_modify
        window_modify = Toplevel(self.root)
        window_modify.geometry('450x280+200+100')
        window_modify.title('修改信息')
        window_modify.transient(self.root)
        window_modify.configure(bg='#E1EFF5')
        # 头像
        frame_register_head = Frame(window_modify, bg='#E1EFF5',relief=RAISED, borderwidth=0, width=600, height=40)
        frame_register_head.place(x=30, y=20)
        Label(frame_register_head, bg='#E1EFF5', text='头   像：').place(x=40, y=8)
        Entry(frame_register_head, width=25, textvariable=var_pic_path, state='disabled').place(x=100, y=8)
        Button(frame_register_head, bg='#ABDAD9', text='选择头像', command=show_openfile_dialog).place(x=290, y=5)

        # 昵称
        frame_register_username = Frame(window_modify, bg='#E1EFF5',relief=RAISED, borderwidth=0, width=600, height=40)
        frame_register_username.place(x=30, y=60)
        Label(frame_register_username, bg='#E1EFF5',text='昵   称：').place(x=40, y=8)
        Entry(frame_register_username, bg='#E1EFF5',show=None, textvariable=var_username, width=25).place(x=100, y=8)

        # 性别
        frame_register_sex = Frame(window_modify, bg='#E1EFF5',relief=RAISED, borderwidth=0, width=600, height=40)
        frame_register_sex.place(x=30, y=100)
        label_register_sex = Label(frame_register_sex, bg='#E1EFF5',text='性   别：')
        label_register_sex.place(x=40, y=8)
        Radiobutton(frame_register_sex,bg='#E1EFF5', text='男', variable=var_sex_val, value='1').place(x=100, y=8)
        Radiobutton(frame_register_sex, bg='#E1EFF5',text='女', variable=var_sex_val, value='0').place(x=150, y=8)

        # 密码
        frame_register_password1 = Frame(window_modify, bg='#E1EFF5',relief=RAISED, borderwidth=0, width=600, height=40)
        frame_register_password1.place(x=30, y=140)
        Label(frame_register_password1, bg='#E1EFF5',text='密   码：').place(x=40, y=8)
        Entry(frame_register_password1, show='*', textvariable=var_pwd1, width=25).place(x=100, y=8)

        frame_register_password2 = Frame(window_modify, bg='#E1EFF5',relief=RAISED, borderwidth=0, width=600, height=40)
        frame_register_password2.place(x=30, y=180)
        Label(frame_register_password2,bg='#E1EFF5', text='重复密码：').place(x=40, y=8)
        Entry(frame_register_password2, show='*', textvariable=var_pwd2, width=25).place(x=100, y=8)

        # 按钮
        frame_register_button = Frame(window_modify, bg='#E1EFF5',relief=RAISED, borderwidth=0, width=600, height=40)
        frame_register_button.place(x=30, y=220)
        button_confirm = Button(frame_register_button,bg='#ABDAD9', width=15, text='确定修改', command=confirm_modify)
        button_confirm.place(x=150, y=5)

    def open_chat_window(self, is_friend, to_id):
        if self.window_chat is not None and len(self.window_chat.children) > 0:
            for widget in self.window_chat.winfo_children():
                widget.destroy()
        else:
            # 个人聊天主界面
            self.window_chat = Toplevel(self.root)
            self.window_chat.geometry('720x555+200+0')
            self.window_chat.minsize(720, 555)
            self.window_chat.maxsize(720, 555)
            self.window_chat.title('聊天')
            self.window_chat.transient(self.root)
            self.window_chat.protocol("WM_DELETE_WINDOW", self.close_window_chat)

        # 聊天主界面
        self.window_chat_context = ChatWindow(self.window_chat, self, is_friend, self.uid, to_id)
        if is_friend == 1:
            self.frames_friend_view[to_id].set_msg_text(0)
        else:
            self.frames_group_view[to_id].set_msg_text(0)

    # 关闭聊天框
    def close_window_chat(self):
        self.window_chat_context.destroy()
        self.window_chat.destroy()
        self.window_chat = None
        self.window_chat_context = None

    def refresh_message_count(self):
        message_url = self.server_config.HTTP_SERVER_ADDRESS + '/hasNewMessage?uid=' + str(self.uid)
        result_new_msg = requests.get(message_url)
        result_new_msg_json = json.loads(result_new_msg.text)
        if result_new_msg_json['code'] != 200:
            tkinter.messagebox.showwarning('提示', '参数出错，请正确运行程序!')
            sys.exit()
        count = result_new_msg_json['data']
        message_text = '您有 ' + str(count) + ' 条未处理消息'
        self.label_message_tip['text'] = message_text
        if count == 0:
            self.label_message_tip['fg'] = '#000000'
        else:
            self.label_message_tip['fg'] = 'green'

    def init_friends_and_group_view(self):

        if self.frame_mid is not None:
            for widget in self.frame_mid.winfo_children():
                widget.destroy()

        # 无内容，做间距用
        self.scrollbar = Scrollbar(self.frame_mid, width=10)
        self.canvas = Canvas(self.frame_mid, yscrollcommand=self.scrollbar.set, height=340, width=338)
        self.scrollbar.config(command=self.canvas.yview)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.canvas.pack(side=LEFT, fill='both', expand=True)

        # 获取好友列表
        init_friends_url = self.server_config.HTTP_SERVER_ADDRESS + '/getFriendsById?uid=' + str(self.uid)
        result_friends = requests.get(init_friends_url)
        result_friends = json.loads(result_friends.text)
        if result_friends['code'] != 200:
            tkinter.messagebox.showwarning('提示', '参数出错，请正确运行程序!')
            sys.exit()
        else:
            friends = result_friends['data']
        # 获取群列表
        init_group_url = self.server_config.HTTP_SERVER_ADDRESS + '/getGroupsById?uid=' + str(self.uid)
        result_groups = requests.get(init_group_url)
        result_groups_json = json.loads(result_groups.text)
        if result_groups_json['code'] != 200:
            tkinter.messagebox.showwarning('提示', '参数出错，请正确运行程序!')
            sys.exit()
        else:
            groups = result_groups_json['data']

        frame_len = len(friends) + len(groups)
        frame_height = frame_len * 61 + 2
        self.canvas_frame = Frame(self.canvas, width=370, height=frame_height)
        self.canvas.create_window(0, 0, window=self.canvas_frame, anchor='nw', width=370)
        self.canvas_frame.bind("<MouseWheel>", self.process_wheel)

        Frame(self.canvas_frame, width=370, height=1, bg='#99d9ea').place(x=0, y=0)
        y_index = 1
        for friend in friends:
            big_frame = Frame(self.canvas_frame, relief=RAISED, borderwidth=0, width=370, height=60)
            big_frame.place(x=0, y=y_index)
            friend_view = FriendView(big_frame, self.process_wheel, self, friend)
            friend_view.place(x=0, y=0)
            self.frames_friend_view[friend['user']['id']] = friend_view
            big_frame.bind("<MouseWheel>", self.process_wheel)
            y_index += 60
            Frame(self.canvas_frame, width=370, height=1, bg='#99d9ea').place(x=0, y=y_index)
            y_index += 1
        for g in groups:
            big_frame = Frame(self.canvas_frame, relief=RAISED, borderwidth=0, width=370, height=60)
            big_frame.place(x=0, y=y_index)
            group_view = GroupsView(big_frame, self.process_wheel, self, g)
            group_view.place(x=0, y=0)
            self.frames_group_view[g['id']] = group_view
            big_frame.bind("<MouseWheel>", self.process_wheel)
            y_index += 60
            Frame(self.canvas_frame, width=370, height=1, bg='#99d9ea').place(x=0, y=y_index)
            y_index += 1

        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.canvas.bind("<MouseWheel>", self.process_wheel)
        # self.frame_mid.update()

    # 利用self.socket.send发送消息
    def chat_send_msg(self, is_friend, to_id, send_time, msg):
        send_data = {'type': UtilsAndConfig.CHAT_SEND_MSG, 'isFriend': is_friend,
                     'fromId': self.uid, 'toId': to_id,
                     'sendTime': send_time, 'msgText': msg}
        # 使用des进行加密
        des = MyDES.MyDes()
        text = str(send_data)
        bit64_plain_text_str_array, end_add_zeros_count = utils.group_by_64_bit(text, False)
        if des_setting.IS_PRINT_BIT64_PLAIN_TEXT_STR_ARRAY:
            if end_add_zeros_count > 0 and end_add_zeros_count % 8 == 0:
                bit64_plain_text_str_array, end_add_zeros_count = utils.group_by_64_bit(text, False)
                bit64_plain_text_str_array[-1] = bit64_plain_text_str_array[-1][:-end_add_zeros_count:]
        key = "hfut"
        cipher_text = des.encode(text, key)[0]
        if des_setting.IS_PRINT_CIPHER_TEXT:
            str_cipher_text = ""
            for line in utils.group_by_64_bit(cipher_text, True)[0]:
                print(line)
                str_cipher_text += line
        self.socket.send(json.dumps(send_data).encode())


    # 利用self.socket.send发送文件
    def chat_send_file(self, file_path, is_friend, to_id):
        # 告诉server 发送聊天文件
        if not os.path.isfile(file_path):
            # tkinter.messagebox.showwarning('提示', '未选择文件!')
            return
        if not os.path.exists(file_path):
            tkinter.messagebox.showwarning('提示', '选择的文件不存在!')
            return
        suffix = file_path.split(".")[-1]
        file = open(file_path, "rb")
        data = file.read()
        if len(data) == 0:
            tkinter.messagebox.showwarning('提示', '选择的文件内容为空!')
            return
        1.0 * len(data) / 1024 / 1024
        max_size = 50 * 1024 * 1024
        if len(data) > max_size:
            tkinter.messagebox.showwarning('提示', '最大传输50MB文件!')
            return
        # 调用发送文件窗口
        self.window_chat_context.sending_file(True)
        send_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        send_data = {'type': UtilsAndConfig.CHAT_SEND_FILE, 'from_id': self.uid, 'to_id': to_id,
                     'is_friend': is_friend, 'send_date': send_date, 'file_length': len(data),
                     'file_suffix': suffix, 'file_name': file_path}
        self.socket.send(json.dumps(send_data).encode())
        self.socket.sendall(data)
        file.close()

    # 保持socket通信
    def socket_keep_link_thread(self):
        while True:
            try:
                back_msg = self.socket.recv(1024).decode()
                # key = "hfut"
                # des = MyDES.MyDes()
                # back_msg = des.decode(back_msg, key)
                msg = json.loads(back_msg)
                # 好友状态改变
                if msg['type'] == UtilsAndConfig.FRIENDS_ONLINE_CHANGED:
                    self.frames_friend_view[msg['uid']].online_type_change(msg['online'])
                # 有新验证消息
                if msg['type'] == UtilsAndConfig.MESSAGE_NEW_MSG:
                    self.refresh_message_count()
                # 好友/群数量改变
                if msg['type'] == UtilsAndConfig.FRIENDS_GROUPS_COUNT_CHANGED:
                    self.init_friends_and_group_view()
                    self.refresh_message_count()
                # 有新文本消息， 写入缓存，更新显示
                if msg['type'] == UtilsAndConfig.CHAT_HAS_NEW_MSG:
                    from_uid = msg['from_uid']
                    to_id = msg['to_id']
                    is_friend = msg['is_friend']
                    txt = {'type': 'get', 'from_uid': from_uid, 'datetime': msg['send_time'],
                           'msg': msg['msg_text'], 'msg_type': 'train'}
                    UtilsAndConfig.add_one_chat_record(self.uid, is_friend, from_uid, to_id,
                                                       json.dumps(txt, cls=UtilsAndConfig.MyJSONEncoder,
                                                                  ensure_ascii=False), False)
                    # 是否打开聊天界面，打开则更新，未打开则好友列表提示新消息
                    if self.window_chat_context is not None and self.window_chat_context.to_id == from_uid \
                            and self.window_chat_context.is_friend == 1 and is_friend == 1:
                        self.window_chat_context.get_new_msg()
                        pass
                    elif self.window_chat_context is not None and self.window_chat_context.to_id == to_id \
                            and self.window_chat_context.is_friend == 0 and is_friend == 0:
                        self.window_chat_context.get_new_msg()
                    else:
                        if is_friend == 1:
                            self.frames_friend_view[from_uid].new_msg_comming()
                        else:
                            self.frames_group_view[to_id].new_msg_comming()
                # 发送文本消息成功， 写入本地缓存，更新显示
                if msg['type'] == UtilsAndConfig.CHAT_SEND_MSG_SUCCESS:
                    from_uid = msg['from_uid']
                    to_id = msg['to_id']
                    send_time = msg['send_time']
                    msg_text = msg['msg_text']
                    is_friend = msg['is_friend']
                    txt = {'type': 'send', 'datetime': send_time, 'msg': msg_text, 'msg_type': 'train'}
                    UtilsAndConfig.add_one_chat_record(self.uid, is_friend, from_uid, to_id,
                                                       json.dumps(txt, cls=UtilsAndConfig.MyJSONEncoder,
                                                                  ensure_ascii=False), True)
                    self.window_chat_context.get_new_msg()
                # 发送文件成功
                if msg['type'] == UtilsAndConfig.CHAT_SEND_FILE_SUCCESS:
                    to_id = msg['to_id']
                    send_time = msg['send_time']
                    file_name = msg['file_name']
                    is_friend = msg['is_friend']
                    txt = {'type': 'send', 'datetime': send_time, 'msg': file_name, 'msg_type': 'file'}
                    UtilsAndConfig.add_one_chat_record(self.uid, is_friend, self.uid, to_id,
                                                       json.dumps(txt, cls=UtilsAndConfig.MyJSONEncoder,
                                                                  ensure_ascii=False), True)
                    self.window_chat_context.get_new_msg()
                    self.window_chat_context.sending_file(False)
                # 收到文件
                if msg['type'] == UtilsAndConfig.CHAT_HAS_NEW_FILE:
                    to_id = msg['to_id']
                    from_uid = msg['from_uid']
                    send_time = msg['send_time']
                    file_name = msg['file_name']
                    is_friend = msg['is_friend']
                    file_path = msg['file_path']
                    files_dir = os.path.abspath(os.path.dirname(__file__)) + '/static/LocalCache/' \
                                + str(self.uid) + '/files/'
                    if not os.path.exists(os.path.dirname(files_dir)):
                        os.makedirs(os.path.dirname(files_dir))

                    all_file_name = file_name.split('/')[-1]
                    file_suffix = all_file_name.split('.')[-1]
                    end_index = len(all_file_name) - len(file_suffix) - 1
                    file_name = all_file_name[0:end_index]
                    file_save_path = files_dir + file_name + '.' + file_suffix
                    i = 1
                    while os.path.exists(file_save_path):
                        file_save_path = files_dir + file_name + '（' + str(i) + '）' + '.' + file_suffix
                        i += 1
                    # http下载文件，保存到本地
                    try:
                        url = self.server_config.HTTP_SERVER_ADDRESS + file_path
                        res = requests.get(url)
                        file_content = res.content
                        file = open(file_save_path, 'wb')
                        file.write(file_content)
                        file.close()
                    except requests.exceptions.InvalidSchema:
                        pass
                        # 服务器中文件不存在
                    txt = {'type': 'get', 'from_uid': from_uid, 'datetime': send_time,
                           'msg': file_save_path, 'msg_type': 'file'}
                    UtilsAndConfig.add_one_chat_record(self.uid, is_friend, from_uid, to_id,
                                                       json.dumps(txt, cls=UtilsAndConfig.MyJSONEncoder,
                                                                  ensure_ascii=False), False)

                    if self.window_chat_context is not None and self.window_chat_context.to_id == from_uid \
                            and self.window_chat_context.is_friend == 1 and is_friend == 1:
                        self.window_chat_context.get_new_msg()
                        pass
                    elif self.window_chat_context is not None and self.window_chat_context.to_id == to_id \
                            and self.window_chat_context.is_friend == 0 and is_friend == 0:
                        self.window_chat_context.get_new_msg()
                    else:
                        if is_friend == 1:
                            self.frames_friend_view[from_uid].new_msg_comming()
                        else:
                            self.frames_group_view[to_id].new_msg_comming()
                    # 告诉服务器 文件下载完成，可删除
                    url = self.server_config.HTTP_SERVER_ADDRESS + '/downloadFileSuccess?path=' + file_path
                    requests.get(url)
                # 发送聊天消息失败，不写入缓存，提示对方已下线
                if msg['type'] == UtilsAndConfig.CHAT_SEND_MSG_ERR:
                    tkinter.messagebox.showwarning('提示', '对方已下线或无在线群成员，不能发送消息')
                # 服务器强制下线
                if msg['type'] == UtilsAndConfig.SYSTEM_LOGOUT:
                    self.socket.close()
                    tkinter.messagebox.showwarning('提示', '此账号已在别处登录!')
                    self.root.destroy()
                    return
            except ConnectionAbortedError:
                tkinter.messagebox.showwarning('提示', '与服务器断开连接!')
                self.root.destroy()
                return
            except ConnectionResetError:
                tkinter.messagebox.showwarning('提示', '与服务器断开连接!')
                self.root.destroy()
                return

    # 基本函数
    def process_wheel(self, event):
        a = int(-event.delta / 60)
        self.canvas.yview_scroll(a, 'units')

    def open_add_friends(self):
        def search_friends():
            for widget in frame_search_result.winfo_children():
                widget.destroy()
            search_text = var_search_text.get()
            if search_text == '' or len(search_text) == 0:
                return
            else:
                search_friends_url = self.server_config.HTTP_SERVER_ADDRESS + \
                                     '/searchFriendsGroups?searchText=' + search_text
                result_search_friends = requests.get(search_friends_url)
                result_search_friends = json.loads(result_search_friends.text)
                if result_search_friends['code'] != 200:
                    Label(frame_search_result, text='参数出错，请正确搜索', anchor='w', fg='red').pack()
                    return
                else:
                    def add_friends():
                        url = self.server_config.HTTP_SERVER_ADDRESS + '/addFriendsOrGroup?type=' + str(friend_type) + \
                              '&uid=' + str(self.uid) + '&id=' + str(friend_id)
                        add_friend = requests.get(url)
                        add_friend_json = json.loads(add_friend.text)
                        if add_friend_json['code'] != 200:
                            Label(frame_search_result, text='添加时发生错误，请重试', anchor='w', fg='red').pack()
                        else:
                            search_friends()

                    search_friends_data = result_search_friends['data']
                    if search_friends_data['type'] not in ['user', 'group', 'none']:
                        Label(frame_search_result, text='参数出错，请正确搜索', anchor='w', fg='red').pack()
                        return
                    if search_friends_data['type'] == 'none':
                        Label(frame_search_result, text='不存登录名/群号', anchor='w', fg='red').pack()
                        return
                    column0 = ''
                    column1 = ''
                    column2 = ''
                    column3 = ''
                    if search_friends_data['type'] == 'user':
                        column0 = '类型 ： 用户'
                        column1 = '登录名 ： ' + search_friends_data['data']['loginName']
                        column2 = '昵称 ： ' + search_friends_data['data']['username']
                        if search_friends_data['data']['sex'] == 1:
                            column3 = '性别 ： ' + '男'
                        else:
                            column3 = '性别 : ' + '女'
                    if search_friends_data['type'] == 'group':
                        column0 = '类型 ： 群'
                        column1 = '群名 ： ' + search_friends_data['data']['gname']
                        gid = search_friends_data['data']['id']
                        search_get_group_size_url = self.server_config.HTTP_SERVER_ADDRESS + \
                                                    '/getGroupSize?gid=' + str(gid)
                        search_json_text = json.loads(requests.get(search_get_group_size_url).text)
                        if search_json_text['code'] == 200:
                            column2 = '群人数 ： ' + str(search_json_text['data'])
                        create_uid = search_friends_data['data']['createUid']
                        column3 = '群主 ：' + UtilsAndConfig.get_username_by_uid(create_uid)

                    # label_search_result_column0 = Label(frame_search_result, bg='#C6E4E8',text=column0, anchor='w')
                    # label_search_result_column0.pack(side=TOP, fill=X)
                    # label_search_result_column1 = Label(frame_search_result, bg='#C6E4E8',text=column1, anchor='w')
                    # label_search_result_column1.pack(side=TOP, fill=X)
                    label_search_result_column2 = Label(frame_search_result, bg='#C6E4E8',text=column2, anchor='w')
                    label_search_result_column2.pack(side=TOP, fill=X)
                    label_search_result_column3 = Label(frame_search_result, bg='#C6E4E8',text=column3, anchor='w')
                    label_search_result_column3.pack(side=TOP, fill=X)

                    friend_type = search_friends_data['type']
                    friend_id = search_friends_data['data']['id']

                    url = self.server_config.HTTP_SERVER_ADDRESS + '/canAddFriends?type=' + friend_type + \
                          '&uid=' + str(self.uid) + '&id=' + str(friend_id)
                    search_json_text = json.loads(requests.get(url).text)
                    if search_json_text['data'] == 1:
                        column4 = '状态 ： 已添加 或 已发送申请'
                        label_search_result_column4 = Label(frame_search_result,bg='#C6E4E8', text=column4, anchor='w', fg='red')
                        label_search_result_column4.pack(side=TOP, fill=X)
                    else:
                        column4 = '状态 ： 未添加 或 未发送申请'
                        label_search_result_column4 = Label(frame_search_result, bg='#C6E4E8',text=column4, anchor='w', fg='green')
                        label_search_result_column4.pack(side=TOP, fill=X)

                    button_search_result_add = Button(frame_search_result,bg='#ABDAD9', text='添 加', command=add_friends)
                    button_search_result_add.pack(side=TOP, fill=X)

                    if search_json_text['data'] == 1:
                        button_search_result_add['state'] = DISABLED
                    else:
                        button_search_result_add['state'] = NORMAL

        window_add_friends = Toplevel(self.root)
        window_add_friends.geometry('330x400+200+100')
        window_add_friends.title('添加好友')
        window_add_friends.transient(self.root)
        window_add_friends.configure(bg='#C6E4E8')
        var_search_text = StringVar()
        var_search_text.set('')

        frame_add_friends_search = Frame(window_add_friends, bg='#C6E4E8', relief=RAISED, borderwidth=0, width=300, height=40)
        frame_add_friends_search.pack()
        label_add_friends_search = Label(frame_add_friends_search, bg='#C6E4E8',text='用户昵称：')
        label_add_friends_search.place(x=2, y=8)
        entry_add_friends_search_text = Entry(window_add_friends, width=20, textvariable=var_search_text)
        entry_add_friends_search_text.place(x=100, y=8)
        button_entry_add_friends_search = Button(window_add_friends,bg='#ABDAD9', text='点击搜索', command=search_friends)
        button_entry_add_friends_search.place(x=240, y=5)
        frame_search_result = Frame(window_add_friends, bg='#C6E4E8',relief=RAISED, borderwidth=0, width=300, height=40)
        frame_search_result.pack()

    def open_message_window(self):
        window_message = Toplevel(self.root)
        window_message.geometry('600x400+600+400')
        window_message.title('请求加好友/群')
        window_message.transient(self.root)

        # 加载未处理的消息
        message_url = self.server_config.HTTP_SERVER_ADDRESS + '/getNoHandleMessages?uid=' + str(self.uid)
        result_msg = requests.get(message_url)
        result_msg_json = json.loads(result_msg.text)
        if result_msg_json['code'] != 200:
            Label(window_message, text='参数出错，请正确搜索', anchor='w', fg='red').pack()
        else:
            msgs = result_msg_json['data']
            if len(msgs) == 0:
                Label(window_message, text='无消息', anchor='w', fg='red').pack()

            y_index = 0

            def agree(msg_id):
                msg_handle_url = self.server_config.HTTP_SERVER_ADDRESS + \
                                 '/messageHandle?msgId=' + str(msg_id) + '&msgHandle=1'
                requests.get(msg_handle_url)
                window_message.destroy()
                self.open_message_window()

            def disagree(msg_id):
                msg_handle_url = self.server_config.HTTP_SERVER_ADDRESS + \
                                 '/messageHandle?msgId=' + str(msg_id) + '&msgHandle=2'
                requests.get(msg_handle_url)
                window_message.destroy()
                self.open_message_window()

            for m in msgs:
                # 1: 添加好友
                # 2: 申请入群
                # 3: 邀请入群
                from_username = UtilsAndConfig.get_username_by_uid(m['fromUid'])

                frame_message_add_user = Frame(window_message, relief=RAISED, borderwidth=1, width=700, height=60)
                frame_message_add_user.place(x=0, y=y_index)
                if m['type'] == 1:
                    text = '用户:  ' + from_username + '， 申请添加您为好友'
                    Label(frame_message_add_user, text=text).place(x=20, y=20)
                if m['type'] == 2:
                    gname = UtilsAndConfig.get_group_name_by_gid(m['gId'])
                    text = '用户:  ' + from_username + '， 申请加入群聊: ' + gname
                    Label(frame_message_add_user, text=text).place(x=20, y=20)
                if m['type'] == 3:
                    gname = UtilsAndConfig.get_group_name_by_gid(m['gId'])
                    text = '用户:  ' + from_username + '， 邀请您加入群聊: ' + gname
                    Label(frame_message_add_user, text=text).place(x=20, y=20)
                Button(frame_message_add_user,bg='#ABDAD9', text='同 意', command=lambda arg=m['id']: agree(arg)).place(x=560, y=15)
                Button(frame_message_add_user, bg='#ABDAD9', text='拒绝', command=lambda arg=m['id']: disagree(arg)).place(x=625, y=15)
                y_index += 60

    def open_create_groups(self):
        def create_gourp():
            group_name = var_group_name.get()
            if len(group_name) == 0:
                var_group_tip.set('不能为空')
                return
            if len(group_name) > 6:
                var_group_tip.set('不能超过6个字')
                return
            if group_name.isdigit():
                var_group_tip.set('不能为纯数字')
                return
            var_group_tip.set('')
            create_gourp_url = self.server_config.HTTP_SERVER_ADDRESS + \
                               '/createGroup?uid=' + str(self.uid) + '&gName=' + group_name
            create_gourp_json = json.loads(requests.get(create_gourp_url).text)
            if create_gourp_json['code'] != 200:
                var_group_tip.set(create_gourp_json['message'])
                return
            tkinter.messagebox.showwarning('提示', '创建成功')
            window_create_group.destroy()

        window_create_group = Toplevel(self.root)
        window_create_group.geometry('300x400+200+100')
        window_create_group.title('创建群聊')
        window_create_group.transient(self.root)
        window_create_group.configure(bg='#C6E4E8')
        var_group_name = StringVar()
        var_group_name.set('')
        var_group_tip = StringVar()
        var_group_tip.set('不能使用纯数字')

        frames_group_name = Frame(window_create_group, bg='#C6E4E8', relief=RAISED, borderwidth=0, width=300, height=40)
        frames_group_name.pack()
        Label(frames_group_name, bg='#C6E4E8', text='群昵称：').place(x=10, y=10)
        Entry(frames_group_name, width=28, textvariable=var_group_name).place(x=60, y=10)
        Label(window_create_group, textvariable=var_group_tip, fg='red').pack()
        Button(window_create_group, text='点击确定', bg='#ABDAD9', width=20, command=create_gourp).pack()
