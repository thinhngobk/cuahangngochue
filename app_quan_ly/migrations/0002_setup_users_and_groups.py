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
    print("KHOI TAO DU LIEU BAN DAU")
    print("="*60)
    
    # ===== 1. TAO 3 USERS =====
    print("\nTao users...")
    
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
            'first_name': 'Quan ly',
            'last_name': 'Cua hang'
        },
        {
            'username': 'ketoan',
            'email': 'ketoan@geminipos.com',
            'password': make_password('ketoan123'),
            'is_staff': True,
            'is_superuser': False,
            'first_name': 'Ke toan',
            'last_name': 'Vien'
        },
    ]
    
    created_users = {}
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults=user_data
        )
        created_users[user_data['username']] = user
        status = "Tao moi" if created else "Da ton tai"
        print(f"  {status}: {user_data['username']}")
    
    # ===== 2. TAO 3 GROUPS =====
    print("\nTao groups...")
    
    admin_group, created = Group.objects.get_or_create(name='Admin')
    print(f"  {'Tao moi' if created else 'Da ton tai'}: Admin")
    
    manager_group, created = Group.objects.get_or_create(name='Manager')
    print(f"  {'Tao moi' if created else 'Da ton tai'}: Manager")
    
    staff_group, created = Group.objects.get_or_create(name='Staff')
    print(f"  {'Tao moi' if created else 'Da ton tai'}: Staff")
    
    # ===== 3. GAN USERS VAO GROUPS =====
    print("\nGan users vao groups...")
    
    created_users['admin'].groups.add(admin_group)
    print("  admin -> Admin group")
    
    created_users['quanly'].groups.add(manager_group)
    print("  quanly -> Manager group")
    
    created_users['ketoan'].groups.add(staff_group)
    print("  ketoan -> Staff group")
    
    # ===== 4. SET PERMISSIONS CHO GROUPS =====
    print("\nCau hinh permissions...")
    
    try:
        hoadonban_ct = ContentType.objects.get(app_label='app_quan_ly', model='hoadonban')
        khachhang_ct = ContentType.objects.get(app_label='app_quan_ly', model='khachhang')
        sanpham_ct = ContentType.objects.get(app_label='app_quan_ly', model='sanpham')
        phieuthu_ct = ContentType.objects.get(app_label='app_quan_ly', model='phieuthu')
        
        # --- ADMIN: Toan quyen ---
        admin_perms = Permission.objects.filter(
            content_type__in=[hoadonban_ct, khachhang_ct, sanpham_ct, phieuthu_ct]
        )
        admin_group.permissions.set(admin_perms)
        print(f"  Admin: {admin_perms.count()} permissions")
        
        # --- MANAGER: Duyet don, quan ly ---
        manager_perms = Permission.objects.filter(
            content_type__in=[hoadonban_ct, khachhang_ct, phieuthu_ct],
            codename__in=[
                'view_hoadonban', 'add_hoadonban', 'change_hoadonban',
                'view_khachhang', 'add_khachhang', 'change_khachhang',
                'view_phieuthu', 'add_phieuthu', 'change_phieuthu',
            ]
        )
        manager_group.permissions.set(manager_perms)
        print(f"  Manager: {manager_perms.count()} permissions")
        
        # --- STAFF: Tao don, xem ---
        staff_perms = Permission.objects.filter(
            content_type__in=[hoadonban_ct, khachhang_ct, sanpham_ct],
            codename__in=[
                'view_hoadonban', 'add_hoadonban',
                'view_khachhang',
                'view_sanpham',
            ]
        )
        staff_group.permissions.set(staff_perms)
        print(f"  Staff: {staff_perms.count()} permissions")
        
    except ContentType.DoesNotExist:
        print("  Models chua migrate, bo qua permissions")
    
    print("\n" + "="*60)
    print("HOAN THANH KHOI TAO DU LIEU")
    print("="*60)
    print("\nTHONG TIN DANG NHAP:")
    print("  admin / admin123 (Superuser)")
    print("  quanly / quanly123 (Manager)")
    print("  ketoan / ketoan123 (Staff)")
    print("="*60 + "\n")

def reverse_migration(apps, schema_editor):
    """Xoa tat ca khi rollback"""
    User = apps.get_model('auth', 'User')
    Group = apps.get_model('auth', 'Group')
    
    User.objects.filter(username__in=['admin', 'quanly', 'ketoan']).delete()
    Group.objects.filter(name__in=['Admin', 'Manager', 'Staff']).delete()
    
    print("Da xoa users va groups")

class Migration(migrations.Migration):

    dependencies = [
        ('app_quan_ly', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(setup_initial_data, reverse_migration),
    ]