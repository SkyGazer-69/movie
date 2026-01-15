# coding = utf-8
# 改进的推荐算法实现
import csv
import pymysql
import math
from operator import itemgetter
import random


class UserBasedCF():
    # 初始化相关参数
    def __init__(self):
        # 找到与目标用户兴趣相似的5个用户，为其推荐10部电影
        self.n_sim_user = 5
        self.n_rec_movie = 10

        self.train_data = {}
        self.user_sim_matrix = {}
        self.movie_count = 0
        self.movie_popularity = {}

        print('Similar user number = %d' % self.n_sim_user)
        print('Recommended movie number = %d' % self.n_rec_movie)

    # 读文件得到"用户-电影"数据
    def get_dataset(self, filename, pivot=0.8):
        for line in self.load_file(filename):
            user, movie, rating = line.split(',')
            self.train_data.setdefault(user, {})
            self.train_data[user][movie] = float(rating)

            # 计算电影流行度
            if movie not in self.movie_popularity:
                self.movie_popularity[movie] = 0
            self.movie_popularity[movie] += 1
        print('Load training data success!')

    # 读文件，返回文件的每一行
    def load_file(self, filename):
        with open(filename, 'r') as f:
            for i, line in enumerate(f):
                if i == 0:  # 去掉文件第一行的title
                    continue
                yield line.strip('\n')
        print('Load %s success!' % filename)

    # 计算用户之间的相似度（使用余弦相似度）
    def calc_user_sim(self):
        # 构建"电影-用户"倒排索引
        print('Building movie-user table ...')
        movie_user = {}
        for user, movies in self.train_data.items():
            for movie in movies:
                if movie not in movie_user:
                    movie_user[movie] = set()
                movie_user[movie].add(user)
        print('Build movie-user table success!')

        self.movie_count = len(movie_user)
        print('Total movie number = %d' % self.movie_count)

        print('Build user co-rated movies matrix ...')
        for movie, users in movie_user.items():
            for u in users:
                for v in users:
                    if u == v:
                        continue
                    self.user_sim_matrix.setdefault(u, {})
                    self.user_sim_matrix[u].setdefault(v, 0)
                    # 使用余弦相似度计算
                    self.user_sim_matrix[u][v] += 1
        print('Build user co-rated movies matrix success!')

        # 计算相似度（归一化）
        print('Calculating user similarity matrix ...')
        for u, related_users in self.user_sim_matrix.items():
            for v, count in related_users.items():
                # 使用余弦相似度：|N(u) ∩ N(v)| / sqrt(|N(u)| * |N(v)|)
                self.user_sim_matrix[u][v] = count / math.sqrt(
                    len(self.train_data[u]) * len(self.train_data[v])
                )
        print('Calculate user similarity matrix success!')

    def recommend(self, user, n_items=None):
        """
        为指定用户推荐物品
        :param user: 用户ID
        :param n_items: 推荐物品数量
        :return: 推荐物品列表
        """
        if n_items is None:
            n_items = self.n_rec_movie

        K = self.n_sim_user

        # 检查用户是否在训练集中
        if user not in self.train_data:
            print(f"Warning: User {user} not in training data. Using popular items.")
            return self.get_popular_movies(n_items)

        # 获取用户已经看过的电影
        watched_movies = set(self.train_data[user].keys())

        # 计算推荐分数
        rank = {}
        sim_sum = {}

        # 找到与目标用户最相似的K个用户
        for similar_user, similarity in sorted(
                self.user_sim_matrix.get(user, {}).items(),
                key=itemgetter(1),
                reverse=True
        )[:K]:

            # 遍历相似用户的电影
            for movie in self.train_data[similar_user]:
                # 如果目标用户已经看过，则跳过
                if movie in watched_movies:
                    continue

                # 计算推荐分数（考虑用户评分和相似度）
                rating = float(self.train_data[similar_user][movie])
                if movie not in rank:
                    rank[movie] = 0.0
                    sim_sum[movie] = 0.0

                # 加权评分：相似度 * 用户评分
                rank[movie] += similarity * rating
                sim_sum[movie] += abs(similarity)

        # 归一化得分
        for movie in rank:
            if sim_sum[movie] != 0:
                rank[movie] = rank[movie] / sim_sum[movie]
            else:
                rank[movie] = 0

        # 如果推荐列表为空，返回热门电影
        if not rank:
            print(f"Warning: No recommendations found for user {user}. Using popular items.")
            return self.get_popular_movies(n_items)

        # 按得分排序并返回
        sorted_rank = sorted(rank.items(), key=itemgetter(1), reverse=True)[:n_items]
        return sorted_rank

    def get_popular_movies(self, n_items):
        """
        获取热门电影
        """
        # 按流行度排序
        sorted_popular = sorted(self.movie_popularity.items(), key=itemgetter(1), reverse=True)
        return [(movie_id, score) for movie_id, score in sorted_popular[:n_items]]

    def hybrid_recommend(self, user, n_items=None):
        """
        混合推荐：结合协同过滤和基于流行度的推荐
        """
        if n_items is None:
            n_items = self.n_rec_movie

        # 协同过滤推荐
        cf_recs = dict(self.recommend(user, n_items * 2))

        # 流行度推荐
        pop_recs = dict(self.get_popular_movies(n_items * 2))

        # 混合策略：给协同过滤推荐更高的权重
        final_rank = {}

        # 协同过滤推荐结果给予更高权重
        for movie, score in cf_recs.items():
            final_rank[movie] = score * 1.5  # 权重1.5

        # 流行度推荐结果给予较低权重
        for movie, popularity in pop_recs.items():
            if movie in final_rank:
                final_rank[movie] += popularity * 0.5  # 权重0.5
            else:
                final_rank[movie] = popularity * 0.5

        # 按最终得分排序
        sorted_final = sorted(final_rank.items(), key=itemgetter(1), reverse=True)[:n_items]
        return sorted_final

    def evaluate_and_save(self):
        print("Saving recommendations to database ...")

        # 连接数据库
        db = pymysql.connect(
            host='localhost',
            user='root',
            password='123456',
            database='django_movie',
            charset='utf8'
        )
        cursor = db.cursor()

        try:
            sql_truncate = "TRUNCATE TABLE myapp_rec;"
            cursor.execute(sql_truncate)
            db.commit()

            # 为每个用户生成推荐
            insert_sql = "INSERT INTO myapp_rec(user_id, movie_id, rating) VALUES (%s, %s, %s)"

            for user in self.train_data.keys():
                # 使用混合推荐算法
                rec_movies = self.hybrid_recommend(user)

                print(f"Recommendations for user {user}: {rec_movies}")

                # 插入推荐数据
                for movie_id, rating in rec_movies:
                    data = (int(user), int(movie_id), float(rating))
                    cursor.execute(insert_sql, data)

            db.commit()
            print("Recommendations saved successfully!")

        except Exception as e:
            print(f"Error saving recommendations: {e}")
            db.rollback()
        finally:
            cursor.close()
            db.close()


if __name__ == '__main__':
    db = pymysql.connect(host='localhost', user='root', password='123456', database='django_movie', charset='utf8')
    cursor = db.cursor()
    sql = "SELECT comment_user, movie, comment_score FROM myapp_comment"
    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    db.close()

    with open('rating.csv', 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['userId', 'movieId', 'rating'])
        for item in data:
            user_id = item[0]
            try:
                movie_id = int(item[1])
            except:
                continue
            rating = item[2]
            writer.writerow([user_id, movie_id, rating])

    rating_file = 'rating.csv'

    userCF = UserBasedCF()
    userCF.get_dataset(rating_file)
    userCF.calc_user_sim()
    userCF.evaluate_and_save()

    print("Recommendation system updated successfully!")
