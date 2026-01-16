from django.apps import AppConfig

class AppQuanLyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_quan_ly'
    
    def ready(self):
        """Import signals khi app khởi động"""
        import app_quan_ly.signals
        
        # ← THÊM: Tự động tạo users + groups khi migrate
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver
        
        @receiver(post_migrate)
        def create_default_users_and_groups(sender, **kwargs):
            """Tự động tạo users + groups sau khi migrate"""
            if sender.name != 'app_quan_ly':
                return
            
            from django.contrib.auth.models import User, Group
            
            print("\n" + "="*60)
            print("KHOI TAO DU LIEU MAC DINH")
            print("="*60)
            
            # Tạo Groups
            admin_group, _ = Group.objects.get_or_create(name='Admin')
            manager_group, _ = Group.objects.get_or_create(name='Manager')
            staff_group, _ = Group.objects.get_or_create(name='Staff')
            print("\nTao groups: Admin, Manager, Staff")
            
            # Tạo Users
            users_config = [
                ('admin', 'admin123', True, True, admin_group),
                ('quanly', 'quanly123', True, False, manager_group),
                ('ketoan', 'ketoan123', True, False, staff_group),
            ]
            
            print("\nTao users:")
            for username, password, is_staff, is_superuser, group in users_config:
                user, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'is_staff': is_staff,
                        'is_superuser': is_superuser,
                        'email': f'{username}@geminipos.com',
                        'first_name': username.capitalize(),
                    }
                )
                if created:
                    user.set_password(password)
                    user.save()
                    user.groups.add(group)
                    print(f"  Tao moi: {username} / {password}")
                else:
                    print(f"  Da ton tai: {username}")
            
            print("\n" + "="*60)
            print("HOAN THANH!")
            print("="*60 + "\n")