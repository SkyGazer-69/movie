from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin


class Movie(models.Model):
    movie_ID = models.CharField(max_length=32, null=False, verbose_name="影片ID", default="unknown_id", db_index=True)
    name = models.CharField(max_length=32, null=False, verbose_name="影片名", default="无", db_index=True)
    director = models.CharField(max_length=32, null=False, verbose_name="导演", default="未知导演")
    scriptwriter = models.CharField(max_length=32, null=False, verbose_name="编剧", default="无")
    actors = models.CharField(max_length=256, null=False, verbose_name="主演", default="无")
    type = models.CharField(max_length=32, null=False, verbose_name="类型", default="无", db_index=True)
    region = models.CharField(max_length=32, null=False, verbose_name="出品地区", default="无", db_index=True)
    language = models.CharField(max_length=32, null=False, verbose_name="语言", default="未知语言")
    moive_time = models.CharField(max_length=32, null=False, verbose_name="上映时间", default="未知时间", db_index=True)
    min = models.IntegerField(null=False, verbose_name="时长", default=0)
    introduction = models.CharField(max_length=256, null=False, verbose_name="简介", default="暂无简介")
    poster = models.CharField(max_length=256, null=False, verbose_name="海报链接", default="无")
    movie_score = models.DecimalField(max_digits=3, decimal_places=1, null=False, verbose_name="评分", default=0.00, db_index=True)
    number = models.IntegerField(verbose_name="评分人数", default=0)

    # class Meta:
    #     verbose_name = "电影"
    #     verbose_name_plural = "电影集"
    #
    # def __str__(self):
    #     return self.title


class UserManager(BaseUserManager):
    def _create_user(self, username, password, email, **kwargs):
        if not username:
            raise ValueError("请传入用户名！")
        if not password:
            raise ValueError("请传入密码！")
        if not email:
            raise ValueError("请传入邮箱地址！")

        user = self.model(username=username, email=email,** kwargs)
        user.set_password(password)
        user.save()
        return user

    def create_user(self, username, password, email, **kwargs):
        kwargs['is_superuser'] = False
        return self._create_user(username, password, email,** kwargs)

    def create_superuser(self, username, password, email, **kwargs):
        kwargs['is_superuser'] = True
        return self._create_user(username, password, email,** kwargs)


class UserInfo(AbstractBaseUser, PermissionsMixin):
    is_superuser = models.BooleanField(default=False, verbose_name="是否为超级用户")
    user_ID = models.CharField(max_length=32, null=False, verbose_name="用户ID", db_index=True)
    username = models.CharField(max_length=255, null=False, verbose_name="用户名", unique=True)
    password = models.CharField(max_length=255, null=False, verbose_name="用户密码")
    nickname = models.CharField(max_length=255, null=False, verbose_name="用户昵称")
    sex_choice = ((0, "女"),(1, "男"),)
    sex = models.IntegerField(choices=sex_choice, null=False, verbose_name="性别", default=1)
    age = models.IntegerField(verbose_name="年龄", null=True, db_index=True)
    email = models.EmailField(null=False, verbose_name="邮箱", unique=False)
    registration = models.DateTimeField(auto_now_add=True, verbose_name="创建时间", null=False, db_index=True)
    last_login = models.DateTimeField(auto_now_add=True, verbose_name="最后登录时间", null=False, db_index=True)
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ['email']
    EMAIL_FIELD = 'email'
    objects = UserManager()

    def __str__(self):
        return self.username


class Collect(models.Model):
    collect_user = models.CharField(max_length=255, null=False, verbose_name="收藏用户名", db_index=True)
    collect_movie = models.CharField(max_length=255, null=False, verbose_name="影片名", db_index=True)
    movie_information = models.ForeignKey(Movie, on_delete=models.CASCADE, null=True, db_index=True)

class Comment(models.Model):
    comment_ID = models.CharField(max_length=32, null=False, verbose_name="评论ID", db_index=True)
    comment_time = models.DateTimeField(auto_now_add=True, verbose_name="发布时间", db_index=True)
    comment_user = models.CharField(max_length=64, null=False, verbose_name="评论用户", db_index=True)
    movie = models.CharField(max_length=128, null=False, verbose_name="影片名", db_index=True)
    discussion = models.TextField(max_length=256, null=False, verbose_name="评论内容")
    comment_score = models.FloatField(null=False, verbose_name="评分", db_index=True)

class Rec(models.Model):
    user_id = models.IntegerField(null=False,verbose_name="收藏用户id", db_index=True)
    movie_id = models.IntegerField(null=False,verbose_name="影片id", db_index=True)
    rating = models.FloatField(null=False,verbose_name="推荐度")

class Collect(models.Model):
    board_ID = models.CharField(max_length=32, unique=True, verbose_name="留言ID")
    board_time = models.DateTimeField(auto_now_add=True, verbose_name="留言时间")
    board_message = models.CharField(max_length=256, verbose_name="留言内容")
    board_user = models.CharField(max_length=255, verbose_name="留言用户")

    class Meta:
        verbose_name = "留言板"
        verbose_name_plural = "留言板"

    def __str__(self):
        return self.board_ID