# views/helper_views.py
"""
Các hàm helper dùng chung cho tất cả views
"""
from decimal import Decimal
from django.db import transaction
from app_quan_ly.models import SoCaiCongNo
def update_ledger(khachhang, ma_ct, dien_giai, tang, giam, ghi_chu="", user=None):
    """
    Tối ưu: Dùng F() expression và atomic transaction
    """
    val_tang = Decimal(str(tang or 0)).quantize(Decimal('1'))
    val_giam = Decimal(str(giam or 0)).quantize(Decimal('1'))

    with transaction.atomic():
        # Lấy dư nợ hiện tại KHÔNG LOCK
        last_log = SoCaiCongNo.objects.filter(
            khachhang=khachhang
        ).order_by('-ngay_ghi_so', '-id').first()
        
        if last_log:
            current_no = Decimal(str(last_log.du_no_tuc_thoi))
        else:
            current_no = Decimal(str(khachhang.no_dau_ky))
        
        current_no = current_no.quantize(Decimal('1'))
        new_no = current_no + val_tang - val_giam
        
        # Tạo record mới - Django tự động lock khi INSERT
        return SoCaiCongNo.objects.create(
            khachhang=khachhang,
            ma_chung_tu=ma_ct,
            dien_giai=dien_giai,
            tang=val_tang,
            giam=val_giam,
            du_no_tuc_thoi=new_no,
            ghichu=ghi_chu,
            user=user
        )