import asyncio
import logging

import threading
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

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
    return requests.get(url, headers=headers).json()
    session = get_session()
    try:
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
            return request_url(url, headers, data)  # 重试请求
    except Exception as e:
        logger.error(f"Error fetching {url} data: {e}")
        return {"error": str(e), "url": url}
    return response.json()

# 配置日志记录
logging.basicConfig(level=logging.INFO)

# 请求的URL
DISPATCHES_URL = "https://api.helldivers2.dev/api/v1/dispatches"
STEAM_URL = "https://api.helldivers2.dev/api/v1/steam"
ASSIGNMENTS_URL = "https://api.helldivers2.dev/api/v1/assignments"

# 请求头
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your_token_here"  # 替换为实际的token
}

async def fetch_data(url):
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(None, request_url, url, HEADERS)
    logger.info(data)
    return data

async def main():
    urls = [DISPATCHES_URL, STEAM_URL, ASSIGNMENTS_URL]
    
    # 多轮请求测试
    for i in range(10):  # 进行10轮请求
        logger.info(f"Starting round {i+1}")
        tasks = [fetch_data(url) for url in urls]
        for url in urls:
            await fetch_data(url)
            await asyncio.sleep(20)
        # results = await asyncio.gather(*tasks)
        logger.info(f"Round {i+1}")
        await asyncio.sleep(20)  # 每轮请求之间等待20秒

# 运行主函数
if __name__ == "__main__":
    asyncio.run(main())