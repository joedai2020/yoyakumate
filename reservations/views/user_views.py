import pytz, datetime
from django.shortcuts import render 
from django.contrib.auth.decorators import login_required,user_passes_test
from django.utils import timezone
from django.db.models import Q
from ..models import Reservation

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