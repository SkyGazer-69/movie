from django.urls import path, re_path

from . import views

urlpatterns = [
    path('login/', views.login_user),
    path('register/', views.register),
    path('logout/', views.logout_user),
    path('', views.index),
    path('front_index/', views.front_index),
    path('rank/', views.rank),
    path('depot/', views.depot),
    re_path('depot-(?P<depot_type_ID>(\d+))-(?P<depot_region_ID>(\d+))-(?P<depot_time_ID>(\d+))', views.depot),
    path('movie/<int:uid>/details/', views.details, name='movie_details'),
    path('collect/', views.collect, name='collect'),
    path('comment/add/', views.comment_add, name='comment_add'),
    path('recommend/', views.recommend),
    path('center/', views.center, name='user_center'),
    path('board/add/', views.board_add),

    path('search_suggest/', views.search_suggest, name='search_suggest'),
    path('result/', views.search_result, name='search_result'),

    # 管理员路由
    path('movie/', views.movie),
    path('movie/add/', views.movie_add),
    path('movie/delete/', views.movie_delete),
    path('movie/detail/', views.movie_detail),
    path('movie/edit/', views.movie_edit),
    path('users/', views.users),
    path('users/delete/', views.users_delete),
    path('users/reset/', views.users_reset),
    path('admin_index/', views.admin_index, name='admin_index'),

    # 功能路由
    path('user/profile/update/', views.update_profile, name='update_profile'),
    path('user/password/update/', views.update_password, name='update_password'),
]
