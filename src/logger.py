# -*- coding: utf-8 -*-
import datetime
from enum import Enum
from typing import Optional

import motor.motor_tornado


db = motor.motor_tornado.MotorClient('localhost', 27017)['imageboard']


class MessageTypes(Enum):
    POST = 'post'
    POST_REMOVAL = 'post_remove'
    BOARD_CREATE = 'board_creation'
    BOARD_EDIT = 'board_edit'
    BOARD_REMOVE = 'board_remove'
    BAN = 'ban'
    UNBAN = 'unban'
    OTHER = 'other'


async def log(message_type: Optional[MessageTypes], message: str):
    if not message_type:
        message_type = MessageTypes.OTHER
    data = {
        'time': datetime.datetime.utcnow(),
        'type': message_type.value,
        'message': message,
    }
    await db.log.insert_one(data)
