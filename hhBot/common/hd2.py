import json

import re
from ..conf import config as conf
import requests
from translate import Translator
import requests

from .common import is_english, translate_text

from pathlib import Path

hd2 = conf.config['helldivers2']


DISPATCHES_URL = hd2['DISPATCHES_URL']
STEAM_URL = hd2['STEAM_URL']
NEW_DISPATCHES_FILE = hd2['NEW_DISPATCHES_FILE']
HISTORY_DISPATCHES_FILE = hd2['HISTORY_DISPATCHES_FILE']

NEW_STEAM_DATA_FILE = hd2['NEW_STEAM_DATA_FILE']
HISTORY_STEAM_DATA_FILE = hd2['HISTORY_STEAM_DATA_FILE']


def format_dispatch_message(message):
    # 使用正则表达式替换<i=1>和<i=3>标签
    message = re.sub(r'<i=1>(.*?)</i>', r'  <span style="color:SkyBlue">**\1**</span>  ', message)
    message = re.sub(r'<i=3>(.*?)</i>', r'  <span style="color:SkyBlue">***\1***</span>  ', message)
    message = re.sub(r'\[list\]', '\n\n', message)
    message = re.sub(r'\[/list\]', '\n\n', message)
    message = re.sub(r'\[\*\]', '\n- ', message)
    # message = re.sub(r'\[\*\](.*?)\[/\*\]', r'- \1', message)
    # 为特定文字添加颜色
    message = re.sub('机器人', r'<span style="color:red">机器人</span>', message)
    message = re.sub('绝地潜兵', r'<span style="color:gold">绝地潜兵</span>', message)
    message = re.sub('超级地球', r'<span style="color:CornflowerBlue">超级地球</span>', message)
    message = message.replace('[', '<')
    message = message.replace(']', '>')
    # message = re.sub(r'<color=red>(.*?)</color>', r'<span style="color:red">\1</span>', message)
    return message

def fetch_and_update_dispatches():
    headers = {
        'Accept-Language': 'zh-CN'
    }

    response = requests.get(DISPATCHES_URL, headers=headers)
    response.raise_for_status()
    dispatches = response.json()

    if not dispatches:
        return

    latest_dispatch = max(dispatches, key=lambda x: x['id'])
    latest_dispatch['message'] = format_dispatch_message(latest_dispatch['message'])
    if Path(NEW_DISPATCHES_FILE).exists():
        with open(NEW_DISPATCHES_FILE, 'r') as f:
            current_dispatch = json.load(f)
            current_id = current_dispatch.get('id', 0)
    else:
        current_id = 0

    if latest_dispatch['id'] >= current_id:
        with open(NEW_DISPATCHES_FILE, 'w') as f:
            json.dump(latest_dispatch, f, indent=4, ensure_ascii=False)
        
        if Path(HISTORY_DISPATCHES_FILE).exists():
            with open(HISTORY_DISPATCHES_FILE, 'r') as f:
                history_dispatches = json.load(f)
        else:
            history_dispatches = []

        # 更新或添加到历史记录
        for i, dispatch in enumerate(history_dispatches):
            if dispatch['id'] == latest_dispatch['id']:
                history_dispatches[i] = latest_dispatch
                break
        else:
            history_dispatches.append(latest_dispatch)

        with open(HISTORY_DISPATCHES_FILE, 'w') as f:
            json.dump(history_dispatches, f, indent=4, ensure_ascii=False)

def get_new_dispatches():
    # 读取最新的 dispatch 数据
    if Path(NEW_DISPATCHES_FILE).exists():
        with open(NEW_DISPATCHES_FILE, 'r') as f:
            latest_dispatch = json.load(f)
            msg = latest_dispatch.get('message', "暂时未获取到最新指令，请稍后。")
            time = latest_dispatch.get('published', "")
            msg = time + ' | ' + msg
    else:
        msg = "暂时未获取到最新指令，请稍后。"
    print(msg)
    return msg


def preserve_tags_and_translate(original_text, dest_language='zh'):
    # 提取标签内和标签外的部分
    parts = re.split(r'(\[.*?\])', original_text)
    
    translated_text = []
    for part in parts:
        if re.match(r'\[.*?\]', part):
            # 如果是标签，直接添加到结果中
            translated_text.append(part)
        else:
            # 如果是需要翻译的部分，进行翻译并添加到结果中
            translated_text.append(translate_text(part, dest_language))
    
    return ''.join(translated_text)


def fetch_and_update_steam_data():
    headers = {
        'Accept-Language': 'zh-CN'
    }

    response = requests.get(STEAM_URL, headers=headers)
    response.raise_for_status()
    steam_data = response.json()

    if not steam_data:
        return

    latest_steam_data = max(steam_data, key=lambda x: x['id'])
    if is_english(latest_steam_data['content']):
        latest_steam_data['content'] = preserve_tags_and_translate(latest_steam_data['content'])
    latest_steam_data['content'] = format_dispatch_message(latest_steam_data['content'])
    if Path(NEW_STEAM_DATA_FILE).exists():
        with open(NEW_STEAM_DATA_FILE, 'r', encoding='utf-8') as f:
            current_steam_data = json.load(f)
            current_id = current_steam_data.get('id', 0)
    else:
        current_id = '0'

    if latest_steam_data['id'] >= current_id:
        with open(NEW_STEAM_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(latest_steam_data, f, ensure_ascii=False, indent=4)
        
        if Path(HISTORY_STEAM_DATA_FILE).exists():
            with open(HISTORY_STEAM_DATA_FILE, 'r', encoding='utf-8') as f:
                history_steam_data = json.load(f)
        else:
            history_steam_data = []

        # 更新或添加到历史记录
        for i, data in enumerate(history_steam_data):
            if data['id'] == latest_steam_data['id']:
                history_steam_data[i] = latest_steam_data
                break
        else:
            history_steam_data.append(latest_steam_data)

        with open(HISTORY_STEAM_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(history_steam_data, f, ensure_ascii=False, indent=4)

def get_new_steam_data():
    if Path(NEW_STEAM_DATA_FILE).exists():
        with open(NEW_STEAM_DATA_FILE, 'r', encoding='utf-8') as f:
            latest_steam_data = json.load(f)
            return latest_steam_data.get('content', "暂时未获取到最新Steam数据，请稍后。")
    return "暂时未获取到最新Steam数据，请稍后。"
