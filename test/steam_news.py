import xml.etree.ElementTree as ET
import requests
import json

def xml_to_json(url):
    # 发送请求获取XML内容
    headers = {
        "Host":"store.steampowered.com",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Connection": "keep-alive",
        "Cookie": "app_impressions=553850@1_5_9__412|2514130@1_5_9__412; recentapps=%7B%22553850%22%3A1729011029%7D; timezoneOffset=28800,0; birthtime=-915177599; lastagecheckage=1-January-1941; sessionid=65e29f37b7a7fb5e35da36bb; steamCountry=US%7C843c0782a24a8c6e070f4a63126c8eee; browserid=3485303138265202348",
        "Priority": "u=0, i",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0.1 Safari/605.1.15"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {"error": f"Failed to fetch data from {url}"}
    
    # 解析XML内容
    root = ET.fromstring(response.content)
    
    # 定义一个递归函数来将XML转换为字典
    def xml_to_dict(element):
        node = {}
        # 处理属性
        if element.attrib:
            node['attributes'] = element.attrib
        # 处理子元素
        for child in element:
            child_dict = xml_to_dict(child)
            if child.tag in node:
                if not isinstance(node[child.tag], list):
                    node[child.tag] = [node[child.tag]]
                node[child.tag].append(child_dict)
            else:
                node[child.tag] = child_dict
        # 处理文本内容
        if element.text and element.text.strip():
            node['text'] = element.text.strip()
        return node
    
    # 调用递归函数从根元素开始构建字典
    xml_dict = xml_to_dict(root)['channel']['item']
    
    
    return xml_dict

# 使用函数
url = "https://store.steampowered.com/feeds/news/app/553850/?cc=GB&l=chinese"
json_output = xml_to_json(url)
print(json_output)
