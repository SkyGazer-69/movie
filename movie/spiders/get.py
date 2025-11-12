import requests
import json
import random
import time

iplist = []
with open("ipdaili.txt") as f:
    iplist = f.readlines()

def getip():
    proxy = iplist[random.randint(0, len(iplist) - 1)]
    proxy = proxy.replace("\n", "")
    proxies = {
        'http': 'http://' + str(proxy)
    }
    return proxies

headers = [
    {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    },
    {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
    },
    {
        "user-agent": "Mozilla/5.0 (Linux; Android 14; SM-G998B) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Mobile Safari/537.36"
    }
]

# 匹配分类页的电影类型ID
target_types = {
    "动作": 5, "喜剧": 24, "爱情": 13, "科幻": 22,
    "恐怖": 19, "剧情": 11, "战争": 26, "犯罪": 17,
    "惊悚": 10, "冒险": 14, "悬疑": 10, "武侠": 28,
    "奇幻": 16, "动画": 25, "历史": 27
}

def count_movies_in_ur():
    """统计ur.txt中符合目标类型的电影数量"""
    count = 0
    try:
        with open("ur.txt", "r", encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                movies = json.loads(line)
                for movie in movies:
                    for typ in movie.get("types", []):
                        if typ in target_types:
                            count += 1
                            break
        return count
    except Exception as e:
        print(f"统计ur.txt失败：{str(e)}")
        return 0

# 覆盖写入ur.txt
with open("ur.txt", "w", encoding='utf-8') as f:
    f.write("")
print("已清空ur.txt，开始爬取符合分类页的电影...")

total_target = 500
current_count = count_movies_in_ur()
page = 0

while current_count < total_target:
    sleep_time = random.uniform(1, 3)
    time.sleep(sleep_time)

    start = page * 20
    # 随机选择一个目标类型爬取，确保类型多样性
    type_name, type_id = random.choice(list(target_types.items()))
    url = f'https://movie.douban.com/j/chart/top_list?type={type_id}&interval_id=50:40&action=&start={start}&limit=20'

    try:
        r = requests.get(
            url,
            proxies=getip(),
            headers=random.choice(headers),
            timeout=10
        )
        result = json.loads(r.text)

        if not result:
            print(f"第{page}页无数据，切换类型继续爬取")
            page = 0
            continue

        # 筛选符合目标类型的电影
        filtered = []
        for movie in result:
            for typ in movie.get("types", []):
                if typ in target_types:
                    filtered.append(movie)
                    break

        if filtered:
            with open("ur.txt", "a", encoding='utf-8') as f:
                f.write(json.dumps(filtered, ensure_ascii=False) + '\n')
            current_count = count_movies_in_ur()
            print(f"第{page}页爬取完成，当前符合条件的电影数：{current_count}/{total_target}（休眠了{sleep_time:.2f}秒）")
        else:
            print(f"第{page}页无符合目标类型的电影，切换类型")

        page += 1
    except Exception as e:
        print(f"第{page}页爬取失败：{str(e)}，切换类型继续")
        page = 0

print(f"爬取结束！ur.txt中已包含{current_count}部符合分类页的电影（目标500部）")