from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, InvitationCode, ManagementOffice, Facility

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
        return inv  # 直接返回 InvitationCode 对象

    def save(self, commit=True):
        user = super().save(commit=False)
        invitation = self.cleaned_data['invitation_code']  # 已经是 InvitationCode 对象

        if commit:
            user.save()
            # 绑定管理所到 ManagerProfile
            from .models import ManagerProfile
            ManagerProfile.objects.create(user=user, office=invitation.community)
            # 标记邀请码已使用
            invitation.is_used = True
            invitation.save()

        return user


class FacilityForm(forms.ModelForm):

    class Meta:
        model = Facility
        fields = ['office', 'name', 'description']  # 必要に応じてフィールドを調整