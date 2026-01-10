from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import (
    KhachHang, SanPham, HoaDonBan, ChiTietHoaDonBan, 
    HoaDonHoan, PhieuThu, SoCaiCongNo
)

# 1. Inline Sổ Cái (Sổ nợ chi tiết)
class SoCaiCongNoInline(TabularInline):
    model = SoCaiCongNo
    extra = 0
    readonly_fields = ["ngay_ghi_so", "ma_chung_tu", "dien_giai", "tang", "giam", "du_no_tuc_thoi", "ghichu"]
    can_delete = False 
    # classes = ["tab-ledger"]

# 2. Inline Chi tiết hóa đơn
class ChiTietHoaDonInline(TabularInline):
    model = ChiTietHoaDonBan
    extra = 0

@admin.register(KhachHang)
class KhachHangAdmin(ModelAdmin):
    # Thêm is_active vào danh sách hiển thị
    list_display = ["makhachhang", "tenkhachhang", "phanloai", "sdt", "du_no_hien_tai_display", "is_active"]
    # Cho phép tích bật/tắt nhanh ngay tại trang danh sách
    list_editable = ["is_active"]
    search_fields = ["tenkhachhang", "tenkhachhangkhongdau", "makhachhang", "sdt"]
    # Thêm bộ lọc is_active bên phải
    list_filter = ["is_active", "phanloai"]
    readonly_fields = ["makhachhang", "tenkhachhangkhongdau", "du_no_hien_tai_display"]
    inlines = [SoCaiCongNoInline]

    def du_no_hien_tai_display(self, obj):
        return f"{int(obj.du_no_hien_tai):,} đ"
    du_no_hien_tai_display.short_description = "Dư nợ hiện tại"

@admin.register(SanPham)
class SanPhamAdmin(ModelAdmin):
    # Thêm is_active vào sản phẩm
    list_display = ["masanpham", "tensanpham", "donvitinh", "dongiaban", "tonkho", "is_active"]
    list_editable = ["is_active"]
    search_fields = ["tensanpham", "tensanphamkhongdau", "masanpham", "barcode"]
    list_filter = ["is_active", "donvitinh"]
    readonly_fields = ["masanpham", "tensanphamkhongdau"]

@admin.register(HoaDonBan)
class HoaDonBanAdmin(ModelAdmin):
    list_display = ["mahoadonban", "khachhang", "tongtienphaithanhtoan", "trangthaidon", "ngaytao"]
    list_filter = ["trangthaidon"]
    inlines = [ChiTietHoaDonInline]
    actions = ["duyet_nhanh_hoa_don"]

    # --- LỌC KHÁCH HÀNG KHI LẬP ĐƠN ---
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "khachhang":
            # Chỉ hiện khách hàng đang hoạt động trong ô chọn
            kwargs["queryset"] = KhachHang.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.action(description="Duyệt các hóa đơn đã chọn")
    def duyet_nhanh_hoa_don(self, request, queryset):
        count = 0
        for hd in queryset.filter(trangthaidon='pending'):
            hd.trangthaidon = 'approved'
            hd.save()
            count += 1
        self.message_user(request, f"Đã duyệt thành công {count} hóa đơn.")

@admin.register(PhieuThu)
class PhieuThuAdmin(ModelAdmin):
    list_display = ["maphieuthu", "khachhang", "sotienthu", "ngaylap"]
    search_fields = ["khachhang__tenkhachhang", "maphieuthu"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "khachhang":
            kwargs["queryset"] = KhachHang.objects.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(HoaDonHoan)
class HoaDonHoanAdmin(ModelAdmin):
    list_display = ["mahoadonhoan", "khachhang", "tongtienhoan", "trangthaiduyet"]
    list_filter = ["trangthaiduyet"]

@admin.register(SoCaiCongNo)
class SoCaiCongNoAdmin(admin.ModelAdmin):
    # 1. Thêm 'dien_giai' và 'ghichu' vào đây để nó hiện thành cột
    list_display = (
        'ngay_ghi_so', 
        'khachhang',
        'ma_chung_tu', 
        'dien_giai',   # Cột diễn giải
        'get_tang', 
        'get_giam', 
        'get_du_no',
        'ghichu'       # Cột ghi chú
    )
    
    # 2. Thêm thanh tìm kiếm và bộ lọc bên phải
    list_filter = ('khachhang', 'ngay_ghi_so')
    search_fields = ('ma_chung_tu', 'dien_giai', 'ghichu', 'khachhang__tenkhachhang')
    
    # 3. Định dạng số cho dễ đọc (ví dụ: 1,000,000)
    def get_tang(self, obj):
        return f"{int(obj.tang):,}"
    get_tang.short_description = 'Tăng (Nợ)'

    def get_giam(self, obj):
        return f"{int(obj.giam):,}"
    get_giam.short_description = 'Giảm (Trả)'

    def get_du_no(self, obj):
        return f"{int(obj.du_no_tuc_thoi):,}"
    get_du_no.short_description = 'Dư nợ lũy tiến'

    # 4. Sắp xếp mặc định: Mới nhất hiện lên đầu
    ordering = ('-ngay_ghi_so', '-id')