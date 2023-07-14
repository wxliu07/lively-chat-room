from tkinter import *
import UtilsAndConfig


class FriendView(Frame):

    # 初始化朋友显示列表
    def __init__(self, master=None, process_wheel=None, home_view=None, friend=None):
        super().__init__(master)
        self.master = master
        self.process_wheel = process_wheel
        self.home_view = home_view
        self.friend = friend

        # 框架
        self.parent = None
        self.leftChild = None
        self.midChild = None
        self.rightChild = None

        # 头像
        self.img_open = None
        self.img_jpg = None
        self.label_img = None
        # 状态
        self.var_online_text = StringVar()
        self.var_online_color = StringVar()
        self.label_status = None
        # 昵称
        self.var_username = StringVar()
        self.label_name = None
        # 消息条数
        self.label_msg_count = None

        self.var_username.set(self.friend['user']['username'])

        self.var_msg_count_text = StringVar()
        self.var_msg_count_text.set('')

        self.new_msg_count = 0

        self.create_widget()

    def create_widget(self):
        self.parent = Frame(self.master, relief=RAISED, borderwidth=0, height=60, width=370)
        self.parent.place(x=0, y=0)

        self.leftChild = Frame(self.parent, relief=RAISED, width=52, height=52, bg='#cccccc')
        self.leftChild.place(x=15, y=3)

        self.midChild = Frame(self.parent, relief=RAISED, width=150, height=50)
        self.midChild.place(x=85, y=5)

        self.rightChild = Frame(self.parent, relief=RAISED, width=100, height=50)
        self.rightChild.place(x=230, y=5)

        # 头像

        # 网络图片
        self.img_jpg = UtilsAndConfig.resize_image(True, self.friend['user']['picUrl'], 50, 50)
        self.label_img = Label(self.leftChild, image=self.img_jpg)
        self.label_img.place(x=1, y=1)

        # 状态和昵称
        if self.friend['online'] == 1:
            self.var_online_text.set('[在线]')
            self.label_status = Label(self.midChild, textvariable=self.var_online_text, fg='green')
            self.label_status.place(x=1, y=28)
        else:
            self.var_online_text.set('[离线]')
            self.label_status = Label(self.midChild, textvariable=self.var_online_text, fg='#000000')
            self.label_status.place(x=1, y=28)

        self.label_name = Label(self.midChild, textvariable=self.var_username, font=('黑体', 11))
        self.label_name.place(x=1, y=1)

        # 新消息提醒
        self.label_msg_count = Label(self.rightChild, textvariable=self.var_msg_count_text, width=13, fg='red')
        self.label_msg_count.place(x=4, y=12)

        # 双击和滚动事件
        self.parent.bind('<Double-Button-1>', self.double_click)
        self.parent.bind('<MouseWheel>', self.process_wheel)
        self.label_img.bind('<Double-Button-1>', self.double_click)
        self.label_img.bind('<MouseWheel>', self.process_wheel)
        self.label_status.bind('<Double-Button-1>', self.double_click)
        self.label_status.bind('<MouseWheel>', self.process_wheel)
        self.label_name.bind('<Double-Button-1>', self.double_click)
        self.label_name.bind('<MouseWheel>', self.process_wheel)
        self.label_msg_count.bind('<Double-Button-1>', self.double_click)
        self.label_msg_count.bind('<MouseWheel>', self.process_wheel)
        self.midChild.bind('<Double-Button-1>', self.double_click)
        self.midChild.bind('<MouseWheel>', self.process_wheel)
        self.leftChild.bind('<Double-Button-1>', self.double_click)
        self.leftChild.bind('<MouseWheel>', self.process_wheel)
        self.rightChild.bind('<Double-Button-1>', self.double_click)
        self.rightChild.bind('<MouseWheel>', self.process_wheel)

    def double_click(self, event):
        self.home_view.open_chat_window(1, self.friend['user']['id'])

    # 显示离线和在线状态
    def online_type_change(self, online_type):
        if online_type == 1:
            self.var_online_text.set('[在线]')
            self.label_status['fg'] = 'green'
        else:
            self.var_online_text.set('[离线]')
            self.label_status['fg'] = '#000000'

    def set_msg_text(self, new_msg_count):
        if new_msg_count == 0:
            self.new_msg_count = 0
            self.var_msg_count_text.set('')
        else:
            tip = str(new_msg_count) + '消息'
            self.var_msg_count_text.set(tip)

    # 处理新消息
    def new_msg_comming(self):
        # 新消息条数控制
        self.new_msg_count += 1
        if self.new_msg_count > 99:
            self.new_msg_count = 99

        # 调用方法设置
        self.set_msg_text(self.new_msg_count)
