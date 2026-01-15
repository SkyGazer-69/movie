from board import Board
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.shortcuts import render, redirect
from django import forms
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.contrib import messages
from .models import *
import random
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from myapp.pagination import Pagination
import json
from django.views.decorators.csrf import csrf_exempt
from functools import wraps
from django.utils import timezone as dj_timezone

def superuser_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')

        if not request.user.is_superuser:
            messages.error(request, '无权限访问管理员页面！')
            return redirect('/front_index/')

        return view_func(request, *args, **kwargs)

    return _wrapped_view


class LoginForm(forms.Form):
    username = forms.CharField(
        required=True,
        min_length=3,
        max_length=18,
        error_messages={
            "required": "用户名不能为空!",
            "min_length": "用户名不能低于3个字!",
            "max_length": "用户名不能多于18个字!"
        }
    )
    password = forms.CharField(
        required=True,
        error_messages={
            "required": "密码不能为空!"
        }
    )


def login_user(request):
    if request.method == "GET":
        # GET 请求渲染登录页
        return render(request, 'login.html')

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                request.session.set_expiry(None)
                next_url = request.GET.get('next', '/front_index/')  # 默认为首页
                return redirect(next_url)
            else:
                messages.error(request, '用户不存在或密码错误!')
                return redirect('/login/')
        else:
            # 表单验证失败，返回错误并渲染登录页
            return render(request, 'login.html', {'form': form})
    # 其他请求方法（如PUT/DELETE）返回405
    return HttpResponse(status=405)


class RegisterForm(forms.Form):
    username = forms.CharField(
        required=True,
        min_length=3,
        max_length=18,
        error_messages={
            "required": "用户名不能为空!",
            "min_length": "用户名不能低于3个字!",
            "max_length": "用户名不能多于18个字!"
        }
    )
    password1 = forms.CharField(
        required=True,
        min_length=3,
        max_length=18,
        error_messages={
            "required": "密码不能为空!",
            "min_length": "密码不能低于3个字!",
            "max_length": "密码不能多于18个字!"
        }
    )
    password2 = forms.CharField(required=False)
    email = forms.EmailField(
        required=True,
        error_messages={
            "required": "邮箱不能为空!"
        }
    )

    def clean_password2(self):
        if not self.errors.get("password1"):
            if self.cleaned_data["password2"] != self.cleaned_data["password1"]:
                raise ValidationError("您输入的密码不一致,请重新输入!")
        return self.cleaned_data


def register(request):
    if request.method == "GET":
        return render(request, "register.html")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            email = form.cleaned_data["email"]
            username_exists = UserInfo.objects.filter(username=username).exists()
            if username_exists:
                messages.error(request, '你输入的用户名已存在!')
                return HttpResponseRedirect('/register/')
            email_exists = UserInfo.objects.filter(email=email).exists()
            if email_exists:
                messages.error(request, '你输入的邮箱已经被注册了!')
                return HttpResponseRedirect('/register/')
            user_ID = datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(1000, 9999))
            UserInfo.objects.create_user(username=username, password=password, email=email, user_ID=user_ID)
            messages.success(request, '注册成功,请登入!')
            return HttpResponseRedirect('/login/')
        else:
            return render(request, 'register.html', {'form': form})


def logout_user(request):
    logout(request)
    return redirect('/front_index/')


def index(request):
    queryset_hot = Movie.objects.order_by('-moive_time', 'movie_ID')[:8]
    queryset_high = Movie.objects.order_by('-movie_score', 'movie_ID')[:8]
    return render(request, 'front_index.html', {"queryset_hot": queryset_hot, "queryset_high": queryset_high})


def front_index(request):
    queryset_hot = Movie.objects.order_by('-moive_time', 'movie_ID')[:8]
    queryset_high = Movie.objects.order_by('-movie_score', 'movie_ID')[:8]
    return render(request, 'front_index.html', {"queryset_hot": queryset_hot, "queryset_high": queryset_high})


def rank(request):
    queryset_high = Movie.objects.order_by('-moive_time')[:10]
    queryset_action = Movie.objects.filter(type__contains="动作")[:10]
    queryset_comedy = Movie.objects.filter(type__contains="喜剧")[:10]
    queryset_love = Movie.objects.filter(type__contains="爱情")[:10]
    queryset_scienceFiction = Movie.objects.filter(type__contains="科幻")[:10]
    queryset_terror = Movie.objects.filter(type__contains="恐怖")[:10]
    queryset_plot = Movie.objects.filter(type__contains="剧情")[:10]
    queryset_war = Movie.objects.filter(type__contains="战争")[:10]
    queryset_crime = Movie.objects.filter(type__contains="犯罪")[:10]
    queryset_thriller = Movie.objects.filter(type__contains="惊悚")[:10]
    queryset_cartoon = Movie.objects.filter(type__contains="动画")[:10]
    queryset_history = Movie.objects.filter(type__contains="历史")[:10]

    context = {
        "queryset_high": queryset_high,
        "queryset_action": queryset_action,
        "queryset_comedy": queryset_comedy,
        "queryset_love": queryset_love,
        "queryset_scienceFiction": queryset_scienceFiction,
        "queryset_terror": queryset_terror,
        "queryset_plot": queryset_plot,
        "queryset_war": queryset_war,
        "queryset_crime": queryset_crime,
        "queryset_thriller": queryset_thriller,
        "queryset_cartoon": queryset_cartoon,
        "queryset_history": queryset_history,
    }

    return render(request, 'front_rank.html', context)


def depot(request, *args, **kwargs):
    if not kwargs:
        kwargs = {
            'depot_type_ID': '0',
            'depot_region_ID': '0',
            'depot_time_ID': '0',
        }

    # 从kwargs中取出对应的id
    type_ID = kwargs.get('depot_type_ID')
    region_ID = kwargs.get('depot_region_ID')
    time_ID = kwargs.get('depot_time_ID')

    # 类型列表
    type_list = [
        {"ID": "1", "type": "动作"}, {"ID": "2", "type": "喜剧"}, {"ID": "3", "type": "爱情"},
        {"ID": "4", "type": "科幻"}, {"ID": "5", "type": "恐怖"}, {"ID": "6", "type": "剧情"},
        {"ID": "7", "type": "战争"}, {"ID": "8", "type": "犯罪"}, {"ID": "9", "type": "惊悚"},
        {"ID": "10", "type": "冒险"}, {"ID": "11", "type": "悬疑"}, {"ID": "12", "type": "武侠"},
        {"ID": "13", "type": "奇幻"}, {"ID": "14", "type": "动画"}, {"ID": "15", "type": "历史"}]
    # 地区列表
    region_list = [
        {"ID": "1", "region": "大陆"}, {"ID": "2", "region": "香港"}, {"ID": "3", "region": "台湾"},
        {"ID": "4", "region": "美国"}, {"ID": "5", "region": "法国"}, {"ID": "6", "region": "英国"},
        {"ID": "7", "region": "日本"}, {"ID": "8", "region": "韩国"}, {"ID": "9", "region": "德国"},
        {"ID": "10", "region": "泰国"}, {"ID": "11", "region": "印度"}, {"ID": "12", "region": "意大利"},
        {"ID": "13", "region": "西班牙"}, {"ID": "14", "region": "加拿大"}]
    # 时间列表
    time_list = [
        {"ID": "1", "time": "2024"}, {"ID": "2", "time": "2023"}, {"ID": "3", "time": "2022"},
        {"ID": "4", "time": "2021"}, {"ID": "5", "time": "2020"}, {"ID": "6", "time": "2019"},
        {"ID": "7", "time": "2018"}, {"ID": "8", "time": "2017"}, {"ID": "9", "time": "2016"},
        {"ID": "10", "time": "2015"}, {"ID": "11", "time": "2014"}, {"ID": "12", "time": "其他"}]

    type_name = '全部'
    region_name = '全部'
    time_name = '全部'
    if type_ID == '0':
        type = ""
    else:
        type_int = int(type_ID)
        type = type_list[type_int - 1].get("type")
        type_name = type_list[type_int - 1].get("type")
    if region_ID == '0':
        region = ''
    else:
        region_int = int(region_ID)
        region = region_list[region_int - 1].get("region")
        region_name = region_list[region_int - 1].get("region")
    if time_ID == '0':
        time = ''
    else:
        time_int = int(time_ID)
        time = time_list[time_int - 1].get("time")
        time_name = time_list[time_int - 1].get("time")

    queryset = Movie.objects.filter(
        Q(type__contains=type) & Q(region__contains=region) & Q(moive_time__contains=time))

    return render(
        request,
        'front_depot.html',
        {
            'type_list': type_list,
            'region_list': region_list,
            'time_list': time_list,
            'queryset': queryset,
            'kwargs': kwargs,
            'type_name': type_name,
            'region_name': region_name,
            'time_name': time_name
        }
    )


def details(request, uid):
    movie_information = Movie.objects.filter(movie_ID=uid)
    movie_name = ""
    movie_ID = ""
    for obj in movie_information:
        movie_name = obj.name
        movie_ID = obj.movie_ID
    queryset = Comment.objects.filter(movie=movie_ID).order_by('-comment_time')
    processed_comments = []
    for comment in queryset:
        user_id = comment.comment_user
        if len(user_id) > 8:
            masked_user_id = f"{user_id[:4]}...{user_id[-4:]}"
        else:
            masked_user_id = user_id
        comment_date = comment.comment_time.date()  # 获取日期对象

        processed_comments.append({
            'obj': comment,
            'masked_user_id': masked_user_id,
            'comment_date': comment_date,
        })

    request.session["info"] = {"movie_ID": movie_ID, "ID": uid}
    collect = Collect.objects.filter(Q(collect_user=request.user.username) & Q(collect_movie=movie_name))

    page_object = Pagination(request, queryset)
    processed_page_queryset = []
    for comment in page_object.page_queryset:
        user_id = comment.comment_user
        if len(user_id) > 8:
            masked_user_id = f"{user_id[:4]}...{user_id[-4:]}"
        else:
            masked_user_id = user_id

        comment_date = comment.comment_time.date()

        processed_page_queryset.append({
            'obj': comment,
            'masked_user_id': masked_user_id,
            'comment_date': comment_date,
        })

    context = {
        "movie_name": movie_name,
        "collect": collect,
        "movie_information": movie_information,
        "queryset": processed_page_queryset,
        "page_string": page_object.html()
    }
    return render(request, 'front_details.html', context)


def collect(request):
    collect_user = request.user.username
    collect_movie = request.GET.get('movie_name')
    queryset_collect = Collect.objects.filter(collect_user=collect_user)
    list_movie = Movie.objects.get(name=collect_movie)
    if queryset_collect.filter(collect_movie=collect_movie).exists():
        queryset_collect.filter(collect_movie=collect_movie).delete()  # 取消收藏
        return JsonResponse({"status": "uncollect", "message": "取消收藏"})
    else:
        file_list = {
            'collect_movie': collect_movie,
            'collect_user': collect_user,
            'movie_information': list_movie,
        }
        Collect.objects.create(**file_list)
        return JsonResponse({"status": "collect", "message": "收藏成功"})


def comment_add(request):
    try:
        comment_score = request.POST.get('comment_score', '').strip()
        comment_discussion = request.POST.get('discussion', '').strip()

        session_info = request.session["info"]
        movie_id = session_info["movie_ID"]
        detail_page_id = session_info["ID"]

        comment_ID = datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(1000, 9999))

        user_info = UserInfo.objects.get(username=request.user.username)
        user_ID = user_info.user_ID

        Comment.objects.create(
            comment_score=float(comment_score),
            discussion=comment_discussion,
            comment_user=user_ID,
            movie=movie_id,
            comment_ID=comment_ID
        )

        return redirect('movie_details', uid=detail_page_id)
    except Exception as e:
        print(f"评论失败: {e}")
        return redirect('/front_index')


# def recommend(request):
#     try:
#         username = request.user
#         userobj = UserInfo.objects.filter(username=username)
#         for obj in userobj:
#             userid = obj.user_ID
#
#         movie_information = Rec.objects.filter(user_id=userid)
#         data_list = []
#
#         for movie in movie_information:
#             data_list.append(Movie.objects.filter(movie_ID=movie.movie_id).first())
#         return render(request, 'front_recommendation.html', {'data_list': data_list})
#     except:
#         return redirect('/front_index')


# 个人中心视图
# 在现有 views.py 文件中替换 recommend 函数

def recommend(request):
    """
    个性化推荐视图
    """
    user = request.user
    if not user.is_authenticated:
        messages.error(request, '请先登录以查看个性化推荐！')
        return redirect('/login/')

    # 获取用户信息
    user_obj = UserInfo.objects.get(username=user.username)
    user_id = user_obj.user_ID

    # 从 Rec 表获取推荐电影
    rec_movies = Rec.objects.filter(user_id=user_id).order_by('-rating')[:10]
    recommended_movies = []

    for rec in rec_movies:
        try:
            # 添加异常处理，防止Movie.DoesNotExist
            movie = Movie.objects.get(movie_ID=rec.movie_id)
            recommended_movies.append(movie)
        except Movie.DoesNotExist:
            # 如果推荐的电影不存在，跳过该推荐
            continue

    # 如果推荐电影不足，补充热门电影
    if len(recommended_movies) < 10:
        hot_movies = Movie.objects.order_by('-movie_score', '-moive_time')
        for movie in hot_movies:
            if movie not in recommended_movies and len(recommended_movies) < 10:
                recommended_movies.append(movie)

    if not recommended_movies:
        # 如果仍然没有电影，返回首页
        messages.info(request, '暂时没有可推荐的电影')
        return redirect('/front_index/')

    return render(request, 'front_recommendation.html', {
        'data_list': recommended_movies,
        'recommendation_source': 'personalized' if len(rec_movies) > 0 else 'popular'
    })


@login_required
def center(request):
    try:
        # 1. 查询当前登录用户信息
        queryset_user = UserInfo.objects.get(username=request.user.username)
        # 2. 查询用户评论
        queryset_comment = Comment.objects.filter(comment_user=queryset_user.user_ID)
        # 3. 查询用户收藏
        queryset_collect = Collect.objects.filter(collect_user=request.user.username)

        # 评论分页处理（原有功能）
        page_object = Pagination(request, queryset_comment)
        processed_page_queryset = []
        for comment in page_object.page_queryset:
            user_id = comment.comment_user
            if len(user_id) > 8:
                masked_user_id = f"{user_id[:4]}...{user_id[-4:]}"
            else:
                masked_user_id = user_id
            comment_date = comment.comment_time.date()
            processed_page_queryset.append({
                'obj': comment,
                'masked_user_id': masked_user_id,
                'comment_date': comment_date,
            })
    except UserInfo.DoesNotExist:
        queryset_user = None
        queryset_collect = []
        processed_page_queryset = []
        page_object = None

    context = {
        "queryset_user": queryset_user,
        "queryset_collect": queryset_collect,
        "queryset": processed_page_queryset,
        "page_string": page_object.html() if page_object else "",
    }
    # 渲染个人中心模板
    return render(request, 'front_center.html', context)


def board_add(request):
    # 增加未登录校验
    if not request.user.is_authenticated:
        messages.error(request, '请先登录')
        return HttpResponseRedirect('/login/')

    board_mes = request.GET.get('boardMessage', '')
    if not board_mes:
        messages.warning(request, '留言失败，请输入内容')
        return HttpResponseRedirect('/center/')
    else:
        board_ID = datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(1000, 9999))
        Board.objects.create(board_message=board_mes, board_user=request.user.username, board_ID=board_ID)
        messages.success(request, '留言成功')
        return HttpResponseRedirect('/center/')
#


# 电影模型表单类，用于电影的添加/编辑
class MovieModelForm(forms.ModelForm):
    class Meta:
        model = Movie  # 关联Movie模型
        exclude = ["movie_ID", "movie_time", "number"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 给所有表单字段添加样式（form-control）和占位符
        for name, field in self.fields.items():
            field.widget.attrs = {"class": "form-control", "placeholder": field.label}


# 电影管理页面视图：展示电影列表、搜索、分页
@superuser_required
def movie(request):
    data_dict = {}
    # 获取搜索关键词
    search_data = request.GET.get('search', "")
    if search_data:
        # 按电影名称模糊搜索
        data_dict["name__contains"] = search_data

    # 查询符合条件的电影数据
    queryset = Movie.objects.filter(**data_dict)
    # 分页处理
    page_object = Pagination(request, queryset)
    form = MovieModelForm()  # 初始化电影表单
    context = {
        "form": form,
        "search_data": search_data,
        "queryset": page_object.page_queryset,  # 分页后的数据
        "page_string": page_object.html()  # 分页页码HTML
    }
    # 渲染电影管理页面模板
    return render(request, 'admin_movie.html', context)


# 电影添加
@superuser_required
@csrf_exempt
def movie_add(request):
    # 用POST数据初始化表单
    form = MovieModelForm(data=request.POST)
    if form.is_valid():
        # 自动生成movie_ID
        form.instance.movie_ID = datetime.now().strftime("%Y%m%d%H%M%S") + str(form.instance.min)
        form.save()
        return JsonResponse({"status": True})
    return JsonResponse({"status": False, "error": form.errors})


# 电影删除
@superuser_required  # 新增装饰器
def movie_delete(request):
    uid = request.GET.get('uid')  # 获取要删除的电影ID
    # 检查电影是否存在
    exists = Movie.objects.filter(movie_ID=uid).exists()
    if not exists:
        return JsonResponse({"status": False, "error": "删除失败，数据不存在。"})

    # 删除对应的电影数据
    Movie.objects.filter(movie_ID=uid).delete()
    return JsonResponse({"status": True})  # 返回成功响应


# 电影详情
@superuser_required
def movie_detail(request):
    uid = request.GET.get("uid")
    row_object = Movie.objects.filter(movie_ID=uid).first()
    if not row_object:
        return JsonResponse({"status": False, "error": "数据不存在。"})
    result = {
        "status": True,
        "data": {
            "name": row_object.name,
            "director": row_object.director,
            "scriptwriter": row_object.scriptwriter,
            "actors": row_object.actors,
            "type": row_object.type,
            "region": row_object.region,
            "language": row_object.language,
            "movie_time": row_object.moive_time,
            "min": row_object.min,
            "introduction": row_object.introduction,
            "poster": row_object.poster,
        }
    }
    return JsonResponse(result)


# 电影编辑
@superuser_required
@csrf_exempt
def movie_edit(request):
    uid = request.GET.get("uid")
    row_object = Movie.objects.filter(movie_ID=uid).first()
    if not row_object:
        return JsonResponse({"status": False, "tips": "数据不存在，请刷新重试。"})

    form = MovieModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()  #
        return JsonResponse({"status": True})

    return JsonResponse({"status": False, "error": form.errors})


# 用户密码修改表单类
class UserModelForm(forms.ModelForm):
    class Meta:
        model = UserInfo  # 关联UserInfo模型
        fields = ["password"]  # 仅显示密码字段

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 给密码字段添加样式和占位符
        for name, field in self.fields.items():
            field.widget.attrs = {"class": "form-control", "placeholder": field.label}


# 用户管理页面
@superuser_required  # 新增装饰器
def users(request):
    data_dict = {}
    # 获取搜索关键词
    search_data = request.GET.get('search', "")
    if search_data:
        # 按用户名模糊搜索
        data_dict["username__contains"] = search_data

    # 查询符合条件的用户数据
    queryset = UserInfo.objects.filter(**data_dict)
    # 分页处理
    page_object = Pagination(request, queryset)
    form = UserModelForm()  # 初始化用户密码表单
    context = {
        "form": form,
        "search_data": search_data,
        "queryset": page_object.page_queryset,  # 分页后的数据
        "page_string": page_object.html()  # 分页
    }
    # 渲染用户管理页面模板
    return render(request, 'admin_users.html', context)


# 用户删除
@superuser_required
def users_delete(request):
    uid = request.GET.get('uid')  # 获取要删除的用户ID
    # 检查用户是否存在
    exists = UserInfo.objects.filter(user_ID=uid).exists()
    if not exists:
        return JsonResponse({"status": False, "error": "删除失败，数据不存在。"})

    # 删除对应的用户数据
    UserInfo.objects.filter(user_ID=uid).delete()
    return JsonResponse({"status": True})  # 返回成功响应


# 用户密码重置
@superuser_required
def users_reset(request):
    uid = request.GET.get('uid')  # 获取要重置密码的用户ID
    # 检查用户是否存在
    exists = UserInfo.objects.filter(user_ID=uid).exists()
    if not exists:
        return JsonResponse({"status": False, "error": "重置失败，数据不存在。"})
    user = UserInfo.objects.get(user_ID=uid)
    user.set_password('654321')
    user.save()
    return JsonResponse({"status": True})


# 返回最多5个电影标题
def search_suggest(request):
    keyword = request.GET.get("keyword", "")
    if not keyword:
        return JsonResponse([], safe=False)
    results = Movie.objects.filter(name__icontains=keyword)[:5]
    suggestions = [
        {
            "title": movie.name,
            "url": f"/movie/{movie.movie_ID}/details/"
        }
        for movie in results
    ]
    return JsonResponse(suggestions, safe=False)


# 显示所有匹配电影
def search_result(request):
    keyword = request.GET.get("search", "")
    if not keyword:
        return render(request, "search_result.html", {"movies": []})
    movies = Movie.objects.filter(name__icontains=keyword)
    return render(request, "search_result.html", {"movies": movies, "keyword": keyword})


# 个人信息更新
@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user  # 当前登录用户
        try:
            nickname = request.POST.get('nickname', '').strip()
            sex = request.POST.get('sex', '')
            age = request.POST.get('age', '')

            if not nickname:
                messages.error(request, '昵称不能为空！')
                return redirect('/center/')

            user.nickname = nickname
            user.sex = int(sex) if sex and sex.isdigit() else None
            user.age = int(age) if age and age.isdigit() else None
            user.save()  # 保存到数据库

            messages.success(request, '个人信息更新成功！')
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')

        return redirect('/center/')
    return redirect('/center/')


@login_required
def update_password(request):
    if request.method == 'POST':
        user = request.user
        try:
            email = request.POST.get('email', '').strip()
            new_password = request.POST.get('new_password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()

            if user.email != email:
                return JsonResponse({'success': False, 'message': '邮箱与当前账号不匹配！'})
            if new_password != confirm_password:
                return JsonResponse({'success': False, 'message': '两次密码输入不一致！'})
            if len(new_password) < 6:
                return JsonResponse({'success': False, 'message': '新密码长度不能少于6位！'})
            user.set_password(new_password)
            user.save()
            logout(request)  # 密码修改后主动登出

            return JsonResponse({
                'success': True,
                'message': '密码修改成功，请重新登录！',
                'login_url': '/login/'  # 登录页路径
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'修改失败：{str(e)}'})

    return JsonResponse({'success': False, 'message': '仅支持POST请求！'})



@superuser_required
def admin_index(request):
    # 基础统计数据
    movie_num = Movie.objects.values('movie_ID', 'name').distinct().count()
    user_num = UserInfo.objects.count()
    comment_num = Comment.objects.count()
    collect_num = Collect.objects.count()

    # 评分分布统计
    score_distribution = []
    for i in range(10):
        count = Movie.objects.filter(movie_score__gte=i, movie_score__lt=i + 1).count()
        score_distribution.append(count)

    # 1. 影片分析
    # 1.1 类型分布
    movie_type_data = {}
    for movie in Movie.objects.exclude(type="无").exclude(type=""):
        types = movie.type.split(',')
        for t in types:
            t = t.strip()
            if t:
                movie_type_data[t] = movie_type_data.get(t, 0) + 1
    top_types = sorted(movie_type_data.items(), key=lambda x: x[1], reverse=True)[:10]

    # 1.2 评分分布（饼图）
    score_ranges = [
        ('9-10分', 9, 10),
        ('8-9分', 8, 9),
        ('7-8分', 7, 8),
        ('6-7分', 6, 7),
        ('5-6分', 5, 6),
        ('3-5分', 3, 5),
        ('1-3分', 1, 3)
    ]
    movie_score_pie = []
    for label, start, end in score_ranges:
        count = Movie.objects.filter(
            movie_score__gte=start,
            movie_score__lt=end
        ).count()
        if count > 0:
            movie_score_pie.append({"name": label, "value": count})

    # 1.3 地区分布
    region_data = {}
    for movie in Movie.objects.exclude(region="无").exclude(region=""):
        regions = movie.region.split(',')
        for r in regions:
            r = r.strip()
            if r:
                region_data[r] = region_data.get(r, 0) + 1
    top_regions = sorted(region_data.items(), key=lambda x: x[1], reverse=True)[:10]

    # 1.4 年份趋势
    current_year = datetime.now().year
    yearly_movies = []
    for year in range(current_year - 9, current_year + 1):
        count = Movie.objects.filter(
            moive_time__icontains=str(year)
        ).count()
        yearly_movies.append({
            "year": str(year),
            "count": count
        })

    # 2. 收藏分析
    collect_type_data = {}
    for collect in Collect.objects.select_related('movie_information'):
        if collect.movie_information and collect.movie_information.type != "无" and collect.movie_information.type != "":
            movie = collect.movie_information
            types = movie.type.split(',')
            for t in types:
                t = t.strip()
                if t:
                    collect_type_data[t] = collect_type_data.get(t, 0) + 1
    top_collect_types = sorted(collect_type_data.items(), key=lambda x: x[1], reverse=True)[:10]

    # 2.2 热门影片TOP10（截取中文标题）
    top_movies = Collect.objects.values('collect_movie').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # 截取中文标题，优先显示中文部分
    processed_top_movies = []
    for movie in top_movies:
        movie_title = movie['collect_movie']
        # 提取中文字符
        chinese_chars = ''.join([char for char in movie_title if '\u4e00' <= char <= '\u9fff'])
        if chinese_chars:
            truncated_title = chinese_chars[:8] if len(chinese_chars) > 8 else chinese_chars
        else:
            truncated_title = movie_title[:8] if len(movie_title) > 8 else movie_title
        processed_top_movies.append({
            'collect_movie': truncated_title,
            'count': movie['count']
        })

    # 2.3 收藏月度趋势
    monthly_collects = []
    for i in range(12):
        start_date = dj_timezone.now() - timedelta(days=30 * i)
        count = Collect.objects.filter(
            movie_information__moive_time__icontains=start_date.strftime('%Y-%m')
        ).count()
        monthly_collects.append({
            "month": start_date.strftime('%Y-%m'),
            "count": count
        })
    monthly_collects.reverse()

    # 3. 用户分析
    user_sex_data = [
        {"name": "男", "value": UserInfo.objects.filter(sex=1).count()},
        {"name": "女", "value": UserInfo.objects.filter(sex=0).count()}
    ]

    # 3.2 年龄分布
    age_labels = ['18岁以下', '18-25岁', '26-35岁', '36-45岁', '46-60岁', '60岁以上']
    age_ranges = [(0, 18), (18, 25), (26, 35), (36, 45), (46, 60), (60, 150)]
    user_age_data = []
    for label, (start, end) in zip(age_labels, age_ranges):
        count = UserInfo.objects.filter(
            age__gte=start,
            age__lt=end
        ).count()
        user_age_data.append({
            "name": label,
            "value": count
        })

    # 3.3 注册趋势
    monthly_users = []
    for i in range(12):
        start_date = dj_timezone.now() - timedelta(days=30 * i)
        end_date = dj_timezone.now() - timedelta(days=30 * (i + 1))
        count = UserInfo.objects.filter(
            registration__gte=end_date,
            registration__lt=start_date
        ).count()
        monthly_users.append({
            "month": start_date.strftime('%Y-%m'),
            "count": count
        })
    monthly_users.reverse()

    # 3.4 用户活跃度
    now = dj_timezone.now()
    user_active_data = [
        {"name": '7天内', "value": UserInfo.objects.filter(last_login__gte=now - timedelta(days=7)).count()},
        {"name": '30天内', "value": UserInfo.objects.filter(last_login__gte=now - timedelta(days=30)).count()},
        {"name": '90天内', "value": UserInfo.objects.filter(last_login__gte=now - timedelta(days=90)).count()},
        {"name": '超过90天', "value": UserInfo.objects.filter(last_login__lt=now - timedelta(days=90)).count()}
    ]

    # 4. 评价分析
    comment_score_data = []
    for i in range(11):
        count = Comment.objects.filter(
            comment_score__gte=i,
            comment_score__lt=i + 1
        ).count()
        comment_score_data.append(count)

    # 4.2 评价趋势
    monthly_comments = []
    for i in range(12):
        start_date = dj_timezone.now() - timedelta(days=30 * i)
        end_date = dj_timezone.now() - timedelta(days=30 * (i + 1))
        count = Comment.objects.filter(
            comment_time__gte=end_date,
            comment_time__lt=start_date
        ).count()
        monthly_comments.append({
            "month": start_date.strftime('%Y-%m'),
            "count": count
        })
    monthly_comments.reverse()

    # 4.3 评价字数分布
    try:
        from django.db.models.functions import Length
        word_ranges = [
            ('0-50字', 0, 50),
            ('50-100字', 50, 100),
            ('100-200字', 100, 200),
            ('200字以上', 200, 999999)
        ]
        comment_length_data = []
        for label, start, end in word_ranges:
            count = Comment.objects.annotate(
                text_len=Length('discussion')
            ).filter(
                text_len__gte=start,
                text_len__lt=end
            ).count()
            if count > 0:
                comment_length_data.append({
                    "name": label,
                    "value": count
                })
    except:
        comment_length_data = [
            {"name": "0-50字", "value": sum(1 for c in Comment.objects.all() if len(c.discussion or '') < 50)},
            {"name": "50-100字", "value": sum(1 for c in Comment.objects.all() if 50 <= len(c.discussion or '') < 100)},
            {"name": "100-200字",
             "value": sum(1 for c in Comment.objects.all() if 100 <= len(c.discussion or '') < 200)},
            {"name": "200字以上", "value": sum(1 for c in Comment.objects.all() if len(c.discussion or '') >= 200)}
        ]

    # 4.4 活跃用户TOP10
    top_active_users = Comment.objects.values('comment_user').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    # 数据完整性保护
    if not top_types:
        top_types = [("暂无数据", 0)]
    if not top_collect_types:
        top_collect_types = [("暂无数据", 0)]
    if not movie_score_pie:
        movie_score_pie = [{"name": "暂无数据", "value": 1}]
    if not comment_length_data:
        comment_length_data = [{"name": "暂无数据", "value": 1}]

    # 数据打包
    context = {
        "movie_num": movie_num,
        "user_num": user_num,
        "comment_num": comment_num,
        "collect_num": collect_num,
        "score_distribution": score_distribution,

        # 图表数据
        "chart_data_json": json.dumps({
            "movie": {
                "type_bar": {
                    "labels": [t[0] for t in top_types],
                    "values": [t[1] for t in top_types]
                },
                "score_pie": movie_score_pie,
                "region_bar": {
                    "labels": [r[0] for r in top_regions],
                    "values": [r[1] for r in top_regions]
                },
                "year_line": {
                    "labels": [y["year"] for y in yearly_movies],
                    "values": [y["count"] for y in yearly_movies]
                }
            },
            "collect": {
                "type_line": {
                    "labels": [t[0] for t in top_collect_types],
                    "values": [t[1] for t in top_collect_types]
                },
                "top_movies": {
                    "movies": [m['collect_movie'] for m in processed_top_movies],
                    "values": [m['count'] for m in processed_top_movies]
                },
                "monthly_line": {
                    "labels": [d["month"] for d in monthly_collects],
                    "values": [d["count"] for d in monthly_collects]
                }
            },
            "user": {
                "sex_pie": user_sex_data,
                "age_bar": user_age_data,
                "reg_month_line": {
                    "labels": [m["month"] for m in monthly_users],
                    "values": [m["count"] for m in monthly_users]
                },
                "active_pie": user_active_data
            },
            "comment": {
                "score_bar": comment_score_data,
                "monthly_line": {
                    "labels": [d["month"] for d in monthly_comments],
                    "values": [d["count"] for d in monthly_comments]
                },
                "length_pie": comment_length_data,
                "top_users": {
                    "users": [str(u["comment_user"])[:8] for u in top_active_users],
                    "values": [u["count"] for u in top_active_users]
                }
            }
        }, ensure_ascii=False)
    }
    return render(request, 'admin_index.html', context)



