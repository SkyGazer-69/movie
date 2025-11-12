from board import Board
from django.db.models import Q
from django.shortcuts import render, redirect
from django import forms
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.contrib import messages
from .models import *
import random
from datetime import datetime, timezone
from django.core.exceptions import ValidationError
from myapp.pagination import Pagination
import json
from django.views.decorators.csrf import csrf_exempt


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
                return redirect('/front_index')
            else:
                messages.error(request, '用户不存在或密码错误!')
                return redirect('/login/')


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
        return render(request,"register.html")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            email = form.cleaned_data["email"]
            username_exists = UserInfo.objects.filter(username = username).exists()
            if username_exists:
                messages.error(request,'你输入的用户名已存在!')
                return HttpResponseRedirect('/register/')
            email_exists = UserInfo.objects.filter(email = email).exists()
            if email_exists:
                messages.error(request,'你输入的邮箱已经被注册了!')
                return HttpResponseRedirect('/register/')
            user_ID = datetime.now().strftime("%Y%m%d%H%M%S") + str(random.randint(1000,9999))
            UserInfo.objects.create_user(username = username,password = password,email = email,user_ID = user_ID)
            messages.success(request,'注册成功,请登入!')
            return  HttpResponseRedirect('/login/')
        else:
            return render(request, 'register.html', {'form': form})


def logout_user(request):
    logout(request)
    return redirect('/front_index/')

def index(request):
    queryset_hot = Movie.objects.order_by('-moive_time')[:8]
    queryset_high = Movie.objects.order_by('-moive_time')[:8]
    return render(request,'front_index.html',{"queryset_hot":queryset_hot,"queryset_high":queryset_high})


def front_index(request):
    queryset_hot = Movie.objects.order_by('-moive_time')[:8]
    queryset_high = Movie.objects.order_by('-moive_time')[:8]
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
        return JsonResponse({"status": "uncollect", "message": "取消收藏成功"})
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


def recommend(request):
    try:
        username = request.user
        userobj = UserInfo.objects.filter(username=username)
        for obj in userobj:
            userid = obj.user_ID

        movie_information = Rec.objects.filter(user_id=userid)
        data_list = []

        for movie in movie_information:
            data_list.append(Movie.objects.filter(movie_ID=movie.movie_id).first())
        return render(request, 'front_recommendation.html', {'data_list': data_list})
    except:
        return redirect('/front_index')


def center(request):
    queryset_user = UserInfo.objects.filter(username=request.user.username)
    queryset_comment = Comment.objects.filter(comment_user=request.user.username)
    queryset_collect = Collect.objects.filter(collect_user=request.user.username)
    page_object = Pagination(request, queryset_comment)
    context = {
        "queryset_user": queryset_user,
        "queryset_collect": queryset_collect,
        "queryset": page_object.page_queryset,  # 分页的数据
        "page_string": page_object.html()  # 页码
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


def admin_index(request):
    time = datetime.now()
    movie_num = Movie.objects.count()  # 统计电影总数
    board_num = Board.objects.count()  # 统计留言总数
    user_num = UserInfo.objects.count()  # 统计用户总数
    comment_num = Comment.objects.count()
    # print(comment_num)  # 打印评论总数到控制台
    context = {
        "movie_num": movie_num,
        "board_num": board_num,
        "user_num": user_num,
        "comment_num": comment_num,
    }
    return render(request, 'admin_index.html', context)


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
def movie(request):
    data_dict = {}
    # 获取搜索关键词（默认空字符串）
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


# 电影添加接口（排除CSRF校验）
@csrf_exempt
def movie_add(request):
    # 用POST数据初始化表单
    form = MovieModelForm(data=request.POST)
    if form.is_valid():
        # 自动生成movie_ID（时间戳+片长）
        form.instance.movie_ID = datetime.now().strftime("%Y%m%d%H%M%S") + str(form.instance.min)
        form.save()  # 保存数据到数据库
        return JsonResponse({"status": True})  # 返回成功响应
    # 表单验证失败，返回错误信息
    return JsonResponse({"status": False, "error": form.errors})


# 电影删除接口
def movie_delete(request):
    uid = request.GET.get('uid')  # 获取要删除的电影ID
    # 检查电影是否存在
    exists = Movie.objects.filter(movie_ID=uid).exists()
    if not exists:
        return JsonResponse({"status": False, "error": "删除失败，数据不存在。"})

    # 删除对应的电影数据
    Movie.objects.filter(movie_ID=uid).delete()
    return JsonResponse({"status": True})  # 返回成功响应


# 电影详情接口：获取单部电影的详细信息
def movie_detail(request):
    uid = request.GET.get("uid")  # 获取电影ID
    # 查询对应的电影对象（取第一个）
    row_object = Movie.objects.filter(movie_ID=uid).first()
    if not row_object:
        return JsonResponse({"status": False, "error": "数据不存在。"})
    # 构造返回的电影详情数据
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
    return JsonResponse(result)  # 返回JSON格式的详情数据


# 电影编辑接口（排除CSRF校验）
@csrf_exempt
def movie_edit(request):
    uid = request.GET.get("uid")  # 获取要编辑的电影ID
    # 查询对应的电影对象
    row_object = Movie.objects.filter(movie_ID=uid).first()
    if not row_object:
        return JsonResponse({"status": False, "tips": "数据不存在，请刷新重试。"})

    # 用POST数据和已有对象初始化表单（实现编辑功能）
    form = MovieModelForm(data=request.POST, instance=row_object)
    if form.is_valid():
        form.save()  # 保存修改后的数据
        return JsonResponse({"status": True})

    # 表单验证失败，返回错误信息
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


# 用户管理页面视图：展示用户列表、搜索、分页
def users(request):
    data_dict = {}
    # 获取搜索关键词（默认空字符串）
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
        "page_string": page_object.html()  # 分页页码HTML
    }
    # 渲染用户管理页面模板
    return render(request, 'admin_users.html', context)


# 用户删除接口
def users_delete(request):
    uid = request.GET.get('uid')  # 获取要删除的用户ID
    # 检查用户是否存在
    exists = UserInfo.objects.filter(user_ID=uid).exists()
    if not exists:
        return JsonResponse({"status": False, "error": "删除失败，数据不存在。"})

    # 删除对应的用户数据
    UserInfo.objects.filter(user_ID=uid).delete()
    return JsonResponse({"status": True})  # 返回成功响应


# 用户密码重置接口
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



