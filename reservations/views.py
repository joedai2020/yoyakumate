import pytz, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.db.models import Count
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.urls import reverse
from django.db.models import Q
from urllib.parse import urlencode
from .models import Reservation, FacilityItem, Facility, Reservation
from .forms import *
from .utils import get_timeslot_formset, clear_reservation_session


def is_manager(user):
    return hasattr(user, 'managerprofile')

def root_redirect(request):
    if request.user.is_authenticated:
        try:
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
    now = timezone.now()

    reservations = Reservation.objects.filter(
        user=user
    ).filter(
        Q(date__gt=now.date()) |
        Q(date=now.date(), end_time__gt=now.time())
    ).select_related(
        'facilityItem__facility__office',
        'facilityItem__facility',
        'facilityItem'
    )

    for r in reservations:
        r.time_slot = f"{r.start_time.strftime('%H:%M')} - {r.end_time.strftime('%H:%M')}"
        r.office = r.facilityItem.facility.office
        r.facility = r.facilityItem.facility
        r.facility_item = r.facilityItem

    context = {
        'reservations': reservations,
    }
    return render(request, 'reservations/user_home.html', context)

@login_required
@user_passes_test(is_manager)
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
    jst = pytz.timezone('Asia/Tokyo')
    now_jst = timezone.now().astimezone(jst)
    now_hour = now_jst.hour
    params = {'now_hour': now_hour}
    
    if request.user.is_authenticated:
        if hasattr(request.user, 'managerprofile'):
            
            url = reverse('reservations:manager_home') + '?' + urlencode(params)
            return redirect(url)
        else:
            url = reverse('reservations:user_home') + '?' + urlencode(params)
            return redirect(url)

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            
            # 判断是否是管理者
            if hasattr(user, 'managerprofile'):
                return render(request, 'reservations/manager_home.html', {'now_hour': now_hour})
            else:
                params = {'now_hour': now_hour}
                url = reverse('reservations:user_home') + '?' + urlencode(params)
                return redirect(url)
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
@user_passes_test(is_manager, login_url='reservations:user_home')
def facility_item_list(request, facility_id):
    facility = get_object_or_404(Facility, id=facility_id)
    items = facility.facilityitem_set.all()  # related_name='items'
    return render(request, 'reservations/facility_item_list.html', {
        'facility': facility,
        'items': items
    })

@login_required
@user_passes_test(is_manager, login_url='reservations:user_home')
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
@user_passes_test(is_manager, login_url='reservations:user_home')
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
@user_passes_test(is_manager, login_url='reservations:user_home')
def facility_item_delete(request, item_id):
    item = get_object_or_404(FacilityItem, id=item_id)
    facility_id = item.facility.id
    if request.method == 'POST':
        item.delete()
        return redirect('reservations:facility_item_list', facility_id=facility_id)
    return render(request, 'reservations/facility_item_confirm_delete.html', {
        'item': item
    })


@login_required
@user_passes_test(is_manager, login_url='reservations:user_home')
def reservation_search(request):
    form = ReservationSearchForm(request.GET or None)
    reservations = []
    
    if form.is_valid():
        reservations = Reservation.objects.all()
        
        name = form.cleaned_data.get('name')
        phone = form.cleaned_data.get('phone')
        email = form.cleaned_data.get('email')

        q_user = Q()
        q_guest = Q()

        if name:
            q_user &= Q(user__full_name__startswith=name)
            q_guest &= Q(guest__full_name__startswith=name)
        if phone:
            q_user &= Q(user__phone__startswith=phone)
            q_guest &= Q(guest__phone__startswith=phone)
        if email:
            q_user &= Q(user__email__startswith=email)
            q_guest &= Q(guest__email__startswith=email)

        if any([name, phone, email]):
            reservations = reservations.filter(q_user | q_guest)

        date_from = form.cleaned_data.get('date_from')
        
        if date_from:
            reservations = reservations.filter(date__gte=date_from)
    context = {
        'form': form,
        'reservations': reservations,
    }
    return render(request, 'reservations/reservation_search.html', context)


@login_required
@user_passes_test(is_manager, login_url='reservations:user_home')
def user_manage(request):
    form = UserSearchForm(request.GET or None)
    users = CustomUser.objects.filter(is_superuser=False).exclude(id=request.user.id) 

    if form.is_valid():
        full_name = form.cleaned_data.get('full_name')
        phone = form.cleaned_data.get('phone')
        email = form.cleaned_data.get('email')

        if full_name:
            users = users.filter(full_name__icontains=full_name)
        if phone:
            users = users.filter(phone__icontains=phone)
        if email:
            users = users.filter(email__icontains=email)

    users = users.order_by('full_name')

    return render(request, 'reservations/user_manage.html', {
        'form': form,
        'users': users,
    })

@login_required
def user_edit(request, user_id):
    user_obj = get_object_or_404(CustomUser, id=user_id, is_superuser=False)

    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'ユーザー情報を更新しました。')
            return redirect('reservations:user_manage')
    else:
        form = UserEditForm(instance=user_obj)

    return render(request, 'reservations/user_edit.html', {
        'form': form,
        'user_obj': user_obj,
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


# Step 1: 
# 1. 管理所選択
@login_required
def select_office(request, reservation_id=None):

    error = None
    offices = ManagementOffice.objects.all()
    
    if reservation_id:
        reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)

        request.session['editing_reservation_id'] = reservation.id
        request.session['selected_office'] = reservation.facilityItem.facility.office.id
        request.session['selected_facility'] = reservation.facilityItem.facility.id
        request.session['selected_item'] = reservation.facilityItem.id
        request.session['selected_date'] = str(reservation.date)

        time_slot = FacilityTimeSlot.objects.filter(
            facility=reservation.facilityItem.facility,
            start_time=reservation.start_time,
            end_time=reservation.end_time
        ).first()
        
        if time_slot:
            request.session['selected_time_slot'] = str(time_slot.id)
        else:
            request.session.pop('selected_time_slot', None)

    # 管理所が1件だけなら自動選択して次へリダイレクト
    if offices.count() == 1:
        request.session['selected_office'] = offices.first().id
        
        # 編集モードなら編集用の予約情報もセットする処理は後述
        return redirect('reservations:select_facility')

    # セッションクリアは編集モードでなければ行う
    if reservation_id is None:
        clear_reservation_session(request)

    # 編集モード処理
    if reservation_id:

        if request.method == 'POST':
            office_id = request.POST.get('office_id')
            if offices.filter(id=office_id).exists():
                request.session['selected_office'] = office_id
                return redirect('reservations:select_facility')
            else:
                error = '有効な管理所を選択してください。'
                return render(request, 'reservations/select_office.html', {
                    'offices': offices,
                    'error': error,
                    'selected_office': int(request.session.get('selected_office')),
                })

    else:
        # 新規予約モード
        if request.method == 'POST':
            office_id = request.POST.get('office_id')
            if offices.filter(id=office_id).exists():
                request.session['selected_office'] = office_id
                request.session.pop('editing_reservation_id', None)
                return redirect('reservations:select_facility')
            else:
                error = '有効な管理所を選択してください。'
                return render(request, 'reservations/select_office.html', {
                    'offices': offices,
                    'error': error,
                    'selected_office': None,
                })

    selected_office = request.session.get('selected_office')
    
    return render(request, 'reservations/select_office.html', {
        'offices': offices,
        'error': error,
        'selected_office': int(selected_office) if selected_office else None,
    })

# 2. 施設タイプ選択
@login_required
def select_facility(request):
    
    offices = ManagementOffice.objects.all()
    single_office = (offices.count() == 1)
    
    office_id = request.session.get('selected_office')
    
    if not office_id:
        return redirect('reservations:select_office')

    selected_facility = request.session.get('selected_facility')
    
    facilities = Facility.objects.filter(office_id=office_id)

    if request.method == 'POST':
        facility_id = request.POST.get('facility_id')
        if facilities.filter(id=facility_id).exists():
            request.session['selected_facility'] = facility_id
            return redirect('reservations:select_item')
        else:
            error = '有効な施設タイプを選択してください。'
            return render(request, 'reservations/select_facility.html', {'facilities': facilities, 'error': error})

    context = {
        'facilities': facilities,
        'single_office': single_office,
        'selected_facility': int(selected_facility) if selected_facility else None,
    }
    return render(request, 'reservations/select_facility.html', context)

# 3. 具体的な設備選択
@login_required
def select_item(request):
    facility_id = request.session.get('selected_facility')
    selected_item = request.session.get('selected_item')
    if not facility_id:
        return redirect('reservations:select_facility')

    items = FacilityItem.objects.filter(facility_id=facility_id)

    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        if items.filter(id=item_id).exists():
            request.session['selected_item'] = item_id
            return redirect('reservations:select_date')
        else:
            error = '有効な設備を選択してください。'
            return render(request, 'reservations/select_item.html', {'items': items, 'error': error})

    context = {
        'items': items,
        'selected_item': int(selected_item) if selected_item else None,
    }
    return render(request, 'reservations/select_item.html', context)

# 4. 日付選択
@login_required
def select_date(request):
    if not request.session.get('selected_item'):
        return redirect('reservations:select_item')

    today = datetime.date.today()
    max_date = today + datetime.timedelta(days=6)

    if request.method == 'POST':
        form = SelectDateForm(request.POST)
        if form.is_valid():
            selected_date = form.cleaned_data['date']
            if selected_date < today:
                error = '過去の日付は選択できません。'
                return render(request, 'reservations/select_date.html', {
                    'form': form,
                    'error': error,
                    'min_date': today.isoformat(),
                    'max_date': max_date.isoformat(),
                })
            if selected_date > max_date:
                error = '選択できるのは今日から1週間以内の日付です。'
                return render(request, 'reservations/select_date.html', {
                    'form': form,
                    'error': error,
                    'min_date': today.isoformat(),
                    'max_date': max_date.isoformat(),
                })
            request.session['selected_date'] = str(selected_date)
            return redirect('reservations:select_time_slot')
    else:
        initial_date = request.session.get('selected_date')
        if initial_date:
            form = SelectDateForm(initial={'date': initial_date})
        else:
            form = SelectDateForm()

    return render(request, 'reservations/select_date.html', {
        'form': form,
        'min_date': today.isoformat(),
        'max_date': max_date.isoformat(),
    })

# 5. 時間帯選択
@login_required
def select_time_slot(request):
    item_id = request.session.get('selected_item')
    selected_date = request.session.get('selected_date')

    if not (item_id and selected_date):
        return redirect('reservations:select_date')

    item = FacilityItem.objects.get(id=item_id)

    # 編集中の予約IDをセッションから取得（なければ None）
    editing_reservation_id = request.session.get('editing_reservation_id')

    # 予約済み時間帯のstart_timeを取得。編集中の予約は除外する。
    reserved_qs = Reservation.objects.filter(
        facilityItem__facility=item.facility,
        date=selected_date,
    )
    if editing_reservation_id:
        reserved_qs = reserved_qs.exclude(id=editing_reservation_id)

    reserved_start_times = set(reserved_qs.values_list('start_time', flat=True))

    all_time_slots = FacilityTimeSlot.objects.filter(facility=item.facility).order_by('start_time')

    available_time_slots = [ts for ts in all_time_slots if ts.start_time not in reserved_start_times]

    reserved_count = len(all_time_slots) - len(available_time_slots)
    if reserved_count > 0:
        messages.info(request, f"{reserved_count}件の時間帯はすでに予約されています。")

    time_choices = [
        (str(ts.id), f"{ts.start_time.strftime('%H:%M')} - {ts.end_time.strftime('%H:%M')}")
        for ts in available_time_slots
    ]

    if request.method == 'POST':
        form = SelectTimeSlotForm(request.POST, time_choices=time_choices)
        if form.is_valid():
            request.session['selected_time_slot'] = form.cleaned_data['time_slot']
            return redirect('reservations:reserve_confirm')
    else:
        initial_time_slot = request.session.get('selected_time_slot')
        if initial_time_slot:
            form = SelectTimeSlotForm(time_choices=time_choices, initial={'time_slot': initial_time_slot})
        else:
            form = SelectTimeSlotForm(time_choices=time_choices)

    return render(request, 'reservations/select_time_slot.html', {'form': form})

# 6. 予約確認・保存
@login_required
def reserve_confirm(request):
    office_id = request.session.get('selected_office')
    facility_id = request.session.get('selected_facility')
    item_id = request.session.get('selected_item')
    selected_date = request.session.get('selected_date')
    time_slot_id = request.session.get('selected_time_slot')

    if not all([office_id, facility_id, item_id, selected_date, time_slot_id]):
        return redirect('reservations:select_office')

    office = ManagementOffice.objects.get(id=office_id)
    facility = Facility.objects.get(id=facility_id)
    item = FacilityItem.objects.get(id=item_id)
    time_slot = FacilityTimeSlot.objects.get(id=time_slot_id)

    # 編集中の予約ID（編集モードかどうか判定）
    editing_reservation_id = request.session.get('editing_reservation_id')

    if request.method == 'POST':

        # 予約済みチェック（編集中の自分の予約は除外）
        already_reserved_qs = Reservation.objects.filter(
            facilityItem=item,
            date=selected_date,
            start_time=time_slot.start_time,
            end_time=time_slot.end_time
        )
        if editing_reservation_id:
            already_reserved_qs = already_reserved_qs.exclude(id=editing_reservation_id)
        already_reserved = already_reserved_qs.exists()

        if already_reserved:
            error = '選択された日時は既に予約されています。別の時間帯または設備を選択してください。'

            return render(request, 'reservations/reserve_confirm.html', {
                'office': office,
                'facility': facility,
                'item': item,
                'selected_date': selected_date,
                'time_slot': time_slot,
                'error': error,
            })
        else:
            if editing_reservation_id:
                # 既存予約の更新
                reservation = Reservation.objects.get(id=editing_reservation_id)
                reservation.facilityItem = item
                reservation.date = selected_date
                reservation.start_time = time_slot.start_time
                reservation.end_time = time_slot.end_time
                reservation.user = request.user
                reservation.save()
                
                # 編集用セッションはクリア
                del request.session['editing_reservation_id']
            else:
                # 新規予約作成
                Reservation.objects.create(
                    facilityItem=item,
                    date=selected_date,
                    start_time=time_slot.start_time,
                    end_time=time_slot.end_time,
                    user=request.user
                )

            # セッションをクリア
            clear_reservation_session(request)

        return redirect('reservations:user_home')

    return render(request, 'reservations/reserve_confirm.html', {
        'office': office,
        'facility': facility,
        'item': item,
        'selected_date': selected_date,
        'time_slot': time_slot,
    })

@login_required
def reservation_delete(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)

    if request.method == 'POST':
        reservation.delete()
        messages.success(request, '予約を削除しました。')
        return redirect('reservations:user_home')

    # GETの場合は削除確認画面を表示
    return render(request, 'reservations/reservation_confirm_delete.html', {
        'reservation': reservation,
    })