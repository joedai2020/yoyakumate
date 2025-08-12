from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from datetime import date, timedelta
from django.db.models import Count
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ObjectDoesNotExist
import datetime
from .models import Reservation, FacilityItem, Facility, Reservation
from .forms import *
from .utils import get_timeslot_formset


def is_manager(user):
    return hasattr(user, 'managerprofile')

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

    # 只取当前用户的预约
    reservations = Reservation.objects.filter(user=user).select_related(
        'facilityItem__facility__office',  # 管理所
        'facilityItem__facility',                     # 施設
        'facilityItem'                                 # 設備
    )

    # 给每条记录增加一个 time_slot 属性方便模板显示
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


# Step 1: 
# 1. 管理所選択
@login_required
def select_office(request):
    offices = ManagementOffice.objects.all()

    if request.method == 'POST':
        office_id = request.POST.get('office_id')
        if offices.filter(id=office_id).exists():
            request.session['selected_office'] = office_id
            return redirect('reservations:select_facility')
        else:
            error = '有効な管理所を選択してください。'
            return render(request, 'reservations/select_office.html', {'offices': offices, 'error': error})

    return render(request, 'reservations/select_office.html', {'offices': offices})

# 2. 施設タイプ選択
@login_required
def select_facility(request):
    office_id = request.session.get('selected_office')
    if not office_id:
        return redirect('reservations:select_office')

    facilities = Facility.objects.filter(office_id=office_id)

    if request.method == 'POST':
        facility_id = request.POST.get('facility_id')
        if facilities.filter(id=facility_id).exists():
            request.session['selected_facility'] = facility_id
            return redirect('reservations:select_item')
        else:
            error = '有効な施設タイプを選択してください。'
            return render(request, 'reservations/select_facility.html', {'facilities': facilities, 'error': error})

    return render(request, 'reservations/select_facility.html', {'facilities': facilities})

# 3. 具体的な設備選択
@login_required
def select_item(request):
    facility_id = request.session.get('selected_facility')
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

    return render(request, 'reservations/select_item.html', {'items': items})

# 4. 日付選択
@login_required
def select_date(request):
    if not request.session.get('selected_item'):
        return redirect('reservations:select_item')

    if request.method == 'POST':
        form = SelectDateForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            today = datetime.date.today()
            if date < today:
                error = '過去の日付は選択できません。'
                return render(request, 'reservations/select_date.html', {'form': form, 'error': error})
            request.session['selected_date'] = str(date)
            return redirect('reservations:select_time_slot')
    else:
        form = SelectDateForm()

    return render(request, 'reservations/select_date.html', {'form': form})

# 5. 時間帯選択
@login_required
def select_time_slot(request):
    item_id = request.session.get('selected_item')
    selected_date = request.session.get('selected_date')

    if not (item_id and selected_date):
        return redirect('reservations:select_date')

    item = FacilityItem.objects.get(id=item_id)
    # 施設に紐づく時間帯を取得
    time_slots = FacilityTimeSlot.objects.filter(facility=item.facility).order_by('start_time')

    time_choices = [
        (str(ts.id), f"{ts.start_time.strftime('%H:%M')} - {ts.end_time.strftime('%H:%M')}")
        for ts in time_slots
    ]

    if request.method == 'POST':
        form = SelectTimeSlotForm(request.POST, time_choices=time_choices)
        if form.is_valid():
            request.session['selected_time_slot'] = form.cleaned_data['time_slot']
            return redirect('reservations:reserve_confirm')
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

    if request.method == 'POST':
        Reservation.objects.create(
            facilityItem=item,
            date=selected_date,
            start_time=time_slot.start_time,
            end_time=time_slot.end_time,
            user=request.user
        )
        # セッションをクリア
        for key in ['selected_office', 'selected_facility', 'selected_item', 'selected_date', 'selected_time_slot']:
            request.session.pop(key, None)

        return redirect('reservations:select_office')

    return render(request, 'reservations/reserve_confirm.html', {
        'office': office,
        'facility': facility,
        'item': item,
        'selected_date': selected_date,
        'time_slot': time_slot,
    })