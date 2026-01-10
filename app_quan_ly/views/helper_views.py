# views/helper_views.py
"""
Các hàm helper dùng chung cho tất cả views
"""
from decimal import Decimal
from django.db import transaction
from app_quan_ly.models import SoCaiCongNo


def update_ledger(khachhang, ma_ct, dien_giai, tang, giam, ghi_chu="", user=None):
    """
    Hàm cập nhật sổ cái công nợ thủ công
    
    Args:
        khachhang: Đối tượng KhachHang
        ma_ct: Mã chứng từ (HDB-xxx, PT-xxx, HDH-xxx)
        dien_giai: Diễn giải giao dịch
        tang: Số tiền nợ tăng
        giam: Số tiền nợ giảm
        ghi_chu: Ghi chú bổ sung
        user: User thực hiện (request.user)
        
    Returns:
        SoCaiCongNo object đã tạo
    """
    # 1. Ép kiểu và làm tròn về số nguyên (Decimal)
    val_tang = Decimal(str(tang or 0)).quantize(Decimal('1'))
    val_giam = Decimal(str(giam or 0)).quantize(Decimal('1'))

    # 2. Sử dụng transaction và select_for_update để chống sai số dư
    with transaction.atomic():
        # Tìm bản ghi cuối cùng của khách hàng này để lấy số dư hiện tại
        last_log = SoCaiCongNo.objects.filter(
            khachhang=khachhang
        ).select_for_update().order_by('-ngay_ghi_so', '-id').first()
        
        # 3. Xác định dư nợ gốc để bắt đầu tính toán
        if last_log:
            current_no = Decimal(str(last_log.du_no_tuc_thoi))
        else:
            # Nếu khách chưa từng có giao dịch, lấy nợ đầu kỳ
            current_no = Decimal(str(khachhang.no_dau_ky))
        
        current_no = current_no.quantize(Decimal('1'))
        
        # 4. Tính dư nợ mới: Dư cũ + Tăng - Giảm
        new_no = current_no + val_tang - val_giam
        
        # 5. Lưu dòng nhật ký mới vào bảng SoCaiCongNo
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