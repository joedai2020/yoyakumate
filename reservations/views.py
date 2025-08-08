from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import UserRegisterForm, AdminRegisterForm
from .models import ManagementOffice, Facility, Reservation
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm

def root_redirect(request):
    if request.user.is_authenticated:
        return redirect('reservations:home')
    else:
        return redirect('reservations:login')

# ホームページ（予約一覧または管理所一覧）
@login_required
def home(request):
    # 登録ユーザーなら本人予約展示
    reservations = Reservation.objects.filter(user=request.user).order_by('-date', 'start_time')
    return render(request, 'reservations/home.html', {'reservations': reservations})

# 一般ユーザー登録
def register(request):
    if request.method == 'POST':
        submit_type = request.POST.get('submit_type')
        if submit_type == 'admin':
            admin_form = AdminRegisterForm(request.POST)
            normal_form = UserRegisterForm()  # 空表单
            if admin_form.is_valid():
                admin_form.save()
                messages.success(request, '管理者登録が完了しました。ログインしてください。')
                return redirect('reservations:login')
        else:
            normal_form = UserRegisterForm(request.POST)
            admin_form = AdminRegisterForm()  # 空表单
            if normal_form.is_valid():
                normal_form.save()
                messages.success(request, '一般ユーザー登録が完了しました。ログインしてください。')
                return redirect('reservations:login')
    else:
        normal_form = UserRegisterForm()
        admin_form = AdminRegisterForm()

    return render(request, 'reservations/register.html', {
        'normal_form': normal_form,
        'admin_form': admin_form,
    })

# ログイン
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('reservations:home')
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
