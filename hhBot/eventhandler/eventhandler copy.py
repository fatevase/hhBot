from ..common import common, hd2
from ..conf import command, model
from ..conf import config as conf

new_dispatches_cid = conf.config['cid']['new_dispatches']
new_steamupdate_cid = conf.config['cid']['new_steamupdate']
new_assignments_cid = conf.config['cid']['new_assignments']

def handle_command(meta, get_data_func, msg_type, *args, **kwargs):
    channel_id = meta.channel_base_info.channel_id
    room_id = meta.room_base_info.room_id

    if meta.command_info.options is None:
        data = get_data_func(*args, **kwargs)
        common.SendMessage(data, msg_type, channel_id, room_id)
    elif len(meta.command_info.options) == 1:
        option = meta.command_info.options[0]
        if option.type != command.TYPE_STRING:
            return
        common.SendMessage(option.value, msg_type, channel_id, room_id)

def on_use_bot_command(data):
    meta = {}
    if not isinstance(data, dict):
        print(f"got error for data:{data}")
        return
    meta = model.UseCommandData(**data)
    if meta and meta.command_info:
        command_id = meta.command_info.id
        if command_id == new_dispatches_cid:
            handle_command(meta, hd2.get_new_dispatches, model.MSG_TYPE_MDTEXT)
        elif command_id == new_steamupdate_cid:
            handle_command(meta, hd2.get_new_steam_data, model.MSG_TYPE_MDTEXT)
        elif command_id == new_assignments_cid:
            handle_command(meta, hd2.get_new_assignments, model.MSG_TYPE_MDTEXT)

class EventHandler:
    async def on_message(self, data):
        message_type = data["type"]
        message_data = data["data"]
        if message_type == model.MSG_TYPE_USECOMMAND:
            on_use_bot_command(message_data)
