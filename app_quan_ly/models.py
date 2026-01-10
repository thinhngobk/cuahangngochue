from django.db import models, transaction
from django.db.models import Sum
from unidecode import unidecode
from django.utils import timezone
from django.contrib.auth.models import User
from datetime import datetime, date
import uuid            

class KhachHang(models.Model):
    
    PHAN_LOAI = [('SI', 'Sỉ'), ('LE', 'Lẻ')]
    
    makhachhang = models.CharField(max_length=15, unique=True, editable=False)
    tenkhachhang = models.CharField(max_length=255)
    tenkhachhangkhongdau = models.CharField(max_length=255, blank=True, editable=False)
    diachi = models.CharField(max_length=500, blank=True)
    sdt = models.CharField(max_length=20, blank=True)
    mst = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phanloai = models.CharField(max_length=2, choices=PHAN_LOAI, default='LE')
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")
    no_dau_ky = models.DecimalField(max_digits=15, decimal_places=0, default=0, help_text="Số nợ cũ trước khi dùng phần mềm")
    han_muc_no = models.DecimalField(max_digits=15, decimal_places=0, default=0, help_text="Giới hạn nợ tối đa cho phép")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ghichu = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if self.tenkhachhang:
            self.tenkhachhangkhongdau = unidecode(self.tenkhachhang).lower()
        if not self.makhachhang:
            import random
            while True:
                ma = f"KH{random.randint(10000, 99999)}"
                if not KhachHang.objects.filter(makhachhang=ma).exists():
                    self.makhachhang = ma
                    break
        super().save(*args, **kwargs)
    def __str__(self):
        sdt_str = f" - {self.sdt}" if self.sdt else ""
        diachi_str = f" ({self.diachi})" if self.diachi else ""
        return f"{self.tenkhachhang}{sdt_str}{diachi_str}"
    
    @property
    def tong_no_hoa_don(self):
        """Tổng phát sinh nợ từ các hóa đơn bán hàng đã duyệt"""
        return HoaDonBan.objects.filter(
            khachhang=self, 
            trangthaidon='approved'
        ).aggregate(total=Sum('tongtienphaithanhtoan'))['total'] or 0

    @property
    def tong_da_thanh_toan(self):
        """Tổng tất cả các khoản tiền khách đã trả (Phiếu thu)"""
        return PhieuThu.objects.filter(
            khachhang=self,
            trang_thai_duyet='approved'
        ).aggregate(total=Sum('sotienthu'))['total'] or 0

    @property
    def tong_gia_tri_tra_hang(self):
        """Tổng tiền được trừ nợ do trả hàng (Hóa đơn hoàn)"""
        return HoaDonHoan.objects.filter(
            khachhang=self, 
            trangthaiduyet='approved'
        ).aggregate(total=Sum('tongtienhoan'))['total'] or 0

    @property
    def du_no_hien_tai(self):
        """✅ Lấy dư nợ từ dòng cuối cùng của Sổ Cái - Có cache"""
        # Nếu chưa save (chưa có pk) → trả về nợ đầu kỳ
        if not self.pk:
            return self.no_dau_ky
        
        if not hasattr(self, '_cached_du_no'):
            last_entry = self.so_no_rieng.order_by('-ngay_ghi_so', '-id').first()
            self._cached_du_no = last_entry.du_no_tuc_thoi if last_entry else self.no_dau_ky
        return self._cached_du_no

    @property
    def trang_thai_no(self):
        """Cảnh báo nhanh về tình trạng nợ"""
        du_no = self.du_no_hien_tai
        if du_no > self.han_muc_no > 0:
            return "Vượt hạn mức"
        if du_no > 0:
            return "Đang nợ"
        if du_no < 0:
            return "Khách trả dư"
        return "Hết nợ"


class SanPham(models.Model):
    masanpham = models.CharField(max_length=15, unique=True, editable=False)
    barcode = models.CharField(max_length=100, blank=True)
    tensanpham = models.CharField(max_length=255)
    tensanphamkhongdau = models.CharField(max_length=255, blank=True, editable=False)
    donvitinh = models.CharField(max_length=50)
    dongiagoc = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    dongiaban = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    tonkho = models.IntegerField(default=0)
    ghichu = models.TextField(blank=True)
    ngaytao = models.DateTimeField(auto_now_add=True)
    ngaycapnhat = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Đang kinh doanh")
    
    def save(self, *args, **kwargs):
        if self.tensanpham:
            self.tensanphamkhongdau = unidecode(self.tensanpham).lower()
        if not self.masanpham:
            import random
            while True:
                ma = f"SP{random.randint(100000, 999999)}"
                if not SanPham.objects.filter(masanpham=ma).exists():
                    self.masanpham = ma
                    break
        super().save(*args, **kwargs)  # ← THÊM 8 SPACES (2 TAB)
    
    def __str__(self):
        return f"{self.masanpham} - {self.tensanpham}"
class HoaDonBan(models.Model):
    TRANG_THAI_DON = [
        ('pending', 'Chờ duyệt'), 
        ('approved', 'Đã duyệt'), 
        ('canceled', 'Hủy')
    ]
    
    class Meta:
        permissions = [
            ("approve_hoadonban", "Có thể duyệt hóa đơn bán"),
            ("cancel_hoadonban", "Có thể hủy hóa đơn bán"),
        ]
    
    mahoadonban = models.CharField(max_length=50, unique=True, editable=False)
    khachhang = models.ForeignKey(KhachHang, on_delete=models.PROTECT, related_name='hoadon_ban')
    chietkhauchung = models.DecimalField(max_digits=5, decimal_places=2, default=0) 
    tongtienphaithanhtoan = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    khachhangungtien = models.DecimalField(max_digits=15, decimal_places=0, default=0) 
    trangthaidon = models.CharField(max_length=10, choices=TRANG_THAI_DON, default='pending')
    ghichu = models.TextField(blank=True)
    ngaytao = models.DateTimeField(auto_now_add=True) # ngày tạo record vào hệ thống (hoá đơn bán ra ngày 1/1, ngày tạo bản ghi 5/1)
    ngaylap = models.DateField(default=date.today) # ngày xuất háo đơn thực tế
    ngaycapnhat = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if self.khachhangungtien:
            self.khachhangungtien = int(self.khachhangungtien)

        if not self.mahoadonban:
            import random
            local_now = timezone.localtime(timezone.now())
            ma_kh = self.khachhang.makhachhang if (self.khachhang and self.khachhang.makhachhang) else "KLE"
            ngay_str = local_now.strftime("%d%m%y")
            unique_id = uuid.uuid4().hex[:6].upper()  # Dùng UUID thay vì random
            
            self.mahoadonban = f"HDB-{ma_kh}-{ngay_str}-{unique_id}"
            # ✅ TĂNG từ 4 chữ số → 6 chữ số
            
        if self.pk:
            old_obj = HoaDonBan.objects.get(pk=self.pk)
            if old_obj.trangthaidon == 'approved':
                raise ValueError(f"Hóa đơn {self.mahoadonban} đã duyệt!")
        
        super().save(*args, **kwargs)

class ChiTietHoaDonBan(models.Model):
    hoadonban = models.ForeignKey(HoaDonBan, related_name='chitiet_ban', on_delete=models.CASCADE)
    sanpham = models.ForeignKey(SanPham, on_delete=models.PROTECT)
    tensanpham = models.CharField(max_length=255)
    donvitinh = models.CharField(max_length=50, null=True, blank=True)
    soluong = models.DecimalField(max_digits=10, decimal_places=2)
    dongiagoc = models.DecimalField(max_digits=15, decimal_places=0)
    dongiaban = models.DecimalField(max_digits=15, decimal_places=0)
    chietkhau = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    thanhtien = models.DecimalField(max_digits=15, decimal_places=0)
    ghichu = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)


class HoaDonHoan(models.Model):
    TRANG_THAI_DUYET = [('pending', 'Chờ duyệt'), ('approved', 'Đã duyệt'), ('canceled', 'Hủy')]
    
    class Meta:
        permissions = [
            ("approve_hoadonhoan", "Có thể duyệt đơn hoàn"),
            ("cancel_hoadonhoan", "Có thể hủy đơn hoàn"),
        ]
    
    mahoadonhoan = models.CharField(max_length=50, unique=True, editable=False)
    khachhang = models.ForeignKey(KhachHang, on_delete=models.PROTECT, related_name='hoadon_hoan')
    trangthaiduyet = models.CharField(max_length=10, choices=TRANG_THAI_DUYET, default='pending')
    tongtienhoan = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    lydohoan = models.TextField(blank=True)
    ngaylap = models.DateField(default=date.today) 
    ngayduyet = models.DateTimeField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.mahoadonhoan:

            
            # Tạo mã hoàn hàng
            local_now = timezone.localtime(timezone.now())
            ma_kh = self.khachhang.makhachhang if self.khachhang else "KLE"
            ngay_str = local_now.strftime("%d%m%y")
            unique_id = uuid.uuid4().hex[:6].upper()  # Dùng UUID thay vì random
            
            self.mahoadonhoan = f"HHG-{ma_kh}-{ngay_str}-{unique_id}"
            # Ví dụ: HHG-KH1172-090126-A3F2B8
        
        super().save(*args, **kwargs)


class ChiTietHoaDonHoan(models.Model):
    hoadonhoan = models.ForeignKey(HoaDonHoan, related_name='chitiet_hoan', on_delete=models.CASCADE)
    sanpham = models.ForeignKey(SanPham, on_delete=models.PROTECT)
    tensanpham = models.CharField(max_length=255)
    donvitinh = models.CharField(max_length=50)
    soluong = models.DecimalField(max_digits=10, decimal_places=2)
    dongiagoc = models.DecimalField(max_digits=15, decimal_places=0)
    dongialucban = models.DecimalField(max_digits=15, decimal_places=0)
    chietkhau = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    thanhtien = models.DecimalField(max_digits=15, decimal_places=0)
    ghichu = models.CharField(max_length=255, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)


class PhieuThu(models.Model):
    TRANG_THAI_DUYET = [
        ('pending', 'Chờ duyệt'), 
        ('approved', 'Đã duyệt'), 
        ('canceled', 'Hủy')
    ]
    
    class Meta:
        permissions = [
            ("approve_phieuthu", "Có thể duyệt phiếu thu"),
            ("cancel_phieuthu", "Có thể hủy phiếu thu"),
        ]
    
    maphieuthu = models.CharField(max_length=20, unique=True, editable=False)
    mahoadon = models.CharField(max_length=20, blank=True)
    khachhang = models.ForeignKey(KhachHang, on_delete=models.PROTECT)
    ngaylap = models.DateTimeField(auto_now_add=True)
    nguoi_lap = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='phieu_thu_da_lap'
    )
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    sotienthu = models.DecimalField(max_digits=15, decimal_places=0)
    hinhthucthanhtoan = models.CharField(max_length=100, default='Tiền mặt')
    ghichu = models.TextField(blank=True)
    trang_thai_duyet = models.CharField(
        max_length=20, 
        choices=TRANG_THAI_DUYET, 
        default='pending'
    )

    def save(self, *args, **kwargs):
        if not self.maphieuthu:
            import uuid
            from django.utils import timezone
            
            # Nếu có HĐ → Tạo mã dựa trên HĐ
            if self.mahoadon:
                if isinstance(self.mahoadon, str):
                    ma_hd = self.mahoadon
                else:
                    ma_hd = self.mahoadon.mahoadonban
                
                # Đếm số phiếu thu của HĐ này
                so_phieu = PhieuThu.objects.filter(mahoadon=ma_hd).count() + 1
                self.maphieuthu = f"PT-{ma_hd}-{so_phieu:02d}"
            else:
                # Không có HĐ → Dùng UUID
                local_now = timezone.localtime(timezone.now())
                ngay_str = local_now.strftime("%d%m%y")
                unique_id = uuid.uuid4().hex[:4].upper()
                
                self.maphieuthu = f"PT-{ngay_str}-{unique_id}"
                # Ví dụ: PT-090126-A3F2
        
        super().save(*args, **kwargs)
class SoCaiCongNo(models.Model):
    khachhang = models.ForeignKey(KhachHang, on_delete=models.CASCADE, related_name='so_no_rieng')
    ngay_ghi_so = models.DateTimeField(auto_now_add=True)
    ma_chung_tu = models.CharField(max_length=50)
    dien_giai = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    tang = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    giam = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    du_no_tuc_thoi = models.DecimalField(max_digits=15, decimal_places=0, default=0)
    ghichu = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['ngay_ghi_so', 'id']
        indexes = [
            models.Index(fields=['khachhang', '-ngay_ghi_so', '-id']),
            models.Index(fields=['ma_chung_tu']),
        ]