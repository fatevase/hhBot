import json

import re
from ..conf import config as conf
import requests
from translate import Translator
import requests
from datetime import datetime, timezone

from .common import is_english, translate_text, start_data_fetching_process

import multiprocessing
from pathlib import Path

hd2 = conf.config['helldivers2']


DISPATCHES_URL = hd2['DISPATCHES_URL']
STEAM_URL = hd2['STEAM_URL']
ASSIGNMENTS_URL = hd2['ASSIGNMENTS_URL']

NEW_DISPATCHES_FILE = hd2['NEW_DISPATCHES_FILE']
HISTORY_DISPATCHES_FILE = hd2['HISTORY_DISPATCHES_FILE']

NEW_STEAM_DATA_FILE = hd2['NEW_STEAM_DATA_FILE']
HISTORY_STEAM_DATA_FILE = hd2['HISTORY_STEAM_DATA_FILE']

NEW_ASSIGNMENTS_FILE = hd2['NEW_ASSIGNMENTS_FILE']
HISTORY_ASSIGNMENTS_FILE = hd2['HISTORY_ASSIGNMENTS_FILE']

def get_time_difference(future_time_str):
    future_time = datetime.strptime(future_time_str[:16], "%Y-%m-%dT%H:%M")
    future_time = future_time.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    delta = future_time - now

    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    return f"{days}天{hours}小时{minutes}分钟"


def format_dispatch_message(message):
    # 使用正则表达式替换 <i=1> 和 <i=3> 标签
    message = re.sub(r'<i=1>(.*?)</i>', r'  <span style="color:SkyBlue">**\1**</span>  ', message)
    message = re.sub(r'<i=3>(.*?)</i>', r'  <span style="color:SkyBlue">***\1***</span>  ', message)
    
    # 替换 [list] 和 [/list] 标签
    message = re.sub(r'\[list\]', '\n\n', message)
    message = re.sub(r'\[/list\]', '\n\n', message)
    
    # 替换 [*] 和 [/*] 标签
    message = re.sub(r'\[\*\]\n?', '\n- ', message)
    message = re.sub(r'\[/\*\]', '', message)
    
    # 替换 [u][/u] 标签
    message = re.sub(r'\[u\](.*?)\[/u\]', r'<span style="text-decoration:underline">\1</span>', message)
    
    # 为特定文字添加颜色
    message = re.sub('机器人', r'<span style="color:red">机器人</span>', message)
    message = re.sub('绝地潜兵', r'<span style="color:gold">绝地潜兵</span>', message)
    message = re.sub('超级地球', r'<span style="color:CornflowerBlue">超级地球</span>', message)
    
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
    return latest_dispatch

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
    zh_text = translate_text(original_text, dest_language)
    zh_text = zh_text.replace('列表]', 'list]')
    return zh_text
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
        return None

    # 按照最新日期获取最新的 Steam 数据
    #latest_steam_data = max(steam_data, key=lambda x: datetime.strptime(x['date'], "%Y-%m-%dT%H:%M:%SZ"))
    latest_steam_data = steam_data[0]
    if Path(NEW_STEAM_DATA_FILE).exists():
        with open(NEW_STEAM_DATA_FILE, 'r', encoding='utf-8') as f:
            current_steam_data = json.load(f)
            cur_pubtime = current_steam_data.get('publishedAt', '2020-01-01T00:00:00Z')
    else:
        cur_pubtime = '2020-01-01T00:00:00Z'

    if latest_steam_data['publishedAt'] > cur_pubtime:
        if is_english(latest_steam_data['content']):
            latest_steam_data['content'] = preserve_tags_and_translate(latest_steam_data['content'])
        latest_steam_data['content'] = format_dispatch_message(latest_steam_data['content'])

        with open(NEW_STEAM_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(latest_steam_data, f, ensure_ascii=False, indent=4)
        
        if Path(HISTORY_STEAM_DATA_FILE).exists():
            with open(HISTORY_STEAM_DATA_FILE, 'r', encoding='utf-8') as f:
                history_steam_data = json.load(f)
        else:
            history_steam_data = []

        # 更新或添加到历史记录
        for i, data in enumerate(history_steam_data):
            if data['publishedAt'] == latest_steam_data['publishedAt']:
                history_steam_data[i] = latest_steam_data
                break
        else:
            history_steam_data.append(latest_steam_data)

        with open(HISTORY_STEAM_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(history_steam_data, f, ensure_ascii=False, indent=4)
    return latest_steam_data

def get_new_steam_data():
    if Path(NEW_STEAM_DATA_FILE).exists():
        with open(NEW_STEAM_DATA_FILE, 'r', encoding='utf-8') as f:
            latest_steam_data = json.load(f)
            content = latest_steam_data.get('content', "暂时未获取到最新Steam数据，请稍后。")
            content += f"| {latest_steam_data.get('publishedAt', "")}"
            return content
    return "暂时未获取到最新Steam数据，请稍后。"



def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)
    
def format_assignment(assignment):
    def get_reward_type(reward_type_id):
        reward_types = load_json('data/json/assignments/reward/type_zh.json')
        return reward_types.get(str(reward_type_id), "Unknown")

    def get_task_type(task_type_id):
        task_types = load_json('data/json/assignments/tasks/task/type_zh.json')
        return task_types.get(str(task_type_id), "Unknown")

    def get_task_value(task_value_id):
        task_values = load_json('data/json/assignments/tasks/task/values_zh.json')
        return task_values.get(str(task_value_id), "Unknown")

    def get_task_value_type(task_value_type_id):
        task_value_types = load_json('data/json/assignments/tasks/task/valueTypes_zh.json')
        return task_value_types.get(str(task_value_type_id), "Unknown")
    
    def get_plant_value_type(task_value_type_id):
        task_value_types = load_json('data/json/planets/planets.json')
        return task_value_types.get(str(task_value_type_id), "Unknown")

    time = assignment['expiration']
    title = f"[{assignment['title']}] {assignment['briefing']}"
    progress = assignment['progress']
    reward = {
        "type": get_reward_type(assignment['reward']['type']),
        "amount": assignment['reward']['amount']
    }
    targets = []
    for task in assignment['tasks']:
        task_value = [get_task_value_type(task['valueTypes'][1]), get_plant_value_type(task['values'][-1])['names']['zh-Hans']]
        target = {
            "type": get_task_type(task['type']),
            # "values": [get_task_value(value) for value in task['values']],
            "values": " ".join(task_value),
            # "valueTypes": [get_task_value_type(value_type) for value_type in task['valueTypes']]
        }
        targets.append(target)
    return {
        "id": assignment['id'],
        "time": time,
        "title": title,
        "reward": reward,
        "targets": targets,
        "progress": progress
    }

def fetch_and_update_assignments():
    headers = {
        'Accept-Language': 'zh-CN'
    }

    response = requests.get(ASSIGNMENTS_URL, headers=headers)
    response.raise_for_status()
    assignments = response.json()

    if not assignments:
        return

    latest_assignment = max(assignments, key=lambda x: x['id'])
    formatted_assignment = format_assignment(latest_assignment)
    if Path(NEW_ASSIGNMENTS_FILE).exists():
        with open(NEW_ASSIGNMENTS_FILE, 'r') as f:
            current_assignment = json.load(f)
            current_id = current_assignment.get('id', 0)
    else:
        current_id = 0

    if latest_assignment['id'] >= current_id:
        with open(NEW_ASSIGNMENTS_FILE, 'w') as f:
            json.dump(formatted_assignment, f, indent=4, ensure_ascii=False)
        
        if Path(HISTORY_ASSIGNMENTS_FILE).exists():
            with open(HISTORY_ASSIGNMENTS_FILE, 'r') as f:
                history_assignments = json.load(f)
        else:
            history_assignments = []

        # 更新或添加到历史记录
        for i, assignment in enumerate(history_assignments):
            if assignment['id'] == latest_assignment['id']:
                history_assignments[i] = formatted_assignment
                break
        else:
            history_assignments.append(formatted_assignment)

        with open(HISTORY_ASSIGNMENTS_FILE, 'w') as f:
            json.dump(history_assignments, f, indent=4, ensure_ascii=False)
    return formatted_assignment

def get_new_assignments():
    # 读取最新的 assignments 数据
    if Path(NEW_ASSIGNMENTS_FILE).exists():
        with open(NEW_ASSIGNMENTS_FILE, 'r') as f:
            latest_assignment = json.load(f)
            markdown = f"# {latest_assignment['title']}\n\n"
            markdown += f"**剩余时间**: {get_time_difference(latest_assignment['time'])}\n\n"
            
            # 格式化奖励
            reward = latest_assignment['reward']
            markdown += f"**奖励**: {reward['type']} - {reward['amount']}\n\n"
            
            # 格式化目标
            markdown += "## 目标\n"
            progress = latest_assignment['progress']
            for i, target in enumerate(latest_assignment['targets']):
                markdown += "- ✅ " if progress[i] else "- ❌"
                markdown += f" **{target['type']}**: \n"
                markdown += f" **{target['values']}**. \n"

            msg = markdown
    else:
        msg = "暂时未获取到最新全服任务列表，请稍后。"
    return msg
    

def start():
    events = [
        {
            'task': fetch_and_update_dispatches,
            'save': True
        },
        {
            'task': fetch_and_update_steam_data,
            'save': True
        },
        {
            'task': fetch_and_update_assignments,
            'save': True
        }
    ]
    p = multiprocessing.Process(target=start_data_fetching_process, args=(events,))
    p.start()