from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import UserRegisterForm, AdminRegisterForm, FacilityForm
from .models import ManagementOffice, Facility, Reservation
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ObjectDoesNotExist

def root_redirect(request):
    if request.user.is_authenticated:
        try:
            # 如果存在 ManagerProfile，则是管理者
            if hasattr(request.user, 'managerprofile'):
                return redirect('reservations:manager_home')
            else:
                return redirect('reservations:user_home')
        except ObjectDoesNotExist:
            return redirect('reservations:user_home')
    else:
        return redirect('reservations:login')

# ホームページ（予約一覧または管理所一覧）
@login_required
def user_home(request):
    # 登録ユーザーなら本人予約展示
    reservations = Reservation.objects.filter(user=request.user).order_by('-date', 'start_time')
    return render(request, 'reservations/home.html', {'reservations': reservations})

@login_required
def manager_home(request):
    return render(request, 'reservations/manager_home.html')

# 一般ユーザー登録
def register(request):
    if request.method == 'POST':
        user_type = request.POST.get('user_type', 'user')  # POSTのuser_typeを取得（なければ'user'）
        if user_type == 'admin':
            admin_form = AdminRegisterForm(request.POST)
            normal_form = UserRegisterForm()
            if admin_form.is_valid():
                admin_form.save()
                messages.success(request, '管理者登録が完了しました。ログインしてください。')
                return redirect('reservations:login')
        else:
            normal_form = UserRegisterForm(request.POST)
            admin_form = AdminRegisterForm()
            if normal_form.is_valid():
                normal_form.save()
                messages.success(request, '一般ユーザー登録が完了しました。ログインしてください。')
                return redirect('reservations:login')
    else:
        user_type = 'user'  # デフォルト値
        normal_form = UserRegisterForm()
        admin_form = AdminRegisterForm()

    return render(request, 'reservations/register.html', {
        'normal_form': normal_form,
        'admin_form': admin_form,
        'user_type': user_type,  # テンプレートに渡す
    })

# ログイン
def login_view(request):
    
    # すでにログインしている場合はホームにリダイレクト
    if request.user.is_authenticated:
        if hasattr(request.user, 'managerprofile'):
            return redirect('reservations:manager_home')
        else:
            return redirect('reservations:user_home')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # 判断是否是管理者
            if hasattr(user, 'managerprofile'):
                return render(request, 'reservations/manager_home.html')
            else:
                return redirect('reservations:user_home')
        else:
            messages.error(request, 'ユーザー名かパスワードが正しくありません。')
    else:
        form = AuthenticationForm()

    return render(request, 'reservations/login.html', {'form': form})

# ログアウト
@login_required
def logout_view(request):
    logout(request)
    return redirect('reservations:login')

# 設備管理開始
@login_required  # ログインユーザーのみアクセス可能
def facility_list(request):
    
    # データベースから全ての施設を取得し、名前順に並べる
    facilities = Facility.objects.all().order_by('name')

    # facility_list.html テンプレートを表示し、施設データを渡す
    return render(request, 'reservations/facility_list.html', {
        'facilities': facilities
    })

@login_required
def facility_create(request):
    if request.method == 'POST':
        form = FacilityForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('reservations:facility_list')
    else:
        form = FacilityForm()
    return render(request, 'reservations/facility_form.html', {'form': form, 'title': '施設追加'})

@login_required
def facility_edit(request, pk):
    facility = get_object_or_404(Facility, pk=pk)
    if request.method == 'POST':
        form = FacilityForm(request.POST, instance=facility)
        if form.is_valid():
            form.save()
            return redirect('reservations:facility_list')
    else:
        form = FacilityForm(instance=facility)
    return render(request, 'reservations/facility_form.html', {'form': form, 'title': '施設編集'})

@login_required
def facility_delete(request, pk):
    facility = get_object_or_404(Facility, pk=pk)
    if request.method == 'POST':
        facility.delete()
        return redirect('reservations:facility_list')
    return render(request, 'reservations/facility_confirm_delete.html', {'facility': facility})
# 設備管理終了


@login_required  # ログインユーザーのみアクセス可能
def reservation_list(request):
    user = request.user

    # 管理者ユーザーの場合
    if hasattr(user, 'managerprofile'):
        # 管理者が管理する管理組合を取得
        managed_office = user.managerprofile.management_office
        # 管理組合の施設に紐づく予約を取得し、開始時間の降順で並べる
        reservations = Reservation.objects.filter(facility__management_office=managed_office).order_by('-start_time')

    else:
        # 一般ユーザーの場合は、自分の予約のみ取得
        reservations = Reservation.objects.filter(user=user).order_by('-start_time')

    # 予約一覧テンプレートをレンダリングし、予約データを渡す
    return render(request, 'reservations/reservation_list.html', {
        'reservations': reservations,
    })