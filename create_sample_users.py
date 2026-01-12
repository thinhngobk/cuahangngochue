# app_quan_ly/management/commands/create_sample_users.py
"""
Tạo 3 user mẫu: staff1, manager1, admin1

Chạy: python manage.py create_sample_users
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group


class Command(BaseCommand):
    help = 'Tạo 3 user mẫu cho Staff, Manager, Admin'

    def handle(self, *args, **kwargs):
        self.stdout.write('\n' + '='*60)
        self.stdout.write('TẠO USER MẪU')
        self.stdout.write('='*60 + '\n')
        
        # Kiểm tra groups
        try:
            group_staff = Group.objects.get(name='Staff')
            group_manager = Group.objects.get(name='Manager')
            group_admin = Group.objects.get(name='Admin')
        except Group.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                '❌ Chưa có groups! Chạy lệnh:\n'
                '   python manage.py migrate\n'
            ))
            return
        
        users = []
        
        # 1. STAFF
        if not User.objects.filter(username='staff1').exists():
            user = User.objects.create_user(
                username='staff1',
                password='staff123',
                email='staff@gemini.com',
                first_name='Nhân viên',
                last_name='Bán hàng'
            )
            user.groups.add(group_staff)
            users.append(('staff1', 'staff123', 'Staff', 'Xem + Tạo + Sửa'))
            self.stdout.write(self.style.SUCCESS('✅ Tạo staff1'))
        
        # 2. MANAGER
        if not User.objects.filter(username='manager1').exists():
            user = User.objects.create_user(
                username='manager1',
                password='manager123',
                email='manager@gemini.com',
                first_name='Quản lý',
                last_name='Kinh doanh',
                is_staff=True  # Để vào admin site xem báo cáo
            )
            user.groups.add(group_manager)
            users.append(('manager1', 'manager123', 'Manager', 'Full quyền'))
            self.stdout.write(self.style.SUCCESS('✅ Tạo manager1'))
        
        # 3. ADMIN
        if not User.objects.filter(username='admin1').exists():
            user = User.objects.create_superuser(
                username='admin1',
                password='admin123',
                email='admin@gemini.com',
                first_name='Admin',
                last_name='Hệ thống'
            )
            user.groups.add(group_admin)
            users.append(('admin1', 'admin123', 'Admin', 'Superuser'))
            self.stdout.write(self.style.SUCCESS('✅ Tạo admin1'))
        
        # Hiển thị bảng
        if users:
            self.stdout.write('\n' + '='*60)
            self.stdout.write('✅ THÀNH CÔNG!')
            self.stdout.write('='*60 + '\n')
            self.stdout.write('{:<12} {:<12} {:<10} {:<20}'.format(
                'USERNAME', 'PASSWORD', 'ROLE', 'QUYỀN'
            ))
            self.stdout.write('-' * 60)
            for u in users:
                self.stdout.write('{:<12} {:<12} {:<10} {:<20}'.format(*u))
            self.stdout.write('\n⚠️  Đây là user MẪU cho DEV - Đổi password khi PRODUCTION!\n')
        else:
            self.stdout.write(self.style.WARNING('\n✅ Các user đã tồn tại!\n'))
