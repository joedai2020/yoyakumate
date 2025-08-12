from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Count
from django.contrib.auth.decorators import login_required,user_passes_test
from django.db.models import Q
from ..models import Reservation, FacilityItem, Facility, Reservation
from ..forms import FacilityForm, FacilityItemForm, ReservationSearchForm, UserSearchForm, CustomUser, UserEditForm
from ..utils import is_manager, get_timeslot_formset

def manager_required(view_func):
    decorated_view_func = login_required(user_passes_test(is_manager)(view_func))
    return decorated_view_func

@manager_required
def manager_home(request):
    return render(request, 'reservations/manager_home.html')


# 設備管理開始
@manager_required
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
@manager_required
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


@manager_required
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


@manager_required
def facility_delete(request, pk):
    facility = get_object_or_404(Facility, pk=pk)
    if request.method == 'POST':
        facility.delete()
        return redirect('reservations:facility_list')

    return render(request, 'reservations/facility_confirm_delete.html', {
        'facility': facility
    })
    
#施設アイテム
@manager_required
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

@manager_required
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


@manager_required
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


@manager_required
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

@manager_required
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