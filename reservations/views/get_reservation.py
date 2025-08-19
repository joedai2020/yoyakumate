from datetime import date, timedelta
from django.shortcuts import render, redirect
from ..models import FacilityItem, Facility ,TemporaryReservationUser, Reservation, FacilityTimeSlot
from ..forms import ManagementOffice, GuestDateForm, GuestTimeSlotForm, GuestUserForm
from ..utils import clear_guest_reservation_session

def guest_reservation(request):
    # セッション初期化（非登録ユーザー用）
    clear_guest_reservation_session(request)
    return redirect('reservations:guest_select_office')

def guest_select_office(request):
    error = None
    offices = ManagementOffice.objects.all()

    # セッション初期化（非登録ユーザー用）
    clear_guest_reservation_session(request)

    # 管理所が1件だけなら自動選択して次へ遷移
    if offices.count() == 1:
        request.session['guest_selected_office'] = offices.first().id
        return redirect('reservations:guest_select_facility')

    # POST処理（選択された管理所を保存）
    if request.method == 'POST':
        office_id = request.POST.get('office_id')
        if offices.filter(id=office_id).exists():
            request.session['guest_selected_office'] = office_id
            return redirect('reservations:guest_select_facility')
        else:
            error = '有効な管理所を選択してください。'
            return render(request, 'reservations/guest/get_select_office.html', {
                'offices': offices,
                'error': error,
                'selected_office': None,
            })

    selected_office = request.session.get('guest_selected_office')

    return render(request, 'reservations/guest/get_select_office.html', {
        'offices': offices,
        'error': error,
        'selected_office': int(selected_office) if selected_office else None,
    })

def guest_select_facility(request):
    offices = ManagementOffice.objects.all()
    single_office = (offices.count() == 1)

    office_id = request.session.get('guest_selected_office')
    if not office_id:
        return redirect('reservations:guest_select_office')

    selected_facility = request.session.get('guest_selected_facility')
    facilities = Facility.objects.filter(office_id=office_id)
    error = None

    if request.method == 'POST':
        facility_id = request.POST.get('facility_id')
        if facilities.filter(id=facility_id).exists():
            request.session['guest_selected_facility'] = facility_id
            return redirect('reservations:guest_select_item')
        else:
            error = '有効な施設タイプを選択してください。'

    context = {
        'facilities': facilities,
        'single_office': single_office,
        'selected_facility': int(selected_facility) if selected_facility else None,
        'error': error,
    }
    return render(request, 'reservations/guest/get_select_facility.html', context)

def guest_select_item(request):
    facility_id = request.session.get('guest_selected_facility')
    if not facility_id:
        return redirect('reservations:guest_select_facility')

    items = FacilityItem.objects.filter(facility_id=facility_id)
    selected_item = request.session.get('guest_selected_item')
    error = None

    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        if items.filter(id=item_id).exists():
            request.session['guest_selected_item'] = item_id
            return redirect('reservations:guest_select_date')
        else:
            error = '有効な設備を選択してください。'

    return render(request, 'reservations/guest/get_select_item.html', {
        'items': items,
        'selected_item': int(selected_item) if selected_item else None,
        'error': error,
    })


def guest_select_date(request):
    selected_date = request.session.get('guest_selected_date')
    error = None

    if request.method == 'POST':
        form = GuestDateForm(request.POST)
        if form.is_valid():
            request.session['guest_selected_date'] = str(form.cleaned_data['date'])
            return redirect('reservations:guest_select_time_slot')
        else:
            error = '日付を正しく選択してください。'
    else:        
        # 初期値が未設定なら、今日＋1日を使う
        if not selected_date:
            selected_date = (date.today() + timedelta(days=1)).isoformat()
        form = GuestDateForm(initial={'date': selected_date})


    return render(request, 'reservations/guest/get_select_date.html', {
        'form': form,
        'error': error,
        'min_date': form.fields['date'].widget.attrs['min'],
        'max_date': form.fields['date'].widget.attrs['max'],
    })

def guest_select_time_slot(request):
    facility_id = request.session.get('guest_selected_facility')
    if not facility_id:
        return redirect('reservations:guest_select_facility')

    selected_slot = request.session.get('guest_selected_time_slot')
    error = None

    if request.method == 'POST':
        form = GuestTimeSlotForm(facility_id, request.POST)
        if form.is_valid():
            request.session['guest_selected_time_slot'] = form.cleaned_data['time_slot'].id
            return redirect('reservations:guest_user_info')
        else:
            error = '時間帯を選択してください。'
    else:
        form = GuestTimeSlotForm(facility_id, initial={'time_slot': selected_slot})

    return render(request, 'reservations/guest/get_select_time_slot.html', {
        'form': form,
        'error': error,
    })

def guest_user_info(request):
    error = None

    if request.method == 'POST':
        form = GuestUserForm(request.POST)
        if form.is_valid():
            guest = TemporaryReservationUser.objects.create(
                full_name=form.cleaned_data['full_name'],
                phone=form.cleaned_data['phone'],
                email=form.cleaned_data['email']
            )
            request.session['guest_guest_user_info'] = form.cleaned_data
            return redirect('reservations:guest_reserve_confirm')
        else:
            error = 'すべての項目を正しく入力してください。'
    else:
        form = GuestUserForm()

    return render(request, 'reservations/guest/get_user_info.html', {
        'form': form,
        'error': error,
    })

def guest_reserve_confirm(request):
    office_id = request.session.get('guest_selected_office')
    facility_id = request.session.get('guest_selected_facility')
    item_id = request.session.get('guest_selected_item')
    selected_date = request.session.get('guest_selected_date')
    time_slot_id = request.session.get('guest_selected_time_slot')
    guest_info = request.session.get('guest_guest_user_info', {})

    if not all([office_id, facility_id, item_id, selected_date, time_slot_id, guest_info]):
        return redirect('reservations:guest_select_office')

    office = ManagementOffice.objects.get(id=office_id)
    facility = Facility.objects.get(id=facility_id)
    item = FacilityItem.objects.get(id=item_id)
    time_slot = FacilityTimeSlot.objects.get(id=time_slot_id)

    if request.method == 'POST':
        already_reserved = Reservation.objects.filter(
            facilityItem=item,
            date=selected_date,
            start_time=time_slot.start_time,
            end_time=time_slot.end_time
        ).exists()

        if already_reserved:
            error = '選択された日時は既に予約されています。別の時間帯または設備を選択してください。'
            return render(request, 'reservations/guest/reserve_confirm.html', {
                'office': office,
                'facility': facility,
                'item': item,
                'selected_date': selected_date,
                'time_slot': time_slot,
                'guest_info': guest_info,
                'error': error,
            })

        # 新規予約作成（非登録ユーザー）
        guest_info = request.session.get('guest_guest_user_info', {})

        guest_user = TemporaryReservationUser.objects.create(
            full_name=guest_info.get('full_name', 'ゲスト'),
            phone=guest_info.get('phone', ''),
            email=guest_info.get('email', '')
        )

        Reservation.objects.create(
            facilityItem=item,
            date=selected_date,
            start_time=time_slot.start_time,
            end_time=time_slot.end_time,
            user=None,
            guest=guest_user  # ✅ ForeignKey にオブジェクトを渡す
        )

        clear_guest_reservation_session(request)
        return redirect('reservations:guest_complete')

    return render(request, 'reservations/guest/get_reserve_confirm.html', {
        'office': office,
        'facility': facility,
        'item': item,
        'selected_date': selected_date,
        'time_slot': time_slot,
        'guest_info': guest_info,
    })


def guest_complete(request):
    # セッションはすでに clear_reservation_session() でクリア済みの想定
    return render(request, 'reservations/guest/complete.html')
