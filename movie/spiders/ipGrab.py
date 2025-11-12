import requests
import time
import threading
from queue import Queue
from lxml import etree
from requests.exceptions import RequestException

PROXY_SOURCES = [
    'https://www.zdaye.com/dayProxy.html',
    'https://www.kuaidaili.com/free/intr/',
    'https://www.89ip.cn/index_1.html',
    'https://www.66ip.cn/1.html',
    'https://ip.ihuan.me/address/5Lit5Zu9.html',
    'https://www.ip3366.net/free/',
    'https://www.data5u.com/free/',
    'https://www.xiladaili.com/',
    'https://www.feilongip.com/'
]

# 线程数设置
THREAD_NUM = 5
# 存储所有抓取到的IP（去重）
all_proxies = set()
# 线程锁
lock = threading.Lock()


def fetch_proxies(url, queue):
    """从单个代理源抓取IP并放入队列"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/'
                      '118.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }

    try:
        print(f"正在抓取代理源: {url}")
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.encoding = response.apparent_encoding
        html = response.text

        # 根据不同网站解析IP和端口
        if 'zdaye.com' in url:
            tree = etree.HTML(html)
            rows = tree.xpath('//div[@class="cont"]/table//tr')[1:]
            for row in rows:
                try:
                    ip = row.xpath('./td[1]/text()')[0].strip()
                    port = row.xpath('./td[2]/text()')[0].strip()
                    queue.put(f"{ip}:{port}")
                except:
                    continue

        elif 'kuaidaili.com' in url:
            tree = etree.HTML(html)
            rows = tree.xpath('//table[@class="table table-bordered table-striped"]//tr')[1:]
            for row in rows:
                try:
                    ip = row.xpath('./td[1]/text()')[0].strip()
                    port = row.xpath('./td[2]/text()')[0].strip()
                    queue.put(f"{ip}:{port}")
                except:
                    continue

        elif '89ip.cn' in url:
            tree = etree.HTML(html)
            rows = tree.xpath('//table[@class="layui-table"]//tr')[1:]
            for row in rows:
                try:
                    ip = row.xpath('./td[1]/text()')[0].strip()
                    port = row.xpath('./td[2]/text()')[0].strip()
                    queue.put(f"{ip}:{port}")
                except:
                    continue

        elif '66ip.cn' in url:
            tree = etree.HTML(html)
            rows = tree.xpath('//table//tr')[2:]
            for row in rows:
                try:
                    ip = row.xpath('./td[1]/text()')[0].strip()
                    port = row.xpath('./td[2]/text()')[0].strip()
                    queue.put(f"{ip}:{port}")
                except:
                    continue

        elif 'ihuan.me' in url:
            tree = etree.HTML(html)
            rows = tree.xpath('//div[@class="table-responsive"]/table//tr')[1:]
            for row in rows:
                try:
                    ip = row.xpath('./td[1]/text()')[0].strip()
                    port = row.xpath('./td[2]/text()')[0].strip()
                    queue.put(f"{ip}:{port}")
                except:
                    continue

        elif 'ip3366.net' in url:
            tree = etree.HTML(html)
            rows = tree.xpath('//table[@class="table table-bordered table-striped"]//tr')[1:]
            for row in rows:
                try:
                    ip = row.xpath('./td[1]/text()')[0].strip()
                    port = row.xpath('./td[2]/text()')[0].strip()
                    queue.put(f"{ip}:{port}")
                except:
                    continue

        elif 'data5u.com' in url:
            tree = etree.HTML(html)
            rows = tree.xpath('//ul[@class="l2"]')
            for row in rows:
                try:
                    ip = row.xpath('./span[1]/li/text()')[0].strip()
                    port = row.xpath('./span[2]/li/text()')[0].strip()
                    queue.put(f"{ip}:{port}")
                except:
                    continue

        print(f"代理源 {url} 抓取完成")

    except Exception as e:
        print(f"抓取代理源 {url} 出错: {str(e)}")


def process_queue(queue):
    """处理队列中的IP，去重后存储"""
    global all_proxies
    while not queue.empty():
        proxy = queue.get()
        try:
            with lock:
                if proxy not in all_proxies:
                    all_proxies.add(proxy)
                    print(f"已收集代理IP: {proxy} (总计: {len(all_proxies)})")
        finally:
            queue.task_done()


def main():
    print("开始全网代理IP抓取...")
    start_time = time.time()
    proxy_queue = Queue()

    # 1. 多线程抓取代理
    fetch_threads = []
    for url in PROXY_SOURCES:
        t = threading.Thread(target=fetch_proxies, args=(url, proxy_queue))
        t.start()
        fetch_threads.append(t)
        time.sleep(1)  # 间隔请求，避免被反爬

    # 等待所有抓取线程完成
    for t in fetch_threads:
        t.join()

    # 2. 多线程处理队列（去重）
    process_threads = []
    for _ in range(THREAD_NUM):
        t = threading.Thread(target=process_queue, args=(proxy_queue,))
        t.start()
        process_threads.append(t)

    # 等待处理完成
    proxy_queue.join()
    for t in process_threads:
        t.join()

    # 3. 保存结果到文件（覆盖原有内容）
    with open('ipdaili.txt', 'w', encoding='utf-8') as f:
        for proxy in all_proxies:
            f.write(f"{proxy}\n")

    # 4. 输出统计信息
    end_time = time.time()
    print(f"\n抓取完成！共收集到 {len(all_proxies)} 个代理IP")
    print(f"结果已保存到 ipdaili.txt")
    print(f"总耗时: {end_time - start_time:.2f}秒")


if __name__ == "__main__":
    # 忽略SSL警告
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()