from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    # ホームページ（予約一覧など）
    path('', views.root_redirect, name='root_redirect'),  # 根路径重定向
    path('manager/home/', views.manager_home, name='manager_home'),
    path('user/home/', views.user_home, name='user_home'),

    # # コミュニティ（管理所）一覧・詳細
    # path('communities/', views.community_list, name='community_list'),
    # path('community/<int:pk>/', views.community_detail, name='community_detail'),

    # # 施設（麻将、棋牌、乒乓など）一覧・詳細
    path('facilities/', views.facility_list, name='facility_list'),
    path('create/', views.facility_create, name='facility_create'),    # 施設追加
    path('edit/<int:pk>/', views.facility_edit, name='facility_edit'), # 施設編集
    path('delete/<int:pk>/', views.facility_delete, name='facility_delete'), # 施設削除
    
    # 設備（FacilityItem）
    path('facilities/<int:facility_id>/items/', views.facility_item_list, name='facility_item_list'),
    path('facilities/<int:facility_id>/items/create/', views.facility_item_create, name='facility_item_create'),
    path('facility-items/<int:item_id>/edit/', views.facility_item_edit, name='facility_item_edit'),
    path('facility-items/<int:item_id>/delete/', views.facility_item_delete, name='facility_item_delete'),

    # # スケジュール関連
    # path('schedule/<int:pk>/', views.schedule_detail, name='schedule_detail'),

    # # 予約関連
    path('reservation/list/', views.reservation_list, name='reservation_list'),
    path('api/facilities/', views.api_facilities, name='api_facilities'),
    path('api/time_slots/', views.api_time_slots, name='api_time_slots'),
    path('reservations/create/', views.create_reservation, name='create_reservation'),

    # # ユーザー登録・ログイン
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
