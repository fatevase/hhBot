import json

import re
from ..conf import config as conf
import requests
from translate import Translator
import requests
from pathlib import Path


def is_english(text, thresh=0.5):
    # 计算文本中英文字符的比例
    english_chars = re.findall(r'[a-zA-Z]', text)
    total_chars = len(text)
    if total_chars == 0:
        return False
    english_ratio = len(english_chars) / total_chars
    return english_ratio > thresh


def translate_text(text, dest_language='zh'):
    translator = Translator(to_lang=dest_language)
    translation = translator.translate(text)
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
