from django.forms import inlineformset_factory
from .models import Facility, FacilityTimeSlot
from .forms import FacilityTimeSlotForm,FacilityTimeSlotFormSet

def get_timeslot_formset(extra=5, can_delete=True):
    return inlineformset_factory(
        Facility, FacilityTimeSlot,
        form=FacilityTimeSlotForm,
        formset=FacilityTimeSlotFormSet,
        extra=extra,
        can_delete=can_delete
    )