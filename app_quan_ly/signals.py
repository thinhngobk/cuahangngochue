from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import HoaDonBan, PhieuThu, HoaDonHoan, SoCaiCongNo,KhachHang
from .views.ledger_views import update_ledger
from django.db import transaction
from decimal import Decimal
@receiver(post_save, sender=HoaDonBan)
def ghi_so_hoa_don(sender, instance, created, **kwargs):
    """Tự động ghi sổ khi hóa đơn được duyệt"""
    if instance.trangthaidon == 'approved':
        # ✅ THÊM: Kiểm tra đã ghi sổ chưa
        if SoCaiCongNo.objects.filter(ma_chung_tu=instance.mahoadonban).exists():
            return
        
        update_ledger(
            khachhang=instance.khachhang,
            ma_ct=instance.mahoadonban,
            dien_giai=f"Bán hàng đơn {instance.mahoadonban}",
            tang=instance.tongtienphaithanhtoan,
            giam=0,
            ghi_chu=instance.ghichu or "",
            user=instance.user
        )

@receiver(pre_save, sender=PhieuThu)
def track_phieu_thu_status(sender, instance, **kwargs):
    """Lưu trạng thái cũ để so sánh"""
    if instance.pk:  # Nếu đang update (không phải tạo mới)
        try:
            old = PhieuThu.objects.get(pk=instance.pk)
            instance._old_status = old.trang_thai_duyet
        except PhieuThu.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=PhieuThu)
def ghi_so_phieu_thu(sender, instance, created, **kwargs):
    """Tự động ghi sổ khi phiếu thu được duyệt"""
    if instance.trang_thai_duyet == 'approved':
        if not SoCaiCongNo.objects.filter(ma_chung_tu=instance.maphieuthu).exists():
            with transaction.atomic():
                khach = instance.khachhang
                
                last_entry = SoCaiCongNo.objects.filter(
                    khachhang=khach
                ).select_for_update().order_by('-ngay_ghi_so', '-id').first()
                
                if last_entry:
                    no_hien_tai = Decimal(str(last_entry.du_no_tuc_thoi))
                else:
                    no_hien_tai = Decimal(str(khach.no_dau_ky))
                
                giam = Decimal(str(instance.sotienthu))
                no_moi = no_hien_tai - giam
                
                SoCaiCongNo.objects.create(
                    khachhang=khach,
                    ma_chung_tu=instance.maphieuthu,
                    dien_giai=f"Thu tiền {'đơn ' + instance.mahoadon if instance.mahoadon else 'nợ'}",
                    tang=0,
                    giam=giam,
                    du_no_tuc_thoi=no_moi,
                    user=instance.user,
                    ghichu=instance.ghichu or ""
                )
@receiver(post_save, sender=HoaDonHoan)
def ghi_so_hoan_hang(sender, instance, created, **kwargs):
    """Tự động ghi sổ khi hóa đơn hoàn được duyệt"""
    if instance.trangthaiduyet == 'approved':
        # ✅ THÊM: Kiểm tra đã ghi sổ chưa
        if SoCaiCongNo.objects.filter(ma_chung_tu=instance.mahoadonhoan).exists():
            return
        
        update_ledger(
            khachhang=instance.khachhang,
            ma_ct=instance.mahoadonhoan,
            dien_giai=f"Khách trả hàng đơn {instance.mahoadonhoan}",
            tang=0,
            giam=instance.tongtienhoan,
            ghi_chu=instance.lydohoan or "",
            user=instance.user
        )
@receiver(post_save, sender=KhachHang)
def ghi_so_no_dau_ky(sender, instance, created, **kwargs):
    """
    Ghi sổ nợ đầu kỳ khi tạo khách hàng mới
    """
    if created and instance.no_dau_ky > 0:
        if not SoCaiCongNo.objects.filter(
            khachhang=instance,
            ma_chung_tu=f"NĐKY-{instance.makhachhang}"
        ).exists():
            SoCaiCongNo.objects.create(
                khachhang=instance,
                ma_chung_tu=f"NĐKY-{instance.makhachhang}",
                dien_giai="Nợ đầu kỳ",
                tang=instance.no_dau_ky,
                giam=0,
                du_no_tuc_thoi=instance.no_dau_ky,
                user=instance.user,
                ghichu="Số dư ban đầu khi nhập khách hàng"
            )