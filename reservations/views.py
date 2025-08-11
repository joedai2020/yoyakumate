from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.utils.dateparse import parse_date
from .models import Reservation, FacilityTimeSlot, TemporaryReservationUser, FacilityItem
from .forms import UserRegisterForm, AdminRegisterForm, FacilityForm, FacilityItemForm
from .models import Facility, Reservation, ManagementOffice, FacilityTimeSlot
from .utils import get_timeslot_formset


def is_manager(user):
    return user.groups.filter(name='manager').exists()


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
    user = request.user
    reservations = Reservation.objects.filter(user=user)
    context = {
        'reservations': reservations,
    }
    return render(request, 'reservations/user_home.html', context)

@login_required
@user_passes_test(is_manager, login_url='reservations:user_home')
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
@user_passes_test(is_manager, login_url='reservations:user_home')
def facility_list(request):
    
    # データベースから全ての施設を取得し、名前順に並べる
    facilities = Facility.objects.annotate(
        item_count=Count('facilityitem')  # 'items'はFacilityItemのForeignKeyに付けたrelated_name
    ).order_by('name')

    # facility_list.html テンプレートを表示し、施設データを渡す
    return render(request, 'reservations/facility_list.html', {
        'facilities': facilities
    })

@login_required
@user_passes_test(is_manager, login_url='reservations:user_home')
def facility_create(request):
    office = request.user.managerprofile.office
    TimeSlotFormSet = get_timeslot_formset()
    if request.method == 'POST':
        form = FacilityForm(request.POST)
        formset = TimeSlotFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            facility = form.save(commit=False)
            facility.office = office
            facility.save()
            
            formset.instance = facility
            formset.save()
            return redirect('reservations:facility_list')
    else:
        form = FacilityForm()
        formset = TimeSlotFormSet()
        
    return render(request, 'reservations/facility_form.html', {
        'form': form,
        'formset': formset,
        'title': '施設タイプ追加',
        'office_name': office.name })


@login_required
@user_passes_test(is_manager, login_url='reservations:user_home')
def facility_edit(request, pk):
    facility = get_object_or_404(Facility, pk=pk)
    TimeSlotFormSet = get_timeslot_formset()

    if request.method == 'POST':
        form = FacilityForm(request.POST, instance=facility)
        formset = TimeSlotFormSet(request.POST, instance=facility)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('reservations:facility_list')
    else:
        form = FacilityForm(instance=facility)
        formset = TimeSlotFormSet(instance=facility)

    return render(request, 'reservations/facility_form.html', {
        'form': form,
        'formset': formset,
        'title': '施設タイプ編集',
        'office_name': facility.office.name,
    })


@login_required
@user_passes_test(is_manager, login_url='reservations:user_home')
def facility_delete(request, pk):
    facility = get_object_or_404(Facility, pk=pk)
    if request.method == 'POST':
        facility.delete()
        return redirect('reservations:facility_list')

    return render(request, 'reservations/facility_confirm_delete.html', {
        'facility': facility
    })
    
#施設アイテム
@login_required
def facility_item_list(request, facility_id):
    facility = get_object_or_404(Facility, id=facility_id)
    items = facility.facilityitem_set.all()  # related_name='items'
    return render(request, 'reservations/facility_item_list.html', {
        'facility': facility,
        'items': items
    })

@login_required
def facility_item_create(request, facility_id):
    facility = get_object_or_404(Facility, id=facility_id)
    if request.method == 'POST':
        form = FacilityItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.facility = facility
            item.save()
            return redirect('reservations:facility_item_list', facility_id=facility.id)
    else:
        form = FacilityItemForm()
    return render(request, 'reservations/facility_item_form.html', {
        'facility': facility,
        'form': form
    })

@login_required
def facility_item_edit(request, item_id):
    item = get_object_or_404(FacilityItem, id=item_id)
    if request.method == 'POST':
        form = FacilityItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            return redirect('reservations:facility_item_list', facility_id=item.facility.id)
    else:
        form = FacilityItemForm(instance=item)
    return render(request, 'reservations/facility_item_form.html', {
        'facility': item.facility,
        'form': form
    })

@login_required
def facility_item_delete(request, item_id):
    item = get_object_or_404(FacilityItem, id=item_id)
    facility_id = item.facility.id
    if request.method == 'POST':
        item.delete()
        return redirect('reservations:facility_item_list', facility_id=facility_id)
    return render(request, 'reservations/facility_item_confirm_delete.html', {
        'item': item
    })
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

def api_facilities(request):
    # 管理所IDをGETパラメータから取得
    office_id = request.GET.get('office_id')
    if not office_id:
        return JsonResponse({'facilities': []})

    # 指定管理所の設備一覧を取得
    facilities = Facility.objects.filter(office_id=office_id).order_by('name')
    
    result = []
    for facility in facilities:
        items = FacilityItem.objects.filter(facility=facility).values('id', 'item_name').order_by('item_name')
        result.append({
            'facility_id': facility.id,
            'facility_name': facility.name,
            'items': list(items)
        })
    
    return JsonResponse({'facilities': result})

def api_time_slots(request):
    facility_item_id = request.GET.get('facility_item_id')
    if not facility_item_id:
        return JsonResponse({'time_slots': []})

    slots = FacilityTimeSlot.objects.filter(facility_item_id=facility_item_id)
    time_slots_list = [{
        'id': slot.id,
        'label': f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}"
    } for slot in slots]

    return JsonResponse({'time_slots': time_slots_list})

@require_POST
@csrf_protect  # CSRFトークン検証を有効化
def create_reservation(request):
    # POSTデータ取得
    facility_id = request.POST.get('facility_id')
    date_str = request.POST.get('date')
    time_slot_id = request.POST.get('time_slot_id')

    # バリデーション: 必須パラメータチェック
    if not (facility_id and date_str and time_slot_id):
        return JsonResponse({'status': 'error', 'message': '必要なパラメータが不足しています。'}, status=400)

    # 日付フォーマットチェック
    date = parse_date(date_str)
    if date is None:
        return JsonResponse({'status': 'error', 'message': '予約日の日付形式が不正です。'}, status=400)

    # 過去日付予約不可チェック（現在日付と比較）
    from django.utils.timezone import localdate
    today = localdate()
    if date < today:
        return JsonResponse({'status': 'error', 'message': '過去の日付には予約できません。'}, status=400)

    # FacilityTimeSlotを取得
    try:
        time_slot = FacilityTimeSlot.objects.get(id=time_slot_id, facility_id=facility_id)
    except FacilityTimeSlot.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '指定された時間帯が存在しません。'}, status=404)

    # ログインユーザー判定
    if request.user.is_authenticated:
        user = request.user
        guest = None
    else:
        # 非登録ユーザー処理
        # 例としてメールアドレスをPOSTから受け取り一時ユーザー作成 or 取得
        guest_email = request.POST.get('guest_email')
        if not guest_email:
            return JsonResponse({'status': 'error', 'message': '非登録ユーザーはメールアドレスが必要です。'}, status=400)
        guest, created = TemporaryReservationUser.objects.get_or_create(email=guest_email)
        user = None

    # 予約重複チェック（同施設・同日・同時間帯）
    exists = Reservation.objects.filter(
        facility_id=facility_id,
        date=date,
        start_time=time_slot.start_time,
        end_time=time_slot.end_time,
    ).exists()
    if exists:
        return JsonResponse({'status': 'error', 'message': '同じ時間帯の予約がすでに存在します。'}, status=400)

    # 予約を作成
    reservation = Reservation.objects.create(
        facility_id=facility_id,
        date=date,
        start_time=time_slot.start_time,
        end_time=time_slot.end_time,
        user=user,
        guest=guest,
    )

    return JsonResponse({'status': 'success', 'reservation_id': reservation.id})