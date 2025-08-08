from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    # ホームページ（予約一覧など）
    path('', views.root_redirect, name='root_redirect'),  # 根路径重定向
    path('home/', views.home, name='home'),  # /home/

    # # コミュニティ（管理所）一覧・詳細
    # path('communities/', views.community_list, name='community_list'),
    # path('community/<int:pk>/', views.community_detail, name='community_detail'),

    # # 施設（麻将、棋牌、乒乓など）一覧・詳細
    # path('facilities/', views.facility_list, name='facility_list'),
    # path('facility/<int:pk>/', views.facility_detail, name='facility_detail'),

    # # スケジュール関連
    # path('schedule/<int:pk>/', views.schedule_detail, name='schedule_detail'),

    # # 予約関連
    # path('reservation/create/<int:schedule_id>/', views.reservation_create, name='reservation_create'),
    # path('reservation/list/', views.reservation_list, name='reservation_list'),
    # path('reservation/update/<int:pk>/', views.reservation_update, name='reservation_update'),
    # path('reservation/delete/<int:pk>/', views.reservation_delete, name='reservation_delete'),

    # # ユーザー登録・ログイン
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
