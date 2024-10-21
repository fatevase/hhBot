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
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import threading
# 创建一个线程本地存储对象
thread_local = threading.local()

def get_session():
    if not hasattr(thread_local, "session"):
        retry_strategy = Retry(
            total=3,  # 总共重试次数
            backoff_factor=1,  # 重试间隔时间的指数退避因子
            status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的状态码
            allowed_methods=["HEAD", "GET", "OPTIONS"]  # 需要重试的方法
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        thread_local.session = session
    return thread_local.session

def request_url(url, headers, data=None):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 获取速率限制信息
        rate_limit = response.headers.get("X-RateLimit-Limit")
        rate_limit_remaining = response.headers.get("X-RateLimit-Remaining")


        logger.info(f"Response from {url}: {response}, Rate Limit: {rate_limit}, Rate Limit Remaining: {rate_limit_remaining}")

        if response.status_code == 429:
            retry_after = int(retry_after or 1)  # 获取 retry-after 时间
            logger.warning(f"Rate limit reached, retrying after {retry_after} seconds")
            time.sleep(retry_after)
            return request_url(url, headers, data)  # 重试请求

    except Exception as e:
        logger.error(f"Error fetching {url} data: {e}")
        return None
    return response
    try:
        retry_strategy = Retry(
        total=3,  # 总共重试次数
        backoff_factor=1,  # 重试间隔时间的指数退避因子
        status_forcelist=[429, 500, 502, 503, 504],  # 需要重试的状态码
        allowed_methods=["HEAD", "GET", "OPTIONS"]  # 需要重试的方法
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        
        if data is None:
            response = session.get(url, headers=headers)
        else:
            response = session.post(url, headers=headers, data=data)
        response.raise_for_status()
        logger.info(f"Response from {url}: {response}")
        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 1))  # 获取 retry-after 时间
            logger.warning(f"Rate limit reached, retrying after {retry_after} seconds")
            time.sleep(retry_after)
    except Exception as e:
        logger.error(f"Error fetching {url} data: {e}")
        return None
    finally:
        session.close()
    return response

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

async def retry_task(task, retries, retry_delay, *args, **kwargs):
    for attempt in range(retries):
        try:
            return await task(*args, **kwargs)
        except Exception as e:
            logger.error(f"Task failed, retrying {attempt + 1}/{retries}: {e}")
            await asyncio.sleep(retry_delay)
    logger.error(f"Task failed after {retries} retries")



async def fetch_data_once(executor, event, max_retries=3, retry_delay=5):
    task = event['task']
    args = event.get('args', [])
    kwargs = event.get('kwargs', {})
    retries = 0
    loop = asyncio.get_running_loop()
    print(loop)
    while retries < max_retries:
        try:
            partial_task = functools.partial(task, *args, **kwargs)
            # 动态超时：根据任务复杂度或类型调整
            timeout = event.get('timeout', 30)  
            data = await asyncio.wait_for(loop.run_in_executor(executor, partial_task), timeout=timeout)
            logger.info(f"Data fetched from {task.__name__}: {data}")
            return data  # 成功获取数据后返回
        except asyncio.TimeoutError:
            logger.error(f"Task {task.__name__} timed out")
        except Exception as e:
            logger.error(f"Error executing task {task.__name__}: {e}")
    
        retries += 1
        if retries < max_retries:
            logger.info(f"Retrying task {task.__name__} ({retries}/{max_retries}) after {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)
        else:
            logger.error(f"Task {task.__name__} failed after {max_retries} retries")
            return None  # 返回 None 以指示任务失败

def start_data_fetching_process(events, interval=30):
    """合并后的主函数，定时执行任务"""
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)  # 根据任务类型设置线程池大小
    async def periodic_fetch_data():
        tasks = []
        while True:
            for i, event in enumerate(events):
                await fetch_data_once(executor, event)
                await asyncio.sleep(interval)  # 每分钟执行一个任务
                logger.info(f"Task {i + 1}/{len(events)} completed, waiting for next task...")
            await asyncio.sleep(interval)
            # tasks = [fetch_data_once(executor, event) for event in events]
            # await asyncio.gather(*tasks)  # 并行执行所有任务
            # await asyncio.sleep(interval)  # 等待 interval 秒后再次调度任务

    try:
        asyncio.run(periodic_fetch_data())  # 启动异步任务调度
    except Exception as e:
        logger.error(f"Error in data fetching process: {e}")
