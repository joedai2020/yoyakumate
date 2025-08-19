import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from ..models import Reservation, FacilityItem, Facility, Reservation
from ..forms import ManagementOffice, FacilityTimeSlot, SelectDateForm, SelectTimeSlotForm
from ..utils import clear_reservation_session

# 1. 管理所選択
@login_required
def select_office(request, reservation_id=None):
    error = None
    offices = ManagementOffice.objects.all()
    
    if reservation_id:
        reservation = get_object_or_404(Reservation, id=reservation_id, user=request.user)

        # 編集中の予約情報をセッションに保存
        request.session['editing_reservation_id'] = reservation.id
        request.session['selected_office'] = reservation.facilityItem.facility.office.id
        request.session['selected_facility'] = reservation.facilityItem.facility.id
        request.session['selected_item'] = reservation.facilityItem.id
        request.session['selected_date'] = str(reservation.date)

        # 予約の時間帯を取得しセッションに保存
        time_slot = FacilityTimeSlot.objects.filter(
            facility=reservation.facilityItem.facility,
            start_time=reservation.start_time,
            end_time=reservation.end_time
        ).first()
        
        if time_slot:
            request.session['selected_time_slot'] = str(time_slot.id)
        else:
            request.session.pop('selected_time_slot', None)

    # 編集モードでなければセッションをクリア
    if reservation_id is None:
        clear_reservation_session(request)

    # 管理所が1件だけなら自動選択して次へ遷移
    if offices.count() == 1:
        request.session['selected_office'] = offices.first().id
        return redirect('reservations:select_facility')

    # 編集モード時の処理
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
        # 新規予約モードの処理
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
            # 初回アクセス時は「今日＋1日」を初期値に設定
            tomorrow = today + datetime.timedelta(days=1)
            form = SelectDateForm(initial={'date': tomorrow})

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

    # 予約済み時間帯のstart_timeを取得（編集中の予約は除外）
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
    if reserved_count == 0:
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

    # 編集中の予約ID（編集モード判定）
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
                try:
                    reservation = Reservation.objects.get(id=editing_reservation_id)
                except ObjectDoesNotExist:
                    messages.error(request, '編集中の予約が見つかりません。')
                    clear_reservation_session(request)
                    return redirect('reservations:select_office')

                reservation.facilityItem = item
                reservation.date = selected_date
                reservation.start_time = time_slot.start_time
                reservation.end_time = time_slot.end_time
                reservation.user = request.user
                reservation.save()
                
                # 編集用セッションをクリア
                del request.session['editing_reservation_id']
            else:
                # 新規予約作成処理
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

# 予約削除
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
