from django.contrib import admin
from django.utils.crypto import get_random_string
from django.contrib.auth.admin import UserAdmin
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import (
    CustomUser, ManagementOffice, Facility, ManagerProfile,
    TemporaryReservationUser, Reservation, InvitationCode
)

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

@admin.register(ManagementOffice)
class ManagementOfficeAdmin(admin.ModelAdmin):
    list_display = ('name', 'address')
    search_fields = ('name', 'address')

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'office')
    list_filter = ('office',)
    search_fields = ('name',)

@admin.register(ManagerProfile)
class ManagerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'office')
    search_fields = ('user__username', 'office__name')

@admin.register(TemporaryReservationUser)
class TemporaryReservationUserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone', 'email')
    search_fields = ('full_name', 'phone', 'email')

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('facilityItem', 'date', 'start_time', 'end_time', 'user', 'guest', 'created_at')
    list_filter = ('facilityItem', 'date')
    search_fields = ('user__username', 'guest__full_name')

@admin.register(InvitationCode)
class InvitationCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'community', 'is_used', 'created_at')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('generate/', self.admin_site.admin_view(self.generate_code_view), name='reservations_invitationcode_generate'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['generate_url'] = reverse('admin:reservations_invitationcode_generate')
        return super().changelist_view(request, extra_context=extra_context)

    def generate_code_view(self, request):
        if request.method == 'POST':
            community_id = request.POST.get('community')
            try:
                community = ManagementOffice.objects.get(pk=community_id)
            except ManagementOffice.DoesNotExist:
                messages.error(request, "管理所が見つかりません。")
                return redirect('admin:reservations_invitationcode_generate')

            code = get_random_string(length=8).upper()
            InvitationCode.objects.create(code=code, community=community)
            messages.success(request, f"{community.name}の招待コード「{code}」を生成しました。")
            return redirect('admin:reservations_invitationcode_changelist')

        communities = ManagementOffice.objects.all()
        context = dict(
            self.admin_site.each_context(request),
            communities=communities,
        )
        return render(request, 'admin/invitationcode_generate.html', context)
