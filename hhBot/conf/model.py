from typing import Any, List, Optional

from pydantic import BaseModel

from ..conf.command import CommandInfo


class RoomBaseInfo(BaseModel):
    room_avatar: str
    room_id: str
    room_name: str


class AvatarDecoration(BaseModel):
    src_type: str
    src_url: str


class SenderInfo(BaseModel):
    avatar: str
    level: int
    nickname: str
    roles: Optional[List['str']]
    room_nickname: str
    user_id: int


class ChannelBaseInfo(BaseModel):
    channel_id: str
    channel_name: str
    channel_type: int


class UseCommandData(BaseModel):
    bot_id: int
    channel_base_info: ChannelBaseInfo
    command_info: CommandInfo
    msg: str
    msg_id: str
    room_base_info: RoomBaseInfo
    send_time: int
    sender_info: SenderInfo


MSG_TYPE_MDTEXT = 4
MSG_TYPE_USECOMMAND = "50"

MSG_TYPE_CARD = 20


class ChannelImSendReq(BaseModel):
    msg: str = ""
    msg_type: int = 0
    heychat_ack_id: str = ""
    reply_id: str = ""
    room_id: str = ""
    addition: str = ""
    at_user_id: str = ""
    at_role_id: str = ""
    mention_channel_id: str = ""
    channel_id: str = ""
    channel_type: int = 0
