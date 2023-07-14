from tkinter import *
import tkinter.messagebox
import UtilsAndConfig
import requests
import json
import datetime
import tkinter.font as tf
import tkinter.filedialog
import os
from UtilsAndConfig import ServerConfig

# 聊天窗口类
class ChatWindow(Frame):

    def __init__(self, master=None, home_view=None, is_friend=None, uid=None, to_id=None):
        super().__init__(master)
        self.server_config = ServerConfig()
        self.master = master
        self.uid = uid
        self.home_view = home_view
        self.is_friend = is_friend
        self.to_id = to_id
        self.chat_record_text = None
        self.chat_msg_text = None
        self.chat_record_scroll = None
        self.frame_bottom_right = None
        self.window_choose_emoji = None
        self.label_sending_file = None
        self.button_send = None
        self.canvas = None
        self.canvas_frame = None
        self.label_group_name = None
        self.label_group_name_text = StringVar()
        self.label_top_text = StringVar()
        self.usernames = dict()
        self.img_files = list()

        self.init_usernames()
        self.create_widget()
        self.init_msg_text()

    def init_usernames(self):
        if self.is_friend == 1:
            friend_name = UtilsAndConfig.get_username_by_uid(self.to_id)
            self.usernames[self.to_id] = friend_name
        else:
            url = self.server_config.HTTP_SERVER_ADDRESS + '/getGroupMembers?gid=' + str(self.to_id)
            result_json = json.loads(requests.get(url).text)
            if result_json['code'] == 200:
                for u in result_json['data']:
                    self.usernames[u['id']] = u['username']

    # 绘制私聊和群聊窗口
    def create_widget(self):

        # 上方标题
        frame_top = Frame(self.master, relief=RAISED, borderwidth=0, height=30, width=720)
        frame_top.place(x=0, y=0)

        # 判断私聊和群聊
        if self.is_friend == 1:
            self.label_top_text.set('与 ' + self.usernames[self.to_id] + ' 聊天中')
        else:
            self.label_top_text.set('在 ' + UtilsAndConfig.get_group_name_by_gid(self.to_id) + ' 群与大家聊天中')


        # 显示的字体
        Label(frame_top, textvariable=self.label_top_text, width=90, bg='#ABDAD9',
              font=('黑体', 12)).place(x=0, y=2)

        frame_bottom = Frame(self.master, bg='#E1EFF5', relief=RAISED, borderwidth=0, height=670, width=740)
        frame_bottom.place(x=0, y=25)

        frame_bottom_left = Frame(frame_bottom, relief=RAISED, borderwidth=0, height=670, width=650)
        frame_bottom_left.place(x=0, y=0)

        frame_chat_record = Frame(frame_bottom_left, bg='#E1EFF5', relief=RAISED, borderwidth=0, height=230, width=530)
        frame_chat_record.place(x=0, y=0)


        # 聊天记录框 530x330
        chat_record_scroll = Scrollbar(frame_chat_record, bg='#F7F9ED', width=10)
        self.chat_record_text = Text(frame_chat_record, state=DISABLED, width=75, height=25)
        chat_record_scroll.pack(side='right', fill=Y)
        self.chat_record_text.pack(side='left', fill=Y)
        chat_record_scroll.config(command=self.chat_record_text.yview)
        self.chat_record_text.config(yscrollcommand=chat_record_scroll.set)

        # 4f7da4
        frame_emoji = Frame(frame_bottom_left, bg='#E1EFF5', relief=RAISED, borderwidth=0, height=40, width=650)
        frame_emoji.place(x=0, y=330)
        Button(frame_emoji, bg='#ABDAD9', text='表 情', command=self.open_choose_emoji).place(x=10, y=5)
        Button(frame_emoji, bg='#ABDAD9', text='图 片', command=self.open_choose_img).place(x=60, y=5)
        Button(frame_emoji, bg='#ABDAD9', text='文 件', command=self.open_choose_file).place(x=110, y=5)
        Button(frame_emoji, bg='#ABDAD9', text='下载管理', command=self.browse_files).place(x=160, y=5)
        self.label_sending_file = Label(frame_emoji, text='发送文件中...请等待！', fg='red')

        # 聊天输入框
        frame_send_msg = Frame(frame_bottom_left, bg='#E1EFF5', relief=RAISED, borderwidth=0, height=185, width=650)
        frame_send_msg.place(x=0, y=370)

        chat_msg_scroll = Scrollbar(frame_send_msg, width=10)
        self.chat_msg_text = Text(frame_send_msg, state=NORMAL, width=60, height=11)
        self.chat_msg_text.pack(side='left', fill=Y)
        self.chat_msg_text.bind('<KeyRelease-Return>', self.send_msg_event)
        chat_msg_scroll.pack(side='left', fill=Y)
        chat_msg_scroll.config(command=self.chat_msg_text.yview)
        self.chat_msg_text.config(yscrollcommand=chat_msg_scroll.set)
        self.button_send = Button(frame_send_msg, width=10, text='发     送', command=self.send_msg)
        self.button_send.pack(side='right')

        self.frame_bottom_right = Frame(frame_bottom, height=520, width=180, bg='#E1EFF5')
        self.frame_bottom_right.place(x=540, y=0)

        scrollbar = Scrollbar(self.frame_bottom_right, width=10)
        self.canvas = Canvas(self.frame_bottom_right, yscrollcommand=scrollbar.set, height=520, width=160, bg='#E1EFF5')
        scrollbar.config(command=self.canvas.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.canvas.pack(side=LEFT, fill='both', expand=True)
        self.init_frame_bottom_right()
        self.master.update()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        self.canvas.bind("<MouseWheel>", self.process_wheel)

    # ffffff
    def process_wheel(self, event):
        a = int(-event.delta / 60)
        self.canvas.yview_scroll(a, 'units')

    def open_choose_file(self):
        file_types = [('发送文件', '*.*')]
        file_path = tkinter.filedialog.askopenfilename(title=u'选择文件', filetypes=file_types)
        self.home_view.chat_send_file(file_path, self.is_friend, self.to_id)

    def browse_files(self):
        dir_path = os.path.abspath(os.path.dirname(__file__)) + '/static/LocalCache/' + str(self.uid) + '/files/'
        if not os.path.exists(os.path.dirname(dir_path)):
            os.makedirs(os.path.dirname(dir_path))
        os.startfile(dir_path)

    def open_choose_img(self):
        file_types = [('发送图片', '*.jpg *.png *.gif')]
        file_path = tkinter.filedialog.askopenfilename(title=u'选择照片', filetypes=file_types)
        self.home_view.chat_send_file(file_path, self.is_friend, self.to_id)

    def open_choose_emoji(self):
        master_geometry = self.master.geometry()
        strs = str(master_geometry).split('+')
        w = int(strs[1]) + 33
        h = int(strs[2]) + 300
        if self.window_choose_emoji is not None:
            self.window_choose_emoji.destroy()
        self.window_choose_emoji = Toplevel(self)
        position = '438x230+w+h'.replace('w', str(w))
        position = position.replace('h', str(h))
        self.window_choose_emoji.geometry(position)
        self.window_choose_emoji.title('表情')
        self.window_choose_emoji.transient(self.master)

        frame_emoji = Frame(self.window_choose_emoji, relief=RAISED, borderwidth=2)
        frame_emoji.pack(side=TOP, fill=BOTH, ipadx=5, ipady=5, expand=1)

        # 1行19个
        i = 0
        row_cout = 14
        for emoji in self.home_view.emoji_cache:
            Button(frame_emoji, image=self.home_view.emoji_cache[emoji],
                   command=lambda arg=emoji: self.emoji_click(arg))\
                .grid(row=i//row_cout, column=i % row_cout)
            i += 1

    def emoji_click(self, emoji_name):
        self.chat_msg_text.insert(END, '[' + emoji_name + ']')
        self.chat_msg_text.see(END)
        self.window_choose_emoji.destroy()
        self.window_choose_emoji = None

    def init_frame_bottom_right(self):
        if self.canvas_frame is not None:
            for widget in self.canvas_frame.winfo_children():
                widget.destroy()
        # 好友时
        if self.is_friend:
            # 好友：删除好友操作
            self.canvas_frame = Frame(self.canvas, bg='#E1EFF5', width=160, height=520, )
            self.canvas.create_window(0, 0, window=self.canvas_frame, anchor='nw', width=160)
            self.canvas_frame.bind("<MouseWheel>", self.process_wheel)
            but_del = Button(self.canvas_frame, bg='#ABDAD9',text='删除好友', command=self.delete_friend)
            but_del.place(x=5, y=20)
            but_del.bind("<MouseWheel>", self.process_wheel)

            url = self.server_config.HTTP_SERVER_ADDRESS + '/getUserById?uid=' + str(self.to_id)
            result_json = json.loads(requests.get(url).text)
            if result_json['code'] == 200:
                user = result_json['data']
                column1 = '登录名： ' + user['loginName']
                column2 = '昵  称： ' + user['username']
                column3 = '性  别： 男' if user['sex'] == 1 else '性  别： 女'
                # label1 = Label(self.canvas_frame, text=column1, anchor='w', bg='#C6E4E8')
                # label1.place(x=0, y=60)
                label2 = Label(self.canvas_frame, text=column2, anchor='w',)
                label2.place(x=0, y=90)
                label3 = Label(self.canvas_frame, text=column3, anchor='w', )
                label3.place(x=0, y=120)

                # label1.bind("<MouseWheel>", self.process_wheel)
                label2.bind("<MouseWheel>", self.process_wheel)
                label3.bind("<MouseWheel>", self.process_wheel)
        # 群聊时
        else:
            url = self.server_config.HTTP_SERVER_ADDRESS + '/getGroupsDetails?gid=' + str(self.to_id)
            result_json = json.loads(requests.get(url).text)
            if result_json['code'] == 200:
                # 群主：邀请新人，解散群，删除人
                # 成员：退出群
                is_create_user = False

                column1 = '群  名 ： ' + result_json['data']['group']['gname']
                column2 = '群  号 ： ' + str(result_json['data']['group']['id'])
                column3 = '群  主 ： ' + result_json['data']['createName']
                column4 = '成员数 ： ' + str(len(result_json['data']['members']))
                online = 0
                for m in result_json['data']['members']:
                    if m['online'] == 1:
                        online += 1
                column5 = '在线数 ： ' + str(online)

                f_height = 180 + (37 * len(result_json['data']['members']))
                if result_json['data']['group']['createUid'] == self.uid:
                    f_height = 220 + (37 * len(result_json['data']['members']))
                    is_create_user = True
                self.canvas_frame = Frame(self.canvas, width=160, height=f_height, bg='#E1EFF5')
                self.canvas.create_window(0, 0, window=self.canvas_frame, anchor='nw', width=160)
                self.canvas_frame.bind("<MouseWheel>", self.process_wheel)
                y_index = 20
                if is_create_user:
                    btn_add = Button(self.canvas_frame, bg='#ABDAD9', text='邀请新人', command=self.open_add_member_window, width=16)
                    btn_add.place(x=5, y=y_index)
                    y_index += 40
                    bun_delete = Button(self.canvas_frame,bg='#ABDAD9', text='解散此群', command=self.delete_group, width=16)
                    bun_delete.place(x=5, y=y_index)
                    y_index += 40
                    bun_modify = Button(self.canvas_frame,bg='#ABDAD9', text='修改群名', command=self.modify_group_name, width=16)
                    bun_modify.place(x=5, y=y_index)
                    y_index += 10
                    btn_add.bind("<MouseWheel>", self.process_wheel)
                    bun_delete.bind("<MouseWheel>", self.process_wheel)
                else:
                    btn_quit = Button(self.canvas_frame,bg='#ABDAD9', text='退出此群', command=self.quit_group)
                    btn_quit.place(x=5, y=y_index)
                    btn_quit.bind("<MouseWheel>", self.process_wheel)
                y_index += 40
                self.label_group_name_text.set(column1)
                self.label_group_name = Label(self.canvas_frame,
                                              textvariable=self.label_group_name_text, anchor='w', bg='#E1EFF5')
                self.label_group_name.place(x=0, y=y_index)
                y_index += 20
                label2 = Label(self.canvas_frame, text=column2, anchor='w', bg='#E1EFF5')
                label2.place(x=0, y=y_index)
                y_index += 20
                label3 = Label(self.canvas_frame, text=column3, anchor='w', bg='#E1EFF5')
                label3.place(x=0, y=y_index)
                y_index += 20
                label4 = Label(self.canvas_frame, text=column4, anchor='w', bg='#E1EFF5')
                label4.place(x=0, y=y_index)
                y_index += 20
                label5 = Label(self.canvas_frame, text=column5, anchor='w', bg='#E1EFF5')
                label5.place(x=0, y=y_index)

                self.label_group_name.bind("<MouseWheel>", self.process_wheel)
                label2.bind("<MouseWheel>", self.process_wheel)
                label3.bind("<MouseWheel>", self.process_wheel)
                label4.bind("<MouseWheel>", self.process_wheel)
                label5.bind("<MouseWheel>", self.process_wheel)

                y_index += 35
                for m in result_json['data']['members']:
                    if m['online'] == 1:
                        members_text = m['name'] + ' [在线]'
                        label_tmp = Label(self.canvas_frame, text=members_text, anchor='w',
                                          bg='#E1EFF5', fg='green')
                        label_tmp.place(x=0, y=y_index + 5)
                        label_tmp.bind("<MouseWheel>", self.process_wheel)
                    else:
                        members_text = m['name'] + ' [离线]'
                        label_tmp = Label(self.canvas_frame, text=members_text, anchor='w',
                                          bg='#E1EFF5', fg='#999999')
                        label_tmp.place(x=0, y=y_index + 5)
                        label_tmp.bind("<MouseWheel>", self.process_wheel)
                    if is_create_user:
                        if result_json['data']['group']['createUid'] != m['uid']:
                            btn_tmp = Button(self.canvas_frame, bg='#ABDAD9',text='踢出', width=5,
                                             command=lambda arg=m['uid']: self.remove_member(arg))
                            btn_tmp.place(x=100, y=y_index)
                            btn_tmp.bind("<MouseWheel>", self.process_wheel)
                    y_index += 35

    def remove_member(self, uid):
        if tkinter.messagebox.askyesno("提示", "确定要踢出此人吗? "):
            url = self.server_config.HTTP_SERVER_ADDRESS + '/removeMember?uid='\
                  + str(uid) + '&gid=' + str(self.to_id) + '&createId=' + str(self.uid)
            result_json = json.loads(requests.get(url).text)
            if result_json['code'] == 200:
                self.home_view.init_friends_and_group_view()
                self.init_frame_bottom_right()
                tkinter.messagebox.showwarning('提示', '踢出成功')
            else:
                tkinter.messagebox.showwarning('提示', result_json['message'])

    def open_add_member_window(self):
        def search_user():
            for widget in frame_search_result.winfo_children():
                widget.destroy()
            search_text = var_search_text.get().strip()
            if search_text == '' or len(search_text) == 0:
                Label(frame_search_result, text='参数出错，请正确搜索', anchor='w', fg='red').pack()
                return
            if not UtilsAndConfig.check_login_name(search_text):
                Label(frame_search_result, text='参数出错，请正确搜索', anchor='w', fg='red').pack()
                return
            else:
                search_friends_url = self.server_config.HTTP_SERVER_ADDRESS\
                                     + '/searchUserByLoginname?searchText=' + search_text
                result_search_friends = json.loads(requests.get(search_friends_url).text)
                if result_search_friends['code'] != 200:
                    Label(frame_search_result, text=result_search_friends['message'], anchor='w', fg='red').pack()
                    return
                else:
                    def add_member():
                        url = self.server_config.HTTP_SERVER_ADDRESS + '/addGroupMember?gid=' + str(self.to_id) + \
                              '&uid=' + str(user_id) + '&fromId=' + str(self.uid)
                        add_member_json = json.loads(requests.get(url).text)
                        if add_member_json['code'] != 200:
                            Label(frame_search_result, text='参数出错，请正确搜索', anchor='w', fg='red').pack()
                        else:
                            search_user()

                    column1 = '登录名 ： ' + result_search_friends['data']['loginName']
                    column2 = '昵称 ： ' + result_search_friends['data']['username']
                    if result_search_friends['data']['sex'] == 1:
                        column3 = '性别 ： ' + '男'
                    else:
                        column3 = '性别 : ' + '女'
                    Label(frame_search_result, bg='#E1EFF5',text=column1, anchor='w').pack(side=TOP, fill=X)
                    Label(frame_search_result, bg='#E1EFF5',text=column2, anchor='w').pack(side=TOP, fill=X)
                    Label(frame_search_result, bg='#E1EFF5',text=column3, anchor='w').pack(side=TOP, fill=X)
                    user_id = result_search_friends['data']['id']

                    url = self.server_config.HTTP_SERVER_ADDRESS + '/canAddGroupMember?uid=' +\
                          str(user_id) + '&gid=' + str(self.to_id)
                    search_json_text = json.loads(requests.get(url).text)
                    if search_json_text['data'] == 0:
                        column4 = '状态 ： 已添加 或 已发送申请'
                        label_search_result_column4 = Label(frame_search_result, text=column4, anchor='w', fg='red')
                        label_search_result_column4.pack(side=TOP, fill=X)
                    else:
                        column4 = '状态 ： 未添加 或 未发送申请'
                        label_search_result_column4 = Label(frame_search_result, text=column4, anchor='w', fg='green')
                        label_search_result_column4.pack(side=TOP, fill=X)

                    button_search_result_add = Button(frame_search_result, text='添 加', command=add_member)
                    button_search_result_add.pack(side=TOP, fill=X)

                    if search_json_text['data'] == 0:
                        button_search_result_add['state'] = DISABLED
                    else:
                        button_search_result_add['state'] = NORMAL

        add_member_window = Toplevel(self.master)
        add_member_window.geometry('330x400+200+200')
        add_member_window.title('邀请入群窗口')
        add_member_window.transient(self.master)

        var_search_text = StringVar()
        var_search_text.set('')

        frame_user_search = Frame(add_member_window, relief=RAISED, borderwidth=0, width=300, height=40)
        frame_user_search.pack()
        Label(frame_user_search, text='登录名：').place(x=10, y=8)
        Entry(frame_user_search, width=20, textvariable=var_search_text).place(x=100, y=8)
        Button(frame_user_search, text='搜 索', command=search_user).place(x=260, y=5)
        frame_search_result = Frame(add_member_window, bg='#E1EFF5', relief=RAISED, borderwidth=0, width=300, height=40)
        frame_search_result.pack()

    def modify_group_name(self):
        def modify_name():
            new_group_name = var_new_group_name.get().strip()
            if len(new_group_name) == 0:
                label_tip_text.set('不能为空')
                return
            if len(new_group_name) > 6:
                label_tip_text.set('不能超过6个字')
                return
            if new_group_name.isdigit():
                label_tip_text.set('不能为纯数字')
                return
            url = self.server_config.HTTP_SERVER_ADDRESS + '/modifyGroupName?gid=' + str(self.to_id) +\
                  '&newName=' + new_group_name + '&uid=' + str(self.uid)
            result_json = json.loads(requests.get(url).text)
            if result_json['code'] == 200:
                # 刷新群名
                self.label_group_name_text.set('群  名 ： ' + new_group_name)
                self.label_top_text.set('与【' + new_group_name + '】群聊中')
                self.master.update()
                modify_group_name_win.destroy()
                self.home_view.init_friends_and_group_view()
                tkinter.messagebox.showwarning('提示', '修改成功')
            else:
                label_tip_text.set(result_json['message'])
                return

        modify_group_name_win = Toplevel(self.master)
        modify_group_name_win.geometry('375x200+200+100')
        modify_group_name_win.title('修改群名')
        modify_group_name_win.transient(self.master)

        var_new_group_name = StringVar()
        var_new_group_name.set('')

        # 创建了一个名为 frame_input 的框架
        frame_input = Frame(modify_group_name_win, width=375, height=40)
        frame_input.pack()
        Label(frame_input, text='新群名 ：').place(x=50, y=8)   # 创建标签
        Entry(frame_input, width=20, textvariable=var_new_group_name).place(x=120, y=8)
        Button(frame_input, text='修  改', command=modify_name).place(x=280, y=5)
        label_tip_text = StringVar()
        label_tip_text.set('不能使用纯数字')
        label_tip = Label(modify_group_name_win, textvariable=label_tip_text, fg='red')
        label_tip.pack()

    def delete_group(self):
        if tkinter.messagebox.askyesno("提示", "确定要解散此群吗? "):
            url = self.server_config.HTTP_SERVER_ADDRESS + '/deleteGroup?uid='\
                  + str(self.uid) + '&groupId=' + str(self.to_id)
            result_json = json.loads(requests.get(url).text)
            if result_json['code'] == 200:
                self.home_view.close_window_chat()
                self.home_view.init_friends_and_group_view()
                tkinter.messagebox.showwarning('提示', '解散成功')
            else:
                tkinter.messagebox.showwarning('提示', result_json['message'])

    def quit_group(self):
        if tkinter.messagebox.askyesno("提示", "确定要退出此群吗? "):
            url = self.server_config.HTTP_SERVER_ADDRESS + '/quitGroup?uid='\
                  + str(self.uid) + '&groupId=' + str(self.to_id)
            result_json = json.loads(requests.get(url).text)
            if result_json['code'] == 200:
                self.home_view.close_window_chat()
                self.home_view.init_friends_and_group_view()
                tkinter.messagebox.showwarning('提示', '退出成功')
            else:
                tkinter.messagebox.showwarning('提示', result_json['message'])

    def delete_friend(self):
        if tkinter.messagebox.askyesno("提示", "确定要删除此好友吗? "):
            url = self.server_config.HTTP_SERVER_ADDRESS + '/delete_friend?uid='\
                  + str(self.uid) + '&friendId=' + str(self.to_id)
            result_json = json.loads(requests.get(url).text)
            if result_json['code'] == 200:
                self.home_view.close_window_chat()
                tkinter.messagebox.showwarning('提示', '删除成功')
            else:
                tkinter.messagebox.showwarning('提示', result_json['message'])

    # 初始化消息文本
    def init_msg_text(self):
        # 得到自己的消息缓存文件
        path = UtilsAndConfig.get_local_cache_path(self.uid, self.is_friend, self.uid, self.to_id, True)
        UtilsAndConfig.check_path(path)
        with open(path, 'r', encoding='utf-8') as f:
            # 先读出第一行然后抛弃
            line = f.readline()
            line = f.readline()
            # 循环读出文件内容
            while line is not None and line != '':
                msg = UtilsAndConfig.decode_msg(line)
                self.add_line(msg)
                line = f.readline()

    # 显示消息记录
    def add_line(self, msg):
        ft_time = tf.Font(family='微软雅黑', size=8)
        ft_msg = tf.Font(family='微软雅黑', size=12)
        self.chat_record_text['state'] = NORMAL
        self.chat_record_text.insert(END, '\n\n')

        msg_json = json.loads(str(msg))
        msg_txt = UtilsAndConfig.decode_msg(msg_json['msg'])
        send_time = msg_json['datetime']
        msg_type = msg_json['msg_type']
        name = '我: '
        msg_tag = "msg_send"
        if msg_json['type'] == 'get':
            msg_tag = "msg_get"
            if msg_json['from_uid'] in self.usernames.keys():
                name = self.usernames[msg_json['from_uid']] + ': '
            else:
                name = UtilsAndConfig.get_username_by_uid(msg_json['from_uid'])

        self.chat_record_text.insert(END, name + send_time, 'time')
        self.chat_record_text.tag_add('time', END)
        self.chat_record_text.tag_config('time', foreground='#666666', font=ft_time)

        self.chat_record_text.insert(END, '\n')
        # 文本
        if msg_type == 'train':
            # 检测是否有表情，并显示
            text_length = len(msg_txt)
            i = 0
            flag = False
            emoji_name = ''
            while i < text_length:
                if not flag and msg_txt[i] != '[':
                    self.chat_record_text.insert(END, msg_txt[i], msg_tag)
                elif not flag and msg_txt[i] == '[':
                    flag = True
                elif flag and msg_txt[i] == ']':
                    if emoji_name in self.home_view.emoji_cache.keys():
                        self.chat_record_text.image_create(END, image=self.home_view.emoji_cache[emoji_name])
                    else:
                        self.chat_record_text.insert(END, '[' + emoji_name + ']', msg_tag)
                    emoji_name = ''
                    flag = False
                else:
                    emoji_name = emoji_name + msg_txt[i]
                i += 1
            if flag:
                self.chat_record_text.insert(END, '[' + emoji_name, msg_tag)
        # 文件
        else:
            file_name = msg_txt.split("/")[-1]
            flag = False
            if not os.path.exists(msg_txt):
                flag = True
            if not os.path.isfile(msg_txt):
                flag = True
            if flag:
                file_name = file_name + '[文件已被清理]'
            l = Label(self.chat_record_text, text=file_name, foreground='blue',
                      font=('黑体', 10, 'underline'))
            l.bind("<Button-1>", self.handler_adaptor(self.file_name_click, path=msg_txt))

            self.chat_record_text.window_create(END, window=l)
            suffix = msg_txt.split(".")[-1]
            img_type = ['jpg', 'png', 'gif']
            # 照片 预览显示
            if suffix in img_type and not flag:
                self.chat_record_text.insert(END, '\n')
                img_jpg = UtilsAndConfig.resize_image(False, msg_txt, 150, 150)
                self.img_files.append(img_jpg)
                self.chat_record_text.image_create(END, image=self.img_files[-1])

        if msg_json['type'] == 'get':
            self.chat_record_text.tag_add('msg_get', END)
            self.chat_record_text.tag_config('msg_get', foreground='#000', font=ft_msg)
        else:
            self.chat_record_text.tag_add('msg_send', END)
            self.chat_record_text.tag_config('msg_send', foreground='green', font=ft_msg)

        self.chat_record_text['state'] = DISABLED
        self.chat_msg_text.delete('0.0', END)
        self.chat_record_text.see(END)

    def handler_adaptor(self, func, **kwd):
        return lambda event, fun=func, kwds=kwd: fun(event, **kwds)

    def file_name_click(self, event, path):
        if not os.path.exists(path):
            return
        if not os.path.isfile(path):
            return
        os.startfile(path)

    def get_new_msg(self):
        msg = UtilsAndConfig.get_one_chat_record(self.is_friend, self.uid, self.to_id)
        self.add_line(msg)

    # 发送消息
    def send_msg(self):
        msg_text = self.chat_msg_text.get('0.0', END).strip()
        if len(msg_text) > 0:
            send_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.home_view.chat_send_msg(self.is_friend, self.to_id, send_date, msg_text)

    def send_msg_event(self, event):
        self.send_msg()

    def sending_file(self, flag):
        if flag is False:
            self.label_sending_file.place_forget()
            self.button_send['state'] = NORMAL
        else:
            self.label_sending_file.place(x=252, y=8)
            self.button_send['state'] = DISABLED