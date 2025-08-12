import pytz, datetime
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from django.urls import reverse
from urllib.parse import urlencode
from ..forms import AdminRegisterForm, UserRegisterForm

# ログイン処理
def login_view(request):
    # JST（日本標準時）の現在時刻を取得
    jst = pytz.timezone('Asia/Tokyo')
    now_jst = timezone.now().astimezone(jst)
    now_hour = now_jst.hour
    params = {'now_hour': now_hour}

    # すでにログインしている場合はホームにリダイレクト
    if request.user.is_authenticated:
        if hasattr(request.user, 'managerprofile'):
            url = reverse('reservations:manager_home') + '?' + urlencode(params)
            return redirect(url)
        else:
            url = reverse('reservations:user_home') + '?' + urlencode(params)
            return redirect(url)

    # POSTメソッドの場合、フォームのバリデーションを行う
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # 管理者かどうか判定し、遷移先を分ける
            if hasattr(user, 'managerprofile'):
                return render(request, 'reservations/manager_home.html', {'now_hour': now_hour})
            else:
                url = reverse('reservations:user_home') + '?' + urlencode(params)
                return redirect(url)
        else:
            messages.error(request, 'ユーザー名かパスワードが正しくありません。')
    else:
        form = AuthenticationForm()

    # ログインページを表示
    return render(request, 'reservations/login.html', {'form': form})

# ログアウト
@login_required
def logout_view(request):
    logout(request)
    return redirect('reservations:login')

def root_redirect(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'managerprofile'):
            return redirect('reservations:manager_home')
        else:
            return redirect('reservations:user_home')
    else:
        return redirect('reservations:login')


# ユーザー登録
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