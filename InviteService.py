#coding=utf-8
#-*- encoding: utf-8 -*-

from datetime import datetime, timedelta
from MySQL import MySQL
from random import randint

import Config
import Utils
import UserService

__create_table_script = """
CREATE TABLE IF NOT EXISTS `invite` (
  `id` char(32) COLLATE utf8_bin NOT NULL,
  `user_id` char(32) COLLATE utf8_bin NOT NULL,
  `type` varchar(20) COLLATE utf8_bin NOT NULL,
  `info` text COLLATE utf8_bin,
  `invite_date` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `deal_date` timestamp NULL DEFAULT NULL,
  `is_deal` tinyint(1) DEFAULT NULL,
  `deal_user_id` char(32) COLLATE utf8_bin DEFAULT NULL,
  `is_pocket` tinyint(1) DEFAULT NULL,
  `pocket_date` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`,`type`),
  KEY `deal_user_id` (`deal_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
"""

