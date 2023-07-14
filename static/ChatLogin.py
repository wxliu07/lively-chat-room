import tkinter.messagebox
import tkinter.filedialog
import json
import socket
import requests
import ChatHome
import UtilsAndConfig
from tkinter import *
from UtilsAndConfig import ServerConfig

# 定义配置
serverConfig = ServerConfig()
SERVER_ADDRESS = serverConfig.HTTP_SERVER_ADDRESS

# 登录窗口
root = Tk()
root.title('登录')
root.geometry('500x300+600+300')
root.minsize(500, 300)
root.maxsize(500, 300)
root.configure(bg='#E1EFF5')
# 父frame
frame_login = Frame(root, relief=RAISED, borderwidth=0, width=300, height=200)
frame_login.place(x=100, y=40)
label = Label(frame_login, text="Login", bg='#E1EFF5', font=('Times New Roman', 19, 'bold'), relief=RAISED, width=300, height=50, )
label.place(x=170, y=10, anchor=CENTER)

frame_parent = Frame(root, bg='#E1EFF5', relief=RAISED, borderwidth=0, width=300, height=200)
frame_parent.place(x=100, y=80)

# 回车键有效
flag_enter_enable = True


def login():
    login_name = var_login_name.get()
    pwd = var_pwd.get()
    global flag_enter_enable

    if not UtilsAndConfig.check_login_name(login_name):
        flag_enter_enable = False
        tkinter.messagebox.showwarning('提示', '请检查登录名!')
        flag_enter_enable = True
        return
    if pwd == '' or len(pwd) == 0:
        flag_enter_enable = False
        tkinter.messagebox.showwarning('提示', '请输入密码!')
        flag_enter_enable = True
        return

    # 此处开始进行登录
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.connect((serverConfig.SERVER_IP, serverConfig.SOCKET_PORT))

    # 发送登录消息
    send_data = {'type': UtilsAndConfig.USER_LOGIN, 'login_name': login_name, "pwd": pwd}
    my_socket.send(json.dumps(send_data).encode())

    # 接收服务器结果
    socket_result = my_socket.recv(1024).decode()
    msg = json.loads(socket_result)

    if msg['type'] == UtilsAndConfig.USER_LOGIN_SUCCESS:
        root.destroy()
        ChatHome.ChatHome(msg['uid'], my_socket)    # 登陆后就可以创建ChatHome对象
    if msg['type'] == UtilsAndConfig.USER_LOGIN_FAILED:
        flag_enter_enable = False
        tkinter.messagebox.showwarning('提示', "账号不存在或密码错误")
        my_socket.close()
        flag_enter_enable = True


def do_something(event):
    if flag_enter_enable:
        login()


# 账号frame
frame_uid = Frame(frame_parent,  bg='#E1EFF5', relief=RAISED, borderwidth=0, width=300, height=40)
frame_uid.place(x=0, y=10)
label_uid = Label(frame_uid,bg='#E1EFF5', text='用户名： ')
label_uid.place(x=30, y=10)
var_login_name = StringVar()
entry_uid = Entry(frame_uid, show=None, textvariable=var_login_name, width=25)
entry_uid.place(x=90, y=10)
entry_uid.focus_set()
entry_uid.bind('<KeyRelease-Return>', do_something)

# 密码frame
frame_pwd = Frame(frame_parent, bg='#E1EFF5',  relief=RAISED, borderwidth=0, width=300, height=40)
frame_pwd.place(x=0, y=50)
label_pwd = Label(frame_pwd, bg='#E1EFF5',text='密   码：')
label_pwd.place(x=30, y=10)
var_pwd = StringVar()
entry_pwd = Entry(frame_pwd, show='*', textvariable=var_pwd, width=25)
entry_pwd.place(x=90, y=10)
entry_pwd.bind('<KeyRelease-Return>', do_something)


# 注册窗口关闭时，重新启用主窗口
def window_register_close_handler():
    root.attributes("-disabled", 0)
    window_register.destroy()


# 注册函数
def register():
    var_register_pic_path.set('')
    var_register_login_name.set('')
    var_register_username.set('')
    var_register_sex_val.set(1)
    var_register_pwd1.set('')
    var_register_pwd2.set('')

    # 选择头像图片函数
    def show_openfile_dialog():
        file_types = [('头像图片', '*.jpg')]
        file_path = tkinter.filedialog.askopenfilename(title=u'选择文件', filetypes=file_types)
        var_register_pic_path.set(file_path)

    # 检查登录名是否唯一
    def check_login_name():
        if UtilsAndConfig.check_login_name(var_register_login_name.get()):
            url = SERVER_ADDRESS + '/checkLoginName?name=' + var_register_login_name.get()
            request = requests.get(url)
            result = json.loads(request.text)
            if result['code'] == 200:
                tkinter.messagebox.showwarning('提示', '登录名可用!')
            else:
                tkinter.messagebox.showwarning('提示', result['message'])
        else:
            tkinter.messagebox.showwarning('提示', '请检查登录名!')
            return

    # 注册按钮函数
    def button_register_click_fun():
        # 用户信息
        pic_path = var_register_pic_path.get()
        login_name = var_register_login_name.get()
        name = var_register_username.get()
        sex = var_register_sex_val.get()
        pwd1 = var_register_pwd1.get()
        pwd2 = var_register_pwd2.get()

        if pic_path == '' or len(pic_path) == 0:
            tkinter.messagebox.showwarning('提示', '请选择头像!')
            return

        if name == '' or len(name) == 0:
            tkinter.messagebox.showwarning('提示', '昵称不能为空!')
            return

        if not UtilsAndConfig.check_login_name(login_name):
            tkinter.messagebox.showwarning('提示', '请检查登录名!')
            return
        if len(name) > 6:
            tkinter.messagebox.showwarning('提示', '昵称长度不能大于6!')
            return

        if pwd1 == '' or len(pwd1) == 0:
            tkinter.messagebox.showwarning('提示', '请输入密码!')
            return
        if pwd2 == '' or len(pwd2) == 0:
            tkinter.messagebox.showwarning('提示', '请输入重复密码!')
            return
        if pwd1 != pwd2:
            tkinter.messagebox.showwarning('提示', '密码不一致!')
            return

        url = SERVER_ADDRESS + '/register'
        files = {'file': open(pic_path, 'rb')}
        params = {
            'loginName': login_name,
            'name': name,
            'sex': sex,
            'pwd1': pwd1,
            'pwd2': pwd2
        }
        button_register_click['state'] = DISABLED
        r = requests.post(url, data=params, files=files)
        button_register_click['state'] = NORMAL
        result = json.loads(r.text)
        if result['code'] == 200:
            window_register.destroy()
            root.attributes("-disabled", 0)
            tkinter.messagebox.showwarning('提示', '注册成功，请登录!')
            return
        else:
            tkinter.messagebox.showwarning('提示', result['message'])

    global window_register
    window_register = Toplevel(root)
    window_register.geometry('600x400+600+400')
    window_register.title('注册账号')
    window_register.transient(root)
    window_register.configure(bg='#C6E4E8')
    # 头像
    frame_register_head = Frame(window_register, bg='#C6E4E8',relief=RAISED, borderwidth=0, width=600, height=40)
    frame_register_head.place(x=0, y=50)
    label_register_head = Label(frame_register_head, bg='#C6E4E8',text='头   像：')
    label_register_head.place(x=150, y=8)
    entry_pic_path = Entry(frame_register_head, bg='#C6E4E8',width=25, textvariable=var_register_pic_path, state='disabled')
    entry_pic_path.place(x=210, y=8)
    button_head = Button(frame_register_head, bg='#ABDAD9', text='选择您的头像', command=show_openfile_dialog)
    button_head.place(x=460, y=5)

    # 登录名（唯一）
    frame_register_login_name = Frame(window_register, bg='#C6E4E8',relief=RAISED, borderwidth=0, width=600, height=55)
    frame_register_login_name.place(x=0, y=90)
    label_register_login_name = Label(frame_register_login_name,bg='#C6E4E8', text='登录名：')
    label_register_login_name.place(x=150, y=8)
    entry_login_name = Entry(frame_register_login_name, show=None, textvariable=var_register_login_name, width=25)
    entry_login_name.place(x=210, y=8)
    button_check_login_name = Button(frame_register_login_name, bg='#ABDAD9',text='检查是否重复', command=check_login_name)
    button_check_login_name.place(x=460, y=5)
    # label_login_name_tip = Label(frame_register_login_name, fg='red', text='字母开头的5-15位字母+数字的组合')
    # label_login_name_tip.place(x=210, y=30)

    # 昵称
    frame_register_username = Frame(window_register, bg='#C6E4E8',relief=RAISED, borderwidth=0, width=600, height=40)
    frame_register_username.place(x=0, y=145)
    label_register_username = Label(frame_register_username,bg='#C6E4E8', text='昵   称：')
    label_register_username.place(x=150, y=8)
    entry_username = Entry(frame_register_username, show=None, textvariable=var_register_username, width=25)
    entry_username.place(x=210, y=8)

    # 性别
    frame_register_sex = Frame(window_register, bg='#C6E4E8',relief=RAISED, borderwidth=0, width=600, height=40)
    frame_register_sex.place(x=0, y=185)
    label_register_sex = Label(frame_register_sex,bg='#C6E4E8', text='性   别：')
    label_register_sex.place(x=150, y=8)
    var_register_sex_val.set('1')
    radiobutton_sex1 = Radiobutton(frame_register_sex, bg='#C6E4E8',text='男',
                                   variable=var_register_sex_val, value='1')
    radiobutton_sex1.place(x=210, y=8)
    radiobutton_sex2 = Radiobutton(frame_register_sex, bg='#C6E4E8',text='女',
                                   variable=var_register_sex_val, value='0')
    radiobutton_sex2.place(x=260, y=8)

    # 密码
    frame_register_password1 = Frame(window_register, bg='#C6E4E8',relief=RAISED, borderwidth=0, width=600, height=40)
    frame_register_password1.place(x=0, y=225)
    label_register_password1 = Label(frame_register_password1, bg='#C6E4E8',text='密   码：')
    label_register_password1.place(x=150, y=8)
    entry_password1 = Entry(frame_register_password1, show='*', textvariable=var_register_pwd1, width=25)
    entry_password1.place(x=210, y=8)

    frame_register_password2 = Frame(window_register,bg='#C6E4E8', relief=RAISED, borderwidth=0, width=600, height=40)
    frame_register_password2.place(x=0, y=265)
    label_register_password2 = Label(frame_register_password2,bg='#C6E4E8', text='重复密码：')
    label_register_password2.place(x=140, y=8)
    entry_password2 = Entry(frame_register_password2, show='*', textvariable=var_register_pwd2, width=25)
    entry_password2.place(x=210, y=8)

    # 按钮
    frame_register_button = Frame(window_register,bg='#C6E4E8', relief=RAISED, borderwidth=0, width=600, height=40)
    frame_register_button.place(x=0, y=305)
    button_register_click = Button(frame_register_button, bg='#ABDAD9',width=20, text='注 册', command=button_register_click_fun)
    button_register_click.place(x=230, y=5)

    # 打开时禁用主窗口 关闭时启用主窗口
    root.attributes("-disabled", 1)
    window_register.protocol("WM_DELETE_WINDOW", window_register_close_handler)


# 按钮frame
var_register_pic_path = StringVar()
var_register_login_name = StringVar()
var_register_username = StringVar()
var_register_sex_val = StringVar()
var_register_pwd1 = StringVar()
var_register_pwd2 = StringVar()
frame_button = Frame(frame_parent, bg='#E1EFF5', relief=SOLID, borderwidth=0, width=300, height=40)
frame_button.place(x=0, y=100)
button_login = Button(frame_button,bg='#E1EFF5',  width=12, text='登 录', command=login)
button_login.place(x=30, y=5)
button_register = Button(frame_button, bg='#E1EFF5', width=12, text='注 册', command=register)
button_register.place(x=170, y=5)


root.mainloop()
