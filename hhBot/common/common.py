import json

import re
from ..conf import config as conf
import requests

import requests
from pathlib import Path
import time
import asyncio
import concurrent.futures
from ..conf import model

from .logger import logger
import functools

HEYCHAT_ACK_ID = 0
def is_english(text, thresh=0.5):
    # 计算文本中英文字符的比例
    english_chars = re.findall(r'[a-zA-Z]', text)
    total_chars = len(text)
    if total_chars == 0:
        return False
    english_ratio = len(english_chars) / total_chars
    return english_ratio > thresh

def translate_func(text, dest_lang='zh'):
    url = "https://aibit-translator.p.rapidapi.com/api/v1/translator/html"

    payload = {
        "from": "en",
        "to": dest_lang,
        "html": text
    }
    headers = {
        "x-rapidapi-key": "7560b0af85mshae09d0211beb496p166c68jsn945968a3524e",
        "x-rapidapi-host": "aibit-translator.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    return response.json()['trans']

def translate_text(text, dest_lang='zh'):
    try:
        translation = translate_func(text, dest_lang)
    except Exception as e:
        print("translate_text error:", e)
        translation = ""
    if translation == "":
        translation = text

    return translation



def split_message(msg, max_length):
    # 自定义消息拆分逻辑，确保不破坏数据内容
    parts = []
    while len(msg) > max_length:
        split_index = msg.rfind('\n', 0, max_length)
        if split_index == -1:
            split_index = msg.rfind(' ', 0, max_length)
            if split_index == -1:
                split_index = max_length
        parts.append(msg[:split_index])
        msg = msg[split_index:].lstrip()
    parts.append(msg)
    return parts

def SendMessage(msg, msg_type, channel_id, room_id):
    url = f"{conf.HTTP_HOST}{conf.SEND_MSG_URL}{conf.COMMON_PARAMS}"
    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'token': conf.HeyChatAPPToken,
    }

    # 假设消息长度限制为 1000 字符
    MAX_LENGTH = 3000
    MAX_RETRIES = 3

    # 将消息拆分成多段
    # messages = textwrap.wrap(msg, MAX_LENGTH)
    messages = split_message(msg, MAX_LENGTH)
    global HEYCHAT_ACK_ID
    for msg_part in messages:
        payload = model.ChannelImSendReq(
            msg=msg_part,
            msg_type=msg_type,
            channel_id=channel_id,
            room_id=room_id,
            heychat_ack_id=str(HEYCHAT_ACK_ID)
        )

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.request("POST", url, headers=headers, data=payload.model_dump_json())
                response.raise_for_status()  # 如果响应状态码不是 200，抛出 HTTPError
                content = response.content.decode('utf-8')
                HEYCHAT_ACK_ID += 1
                logger.info(f"发送成功: {content}")
                break  # 如果成功，跳出重试循环
            except requests.RequestException as e:
                logger.error(f"发送失败，重试 {attempt + 1}/{MAX_RETRIES} 次: {e}")

                time.sleep(2 ** attempt)  # 指数退避重试

# 假设 hd2.fetch_and_update_steam_data() 返回数据
async def fetch_data_periodically(executor, events):
    loop = asyncio.get_event_loop()
    while True:
        for event in events:
            task = event['task']
            args = event.get('args', [])
            kwargs = event.get('kwargs', {})
            try:
                partial_task = functools.partial(task, *args, **kwargs)
                # 增加超时机制
                data = await asyncio.wait_for(loop.run_in_executor(executor, partial_task), timeout=30)
                logger.info(f"Data fetched: {data}")
            except asyncio.TimeoutError:
                logger.error(f"Task {task.__name__} timed out")
            except Exception as e:
                logger.error(f"Error executing task {task.__name__}: {e}")

            # if 'save' in event and event['save']:
            #     await loop.run_in_executor(executor, save_data_to_local, data)
        await asyncio.sleep(60)  # 每隔1分钟获取一次数据

def start_data_fetching_process(events):
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=1)
    try:
        asyncio.run(fetch_data_periodically(executor, events))
    except Exception as e:
        logger.error(f"Error in data fetching process: {e}")