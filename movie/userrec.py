# coding = utf-8
# 推荐算法实现
import csv
import pymysql
import math
from operator import itemgetter


class UserBasedCF():
    # 初始化相关参数
    def __init__(self):
        # 找到与目标用户兴趣相似的3个用户，为其推荐5部电影
        self.n_sim_user = 3
        self.n_rec_movie = 5

        self.dataSet = {}
        # 用户相似度矩阵
        self.user_sim_matrix = {}
        self.movie_count = 0

        print('Similar user number = %d' % self.n_sim_user)
        print('Recommended movie number = %d' % self.n_rec_movie)

    # 读文件得到“用户-电影”数据
    def get_dataset(self, filename, pivot=0.75):
        dataSet_len = 0
        for line in self.load_file(filename):
            user, movie, rating = line.split(',')
            # if random.random() < pivot:
            self.dataSet.setdefault(user, {})
            self.dataSet[user][movie] = rating
            dataSet_len += 1
            # else:
                # self.testSet.setdefault(user, {})
                # self.testSet[user][movie] = rating
        print('Split trainingSet and testSet success!')
        print('dataSet_len = %s' % dataSet_len)

    # 读文件，返回文件的每一行
    def load_file(self, filename):
        with open(filename, 'r') as f:
            for i, line in enumerate(f):
                if i == 0:  # 去掉文件第一行的title
                    continue
                yield line.strip('\n')
        print('Load %s success!' % filename)

    # 计算用户之间的相似度
    def calc_user_sim(self):
        # 构建“电影-用户”倒排索引
        # key = movieId, value = list of userIDs who have seen this movie
        print('Building movie-user table ...')
        movie_user = {}
        for user, movies in self.dataSet.items():
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
                    self.user_sim_matrix[u][v] += 1
        print('Build user co-rated movies matrix success!')

        # 计算相似度
        print('Calculating user similarity matrix ...')
        for u, related_users in self.user_sim_matrix.items():
            for v, count in related_users.items():
                self.user_sim_matrix[u][v] = count / math.sqrt(len(self.dataSet[u]) * len(self.dataSet[v]))
        print('Calculate user similarity matrix success!')

    # # 针对目标用户，找到其最相似的K个用户，产生N个推荐
    # def recommend(self, user):
    #     K = self.n_sim_user
    #     N = self.n_rec_movie
    #     rank = {}
    #     watched_movies = self.dataSet[user]
    #
    #     # v=similar user, wuv=similar factor
    #     for v, wuv in sorted(self.user_sim_matrix[user].items(), key=itemgetter(1), reverse=True)[0:K]:
    #         for movie in self.dataSet[v]:
    #             if movie in watched_movies:
    #                 continue
    #             rank.setdefault(movie, 0)
    #             rank[movie] += wuv
    #     return sorted(rank.items(), key=itemgetter(1), reverse=True)[0:N]

    # 针对目标用户，找到其最相似的K个用户，产生N个推荐
    def recommend(self, user):
        K = self.n_sim_user
        N = self.n_rec_movie
        rank = {}

        # --- 新增的前置检查 ---
        # 如果用户不在相似度矩阵中，直接返回热门电影
        if user not in self.user_sim_matrix:
            print(f"Warning: User {user} has no similar users. Returning popular movies.")
            return self.get_popular_movies(N)

        watched_movies = self.dataSet[user]

        # v=similar user, wuv=similar factor
        # 遍历最相似的K个用户
        for v, wuv in sorted(self.user_sim_matrix[user].items(), key=itemgetter(1), reverse=True)[0:K]:
            for movie in self.dataSet[v]:
                if movie in watched_movies:
                    continue
                rank.setdefault(movie, 0)
                rank[movie] += wuv

        # 如果没有找到任何推荐电影（例如，相似用户看过的电影该用户都看过了），也返回热门电影
        if not rank:
            print(f"Warning: User {user} has no new movies to recommend. Returning popular movies.")
            return self.get_popular_movies(N)

        return sorted(rank.items(), key=itemgetter(1), reverse=True)[0:N]

    # --- 新增的辅助方法：获取热门电影 ---
    def get_popular_movies(self, top_n):
        """
        计算并返回观看人数最多的前N部电影
        """
        movie_popularity = {}
        for user, movies in self.dataSet.items():
            for movie in movies:
                if movie not in movie_popularity:
                    movie_popularity[movie] = 0
                movie_popularity[movie] += 1

        # 按流行度排序并返回前N部
        popular_movies = sorted(movie_popularity.items(), key=itemgetter(1), reverse=True)
        return popular_movies[:top_n] if len(popular_movies) >= top_n else popular_movies

    # 产生推荐并通过准确率、召回率和覆盖率进行评估
    def evaluate(self):
        print("Evaluation start ...")
        N = self.n_rec_movie
        # 准确率和召回率
        hit = 0
        rec_count = 0
        test_count = 0
        # 覆盖率
        all_rec_movies = set()

        # 打开数据库连接
        db = pymysql.connect(host='localhost', user='root', password='123456', database='django_movie', charset='utf8')
        cursor = db.cursor()
        # 使用 execute() 方法执行 SQL 查询
        sql1="truncate table myapp_rec;"
        cursor.execute(sql1)
        db.commit()

        sql = "insert into myapp_rec(user_id,movie_id,rating) values (%s,%s,%s)"
        for i, user in enumerate(self.dataSet):
            rec_movies = self.recommend(user)
            print(user,rec_movies)
            for item in rec_movies:
                data=(user,item[0],item[1])
                cursor.execute(sql, data)
                db.commit()
        #rec_movies是推荐后的数据
        #user:rec-rating 存到数据库
        cursor.close()
        db.close()


if __name__ == '__main__':
    db = pymysql.connect(host='localhost', user='root', password='123456', database='django_movie', charset='utf8')
    cursor = db.cursor()
    sql = "select * from myapp_comment"
    cursor.execute(sql)
    data = cursor.fetchall()
    cursor.close()
    db.close()

    with open('rating.csv','w',encoding='utf-8',newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['userId','musicId','rating'])
        for item in data:
            writer.writerow([item[5],item[6],item[4]])
    rating_file = 'rating.csv'
    userCF = UserBasedCF()
    userCF.get_dataset(rating_file)
    userCF.calc_user_sim()
    userCF.evaluate()






