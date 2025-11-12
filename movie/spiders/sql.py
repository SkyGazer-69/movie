import pymysql
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'passwd': '123456',
    'db': 'django_movie',
    'charset': 'utf8mb4',
}

# 外键约束配置
FOREIGN_KEY_NAME = "MovieRecommendation__movie_information_id_064b8705_fk_MovieReco"
RELATED_TABLE = "myapp_collect"


def parse_ur_data():
    movie_list = []
    try:
        with open('ur.txt', 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    movies = json.loads(line)
                    for movie in movies:
                        movie_list.append({
                            "title": movie.get("title", ""),
                            "director": "/".join(movie.get("directors", [])),
                            "actors": "/".join(movie.get("actors", [])),
                            "type": "/".join(movie.get("types", [])),
                            "region": "/".join(movie.get("regions", [])),
                            "language": movie.get("language", ""),
                            "release_date": movie.get("release_date", ""),
                            "duration": movie.get("duration", ""),
                            "summary": movie.get("summary", ""),
                            "cover_url": movie.get("cover_url", ""),
                            "score": movie.get("score", "")
                        })
                except json.JSONDecodeError as e:
                    logger.warning(f"第{line_num}行JSON解析失败，跳过：{str(e)}")
        logger.info(f"成功解析ur.txt，共提取{len(movie_list)}条电影信息")
    except Exception as e:
        logger.error(f"解析ur.txt失败: {str(e)}", exc_info=True)
    return movie_list


def drop_foreign_key():
    """删除外键约束"""
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            sql = f"ALTER TABLE {RELATED_TABLE} DROP FOREIGN KEY {FOREIGN_KEY_NAME}"
            cursor.execute(sql)
            conn.commit()
            logger.info(f"已删除{RELATED_TABLE}表的外键约束{FOREIGN_KEY_NAME}")
    except pymysql.MySQLError as e:
        logger.warning(f"删除外键约束失败（可能已不存在）: {str(e)}")
    finally:
        if conn:
            conn.close()


def recreate_foreign_key():
    """重建外键约束"""
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            sql = f"""
                ALTER TABLE {RELATED_TABLE} 
                ADD CONSTRAINT {FOREIGN_KEY_NAME} 
                FOREIGN KEY (movie_information_id) 
                REFERENCES myapp_movie(id)
            """
            cursor.execute(sql)
            conn.commit()
            logger.info(f"已重建{RELATED_TABLE}表的外键约束{FOREIGN_KEY_NAME}")
    except pymysql.MySQLError as e:
        logger.error(f"重建外键约束失败: {str(e)}")
    finally:
        if conn:
            conn.close()


def get_latest_movie_id():
    """获取数据库中最新的movie_ID（用于自增）"""
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(movie_ID) FROM myapp_movie")
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0
    except pymysql.MySQLError as e:
        logger.error(f"查询最新movie_ID失败: {str(e)}")
        return 0
    finally:
        if conn:
            conn.close()


def insert_new_movies(movie_list):
    """插入新电影数据（去重 + movie_ID自增），并统计重复和成功插入数量"""
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        with conn.cursor() as cursor:
            # 查询已有电影标题，用于去重
            cursor.execute("SELECT name FROM myapp_movie")
            existing_titles = {row[0] for row in cursor.fetchall()}
            duplicate_count = 0
            new_movies = []

            latest_id = get_latest_movie_id()
            new_id = latest_id + 1

            for movie in movie_list:
                title = movie["title"]
                if title in existing_titles:
                    duplicate_count += 1
                else:
                    min_duration = None
                    duration = movie["duration"]
                    if "分钟" in duration:
                        min_str = duration.split("分钟")[0]
                        if min_str.isdigit():
                            min_duration = int(min_str)

                    new_movies.append({
                        'movie_ID': new_id,
                        'name': title,
                        'director': movie["director"],
                        'scriptwriter': '',  # 若无编剧信息可留空
                        'actors': movie["actors"],
                        'type': movie["type"],
                        'region': movie["region"],
                        'language': movie["language"],
                        'moive_time': movie["release_date"],
                        'min': min_duration,
                        'introduction': movie["summary"],
                        'poster': movie["cover_url"],
                        'movie_score': movie["score"],
                        'number': None
                    })
                    new_id += 1

            if not new_movies:
                logger.info("无新电影数据可插入")
                return
            else:
                logger.info(f"检测到{duplicate_count}部重复电影，将插入{len(new_movies)}部新电影")

            sql = """
                INSERT INTO myapp_movie 
                (movie_ID, name, director, scriptwriter, actors, type, region, language, moive_time, min, introduction, poster, movie_score, number) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(sql, [
                (movie['movie_ID'], movie['name'], movie['director'], movie['scriptwriter'],
                 movie['actors'], movie['type'], movie['region'], movie['language'],
                 movie['moive_time'], movie['min'], movie['introduction'], movie['poster'],
                 movie['movie_score'], movie['number'])
                for movie in new_movies
            ])
            conn.commit()
            logger.info(f"成功插入{len(new_movies)}条新电影数据")
    except pymysql.MySQLError as e:
        logger.error(f"插入新数据失败: {str(e)}", exc_info=True)
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def main():
    try:
        # 1. 解析ur.txt数据
        movie_list = parse_ur_data()
        if not movie_list:
            logger.error("ur.txt解析失败，程序退出")
            return

        drop_foreign_key()

        insert_new_movies(movie_list)

        recreate_foreign_key()

        logger.info("所有操作完成！")
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()