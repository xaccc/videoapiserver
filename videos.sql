-- phpMyAdmin SQL Dump
-- version 2.11.11.3
-- http://www.phpmyadmin.net
--
-- 主机: localhost
-- 生成日期: 2014 年 03 月 19 日 11:44
-- 服务器版本: 5.1.69
-- PHP 版本: 5.3.3

SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";

--
-- 数据库: `videos`
--

-- --------------------------------------------------------

--
-- 表的结构 `app`
--

DROP TABLE IF EXISTS `app`;
CREATE TABLE IF NOT EXISTS `app` (
  `id` char(32) COLLATE utf8_bin NOT NULL COMMENT '应用UUID',
  `app` varchar(32) COLLATE utf8_bin NOT NULL COMMENT '登录名',
  `password` char(32) COLLATE utf8_bin NOT NULL COMMENT '密码',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `app` (`app`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='接口应用';

-- --------------------------------------------------------

--
-- 表的结构 `session`
--

DROP TABLE IF EXISTS `session`;
CREATE TABLE IF NOT EXISTS `session` (
  `id` char(32) COLLATE utf8_bin NOT NULL COMMENT '登录会话ID',
  `user_id` char(32) COLLATE utf8_bin NOT NULL COMMENT '用户ID',
  `device` varchar(50) COLLATE utf8_bin NOT NULL COMMENT '登录设备名称',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登录时间',
  `valid_time` datetime NOT NULL COMMENT '过期时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `appid` (`user_id`,`device`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='用户会话';

-- --------------------------------------------------------

--
-- 表的结构 `share`
--

DROP TABLE IF EXISTS `share`;
CREATE TABLE IF NOT EXISTS `share` (
  `owner_id` char(32) COLLATE utf8_bin NOT NULL COMMENT '用户ID',
  `video_id` char(32) COLLATE utf8_bin NOT NULL COMMENT '视频ID',
  `to_user_id` char(32) COLLATE utf8_bin DEFAULT NULL COMMENT '分享用户ID',
  `to_mobile` varchar(20) COLLATE utf8_bin DEFAULT NULL COMMENT '分享手机号',
  `to_name` varchar(30) COLLATE utf8_bin DEFAULT NULL COMMENT '分享对象姓名',
  `to_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '分享时间',
  KEY `video_id` (`video_id`),
  KEY `user_id` (`to_mobile`),
  KEY `owner_id` (`owner_id`),
  KEY `user_id_2` (`to_mobile`,`to_time`),
  KEY `owner_id_2` (`owner_id`,`to_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='分享记录';

-- --------------------------------------------------------

--
-- 表的结构 `upload`
--

DROP TABLE IF EXISTS `upload`;
CREATE TABLE IF NOT EXISTS `upload` (
  `id` char(32) COLLATE utf8_bin NOT NULL COMMENT '上床会话ID',
  `owner_id` char(32) COLLATE utf8_bin NOT NULL COMMENT '所有者ID',
  `length` bigint(20) NOT NULL COMMENT '文件字节数',
  `saved` bigint(20) NOT NULL COMMENT '上传字节数',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` timestamp NULL DEFAULT NULL COMMENT '最后上传时间',
  PRIMARY KEY (`id`),
  KEY `owner_id` (`owner_id`),
  KEY `create_time` (`create_time`),
  KEY `update_time` (`update_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='上传会话';

-- --------------------------------------------------------

--
-- 表的结构 `user`
--

DROP TABLE IF EXISTS `user`;
CREATE TABLE IF NOT EXISTS `user` (
  `id` char(32) COLLATE utf8_bin NOT NULL COMMENT '用户UUID',
  `mobile` varchar(20) COLLATE utf8_bin NOT NULL COMMENT '绑定的手机号',
  `password` char(32) COLLATE utf8_bin DEFAULT NULL COMMENT '登录密码',
  `name` varchar(20) COLLATE utf8_bin DEFAULT NULL COMMENT '姓名',
  `email` varchar(50) COLLATE utf8_bin DEFAULT NULL COMMENT '绑定邮箱',
  `login` varchar(20) COLLATE utf8_bin DEFAULT NULL COMMENT '登录名',
  PRIMARY KEY (`id`),
  UNIQUE KEY `mobile` (`mobile`),
  UNIQUE KEY `login` (`login`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='用户';

-- --------------------------------------------------------

--
-- 表的结构 `validate`
--

DROP TABLE IF EXISTS `validate`;
CREATE TABLE IF NOT EXISTS `validate` (
  `mobile` varchar(20) COLLATE utf8_bin NOT NULL COMMENT '手机号码',
  `code` varchar(20) COLLATE utf8_bin NOT NULL COMMENT '验证码',
  `device` varchar(50) COLLATE utf8_bin DEFAULT NULL COMMENT '设备名称',
  `valid_date` datetime NOT NULL COMMENT '验证码有效期',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  KEY `user_id` (`mobile`,`device`),
  KEY `create_time` (`create_time`),
  KEY `user_id_2` (`mobile`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='验证信息';

-- --------------------------------------------------------

--
-- 表的结构 `video`
--

DROP TABLE IF EXISTS `video`;
CREATE TABLE IF NOT EXISTS `video` (
  `id` char(32) COLLATE utf8_bin NOT NULL COMMENT '视频ID',
  `upload_id` char(32) COLLATE utf8_bin NOT NULL COMMENT '上传任务ID',
  `owner_id` char(32) COLLATE utf8_bin NOT NULL COMMENT '所有者ID',
  `title` varchar(250) COLLATE utf8_bin DEFAULT NULL COMMENT '标题',
  `author` varchar(20) COLLATE utf8_bin DEFAULT NULL COMMENT '作者',
  `create_date` datetime DEFAULT NULL COMMENT '创作日期',
  `category` varchar(50) COLLATE utf8_bin DEFAULT NULL COMMENT '分类/频道',
  `describe` text COLLATE utf8_bin COMMENT '描述',
  `duration` float DEFAULT NULL COMMENT '视频播放长度',
  `video_width` int(11) DEFAULT NULL COMMENT '原始视频宽',
  `video_height` int(11) DEFAULT NULL COMMENT '原始视频高',
  `video_bitrate` int(11) DEFAULT NULL COMMENT '原始视频码率',
  `upload_progress` int(11) DEFAULT NULL COMMENT '上传进度(保留)',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin COMMENT='视频';

-- --------------------------------------------------------

--
-- 表的结构 `video_poster`
--

DROP TABLE IF EXISTS `video_poster`;
CREATE TABLE IF NOT EXISTS `video_poster` (
  `video_id` char(32) NOT NULL COMMENT '视频ID',
  `duration` float NOT NULL COMMENT '截图时间点',
  `fileName` varchar(250) NOT NULL COMMENT '截图文件名',
  KEY `video_id` (`video_id`),
  KEY `duration` (`duration`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='视频截图';

-- --------------------------------------------------------

--
-- 表的结构 `video_transcode`
--

DROP TABLE IF EXISTS `video_transcode`;
CREATE TABLE IF NOT EXISTS `video_transcode` (
  `video_id` char(32) NOT NULL COMMENT '视频ID',
  `duration` float DEFAULT NULL COMMENT '视频时长',
  `file_name` varchar(250) NOT NULL COMMENT '视频文件名',
  `video_width` int(11) DEFAULT NULL,
  `video_height` int(11) DEFAULT NULL,
  `video_bitrate` int(11) DEFAULT NULL,
  `video_codec` varchar(20) DEFAULT NULL,
  `audio_channels` int(11) DEFAULT NULL,
  `audio_bitrate` int(11) DEFAULT NULL,
  `audio_codec` varchar(20) DEFAULT NULL,
  `transcoder` varchar(50) DEFAULT NULL COMMENT '转码器',
  `ready` int(11) NOT NULL DEFAULT '0' COMMENT '是否转码完成',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `assign_time` timestamp NULL DEFAULT NULL COMMENT '转码器分配时间',
  `finish_time` timestamp NULL DEFAULT NULL COMMENT '转码完成时间',
  KEY `video_id` (`video_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='视频转码格式';

-- --------------------------------------------------------

--
-- Stand-in structure for view `video_view`
--
DROP VIEW IF EXISTS `video_view`;
CREATE TABLE IF NOT EXISTS `video_view` (
`id` char(32)
,`upload_id` char(32)
,`owner_id` char(32)
,`title` varchar(250)
,`author` varchar(20)
,`create_date` datetime
,`category` varchar(50)
,`describe` text
,`duration` float
,`video_width` int(11)
,`video_height` int(11)
,`video_bitrate` int(11)
,`upload_progress` int(11)
,`create_time` timestamp
,`length` bigint(20)
);
-- --------------------------------------------------------

--
-- Structure for view `video_view`
--
DROP TABLE IF EXISTS `video_view`;

CREATE VIEW `video_view` AS 
select `a`.`id` AS `id`,`a`.`upload_id` AS `upload_id`,`a`.`owner_id` AS `owner_id`,`a`.`title` AS `title`,`a`.`author` AS `author`,`a`.`create_date` AS `create_date`,`a`.`category` AS `category`,`a`.`describe` AS `describe`,`a`.`duration` AS `duration`,`a`.`video_width` AS `video_width`,`a`.`video_height` AS `video_height`,`a`.`video_bitrate` AS `video_bitrate`,`a`.`upload_progress` AS `upload_progress`,`a`.`create_time` AS `create_time`,`b`.`length` AS `length` from (`video` `a` left join `upload` `b` on((`a`.`upload_id` = `b`.`id`))) order by `a`.`create_time` desc;
