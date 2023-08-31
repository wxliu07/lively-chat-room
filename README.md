# Lively-Chat-Room

## 总体介绍

在线聊天室, 合工大2020级小学期项目

主要技术：Socket 实现实时聊天和通知等双向性的功能，HTTP 实现登录注册等单向性的功能

## 开发环境与工具

- **开发环境:**  Windows10 + Python3.8 + MySQL8.0.26
- **开发工具:**  PyCharm Community Edition 2021.3.1

## 实现功能

- 基本的聊天功能: **离线消息、私聊功能、群聊功能**

- 基本的好友管理、个人信息管理功能: **添加好友**
- 基本的表情、文件和图片发送功能: **缓存式发送**
- QQ一体化风格的聊天界面: **聊天界面样式**
- 简单的安全处理:  **DES实现消息加密** 

<img src="README.assets/image-20230831105211180.png" alt="image-20230831105211180" style="zoom:67%;" />

<center>图 1 : 项目整体功能
</center>



## 项目亮点

- **架构清晰**, **封装完备**, **全面向对象**, **可维护性强**
- **用户界面友好**, **聊天体验优秀**

## UI展示

### 注册和登录界面

<img src="README.assets/image-20230831111217420.png" alt="image-20230831111217420" style="zoom:67%;" />

<center>登录界面

<img src="README.assets/image-20230831111303347.png" alt="image-20230831111303347" style="zoom:67%;" />

<center>注册界面

### 个人主界面

<img src="README.assets/image-20230831111340662.png" alt="image-20230831111340662" style="zoom:67%;" />

<center>个人主界面

### 聊天界面

#### 添加好友

<img src="README.assets/image-20230831111423680.png" alt="image-20230831111423680" style="zoom:67%;" />

<center>添加好友

#### 好友聊天

<img src="README.assets/image-20230831111458277.png" alt="image-20230831111458277" style="zoom:67%;" />



#### 群友聊天

<img src="README.assets/image-20230831111524301.png" alt="image-20230831111524301" style="zoom:67%;" />

<center>群友聊天

#### 收发文件

<img src="README.assets/image-20230831111554898.png" alt="image-20230831111554898" style="zoom:67%;" />

<center>文件管理



## 设计原理

### 基于TCP通信

由于TCP的可靠性，面向连接特点，在本例中，客户端与服务器之间的通信是基于TCP协议的。服务器可以通过TCP套接字实时掌握与客户端之间的通信情况。

### 收发并行

为了客户端界面不会因为接收信息而遭到阻塞无法操作，另外开辟了子线程来接收消息。有些如IO这些比较耗时间的操作，会另外开辟新线程来处理。



### 消息

通过固定格式的消息实现客户端与服务端之间的通信。

在本例中，服务器主要是发挥了中间站转发作用，通过消息中的接收者来进行消息的转发。

服务器通过消息类型和消息内容来进行进一步的消息处理，是转发还是返回响应内容。

<img src="README.assets/image-20230831110557925.png" alt="image-20230831110557925" style="zoom:67%;" />

<center>消息内容

<img src="README.assets/image-20230831110635100.png" alt="image-20230831110635100" style="zoom:67%;" />

<center>消息类别

### 消息加密

​		在本学期中学习了信息安全技术, 了解到了其中相关的概念和通信加密技术。因此在本次课程设计中我也考虑到了如何实现高效、安全的文件传输，并保护通信过程中的数据安全性。

​		在这一部分中, 我采用DES加密算法对数据进行加密，保护通信过程中的数据安全。在实现DES的过程中也对这个加密方法有了更深入的了解。

​		**DES 是分组长度为64 位的分组密码算法，密钥长度也是64位，其中每8位有一个奇偶校验位 ，因此有效密钥长度为56位。**DES 算法公开，安全性依赖密钥的保密程度。

​		其中DES加密算法可以归纳为三个关键步骤：1. 两次初始置换(初始置换和初始逆置换); 2. 子密钥控制下的十六轮迭代加密(也称为乘积变换); 3. 十六轮子密钥生成; 其中S盒是DES加密算法中唯一的非线性操作，也是DES具有较高安全性的关键所在。以下是DES加密算法的流程图: 

​		大致思路是在消息发送的时候由服务器约定通信双方密钥, 在发送方发送数据前对数据进行加密, 服务器转发消息后对消息进行解密再展示到客户端上。

<img src="README.assets/image-20230831112251702.png" alt="image-20230831112251702" style="zoom:67%;" />

<center>DES加密流程
### 粘包

由于TCP面向字节流的特点，在本例中，可能会出现多条消息同时接收的情况。因此，为了防止消息内容中出现分割标志导致消息分割混乱, 可以通过特定字符作为分割标志来把多条消息分开；




### 接口设计

<center>通信接口定义表

| 接口名称              | 接口功能       | 请求方式 |
| --------------------- | -------------- | -------- |
| modifyUser            | 修改用户信息   | POST     |
| getGroupSize          | 获取群聊人数   | GET      |
| modifyGroupName       | 修改群聊名称   | GET      |
| getGnameByGid         | 获取群聊名称   | GET      |
| getUsernameByUid      | 获取用户姓名   | GET      |
| searchUserByLoginname | 搜索用户姓名   | GET      |
| checkLoginName        | 检测登录姓名   | GET      |
| register              | 用户登录       | GET      |
| createGroup           | 创建群聊       | GET      |
| removeMember          | 踢出群聊       | GET      |
| deleteGroup           | 删除群聊       | GET      |
| quitGroup             | 退出群聊       | GET      |
| getFriendsById        | 获取好友信息   | GET      |
| delete_friend         | 删除好友       | GET      |
| addFriendsOrGroup     | 添加好友       | GET      |
| canAddFriends         | 判断是否能添加 | GET      |
| messageHandle         | 处理消息       | GET      |
| getNoHandleMessages   | 获取未处理消息 | GET      |
| downloadFileSuccess   | 文件下载成功   | GET      |



### 数据库设计

<img src="README.assets/image-20230831111650275.png" alt="image-20230831111650275" style="zoom:67%;" />

<center>数据库基本表设计结果



### 流程图

<img src="README.assets/image-20230831112328233.png" alt="image-20230831112328233" style="zoom:77%;" />

<center>服务器端运行流程

<img src="README.assets/image-20230831112359500.png" alt="image-20230831112359500" style="zoom:67%;" />

<center>客户端运行流程



## 待改进方面

- 在测试大文件的时候,软件由于没有设计缓冲区会时长崩溃卡死; 并且未考虑文件传输过程中丢包问题,传输过程中的带宽和并发,以及大文件传输多线程优化问题,所以一个重要优化点就是这里;
- 没有涉及到HTTP端的cookie和session处理, 后面可能会针对这部分进行对应的处理进而确保客户端和服务器之间的通信的有效性; 同时界面部分和功能部分还有些bug没有来得及调整,比如消息传输后会被界面挡住等;
- 在实现双方加密通信时候没有考虑周期,尤其是文件传输的时候,未考虑文件传输过程中加密对于文件内容的影响,以及没有对文件传输是否会因为加密导致丢包问题进行测试,未涉及文件验证机制;



## 运行说明

### 检查环境版本

- **确保 python 版本为3.8 或 3.9, 并且确保 MySQL 版 本为8.0 .**

  若环境不是上述版本，请先安装。

  MySQL 8.0 的安装可参考此文章： https://blog.csdn.net/xy_best_/article/details/116698099 

- 安装python后，修改pip镜像与版本，防止库安装不成功

  1. 在cmd执行如下命令，修改pip镜像源（加快下载速度）：

     ```python
     pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
     ```

  2. 修改pip版本，防止一些库下载不成功：

     ```python
     python -m pip install pip==21.3.1
     ```

### 初始化数据库

执行chatdb.sql脚本，初始化数据库。

```mysql
source F:\multiplayer-chat-room\chatdb.sql
```

### 代码导入

此部分简单, 不过多赘述, 注意库的版本即可

导入后需要修改server.conf文件配置: 

```mysql
[server]

# 服务端的ip地址
SERVER_IP = 127.0.0.1

# Http服务的端口号
HTTP_PORT = 8000

# socket服务的端口号
SOCKET_PORT = 8001

# 数据库连接配置 下方root是账号，123是密码
SQLALCHEMY_DATABASE_URI = mysql://root:123@127.0.0.1:3306/chatdb
```

### 运行服务器

运行ChatServer.py文件。

**注意：每次运行都需要先运行此服务端。因为这是整个程序的服务端**

如果出现以下两行绿色的字体, 即运行正常

![image-20230831110417237](README.assets/image-20230831110417237.png)

然后同时运行多个ChatLogin.py，分别登录不同的用户即可进行聊天。

