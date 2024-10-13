from translate import Translator

def translate_text(text, dest_language='zh'):
    translator = Translator(to_lang=dest_language)
    translation = translator.translate(text)
    return translation

# 示例文本
text = "Auspicious day [list]fellow[/list] [h1]citizens[/h1]! Another hot fix rolling out this fine Tuesday."

# 翻译为中文
translated_text = translate_text(text)
print(translated_text)

import re

def format_dispatch_message(message):
    # 替换 [list] 和 [*] 标签为 Markdown 格式
    message = re.sub(r'\[list\]', '\n\n', message)
    message = re.sub(r'\[/list\]', '\n\n', message)
    message = re.sub(r'\[\*\]', '\n- ', message)
    return message

# 示例消息
message = """
[h1]Overview[/h1]
[list] [*] Crash Fixes [*] Weapon & Stratagem fixes [*] Fixes to the Impaler & explosion radius [*] Soft lock fix [/list]
"""

formatted_message = format_dispatch_message(message)
print(formatted_message)