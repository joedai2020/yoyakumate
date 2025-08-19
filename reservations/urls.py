from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    # ホームページ（予約一覧など）
    path('', views.root_redirect, name='root_redirect'),  # 根路径重定向
    path('manager/home/', views.manager_home, name='manager_home'),
    path('user/home/', views.user_home, name='user_home'),
    path('users/manage/', views.user_manage, name='user_manage'),
    path('users/edit/<int:user_id>/', views.user_edit, name='user_edit'), 
    
    path('reservations/search/', views.reservation_search, name='reservation_search'),
    path('reservation_delete/<int:reservation_id>/', views.reservation_delete, name='reservation_delete'),

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
    path('select_office/', views.select_office, name='select_office'),
    path('select_office/<int:reservation_id>/', views.select_office, name='select_office_edit'),
    path('select_facility/', views.select_facility, name='select_facility'),
    path('select_item/', views.select_item, name='select_item'),
    path('select_date/', views.select_date, name='select_date'),
    path('select_time_slot/', views.select_time_slot, name='select_time_slot'),
    path('reserve_confirm/', views.reserve_confirm, name='reserve_confirm'),

    # ゲスト予約関連
    path('guest/reserve/', views.guest_reservation, name='guest_reservation'),
    path('guest/select_office/', views.guest_select_office, name='guest_select_office'),
    path('guest/select_facility/', views.guest_select_facility, name='guest_select_facility'),
    path('guest/select_item/', views.guest_select_item, name='guest_select_item'),
    path('guest/select_date/', views.guest_select_date, name='guest_select_date'),
    path('guest/select_time_slot/', views.guest_select_time_slot, name='guest_select_time_slot'),
    # ユーザー情報入力画面（guest_user_info）
    path('guest/user_info/', views.guest_user_info, name='guest_user_info'),

    # 予約確認画面（guest_reserve_confirm）
    path('guest/reserve_confirm/', views.guest_reserve_confirm, name='guest_reserve_confirm'),

    # 完了画面（guest_complete）
    path('guest/complete/', views.guest_complete, name='guest_complete'),

    # # ユーザー登録・ログイン
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
