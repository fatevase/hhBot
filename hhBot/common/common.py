import json

import re
from ..conf import config as conf
import requests

import requests
from pathlib import Path
import time
import asyncio
import concurrent.futures


import functools

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
        print(translation)
    except Exception as e:
        print(e)
        translation = text

    return translation

def SendMessage(payload):
    url = f"{conf.HTTP_HOST}{conf.SEND_MSG_URL}{conf.COMMON_PARAMS}"

    headers = {
        'Content-Type': 'application/json;charset=UTF-8',
        'token': conf.HeyChatAPPToken,
    }
    response = requests.request("POST", url, headers=headers, data=payload.json())
    content = response.content.decode('utf-8')
    print(content)

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
                data = await loop.run_in_executor(executor, partial_task)
                print(data)
            except Exception as e:
                print(e)

            # if 'save' in event and event['save']:
            #     await loop.run_in_executor(executor, save_data_to_local, data)
        await asyncio.sleep(60)  # 每隔1分钟获取一次数据

def start_data_fetching_process(events):
    executor = concurrent.futures.ProcessPoolExecutor(max_workers=1)
    asyncio.run(fetch_data_periodically(executor, events))
