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
from django.views.decorators.cache import cache_page

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

# 登入
def login_user(request):
    if request.method == "GET":
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
                if user.is_superuser:
                    return redirect('/admin_index/')
                else:
                    next_url = request.GET.get('next', '/front_index/')
                    return redirect(next_url)
            else:
                messages.error(request, '用户不存在或密码错误!')
                return redirect('/login/')
        else:
            return render(request, 'login.html', {'form': form})
    return HttpResponse(status=405)

# 注册提示信息
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

# 注册
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


@cache_page(60 * 120)
def rank(request):
    queryset_high = Movie.objects.order_by('-moive_time')[:10]

    type_filters = {
        "queryset_action": "动作",
        "queryset_comedy": "喜剧",
        "queryset_love": "爱情",
        "queryset_scienceFiction": "科幻",
        "queryset_terror": "恐怖",
        "queryset_plot": "剧情",
        "queryset_war": "战争",
        "queryset_crime": "犯罪",
        "queryset_thriller": "惊悚",
        "queryset_cartoon": "动画",
        "queryset_history": "历史"
    }

    context = {"queryset_high": queryset_high}
    for key, type_name in type_filters.items():
        context[key] = Movie.objects.filter(type__contains=type_name)[:10]

    return render(request, 'front_rank.html', context)


def depot(request, *args, **kwargs):
    if not kwargs:
        kwargs = {
            'depot_type_ID': '0',
            'depot_region_ID': '0',
            'depot_time_ID': '0',
        }

    type_ID = kwargs.get('depot_type_ID')
    region_ID = kwargs.get('depot_region_ID')
    time_ID = kwargs.get('depot_time_ID')

    type_list = [
        {"ID": "1", "type": "动作"}, {"ID": "2", "type": "喜剧"}, {"ID": "3", "type": "爱情"},
        {"ID": "4", "type": "科幻"}, {"ID": "5", "type": "恐怖"}, {"ID": "6", "type": "剧情"},
        {"ID": "7", "type": "战争"}, {"ID": "8", "type": "犯罪"}, {"ID": "9", "type": "惊悚"},
        {"ID": "10", "type": "冒险"}, {"ID": "11", "type": "悬疑"}, {"ID": "12", "type": "武侠"},
        {"ID": "13", "type": "奇幻"}, {"ID": "14", "type": "动画"}, {"ID": "15", "type": "历史"}]
    region_list = [
        {"ID": "1", "region": "大陆"}, {"ID": "2", "region": "香港"}, {"ID": "3", "region": "台湾"},
        {"ID": "4", "region": "美国"}, {"ID": "5", "region": "法国"}, {"ID": "6", "region": "英国"},
        {"ID": "7", "region": "日本"}, {"ID": "8", "region": "韩国"}, {"ID": "9", "region": "德国"},
        {"ID": "10", "region": "泰国"}, {"ID": "11", "region": "印度"}, {"ID": "12", "region": "意大利"},
        {"ID": "13", "region": "西班牙"}, {"ID": "14", "region": "加拿大"}]
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

    filters = Q()
    if type:
        filters &= Q(type__contains=type)
    if region:
        filters &= Q(region__contains=region)
    if time:
        filters &= Q(moive_time__contains=time)

    queryset = Movie.objects.filter(filters) if filters else Movie.objects.all()

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if is_ajax:
        page = int(request.GET.get('page', 1))
        page_size = 50
        start = (page - 1) * page_size
        end = start + page_size

        movies = queryset[start:end]
        has_more = end < queryset.count()

        movie_data = []
        for obj in movies:
            movie_data.append({
                'movie_ID': obj.movie_ID,
                'name': obj.name if obj.name else '未知影片',
                'poster': obj.poster if obj.poster and obj.poster != '' else '/static/img/wt.jpg'
            })

        return JsonResponse({
            'movies': movie_data,
            'has_more': has_more,
            'total': queryset.count()
        })

    return render(
        request,
        'front_depot.html',
        {
            'type_list': type_list,
            'region_list': region_list,
            'time_list': time_list,
            'queryset': queryset[:50],
            'kwargs': kwargs,
            'type_name': type_name,
            'region_name': region_name,
            'time_name': time_name,
            'total_count': queryset.count(),
            'has_more': queryset.count() > 50
        }
    )

# 详情页
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

# 收藏功能
def collect(request):
    collect_user = request.user.username
    collect_movie = request.GET.get('movie_name')
    queryset_collect = Collect.objects.filter(collect_user=collect_user)
    list_movie = Movie.objects.get(name=collect_movie)
    if queryset_collect.filter(collect_movie=collect_movie).exists():
        queryset_collect.filter(collect_movie=collect_movie).delete()
        return JsonResponse({"status": "uncollect", "message": "取消收藏"})
    else:
        file_list = {
            'collect_movie': collect_movie,
            'collect_user': collect_user,
            'movie_information': list_movie,
        }
        Collect.objects.create(**file_list)
        return JsonResponse({"status": "collect", "message": "收藏成功"})

# 添加评论功能
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


def recommend(request):

    user = request.user
    if not user.is_authenticated:
        messages.error(request, '请先登录以查看个性化推荐！')
        return redirect('/login/')

    user_obj = UserInfo.objects.get(username=user.username)
    user_id = user_obj.user_ID

    rec_movies = Rec.objects.filter(user_id=user_id).order_by('-rating')[:10]
    recommended_movies = []

    for rec in rec_movies:
        try:
            # 添加异常处理
            movie = Movie.objects.get(movie_ID=rec.movie_id)
            recommended_movies.append(movie)
        except Movie.DoesNotExist:
            continue

    # 推荐电影不足，补充热门电影
    if len(recommended_movies) < 10:
        hot_movies = Movie.objects.order_by('-movie_score', '-moive_time')
        for movie in hot_movies:
            if movie not in recommended_movies and len(recommended_movies) < 10:
                recommended_movies.append(movie)

    if not recommended_movies:
        messages.info(request, '暂时没有可推荐的电影')
        return redirect('/front_index/')

    return render(request, 'front_recommendation.html', {
        'data_list': recommended_movies,
        'recommendation_source': 'personalized' if len(rec_movies) > 0 else 'popular'
    })


@login_required
def center(request):
    try:
        queryset_user = UserInfo.objects.get(username=request.user.username)
        queryset_comment = Comment.objects.filter(comment_user=queryset_user.user_ID).order_by('-comment_time')
        queryset_collect = Collect.objects.filter(collect_user=request.user.username)

        comment_count = queryset_comment.count()
        collect_count = queryset_collect.count()

        account_level = "初级"
        if comment_count + collect_count >= 10:
            account_level = "中级"
        if comment_count + collect_count >= 30:
            account_level = "高级"
        if comment_count + collect_count >= 50:
            account_level = "资深"

        recent_comments = queryset_comment[:5]
        recent_collects = queryset_collect[:6]

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

        processed_recent_comments = []
        for comment in recent_comments:
            user_id = comment.comment_user
            if len(user_id) > 8:
                masked_user_id = f"{user_id[:4]}...{user_id[-4:]}"
            else:
                masked_user_id = user_id
            comment_date = comment.comment_time.date()
            processed_recent_comments.append({
                'obj': comment,
                'masked_user_id': masked_user_id,
                'comment_date': comment_date,
            })
    except UserInfo.DoesNotExist:
        queryset_user = None
        queryset_collect = []
        processed_page_queryset = []
        processed_recent_comments = []
        recent_collects = []
        page_object = None
        comment_count = 0
        collect_count = 0
        account_level = "未登录"

    context = {
        "queryset_user": queryset_user,
        "queryset_collect": queryset_collect,
        "recent_collects": recent_collects,
        "queryset": processed_page_queryset,
        "recent_comments": processed_recent_comments,
        "page_string": page_object.html() if page_object else "",
        "comment_count": comment_count,
        "collect_count": collect_count,
        "account_level": account_level,
    }
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
        "queryset": page_object.page_queryset,  # 分页数据
        "page_string": page_object.html()  # 分页页码
    }
    # 渲染电影管理页面模板
    return render(request, 'admin_movie.html', context)


# 电影添加
def movie_add(request):
    form = MovieModelForm(data=request.POST)
    if form.is_valid():
        # 生成电影ID
        timestamp = datetime.now().strftime("%m%d%H%M")
        random_suffix = str(random.randint(10, 99))
        form.instance.movie_ID = (timestamp + random_suffix)[:32]
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
    return JsonResponse({"status": True})


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
            user.save()

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
            old_password = request.POST.get('old_password', '').strip()
            new_password = request.POST.get('new_password', '').strip()
            confirm_password = request.POST.get('confirm_password', '').strip()

            if not authenticate(username=user.username, password=old_password):
                return JsonResponse({'success': False, 'message': '原密码错误！'})

            if new_password != confirm_password:
                return JsonResponse({'success': False, 'message': '两次密码输入不一致！'})

            if len(new_password) < 6:
                return JsonResponse({'success': False, 'message': '新密码长度不能少于6位！'})

            if old_password == new_password:
                return JsonResponse({'success': False, 'message': '新密码不能与原密码相同！'})

            user.set_password(new_password)
            user.save()
            logout(request)

            return JsonResponse({
                'success': True,
                'message': '密码修改成功，请重新登录！',
                'login_url': '/login/'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'message': f'修改失败：{str(e)}'})

    return JsonResponse({'success': False, 'message': '仅支持POST请求！'})


@cache_page(60 * 120)
@superuser_required
def admin_index(request):
    from django.db.models import Count, Avg

    movie_num = Movie.objects.count()
    user_num = UserInfo.objects.count()
    comment_num = Comment.objects.count()
    collect_num = Collect.objects.count()

    score_distribution = []
    for i in range(10):
        count = Movie.objects.filter(movie_score__gte=i, movie_score__lt=i + 1).count()
        score_distribution.append(count)

    movie_type_data = {}
    all_movies = Movie.objects.exclude(type="无").exclude(type="").values_list('type', flat=True)
    for type_str in all_movies:
        types = type_str.split(',')
        for t in types:
            t = t.strip()
            if t:
                movie_type_data[t] = movie_type_data.get(t, 0) + 1
    top_types = sorted(movie_type_data.items(), key=lambda x: x[1], reverse=True)[:10]

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

    region_data = {}
    all_regions = Movie.objects.exclude(region="无").exclude(region="").values_list('region', flat=True)
    for region_str in all_regions:
        regions = region_str.split(',')
        for r in regions:
            r = r.strip()
            if r:
                region_data[r] = region_data.get(r, 0) + 1
    top_regions = sorted(region_data.items(), key=lambda x: x[1], reverse=True)[:10]

    current_year = datetime.now().year
    yearly_movies = []
    years_range = range(current_year - 9, current_year + 1)
    year_counts = Movie.objects.filter(
        moive_time__regex='|'.join([str(y) for y in years_range])
    ).values('moive_time').annotate(count=Count('movie_ID'))

    year_count_dict = {str(year): 0 for year in years_range}
    for item in year_counts:
        for year in years_range:
            if str(year) in item['moive_time']:
                year_count_dict[str(year)] += item['count']
                break

    for year in years_range:
        yearly_movies.append({
            "year": str(year),
            "count": year_count_dict.get(str(year), 0)
        })

    collect_type_data = {}
    collect_with_movies = Collect.objects.select_related('movie_information').exclude(
        movie_information__type="无"
    ).exclude(
        movie_information__type=""
    ).values('movie_information__type')

    for item in collect_with_movies:
        type_str = item['movie_information__type']
        if type_str:
            types = type_str.split(',')
            for t in types:
                t = t.strip()
                if t:
                    collect_type_data[t] = collect_type_data.get(t, 0) + 1
    top_collect_types = sorted(collect_type_data.items(), key=lambda x: x[1], reverse=True)[:10]

    top_movies = Collect.objects.values('collect_movie').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    processed_top_movies = []
    for movie in top_movies:
        movie_title = movie['collect_movie']
        chinese_chars = ''.join([char for char in movie_title if '\u4e00' <= char <= '\u9fff'])
        if chinese_chars:
            truncated_title = chinese_chars[:8] if len(chinese_chars) > 8 else chinese_chars
        else:
            truncated_title = movie_title[:8] if len(movie_title) > 8 else movie_title
        processed_top_movies.append({
            'collect_movie': truncated_title,
            'count': movie['count']
        })

    monthly_collects = []
    now = dj_timezone.now()
    for i in range(11, -1, -1):
        target_date = now - timedelta(days=30 * i)
        month_str = target_date.strftime('%Y-%m')
        count = Collect.objects.filter(
            movie_information__moive_time__icontains=month_str
        ).count()
        monthly_collects.append({
            "month": month_str,
            "count": count
        })

    user_sex_data = [
        {"name": "男", "value": UserInfo.objects.filter(sex=1).count()},
        {"name": "女", "value": UserInfo.objects.filter(sex=0).count()}
    ]

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

    monthly_users = []
    for i in range(11, -1, -1):
        start_date = now - timedelta(days=30 * i)
        end_date = now - timedelta(days=30 * (i + 1))
        count = UserInfo.objects.filter(
            registration__gte=end_date,
            registration__lt=start_date
        ).count()
        monthly_users.append({
            "month": start_date.strftime('%Y-%m'),
            "count": count
        })

    user_active_data = [
        {"name": '7天内', "value": UserInfo.objects.filter(last_login__gte=now - timedelta(days=7)).count()},
        {"name": '30天内', "value": UserInfo.objects.filter(last_login__gte=now - timedelta(days=30)).count()},
        {"name": '90天内', "value": UserInfo.objects.filter(last_login__gte=now - timedelta(days=90)).count()},
        {"name": '超过90天', "value": UserInfo.objects.filter(last_login__lt=now - timedelta(days=90)).count()}
    ]

    comment_score_data = []
    for i in range(11):
        count = Comment.objects.filter(
            comment_score__gte=i,
            comment_score__lt=i + 1
        ).count()
        comment_score_data.append(count)

    monthly_comments = []
    for i in range(11, -1, -1):
        start_date = now - timedelta(days=30 * i)
        end_date = now - timedelta(days=30 * (i + 1))
        count = Comment.objects.filter(
            comment_time__gte=end_date,
            comment_time__lt=start_date
        ).count()
        monthly_comments.append({
            "month": start_date.strftime('%Y-%m'),
            "count": count
        })

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
            {"name": "0-50字", "value": Comment.objects.filter(discussion__isnull=False).exclude(discussion='').count()},
        ]

    top_active_users = Comment.objects.values('comment_user').annotate(
        count=Count('id')
    ).order_by('-count')[:10]

    if not top_types:
        top_types = [("暂无数据", 0)]
    if not top_collect_types:
        top_collect_types = [("暂无数据", 0)]
    if not movie_score_pie:
        movie_score_pie = [{"name": "暂无数据", "value": 1}]
    if not comment_length_data:
        comment_length_data = [{"name": "暂无数据", "value": 1}]

    context = {
        "movie_num": movie_num,
        "user_num": user_num,
        "comment_num": comment_num,
        "collect_num": collect_num,
        "score_distribution": score_distribution,

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


@login_required
def delete_comment(request):
    if request.method == 'POST':
        comment_id = request.POST.get('comment_id')
        try:
            user = UserInfo.objects.get(username=request.user.username)
            comment = Comment.objects.get(comment_ID=comment_id, comment_user=user.user_ID)
            comment.delete()
            return JsonResponse({'success': True, 'message': '评论删除成功！'})
        except Comment.DoesNotExist:
            return JsonResponse({'success': False, 'message': '评论不存在或无权限删除！'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'删除失败：{str(e)}'})
    return JsonResponse({'success': False, 'message': '仅支持POST请求！'})


@login_required
def update_avatar(request):
    if request.method == 'POST':
        try:
            avatar = request.POST.get('avatar', '')
            if not avatar:
                return JsonResponse({'success': False, 'message': '请选择头像'})

            user = request.user
            user.avatar = avatar
            user.save()

            return JsonResponse({'success': True, 'message': '头像更新成功'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'更新失败：{str(e)}'})
    return JsonResponse({'success': False, 'message': '仅支持POST请求'})


@login_required
def center(request):
    try:
        queryset_user = UserInfo.objects.get(username=request.user.username)
        queryset_comment = Comment.objects.filter(comment_user=queryset_user.user_ID).order_by('-comment_time')
        queryset_collect = Collect.objects.filter(collect_user=request.user.username)

        comment_count = queryset_comment.count()
        collect_count = queryset_collect.count()

        account_level = "初级"
        if comment_count + collect_count >= 10:
            account_level = "中级"
        if comment_count + collect_count >= 30:
            account_level = "高级"
        if comment_count + collect_count >= 50:
            account_level = "资深"

        recent_comments = queryset_comment[:5]
        recent_collects = queryset_collect[:6]

        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'

        if is_ajax:
            page = int(request.GET.get('page', 1))
            page_size = 10
            data_type = request.GET.get('type', 'comments')

            if data_type == 'comments':
                start = (page - 1) * page_size
                end = start + page_size
                comments = queryset_comment[start:end]

                processed_comments = []
                for comment in comments:
                    user_id = comment.comment_user
                    if len(user_id) > 8:
                        masked_user_id = f"{user_id[:4]}...{user_id[-4:]}"
                    else:
                        masked_user_id = user_id
                    comment_date = comment.comment_time.date()
                    processed_comments.append({
                        'comment_ID': comment.comment_ID,
                        'movie': comment.movie,
                        'discussion': comment.discussion,
                        'comment_score': comment.comment_score,
                        'comment_date': str(comment_date),
                    })

                return JsonResponse({
                    'success': True,
                    'data': processed_comments,
                    'has_more': end < comment_count,
                    'total': comment_count
                })

            elif data_type == 'collects':
                start = (page - 1) * page_size
                end = start + page_size
                collects = queryset_collect[start:end]

                collect_data = []
                for obj in collects:
                    collect_data.append({
                        'movie_ID': obj.movie_information.movie_ID,
                        'name': obj.movie_information.name,
                        'poster': obj.movie_information.poster if obj.movie_information.poster and obj.movie_information.poster != '' else '/static/img/wt.jpg',
                        'movie_score': obj.movie_information.movie_score if obj.movie_information.movie_score else '暂无'
                    })

                return JsonResponse({
                    'success': True,
                    'data': collect_data,
                    'has_more': end < collect_count,
                    'total': collect_count
                })

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

        processed_recent_comments = []
        for comment in recent_comments:
            user_id = comment.comment_user
            if len(user_id) > 8:
                masked_user_id = f"{user_id[:4]}...{user_id[-4:]}"
            else:
                masked_user_id = user_id
            comment_date = comment.comment_time.date()
            processed_recent_comments.append({
                'obj': comment,
                'masked_user_id': masked_user_id,
                'comment_date': comment_date,
            })
    except UserInfo.DoesNotExist:
        queryset_user = None
        queryset_collect = []
        processed_page_queryset = []
        processed_recent_comments = []
        recent_collects = []
        page_object = None
        comment_count = 0
        collect_count = 0
        account_level = "未登录"

    context = {
        "queryset_user": queryset_user,
        "queryset_collect": queryset_collect,
        "recent_collects": recent_collects,
        "queryset": processed_page_queryset,
        "recent_comments": processed_recent_comments,
        "page_string": page_object.html() if page_object else "",
        "comment_count": comment_count,
        "collect_count": collect_count,
        "account_level": account_level,
    }
    return render(request, 'front_center.html', context)

