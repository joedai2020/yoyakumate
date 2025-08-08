from django.contrib import admin
from django.utils.crypto import get_random_string
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, ManagementOffice, Facility, ManagerProfile, TemporaryReservationUser, Reservation, InvitationCode

# カスタムユーザー管理
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'full_name', 'email', 'phone', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('個人情報', {'fields': ('full_name', 'email', 'phone')}),
        ('権限', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('重要日付', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'full_name', 'email', 'phone', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )
    search_fields = ('username', 'full_name', 'email')
    ordering = ('username',)

# 管理所管理
@admin.register(ManagementOffice)
class ManagementOfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')
    search_fields = ('name', 'address')

# 施設管理（麻雀、卓球など）
@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'office')
    list_filter = ('office',)
    search_fields = ('name',)

# 管理者プロフィール管理
@admin.register(ManagerProfile)
class ManagerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'office')
    search_fields = ('user__username', 'office__name')

# 非登録ユーザー管理
@admin.register(TemporaryReservationUser)
class TemporaryReservationUserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'email')
    search_fields = ('full_name', 'phone', 'email')

# 予約管理
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('facility', 'date', 'start_time', 'end_time', 'user', 'guest', 'created_at')
    list_filter = ('facility', 'date')
    search_fields = ('user__username', 'guest__full_name')

# 招待コード管理
@admin.register(InvitationCode)
class InvitationCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'community', 'is_used', 'created_at')
    list_filter = ('community', 'is_used')
    search_fields = ('code',)
    ordering = ('-created_at',)

    # 自动生成邀请码（可选）
    def save_model(self, request, obj, form, change):
        if not obj.code:
            obj.code = get_random_string(length=8).upper()
        super().save_model(request, obj, form, change)