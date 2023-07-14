from tkinter import *
import requests
import json
from UtilsAndConfig import ServerConfig

# 群聊框体显示
class GroupsView(Frame):
    def __init__(self, master=None, process_wheel=None, home_view=None, group=None):
        super().__init__(master)
        self.server_config = ServerConfig()
        self.master = master
        self.process_wheel = process_wheel
        self.group = group
        self.home_view = home_view

        self.parent = None
        self.new_msg_cout = None

        self.label_group_name = None

        self.var_msg_count_text = StringVar()
        self.var_msg_count_text.set('')

        self.new_msg_count = 0

        self.create_widget()

    def create_widget(self):
        self.parent = Frame(self.master, relief=RAISED, borderwidth=0, height=60, width=370)
        self.parent.place(x=0, y=0)

        url = self.server_config.HTTP_SERVER_ADDRESS + '/getGroupMemberCount?gId=' + str(self.group['id'])
        result = requests.get(url)
        result_json = json.loads(result.text)
        member_count_text = ''
        if result_json['code'] == 200:
            member_count_text = '【群】' + self.group['gname'] + '（共' + str(result_json['data']) + '人）'

        self.label_group_name = Label(self.parent, text=member_count_text,
                                      font=('黑体', 11, 'underline'), width=30, anchor='w')
        self.label_group_name.place(x=8, y=15)

        self.new_msg_cout = Label(self.parent, textvariable=self.var_msg_count_text, width=13, fg='red')
        self.new_msg_cout.place(x=230, y=15)

        self.parent.bind('<Double-Button-1>', self.double_click)
        self.parent.bind('<MouseWheel>', self.process_wheel)
        self.label_group_name.bind('<Double-Button-1>', self.double_click)
        self.label_group_name.bind('<MouseWheel>', self.process_wheel)
        self.new_msg_cout.bind('<Double-Button-1>', self.double_click)
        self.new_msg_cout.bind('<MouseWheel>', self.process_wheel)

    def double_click(self, event):
        self.home_view.open_chat_window(0, self.group['id'])

    def set_msg_text(self, new_msg_count):
        if new_msg_count == 0:
            self.new_msg_count = 0
            self.var_msg_count_text.set('')
        else:
            tip = str(new_msg_count) + '消息'
            self.var_msg_count_text.set(tip)

    def new_msg_comming(self):
        self.new_msg_count += 1
        self.set_msg_text(self.new_msg_count)