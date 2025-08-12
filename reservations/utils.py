from django.forms import inlineformset_factory
from .models import Facility, FacilityTimeSlot
from .forms import FacilityTimeSlotForm,FacilityTimeSlotFormSet

def is_manager(user):
    return hasattr(user, 'managerprofile')

def get_timeslot_formset(extra=5, can_delete=True):
    return inlineformset_factory(
        Facility, FacilityTimeSlot,
        form=FacilityTimeSlotForm,
        formset=FacilityTimeSlotFormSet,
        extra=extra,
        can_delete=can_delete
    )

def clear_reservation_session(request):
    keys = ['selected_office', 'selected_facility', 'selected_item', 'selected_date', 'selected_time_slot']
    for key in keys:
        request.session.pop(key, None)