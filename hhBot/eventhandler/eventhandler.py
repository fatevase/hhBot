from ..common import common, hd2
from ..conf import command, model
from ..conf import config as conf

new_dispatches_cid = conf.config['cid']['new_dispatches']
new_steamupdate_cid = conf.config['cid']['new_steamupdate']

def on_use_bot_command(data):
    meta = {}
    if not isinstance(data, dict):
        print(f"got error for data:{data}")
        return
    meta = model.UseCommandData(**data)
    if meta and meta.command_info:
        command_id = meta.command_info.id
        if command_id == new_dispatches_cid:
            on_repdispatch(meta)
        elif command_id == new_steamupdate_cid:
            on_repsteamupdate(meta)

def on_repsteamupdate(meta):
    if meta.command_info.options is None:
        req = model.ChannelImSendReq(
            msg=hd2.get_new_steam_data(),
            msg_type=model.MSG_TYPE_MDTEXT,
            channel_id=meta.channel_base_info.channel_id,
            room_id=meta.room_base_info.room_id,
        )
        common.SendMessage(req)
        try:
            hd2.fetch_and_update_steam_data()
        except Exception as e:
            print(e)
    elif len(meta.command_info.options) == 1:
        option = meta.command_info.options[0]
        if option.type == command.TYPE_STRING:
            req = model.ChannelImSendReq(
                msg=option.value,
                msg_type=model.MSG_TYPE_MDTEXT,
                channel_id=meta.channel_base_info.channel_id,
                room_id=meta.room_base_info.room_id,
            )
            common.SendMessage(req)

def on_repdispatch(meta):
    if meta.command_info.options is None:
        print("new",hd2.get_new_dispatches())
        req = model.ChannelImSendReq(
            msg=hd2.get_new_dispatches(),
            msg_type=model.MSG_TYPE_MDTEXT,
            channel_id=meta.channel_base_info.channel_id,
            room_id=meta.room_base_info.room_id,
        )
        common.SendMessage(req)
        try:
            hd2.fetch_and_update_dispatches()
        except Exception as e:
            print(e)
        
    elif len(meta.command_info.options) == 1:
        option = meta.command_info.options[0]
        if option.type == command.TYPE_STRING:
            req = model.ChannelImSendReq(
                msg=option.value,
                msg_type=model.MSG_TYPE_MDTEXT,
                channel_id=meta.channel_base_info.channel_id,
                room_id=meta.room_base_info.room_id,
            )
            common.SendMessage(req)


class EventHandler:
    async def on_message(self, data):
        message_type = data["type"]
        message_data = data["data"]
        if message_type == model.MSG_TYPE_USECOMMAND:
            on_use_bot_command(message_data)
