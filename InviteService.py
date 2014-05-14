#coding=utf-8
#-*- encoding: utf-8 -*-

from datetime import datetime, timedelta
from MySQL import MySQL
from random import randint

import Config
import Utils
import UserService


def invite_code(data):
    pass


def invite_code(data):
    """
    申请邀请码
    参数：
        UserKey[string] – 用户会话ID
        Type[string] - 邀请类型
        ReferId[string] - 引用对象ID
        Info[string] – 邀请信息
    返回值：
        Code[string] – 邀请码
    """
    pass


def invite_list(data):
    """
    我的邀请列表
    参数：
        UserKey[string] – 用户会话ID
        Type[string] - 邀请类型
    返回值：
        Type[string] - 邀请类型
        Results[Array] – 授权对象列表：
            Code[string] – 邀请码
            IsDeal[boolean] - 0-未接受/1-已经接受
            DealUserId[string] - 接受邀请用户ID
            InviteDate[date] – 邀请日期
            DealDate[date] – 接受邀请日期
            ReferId[string] - 引用对象ID
    """
    pass

def invite_pocket(data):
    """
    完成邀请处理
    参数：
        UserKey[string] – 用户会话ID
        Code[string] – 邀请码
    返回值：
        Code[string] – 邀请码
    """
    pass


def invite_info(data):
    """
    邀请信息
    参数：
        Code[string] – 邀请码
    返回值：
        Code[string] – 邀请码
        Type[string] - 邀请类型
        ReferId[string] - 引用对象ID
        InviterId[string] – 邀请者UserId
        Inviter[string] – 邀请者姓名
        InviteDate[date] – 邀请日期
        Info[string] – 邀请信息
    """
    pass


def invite_deal(data):
    """
    接受邀请
    参数：
        UserKey[string] – 用户会话ID
        Code[string] – 邀请码
    返回值：
        Code[string] – 邀请码
    """
    pass
