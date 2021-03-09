# -*- coding: utf-8 -*-
import datetime

import motor.motor_tornado

import src.ib_settings as _ib

db = motor.motor_tornado.MotorClient('localhost', 27017)['imageboard']

async def log(message_type, message):
    message_types = ['post', 'post_remove', 'board_creation', 'board_edit', 'board_remove', 'ban', 'unban', 'other',]
    if message_type not in message_types:
        message_type = 'other'
    data = {
        'time': datetime.datetime.utcnow(),
        'type': message_type,
        'message': message,
    }
    await db.log.insert_one(data)

