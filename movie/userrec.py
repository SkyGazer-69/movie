import csv
import pymysql
import math
from operator import itemgetter


class UserBasedCF():
    def __init__(self):
        self.n_sim_user = 5
        self.n_rec_movie = 10
        self.train_data = {}
        self.user_sim_matrix = {}
        self.movie_info = {}
        self.movie_popularity = {}

    def get_dataset(self, filename):
        """加载用户评分数据"""
        with open(filename, 'r', encoding='utf-8') as f:
            next(f)
            for line in f:
                user, movie, rating = line.strip().split(',')
                self.train_data.setdefault(user, {})
                self.train_data[user][movie] = float(rating)
                self.movie_popularity[movie] = self.movie_popularity.get(movie, 0) + 1

    def calc_user_sim(self):
        """计算用户相似度（余弦相似度）"""
        # 构建电影 - 用户倒排索引
        movie_user = {}
        for user, movies in self.train_data.items():
            for movie in movies:
                movie_user.setdefault(movie, set()).add(user)

        # 计算共现矩阵
        for movie, users in movie_user.items():
            for u in users:
                for v in users:
                    if u != v:
                        self.user_sim_matrix.setdefault(u, {}).setdefault(v, 0)
                        self.user_sim_matrix[u][v] += 1

        # 归一化
        for u, related_users in self.user_sim_matrix.items():
            for v, count in related_users.items():
                self.user_sim_matrix[u][v] = count / math.sqrt(
                    len(self.train_data[u]) * len(self.train_data[v])
                )

    # 核心
    def recommend(self, user):
        if user not in self.train_data:
            return self.get_popular_movies()

        watched = set(self.train_data[user].keys())

        similar_users = sorted(
            self.user_sim_matrix.get(user, {}).items(),
            key=itemgetter(1), reverse=True
        )[:self.n_sim_user]

        rank = {}
        for sim_user, sim in similar_users:
            for movie, rating in self.train_data[sim_user].items():
                if movie not in watched:
                    rank[movie] = rank.get(movie, 0) + sim * rating

        return sorted(rank.items(), key=itemgetter(1), reverse=True)[:self.n_rec_movie]



    def get_popular_movies(self):
        sorted_popular = sorted(
            self.movie_popularity.items(),
            key=itemgetter(1), reverse=True
        )
        return [(mid, score) for mid, score in sorted_popular[:self.n_rec_movie]]

    def save_to_db(self):
        db = pymysql.connect(
            host='localhost', user='root', password='123456',
            database='django_movie', charset='utf8'
        )
        cursor = db.cursor()

        try:
            cursor.execute("TRUNCATE TABLE myapp_rec;")

            # 为每个用户生成推荐
            insert_sql = "INSERT INTO myapp_rec(user_id, movie_id, rating) VALUES (%s, %s, %s)"
            for user in self.train_data.keys():
                recs = self.recommend(user)
                for movie_id, rating in recs:
                    cursor.execute(insert_sql, (int(user), int(movie_id), float(rating)))

            db.commit()
            print(f"成功为 {len(self.train_data)} 个用户生成推荐！")
        except Exception as e:
            print(f"错误：{e}")
            db.rollback()
        finally:
            cursor.close()
            db.close()


if __name__ == '__main__':
    # 从数据库导出评分数据
    db = pymysql.connect(
        host='localhost', user='root', password='123456',
        database='django_movie', charset='utf8'
    )
    cursor = db.cursor()
    cursor.execute("SELECT comment_user, movie, comment_score FROM myapp_comment")
    data = cursor.fetchall()
    cursor.close()
    db.close()

    with open('rating.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['userId', 'movieId', 'rating'])
        for user_id, movie_id, rating in data:
            try:
                writer.writerow([user_id, int(movie_id), float(rating)])
            except:
                continue

    print("=" * 50)
    print("开始运行基于用户的协同过滤推荐算法...")
    print("=" * 50)

    userCF = UserBasedCF()
    userCF.get_dataset('rating.csv')
    print(f"✓ 加载完成：{len(userCF.train_data)} 个用户，{len(userCF.movie_popularity)} 部电影")

    userCF.calc_user_sim()
    print(f"✓ 相似度计算完成")

    userCF.save_to_db()
    print("✓ 推荐结果已保存到 myapp_rec 表")
    print("=" * 50)
    print("推荐系统更新成功！")
