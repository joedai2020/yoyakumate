from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# カスタムユーザー（登録ユーザー用）
class CustomUser(AbstractUser):
    full_name = models.CharField(max_length=100, verbose_name="氏名")
    phone = models.CharField(max_length=20, verbose_name="電話番号")
    email = models.EmailField(verbose_name="メールアドレス", unique=True)

    def __str__(self):
        return self.full_name


# 管理所モデル（複数の施設を持つ）
class ManagementOffice(models.Model):
    name = models.CharField(max_length=100, verbose_name="管理所名")
    address = models.CharField(max_length=200, verbose_name="住所", blank=True)

    def __str__(self):
        return self.name


# 施設タイプ 管理所の施設（麻雀・卓球など）
class Facility(models.Model):
    office = models.ForeignKey(ManagementOffice, on_delete=models.CASCADE, verbose_name="管理所")
    name = models.CharField(max_length=100, verbose_name="施設名")
    description = models.TextField(blank=True, verbose_name="説明")

    def __str__(self):
        return f"{self.office.name} - {self.name}"

# 具体的な施設（例：卓球台1号、麻雀卓2号など）
class FacilityItem(models.Model):
    # 施設タイプ
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, verbose_name="施設タイプ")
    # 施設の識別名（例：1号台、2号卓など）
    item_name = models.CharField(max_length=100, verbose_name="施設識別名")
    
    description = models.TextField(blank=True, verbose_name="説明")

    def __str__(self):
        return f"{self.facility.name} - {self.item_name}"

# 施設ごとの利用時間帯
class FacilityTimeSlot(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, verbose_name="施設")
    start_time = models.TimeField(verbose_name="開始時間")
    end_time = models.TimeField(verbose_name="終了時間")

    def __str__(self):
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"


# 管理者プロフィール（管理所に紐づく）
class ManagerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    office = models.ForeignKey(ManagementOffice, on_delete=models.CASCADE, verbose_name="担当管理所")

    def __str__(self):
        return f"{self.user.username}（{self.office.name}の管理者）"


# 非登録ユーザー（予約時に記録される）
class TemporaryReservationUser(models.Model):
    full_name = models.CharField(max_length=100, verbose_name="氏名")
    phone = models.CharField(max_length=20, verbose_name="電話番号")
    email = models.EmailField(verbose_name="メールアドレス")

    def __str__(self):
        return self.full_name


# 予約モデル（登録・非登録ユーザー共通）
class Reservation(models.Model):
    facilityItem = models.ForeignKey(FacilityItem, on_delete=models.CASCADE, null=True, blank=True,verbose_name="施設")
    date = models.DateField(verbose_name="予約日")
    start_time = models.TimeField(verbose_name="開始時間")
    end_time = models.TimeField(verbose_name="終了時間")

    user = models.ForeignKey('CustomUser', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="登録ユーザー")
    guest = models.ForeignKey('TemporaryReservationUser', null=True, blank=True, on_delete=models.SET_NULL, verbose_name="非登録ユーザー")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    class Meta:
        verbose_name = "予約"
        verbose_name_plural = "予約"
        ordering = ['-date', 'start_time']

    def __str__(self):
        return f"{self.date} {self.facility} {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"

    
    
class InvitationCode(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name="招待コード")
    community = models.ForeignKey(ManagementOffice, on_delete=models.CASCADE, verbose_name="管理所")
    is_used = models.BooleanField(default=False, verbose_name="使用済み")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    def __str__(self):
        return f"{self.code} - {self.community.name}"

