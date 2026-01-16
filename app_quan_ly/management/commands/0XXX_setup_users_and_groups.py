from django.db import migrations
from django.contrib.auth.hashers import make_password

def setup_initial_data(apps, schema_editor):
    """
    Tạo dữ liệu ban đầu:
    1. 3 Users: admin, quanly, ketoan
    2. 3 Groups: Admin, Manager, Staff
    3. Gán users vào groups
    4. Set permissions cho groups
    """
    User = apps.get_model('auth', 'User')
    Group = apps.get_model('auth', 'Group')
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    
    print("\n" + "="*60)
    print("🚀 KHỞI TẠO DỮ LIỆU BAN ĐẦU")
    print("="*60)
    
    # ===== 1. TẠO 3 USERS =====
    print("\n📦 Tạo users...")
    
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@geminipos.com',
            'password': make_password('admin123'),
            'is_staff': True,
            'is_superuser': True,
            'first_name': 'Admin',
            'last_name': 'System'
        },
        {
            'username': 'quanly',
            'email': 'quanly@geminipos.com',
            'password': make_password('quanly123'),
            'is_staff': True,
            'is_superuser': False,
            'first_name': 'Quản lý',
            'last_name': 'Cửa hàng'
        },
        {
            'username': 'ketoan',
            'email': 'ketoan@geminipos.com',
            'password': make_password('ketoan123'),
            'is_staff': True,
            'is_superuser': False,
            'first_name': 'Kế toán',
            'last_name': 'Viên'
        },
    ]
    
    created_users = {}
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults=user_data
        )
        created_users[user_data['username']] = user
        status = "✅ Tạo mới" if created else "ℹ️  Đã tồn tại"
        print(f"  {status}: {user_data['username']}")
    
    # ===== 2. TẠO 3 GROUPS =====
    print("\n📦 Tạo groups...")
    
    admin_group, created = Group.objects.get_or_create(name='Admin')
    print(f"  {'✅ Tạo mới' if created else 'ℹ️  Đã tồn tại'}: Admin")
    
    manager_group, created = Group.objects.get_or_create(name='Manager')
    print(f"  {'✅ Tạo mới' if created else 'ℹ️  Đã tồn tại'}: Manager")
    
    staff_group, created = Group.objects.get_or_create(name='Staff')
    print(f"  {'✅ Tạo mới' if created else 'ℹ️  Đã tồn tại'}: Staff")
    
    # ===== 3. GÁN USERS VÀO GROUPS =====
    print("\n📦 Gán users vào groups...")
    
    created_users['admin'].groups.add(admin_group)
    print("  ✅ admin → Admin group")
    
    created_users['quanly'].groups.add(manager_group)
    print("  ✅ quanly → Manager group")
    
    created_users['ketoan'].groups.add(staff_group)
    print("  ✅ ketoan → Staff group")
    
    # ===== 4. SET PERMISSIONS CHO GROUPS =====
    print("\n📦 Cấu hình permissions...")
    
    try:
        # Lấy ContentType của models
        hoadonban_ct = ContentType.objects.get(app_label='app_quan_ly', model='hoadonban')
        khachhang_ct = ContentType.objects.get(app_label='app_quan_ly', model='khachhang')
        sanpham_ct = ContentType.objects.get(app_label='app_quan_ly', model='sanpham')
        phieuthu_ct = ContentType.objects.get(app_label='app_quan_ly', model='phieuthu')
        
        # --- ADMIN: Toàn quyền ---
        admin_perms = Permission.objects.filter(
            content_type__in=[hoadonban_ct, khachhang_ct, sanpham_ct, phieuthu_ct]
        )
        admin_group.permissions.set(admin_perms)
        print(f"  ✅ Admin: {admin_perms.count()} permissions")
        
        # --- MANAGER: Duyệt đơn, quản lý ---
        manager_perms = Permission.objects.filter(
            content_type__in=[hoadonban_ct, khachhang_ct, phieuthu_ct],
            codename__in=[
                'view_hoadonban', 'add_hoadonban', 'change_hoadonban',
                'view_khachhang', 'add_khachhang', 'change_khachhang',
                'view_phieuthu', 'add_phieuthu', 'change_phieuthu',
            ]
        )
        manager_group.permissions.set(manager_perms)
        print(f"  ✅ Manager: {manager_perms.count()} permissions")
        
        # --- STAFF: Tạo đơn, xem ---
        staff_perms = Permission.objects.filter(
            content_type__in=[hoadonban_ct, khachhang_ct, sanpham_ct],
            codename__in=[
                'view_hoadonban', 'add_hoadonban',
                'view_khachhang',
                'view_sanpham',
            ]
        )
        staff_group.permissions.set(staff_perms)
        print(f"  ✅ Staff: {staff_perms.count()} permissions")
        
    except ContentType.DoesNotExist:
        print("  ⚠️  Models chưa migrate, bỏ qua permissions")
    
    print("\n" + "="*60)
    print("✅ HOÀN THÀNH KHỞI TẠO DỮ LIỆU")
    print("="*60)
    print("\n📋 THÔNG TIN ĐĂNG NHẬP:")
    print("  👤 admin / admin123 (Superuser)")
    print("  👤 quanly / quanly123 (Manager)")
    print("  👤 ketoan / ketoan123 (Staff)")
    print("="*60 + "\n")

def reverse_migration(apps, schema_editor):
    """Xóa tất cả khi rollback"""
    User = apps.get_model('auth', 'User')
    Group = apps.get_model('auth', 'Group')
    
    User.objects.filter(username__in=['admin', 'quanly', 'ketoan']).delete()
    Group.objects.filter(name__in=['Admin', 'Manager', 'Staff']).delete()
    
    print("🗑️  Đã xóa users và groups")

class Migration(migrations.Migration):

    dependencies = [
        ('app_quan_ly', '0001_initial'),  # ← SỬA: Migration đầu tiên của app
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(setup_initial_data, reverse_migration),
    ]