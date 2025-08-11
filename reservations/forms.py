from django import forms
from django.forms.models import BaseInlineFormSet
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, InvitationCode, Facility, FacilityTimeSlot, ManagerProfile, FacilityItem

# 一般用户登録フォーム
class UserRegisterForm(UserCreationForm):
    full_name = forms.CharField(label="氏名", widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(label="電話番号", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="メールアドレス", widget=forms.EmailInput(attrs={'class': 'form-control'}))

    password1 = forms.CharField(label="パスワード", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="パスワード（確認）", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'full_name', 'phone', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

# 管理者登録フォーム（招待コード必要）
class AdminRegisterForm(UserCreationForm):
    invitation_code = forms.CharField(
        label="招待コード",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    full_name = forms.CharField(label="氏名", widget=forms.TextInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(label="電話番号", widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label="メールアドレス", widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ['username', 'full_name', 'phone', 'email', 'password1', 'password2', 'invitation_code']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def clean_invitation_code(self):
        code = self.cleaned_data['invitation_code']
        try:
            inv = InvitationCode.objects.get(code=code, is_used=False)
        except InvitationCode.DoesNotExist:
            raise forms.ValidationError("無効な招待コードです。")
        return inv

    def save(self, commit=True):
        user = super().save(commit=False)
        invitation = self.cleaned_data['invitation_code']

        if commit:
            user.save()
            ManagerProfile.objects.create(user=user, office=invitation.community)
            invitation.is_used = True
            invitation.save()

        return user


class FacilityForm(forms.ModelForm):

    class Meta:
        model = Facility
        fields = ['name', 'description']  # 必要に応じてフィールドを調整

class FacilityTimeSlotForm(forms.ModelForm):
    start_time = forms.TimeField(
        widget=forms.TimeInput(
            format='%H:%M',
            attrs={'type': 'time', 'step': 3600}  # 只能选整点
        ),
        label='開始時間'
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(
            format='%H:%M',
            attrs={'type': 'time', 'step': 3600}
        ),
        label='終了時間'
    )

    class Meta:
        model = FacilityTimeSlot
        fields = ['start_time', 'end_time']

    def clean_start_time(self):
        start = self.cleaned_data.get('start_time')
        if start.minute != 0 or start.second != 0:
            raise ValidationError('開始時間の分は00分でなければなりません。')
        return start

    def clean_end_time(self):
        end = self.cleaned_data.get('end_time')
        if end.minute != 0 or end.second != 0:
            raise ValidationError('終了時間の分は00分でなければなりません。')
        return end

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end = cleaned_data.get('end_time')
        if start and end and start >= end:
            raise ValidationError('終了時間は開始時間より後でなければなりません。')

class FacilityTimeSlotFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        time_ranges = []
        for form in self.forms:
            if form.cleaned_data.get('DELETE', False):
                continue
            start = form.cleaned_data.get('start_time')
            end = form.cleaned_data.get('end_time')
            if not start or not end:
                continue
            for s, e in time_ranges:
                if (start < e and end > s):
                    raise ValidationError('時間帯が重複しています。')
            time_ranges.append((start, end))


class FacilityItemForm(forms.ModelForm):
    class Meta:
        model = FacilityItem
        fields = ['item_name', 'description']