from django.urls import path,re_path
from . import views

urlpatterns = [
    path('login/', views.login_user),
    path('register/', views.register),
    path('logout/', views.logout_user),
    path('',views.index),
    path('front_index/',views.front_index),
    path('rank/',views.rank),
    path('depot/',views.depot),
    re_path('depot-(?P<depot_type_ID>(\d+))-(?P<depot_region_ID>(\d+))-(?P<depot_time_ID>(\d+))', views.depot),
    path('movie/<int:uid>/details/', views.details, name='movie_details'),
    path('collect/', views.collect, name='collect'),  # path('collect/',views.collect),
    path('comment/add/', views.comment_add, name='comment_add'),
    path('recommend/',views.recommend),
    path('center/',views.center),
    path('board/add/',views.board_add),

    path('search_suggest/', views.search_suggest, name='search_suggest'),
    path('result/', views.search_result, name='search_result'),

    path('admin_index/', views.admin_index),
    path('movie/', views.movie),
    path('movie/add/', views.movie_add),
    path('movie/delete/', views.movie_delete),
    path('movie/detail/', views.movie_detail),
    path('movie/edit/', views.movie_edit),
    path('users/', views.users),
    path('users/delete/', views.users_delete),
    path('users/reset/', views.users_reset),
]
