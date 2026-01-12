# app_quan_ly/migrations/0002_create_groups_and_permissions.py
"""
Migration tạo 3 groups: Staff, Manager, Admin và phân quyền
Chạy SAU KHI đã migrate models (0001_initial.py)
"""

from django.db import migrations
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def create_groups_and_permissions(apps, schema_editor):
    """Tạo groups và gán permissions"""
    
    # Lấy models
    HoaDonBan = apps.get_model('app_quan_ly', 'HoaDonBan')
    HoaDonHoan = apps.get_model('app_quan_ly', 'HoaDonHoan')
    PhieuThu = apps.get_model('app_quan_ly', 'PhieuThu')
    KhachHang = apps.get_model('app_quan_ly', 'KhachHang')
    SanPham = apps.get_model('app_quan_ly', 'SanPham')
    
    # Tạo groups
    group_staff, _ = Group.objects.get_or_create(name='Staff')
    group_manager, _ = Group.objects.get_or_create(name='Manager')
    group_admin, _ = Group.objects.get_or_create(name='Admin')
    
    print("\n" + "="*60)
    print("✅ Đã tạo 3 groups: Staff, Manager, Admin")
    print("="*60)
    
    # Lấy ContentTypes
    ct_hoadonban = ContentType.objects.get_for_model(HoaDonBan)
    ct_hoadonhoan = ContentType.objects.get_for_model(HoaDonHoan)
    ct_phieuthu = ContentType.objects.get_for_model(PhieuThu)
    ct_khachhang = ContentType.objects.get_for_model(KhachHang)
    ct_sanpham = ContentType.objects.get_for_model(SanPham)
    
    # ================================================================
    # PHÂN QUYỀN CHO STAFF
    # ================================================================
    staff_perms = [
        # Hóa đơn bán: Xem, Tạo, Sửa (KHÔNG Duyệt, Hủy, Xóa)
        Permission.objects.get(codename='view_hoadonban', content_type=ct_hoadonban),
        Permission.objects.get(codename='add_hoadonban', content_type=ct_hoadonban),
        Permission.objects.get(codename='change_hoadonban', content_type=ct_hoadonban),
        
        # Hóa đơn hoàn: Xem, Tạo, Sửa
        Permission.objects.get(codename='view_hoadonhoan', content_type=ct_hoadonhoan),
        Permission.objects.get(codename='add_hoadonhoan', content_type=ct_hoadonhoan),
        Permission.objects.get(codename='change_hoadonhoan', content_type=ct_hoadonhoan),
        
        # Phiếu thu: Xem, Tạo, Sửa
        Permission.objects.get(codename='view_phieuthu', content_type=ct_phieuthu),
        Permission.objects.get(codename='add_phieuthu', content_type=ct_phieuthu),
        Permission.objects.get(codename='change_phieuthu', content_type=ct_phieuthu),
        
        # Khách hàng: Full CRUD
        Permission.objects.get(codename='view_khachhang', content_type=ct_khachhang),
        Permission.objects.get(codename='add_khachhang', content_type=ct_khachhang),
        Permission.objects.get(codename='change_khachhang', content_type=ct_khachhang),
        Permission.objects.get(codename='delete_khachhang', content_type=ct_khachhang),
        
        # Sản phẩm: Full CRUD
        Permission.objects.get(codename='view_sanpham', content_type=ct_sanpham),
        Permission.objects.get(codename='add_sanpham', content_type=ct_sanpham),
        Permission.objects.get(codename='change_sanpham', content_type=ct_sanpham),
        Permission.objects.get(codename='delete_sanpham', content_type=ct_sanpham),
    ]
    
    group_staff.permissions.set(staff_perms)
    print(f"✅ Staff: Đã gán {len(staff_perms)} quyền")
    
    # ================================================================
    # PHÂN QUYỀN CHO MANAGER
    # ================================================================
    manager_perms = [
        # Hóa đơn bán: FULL
        Permission.objects.get(codename='view_hoadonban', content_type=ct_hoadonban),
        Permission.objects.get(codename='add_hoadonban', content_type=ct_hoadonban),
        Permission.objects.get(codename='change_hoadonban', content_type=ct_hoadonban),
        Permission.objects.get(codename='delete_hoadonban', content_type=ct_hoadonban),
        Permission.objects.get(codename='approve_hoadonban', content_type=ct_hoadonban),
        Permission.objects.get(codename='cancel_hoadonban', content_type=ct_hoadonban),
        
        # Hóa đơn hoàn: FULL
        Permission.objects.get(codename='view_hoadonhoan', content_type=ct_hoadonhoan),
        Permission.objects.get(codename='add_hoadonhoan', content_type=ct_hoadonhoan),
        Permission.objects.get(codename='change_hoadonhoan', content_type=ct_hoadonhoan),
        Permission.objects.get(codename='delete_hoadonhoan', content_type=ct_hoadonhoan),
        Permission.objects.get(codename='approve_hoadonhoan', content_type=ct_hoadonhoan),
        Permission.objects.get(codename='cancel_hoadonhoan', content_type=ct_hoadonhoan),
        
        # Phiếu thu: FULL
        Permission.objects.get(codename='view_phieuthu', content_type=ct_phieuthu),
        Permission.objects.get(codename='add_phieuthu', content_type=ct_phieuthu),
        Permission.objects.get(codename='change_phieuthu', content_type=ct_phieuthu),
        Permission.objects.get(codename='delete_phieuthu', content_type=ct_phieuthu),
        Permission.objects.get(codename='approve_phieuthu', content_type=ct_phieuthu),
        Permission.objects.get(codename='cancel_phieuthu', content_type=ct_phieuthu),
        
        # Khách hàng: FULL
        Permission.objects.get(codename='view_khachhang', content_type=ct_khachhang),
        Permission.objects.get(codename='add_khachhang', content_type=ct_khachhang),
        Permission.objects.get(codename='change_khachhang', content_type=ct_khachhang),
        Permission.objects.get(codename='delete_khachhang', content_type=ct_khachhang),
        
        # Sản phẩm: FULL
        Permission.objects.get(codename='view_sanpham', content_type=ct_sanpham),
        Permission.objects.get(codename='add_sanpham', content_type=ct_sanpham),
        Permission.objects.get(codename='change_sanpham', content_type=ct_sanpham),
        Permission.objects.get(codename='delete_sanpham', content_type=ct_sanpham),
    ]
    
    group_manager.permissions.set(manager_perms)
    print(f"✅ Manager: Đã gán {len(manager_perms)} quyền")
    
    # ================================================================
    # ADMIN GROUP (quyền từ is_superuser)
    # ================================================================
    group_admin.permissions.set(manager_perms)
    print(f"✅ Admin: Group đã tạo (quyền thực tế từ is_superuser=True)")
    
    print("\n" + "="*60)
    print("✅ HOÀN TẤT!")
    print("="*60)
    print("\n📋 Tóm tắt:")
    print("   • Staff: Xem + Tạo + Sửa (16 quyền)")
    print("   • Manager: Full quyền (28 quyền)")
    print("   • Admin: Superuser (full quyền)")
    print("\nBước tiếp theo:")
    print("   python manage.py create_sample_users")
    print()


def reverse_func(apps, schema_editor):
    """Xóa groups khi rollback"""
    Group.objects.filter(name__in=['Staff', 'Manager', 'Admin']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('app_quan_ly', '0001_initial'),  # Chạy sau migration tạo models
    ]

    operations = [
        migrations.RunPython(create_groups_and_permissions, reverse_func),
    ]
