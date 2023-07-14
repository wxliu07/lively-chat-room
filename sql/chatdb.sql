CREATE DATABASE chatdb;
USE chatdb;

-- //用户
-- user(id, password, loginName, username, sex, picUrl, updateTime)
CREATE TABLE users(
	id int PRIMARY KEY AUTO_INCREMENT,
	pwd varchar(36) NOT NULL,
	loginName varchar(50) NOT NULL UNIQUE,
	username varchar(50) NOT NULL,
	sex int not null,
	picUrl varchar(200) not null,
	updateTime datetime not null
);

-- //好友
-- friends(id, uid, fridendId, updateTime)
CREATE TABLE friends(
	id int PRIMARY KEY AUTO_INCREMENT,
	uid int NOT NULL,
	friendId int NOT NULL,
	updateTime datetime not null,
	FOREIGN KEY (uid) REFERENCES users (id),
	FOREIGN KEY (friendId) REFERENCES users (id)
);

-- //群聊
-- groupChat(id, createUid, gName, updateTime)
CREATE TABLE groupChat(
	id int PRIMARY KEY AUTO_INCREMENT,
	createUid int not null,
	gname varchar(50) not null,
	updateTime datetime not null,
	FOREIGN KEY (createUid) REFERENCES users (id)
);


-- //成员
-- groupMembers(id, gId, uId, joinTime)
CREATE TABLE groupMembers(
	id int PRIMARY KEY AUTO_INCREMENT,
	gId int not null,
	uId int not null,
	joinTime datetime not null,
	FOREIGN KEY (gId) REFERENCES groupChat(id),
	FOREIGN KEY (uId) REFERENCES users(id)
);


-- //验证消息
-- //type: 1:添加好友  2:申请入群  3:邀请入群
-- //handle: 0:未处理 1:同意  2:拒绝
-- //gId：当type为2、3时有效
-- message(id, fromUid, toUid, type, gId, sendTime, handle, handleTime)
CREATE TABLE message(
	id int PRIMARY key auto_increment,
	fromUid int not null,
	toUid int not null,
	type int not null,
	gId int null null,
	handle int not null DEFAULT 0,
	sendTime datetime not null,
	handleTime datetime null,
	FOREIGN KEY (fromUid) REFERENCES users(id),
	FOREIGN KEY (toUid) REFERENCES users(id),
	FOREIGN KEY (gId) REFERENCES groupChat(id)
);